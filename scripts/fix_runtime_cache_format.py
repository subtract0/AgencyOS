#!/usr/bin/env python3
"""
Fix Runtime Cache Format - Convert legacy format to V5 schema.

Legacy format:
{
  "test_id": {"duration": 0.123}
}

V5 format:
{
  "version": "1.0",
  "source": "junitxml",
  "test_count": N,
  "runtimes": {
    "test_id": {
      "duration_seconds": 0.123,
      "source": "junitxml"
    }
  }
}

Usage:
    python scripts/fix_runtime_cache_format.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def normalize_test_id(test_id: str) -> str:
    """
    Normalize JUnit XML test ID to pytest format.

    JUnit format: tests.adr.test_foo.TestClass::test_method
    Pytest format: tests/adr/test_foo.py::TestClass::test_method

    Args:
        test_id: Test identifier from JUnit XML

    Returns:
        Normalized pytest-style test ID
    """
    if "::" not in test_id:
        return test_id

    # Split by ::
    parts = test_id.split("::")
    dotted_path = parts[0]  # e.g., "tests.adr.test_foo.TestClass"
    rest = parts[1:]  # e.g., ["test_method"]

    # Split the dotted path
    path_components = dotted_path.split(".")

    # Find the test file (component starting with "test_")
    # Everything up to and including this is the file path
    test_file_idx = -1
    for i, component in enumerate(path_components):
        if component.startswith("test_"):
            test_file_idx = i
            break

    if test_file_idx == -1:
        # No test file found, return as-is
        return test_id

    # File path components (e.g., ["tests", "adr", "test_foo"])
    file_components = path_components[:test_file_idx + 1]
    # Class components (e.g., ["TestClass"])
    class_components = path_components[test_file_idx + 1:]

    # Build pytest path: tests/adr/test_foo.py
    file_path = "/".join(file_components) + ".py"

    # Build full test ID
    if class_components:
        # Has class: tests/adr/test_foo.py::TestClass::test_method
        return f"{file_path}::{'::'.join(class_components + rest)}"
    else:
        # No class: tests/adr/test_foo.py::test_method
        return f"{file_path}::{'::'.join(rest)}"


def convert_legacy_to_v5(legacy_cache: dict) -> dict:
    """
    Convert legacy cache format to V5 schema.

    Args:
        legacy_cache: Dict with format {test_id: {duration: float}}

    Returns:
        V5 format dict with metadata and runtimes
    """
    v5_cache = {
        "version": "1.0",
        "source": "junitxml",
        "generated_at": datetime.now().isoformat(),
        "test_count": 0,
        "runtimes": {}
    }

    # Convert each entry
    for test_id, entry in legacy_cache.items():
        if isinstance(entry, dict):
            # Legacy format with dict
            duration = entry.get("duration", 0.0)
        elif isinstance(entry, (int, float)):
            # Very old format: direct float value
            duration = float(entry)
        else:
            print(f"⚠️  Skipping invalid entry: {test_id}")
            continue

        # Normalize test ID to pytest format
        normalized_id = normalize_test_id(test_id)

        v5_cache["runtimes"][normalized_id] = {
            "duration_seconds": duration,
            "source": "junitxml"
        }

    v5_cache["test_count"] = len(v5_cache["runtimes"])

    return v5_cache


def main():
    cache_path = Path(".audit/runtime_cache.json")
    backup_path = Path(".audit/runtime_cache_legacy_backup.json")

    if not cache_path.exists():
        print(f"❌ Cache file not found: {cache_path}")
        print("   Run: pytest tests/ --junitxml=.audit/junit.xml")
        print("   Then: python scripts/convert_junit_to_cache.py")
        sys.exit(1)

    # Load legacy cache
    print(f"📂 Loading legacy cache: {cache_path}")
    try:
        with open(cache_path, 'r') as f:
            legacy_cache = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in cache file: {e}")
        sys.exit(1)

    # Check if already in V5 format
    if "version" in legacy_cache and "runtimes" in legacy_cache:
        print("✅ Cache is already in V5 format")
        print(f"   Version: {legacy_cache['version']}")
        print(f"   Test count: {legacy_cache.get('test_count', 0)}")
        print(f"   Source: {legacy_cache.get('source', 'unknown')}")
        return

    print(f"🔧 Converting legacy cache ({len(legacy_cache)} entries) to V5 format...")

    # Create backup
    print(f"💾 Creating backup: {backup_path}")
    with open(backup_path, 'w') as f:
        json.dump(legacy_cache, f, indent=2)

    # Convert to V5
    v5_cache = convert_legacy_to_v5(legacy_cache)

    # Save V5 cache
    print(f"💾 Saving V5 cache: {cache_path}")
    with open(cache_path, 'w') as f:
        json.dump(v5_cache, f, indent=2)

    # Report results
    print(f"\n✅ Conversion complete!")
    print(f"   Version: {v5_cache['version']}")
    print(f"   Source: {v5_cache['source']}")
    print(f"   Test count: {v5_cache['test_count']}")
    print(f"   Total runtime: {sum(r['duration_seconds'] for r in v5_cache['runtimes'].values()):.1f}s")
    print(f"\n📋 Backup saved to: {backup_path}")
    print(f"\n🎯 Next step: python scripts/verify_v5_calibration.py")


if __name__ == "__main__":
    main()
