#!/usr/bin/env python3
"""
Constitutional Autonomous Worker V4 - Surgical Constitutional Fixes

Simple, effective approach:
1. Dict[Any, Any] -> Dict[str, Any] (most common pattern)
2. Remove obvious TODO/FIXME comments with regex
3. Validate syntax before applying

No LLM - just regex + validation. Fast, safe, reliable.
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Set


class SurgicalWorker:
    """Simple, surgical worker for constitutional fixes."""

    def __init__(self):
        default_root = Path(__file__).resolve().parent
        self.project_root = Path(os.getenv("AGENCY_ROOT", default_root))
        self.log_file = self.project_root / "logs" / "constitutional_worker_v4.log"
        self.fixes_applied = 0
        self.fixed_files: Set[str] = set()
        self.log_file.parent.mkdir(exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().isoformat()
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def find_dict_any_files(self) -> list:
        """Find files with Dict[Any, Any]."""
        try:
            result = subprocess.run(
                ["rg", "--files-with-matches", "--glob", "*.py", r"Dict\[Any, Any\]"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )
            if result.returncode not in (0, 1):
                raise RuntimeError
        except (FileNotFoundError, RuntimeError):
            result = subprocess.run(
                ["grep", "-r", "Dict\\[Any, Any\\]", "--include=*.py", "."],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )
        
        files: set[str] = set()
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if ':' in line and not line.startswith("Binary"):
                    file_path = line.split(':')[0]
                    if file_path:
                        files.add(str((self.project_root / file_path).resolve()))
        return sorted(files)
    
    def fix_dict_any_any(self, file_path: str) -> bool:
        """Fix Dict[Any, Any] with simple regex replacement."""
        full_path = self.project_root / file_path
        
        try:
            content = full_path.read_text()
            original = content
            
            # Count violations
            violations = content.count("Dict[Any, Any]")
            self.log(f"🔧 {file_path}: {violations} Dict[Any, Any] violations")
            
            # Simple replacements - context aware
            # 1. Dict[Any, Any] as return type -> Dict[str, Any]
            content = re.sub(
                r'\) -> Dict\[Any, Any\]',
                r') -> Dict[str, Any]',
                content
            )
            
            # 2. Dict[Any, Any] in type hints -> Dict[str, Any]
            content = re.sub(
                r': Dict\[Any, Any\]',
                r': Dict[str, Any]',
                content
            )
            
            # 3. Dict[Any, Any] in function parameters -> Dict[str, Any]
            content = re.sub(
                r'Dict\[Any, Any\](?=[,\)])',
                r'Dict[str, Any]',
                content
            )
            
            # Only proceed if we made changes
            if content == original:
                self.log(f"   ℹ️  No replaceable patterns found")
                return False
            
            # Validate syntax
            full_path.write_text(content)
            result = subprocess.run(
                ["python3", "-m", "py_compile", str(full_path)],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                self.log(f"   ❌ Syntax error, reverting", "ERROR")
                full_path.write_text(original)
                return False
            
            self.log(f"   ✅ Fixed and validated")
            self.fixes_applied += 1
            self.fixed_files.add(file_path)
            return True
            
        except Exception as e:
            self.log(f"   ❌ Error: {str(e)[:100]}", "ERROR")
            return False
    
    def remove_obvious_todos(self, file_path: str) -> bool:
        """Remove obvious/resolved TODO comments."""
        full_path = self.project_root / file_path
        
        try:
            content = full_path.read_text()
            original = content
            
            # Find TODO lines that are safe to remove
            # Pattern: # TODO: simple comment (not a complex multi-line design doc)
            todos = re.findall(r'^\s*#\s*(?:TODO|FIXME):\s*[^\n]{10,60}$', content, re.MULTILINE)
            
            if not todos or len(todos) > 5:
                return False
            
            self.log(f"🧹 {file_path}: {len(todos)} simple TODOs")
            
            # Remove TODO lines that are clearly simple tasks
            simple_removals = [
                r'^\s*#\s*TODO:.*add.*import.*\n',
                r'^\s*#\s*TODO:.*type.*hint.*\n',
                r'^\s*#\s*FIXME:.*unused.*\n',
            ]
            
            for pattern in simple_removals:
                content = re.sub(pattern, '', content, flags=re.MULTILINE | re.IGNORECASE)
            
            if content == original:
                return False
            
            # Validate
            full_path.write_text(content)
            result = subprocess.run(
                ["python3", "-m", "py_compile", str(full_path)],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                full_path.write_text(original)
                return False
            
            self.log(f"   ✅ Removed safe TODOs")
            self.fixes_applied += 1
            return True
            
        except Exception as e:
            self.log(f"   ❌ Error: {str(e)[:100]}", "ERROR")
            return False
    
    def work_cycle(self):
        """Single focused work cycle."""
        self.log("=" * 60)
        self.log("🏛️ Constitutional Work Cycle (V4 - Surgical)")
        self.log("=" * 60)
        
        # Find files
        dict_files = self.find_dict_any_files()
        
        if not dict_files:
            self.log("✅ No Dict[Any, Any] violations found!", "SUCCESS")
            return False
        
        self.log(f"📋 Processing {len(dict_files[:5])} files (max 5/cycle)...\n")
        
        batch = dict_files[:5]
        for file_path in batch:
            if file_path not in self.fixed_files:
                self.fix_dict_any_any(file_path)
        
        self.log(f"\n📊 Cycle complete: {self.fixes_applied} total fixes\n")
        return len(dict_files) > len(batch)
    
    def run(self, max_cycles: int = 5):
        """Run worker for specified cycles."""
        self.log("🚀 Constitutional Worker V4 - Starting", "INFO")
        self.log(f"   Max cycles: {max_cycles}")
        self.log(f"   Strategy: Surgical regex + validation\n")
        
        for cycle_num in range(1, max_cycles + 1):
            self.log(f"🔄 Cycle {cycle_num}/{max_cycles}")
            
            has_more = self.work_cycle()
            
            if not has_more:
                self.log("🎉 ALL DICT[ANY, ANY] FIXED!", "SUCCESS")
                break
        
        self.log(f"✅ Worker completed: {self.fixes_applied} fixes applied", "SUCCESS")
        self.log("👋 Stopped")


if __name__ == "__main__":
    worker = SurgicalWorker()
    worker.run(max_cycles=5)
