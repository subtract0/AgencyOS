"""
Capture baseline metrics before any changes.

Run this ONCE before starting autonomous improvements.
Use --compare flag to compare current state to baseline.

Constitutional Compliance:
- Article I: Complete context via comprehensive metrics
- Article II: 100% verification via baseline comparison
- Article IV: Learning via metric history tracking
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


BASELINE_PATH = PROJECT_ROOT / "logs" / "metrics_baseline.json"
HISTORY_PATH = PROJECT_ROOT / "logs" / "metrics_history.json"


def capture_baseline(save: bool = True) -> dict:
    """Capture all metrics as baseline.

    Args:
        save: Whether to save to file

    Returns:
        Dictionary with all captured metrics
    """
    print("Capturing baseline metrics...")

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "version": "baseline",
    }

    # 1. Test metrics (collection count)
    print("  Collecting test count...")
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
        # Parse test count from output like "419 tests collected"
        import re
        match = re.search(r"(\d+)\s+tests?\s+collected", result.stdout)
        test_count = int(match.group(1)) if match else 0
        metrics["tests"] = {
            "total_collected": test_count,
        }
    except Exception as e:
        metrics["tests"] = {"error": str(e)}
        print(f"    Warning: Could not collect tests - {e}")

    # 2. Run unit tests for pass rate
    print("  Running unit tests...")
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_ROOT),
        )
        passed = result.stdout.count(" PASSED") + result.stdout.count(" passed")
        failed = result.stdout.count(" FAILED") + result.stdout.count(" failed")
        skipped = result.stdout.count(" SKIPPED") + result.stdout.count(" skipped")

        # Also check for short format
        import re
        short_match = re.search(r"(\d+) passed", result.stdout)
        if short_match and passed == 0:
            passed = int(short_match.group(1))
        short_fail = re.search(r"(\d+) failed", result.stdout)
        if short_fail and failed == 0:
            failed = int(short_fail.group(1))
        short_skip = re.search(r"(\d+) skipped", result.stdout)
        if short_skip and skipped == 0:
            skipped = int(short_skip.group(1))

        total = passed + failed
        metrics["tests"]["passed"] = passed
        metrics["tests"]["failed"] = failed
        metrics["tests"]["skipped"] = skipped
        metrics["tests"]["pass_rate"] = passed / total if total > 0 else 0.0
    except Exception as e:
        metrics["tests"]["run_error"] = str(e)
        print(f"    Warning: Could not run tests - {e}")

    # 3. Code quality metrics
    print("  Scanning code quality...")
    try:
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()
        issues = monitor.scan_code_quality()

        metrics["quality"] = {
            "total_issues": len(issues),
            "high": sum(1 for i in issues if i.get("severity") == "high"),
            "medium": sum(1 for i in issues if i.get("severity") == "medium"),
            "low": sum(1 for i in issues if i.get("severity") == "low"),
        }
    except Exception as e:
        metrics["quality"] = {"error": str(e)}
        print(f"    Warning: Could not scan quality - {e}")

    # 4. Codebase size
    print("  Measuring codebase size...")
    try:
        py_files = list(PROJECT_ROOT.rglob("*.py"))
        # Exclude venv, __pycache__, etc
        py_files = [
            f for f in py_files
            if "venv" not in str(f)
            and "__pycache__" not in str(f)
            and ".venv" not in str(f)
            and "node_modules" not in str(f)
        ]
        total_lines = 0
        for f in py_files:
            try:
                total_lines += len(f.read_text().split("\n"))
            except Exception:
                pass

        metrics["codebase"] = {
            "python_files": len(py_files),
            "total_lines": total_lines,
        }
    except Exception as e:
        metrics["codebase"] = {"error": str(e)}
        print(f"    Warning: Could not measure codebase - {e}")

    # 5. Git metrics
    print("  Collecting git info...")
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        git_ref = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        commit_count = int(result.stdout.strip())

        metrics["git"] = {
            "current_ref": git_ref,
            "commit_count": commit_count,
        }
    except Exception as e:
        metrics["git"] = {"error": str(e)}

    # Save baseline
    if save:
        BASELINE_PATH.parent.mkdir(exist_ok=True)
        BASELINE_PATH.write_text(json.dumps(metrics, indent=2))
        print(f"\n{'='*50}")
        print(f"Baseline captured: {BASELINE_PATH}")
        print(f"{'='*50}")

    # Summary
    if "tests" in metrics and "passed" in metrics["tests"]:
        total = metrics["tests"]["passed"] + metrics["tests"]["failed"]
        print(f"  Tests: {metrics['tests']['passed']}/{total} passing ({metrics['tests']['pass_rate']:.1%})")
    if "quality" in metrics and "total_issues" in metrics["quality"]:
        print(f"  Quality issues: {metrics['quality']['total_issues']} (H:{metrics['quality']['high']}, M:{metrics['quality']['medium']}, L:{metrics['quality']['low']})")
    if "codebase" in metrics and "python_files" in metrics["codebase"]:
        print(f"  Codebase: {metrics['codebase']['python_files']} files, {metrics['codebase']['total_lines']:,} lines")

    return metrics


def capture_current() -> dict:
    """Capture current metrics without saving as baseline.

    Returns:
        Dictionary with current metrics
    """
    return capture_baseline(save=False)


def compare_to_baseline(current: dict | None = None) -> Result[dict, str]:
    """Compare current metrics to baseline.

    Args:
        current: Current metrics (captured if not provided)

    Returns:
        Result with comparison or error
    """
    if not BASELINE_PATH.exists():
        return Err("No baseline captured. Run 'python tools/metrics_baseline.py' first.")

    baseline = json.loads(BASELINE_PATH.read_text())

    if current is None:
        current = capture_current()

    comparison = {
        "timestamp": datetime.now().isoformat(),
        "baseline_timestamp": baseline["timestamp"],
        "improvements": {},
        "regressions": {},
        "unchanged": {},
    }

    # Compare test pass rate
    if "tests" in baseline and "tests" in current:
        baseline_rate = baseline["tests"].get("pass_rate", 0)
        current_rate = current["tests"].get("pass_rate", 0)

        if current_rate > baseline_rate + 0.001:  # More than 0.1% improvement
            comparison["improvements"]["test_pass_rate"] = {
                "baseline": baseline_rate,
                "current": current_rate,
                "delta": current_rate - baseline_rate,
            }
        elif current_rate < baseline_rate - 0.001:  # More than 0.1% regression
            comparison["regressions"]["test_pass_rate"] = {
                "baseline": baseline_rate,
                "current": current_rate,
                "delta": current_rate - baseline_rate,
            }
        else:
            comparison["unchanged"]["test_pass_rate"] = baseline_rate

    # Compare quality issues (lower is better)
    if "quality" in baseline and "quality" in current:
        baseline_issues = baseline["quality"].get("total_issues", 0)
        current_issues = current["quality"].get("total_issues", 0)

        if current_issues < baseline_issues:
            comparison["improvements"]["quality_issues"] = {
                "baseline": baseline_issues,
                "current": current_issues,
                "delta": baseline_issues - current_issues,
            }
        elif current_issues > baseline_issues:
            comparison["regressions"]["quality_issues"] = {
                "baseline": baseline_issues,
                "current": current_issues,
                "delta": current_issues - baseline_issues,
            }
        else:
            comparison["unchanged"]["quality_issues"] = baseline_issues

    # Compare codebase size (informational, not good/bad)
    if "codebase" in baseline and "codebase" in current:
        baseline_lines = baseline["codebase"].get("total_lines", 0)
        current_lines = current["codebase"].get("total_lines", 0)
        comparison["info"] = {
            "lines_delta": current_lines - baseline_lines,
            "files_delta": current["codebase"].get("python_files", 0) - baseline["codebase"].get("python_files", 0),
        }

    # Save to history
    _append_to_history(comparison)

    return Ok(comparison)


def _append_to_history(comparison: dict) -> None:
    """Append comparison to history file.

    Args:
        comparison: Comparison result to append
    """
    history = []
    if HISTORY_PATH.exists():
        try:
            history = json.loads(HISTORY_PATH.read_text())
        except Exception:
            pass

    history.append(comparison)

    # Keep last 100 entries
    if len(history) > 100:
        history = history[-100:]

    HISTORY_PATH.parent.mkdir(exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2))


def get_improvement_trend() -> Result[dict, str]:
    """Analyze improvement trend from history.

    Returns:
        Result with trend analysis or error
    """
    if not HISTORY_PATH.exists():
        return Err("No history available. Run comparisons first.")

    history = json.loads(HISTORY_PATH.read_text())

    if len(history) < 2:
        return Err("Need at least 2 data points for trend analysis.")

    # Count improvements vs regressions
    improvements_count = sum(1 for h in history if len(h.get("improvements", {})) > 0)
    regressions_count = sum(1 for h in history if len(h.get("regressions", {})) > 0)

    return Ok({
        "total_comparisons": len(history),
        "comparisons_with_improvements": improvements_count,
        "comparisons_with_regressions": regressions_count,
        "trend": "positive" if improvements_count > regressions_count else "negative" if regressions_count > improvements_count else "neutral",
    })


def print_comparison(comparison: dict) -> None:
    """Print comparison results in a readable format.

    Args:
        comparison: Comparison dictionary
    """
    print(f"\n{'='*60}")
    print("METRICS COMPARISON")
    print(f"{'='*60}")
    print(f"Baseline: {comparison['baseline_timestamp']}")
    print(f"Current:  {comparison['timestamp']}")

    if comparison.get("improvements"):
        print(f"\n{'🟢 IMPROVEMENTS':}")
        for key, val in comparison["improvements"].items():
            if key == "test_pass_rate":
                print(f"  • Test pass rate: {val['baseline']:.1%} → {val['current']:.1%} (+{val['delta']:.1%})")
            elif key == "quality_issues":
                print(f"  • Quality issues: {val['baseline']} → {val['current']} (-{val['delta']} issues)")

    if comparison.get("regressions"):
        print(f"\n{'🔴 REGRESSIONS':}")
        for key, val in comparison["regressions"].items():
            if key == "test_pass_rate":
                print(f"  • Test pass rate: {val['baseline']:.1%} → {val['current']:.1%} ({val['delta']:+.1%})")
            elif key == "quality_issues":
                print(f"  • Quality issues: {val['baseline']} → {val['current']} (+{val['delta']} issues)")

    if comparison.get("unchanged"):
        print(f"\n{'⚪ UNCHANGED':}")
        for key, val in comparison["unchanged"].items():
            if key == "test_pass_rate":
                print(f"  • Test pass rate: {val:.1%}")
            elif key == "quality_issues":
                print(f"  • Quality issues: {val}")

    if comparison.get("info"):
        info = comparison["info"]
        print(f"\n{'ℹ️ INFO':}")
        print(f"  • Lines changed: {info.get('lines_delta', 0):+,}")
        print(f"  • Files changed: {info.get('files_delta', 0):+}")

    print(f"{'='*60}\n")


def main():
    """Command-line interface for metrics baseline."""
    parser = argparse.ArgumentParser(description="Capture and compare codebase metrics")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare current state to baseline",
    )
    parser.add_argument(
        "--trend",
        action="store_true",
        help="Show improvement trend from history",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    if args.compare:
        result = compare_to_baseline()
        if result.is_err():
            print(f"Error: {result.unwrap_err()}")
            sys.exit(1)

        comparison = result.unwrap()
        if args.json:
            print(json.dumps(comparison, indent=2))
        else:
            print_comparison(comparison)

        # Exit with error if regressions found
        if comparison.get("regressions"):
            sys.exit(1)

    elif args.trend:
        result = get_improvement_trend()
        if result.is_err():
            print(f"Error: {result.unwrap_err()}")
            sys.exit(1)

        trend = result.unwrap()
        if args.json:
            print(json.dumps(trend, indent=2))
        else:
            print(f"\nTrend Analysis:")
            print(f"  Total comparisons: {trend['total_comparisons']}")
            print(f"  With improvements: {trend['comparisons_with_improvements']}")
            print(f"  With regressions: {trend['comparisons_with_regressions']}")
            print(f"  Overall trend: {trend['trend'].upper()}")

    else:
        # Capture baseline
        capture_baseline()


if __name__ == "__main__":
    main()
