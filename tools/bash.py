import logging
import os
import re
import shlex
import subprocess
import threading
from datetime import datetime, timedelta

from agency_swarm.tools import BaseTool
from pydantic import Field, field_validator

from shared.timeout_wrapper import TimeoutConfig, with_constitutional_timeout

# Resource-based locking for file operations with TTL
# Allows parallel execution except when accessing the same resources
_resource_locks: dict[str, tuple[threading.RLock, datetime]] = {}
_locks_mutex = threading.Lock()
_LOCK_TTL = timedelta(minutes=15)  # Locks expire after 15 minutes
_MAX_LOCKS = 1000  # Maximum number of locks to prevent unbounded growth

# Security configuration for command validation
DANGEROUS_COMMANDS = {
    "rm",
    "rmdir",
    "dd",
    "mkfs",
    "fdisk",
    "format",
    "shutdown",
    "reboot",
    "halt",
    "sudo",
    "su",
    "chmod",
    "chown",
    "passwd",
    "useradd",
    "userdel",
    "usermod",
    "mount",
    "umount",
    "crontab",
    "at",
    "systemctl",
    "service",
    "kill",
    "killall",
}

DANGEROUS_PATTERNS = [
    r">\s*/dev/",  # Redirecting to device files
    r"rm\s+-[rf]*[rf].*/",  # rm with recursive or force flags on directories
    r"curl\s+.*\|\s*sh",  # Downloading and executing
    r"wget\s+.*\|\s*sh",  # Downloading and executing
    r"eval\s*\$\(",  # Dynamic evaluation with substitution
    r"[;&|]+\s*rm\s+-[rf]",  # Chained dangerous rm commands
]


class CommandValidationError(Exception):
    """Raised when command validation fails."""

    pass


def cleanup_expired_locks():
    """Remove expired locks to prevent memory leaks."""
    current_time = datetime.now()
    expired_keys = []

    for path, (lock, timestamp) in list(_resource_locks.items()):
        if current_time - timestamp > _LOCK_TTL:
            # Only remove if lock is not currently held
            if lock.acquire(blocking=False):
                try:
                    lock.release()
                    expired_keys.append(path)
                except:
                    pass

    for key in expired_keys:
        del _resource_locks[key]


def get_resource_lock(resource_path: str) -> threading.RLock:
    """Get or create a lock for a specific resource path with TTL and cleanup."""
    with _locks_mutex:
        # Cleanup expired locks periodically
        if len(_resource_locks) % 50 == 0:  # Cleanup every 50 lock accesses
            cleanup_expired_locks()

        # Enforce maximum lock limit
        if len(_resource_locks) >= _MAX_LOCKS:
            cleanup_expired_locks()
            if len(_resource_locks) >= _MAX_LOCKS:
                # Remove oldest locks if still at limit
                oldest_items = sorted(_resource_locks.items(), key=lambda x: x[1][1])[:100]
                for path, _ in oldest_items:
                    if path != resource_path:  # Don't remove the one we're trying to get
                        del _resource_locks[path]

        # Get or create lock
        if resource_path not in _resource_locks:
            _resource_locks[resource_path] = (threading.RLock(), datetime.now())
        else:
            # Update timestamp on access
            lock, _ = _resource_locks[resource_path]
            _resource_locks[resource_path] = (lock, datetime.now())

        return _resource_locks[resource_path][0]


def extract_file_paths(command: str) -> set[str]:
    """Extract potential file paths from a command for locking."""
    paths = set()

    # Common patterns for file operations
    file_ops = [
        r"(?:cat|less|more|head|tail|nano|vi|vim|emacs)\s+([^\s;&|]+)",
        r"(?:touch|mkdir|rmdir|rm)\s+([^\s;&|]+)",
        r"(?:cp|mv)\s+([^\s;&|]+)\s+([^\s;&|]+)",
        r"(?:echo|printf).*?>\s*([^\s;&|]+)",
        r"([^\s;&|]+)\s*<\s*([^\s;&|]+)",
    ]

    for pattern in file_ops:
        for match in re.finditer(pattern, command):
            for group in match.groups():
                if group and not group.startswith("-"):
                    # Resolve to canonical path using os.path.realpath
                    try:
                        # Expand user home and environment variables
                        expanded_path = os.path.expanduser(os.path.expandvars(group))
                        # Get real canonical path (resolves symlinks and ..)
                        canonical_path = os.path.realpath(expanded_path)
                        paths.add(canonical_path)
                    except (OSError, ValueError):
                        # If resolution fails, use the original path
                        paths.add(group)

    return paths


class Bash(BaseTool):  # type: ignore[misc]
    """
    Executes a given bash command in a persistent shell session with constitutional security compliance.

    SECURITY FEATURES (Article I Compliance):
    - Input sanitization and command validation
    - Protection against command injection attacks
    - Sandboxed execution on supported platforms
    - Timeout handling with exponential backoff (2x, 3x, up to 10x)
    - Complete context verification before proceeding
    - Environment variable sanitization

    Before executing the command, please follow these steps:

    1. Directory Verification:
       - If the command will create new directories or files, first use the LS tool to verify the parent directory exists and is the correct location
       - For example, before running "mkdir foo/bar", first use LS to check that "foo" exists and is the intended parent directory

    2. Command Execution:
       - Always quote file paths that contain spaces with double quotes (e.g., cd "path with spaces/file.txt")
       - Examples of proper quoting:
         - cd "/Users/name/My Documents" (correct)
         - cd /Users/name/My Documents (incorrect - will fail)
         - python "/path/with spaces/script.py" (correct)
         - python /path/with spaces/script.py (incorrect - will fail)
       - After ensuring proper quoting, execute the command.
       - Capture the output of the command.

    Usage notes:
      - The command argument is required.
      - You can specify an optional timeout in milliseconds (up to 600000ms / 10 minutes). If not specified, commands will timeout after 120000ms (2 minutes).
      - It is very helpful if you write a clear, concise description of what this command does in 5-10 words.
      - If the output exceeds 30000 characters, output will be truncated before being returned to you.
      - VERY IMPORTANT: Prefer the specialized tools (Grep, Glob, Read, LS, Task) over shell commands with the same names. Do not call CLI `grep`, `find`, or `rg` here for code/content search; use the Grep tool. Do not call CLI `ls` to enumerate; use the LS tool. Do not call CLI `cat`/`head`/`tail` to read files; use the Read tool.
      - When issuing multiple commands, use the ';' or '&&' operator to separate them. Multiline scripts are allowed when needed.
      - Try to maintain your current working directory throughout the session by using absolute paths and avoiding usage of `cd`. You may use `cd` if the User explicitly requests it.
        <good-example>
        pytest /foo/bar/tests
        </good-example>
        <bad-example>
        cd /foo/bar && pytest tests
        </bad-example>



    # Committing changes with git

    When the user asks you to create a new git commit, follow these steps carefully:

    1. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following bash commands in parallel, each using the Bash tool:
      - Run a git status command to see all untracked files.
      - Run a git diff command to see both staged and unstaged changes that will be committed.
      - Run a git log command to see recent commit messages, so that you can follow this repository's commit message style.
    2. Analyze all staged changes (both previously staged and newly added) and draft a commit message:
      - Summarize the nature of the changes (eg. new feature, enhancement to an existing feature, bug fix, refactoring, test, docs, etc.). Ensure the message accurately reflects the changes and their purpose (i.e. "add" means a wholly new feature, "update" means an enhancement to an existing feature, "fix" means a bug fix, etc.).
      - Check for any sensitive information that shouldn't be committed
      - Draft a concise (1-2 sentences) commit message that focuses on the "why" rather than the "what"
      - Ensure it accurately reflects the changes and their purpose
    3. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following commands in parallel:
       - Add relevant untracked files to the staging area.
       - Create the commit.
       - Run git status to make sure the commit succeeded.
    4. If the commit fails due to pre-commit hook changes, retry the commit ONCE to include these automated changes. If it fails again, it usually means a pre-commit hook is preventing the commit. If the commit succeeds but you notice that files were modified by the pre-commit hook, you MUST amend your commit to include them.

    Important notes:
    - NEVER update the git config
    - NEVER run additional commands to read or explore code, besides git bash commands
    - NEVER use the TodoWrite or Task tools
    - DO NOT push to the remote repository unless the user explicitly asks you to do so
    - IMPORTANT: Never use git commands with the -i flag (like git rebase -i or git add -i) since they require interactive input which is not supported.
    - If there are no changes to commit (i.e., no untracked files and no modifications), do not create an empty commit
    - In order to ensure good formatting, ALWAYS pass the commit message via a HEREDOC, a la this example:
    <example>
    git commit -m "$(cat <<'EOF'
       Commit message here.
       EOF
       )"
    </example>

    # Creating pull requests
    Use the gh command via the Bash tool for ALL GitHub-related tasks including working with issues, pull requests, checks, and releases. If given a Github URL use the gh command to get the information needed.

    IMPORTANT: When the user asks you to create a pull request, follow these steps carefully:

    1. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following bash commands in parallel using the Bash tool, in order to understand the current state of the branch since it diverged from the main branch:
       - Run a git status command to see all untracked files
       - Run a git diff command to see both staged and unstaged changes that will be committed
       - Check if the current branch tracks a remote branch and is up to date with the remote, so you know if you need to push to the remote
       - Run a git log command and `git diff [base-branch]...HEAD` to understand the full commit history for the current branch (from the time it diverged from the base branch)
    2. Analyze all changes that will be included in the pull request, making sure to look at all relevant commits (NOT just the latest commit, but ALL commits that will be included in the pull request!!!), and draft a pull request summary
    3. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following commands in parallel:
       - Create new branch if needed
       - Push to remote with -u flag if needed
       - Create PR using gh pr create with the format below. Use a HEREDOC to pass the body to ensure correct formatting.
    <example>
    gh pr create --title "the pr title" --body "$(cat <<'EOF'
    ## Summary
    <1-3 bullet points>

    ## Test plan
    [Checklist of TODOs for testing the pull request...]
    EOF
    )"
    </example>

    Important:
    - NEVER update the git config
    - DO NOT use the TodoWrite or Task tools
    - Return the PR URL when you're done, so the user can see it

    # Other common operations
    - View comments on a Github PR: gh api repos/foo/bar/pulls/123/comments
    """

    command: str = Field(
        ...,
        description="The bash command to execute. Make sure to add interactive flags like --yes, -y, --force, -f, etc.",
    )
    timeout: int = Field(
        12000,
        description="Timeout in milliseconds (max 600000, min 5000)",
        ge=5000,
        le=60000,
    )

    description: str | None = Field(
        None,
        description="Clear, concise description of what this command does in 5-10 words. Examples:\nInput: ls\nOutput: Lists files in current directory\n\nInput: git status\nOutput: Shows working tree status\n\nInput: npm install\nOutput: Installs package dependencies\n\nInput: mkdir foo\nOutput: Creates directory 'foo'",
    )

    # Internal field for timeout configuration (set dynamically during execution)
    timeout_config: TimeoutConfig | None = Field(
        default=None,
        description="Constitutional timeout configuration (internal use)",
        exclude=True,  # Don't include in tool schema
    )

    @field_validator("command")
    @classmethod
    def validate_command_pydantic(cls, v: str) -> str:
        """
        Pydantic field validator for command input validation.

        This provides the first layer of security validation at the input level,
        ensuring dangerous patterns are rejected before the command is processed.

        Raises:
            ValueError: If command fails Pydantic-level validation
        """
        # Empty command check
        if not v or not v.strip():
            raise ValueError("Empty command not allowed")

        # Sanitize command for analysis
        clean_command = v.strip().lower()

        # Check for dangerous command patterns (strict blocking list)
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, clean_command, re.IGNORECASE):
                raise ValueError(f"Dangerous pattern detected: {pattern}")

        # Parse command tokens safely
        try:
            tokens = shlex.split(v)
        except ValueError as e:
            raise ValueError(f"Command parsing failed: {e}")

        if not tokens:
            raise ValueError("No valid command tokens found")

        # Resolve command to canonical form and check against dangerous commands
        main_command = tokens[0]

        # Handle full paths and resolve to canonical command
        if "/" in main_command:
            try:
                canonical_cmd = os.path.realpath(main_command)
                main_command = os.path.basename(canonical_cmd)
            except (OSError, ValueError):
                main_command = os.path.basename(main_command)

        # Check resolved command against dangerous commands (case-insensitive)
        if main_command.lower() in DANGEROUS_COMMANDS:
            raise ValueError(f"Dangerous command not allowed: {main_command}")

        # Validate injection patterns (backticks and command substitution)
        cls._validate_injection_patterns_static(v)

        return v

    @staticmethod
    def _validate_injection_patterns_static(command: str) -> None:
        """
        Static method for validating command injection patterns.
        Used by both Pydantic validator and runtime validation.

        Raises:
            ValueError: If dangerous injection patterns are detected
        """
        # Check for malicious backticks
        backtick_pattern = r"`([^`]*)`"
        backtick_matches = re.findall(backtick_pattern, command)
        if backtick_matches:
            dangerous_backticks = [
                match
                for match in backtick_matches
                if any(
                    danger in match.lower() for danger in ["rm", "curl", "wget", "sudo", "chmod"]
                )
            ]
            if dangerous_backticks:
                raise ValueError(f"Dangerous backtick execution detected: {dangerous_backticks}")

        # Check for dangerous command substitution
        substitution_pattern = r"\$\(([^)]*)\)"
        substitution_matches = re.findall(substitution_pattern, command)
        if substitution_matches:
            safe_substitutions = ["pwd", "date", "whoami", "basename", "dirname", "cat", "echo"]
            dangerous_substitutions = []
            for match in substitution_matches:
                match_lower = match.lower().strip()
                is_safe = any(match_lower.startswith(safe) for safe in safe_substitutions)
                if not is_safe and any(
                    danger in match_lower for danger in ["rm", "curl", "wget", "sudo", "chmod"]
                ):
                    dangerous_substitutions.append(match)
            if dangerous_substitutions:
                raise ValueError(
                    f"Dangerous command substitution detected: {dangerous_substitutions}"
                )

        # Check for suspicious command chaining
        suspicious_chaining = re.findall(
            r"[;&|]+\s*(rm|sudo|chmod|curl.*\||wget.*\|)", command, re.IGNORECASE
        )
        if suspicious_chaining:
            raise ValueError(f"Suspicious command chaining detected: {suspicious_chaining}")

    def _validate_command_security(self, command: str) -> None:
        """
        Validate command against security policies (Article I: Context Verification).

        Raises:
            CommandValidationError: If command fails security validation
        """
        if not command or not command.strip():
            raise CommandValidationError("Empty command not allowed")

        # Sanitize command for analysis
        clean_command = command.strip().lower()

        # Check for dangerous command patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, clean_command, re.IGNORECASE):
                raise CommandValidationError(f"Dangerous pattern detected: {pattern}")

        # Parse command tokens safely
        try:
            tokens = shlex.split(command)
        except ValueError as e:
            raise CommandValidationError(f"Command parsing failed: {e}")

        if not tokens:
            raise CommandValidationError("No valid command tokens found")

        # Resolve command aliases and full paths before checking
        main_command = tokens[0]

        # Handle full paths and resolve to canonical command
        if "/" in main_command:
            try:
                # Resolve symlinks and get real command
                canonical_cmd = os.path.realpath(main_command)
                main_command = os.path.basename(canonical_cmd)
            except (OSError, ValueError):
                # Fallback to simple basename extraction
                main_command = os.path.basename(main_command)
        else:
            # For non-path commands, just use as-is
            main_command = tokens[0]

        # Check resolved command against dangerous commands
        if main_command in DANGEROUS_COMMANDS:
            raise CommandValidationError(f"Dangerous command not allowed: {main_command}")

        # Additional validation for file operations
        self._validate_file_operations(tokens)

        # Check for command injection attempts
        self._validate_injection_patterns(command)

    def _validate_file_operations(self, tokens: list[str]) -> None:
        """Validate file operations for safety using canonical paths."""
        dangerous_paths = {
            "/etc",
            "/bin",
            "/sbin",
            "/usr/bin",
            "/usr/sbin",
            "/boot",
            "/sys",
            "/proc",
        }

        for i, token in enumerate(tokens):
            # Skip non-path tokens
            if not (token.startswith("/") or token.startswith("~") or token.startswith(".")):
                continue

            # Resolve to canonical path to prevent traversal attacks
            try:
                # Expand user home and environment variables
                expanded_path = os.path.expanduser(os.path.expandvars(token))
                # Get real canonical path (resolves symlinks and ..)
                canonical_path = os.path.realpath(expanded_path)

                # Check if canonical path is in dangerous locations
                for danger_path in dangerous_paths:
                    if canonical_path.startswith(danger_path):
                        # Check if this is a write/delete operation
                        if i > 0 and tokens[i - 1] in [">", ">>", "tee", "cp", "mv", "rm", "rmdir"]:
                            raise CommandValidationError(
                                f"Write/delete operation to system directory not allowed: {canonical_path} (from {token})"
                            )
            except (OSError, ValueError):
                # If we can't resolve the path, be conservative and check the raw path
                if token.startswith("/") and any(
                    token.startswith(path) for path in dangerous_paths
                ):
                    if i > 0 and tokens[i - 1] in [">", ">>", "tee", "cp", "mv", "rm", "rmdir"]:
                        raise CommandValidationError(
                            f"Write/delete operation to system directory not allowed: {token}"
                        )

    def _validate_injection_patterns(self, command: str) -> None:
        """
        Check for command injection patterns.

        This method wraps the static validator to maintain backward compatibility
        and convert ValueError to CommandValidationError.
        """
        try:
            self._validate_injection_patterns_static(command)
        except ValueError as e:
            raise CommandValidationError(str(e))

    def run(self):
        """Execute the bash command with security validation."""
        # Removed global _bash_busy - parallel execution now supported

        try:
            # Parallel execution is now allowed - no busy check needed
            pass  # Removed busy check for parallel execution support

            # Article I: Complete Context - Validate command security before execution
            try:
                self._validate_command_security(self.command)
            except CommandValidationError as e:
                return f"Exit code: 1\nSecurity validation failed: {str(e)}\n\nCommand blocked for security reasons."

            # Set timeout (convert from milliseconds to seconds)
            timeout_seconds = self.timeout / 1000

            # Prepare the command - add non-interactive flags for common interactive commands
            command = self.command

            # Handle Python compatibility: replace 'python' with 'python3' throughout command
            # Use word boundaries to avoid replacing parts of words
            command = re.sub(r"\bpython\b", "python3", command)

            # Add non-interactive flags for common commands that might hang
            interactive_commands = {
                "npx create-next-app": lambda cmd: cmd if "--yes" in cmd else cmd + " --yes",
                "npm init": lambda cmd: cmd if "-y" in cmd else cmd + " -y",
                "yarn create": lambda cmd: cmd if "--yes" in cmd else cmd + " --yes",
            }

            for cmd_pattern, modifier in interactive_commands.items():
                if cmd_pattern in command:
                    command = modifier(command)
                    break

            # Extract file paths for resource-based locking
            file_paths = extract_file_paths(command)

            # Acquire locks for all affected resources (sorted to prevent deadlocks)
            sorted_paths = sorted(file_paths)
            locks = [get_resource_lock(path) for path in sorted_paths]

            # Acquire all locks in order
            for lock in locks:
                lock.acquire()

            try:
                # Execute command with resource locks held
                # Configure timeout for decorator via instance attribute
                timeout_ms = int(timeout_seconds * 1000)
                self.timeout_config = TimeoutConfig(
                    base_timeout_ms=timeout_ms,
                    max_retries=3,  # Reduced from 5 to match previous behavior
                    multipliers=[1, 2, 3, 5, 10],
                    completeness_check=True,
                    pause_between_retries_sec=2.0,
                )
                return self._execute_bash_command(command)
            finally:
                # Release all locks in reverse order
                for lock in reversed(locks):
                    lock.release()

        except Exception as e:
            # Handle timeout wrapper exceptions
            from shared.timeout_wrapper import IncompleteContextError, TimeoutExhaustedError

            if isinstance(e, TimeoutExhaustedError):
                return f"Exit code: 124\nCommand timed out after constitutional retry attempts ({e.attempts} attempts, {e.total_time_ms}ms total)\n--- OUTPUT ---\n{getattr(e.last_error, 'stdout', '') if hasattr(e, 'last_error') else ''}"
            elif isinstance(e, IncompleteContextError):
                return f"Exit code: 1\nIncomplete context detected: {e.indicator}\nArticle I: NEVER proceed with incomplete data."
            else:
                return f"Exit code: 1\nError executing command: {str(e)}"

    @with_constitutional_timeout()
    def _execute_bash_command(self, command, timeout_ms=None):
        """Execute a bash command using subprocess.run with constitutional timeout pattern."""
        # timeout_ms is injected by the decorator based on self.timeout_config
        timeout_sec = timeout_ms / 1000.0 if timeout_ms else 120.0  # Default 2 minutes

        try:
            logging.info(f"Executing bash command with timeout: {timeout_sec}s")

            # Build execution command with enhanced sandboxing
            exec_cmd = self._build_secure_execution_command(command)

            result = subprocess.run(
                exec_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=os.getcwd(),
                env=self._get_secure_environment(),
            )

            # Article I: Verify complete context - check for incomplete output indicators
            if not self._is_output_complete(result):
                logging.warning("Output appears incomplete, decorator will retry...")
                raise Exception("Incomplete output detected")

            output = ""
            # Combine stdout and stderr
            if result.stdout:
                output += result.stdout
            if result.stderr:
                if output:
                    output += "\n"
                output += result.stderr

            # Handle empty output
            if not output.strip():
                return f"Exit code: {result.returncode}\n(Command completed with no output)"

            # Truncate if too long
            if len(output) > 30000:
                output = output[-30000:] + "\n (output truncated to last 30000 characters)"

            return f"Exit code: {result.returncode}\n--- OUTPUT ---\n{output.strip()}"

        except subprocess.TimeoutExpired:
            # Re-raise to let decorator handle retry logic
            logging.warning(f"Bash command timed out after {timeout_sec}s")
            raise
        except Exception as e:
            # Re-raise non-timeout exceptions to let decorator handle retries
            if "Incomplete output" not in str(e):
                logging.error(f"Error executing command: {str(e)}")
            raise

    def _build_secure_execution_command(self, command: str) -> list[str]:
        """Build secure execution command with sandboxing."""
        exec_cmd = ["/bin/bash", "-c", command]

        try:
            if os.uname().sysname == "Darwin" and os.path.exists("/usr/bin/sandbox-exec"):
                cwd = os.getcwd()
                # Sanitize cwd to prevent injection - escape quotes and backslashes
                sanitized_cwd = cwd.replace("\\", "\\\\").replace('"', '\\"')
                # Simplified sandbox policy to avoid network syntax issues
                policy = f"""(version 1)
(allow default)
(deny file-write*)
(allow file-write* (subpath \"{sanitized_cwd}\"))
(allow file-write* (subpath \"/tmp\"))
(allow file-write* (subpath \"/private/tmp\"))
"""
                exec_cmd = [
                    "/usr/bin/sandbox-exec",
                    "-p",
                    policy,
                    "/bin/bash",
                    "-c",
                    command,
                ]
        except Exception:
            # If sandbox detection/build fails, fall back to normal execution
            logging.warning("Sandbox execution failed, falling back to normal execution")

        return exec_cmd

    def _get_secure_environment(self) -> dict:
        """Get secure environment variables."""
        env = os.environ.copy()

        # Remove potentially dangerous environment variables
        dangerous_env_vars = ["LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES"]
        for var in dangerous_env_vars:
            env.pop(var, None)

        # Preserve original PATH to maintain python/python3 availability
        # but limit to safe directories
        original_path = env.get("PATH", "")
        safe_paths = ["/usr/bin", "/bin", "/usr/local/bin", "/opt/homebrew/bin"]

        # Add paths from original PATH that are considered safe
        for path in original_path.split(":"):
            if path:
                # Resolve symlinks to prevent path manipulation
                try:
                    real_path = os.path.realpath(path)
                    if any(real_path.startswith(safe) for safe in safe_paths):
                        if real_path not in safe_paths:
                            safe_paths.append(real_path)
                except (OSError, ValueError):
                    # Skip paths that can't be resolved
                    continue

        env["PATH"] = ":".join(safe_paths)
        env["SHELL"] = "/bin/bash"

        return env

    def _is_output_complete(self, result) -> bool:
        """
        Check if command output appears complete (Article I: Context Verification).

        Returns False if output appears truncated or incomplete.
        """
        if result.returncode != 0:
            return True  # Error states are considered "complete" for validation

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # Check for common incomplete output indicators
        incomplete_indicators = [
            "Terminated",
            "Killed",
            "... (truncated)",
            "Connection timed out",
            "Resource temporarily unavailable",
        ]

        combined_output = stdout + stderr
        for indicator in incomplete_indicators:
            if indicator in combined_output:
                logging.warning(f"Incomplete output detected: {indicator}")
                return False

        return True


# Create alias for Agency Swarm tool loading (expects class name = file name)
bash = Bash
