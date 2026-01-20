#!/usr/bin/env python3
"""
scripts/migrate_patterns_to_new_memory.py

Migrates existing patterns from various locations to the new PatternMemory format.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agency_memory.pattern_memory import get_pattern_memory, Pattern

def migrate_pattern_extraction_report(source: Path) -> int:
    """Migrate patterns from pattern_extraction_report format."""
    if not source.exists():
        print(f"  Skipping {source} (not found)")
        return 0

    data = json.loads(source.read_text())
    migrated = 0

    all_patterns = (
        data.get("high_confidence_patterns", []) +
        data.get("medium_confidence_patterns", [])
    )

    memory = get_pattern_memory()

    for p in all_patterns:
        pattern_id = p.get("pattern_id", f"unknown_{migrated}")

        # Construct new Pattern object
        new_pattern = Pattern(
            id=pattern_id,
            content=p.get("pattern", p),
            tags=p.get("tags", []),
            confidence=p.get("confidence", 0.7),
            evidence_count=p.get("evidence_count", 1),
            created_at=data.get("extraction_metadata", {}).get("extraction_date", datetime.now().isoformat()),
            updated_at=datetime.now().isoformat(),
            schema_version=1,
        )

        memory.store(new_pattern)
        print(f"  ✓ Migrated: {pattern_id}")
        migrated += 1

    return migrated


def migrate_session_learnings(source: Path) -> int:
    """Migrate patterns from session_learnings format."""
    if not source.exists():
        print(f"  Skipping {source} (not found)")
        return 0

    data = json.loads(source.read_text())
    migrated = 0
    memory = get_pattern_memory()

    for p in data.get("patterns_extracted", []):
        pattern_id = p.get("pattern_type", f"session_{migrated}")

        new_pattern = Pattern(
            id=pattern_id,
            content={
                "description": p.get("description", ""),
                "fix_strategy": p.get("fix_strategy", ""),
            },
            tags=p.get("tags", []),
            confidence=p.get("confidence", 0.7),
            evidence_count=p.get("evidence_count", p.get("frequency", 1)),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            schema_version=1,
        )

        memory.store(new_pattern)
        print(f"  ✓ Migrated: {pattern_id}")
        migrated += 1

    return migrated


def main():
    print("=" * 60)
    print("Pattern Migration to New Memory Architecture")
    print("=" * 60)

    total = 0

    # Source 1: Pattern extraction report
    print("1. Migrating pattern_extraction_report...")
    source1 = Path("logs/learning/pattern_extraction_report_2025_10_24.json")
    total += migrate_pattern_extraction_report(source1)

    # Source 2: Session learnings
    print("\n2. Migrating session_learnings...")
    source2 = Path("/tmp/session_learnings.json")
    total += migrate_session_learnings(source2)

    print(f"\n{'=' * 60}")
    print(f"Migration complete: {total} patterns migrated")
    print(f"{'=' * 60}")
    
    # Verify via Memory
    memory = get_pattern_memory()
    stats = memory.stats()
    print(f"\nVerification:")
    print(f"  Total Patterns: {stats['total_patterns']}")
    print(f"  Storage Path: {stats['storage_path']}")


if __name__ == "__main__":
    main()
