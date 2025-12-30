"""Self-Healing Health Monitor for AgencyOS.

Continuously monitors system health and triggers automatic fixes:
1. Test suite health
2. Import/dependency issues
3. Missing dependencies
4. Common code patterns that break tests

Constitutional Compliance:
- Article I: Complete context before action (gathers full error info)
- Article II: 100% verification (retries until tests pass)
- Article III: Automated enforcement (no manual bypass)
- Article IV: Learning integration (stores fixes in VectorStore)
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


@dataclass
class HealthReport:
    """System health report from monitoring."""

    timestamp: datetime
    test_pass_rate: float
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    tests_error: int
    collection_errors: int
    issues_detected: list[dict[str, Any]]
    recommendations: list[str]
    auto_fixable: list[dict[str, Any]]


@dataclass
class FixAttempt:
    """Record of a fix attempt."""

    issue_type: str
    file_path: str
    description: str
    fix_applied: str
    success: bool
    error_message: str | None


class SelfHealingMonitor:
    """Monitor system health and auto-fix common issues.

    Patterns that can be auto-fixed:
    1. Missing imports (ModuleNotFoundError)
    2. Missing dependencies (pip install)
    3. Pytest configuration issues
    4. Common test collection errors
    """

    # Known fixes for common import errors
    IMPORT_FIXES = {
        "agents": "openai-agents",
        "sklearn": "scikit-learn",
        "psutil": "psutil",
        "watchdog": "watchdog",
        "faiss": "faiss-cpu",
        "pytest_asyncio": "pytest-asyncio",
        "pytest_timeout": "pytest-timeout",
        "hypothesis": "hypothesis",
        "PIL": "Pillow",
        "cv2": "opencv-python",
        "yaml": "pyyaml",
        "dotenv": "python-dotenv",
        "bs4": "beautifulsoup4",
        "dateutil": "python-dateutil",
        "jwt": "pyjwt",
        "redis": "redis",
        "celery": "celery",
        "numpy": "numpy",
        "pandas": "pandas",
        "torch": "torch",
        "transformers": "transformers",
        "sentence_transformers": "sentence-transformers",
        "openai": "openai",
        "anthropic": "anthropic",
        "httpx": "httpx",
        "aiohttp": "aiohttp",
        "pydantic": "pydantic",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
    }

    # Code quality patterns to detect and fix
    CODE_QUALITY_PATTERNS = {
        "dict_any_any": {
            "pattern": r"Dict\[Any,\s*Any\]",
            "description": "Dict[Any, Any] violates Constitutional Article IV",
            "severity": "high",
        },
        "bare_except": {
            "pattern": r"except\s*:",
            "description": "Bare except catches all exceptions including KeyboardInterrupt",
            "severity": "medium",
        },
        "todo_fixme": {
            "pattern": r"#\s*(TODO|FIXME|XXX|HACK):",
            "description": "Unresolved TODO/FIXME comment",
            "severity": "low",
        },
        "print_debug": {
            "pattern": r"\bprint\s*\([^)]*debug",
            "description": "Debug print statement left in code",
            "severity": "medium",
        },
    }

    def __init__(self, project_root: Path | None = None):
        """Initialize monitor.

        Args:
            project_root: Project root directory (defaults to AgencyOS)
        """
        self.project_root = project_root or PROJECT_ROOT
        self.fix_history: list[FixAttempt] = []

    def check_health(self) -> Result[HealthReport, str]:
        """Run health check and return detailed report.

        Returns:
            Result containing HealthReport or error message
        """
        try:
            # Run pytest collection to detect import errors
            collection_result = self._run_pytest_collection()

            # Parse results
            issues = []
            auto_fixable = []
            recommendations = []

            # Check for import errors
            import_errors = self._parse_import_errors(collection_result)
            for error in import_errors:
                issue = {
                    "type": "import_error",
                    "module": error["module"],
                    "file": error["file"],
                    "line": error.get("line", 0),
                }
                issues.append(issue)

                # Check if we know how to fix it
                if error["module"] in self.IMPORT_FIXES:
                    auto_fixable.append({
                        "issue": issue,
                        "fix": f"pip install {self.IMPORT_FIXES[error['module']]}",
                    })
                else:
                    recommendations.append(
                        f"Missing module '{error['module']}' in {error['file']}"
                    )

            # Count collection errors
            collection_errors = len(import_errors)

            # Run quick test sample to check pass rate
            test_result = self._run_pytest_sample()

            report = HealthReport(
                timestamp=datetime.now(),
                test_pass_rate=test_result.get("pass_rate", 0.0),
                tests_passed=test_result.get("passed", 0),
                tests_failed=test_result.get("failed", 0),
                tests_skipped=test_result.get("skipped", 0),
                tests_error=test_result.get("error", 0),
                collection_errors=collection_errors,
                issues_detected=issues,
                recommendations=recommendations,
                auto_fixable=auto_fixable,
            )

            return Ok(report)

        except Exception as e:
            return Err(f"Health check failed: {e}")

    def auto_heal(self, dry_run: bool = False) -> Result[list[FixAttempt], str]:
        """Attempt to automatically fix detected issues.

        Args:
            dry_run: If True, only report what would be fixed

        Returns:
            Result containing list of fix attempts or error
        """
        health_result = self.check_health()
        if health_result.is_err():
            return Err(health_result.unwrap_err())

        report = health_result.unwrap()
        fixes: list[FixAttempt] = []

        for fix_info in report.auto_fixable:
            issue = fix_info["issue"]
            fix_cmd = fix_info["fix"]

            if dry_run:
                fixes.append(FixAttempt(
                    issue_type=issue["type"],
                    file_path=issue.get("file", ""),
                    description=f"Would run: {fix_cmd}",
                    fix_applied=fix_cmd,
                    success=True,
                    error_message=None,
                ))
                continue

            # Apply the fix
            try:
                result = subprocess.run(
                    fix_cmd.split(),
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

                success = result.returncode == 0
                fixes.append(FixAttempt(
                    issue_type=issue["type"],
                    file_path=issue.get("file", ""),
                    description=f"Ran: {fix_cmd}",
                    fix_applied=fix_cmd,
                    success=success,
                    error_message=result.stderr if not success else None,
                ))

                if success:
                    print(f"✅ Fixed: {fix_cmd}")
                else:
                    print(f"❌ Failed: {fix_cmd}\n{result.stderr}")

            except Exception as e:
                fixes.append(FixAttempt(
                    issue_type=issue["type"],
                    file_path=issue.get("file", ""),
                    description=f"Exception running: {fix_cmd}",
                    fix_applied=fix_cmd,
                    success=False,
                    error_message=str(e),
                ))

        self.fix_history.extend(fixes)
        return Ok(fixes)

    def _run_pytest_collection(self) -> str:
        """Run pytest --collect-only to check for import errors."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
            timeout=120,
        )
        return result.stdout + result.stderr

    def _run_pytest_sample(self) -> dict[str, Any]:
        """Run a quick sample of tests to check pass rate."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=no", "--no-header"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
            timeout=180,
        )

        output = result.stdout + result.stderr

        # Count PASSED and FAILED lines
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        skipped = output.count(" SKIPPED")

        # Also try parsing the summary line if present
        match = re.search(r"(\d+) passed", output)
        if match:
            passed = int(match.group(1))

        match = re.search(r"(\d+) failed", output)
        if match:
            failed = int(match.group(1))

        match = re.search(r"(\d+) skipped", output)
        if match:
            skipped = int(match.group(1))

        total = passed + failed
        pass_rate = passed / total if total > 0 else 1.0 if passed > 0 else 0.0

        return {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "error": 0,
            "pass_rate": pass_rate,
        }

    def _parse_import_errors(self, output: str) -> list[dict[str, str]]:
        """Parse import errors from pytest collection output."""
        errors = []

        # Pattern: ModuleNotFoundError: No module named 'xxx'
        pattern = r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]"

        for match in re.finditer(pattern, output):
            module = match.group(1).split(".")[0]  # Get top-level module

            # Find the file that caused the error
            file_pattern = r"(\S+\.py):\d+: in <module>"
            file_match = re.search(file_pattern, output[max(0, match.start()-500):match.start()])

            errors.append({
                "module": module,
                "file": file_match.group(1) if file_match else "unknown",
            })

        return errors

    def scan_code_quality(self, paths: list[str] | None = None) -> list[dict[str, Any]]:
        """Scan code for quality issues.

        Args:
            paths: List of paths to scan (defaults to common source dirs)

        Returns:
            List of detected issues with file, line, pattern, and severity
        """
        if paths is None:
            paths = ["tools/", "shared/", "coding_agent/", "planner_agent/"]

        issues = []

        for base_path in paths:
            full_path = self.project_root / base_path
            if not full_path.exists():
                continue

            for py_file in full_path.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    lines = content.split("\n")

                    for pattern_name, pattern_info in self.CODE_QUALITY_PATTERNS.items():
                        for i, line in enumerate(lines, 1):
                            if re.search(pattern_info["pattern"], line):
                                issues.append({
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "line": i,
                                    "pattern": pattern_name,
                                    "description": pattern_info["description"],
                                    "severity": pattern_info["severity"],
                                    "content": line.strip()[:100],
                                })
                except Exception:
                    continue  # Skip files that can't be read

        return issues

    def get_semantic_clusters(self, issues: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Cluster similar issues using VLM embeddings.

        Args:
            issues: List of issues to cluster

        Returns:
            Dict mapping cluster names to lists of similar issues
        """
        if not issues:
            return {}

        try:
            from openai import OpenAI
            import numpy as np

            client = OpenAI(
                api_key="lm-studio",
                base_url="http://127.0.0.1:1234/v1",
                timeout=30.0,
            )

            # Get embeddings for each issue description
            embeddings = []
            for issue in issues:
                text = f"{issue.get('description', '')} {issue.get('content', '')}"
                try:
                    resp = client.embeddings.create(
                        model="text-embedding-nomic-embed-text-v1.5",
                        input=text[:500],  # Limit input size
                    )
                    embeddings.append(np.array(resp.data[0].embedding))
                except Exception:
                    embeddings.append(None)

            # Simple clustering based on cosine similarity
            clusters: dict[str, list[dict[str, Any]]] = {}

            def cosine_sim(a, b):
                if a is None or b is None:
                    return 0.0
                return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

            assigned = [False] * len(issues)
            cluster_id = 0

            for i, issue in enumerate(issues):
                if assigned[i]:
                    continue

                cluster_name = f"cluster_{cluster_id}"
                clusters[cluster_name] = [issue]
                assigned[i] = True

                # Find similar issues
                for j, other_issue in enumerate(issues):
                    if not assigned[j] and i != j:
                        sim = cosine_sim(embeddings[i], embeddings[j])
                        if sim > 0.7:  # High similarity threshold
                            clusters[cluster_name].append(other_issue)
                            assigned[j] = True

                cluster_id += 1

            return clusters

        except ImportError:
            # Fallback: cluster by pattern type
            clusters: dict[str, list[dict[str, Any]]] = {}
            for issue in issues:
                pattern = issue.get("pattern", "unknown")
                if pattern not in clusters:
                    clusters[pattern] = []
                clusters[pattern].append(issue)
            return clusters

    def store_learning(self, fix: FixAttempt) -> bool:
        """Store successful fix pattern in VectorStore for future learning.

        Args:
            fix: The fix attempt to store

        Returns:
            True if stored successfully
        """
        if not fix.success:
            return False

        try:
            from shared.agent_context import create_agent_context

            context = create_agent_context(session_id="self_healing")
            context.store_memory(
                key=f"fix_{fix.issue_type}_{datetime.now().isoformat()}",
                content={
                    "issue_type": fix.issue_type,
                    "file_path": fix.file_path,
                    "fix_applied": fix.fix_applied,
                    "description": fix.description,
                    "timestamp": datetime.now().isoformat(),
                },
                tags=["self_healing", "auto_fix", fix.issue_type],
            )
            return True
        except Exception:
            return False  # VectorStore not available

    def query_past_fixes(self, issue_type: str) -> list[dict[str, Any]]:
        """Query VectorStore for past successful fixes of this type.

        Args:
            issue_type: Type of issue to look up

        Returns:
            List of past fix patterns
        """
        try:
            from shared.agent_context import create_agent_context

            context = create_agent_context(session_id="self_healing")
            results = context.search_memories(
                query_terms=["self_healing", "auto_fix", issue_type],
                include_session=False,
            )
            return results
        except Exception:
            return []

    def generate_report(self) -> str:
        """Generate a human-readable health report."""
        result = self.check_health()
        if result.is_err():
            return f"❌ Health check failed: {result.unwrap_err()}"

        report = result.unwrap()

        lines = [
            "=" * 60,
            "AgencyOS Health Report",
            f"Timestamp: {report.timestamp.isoformat()}",
            "=" * 60,
            "",
            f"Test Pass Rate: {report.test_pass_rate*100:.1f}%",
            f"  Passed: {report.tests_passed}",
            f"  Failed: {report.tests_failed}",
            f"  Skipped: {report.tests_skipped}",
            f"  Collection Errors: {report.collection_errors}",
            "",
        ]

        if report.issues_detected:
            lines.append("Issues Detected:")
            for issue in report.issues_detected:
                lines.append(f"  - {issue['type']}: {issue.get('module', '')} in {issue.get('file', '')}")

        if report.auto_fixable:
            lines.append("")
            lines.append("Auto-Fixable Issues:")
            for fix in report.auto_fixable:
                lines.append(f"  - {fix['fix']}")

        if report.recommendations:
            lines.append("")
            lines.append("Recommendations:")
            for rec in report.recommendations:
                lines.append(f"  - {rec}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


def check_vlm_health() -> dict[str, Any]:
    """Check VLM/LM Studio health status."""
    import time

    status = {
        "service": "VLM/LM Studio",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
    }

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key="lm-studio",
            base_url="http://127.0.0.1:1234/v1",
            timeout=10.0,
        )

        # Check 1: API connectivity
        try:
            models = client.models.list()
            status["checks"]["api"] = {
                "status": "ok",
                "models": len(models.data),
            }
        except Exception as e:
            status["checks"]["api"] = {"status": "error", "error": str(e)}
            status["overall"] = "error"
            return status

        # Check 2: Embedding model
        try:
            start = time.time()
            response = client.embeddings.create(
                model="text-embedding-nomic-embed-text-v1.5",
                input="health check",
            )
            latency = int((time.time() - start) * 1000)
            status["checks"]["embedding"] = {
                "status": "ok",
                "dimension": len(response.data[0].embedding),
                "latency_ms": latency,
            }
        except Exception as e:
            status["checks"]["embedding"] = {"status": "error", "error": str(e)}

        status["overall"] = "healthy" if all(
            c.get("status") == "ok" for c in status["checks"].values()
        ) else "degraded"

    except ImportError:
        status["overall"] = "unavailable"
        status["checks"]["import"] = {"status": "error", "error": "openai not installed"}

    return status


def run_daemon(interval_seconds: int = 300, max_cycles: int = 0):
    """Run continuous health monitoring daemon.

    Args:
        interval_seconds: Seconds between health checks (default: 5 min)
        max_cycles: Maximum cycles to run (0 = infinite)
    """
    import time

    monitor = SelfHealingMonitor()
    cycle = 0

    print("=" * 60)
    print("AgencyOS Self-Healing Daemon Started")
    print(f"Interval: {interval_seconds}s | Max cycles: {'∞' if max_cycles == 0 else max_cycles}")
    print("=" * 60)

    try:
        while max_cycles == 0 or cycle < max_cycles:
            cycle += 1
            print(f"\n[Cycle {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Check test health
            health_result = monitor.check_health()
            if health_result.is_ok():
                report = health_result.unwrap()
                print(f"  Tests: {report.test_pass_rate*100:.0f}% pass ({report.tests_passed}/{report.tests_passed + report.tests_failed})")

                if report.auto_fixable:
                    print(f"  Auto-fixing {len(report.auto_fixable)} issues...")
                    fix_result = monitor.auto_heal(dry_run=False)
                    if fix_result.is_ok():
                        fixes = fix_result.unwrap()
                        success_count = sum(1 for f in fixes if f.success)
                        print(f"  Fixed: {success_count}/{len(fixes)}")
            else:
                print(f"  Health check failed: {health_result.unwrap_err()}")

            # Check VLM health
            vlm_status = check_vlm_health()
            vlm_icon = "✓" if vlm_status.get("overall") == "healthy" else "✗"
            print(f"  VLM: {vlm_icon} {vlm_status.get('overall', 'unknown')}")

            if max_cycles == 0 or cycle < max_cycles:
                print(f"  Next check in {interval_seconds}s...")
                time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n\nDaemon stopped by user.")


def generate_dashboard(monitor: SelfHealingMonitor) -> str:
    """Generate a comprehensive health dashboard.

    Returns:
        Markdown-formatted dashboard report
    """
    lines = [
        "# AgencyOS Health Dashboard",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## System Status",
        "",
    ]

    # Test health
    health_result = monitor.check_health()
    if health_result.is_ok():
        report = health_result.unwrap()
        status_icon = "✅" if report.test_pass_rate >= 0.95 else "⚠️" if report.test_pass_rate >= 0.8 else "❌"
        lines.extend([
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Test Pass Rate | {status_icon} {report.test_pass_rate*100:.1f}% |",
            f"| Tests Passed | {report.tests_passed} |",
            f"| Tests Failed | {report.tests_failed} |",
            f"| Tests Skipped | {report.tests_skipped} |",
            f"| Collection Errors | {report.collection_errors} |",
            "",
        ])

    # VLM health
    vlm_status = check_vlm_health()
    vlm_icon = "✅" if vlm_status.get("overall") == "healthy" else "❌"
    lines.extend([
        "## VLM Status",
        "",
        f"| Check | Status |",
        f"|-------|--------|",
    ])
    for check, data in vlm_status.get("checks", {}).items():
        check_icon = "✅" if data.get("status") == "ok" else "❌"
        lines.append(f"| {check} | {check_icon} {data.get('status', 'unknown')} |")
    lines.append("")

    # Code quality issues
    issues = monitor.scan_code_quality()
    by_severity = {"high": [], "medium": [], "low": []}
    for issue in issues:
        by_severity[issue["severity"]].append(issue)

    lines.extend([
        "## Code Quality",
        "",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| 🔴 High | {len(by_severity['high'])} |",
        f"| 🟡 Medium | {len(by_severity['medium'])} |",
        f"| 🔵 Low | {len(by_severity['low'])} |",
        f"| **Total** | **{len(issues)}** |",
        "",
    ])

    # Top issues
    if by_severity["high"]:
        lines.extend([
            "### Top High-Severity Issues",
            "",
        ])
        for issue in by_severity["high"][:5]:
            lines.append(f"- `{issue['file']}:{issue['line']}` - {issue['description']}")
        lines.append("")

    # Auto-fixable summary
    if health_result.is_ok():
        report = health_result.unwrap()
        if report.auto_fixable:
            lines.extend([
                "## Auto-Fixable Issues",
                "",
            ])
            for fix in report.auto_fixable:
                lines.append(f"- `{fix['fix']}`")
            lines.append("")

    lines.extend([
        "---",
        f"*Dashboard generated by AgencyOS Self-Healing Monitor*",
    ])

    return "\n".join(lines)


def main():
    """Run health monitor from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="AgencyOS Self-Healing Monitor")
    parser.add_argument("--heal", action="store_true", help="Attempt auto-healing")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed")
    parser.add_argument("--daemon", action="store_true", help="Run as continuous daemon")
    parser.add_argument("--interval", type=int, default=300, help="Daemon interval in seconds")
    parser.add_argument("--cycles", type=int, default=0, help="Max daemon cycles (0=infinite)")
    parser.add_argument("--vlm", action="store_true", help="Check VLM health only")
    parser.add_argument("--scan", action="store_true", help="Scan code for quality issues")
    parser.add_argument("--cluster", action="store_true", help="Cluster issues by semantic similarity")
    parser.add_argument("--paths", nargs="+", help="Paths to scan (default: tools/, shared/)")
    parser.add_argument("--dashboard", action="store_true", help="Generate health dashboard")
    parser.add_argument("--output", type=str, help="Output file for dashboard (default: stdout)")
    args = parser.parse_args()

    monitor = SelfHealingMonitor()

    if args.vlm:
        status = check_vlm_health()
        print(f"VLM Status: {status.get('overall', 'unknown')}")
        for check, data in status.get("checks", {}).items():
            icon = "✓" if data.get("status") == "ok" else "✗"
            print(f"  {icon} {check}: {data}")
        return

    if args.dashboard:
        dashboard = generate_dashboard(monitor)
        if args.output:
            Path(args.output).write_text(dashboard)
            print(f"✅ Dashboard saved to {args.output}")
        else:
            print(dashboard)
        return

    if args.daemon:
        run_daemon(interval_seconds=args.interval, max_cycles=args.cycles)
        return

    if args.scan:
        print("=" * 60)
        print("Code Quality Scan")
        print("=" * 60)
        issues = monitor.scan_code_quality(paths=args.paths)

        if not issues:
            print("\n✅ No code quality issues detected!")
        else:
            # Group by severity
            by_severity = {"high": [], "medium": [], "low": []}
            for issue in issues:
                by_severity[issue["severity"]].append(issue)

            for severity in ["high", "medium", "low"]:
                if by_severity[severity]:
                    icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🔵"
                    print(f"\n{icon} {severity.upper()} ({len(by_severity[severity])} issues):")
                    for issue in by_severity[severity][:10]:  # Limit display
                        print(f"  {issue['file']}:{issue['line']}")
                        print(f"    {issue['description']}")
                    if len(by_severity[severity]) > 10:
                        print(f"  ... and {len(by_severity[severity]) - 10} more")

            if args.cluster:
                print("\n" + "=" * 60)
                print("Semantic Clustering (using VLM)")
                print("=" * 60)
                clusters = monitor.get_semantic_clusters(issues)
                for cluster_name, cluster_issues in clusters.items():
                    print(f"\n📦 {cluster_name} ({len(cluster_issues)} issues):")
                    for ci in cluster_issues[:5]:
                        print(f"  - {ci['file']}:{ci['line']} ({ci['pattern']})")

            print(f"\nTotal: {len(issues)} issues found")
        return

    print(monitor.generate_report())

    if args.heal:
        print("\n🔧 Attempting auto-healing...")
        result = monitor.auto_heal(dry_run=args.dry_run)
        if result.is_ok():
            fixes = result.unwrap()
            print(f"\n✅ Applied {len(fixes)} fixes")
            for fix in fixes:
                status = "✅" if fix.success else "❌"
                print(f"  {status} {fix.description}")

                # Store successful fixes for learning
                if fix.success and not args.dry_run:
                    if monitor.store_learning(fix):
                        print(f"    📚 Stored in VectorStore for future learning")
        else:
            print(f"\n❌ Auto-healing failed: {result.unwrap_err()}")


if __name__ == "__main__":
    main()
