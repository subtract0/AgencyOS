#!/usr/bin/env python3
"""
Migration validation script for PR #28: SpaceX-style De-bloating
Ensures all removed modules are properly replaced with their new counterparts.
"""

import os
import sys
from pathlib import Path

# Add the project root to sys.path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_memory_migration() -> tuple[bool, list[str]]:
    """Verify all memory operations use enhanced_memory_store."""
    issues = []

    # Check that memory_v2.py is removed
    if Path("memory_v2.py").exists():
        issues.append("ERROR: memory_v2.py still exists")

    # Verify enhanced_memory_store is importable
    try:
        from agency_memory.enhanced_memory_store import EnhancedMemoryStore

        print("✅ EnhancedMemoryStore is accessible")
    except ImportError as e:
        issues.append(f"ERROR: Cannot import EnhancedMemoryStore: {e}")

    # Verify swarm_memory is preserved for agent features
    try:
        from agency_memory.swarm_memory import SwarmMemory

        print("✅ SwarmMemory preserved for agent features")
    except ImportError as e:
        issues.append(f"ERROR: Cannot import SwarmMemory: {e}")

    return len(issues) == 0, issues


def check_pattern_migration() -> tuple[bool, list[str]]:
    """Verify pattern system migration to pattern_intelligence."""
    issues = []

    # Check that core/patterns.py is removed
    if Path("core/patterns.py").exists():
        issues.append("ERROR: core/patterns.py still exists")

    # Verify pattern_intelligence module is functional
    try:
        from pattern_intelligence import CodingPattern
        from pattern_intelligence.pattern_store import PatternStore

        print("✅ Pattern Intelligence module is accessible")
    except ImportError as e:
        issues.append(f"ERROR: Cannot import from pattern_intelligence: {e}")

    # Check for any remaining imports of old pattern system
    try:
        from core.patterns import Pattern  # This should fail

        issues.append("ERROR: core.patterns.Pattern is still importable")
    except ImportError:
        print("✅ Legacy Pattern class properly removed")

    return len(issues) == 0, issues


def check_removed_modules() -> tuple[bool, list[str]]:
    """Verify all intended removals are complete."""
    removed_files = [
        "memory_v2.py",
        "core/patterns.py",
        "core/unified_edit.py",
        "pattern_intelligence/migration.py",
    ]

    removed_dirs = ["demos/archive", "examples", "subagent_example"]

    issues = []

    for file_path in removed_files:
        if Path(file_path).exists():
            issues.append(f"ERROR: {file_path} should be removed but still exists")
        else:
            print(f"✅ {file_path} successfully removed")

    for dir_path in removed_dirs:
        if Path(dir_path).exists():
            issues.append(f"ERROR: {dir_path}/ should be removed but still exists")
        else:
            print(f"✅ {dir_path}/ successfully removed")

    return len(issues) == 0, issues


def check_imports_updated() -> tuple[bool, list[str]]:
    """Verify all imports are updated to new modules."""
    issues = []
    python_files = Path(".").rglob("*.py")

    deprecated_imports = [
        "from core.patterns import",
        "import core.patterns",
        "from memory_v2 import",
        "import memory_v2",
        "from pattern_intelligence.migration import",
        "import pattern_intelligence.migration",
    ]

    for py_file in python_files:
        # Skip virtual env, cache, and this validation script itself
        if (
            ".venv" in str(py_file)
            or "__pycache__" in str(py_file)
            or "validate_migration.py" in str(py_file)
        ):
            continue

        try:
            content = py_file.read_text()
            for deprecated in deprecated_imports:
                # Check if it's an actual import, not a comment
                for line in content.split("\n"):
                    if deprecated in line and not line.strip().startswith("#"):
                        issues.append(f"ERROR: {py_file} contains deprecated import: {deprecated}")
                        break  # Only report once per file/import combo
        except Exception:
            pass  # Skip files we can't read

    if not issues:
        print("✅ No deprecated imports found")

    return len(issues) == 0, issues


def main():
    """Run all migration validations."""
    print("=" * 60)
    print("Migration Validation for PR #28: SpaceX-style De-bloating")
    print("=" * 60)
    print()

    all_passed = True
    all_issues = []

    # Run all checks
    checks = [
        ("Memory System Migration", check_memory_migration),
        ("Pattern System Migration", check_pattern_migration),
        ("Module Removals", check_removed_modules),
        ("Import Updates", check_imports_updated),
    ]

    for check_name, check_func in checks:
        print(f"\n📋 Checking: {check_name}")
        print("-" * 40)
        passed, issues = check_func()

        if not passed:
            all_passed = False
            all_issues.extend(issues)
            for issue in issues:
                print(f"  ❌ {issue}")

    # Final summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL MIGRATION VALIDATIONS PASSED!")
        print("The codebase has been successfully de-bloated.")
        print("All removed modules have proper replacements.")
        return 0
    else:
        print("❌ MIGRATION VALIDATION FAILED")
        print(f"Found {len(all_issues)} issue(s) that need attention:")
        for issue in all_issues:
            print(f"  • {issue}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
