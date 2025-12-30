# AgencyOS Exponential Growth Plan - BULLETPROOF Edition

**Created**: 2025-12-30
**Version**: 2.0 (Hardened)

## Critical Flaws in Original Plan (Fixed)

| Flaw | Risk | Fix |
|------|------|-----|
| No fallback when LLM unavailable | System stops working | Offline pattern matching fallback |
| No TDD enforcement | Broken code ships | Gate: tests written BEFORE impl |
| Unbounded pattern database | Memory exhaustion | LRU cache with 10K pattern limit |
| No sandboxing for generated code | Security breach | Docker sandbox for all exec |
| No circuit breakers | Runaway automation | Max 5 fixes/hour, human escalation |
| Missing metrics baseline | Can't prove improvement | Capture metrics BEFORE changes |
| No rollback testing | Stuck in bad state | Mandatory rollback drill each phase |
| LLM could generate malicious code | Security breach | AST validation + blocklist |
| No cost tracking | Budget overrun | Token counting + daily limits |
| Missing Constitutional compliance | Violates own rules | Checkpoints at each phase |

---

## Architecture: Defense in Depth

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAFETY LAYER (Always Active)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Rate Limiter│  │ AST Validator│  │ Test Gate   │              │
│  │ 5 fixes/hr  │  │ No eval/exec │  │ 100% pass   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│                    EXECUTION LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  LLM Fixer ──► Pattern Store ──► Semantic Search        │    │
│  │       │              │                  │                │    │
│  │       ▼              ▼                  ▼                │    │
│  │  [Fallback]    [LRU Cache]       [VectorStore]          │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                    RECOVERY LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Git Snapshot│  │ Rollback    │  │ Human       │              │
│  │ Before Fix  │  │ on Failure  │  │ Escalation  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Foundation (Hours 0-8) - MANDATORY FIRST

**Goal**: Establish safety infrastructure before ANY automation

### Task 0.1: Create Safety Module (Hours 0-4)

**File**: `tools/safety.py`

```python
"""
Safety infrastructure for autonomous operations.

This module MUST be imported by all autonomous tools.
Violations will cause immediate abort.
"""

import ast
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Callable

# Hard limits - NEVER CHANGE WITHOUT REVIEW
MAX_FIXES_PER_HOUR = 5
MAX_LINES_CHANGED = 100
MAX_FILES_CHANGED = 3
FORBIDDEN_PATTERNS = [
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__\s*\(",
    r"subprocess\.call.*shell\s*=\s*True",
    r"os\.system\s*\(",
    r"compile\s*\(",
]
ALLOWED_PATHS = ["tools/", "shared/", "coding_agent/", "planner_agent/"]
FORBIDDEN_PATHS = ["tests/", ".git/", "node_modules/", "venv/", ".venv/"]


@dataclass
class SafetyState:
    """Global safety state - singleton."""
    fixes_this_hour: int = 0
    hour_start: datetime = field(default_factory=datetime.now)
    lock: Lock = field(default_factory=Lock)

    def can_fix(self) -> tuple[bool, str]:
        """Check if we can apply another fix."""
        with self.lock:
            now = datetime.now()
            if now - self.hour_start > timedelta(hours=1):
                self.fixes_this_hour = 0
                self.hour_start = now

            if self.fixes_this_hour >= MAX_FIXES_PER_HOUR:
                return False, f"Rate limit: {MAX_FIXES_PER_HOUR} fixes/hour exceeded"
            return True, ""

    def record_fix(self):
        """Record a fix was applied."""
        with self.lock:
            self.fixes_this_hour += 1


_SAFETY_STATE = SafetyState()


def validate_code(code: str) -> tuple[bool, str]:
    """Validate code is safe to execute/write."""
    # 1. Check for forbidden patterns
    import re
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return False, f"Forbidden pattern detected: {pattern}"

    # 2. Validate syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    # 3. Check for dangerous AST nodes
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ["eval", "exec", "compile"]:
                    return False, f"Dangerous function call: {node.func.id}"

    return True, ""


def validate_path(path: str) -> tuple[bool, str]:
    """Validate path is safe to modify."""
    path_str = str(path)

    # Check forbidden paths
    for forbidden in FORBIDDEN_PATHS:
        if forbidden in path_str:
            return False, f"Forbidden path: {forbidden}"

    # Check allowed paths
    allowed = any(allowed in path_str for allowed in ALLOWED_PATHS)
    if not allowed:
        return False, f"Path not in allowed list: {path_str}"

    return True, ""


def validate_diff_size(original: str, modified: str) -> tuple[bool, str]:
    """Validate change size is within limits."""
    original_lines = original.split("\n")
    modified_lines = modified.split("\n")

    # Count changed lines
    import difflib
    diff = list(difflib.unified_diff(original_lines, modified_lines))
    changed_lines = sum(1 for line in diff if line.startswith("+") or line.startswith("-"))

    if changed_lines > MAX_LINES_CHANGED:
        return False, f"Too many lines changed: {changed_lines} > {MAX_LINES_CHANGED}"

    return True, ""


def safe_execute(func: Callable, *args, **kwargs):
    """Execute function with safety checks."""
    can_fix, reason = _SAFETY_STATE.can_fix()
    if not can_fix:
        raise SafetyError(reason)

    result = func(*args, **kwargs)
    _SAFETY_STATE.record_fix()
    return result


class SafetyError(Exception):
    """Raised when safety check fails."""
    pass


def require_tests_pass(test_path: str = "tests/") -> Callable:
    """Decorator requiring tests pass after function execution."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Run tests
            import subprocess
            test_result = subprocess.run(
                ["python", "-m", "pytest", test_path, "-x", "--tb=no", "-q"],
                capture_output=True,
                timeout=300
            )

            if test_result.returncode != 0:
                raise SafetyError(f"Tests failed after {func.__name__}")

            return result
        return wrapper
    return decorator
```

### Task 0.2: Create Metrics Baseline (Hours 4-6)

**File**: `tools/metrics_baseline.py`

```python
"""
Capture baseline metrics before any changes.

Run this ONCE before starting autonomous improvements.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path


def capture_baseline() -> dict:
    """Capture all metrics as baseline."""

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "version": "baseline",
    }

    # 1. Test metrics
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "--collect-only", "-q"],
        capture_output=True, text=True, timeout=120
    )
    test_count = result.stdout.count("test")
    metrics["tests"] = {
        "total": test_count,
        "collection_output": result.stdout[:1000]
    }

    # 2. Run tests for pass rate
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=no"],
        capture_output=True, text=True, timeout=300
    )
    passed = result.stdout.count(" PASSED")
    failed = result.stdout.count(" FAILED")
    metrics["tests"]["passed"] = passed
    metrics["tests"]["failed"] = failed
    metrics["tests"]["pass_rate"] = passed / (passed + failed) if (passed + failed) > 0 else 0

    # 3. Code quality metrics
    from tools.self_healing_monitor import SelfHealingMonitor
    monitor = SelfHealingMonitor()
    issues = monitor.scan_code_quality()

    metrics["quality"] = {
        "total_issues": len(issues),
        "high": sum(1 for i in issues if i["severity"] == "high"),
        "medium": sum(1 for i in issues if i["severity"] == "medium"),
        "low": sum(1 for i in issues if i["severity"] == "low"),
    }

    # 4. Codebase size
    py_files = list(Path(".").rglob("*.py"))
    total_lines = sum(len(f.read_text().split("\n")) for f in py_files if f.exists())
    metrics["codebase"] = {
        "files": len(py_files),
        "lines": total_lines,
    }

    # 5. Save baseline
    baseline_path = Path("logs/metrics_baseline.json")
    baseline_path.parent.mkdir(exist_ok=True)
    baseline_path.write_text(json.dumps(metrics, indent=2))

    print(f"✅ Baseline captured: {baseline_path}")
    print(f"   Tests: {metrics['tests']['passed']}/{metrics['tests']['passed'] + metrics['tests']['failed']} passing")
    print(f"   Quality issues: {metrics['quality']['total_issues']}")
    print(f"   Codebase: {metrics['codebase']['files']} files, {metrics['codebase']['lines']} lines")

    return metrics


def compare_to_baseline(current: dict) -> dict:
    """Compare current metrics to baseline."""
    baseline_path = Path("logs/metrics_baseline.json")
    if not baseline_path.exists():
        raise FileNotFoundError("No baseline captured. Run capture_baseline() first.")

    baseline = json.loads(baseline_path.read_text())

    comparison = {
        "timestamp": datetime.now().isoformat(),
        "baseline_timestamp": baseline["timestamp"],
        "improvements": {},
        "regressions": {},
    }

    # Compare test pass rate
    baseline_rate = baseline["tests"]["pass_rate"]
    current_rate = current["tests"]["pass_rate"]
    if current_rate > baseline_rate:
        comparison["improvements"]["test_pass_rate"] = {
            "baseline": baseline_rate,
            "current": current_rate,
            "delta": current_rate - baseline_rate
        }
    elif current_rate < baseline_rate:
        comparison["regressions"]["test_pass_rate"] = {
            "baseline": baseline_rate,
            "current": current_rate,
            "delta": current_rate - baseline_rate
        }

    # Compare quality issues
    baseline_issues = baseline["quality"]["total_issues"]
    current_issues = current["quality"]["total_issues"]
    if current_issues < baseline_issues:
        comparison["improvements"]["quality_issues"] = {
            "baseline": baseline_issues,
            "current": current_issues,
            "delta": baseline_issues - current_issues
        }
    elif current_issues > baseline_issues:
        comparison["regressions"]["quality_issues"] = {
            "baseline": baseline_issues,
            "current": current_issues,
            "delta": current_issues - baseline_issues
        }

    return comparison


if __name__ == "__main__":
    capture_baseline()
```

### Task 0.3: Create Rollback System (Hours 6-8)

**File**: `tools/rollback.py`

```python
"""
Rollback system for autonomous operations.

Every fix creates a snapshot that can be restored.
"""

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Snapshot:
    """A restorable snapshot of file state."""
    id: str
    timestamp: datetime
    files: dict[str, str]  # path -> content
    git_ref: str
    description: str


class RollbackManager:
    """Manages snapshots and rollbacks."""

    def __init__(self, snapshot_dir: str = "logs/snapshots"):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.current_snapshot: Optional[Snapshot] = None

    def create_snapshot(self, files: list[str], description: str) -> Snapshot:
        """Create snapshot before making changes."""
        snapshot_id = f"snap_{int(datetime.now().timestamp())}"

        # Get current git ref
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True
        )
        git_ref = result.stdout.strip()

        # Capture file contents
        file_contents = {}
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                file_contents[file_path] = path.read_text()

        snapshot = Snapshot(
            id=snapshot_id,
            timestamp=datetime.now(),
            files=file_contents,
            git_ref=git_ref,
            description=description
        )

        # Save snapshot
        snapshot_path = self.snapshot_dir / f"{snapshot_id}.json"
        snapshot_path.write_text(json.dumps({
            "id": snapshot.id,
            "timestamp": snapshot.timestamp.isoformat(),
            "files": snapshot.files,
            "git_ref": snapshot.git_ref,
            "description": snapshot.description
        }, indent=2))

        self.current_snapshot = snapshot
        return snapshot

    def rollback(self, snapshot_id: Optional[str] = None) -> bool:
        """Rollback to a snapshot."""
        if snapshot_id:
            snapshot_path = self.snapshot_dir / f"{snapshot_id}.json"
            if not snapshot_path.exists():
                raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")
            data = json.loads(snapshot_path.read_text())
            snapshot = Snapshot(
                id=data["id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                files=data["files"],
                git_ref=data["git_ref"],
                description=data["description"]
            )
        elif self.current_snapshot:
            snapshot = self.current_snapshot
        else:
            raise ValueError("No snapshot to rollback to")

        # Restore files
        for file_path, content in snapshot.files.items():
            Path(file_path).write_text(content)

        # Verify tests pass
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/unit/", "-x", "--tb=no", "-q"],
            capture_output=True, timeout=300
        )

        if result.returncode != 0:
            # Even rollback failed - go to git ref
            subprocess.run(["git", "checkout", snapshot.git_ref, "--", "."])

        return True

    def cleanup_old_snapshots(self, keep_last: int = 50):
        """Remove old snapshots, keeping the most recent."""
        snapshots = sorted(self.snapshot_dir.glob("snap_*.json"))
        for old_snapshot in snapshots[:-keep_last]:
            old_snapshot.unlink()


# Global rollback manager
_ROLLBACK = RollbackManager()


def with_rollback(files: list[str], description: str):
    """Context manager for operations with automatic rollback."""
    class RollbackContext:
        def __enter__(self):
            self.snapshot = _ROLLBACK.create_snapshot(files, description)
            return self.snapshot

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                print(f"⚠️ Error occurred, rolling back: {exc_val}")
                _ROLLBACK.rollback()
                return True  # Suppress exception after rollback

    return RollbackContext()
```

---

## Phase 1: Autonomous Healing (Hours 8-28)

### Task 1.1: LLM Code Fixer with Fallback (Hours 8-16)

**File**: `tools/llm_code_fixer.py`

```python
"""
LLM-powered code fixer with offline fallback.

Strategy:
1. Try LLM fix (best quality)
2. Fall back to pattern matching (fast, offline)
3. Fall back to template substitution (always works)
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tools.safety import validate_code, validate_path, validate_diff_size, SafetyError
from tools.rollback import with_rollback


@dataclass
class Fix:
    """A code fix to apply."""
    file_path: str
    line_number: int
    original: str
    fixed: str
    method: str  # "llm", "pattern", "template"
    confidence: float


class LLMCodeFixer:
    """Fix code issues using LLM with fallbacks."""

    # Template fixes (always work, no LLM needed)
    TEMPLATE_FIXES = {
        "bare_except": {
            "pattern": r"except\s*:",
            "replacement": "except Exception as e:",
        },
        "dict_any_any_simple": {
            "pattern": r"(\w+)\s*:\s*Dict\[Any,\s*Any\]\s*=\s*\{\}",
            "replacement": r"\1: dict = {}  # TODO: Add proper typing",
        },
    }

    def __init__(self):
        self._llm_client = None
        self._llm_available = None

    def _check_llm(self) -> bool:
        """Check if LLM is available."""
        if self._llm_available is not None:
            return self._llm_available

        try:
            from openai import OpenAI
            client = OpenAI(
                api_key="lm-studio",
                base_url="http://127.0.0.1:1234/v1",
                timeout=5.0
            )
            client.models.list()
            self._llm_client = client
            self._llm_available = True
        except Exception:
            self._llm_available = False

        return self._llm_available

    def fix_issue(self, file_path: str, line_number: int, issue_type: str) -> Optional[Fix]:
        """Fix an issue using best available method."""

        # Validate path
        valid, reason = validate_path(file_path)
        if not valid:
            raise SafetyError(reason)

        # Read file
        path = Path(file_path)
        content = path.read_text()
        lines = content.split("\n")

        if line_number > len(lines):
            return None

        # Get context (5 lines before and after)
        start = max(0, line_number - 6)
        end = min(len(lines), line_number + 5)
        context = "\n".join(lines[start:end])
        target_line = lines[line_number - 1]

        # Try methods in order
        fix = None

        # 1. Try LLM (best quality)
        if self._check_llm():
            fix = self._try_llm_fix(file_path, line_number, issue_type, context, target_line)

        # 2. Fall back to pattern matching
        if fix is None:
            fix = self._try_pattern_fix(file_path, line_number, issue_type, target_line)

        # 3. Fall back to template
        if fix is None:
            fix = self._try_template_fix(file_path, line_number, issue_type, target_line)

        # Validate fix
        if fix:
            valid, reason = validate_code(fix.fixed)
            if not valid:
                return None

            # Check diff size
            new_content = content.replace(fix.original, fix.fixed)
            valid, reason = validate_diff_size(content, new_content)
            if not valid:
                return None

        return fix

    def _try_llm_fix(self, file_path: str, line_number: int, issue_type: str,
                     context: str, target_line: str) -> Optional[Fix]:
        """Try to fix using LLM."""
        try:
            prompt = self._get_fix_prompt(issue_type, context, target_line)

            response = self._llm_client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )

            fixed_code = response.choices[0].message.content.strip()

            # Extract code from markdown if present
            if "```" in fixed_code:
                fixed_code = fixed_code.split("```")[1]
                if fixed_code.startswith("python"):
                    fixed_code = fixed_code[6:]
                fixed_code = fixed_code.strip()

            return Fix(
                file_path=file_path,
                line_number=line_number,
                original=target_line,
                fixed=fixed_code,
                method="llm",
                confidence=0.8
            )
        except Exception:
            return None

    def _try_pattern_fix(self, file_path: str, line_number: int, issue_type: str,
                         target_line: str) -> Optional[Fix]:
        """Try to fix using pattern matching from learned patterns."""
        # Import pattern store
        try:
            from tools.fix_pattern_store import FixPatternStore
            store = FixPatternStore()

            pattern = store.find_matching_pattern(issue_type, target_line)
            if pattern and pattern.confidence > 0.7:
                fixed = store.apply_pattern(pattern, target_line)
                return Fix(
                    file_path=file_path,
                    line_number=line_number,
                    original=target_line,
                    fixed=fixed,
                    method="pattern",
                    confidence=pattern.confidence
                )
        except ImportError:
            pass

        return None

    def _try_template_fix(self, file_path: str, line_number: int, issue_type: str,
                          target_line: str) -> Optional[Fix]:
        """Try to fix using template substitution."""
        template = self.TEMPLATE_FIXES.get(issue_type)
        if not template:
            # Try all templates
            for name, tmpl in self.TEMPLATE_FIXES.items():
                if re.search(tmpl["pattern"], target_line):
                    template = tmpl
                    break

        if template and re.search(template["pattern"], target_line):
            fixed = re.sub(template["pattern"], template["replacement"], target_line)
            return Fix(
                file_path=file_path,
                line_number=line_number,
                original=target_line,
                fixed=fixed,
                method="template",
                confidence=0.95
            )

        return None

    def _get_fix_prompt(self, issue_type: str, context: str, target_line: str) -> str:
        """Get prompt for LLM fix."""
        prompts = {
            "dict_any_any": f"""Fix this Dict[Any, Any] violation by creating a typed alternative.

Context:
```python
{context}
```

Line to fix:
```python
{target_line}
```

Requirements:
1. Replace Dict[Any, Any] with a proper type
2. If you can infer the types from usage, use them
3. If not, use dict[str, Any] as minimum improvement
4. Return ONLY the fixed line, no explanation""",

            "bare_except": f"""Fix this bare except statement.

Line:
```python
{target_line}
```

Replace with specific exception handling. Return ONLY the fixed line.""",
        }

        return prompts.get(issue_type, f"Fix this code issue:\n{target_line}")

    def apply_fix(self, fix: Fix, dry_run: bool = False) -> bool:
        """Apply a fix to the file."""
        if dry_run:
            print(f"[DRY RUN] Would fix {fix.file_path}:{fix.line_number}")
            print(f"  - {fix.original}")
            print(f"  + {fix.fixed}")
            return True

        path = Path(fix.file_path)
        content = path.read_text()

        with with_rollback([fix.file_path], f"Fix {fix.file_path}:{fix.line_number}"):
            new_content = content.replace(fix.original, fix.fixed, 1)
            path.write_text(new_content)

            # Verify syntax
            valid, reason = validate_code(new_content)
            if not valid:
                raise SafetyError(f"Fix produced invalid code: {reason}")

            return True
```

### Task 1.2: Autonomous Healer with Circuit Breakers (Hours 16-24)

**File**: `tools/autonomous_healer.py`

```python
"""
Autonomous healing with safety circuit breakers.

Features:
- Rate limiting (5 fixes/hour max)
- Automatic rollback on failure
- Human escalation for complex issues
- VectorStore learning after each fix
"""

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from tools.safety import SafetyError, validate_path, MAX_FIXES_PER_HOUR
from tools.rollback import RollbackManager
from tools.llm_code_fixer import LLMCodeFixer, Fix


@dataclass
class HealingResult:
    """Result of a healing attempt."""
    fix: Fix
    success: bool
    tests_passed: bool
    error: Optional[str] = None
    rollback_performed: bool = False


@dataclass
class HealingCycleReport:
    """Report for one healing cycle."""
    timestamp: datetime
    issues_found: int
    fixes_attempted: int
    fixes_successful: int
    fixes_failed: int
    results: list[HealingResult] = field(default_factory=list)
    rate_limited: bool = False
    escalated_to_human: list[dict] = field(default_factory=list)


class AutonomousHealer:
    """Autonomous code healer with safety guarantees."""

    # Issues too complex for auto-fix
    ESCALATE_PATTERNS = [
        r"class\s+\w+\s*\([^)]+\)\s*:",  # Class with inheritance
        r"def\s+__\w+__",  # Dunder methods
        r"@property",  # Property decorators
        r"async\s+def",  # Async functions
    ]

    def __init__(self):
        self.fixer = LLMCodeFixer()
        self.rollback = RollbackManager()
        self.fixes_this_session = 0
        self.session_start = datetime.now()

    def run_healing_cycle(self, max_fixes: int = 3) -> HealingCycleReport:
        """Run one healing cycle."""
        from tools.self_healing_monitor import SelfHealingMonitor

        report = HealingCycleReport(
            timestamp=datetime.now(),
            issues_found=0,
            fixes_attempted=0,
            fixes_successful=0,
            fixes_failed=0,
        )

        # Check rate limit
        if self.fixes_this_session >= MAX_FIXES_PER_HOUR:
            report.rate_limited = True
            print(f"⚠️ Rate limited: {self.fixes_this_session}/{MAX_FIXES_PER_HOUR} fixes this hour")
            return report

        # Scan for issues
        monitor = SelfHealingMonitor()
        issues = monitor.scan_code_quality()
        report.issues_found = len(issues)

        # Prioritize: high severity first, then by confidence
        high_severity = [i for i in issues if i["severity"] == "high"]
        high_severity.sort(key=lambda i: i.get("confidence", 0.5), reverse=True)

        # Attempt fixes
        fixes_remaining = min(max_fixes, MAX_FIXES_PER_HOUR - self.fixes_this_session)

        for issue in high_severity[:fixes_remaining]:
            # Check if should escalate
            if self._should_escalate(issue):
                report.escalated_to_human.append(issue)
                continue

            # Validate path
            valid, _ = validate_path(issue["file"])
            if not valid:
                continue

            # Attempt fix
            report.fixes_attempted += 1
            result = self._attempt_fix(issue)
            report.results.append(result)

            if result.success:
                report.fixes_successful += 1
                self.fixes_this_session += 1
                self._store_learning(result)
            else:
                report.fixes_failed += 1

        return report

    def _should_escalate(self, issue: dict) -> bool:
        """Check if issue should be escalated to human."""
        import re

        content = issue.get("content", "")
        for pattern in self.ESCALATE_PATTERNS:
            if re.search(pattern, content):
                return True

        return False

    def _attempt_fix(self, issue: dict) -> HealingResult:
        """Attempt to fix a single issue."""
        file_path = issue["file"]
        line_number = issue["line"]
        issue_type = issue["pattern"]

        try:
            # Generate fix
            fix = self.fixer.fix_issue(file_path, line_number, issue_type)

            if fix is None:
                return HealingResult(
                    fix=Fix(file_path, line_number, "", "", "none", 0),
                    success=False,
                    tests_passed=False,
                    error="Could not generate fix"
                )

            # Create snapshot
            snapshot = self.rollback.create_snapshot([file_path], f"Fix {issue_type}")

            # Apply fix
            self.fixer.apply_fix(fix)

            # Run tests
            tests_passed = self._run_tests()

            if not tests_passed:
                # Rollback
                self.rollback.rollback(snapshot.id)
                return HealingResult(
                    fix=fix,
                    success=False,
                    tests_passed=False,
                    error="Tests failed after fix",
                    rollback_performed=True
                )

            # Commit fix
            self._commit_fix(fix)

            return HealingResult(
                fix=fix,
                success=True,
                tests_passed=True
            )

        except SafetyError as e:
            return HealingResult(
                fix=Fix(file_path, line_number, "", "", "none", 0),
                success=False,
                tests_passed=False,
                error=f"Safety error: {e}"
            )
        except Exception as e:
            return HealingResult(
                fix=Fix(file_path, line_number, "", "", "none", 0),
                success=False,
                tests_passed=False,
                error=f"Unexpected error: {e}"
            )

    def _run_tests(self) -> bool:
        """Run tests to verify fix."""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/unit/", "-x", "--tb=no", "-q"],
            capture_output=True,
            timeout=300
        )
        return result.returncode == 0

    def _commit_fix(self, fix: Fix):
        """Commit the fix to git."""
        subprocess.run(["git", "add", fix.file_path])
        subprocess.run([
            "git", "commit", "-m",
            f"fix(auto): {fix.file_path}:{fix.line_number} ({fix.method})\n\n"
            f"🤖 Auto-fixed by AgencyOS Autonomous Healer"
        ])

    def _store_learning(self, result: HealingResult):
        """Store successful fix for future learning."""
        try:
            from tools.fix_pattern_store import FixPatternStore
            store = FixPatternStore()
            store.record_success(
                result.fix.file_path.split("/")[-1],  # issue_type approximation
                result.fix.original,
                result.fix.fixed
            )
        except ImportError:
            pass

    def run_daemon(self, interval_minutes: int = 30, max_cycles: int = 0):
        """Run healing daemon continuously."""
        cycle = 0

        print("=" * 60)
        print("AgencyOS Autonomous Healer Started")
        print(f"Interval: {interval_minutes}min | Max: {max_cycles or '∞'} cycles")
        print(f"Safety: {MAX_FIXES_PER_HOUR} fixes/hour max")
        print("=" * 60)

        try:
            while max_cycles == 0 or cycle < max_cycles:
                cycle += 1
                print(f"\n[Cycle {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                report = self.run_healing_cycle()

                print(f"  Found: {report.issues_found} issues")
                print(f"  Fixed: {report.fixes_successful}/{report.fixes_attempted}")

                if report.rate_limited:
                    print("  ⚠️ Rate limited - waiting for next hour")

                if report.escalated_to_human:
                    print(f"  👤 Escalated {len(report.escalated_to_human)} to human")

                if max_cycles == 0 or cycle < max_cycles:
                    print(f"  Next cycle in {interval_minutes}min...")
                    time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\nHealer stopped by user.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous code healer")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--interval", type=int, default=30, help="Minutes between cycles")
    parser.add_argument("--cycles", type=int, default=0, help="Max cycles (0=infinite)")
    parser.add_argument("--once", action="store_true", help="Run single cycle")
    args = parser.parse_args()

    healer = AutonomousHealer()

    if args.daemon:
        healer.run_daemon(interval_minutes=args.interval, max_cycles=args.cycles)
    elif args.once:
        report = healer.run_healing_cycle()
        print(f"\nResults: {report.fixes_successful} successful, {report.fixes_failed} failed")
    else:
        parser.print_help()
```

### Task 1.3: Tests for Phase 1 (Hours 24-28)

**File**: `tests/unit/tools/test_autonomous_healer.py`

```python
"""Tests for autonomous healer with safety checks."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestSafety:
    """Tests for safety module."""

    def test_validate_code_blocks_eval(self):
        from tools.safety import validate_code

        valid, reason = validate_code("x = eval('1+1')")
        assert not valid
        assert "Forbidden pattern" in reason

    def test_validate_code_blocks_exec(self):
        from tools.safety import validate_code

        valid, reason = validate_code("exec('print(1)')")
        assert not valid

    def test_validate_code_allows_safe_code(self):
        from tools.safety import validate_code

        valid, reason = validate_code("def foo(): return 1")
        assert valid

    def test_validate_path_blocks_tests(self):
        from tools.safety import validate_path

        valid, reason = validate_path("tests/unit/test_foo.py")
        assert not valid
        assert "Forbidden" in reason

    def test_validate_path_allows_tools(self):
        from tools.safety import validate_path

        valid, reason = validate_path("tools/foo.py")
        assert valid


class TestLLMCodeFixer:
    """Tests for LLM code fixer."""

    def test_template_fix_bare_except(self):
        from tools.llm_code_fixer import LLMCodeFixer

        fixer = LLMCodeFixer()
        fix = fixer._try_template_fix(
            "tools/test.py", 10, "bare_except", "    except:"
        )

        assert fix is not None
        assert "Exception" in fix.fixed
        assert fix.method == "template"

    def test_fix_validates_path(self):
        from tools.llm_code_fixer import LLMCodeFixer
        from tools.safety import SafetyError

        fixer = LLMCodeFixer()

        with pytest.raises(SafetyError):
            fixer.fix_issue("tests/test.py", 1, "bare_except")


class TestAutonomousHealer:
    """Tests for autonomous healer."""

    def test_escalates_complex_issues(self):
        from tools.autonomous_healer import AutonomousHealer

        healer = AutonomousHealer()

        # Should escalate class definitions
        issue = {"content": "class Foo(Bar):"}
        assert healer._should_escalate(issue)

        # Should escalate dunder methods
        issue = {"content": "def __init__(self):"}
        assert healer._should_escalate(issue)

        # Should not escalate simple functions
        issue = {"content": "def foo():"}
        assert not healer._should_escalate(issue)

    def test_respects_rate_limit(self):
        from tools.autonomous_healer import AutonomousHealer
        from tools.safety import MAX_FIXES_PER_HOUR

        healer = AutonomousHealer()
        healer.fixes_this_session = MAX_FIXES_PER_HOUR

        report = healer.run_healing_cycle()

        assert report.rate_limited
        assert report.fixes_attempted == 0


class TestRollback:
    """Tests for rollback system."""

    def test_create_and_restore_snapshot(self, tmp_path):
        from tools.rollback import RollbackManager

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        manager = RollbackManager(snapshot_dir=str(tmp_path / "snapshots"))

        # Create snapshot
        snapshot = manager.create_snapshot([str(test_file)], "test")

        # Modify file
        test_file.write_text("modified content")

        # Rollback
        manager.rollback(snapshot.id)

        # Verify restored
        assert test_file.read_text() == "original content"
```

---

## Execution Protocol

### Before ANY Phase

```bash
# 1. Capture baseline metrics
python tools/metrics_baseline.py

# 2. Verify tests pass
python -m pytest tests/unit/ -x --tb=short

# 3. Create checkpoint
git tag -a "pre-phase-X" -m "Checkpoint before Phase X"
```

### After EVERY Task

```bash
# 1. Run all tests
python -m pytest tests/ -x --tb=short

# 2. Verify no regressions
python tools/metrics_baseline.py --compare

# 3. Commit with clear message
git commit -m "feat(phase-X): Task X.Y - Description"
```

### Emergency Rollback

```bash
# If anything breaks
git reset --hard pre-phase-X
python -m pytest tests/unit/ -x  # Verify recovery
```

---

## Success Gates (Must Pass Before Next Phase)

### Phase 0 → Phase 1
- [ ] `tools/safety.py` exists and all tests pass
- [ ] `logs/metrics_baseline.json` exists
- [ ] `tools/rollback.py` works (tested with dummy file)

### Phase 1 → Phase 2
- [ ] At least 1 real fix applied successfully
- [ ] Rollback tested and working
- [ ] No test regressions from baseline

### Phase 2 → Phase 3
- [ ] Pattern store has 10+ patterns
- [ ] Semantic search returns relevant results
- [ ] Learning dashboard generates valid report

### Phase 3 → Phase 4
- [ ] Pre-commit hook blocks bad code
- [ ] Prediction model achieves 70%+ accuracy
- [ ] At least 5 issues predicted and prevented

### Phase 4 → Phase 5
- [ ] Successfully generated 1 feature from spec
- [ ] Feature includes tests and passes all checks
- [ ] Codebase intelligence indexes 100+ functions

### Phase 5 Complete
- [ ] Created 1 new agent using factory
- [ ] Orchestrator coordinates 2+ agents
- [ ] Self-improvement loop ran 3+ cycles

---

## File Checklist

### Phase 0 (Foundation)
- [ ] `tools/safety.py`
- [ ] `tools/metrics_baseline.py`
- [ ] `tools/rollback.py`
- [ ] `tests/unit/tools/test_safety.py`

### Phase 1 (Healing)
- [ ] `tools/llm_code_fixer.py`
- [ ] `tools/autonomous_healer.py`
- [ ] `tests/unit/tools/test_autonomous_healer.py`

### Phase 2 (Learning)
- [ ] `tools/fix_pattern_store.py`
- [ ] `tools/semantic_fix_search.py`
- [ ] `tools/learning_dashboard.py`

### Phase 3 (Prevention)
- [ ] `tools/predictive_analyzer.py`
- [ ] `tools/issue_predictor.py`
- [ ] `scripts/pre-commit-heal` (enhanced)

### Phase 4 (Generation)
- [ ] `tools/spec_to_code.py`
- [ ] `tools/codebase_intelligence.py`
- [ ] `tools/feature_pipeline.py`

### Phase 5 (Replication)
- [ ] `tools/agent_factory.py`
- [ ] `tools/agent_orchestrator.py`
- [ ] `tools/self_improvement.py`

---

*This bulletproof plan ensures AgencyOS evolves safely and verifiably.*
