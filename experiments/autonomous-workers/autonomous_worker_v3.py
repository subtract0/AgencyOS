#!/usr/bin/env python3
"""
Constitutional Autonomous Worker V3 - Real Code Quality Improvements

Focuses on:
1. Dict[Any, Any] violations (CRITICAL - constitutional)
2. Unresolved TODO/FIXME comments
3. Large files (>1000 lines) - refactoring suggestions
4. Wildcard imports

Uses vcoder-120b at 131k context window for intelligent fixes.
"""

import asyncio
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from openai import OpenAI


class ConstitutionalWorker:
    """Autonomous worker for constitutional code quality improvements."""

    def __init__(self):
        default_root = Path(__file__).resolve().parent
        self.project_root = Path(os.getenv("AGENCY_ROOT", default_root))
        llm_base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")

        self.client = OpenAI(
            base_url=llm_base_url,
            api_key="not-needed"
        )
        self.model = os.getenv("LLM_MODEL", "vcoder-120b-1.0-qx86-hi-mlx")
        self.log_file = self.project_root / "logs" / "constitutional_worker.log"
        self.fixes_applied = 0
        self.fixed_files: Set[str] = set()
        
        self.log_file.parent.mkdir(exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and level."""
        timestamp = datetime.now().isoformat()
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def scan_for_issues(self) -> Dict[str, List[str]]:
        """Scan codebase for constitutional violations and quality issues."""
        self.log("🔍 Scanning codebase for quality issues...")
        
        issues = {
            "dict_any_any": [],
            "todo_fixme": [],
            "large_files": [],
            "wildcard_imports": []
        }
        
        def run_search(primary: list[str], fallback: list[str]) -> subprocess.CompletedProcess[str]:
            try:
                result = subprocess.run(
                    primary,
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_root),
                )
                if result.returncode not in (0, 1):
                    raise RuntimeError("primary search failed")
                return result
            except (FileNotFoundError, RuntimeError):
                return subprocess.run(
                    fallback,
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_root),
                )

        # Find Dict[Any, Any] violations
        result = run_search(
            ["rg", "--files-with-matches", "--glob", "*.py", r"Dict\[Any, Any\]"],
            ["grep", "-r", "Dict\\[Any, Any\\]", "--include=*.py", "."],
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    file_path = line.split(':')[0]
                    if file_path not in issues["dict_any_any"]:
                        issues["dict_any_any"].append(file_path)
        
        # Find TODO/FIXME comments
        result = run_search(
            ["rg", "--files-with-matches", "--glob", "*.py", "(TODO|FIXME)"],
            ["grep", "-r", "-E", "TODO|FIXME", "--include=*.py", "."],
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    file_path = line.split(':')[0]
                    if file_path not in issues["todo_fixme"]:
                        issues["todo_fixme"].append(file_path)
        
        # Find large files (>1000 lines)
        for py_file in self.project_root.rglob("*.py"):
            try:
                lines = len(py_file.read_text().split('\n'))
                if lines > 1000:
                    issues["large_files"].append(str(py_file))
            except:
                pass
        
        # Find wildcard imports
        result = run_search(
            ["rg", "--files-with-matches", "--glob", "*.py", r"from .+ import \*"],
            ["grep", "-r", "from .* import \\*", "--include=*.py", "."],
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    file_path = line.split(':')[0]
                    if file_path not in issues["wildcard_imports"]:
                        issues["wildcard_imports"].append(file_path)
        
        total = sum(len(v) for v in issues.values())
        self.log(f"   Found {total} files with issues:")
        self.log(f"   - Dict[Any, Any]: {len(issues['dict_any_any'])}")
        self.log(f"   - TODO/FIXME: {len(issues['todo_fixme'])}")
        self.log(f"   - Large files: {len(issues['large_files'])}")
        self.log(f"   - Wildcard imports: {len(issues['wildcard_imports'])}")
        
        return issues
    
    async def fix_dict_any_any(self, file_path: str) -> bool:
        """Fix Dict[Any, Any] violations with proper Pydantic models."""
        self.log(f"🔧 Fixing Dict[Any, Any] in: {Path(file_path).name}")
        
        try:
            content = Path(file_path).read_text()
            
            # Count violations
            violations = content.count("Dict[Any, Any]")
            self.log(f"   Found {violations} Dict[Any, Any] violations")
            
            prompt = f"""Fix Dict[Any, Any] violations in this Python file by replacing them with properly typed Pydantic models or specific type hints.

RULES:
1. Replace Dict[Any, Any] with specific types like Dict[str, str], Dict[str, int], etc.
2. Or create Pydantic models with typed fields for complex structures
3. Use JSONValue from shared/type_definitions for truly dynamic JSON
4. Keep all other code exactly the same
5. Output ONLY the fixed Python code

File: {Path(file_path).name}
```python
{content}
```"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at Python type safety and Pydantic. Output ONLY code, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            fixed_code = response.choices[0].message.content
            
            # Extract code from markdown
            if "```python" in fixed_code:
                fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
            elif "```" in fixed_code:
                fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
            
            return await self.test_and_apply_fix(file_path, content, fixed_code, "Dict[Any, Any]")
            
        except Exception as e:
            self.log(f"   ❌ Error: {str(e)[:200]}", "ERROR")
            return False
    
    async def fix_todo_fixme(self, file_path: str) -> bool:
        """Resolve TODO/FIXME comments by implementing or removing them."""
        self.log(f"🔧 Resolving TODOs in: {Path(file_path).name}")
        
        try:
            content = Path(file_path).read_text()
            
            # Find TODO/FIXME comments
            todos = re.findall(r'#.*(?:TODO|FIXME).*', content)
            self.log(f"   Found {len(todos)} TODO/FIXME comments")
            
            if len(todos) > 5:
                self.log(f"   ⚠️ Too many TODOs ({len(todos)}), skipping for now", "WARN")
                return False
            
            prompt = f"""Resolve TODO/FIXME comments in this Python file by either:
1. Implementing the suggested improvement
2. Removing the comment if it's outdated/unnecessary
3. Converting to a proper issue tracker reference if it's complex

RULES:
1. Implement simple TODOs directly
2. Remove outdated TODOs with # RESOLVED: explanation
3. Keep all other code exactly the same
4. Output ONLY the fixed Python code

TODOs to address:
{chr(10).join(todos[:5])}

File: {Path(file_path).name}
```python
{content}
```"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at resolving technical debt. Output ONLY code, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            fixed_code = response.choices[0].message.content
            
            # Extract code from markdown
            if "```python" in fixed_code:
                fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
            elif "```" in fixed_code:
                fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
            
            return await self.test_and_apply_fix(file_path, content, fixed_code, "TODO/FIXME")
            
        except Exception as e:
            self.log(f"   ❌ Error: {str(e)[:200]}", "ERROR")
            return False
    
    async def test_and_apply_fix(self, file_path: str, original: str, fixed: str, issue_type: str) -> bool:
        """Test and apply a fix with validation."""
        self.log(f"🧪 Testing {issue_type} fix...")
        
        # Backup
        backup = Path(file_path + ".backup")
        backup.write_text(original)
        
        try:
            # Write fix
            Path(file_path).write_text(fixed)
            
            # Syntax check
            result = subprocess.run(
                ["python3", "-m", "py_compile", file_path],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.log(f"   ❌ Syntax error", "ERROR")
                Path(file_path).write_text(original)
                backup.unlink()
                return False
            
            self.log(f"   ✅ Syntax check passed")

            # ARTICLE II: Run test suite to verify fix doesn't break functionality
            self.log(f"   🧪 Running test suite (Article II compliance)...")

            # Determine test file path (e.g., tools/foo.py → tests/test_foo.py or tests/tools/test_foo.py)
            file_path_obj = Path(file_path)
            test_file_patterns = [
                self.project_root / "tests" / f"test_{file_path_obj.stem}.py",
                self.project_root / "tests" / file_path_obj.parent.name / f"test_{file_path_obj.stem}.py",
                self.project_root / "tests" / "unit" / file_path_obj.parent.name / f"test_{file_path_obj.stem}.py",
            ]

            # Find existing test file
            test_file = None
            for pattern in test_file_patterns:
                if pattern.exists():
                    test_file = pattern
                    break

            if test_file:
                # Run specific test file
                test_result = subprocess.run(
                    ["python", "-m", "pytest", str(test_file), "-xvs", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(self.project_root)
                )

                if test_result.returncode != 0:
                    self.log(f"   ❌ Tests FAILED (Article II violation)", "ERROR")
                    self.log(f"   Test output: {test_result.stdout[-500:]}", "ERROR")
                    # Rollback on test failure
                    Path(file_path).write_text(original)
                    backup.unlink()
                    return False

                self.log(f"   ✅ Tests passed (Article II compliant)")
            else:
                self.log(f"   ⚠️ No tests found for {file_path_obj.name} (Article II gap)", "WARN")
                # Still allow fix if no tests exist, but warn

            # Check issue is resolved
            if issue_type == "Dict[Any, Any]" and "Dict[Any, Any]" in fixed:
                # Allow some Dict[Any, Any] to remain if they're in comments
                code_only = '\n'.join(line for line in fixed.split('\n') if not line.strip().startswith('#'))
                if "Dict[Any, Any]" in code_only:
                    self.log(f"   ⚠️ Still contains Dict[Any, Any] in code", "WARN")
                    Path(file_path).write_text(original)
                    backup.unlink()
                    return False

            self.log(f"   ✅ {issue_type} resolved")
            backup.unlink()
            self.fixes_applied += 1
            self.fixed_files.add(file_path)
            return True
            
        except Exception as e:
            self.log(f"   ❌ Test failed: {e}", "ERROR")
            Path(file_path).write_text(original)
            if backup.exists():
                backup.unlink()
            return False
    
    async def work_cycle(self):
        """Single work cycle focusing on constitutional issues."""
        self.log("=" * 60)
        self.log("🏛️ Starting Constitutional Work Cycle")
        self.log("=" * 60)
        
        # Scan for issues
        issues = self.scan_for_issues()
        
        if not any(issues.values()):
            self.log("✅ No issues found - codebase is constitutionally compliant!", "SUCCESS")
            return False
        
        # Prioritize: Dict[str, Any] first (constitutional), then TODOs, then wildcards
        files_to_fix = []
        
        # Priority 1: Dict[str, Any] (constitutional violation)
        for file_path in issues["dict_any_any"][:3]:  # Batch of 3
            if file_path not in self.fixed_files:
                files_to_fix.append(("dict_any_any", file_path))
        
        # Priority 2: TODO/FIXME (technical debt)
        for file_path in issues["todo_fixme"][:2]:  # Batch of 2
            if file_path not in self.fixed_files and file_path not in [f[1] for f in files_to_fix]:
                files_to_fix.append(("todo_fixme", file_path))
        
        if not files_to_fix:
            self.log("✅ All prioritized issues fixed!", "SUCCESS")
            return False
        
        self.log(f"📋 Processing {len(files_to_fix)} files this cycle...")
        
        for issue_type, file_path in files_to_fix:
            if issue_type == "dict_any_any":
                await self.fix_dict_any_any(file_path)
            elif issue_type == "todo_fixme":
                await self.fix_todo_fixme(file_path)
        
        self.log(f"📊 Cycle complete: {self.fixes_applied} total fixes applied", "SUCCESS")
        return True
    
    async def run_forever(self):
        """Run worker continuously until all issues fixed."""
        self.log("🚀 Starting Constitutional Autonomous Worker V3", "INFO")
        self.log(f"   Model: {self.model}")
        self.log(f"   Project: {self.project_root}")
        self.log(f"   Focus: Constitutional compliance & code quality")
        self.log("")
        
        cycle_count = 0
        
        while cycle_count < 10:  # Max 10 cycles per session
            try:
                cycle_count += 1
                self.log(f"🔄 Cycle #{cycle_count}")
                
                has_more_work = await self.work_cycle()
                
                if not has_more_work:
                    self.log("🎉 ALL PRIORITY ISSUES RESOLVED!", "SUCCESS")
                    self.log(f"   Total fixes applied: {self.fixes_applied}")
                    break
                
                # Brief pause between cycles
                self.log("🔄 Next cycle in 3 seconds...")
                self.log("")
                await asyncio.sleep(3)
                
            except KeyboardInterrupt:
                self.log("🛑 Shutdown requested", "WARN")
                break
            except Exception as e:
                self.log(f"❌ Error in cycle: {e}", "ERROR")
                await asyncio.sleep(10)
        
        self.log(f"✅ Worker completed: {self.fixes_applied} total fixes", "SUCCESS")
        self.log("👋 Constitutional worker stopped")


async def main():
    worker = ConstitutionalWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
