import os
import subprocess
import threading
from typing import Optional

from agency_swarm.tools import BaseTool
from pydantic import Field

# Global execution lock to prevent parallel bash commands
_bash_execution_lock = threading.Lock()
_bash_busy = False  # Track if a bash command is currently executing


class Bash(BaseTool):
    """
    Executes a given bash command in a persistent shell session with optional timeout, ensuring proper handling and security measures.

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

    description: Optional[str] = Field(
        None,
        description="Clear, concise description of what this command does in 5-10 words. Examples:\nInput: ls\nOutput: Lists files in current directory\n\nInput: git status\nOutput: Shows working tree status\n\nInput: npm install\nOutput: Installs package dependencies\n\nInput: mkdir foo\nOutput: Creates directory 'foo'",
    )

    def run(self):
        """Execute the bash command."""
        global _bash_busy

        try:
            # Check if another bash command is currently executing
            if _bash_busy:
                return """Exit code: 1
Error: Terminal is currently busy executing another command.

🔄 Only one bash command can execute at a time to prevent conflicts.

💡 Please wait for the current command to complete before submitting the next one.
   Submit your commands sequentially, not in parallel.

ℹ️  If you have multiple commands to run, either:
   - Wait and submit them one at a time, or
   - Combine them using ';' or '&&' operators in a single command

Example: echo "first" && echo "second" && ls -la"""

            # Set timeout (convert from milliseconds to seconds)
            timeout_seconds = self.timeout / 1000

            # Prepare the command - add non-interactive flags for common interactive commands
            command = self.command

            # Add non-interactive flags for common commands that might hang
            interactive_commands = {
                "npx create-next-app": lambda cmd: cmd
                if "--yes" in cmd
                else cmd + " --yes",
                "npm init": lambda cmd: cmd if "-y" in cmd else cmd + " -y",
                "yarn create": lambda cmd: cmd if "--yes" in cmd else cmd + " --yes",
            }

            for cmd_pattern, modifier in interactive_commands.items():
                if cmd_pattern in command:
                    command = modifier(command)
                    break

            # Execute with proper locking to prevent parallel execution
            with _bash_execution_lock:
                _bash_busy = True
                try:
                    return self._execute_bash_command(command, timeout_seconds)
                finally:
                    _bash_busy = False

        except Exception as e:
            _bash_busy = False  # Make sure to clear busy flag on exception
            return f"Exit code: 1\nError executing command: {str(e)}"

    def _execute_bash_command(self, command, timeout_seconds):
        """Execute a bash command using subprocess.run with proper timeout."""
        output = ""
        try:
            # Build execution command, sandboxing writes to CWD and /tmp on macOS when available
            exec_cmd = ["/bin/bash", "-c", command]
            try:
                if os.uname().sysname == "Darwin" and os.path.exists(
                    "/usr/bin/sandbox-exec"
                ):
                    cwd = os.getcwd()
                    policy = f"""(version 1)
(allow default)
(deny file-write*)
(allow file-write* (subpath \"{cwd}\"))
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
                exec_cmd = ["/bin/bash", "-c", command]

            result = subprocess.run(
                exec_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=os.getcwd(),
                env=os.environ.copy(),
            )

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
                output = (
                    output[-30000:] + "\n (output truncated to last 30000 characters)"
                )

            return f"Exit code: {result.returncode}\n--- OUTPUT ---\n{output.strip()}"

        except subprocess.TimeoutExpired:
            return f"Exit code: 124\nCommand timed out after {timeout_seconds} seconds\n--- OUTPUT ---\n{output.strip()}"
        except Exception as e:
            return f"Exit code: 1\nError executing command: {str(e)}\n--- OUTPUT ---\n{output.strip()}"


# Create alias for Agency Swarm tool loading (expects class name = file name)
bash = Bash
