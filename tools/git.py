import os
from typing import List, Optional

from agency_swarm.tools import BaseTool
from pydantic import Field


class Git(BaseTool):
    """Read-only git operations using dulwich library only.

    Supports: status, diff, log, show. All operations are safe and non-destructive.
    """

    cmd: str = Field(..., description="Git command: status, diff, log, show")
    ref: str = Field("HEAD", description="Git reference for diff/show operations")
    max_lines: int = Field(20000, description="Max output lines")

    def run(self):
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
