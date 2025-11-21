import subprocess
from typing import List
from night_shift.utils.result import Result
from night_shift.models import GitCommit


def get_recent_commits(limit: int = 10) -> Result[List[GitCommit], str]:
    """Retrieve recent git commits as GitCommit models."""
    try:
        result = subprocess.run(
            ["git", "log", f"-n{limit}", "--pretty=format:%h|%an|%s"],
            capture_output=True,
            text=True,
            check=True,
        )
        commits: List[GitCommit] = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            sha, author, message = line.split("|", 2)
            commits.append(GitCommit(sha=sha, author=author, message=message))
        return Result.Ok(commits)
    except subprocess.CalledProcessError as e:
        return Result.Err(f"Git command failed: {e}")
    except Exception as exc:
        return Result.Err(str(exc))
