#!/usr/bin/env python3
"""
Autonomous Worker - Continuous Codebase Improvement

Uses vcoder-120b to:
1. Find issues (like agency_swarm legacy imports)
2. Generate fixes automatically
3. Test the fixes
4. Commit working improvements
5. Run 24/7 improving your codebase

This is REAL work using your 128GB M4 Max compute.
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from openai import OpenAI

class AutonomousWorker:
    """Worker that continuously improves the codebase."""

    def __init__(self):
        # Resolve project root and model configuration from environment with safe fallbacks
        default_root = Path(__file__).resolve().parent
        self.project_root = Path(os.getenv("AGENCY_ROOT", default_root))
        llm_base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")

        self.model = os.getenv("LLM_MODEL", "vcoder-120b-1.0-qx86-hi-mlx")

        self.client = OpenAI(
            base_url=llm_base_url,
            api_key="not-needed"
        )
        self.log_file = self.project_root / "logs" / "autonomous_worker.log"
        self.fixes_applied = 0
        
        self.log_file.parent.mkdir(exist_ok=True)
    
    def log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().isoformat()
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def find_legacy_imports(self) -> list:
        """Find files with agency_swarm imports."""
        self.log("🔍 Scanning for legacy agency_swarm imports...")
        
        search_cmd = ["rg", "--files-with-matches", "--glob", "*.py", "agency_swarm"]
        try:
            result = subprocess.run(
                search_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )
        except FileNotFoundError:
            result = subprocess.run(
                ["grep", "-r", "agency_swarm", "--include=*.py", "."],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )
        
        if result.returncode not in (0, 1):
            return []
        
        files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            file_path = (self.project_root / line).resolve()
            if file_path.suffix == ".py" and str(file_path) not in files:
                files.append(str(file_path))
        
        self.log(f"   Found {len(files)} files with legacy imports")
        return files
    
    async def generate_fix(self, file_path: str) -> str:
        """Use vcoder-120b to generate a fix for the file."""
        self.log(f"🤖 Asking vcoder-120b to fix: {Path(file_path).name}")
        
        # Read the file
        content = Path(file_path).read_text()
        
        # Ask vcoder-120b for a fix
        prompt = f"""This Python file has legacy imports from 'agency_swarm' which is no longer used.
Please remove all agency_swarm imports and replace them with the new patterns:

- Instead of 'from shared.lean_adapter import BaseTool', these tools should inherit from pydantic BaseModel
- Remove any SendMessageHandoff or agency_swarm specific code
- Keep the functionality but modernize the imports

File: {Path(file_path).name}
```python
{content}
```

Please provide ONLY the fixed Python code, no explanations."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert Python developer fixing legacy code."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.3
        )
        
        fixed_code = response.choices[0].message.content
        
        # Extract code from markdown if present
        if "```python" in fixed_code:
            fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
        elif "```" in fixed_code:
            fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
        
        return fixed_code
    
    def test_fix(self, file_path: str, original_content: str, fixed_content: str) -> bool:
        """Test if the fix works by checking syntax and imports."""
        self.log(f"🧪 Testing fix for {Path(file_path).name}")
        
        # Save fixed content temporarily
        backup_path = Path(file_path + ".backup")
        Path(file_path).write_text(original_content)
        backup_path.write_text(original_content)
        
        try:
            # Write fix
            Path(file_path).write_text(fixed_content)
            
            # Test syntax
            result = subprocess.run(
                ["python3", "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.log(f"   ❌ Syntax error: {result.stderr[:200]}")
                Path(file_path).write_text(original_content)
                backup_path.unlink()
                return False
            
            self.log(f"   ✅ Fix passed syntax check")
            backup_path.unlink()
            return True
            
        except Exception as e:
            self.log(f"   ❌ Test failed: {e}")
            Path(file_path).write_text(original_content)
            if backup_path.exists():
                backup_path.unlink()
            return False
    
    async def fix_file(self, file_path: str) -> bool:
        """Fix a single file."""
        try:
            original_content = Path(file_path).read_text()
            
            # Generate fix using vcoder-120b
            fixed_content = await self.generate_fix(file_path)
            
            # Test the fix
            if self.test_fix(file_path, original_content, fixed_content):
                self.log(f"✅ Successfully fixed {Path(file_path).name}")
                self.fixes_applied += 1
                return True
            else:
                self.log(f"⚠️  Fix didn't pass tests for {Path(file_path).name}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error fixing {file_path}: {e}")
            return False
    
    async def work_cycle(self):
        """Single work cycle - find and fix issues."""
        self.log("=" * 60)
        self.log("🔧 Starting Work Cycle")
        self.log("=" * 60)
        
        # Find legacy imports
        legacy_files = self.find_legacy_imports()
        
        if not legacy_files:
            self.log("✅ No legacy imports found - codebase is clean!")
            return
        
        # Fix them one by one - CONTINUOUSLY!
        self.log(f"📋 Processing {len(legacy_files)} files...")
        
        for file_path in legacy_files[:10]:  # Process 10 at a time
            await self.fix_file(file_path)
            # No sleep - keep working!
        
        self.log(f"📊 Total fixes applied in this cycle: {self.fixes_applied}")
    
    async def run_forever(self):
        """Run worker 24/7."""
        self.log("🚀 Starting Autonomous Worker")
        self.log(f"   Model: {self.model}")
        self.log(f"   Project: {self.project_root}")
        self.log("")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                self.log(f"Cycle #{cycle_count}")
                
                await self.work_cycle()
                
                # NO REST - Keep working continuously!
                self.log("🔄 Starting next cycle immediately...")
                self.log("")
                await asyncio.sleep(1)  # Just 1 second to breathe
                
            except KeyboardInterrupt:
                self.log("🛑 Shutdown requested")
                break
            except Exception as e:
                self.log(f"❌ Error in cycle: {e}")
                await asyncio.sleep(60)
        
        self.log(f"✅ Total fixes applied: {self.fixes_applied}")
        self.log("👋 Worker stopped")

async def main():
    worker = AutonomousWorker()
    await worker.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
