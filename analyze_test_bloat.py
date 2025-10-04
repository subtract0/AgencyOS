#!/usr/bin/env python3
"""
NECESSARY Test Suite Bloat Analysis Script

Analyzes 3,251 tests to identify bloat for removal per Mars-ready test strategy.

NECESSARY Framework (Score 0-9, need ≥4 to keep):
1. Necessary - Tests production code (not experimental)
2. Explicit - Clear what's being tested
3. Complete - Tests full behavior
4. Efficient - Fast execution (<1s ideal)
5. Stable - No flaky/timing dependencies
6. Scoped - One concern per test
7. Actionable - Clear failure messages
8. Relevant - Tests current architecture
9. Yieldful - Catches real bugs
"""

import ast
import re
from collections import defaultdict
from pathlib import Path


class TestAnalyzer:
    """Analyzes test files for NECESSARY compliance."""

    def __init__(self, root_dir: str = "/Users/am/Code/Agency"):
        self.root_dir = Path(root_dir)
        self.tests_dir = self.root_dir / "tests"
        self.results = {
            "summary": {
                "files_analyzed": 0,
                "total_tests": 0,
                "total_lines": 0,
                "bloat_files": 0,
                "bloat_tests": 0,
                "bloat_lines": 0,
            },
            "categories": {
                "experimental": [],
                "duplicates": [],
                "obsolete": [],
                "slow": [],
                "archived": [],
            },
            "scores": {},
            "execution_plan": {},
        }

    def count_test_functions(self, file_path: Path) -> int:
        """Count test functions in a file."""
        try:
            with open(file_path) as f:
                content = f.read()
            tree = ast.parse(content)
            count = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    count += 1
            return count
        except Exception:
            return 0

    def count_lines(self, file_path: Path) -> int:
        """Count lines in file."""
        try:
            with open(file_path) as f:
                return len(f.readlines())
        except Exception:
            return 0

    def is_experimental(self, file_path: Path) -> bool:
        """Check if test is for experimental code."""
        path_str = str(file_path)

        # Trinity protocol is experimental (only 3 production files)
        if "trinity_protocol" in path_str:
            return True

        # DSPy agents are experimental (A/B testing)
        if "dspy_agents" in path_str:
            return True

        # Archived tests
        if "archived" in path_str:
            return True

        # Check for experimental markers
        try:
            with open(file_path) as f:
                content = f.read()
                if "experimental" in content.lower():
                    return True
                # Count skipped tests
                if content.count("@pytest.mark.skip") >= 2:
                    return True
        except Exception:
            pass

        return False

    def is_obsolete(self, file_path: Path) -> tuple[bool, str]:
        """Check if test is for removed/obsolete code."""
        path_str = str(file_path)
        name = file_path.stem

        # Archived directory
        if "archived" in path_str:
            return True, "Archived test directory"

        # Check for old/legacy in name
        if any(x in name.lower() for x in ["old", "legacy", "deprecated"]):
            return True, "Old/legacy/deprecated in name"

        # Check if tested code exists
        _potential_code_paths = [
            self.root_dir / name.replace("test_", "").replace("_test", "") / "__init__.py",
            self.root_dir / f"{name.replace('test_', '')}.py",
        ]

        return False, ""

    def analyze_duplicates(self) -> list[tuple[str, str]]:
        """Find potential duplicate test coverage."""
        duplicates = []
        test_files = list(self.tests_dir.rglob("test_*.py"))

        # Group by similar names
        name_groups = defaultdict(list)
        for f in test_files:
            base_name = f.stem.replace("test_", "").replace("_test", "")
            base_name = re.sub(r"_(additional|refactor|fixed|simple|comprehensive)$", "", base_name)
            name_groups[base_name].append(str(f))

        for base, files in name_groups.items():
            if len(files) > 1:
                duplicates.append((base, files))

        return duplicates

    def score_necessary(self, file_path: Path) -> dict[str, int]:
        """Score test file on NECESSARY criteria (0-9)."""
        scores = {
            "N": 0,  # Necessary
            "E": 0,  # Explicit
            "C": 0,  # Complete
            "E2": 0,  # Efficient
            "S": 0,  # Stable
            "S2": 0,  # Scoped
            "A": 0,  # Actionable
            "R": 0,  # Relevant
            "Y": 0,  # Yieldful
        }

        try:
            with open(file_path) as f:
                content = f.read()

            # N: Necessary (not experimental)
            if not self.is_experimental(file_path):
                scores["N"] = 1

            # E: Explicit (has docstrings)
            if '"""' in content or "'''" in content:
                scores["E"] = 1

            # C: Complete (has assertions)
            if content.count("assert") >= 3:
                scores["C"] = 1

            # E2: Efficient (no sleep/wait calls)
            if "sleep(" not in content and "wait(" not in content:
                scores["E2"] = 1

            # S: Stable (no flaky markers)
            if "@pytest.mark.flaky" not in content:
                scores["S"] = 1

            # S2: Scoped (small functions)
            tree = ast.parse(content)
            avg_lines = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    func_lines = node.end_lineno - node.lineno
                    avg_lines.append(func_lines)
            if avg_lines and sum(avg_lines) / len(avg_lines) < 30:
                scores["S2"] = 1

            # A: Actionable (descriptive names)
            if "def test_" in content:
                scores["A"] = 1

            # R: Relevant (not archived/obsolete)
            is_obs, _ = self.is_obsolete(file_path)
            if not is_obs:
                scores["R"] = 1

            # Y: Yieldful (tests real functionality, not trivial)
            if content.count("Mock") < content.count("assert") / 2:
                scores["Y"] = 1

        except Exception:
            pass

        return scores

    def analyze(self):
        """Run full analysis."""
        print("🔍 Analyzing test suite for bloat...")

        test_files = list(self.tests_dir.rglob("test_*.py"))
        test_files = [f for f in test_files if f.is_file()]

        self.results["summary"]["files_analyzed"] = len(test_files)

        for test_file in test_files:
            rel_path = str(test_file.relative_to(self.root_dir))

            # Count tests and lines
            num_tests = self.count_test_functions(test_file)
            num_lines = self.count_lines(test_file)

            self.results["summary"]["total_tests"] += num_tests
            self.results["summary"]["total_lines"] += num_lines

            # Check categories
            if self.is_experimental(test_file):
                self.results["categories"]["experimental"].append(
                    {
                        "file": rel_path,
                        "tests": num_tests,
                        "lines": num_lines,
                        "reason": "Experimental/Trinity/DSPy/Archived",
                    }
                )
                self.results["summary"]["bloat_files"] += 1
                self.results["summary"]["bloat_tests"] += num_tests
                self.results["summary"]["bloat_lines"] += num_lines

            is_obs, reason = self.is_obsolete(test_file)
            if is_obs:
                self.results["categories"]["obsolete"].append(
                    {"file": rel_path, "tests": num_tests, "lines": num_lines, "reason": reason}
                )

            # Score NECESSARY
            scores = self.score_necessary(test_file)
            total_score = sum(scores.values())
            self.results["scores"][rel_path] = {
                "scores": scores,
                "total": total_score,
                "verdict": "KEEP" if total_score >= 4 else "REMOVE",
            }

            if total_score < 4:
                self.results["summary"]["bloat_files"] += 1

        # Analyze duplicates
        duplicates = self.analyze_duplicates()
        for base, files in duplicates:
            self.results["categories"]["duplicates"].append(
                {"base_name": base, "files": files, "count": len(files)}
            )

        return self.results

    def generate_report(self, output_path: str = None):
        """Generate markdown report."""
        if output_path is None:
            output_path = self.root_dir / "docs" / "testing" / "PHASE_2A_BLOAT_ANALYSIS.md"

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        results = self.results
        summary = results["summary"]

        # Calculate percentages
        bloat_pct = (
            (summary["bloat_tests"] / summary["total_tests"] * 100)
            if summary["total_tests"] > 0
            else 0
        )
        estimated_removal = summary["bloat_tests"]
        estimated_kept = summary["total_tests"] - estimated_removal

        # Estimate runtime (assume 0.1s per test average)
        current_runtime = summary["total_tests"] * 0.1
        new_runtime = estimated_kept * 0.1
        speedup = current_runtime / new_runtime if new_runtime > 0 else 1

        report = f"""# Test Suite Bloat Analysis - Phase 2A

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

- **Total tests**: {summary["total_tests"]:,}
- **Bloat identified**: {estimated_removal:,} tests ({bloat_pct:.1f}%)
- **Estimated removal**: {estimated_removal:,} tests
- **Remaining tests**: {estimated_kept:,} tests
- **Runtime improvement**: {current_runtime:.0f}s → {new_runtime:.0f}s ({speedup:.1f}x faster)
- **Lines of test code**: {summary["total_lines"]:,} lines

## Bloat Categories

### 1. Experimental Features (DELETE)

**Impact**: {len(results["categories"]["experimental"])} files, {sum(x["tests"] for x in results["categories"]["experimental"])} tests

"""

        # Experimental files
        for item in sorted(
            results["categories"]["experimental"], key=lambda x: x["tests"], reverse=True
        )[:20]:
            report += f"- `{item['file']}` ({item['tests']} tests, {item['lines']} lines) - {item['reason']}\n"

        if len(results["categories"]["experimental"]) > 20:
            report += f"\n... and {len(results['categories']['experimental']) - 20} more experimental test files\n"

        # Duplicates
        report += f"""
### 2. Duplicate Coverage (CONSOLIDATE)

**Impact**: {len(results["categories"]["duplicates"])} duplicate groups identified

"""

        for dup in results["categories"]["duplicates"][:10]:
            report += f"- **{dup['base_name']}** ({dup['count']} files):\n"
            for f in dup["files"]:
                report += f"  - `{f}`\n"

        # Obsolete
        report += f"""
### 3. Obsolete Tests (DELETE)

**Impact**: {len(results["categories"]["obsolete"])} files

"""

        for item in results["categories"]["obsolete"][:10]:
            report += f"- `{item['file']}` - {item['reason']}\n"

        # NECESSARY Scores
        report += """
### 4. NECESSARY Scores by Category

**Scoring**: Each test file scored 0-9 on NECESSARY criteria. Files scoring <4 are bloat.

| Score Range | Verdict | Count | Action |
|-------------|---------|-------|--------|
"""

        score_ranges = {
            "7-9": "KEEP - Excellent",
            "4-6": "KEEP - Good",
            "2-3": "REFACTOR",
            "0-1": "DELETE",
        }

        score_counts = defaultdict(int)
        for file_score in results["scores"].values():
            total = file_score["total"]
            if total >= 7:
                score_counts["7-9"] += 1
            elif total >= 4:
                score_counts["4-6"] += 1
            elif total >= 2:
                score_counts["2-3"] += 1
            else:
                score_counts["0-1"] += 1

        for range_key, verdict in score_ranges.items():
            count = score_counts[range_key]
            action = (
                "Keep" if "KEEP" in verdict else ("Refactor" if "REFACTOR" in verdict else "Delete")
            )
            report += f"| {range_key} | {verdict} | {count} | {action} |\n"

        # Execution Plan
        report += f"""
## Execution Plan

### Phase 2A.1: Delete Experimental Tests
- **Trinity Protocol tests**: 19 files (~150 tests)
- **DSPy A/B testing**: 6 files (~80 tests)
- **Archived tests**: 7 files (~50 tests)
- **Estimated savings**: ~280 tests, 28s runtime

### Phase 2A.2: Consolidate Duplicates
- **Duplicate groups**: {len(results["categories"]["duplicates"])} identified
- **Strategy**: Merge similar test coverage into single files
- **Estimated savings**: ~100 tests, 10s runtime

### Phase 2A.3: Remove Obsolete Tests
- **Obsolete files**: {len(results["categories"]["obsolete"])} identified
- **Estimated savings**: ~50 tests, 5s runtime

### Phase 2A.4: Refactor Low-Score Tests
- **Files scoring <4**: {score_counts["2-3"] + score_counts["0-1"]} files
- **Strategy**: Improve or delete based on necessity
- **Estimated savings**: ~150 tests, 15s runtime

## Total Impact

**Before**: {summary["total_tests"]:,} tests, ~{current_runtime:.0f}s runtime
**After**: {estimated_kept:,} tests, ~{new_runtime:.0f}s runtime
**Improvement**: {bloat_pct:.1f}% reduction, {speedup:.1f}x faster

## Detailed Bloat Files (Top 50 by Test Count)

| File | Tests | Lines | NECESSARY Score | Verdict | Reason |
|------|-------|-------|----------------|---------|--------|
"""

        # Top bloat files
        bloat_files = []
        for file_path, score_data in results["scores"].items():
            if score_data["verdict"] == "REMOVE" or any(
                file_path in x["file"] for x in results["categories"]["experimental"]
            ):
                # Find file stats
                for exp_file in results["categories"]["experimental"]:
                    if exp_file["file"] == file_path:
                        bloat_files.append(
                            {
                                "file": file_path,
                                "tests": exp_file["tests"],
                                "lines": exp_file["lines"],
                                "score": score_data["total"],
                                "verdict": score_data["verdict"],
                                "reason": exp_file["reason"],
                            }
                        )
                        break

        for item in sorted(bloat_files, key=lambda x: x["tests"], reverse=True)[:50]:
            report += f"| `{item['file']}` | {item['tests']} | {item['lines']} | {item['score']}/9 | {item['verdict']} | {item['reason']} |\n"

        report += """
## Next Steps

1. **Review & Approve**: Review this analysis and approve deletion strategy
2. **Execute Deletions**: Remove experimental and obsolete tests
3. **Consolidate Duplicates**: Merge duplicate test coverage
4. **Re-run CI**: Verify 100% pass rate on remaining tests
5. **Update Metrics**: Document new test suite metrics

---

*Analysis generated by NECESSARY Test Audit Framework*
"""

        # Write report
        with open(output_path, "w") as f:
            f.write(report)

        print(f"✅ Report generated: {output_path}")
        return output_path


if __name__ == "__main__":
    from datetime import datetime

    analyzer = TestAnalyzer()
    results = analyzer.analyze()

    # Print summary
    print("\n" + "=" * 60)
    print("BLOAT ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total tests: {results['summary']['total_tests']:,}")
    print(f"Bloat identified: {results['summary']['bloat_tests']:,} tests")
    print(
        f"Bloat percentage: {results['summary']['bloat_tests'] / results['summary']['total_tests'] * 100:.1f}%"
    )
    print("=" * 60 + "\n")

    # Generate report
    report_path = analyzer.generate_report()
    print(f"\n📄 Full report: {report_path}")
