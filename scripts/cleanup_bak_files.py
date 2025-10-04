#!/usr/bin/env python3
"""
Cleanup script for .bak files created by automated fixing tools.

This script safely removes .bak backup files that are created during
type fixing and other automated code modification operations.

Usage:
    python scripts/cleanup_bak_files.py [--dry-run]
"""

import argparse
import os
from pathlib import Path


def find_bak_files(root_dir: Path) -> list[Path]:
    """Find all .bak files in the repository."""
    bak_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip hidden directories and common build directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", "build", "dist"]]

        for file in files:
            if file.endswith(".bak"):
                bak_files.append(Path(root) / file)

    return bak_files


def cleanup_bak_files(dry_run: bool = False) -> None:
    """Remove all .bak files from the repository."""
    # Get the repository root (parent of scripts directory)
    repo_root = Path(__file__).parent.parent

    bak_files = find_bak_files(repo_root)

    if not bak_files:
        print("✅ No .bak files found. Repository is clean!")
        return

    print(f"Found {len(bak_files)} .bak file(s):")
    for file in bak_files:
        relative_path = file.relative_to(repo_root)
        print(f"  - {relative_path}")

    if dry_run:
        print("\n🔍 DRY RUN: No files were deleted.")
        print("Run without --dry-run to actually delete these files.")
    else:
        print(f"\n🗑️  Deleting {len(bak_files)} .bak file(s)...")
        for file in bak_files:
            try:
                file.unlink()
                print(f"  ✓ Deleted: {file.relative_to(repo_root)}")
            except Exception as e:
                print(f"  ✗ Error deleting {file.relative_to(repo_root)}: {e}")

        print("\n✅ Cleanup complete!")


def main():
    parser = argparse.ArgumentParser(description="Clean up .bak files created by automated tools")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = parser.parse_args()

    cleanup_bak_files(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
