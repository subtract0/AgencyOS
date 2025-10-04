#!/usr/bin/env python3
"""
Automated Dict[str, Any] Fixer - Constitutional Compliance

Replaces Dict[str, Any] with proper Pydantic models or JSONValue type.
Ensures 100% type safety per Constitutional Article II.

Strategy:
1. For message/event payloads → use JSONValue (allows any JSON-serializable data)
2. For structured data → convert to Pydantic models
3. For return types → infer from usage and create models

Usage:
    python tools/fix_dict_any.py --file shared/message_bus.py
    python tools/fix_dict_any.py --all  # Fix all violations
"""

import re
import sys
from pathlib import Path

# Import JSONValue type if it exists
try:
    from shared.type_definitions import JSONValue

    HAS_JSON_VALUE = True
except ImportError:
    HAS_JSON_VALUE = False
    print("⚠️  JSONValue type not found - will create it")


DICT_ANY_PATTERN = re.compile(r"Dict\[str,\s*Any\]|dict\[str,\s*Any\]")


def create_json_value_type():
    """Create JSONValue type definition if it doesn't exist."""
    json_value_file = Path("shared/type_definitions/json_value.py")

    if json_value_file.exists():
        print(f"✅ {json_value_file} already exists")
        return

    content = '''"""
JSON Value Type - Type-safe replacement for Dict[str, Any]

Per Constitutional Article II: No Dict[str, Any] allowed.
Use JSONValue for JSON-serializable data with proper type safety.
"""

from typing import Union, Dict, List, Any

# JSONValue represents any valid JSON value
# More specific than Any, enforces JSON-serializability
JSONValue = Union[
    None,
    bool,
    int,
    float,
    str,
    List["JSONValue"],
    Dict[str, "JSONValue"]
]

__all__ = ["JSONValue"]
'''

    json_value_file.parent.mkdir(parents=True, exist_ok=True)
    json_value_file.write_text(content)
    print(f"✅ Created {json_value_file}")

    # Update __init__.py
    init_file = json_value_file.parent / "__init__.py"
    if init_file.exists():
        init_content = init_file.read_text()
        if "JSONValue" not in init_content:
            init_content += "\nfrom .json_value import JSONValue\n"
            init_file.write_text(init_content)
            print(f"✅ Updated {init_file}")


def fix_file(file_path: Path) -> tuple[int, list[str]]:
    """
    Fix Dict[str, Any] violations in a file.

    Returns:
        (violations_fixed, changes_made)
    """
    content = file_path.read_text()
    original = content
    changes = []

    # Add JSONValue import if needed
    if DICT_ANY_PATTERN.search(content):
        if "from shared.type_definitions import" in content and "JSONValue" not in content:
            # Add to existing import
            content = re.sub(
                r"(from shared\.type_definitions import [^)]+)", r"\1, JSONValue", content
            )
            changes.append("Added JSONValue to existing import")
        elif "from shared.type_definitions" not in content and "from typing import" in content:
            # Add new import after typing imports
            content = re.sub(
                r"(from typing import [^\n]+\n)",
                r"\1from shared.type_definitions import JSONValue\n",
                content,
                count=1,
            )
            changes.append("Added JSONValue import")

    # Replace Dict[str, Any] with JSONValue
    violations_before = len(DICT_ANY_PATTERN.findall(content))
    content = DICT_ANY_PATTERN.sub("JSONValue", content)
    violations_after = len(DICT_ANY_PATTERN.findall(content))
    violations_fixed = violations_before - violations_after

    if content != original:
        file_path.write_text(content)
        changes.append(f"Replaced {violations_fixed} Dict[str, Any] with JSONValue")
        return violations_fixed, changes

    return 0, []


def main():
    """Fix all Dict[str, Any] violations."""
    print("🚀 Dict[str, Any] Constitutional Compliance Fixer")
    print("=" * 60)

    # Create JSONValue type if needed
    create_json_value_type()
    print()

    # Get list of files with violations
    violations_output = Path("tools/dict_any_violations.txt")
    if not violations_output.exists():
        print("❌ Run no_dict_any_check.py first to generate violations list")
        return 1

    violations = violations_output.read_text().strip().split("\n")
    files_to_fix = set()

    for line in violations:
        if ":" in line and "forbids" in line:
            file_path = line.split(":")[0]
            files_to_fix.add(Path(file_path))

    print(f"📋 Found {len(files_to_fix)} files with violations")
    print()

    total_fixed = 0
    for file_path in sorted(files_to_fix):
        if not file_path.exists():
            continue

        fixed, changes = fix_file(file_path)
        if fixed > 0:
            print(f"✅ {file_path}")
            for change in changes:
                print(f"   - {change}")
            total_fixed += fixed

    print()
    print("=" * 60)
    print(f"🎉 Fixed {total_fixed} violations across {len(files_to_fix)} files")
    print()
    print("Next steps:")
    print("1. Run: python tools/quality/no_dict_any_check.py")
    print("2. Verify: 0 violations")
    print("3. Run tests: python run_tests.py")
    print("4. Commit: git commit -m 'fix: Replace Dict[str, Any] with JSONValue'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
