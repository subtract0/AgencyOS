#!/usr/bin/env python3
"""Post Trinity audit results as a comment on a GitHub PR.

This script mimics what the GitHub Action does, but can be run locally
for testing or manual audits.

Usage:
    python scripts/comment_on_pr.py --pr 39 --repo subtract0/Agency
"""

import argparse
import json
import subprocess
from pathlib import Path


def get_audit_summary(audit_dir: Path) -> str:
    """Generate formatted PR comment from audit state."""
    state_file = audit_dir / ".audit_state.json"

    if not state_file.exists():
        return "⚠️ No audit results found. Run continuous_audit_m4pro.py first."

    # Use format_pr_comment.py to generate the comment
    result = subprocess.run(
        ["python", "scripts/format_pr_comment.py", "--input", str(state_file)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    if result.returncode == 0:
        return result.stdout
    else:
        return f"⚠️ Failed to format comment: {result.stderr}"


def post_comment(repo: str, pr_number: int, comment: str) -> bool:
    """Post comment to PR using GitHub CLI."""
    try:
        result = subprocess.run(
            ["gh", "pr", "comment", str(pr_number), "--body", comment, "--repo", repo],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✅ Comment posted to PR #{pr_number}")
        print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to post comment: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Post Trinity audit to PR")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--repo", default="subtract0/Agency", help="Repository (owner/name)")
    parser.add_argument(
        "--audit-dir",
        type=Path,
        default=Path(".output/audit_recommendations"),
        help="Audit results directory",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print comment without posting")

    args = parser.parse_args()

    print(f"🤖 Trinity PR Comment Tool")
    print(f"   PR: #{args.pr}")
    print(f"   Repo: {args.repo}")
    print(f"   Audit dir: {args.audit_dir}")
    print()

    # Generate comment
    print("📊 Generating comment from audit results...")
    comment = get_audit_summary(args.audit_dir)

    if args.dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN - Comment Preview:")
        print("=" * 80)
        print(comment)
        print("=" * 80)
        return

    # Post to PR
    print("📤 Posting comment to PR...")
    success = post_comment(args.repo, args.pr, comment)

    if success:
        pr_url = f"https://github.com/{args.repo}/pull/{args.pr}"
        print()
        print(f"✅ Done! View comment:")
        print(f"   {pr_url}")
    else:
        print()
        print("❌ Failed to post comment. Check errors above.")
        print()
        print("Troubleshooting:")
        print("  - Is gh CLI authenticated? Run: gh auth status")
        print("  - Does PR #%d exist? Run: gh pr view %d" % (args.pr, args.pr))
        print("  - Do you have write permissions on %s?" % args.repo)


if __name__ == "__main__":
    main()
