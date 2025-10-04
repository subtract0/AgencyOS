# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value"
import os
import re
from typing import Literal

from agency_swarm.tools import BaseTool
from pydantic import Field, field_validator


class Git(BaseTool):  # type: ignore[misc]
    """Read-only git operations using dulwich library only.

    Supports: status, diff, log, show. All operations are safe and non-destructive.

    Security: Command whitelisting and input validation prevent injection attacks.
    """

    cmd: Literal["status", "diff", "log", "show"] = Field(
        ..., description="Git command: status, diff, log, show (read-only operations only)"
    )
    ref: str = Field(
        "HEAD", description="Git reference for diff/show operations (branch, tag, or commit hash)"
    )
    max_lines: int = Field(20000, description="Max output lines (1-1000000)", gt=0, le=1000000)

    @field_validator("cmd")
    @classmethod
    def validate_cmd(cls, v: str) -> str:
        """Validate command is whitelisted and not empty."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty or whitespace-only")
        # Literal type already restricts to whitelist, but explicit check for clarity
        allowed = {"status", "diff", "log", "show"}
        if v not in allowed:
            raise ValueError(f"Command '{v}' not in whitelist: {allowed}")
        return v

    @field_validator("ref")
    @classmethod
    def validate_ref(cls, v: str) -> str:
        """Validate git reference doesn't contain injection patterns.

        Blocks: command injection chars (;|&$`), null bytes, newlines, path traversal.
        Allows: alphanumeric, dash, underscore, dot, forward slash, caret, tilde.
        """
        if not v or not v.strip():
            raise ValueError("Reference cannot be empty or whitespace-only")

        # Check for injection characters
        dangerous_chars = {";", "|", "&", "$", "`", "\x00", "\n", "\r", "\t"}
        for char in dangerous_chars:
            if char in v:
                raise ValueError(
                    f"Reference contains unsafe character: {repr(char)}. "
                    "Possible injection attempt blocked."
                )

        # Check for path traversal attempts
        if ".." in v:
            raise ValueError(
                "Reference contains path traversal pattern '..' - blocked for security"
            )

        # Validate against safe pattern: git refs are alphanumeric with limited special chars
        # Allow: a-z A-Z 0-9 - _ . / ^ ~ (common in git refs)
        safe_pattern = re.compile(r"^[a-zA-Z0-9\-_./^~]+$")
        if not safe_pattern.match(v):
            raise ValueError(
                f"Reference '{v}' contains invalid characters. "
                "Only alphanumeric, dash, underscore, dot, slash, caret, and tilde allowed."
            )

        return v

    def run(self):
        import warnings

        warnings.warn(
            "Git tool is deprecated. Use GitUnified instead: "
            "from tools.git_unified import GitUnified. "
            "This tool will be removed after 2025-11-02 (30 days).",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            from io import StringIO

            from dulwich import porcelain
        except Exception:
            return (
                "Exit code: 1\n"
                "dulwich not installed. Install with: pip install dulwich\n"
                "Or run: pip install -r requirements.txt"
            )

        try:
            repo = porcelain.open_repo(os.getcwd())
        except Exception as e:
            return f"Exit code: 1\nError opening git repo: {e}"

        try:
            if self.cmd == "status":
                st = porcelain.status(repo)
                out = []
                for p in sorted(st.untracked):
                    name = p.decode() if isinstance(p, bytes) else p
                    out.append(f"?? {name}")
                for p in sorted(st.unstaged):
                    name = p.decode() if isinstance(p, bytes) else p
                    out.append(f" M {name}")
                staged = getattr(st, "staged", {}) or {}
                for category, items in staged.items():
                    code = {"add": "A", "delete": "D", "modify": "M"}.get(category, "S")
                    for p in items:
                        name = p.decode() if isinstance(p, bytes) else p
                        out.append(f" {code} {name}")
                return "\n".join(out) or "(clean)"

            if self.cmd == "diff":
                # Show unstaged changes using dulwich
                out = StringIO()
                try:
                    # Get working tree vs HEAD diff
                    porcelain.diff_tree(repo, repo.head(), None, outstream=out)
                    lines = out.getvalue().splitlines()
                    if len(lines) > self.max_lines:
                        lines = lines[: self.max_lines] + ["(truncated)"]
                    return "\n".join(lines)
                except Exception as e:
                    return f"Exit code: 1\nError in diff: {e}"

            if self.cmd == "show":
                # Show commit details
                out = StringIO()
                try:
                    porcelain.show(repo, objects=[self.ref.encode()], outstream=out)
                    lines = out.getvalue().splitlines()
                    if len(lines) > self.max_lines:
                        lines = lines[: self.max_lines] + ["(truncated)"]
                    return "\n".join(lines)
                except Exception as e:
                    return f"Exit code: 1\nError in show: {e}"

            if self.cmd == "log":
                out = StringIO()
                porcelain.log(repo, outstream=out)
                lines = out.getvalue().splitlines()
                if len(lines) > self.max_lines:
                    lines = lines[: self.max_lines] + ["(truncated)"]
                return "\n".join(lines)

            return "Exit code: 1\nUnknown cmd"
        except Exception as e:
            return f"Exit code: 1\nError: {e}"


git = Git
