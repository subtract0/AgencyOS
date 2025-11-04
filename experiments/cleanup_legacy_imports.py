#!/usr/bin/env python3
"""
Surgical cleanup of remaining agency_swarm imports.
Fast, safe, and constitutional-compliant.
"""

import subprocess
import sys
from pathlib import Path


def find_legacy_files():
    """Find all files with agency_swarm imports."""
    result = subprocess.run(
        ["grep", "-r", "from agency_swarm", "--include=*.py", "."],
        capture_output=True,
        text=True,
        cwd="/Users/am/Code/AgencyOS"
    )
    
    if result.returncode != 0:
        return []
    
    files = set()
    for line in result.stdout.strip().split('\n'):
        if ':' in line:
            file_path = line.split(':')[0]
            # Skip worker scripts and comments
            if 'autonomous_worker' not in file_path and '.pyc' not in file_path:
                files.add(file_path)
    
    return sorted(files)


def fix_file(file_path: str) -> bool:
    """Fix a single file with surgical replacements."""
    print(f"🔧 Fixing: {file_path}")
    
    try:
        path = Path(file_path)
        content = path.read_text()
        original = content
        
        # Surgical replacements
        replacements = [
            ("from pydantic import BaseModel", "from pydantic import BaseModel"),
            ("from pydantic import BaseModel as Tool", "from pydantic import BaseModel as Tool"),
            ("(BaseModel)", "(BaseModel)"),
            ("class BaseModel", "class BaseModel"),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        # Only write if changed
        if content != original:
            path.write_text(content)
            
            # Validate syntax
            result = subprocess.run(
                ["python3", "-m", "py_compile", file_path],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"  ❌ Syntax error, reverting")
                path.write_text(original)
                return False
            
            # Check no more agency_swarm
            if "from agency_swarm" in content:
                print(f"  ⚠️  Still has agency_swarm imports")
                return False
            
            print(f"  ✅ Fixed successfully")
            return True
        else:
            print(f"  ℹ️  No changes needed (likely comment only)")
            return True
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Main cleanup routine."""
    print("🚀 Starting surgical cleanup of legacy imports")
    print("=" * 60)
    
    files = find_legacy_files()
    
    if not files:
        print("✅ No legacy imports found!")
        return 0
    
    print(f"📋 Found {len(files)} files to fix\n")
    
    fixed = 0
    failed = 0
    
    for file_path in files:
        if fix_file(file_path):
            fixed += 1
        else:
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Results: {fixed} fixed, {failed} failed")
    
    # Final verification
    remaining = find_legacy_files()
    print(f"🔍 Remaining legacy imports: {len(remaining)}")
    
    if remaining:
        print("\n⚠️  Still have legacy imports in:")
        for f in remaining:
            print(f"  - {f}")
        return 1
    else:
        print("\n🎉 ALL LEGACY IMPORTS REMOVED!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
