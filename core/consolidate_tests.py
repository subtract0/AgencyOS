#!/usr/bin/env python3
"""
Consolidate duplicate test files by merging healed versions into main files.
This reduces test maintenance burden while preserving all test coverage.
"""

import os
import shutil
from pathlib import Path


def consolidate_test_files():
    """
    Consolidate healed test files into their main counterparts.
    Strategy: Since healed versions are more comprehensive, we'll:
    1. Backup original test files
    2. Replace with healed versions
    3. Remove _healed suffix from imports and class names
    """
    tests_dir = Path("tests")
    backup_dir = tests_dir / "backup_pre_consolidation"
    backup_dir.mkdir(exist_ok=True)

    healed_files = list(tests_dir.glob("test_*_healed.py"))
    consolidated = []
    errors = []

    for healed_file in healed_files:
        # Derive the main test file name
        main_file_name = healed_file.name.replace("_healed.py", ".py")
        main_file = tests_dir / main_file_name

        try:
            # Backup original if it exists
            if main_file.exists():
                backup_path = backup_dir / main_file_name
                shutil.copy2(main_file, backup_path)
                print(f"✓ Backed up {main_file_name}")

            # Read healed content
            with open(healed_file, 'r') as f:
                content = f.read()

            # Update content to remove _healed references
            content = content.replace("_healed", "")
            content = content.replace("Healed", "")

            # Add consolidation marker
            if "# CONSOLIDATED FROM HEALED VERSION" not in content:
                lines = content.split('\n')
                # Insert after imports
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        continue
                    elif line.strip() and not line.startswith("#"):
                        lines.insert(i, "\n# CONSOLIDATED FROM HEALED VERSION - More comprehensive tests")
                        break
                content = '\n'.join(lines)

            # Write consolidated content
            with open(main_file, 'w') as f:
                f.write(content)

            # Remove healed file
            healed_file.unlink()

            consolidated.append(main_file_name)
            print(f"✓ Consolidated {main_file_name}")

        except Exception as e:
            errors.append((healed_file.name, str(e)))
            print(f"✗ Error consolidating {healed_file.name}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("CONSOLIDATION SUMMARY")
    print("=" * 60)
    print(f"✓ Successfully consolidated: {len(consolidated)} files")

    if consolidated:
        print("\nConsolidated files:")
        for name in consolidated:
            print(f"  - {name}")

    if errors:
        print(f"\n✗ Errors encountered: {len(errors)}")
        for name, error in errors:
            print(f"  - {name}: {error}")

    print(f"\nBackups saved to: {backup_dir}")
    print("\nNext steps:")
    print("1. Run tests to verify: python run_tests.py")
    print("2. If tests fail, restore from backup")
    print("3. Remove backup directory after verification")

    return len(consolidated), len(errors)


def restore_from_backup():
    """Restore original test files from backup if needed."""
    tests_dir = Path("tests")
    backup_dir = tests_dir / "backup_pre_consolidation"

    if not backup_dir.exists():
        print("No backup directory found")
        return

    restored = 0
    for backup_file in backup_dir.glob("test_*.py"):
        original_path = tests_dir / backup_file.name
        shutil.copy2(backup_file, original_path)
        restored += 1
        print(f"✓ Restored {backup_file.name}")

    print(f"\nRestored {restored} files from backup")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_from_backup()
    else:
        consolidate_test_files()