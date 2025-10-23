#!/usr/bin/env python3
"""
Convert JUnit XML to runtime_cache.json for V5 auditor.

Usage:
    python scripts/convert_junit_to_cache.py .audit/junit.xml .audit/runtime_cache.json
"""

import sys
import json
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from runtime_data_parser import RuntimeDataParser

def main():
    junit_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.audit/junit.xml')
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('.audit/runtime_cache.json')
    
    if not junit_path.exists():
        print(f"❌ JUnit XML not found: {junit_path}")
        print(f"   Generate with: pytest tests/ --junitxml={junit_path}")
        sys.exit(1)
    
    # Parse JUnit XML
    parser = RuntimeDataParser()
    runtimes = parser.parse_junitxml(junit_path)
    
    if not runtimes:
        print(f"⚠️  No runtime data extracted from {junit_path}")
        sys.exit(1)
    
    # Convert to cache format
    cache = {
        "version": "1.0",
        "source": "junitxml",
        "test_count": len(runtimes),
        "runtimes": {}
    }
    
    for test_id, duration in runtimes.items():
        cache["runtimes"][test_id] = {
            "duration_seconds": duration,
            "source": "junitxml"
        }
    
    # Save cache
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f"✅ Runtime cache generated: {output_path}")
    print(f"   Tests: {len(runtimes)}")
    print(f"   Total runtime: {sum(runtimes.values()):.1f}s")
    print(f"\n🎯 Now run: python scripts/test_value_audit.py")
    print(f"   Expected: V5_FULL mode with accurate runtime penalties")

if __name__ == "__main__":
    main()
