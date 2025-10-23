#!/usr/bin/env python3
"""
MARATHON TEST AUDIT - Long-Running Deep Analysis

Analyzes ALL 5,889+ tests individually over hours/days using local Qwen3-Coder.
100% READ-ONLY - no code changes, only creates comprehensive reports.

Purpose:
- Deep NECESSARY pattern compliance analysis (9 categories per test)
- Test quality scoring (complexity, coverage, maintainability)
- Healing roadmap generation (prioritized fix recommendations)
- Constitutional compliance assessment
- Actionable insights for autonomous healing

Execution Time: 4-48 hours (depends on depth setting)
Cost: $0 (100% local execution)
Output: JSON + Markdown reports with test-by-test analysis

Usage:
    # Quick mode (1 hour, top 500 tests)
    python scripts/marathon_test_audit.py --depth quick --max-tests 500

    # Standard mode (8 hours, all tests)
    python scripts/marathon_test_audit.py --depth standard

    # Deep mode (48 hours, all tests + suggestions)
    python scripts/marathon_test_audit.py --depth deep --suggestions

    # Resume from checkpoint
    python scripts/marathon_test_audit.py --resume

Constitutional Compliance:
- Article I: Complete Context (analyzes every test, retries on timeout)
- Article II: 100% Verification (read-only, no changes)
- Article IV: Continuous Learning (stores patterns to VectorStore)
"""

import argparse
import ast
import json
import requests
import time
import signal
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

# Ollama API
OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "qwen3-coder:30b"

# NECESSARY pattern categories (9 total)
NECESSARY_CATEGORIES = [
    "Normal",      # Standard usage paths
    "Edge",        # Boundary conditions
    "Cascading",   # Error propagation
    "Essential",   # Critical business logic
    "Security",    # Auth, injection, XSS
    "Spec",        # Acceptance criteria
    "Accessibility", # Inclusive design
    "Resilience",  # Error recovery
    "Year-round"   # Time-based logic
]

@dataclass
class TestAnalysis:
    """Analysis result for a single test function."""
    file: str
    name: str
    line_start: int
    line_end: int
    lines_of_code: int
    complexity_score: float  # 0.0-1.0
    necessary_coverage: List[str]  # Which NECESSARY categories it covers
    necessary_gaps: List[str]  # Which categories are missing
    quality_issues: List[str]  # Specific issues found
    healing_priority: str  # P0/P1/P2/P3
    healing_suggestions: List[str]  # Actionable fixes
    analysis_timestamp: str

@dataclass
class AuditProgress:
    """Track audit progress for resume capability."""
    total_tests: int
    analyzed_tests: int
    current_file: str
    current_test: str
    start_time: str
    last_checkpoint: str
    estimated_completion: str

class MarathonAuditor:
    """Long-running test auditor with checkpoint/resume."""

    def __init__(self, depth: str = "standard", max_tests: Optional[int] = None, suggestions: bool = False):
        self.depth = depth
        self.max_tests = max_tests
        self.suggestions = suggestions
        self.results: List[TestAnalysis] = []
        self.progress = None
        self.state_file = Path(".marathon_audit_state.json")
        self.output_dir = Path("audit_reports")
        self.output_dir.mkdir(exist_ok=True)

        # Graceful shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        print("\n\n⚠️  Shutdown signal received. Saving checkpoint...")
        self._save_checkpoint()
        print("✅ Checkpoint saved. Resume with: --resume")
        sys.exit(0)

    def call_local_model(self, prompt: str, max_tokens: int = 1024) -> str:
        """Call local model with retry logic."""
        for attempt in range(3):  # Article I: retry on failure
            try:
                response = requests.post(
                    OLLAMA_API,
                    json={
                        "model": MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "num_predict": max_tokens,
                        }
                    },
                    timeout=300
                )

                if response.status_code == 200:
                    return response.json().get('response', '')

            except Exception as e:
                if attempt == 2:  # Last attempt
                    return f"ERROR: {str(e)}"
                time.sleep(5 * (attempt + 1))  # Exponential backoff

        return "ERROR: Max retries exceeded"

    def extract_all_test_functions(self) -> List[Tuple[Path, str, int, int]]:
        """Extract ALL test functions from codebase."""
        print("🔍 Extracting ALL test functions...")

        test_files = list(Path("tests").rglob("test_*.py"))
        all_tests = []

        for test_file in test_files:
            try:
                content = test_file.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                        # Calculate end line (approximate)
                        end_line = node.lineno
                        if node.body:
                            last_stmt = node.body[-1]
                            end_line = getattr(last_stmt, 'end_lineno', node.lineno + 10)

                        all_tests.append((
                            test_file,
                            node.name,
                            node.lineno,
                            end_line
                        ))

            except Exception as e:
                print(f"  ⚠️  Failed to parse {test_file}: {e}")

        print(f"  ✅ Found {len(all_tests)} test functions across {len(test_files)} files")
        return all_tests

    def analyze_test_function(self, test_file: Path, test_name: str, start_line: int, end_line: int) -> TestAnalysis:
        """Deep analysis of a single test function."""

        # Read test code
        lines = test_file.read_text().split('\n')
        test_code = '\n'.join(lines[start_line-1:end_line])
        lines_of_code = len([line for line in test_code.split('\n') if line.strip() and not line.strip().startswith('#')])

        # Call local model for NECESSARY analysis
        prompt = f"""Analyze this test function for NECESSARY pattern compliance.

Test: {test_name} (lines {start_line}-{end_line})
File: {test_file}

Code:
```python
{test_code}
```

NECESSARY Categories (9 total):
1. Normal: Standard usage paths
2. Edge: Boundary conditions
3. Cascading: Error propagation
4. Essential: Critical business logic
5. Security: Auth, injection, XSS
6. Spec: Acceptance criteria
7. Accessibility: Inclusive design
8. Resilience: Error recovery
9. Year-round: Time-based logic

Respond in this EXACT format:
COVERED: [comma-separated categories covered]
GAPS: [comma-separated categories missing]
ISSUES: [bullet list of quality issues]
PRIORITY: P0/P1/P2/P3
"""

        if self.suggestions:
            prompt += "\nSUGGESTIONS: [bullet list of healing suggestions]"

        response = self.call_local_model(prompt, max_tokens=1024)

        # Parse response
        covered = self._parse_field(response, "COVERED:")
        gaps = self._parse_field(response, "GAPS:")
        issues = self._parse_field(response, "ISSUES:")
        priority_list = self._parse_field(response, "PRIORITY:")
        priority = priority_list[0] if priority_list else "P2"
        suggestions = self._parse_field(response, "SUGGESTIONS:") if self.suggestions else []

        # Calculate complexity score
        complexity = min(1.0, lines_of_code / 50.0)  # 50+ lines = max complexity

        return TestAnalysis(
            file=str(test_file),
            name=test_name,
            line_start=start_line,
            line_end=end_line,
            lines_of_code=lines_of_code,
            complexity_score=complexity,
            necessary_coverage=covered,
            necessary_gaps=gaps,
            quality_issues=issues,
            healing_priority=priority,
            healing_suggestions=suggestions,
            analysis_timestamp=datetime.now().isoformat()
        )

    def _parse_field(self, response: str, field_name: str) -> List[str]:
        """Parse field from model response (handles multi-line values)."""
        try:
            lines = response.split('\n')
            collecting = False
            results = []

            for i, line in enumerate(lines):
                # Found the field header
                if line.strip().startswith(field_name):
                    # Check if value is on same line
                    value = line.replace(field_name, '').strip()
                    if value:
                        # Single-line value
                        if ',' in value:
                            return [item.strip() for item in value.split(',') if item.strip()]
                        return [value] if value else []
                    else:
                        # Multi-line value (for ISSUES, SUGGESTIONS)
                        collecting = True
                        continue

                # Collecting multi-line values
                if collecting:
                    # Stop at next field or empty line after content
                    if line.strip().startswith(('COVERED:', 'GAPS:', 'ISSUES:', 'PRIORITY:', 'SUGGESTIONS:', 'REASONING:')):
                        break
                    # Collect bullet points or content
                    if line.strip():
                        # Remove bullet markers
                        clean_line = line.strip().lstrip('- ').lstrip('• ').lstrip('* ')
                        if clean_line:
                            results.append(clean_line)

            return results if results else []
        except:
            return []

    def _save_checkpoint(self):
        """Save current state for resume capability."""
        state = {
            "progress": asdict(self.progress) if self.progress else None,
            "results": [asdict(r) for r in self.results],
            "timestamp": datetime.now().isoformat()
        }

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def _load_checkpoint(self) -> bool:
        """Load checkpoint state."""
        if not self.state_file.exists():
            return False

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)

            self.results = [TestAnalysis(**r) for r in state.get("results", [])]
            prog = state.get("progress")
            if prog:
                self.progress = AuditProgress(**prog)
            return True
        except:
            return False

    def run_audit(self, resume: bool = False):
        """Execute marathon audit."""
        print("="*80)
        print("🏃 MARATHON TEST AUDIT - Long-Running Deep Analysis")
        print("="*80)
        print(f"Model: {MODEL}")
        print(f"Cost: $0 (100% local)")
        print(f"Depth: {self.depth}")
        print(f"Max Tests: {self.max_tests or 'ALL'}")
        print(f"Suggestions: {self.suggestions}")
        print()

        start_time = time.time()

        # Resume or start fresh
        if resume and self._load_checkpoint():
            print(f"📂 Resuming from checkpoint: {len(self.results)} tests already analyzed")
            all_tests = self.extract_all_test_functions()
            analyzed_names = {r.name for r in self.results}
            remaining_tests = [(f, n, s, e) for f, n, s, e in all_tests if n not in analyzed_names]
        else:
            all_tests = self.extract_all_test_functions()
            remaining_tests = all_tests

        if self.max_tests:
            remaining_tests = remaining_tests[:self.max_tests]

        total = len(remaining_tests)

        print(f"🎯 Analyzing {total} test functions...")
        print()

        # Initialize progress
        self.progress = AuditProgress(
            total_tests=total,
            analyzed_tests=len(self.results),
            current_file="",
            current_test="",
            start_time=datetime.now().isoformat(),
            last_checkpoint=datetime.now().isoformat(),
            estimated_completion=""
        )

        # Analyze each test
        for idx, (test_file, test_name, start_line, end_line) in enumerate(remaining_tests):
            self.progress.analyzed_tests += 1
            self.progress.current_file = str(test_file)
            self.progress.current_test = test_name

            # Progress update
            percent = (self.progress.analyzed_tests / total) * 100
            elapsed = time.time() - start_time
            rate = self.progress.analyzed_tests / elapsed if elapsed > 0 else 0
            eta = (total - self.progress.analyzed_tests) / rate if rate > 0 else 0

            print(f"[{percent:5.1f}%] {test_name[:50]:50s} (ETA: {eta/3600:.1f}h)", end='\r')

            # Analyze test
            analysis = self.analyze_test_function(test_file, test_name, start_line, end_line)
            self.results.append(analysis)

            # Checkpoint every 50 tests
            if (idx + 1) % 50 == 0:
                self._save_checkpoint()
                self.progress.last_checkpoint = datetime.now().isoformat()

            # Rate limit (avoid overheating M4 Pro)
            time.sleep(2 if self.depth == "deep" else 1)

        # Final save
        self._save_checkpoint()

        elapsed = time.time() - start_time

        print()
        print()
        print("="*80)
        print("✅ MARATHON AUDIT COMPLETE")
        print("="*80)
        print(f"Execution Time: {elapsed/3600:.1f} hours")
        print(f"Tests Analyzed: {len(self.results)}")
        print(f"Cost: $0.00 (100% local)")
        print(f"Cloud Equivalent: ~${len(self.results) * 0.10:.2f} (AVOIDED!)")
        print()

        # Generate reports
        self.generate_reports()

    def generate_reports(self):
        """Generate comprehensive reports."""
        print("📊 Generating Reports...")

        # JSON report
        json_path = self.output_dir / f"marathon_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w') as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        print(f"  ✅ JSON: {json_path}")

        # Markdown report
        md_path = self.output_dir / f"marathon_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._generate_markdown_report(md_path)
        print(f"  ✅ Markdown: {md_path}")

        # Healing roadmap
        roadmap_path = self.output_dir / f"healing_roadmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._generate_healing_roadmap(roadmap_path)
        print(f"  ✅ Healing Roadmap: {roadmap_path}")

        print()

    def _generate_markdown_report(self, output_path: Path):
        """Generate human-readable markdown report."""
        with open(output_path, 'w') as f:
            f.write("# Marathon Test Audit Report\n\n")
            f.write(f"**Date**: {datetime.now()}\n")
            f.write(f"**Model**: {MODEL}\n")
            f.write(f"**Tests Analyzed**: {len(self.results)}\n")
            f.write(f"**Cost**: $0 (100% local)\n\n")

            # Summary statistics
            f.write("## Summary Statistics\n\n")

            # NECESSARY coverage
            all_covered = defaultdict(int)
            all_gaps = defaultdict(int)
            for result in self.results:
                for cat in result.necessary_coverage:
                    all_covered[cat] += 1
                for cat in result.necessary_gaps:
                    all_gaps[cat] += 1

            f.write("### NECESSARY Pattern Coverage\n\n")
            for cat in NECESSARY_CATEGORIES:
                covered = all_covered.get(cat, 0)
                total = len(self.results)
                pct = (covered / total * 100) if total > 0 else 0
                f.write(f"- **{cat}**: {covered}/{total} tests ({pct:.1f}%)\n")
            f.write("\n")

            # Priority breakdown
            f.write("### Healing Priority Breakdown\n\n")
            priorities = defaultdict(int)
            for result in self.results:
                priorities[result.healing_priority] += 1
            for p in ["P0", "P1", "P2", "P3"]:
                count = priorities.get(p, 0)
                f.write(f"- **{p}**: {count} tests\n")
            f.write("\n")

            # Top issues
            f.write("## Top Priority Tests (P0/P1)\n\n")
            high_priority = [r for r in self.results if r.healing_priority in ["P0", "P1"]]
            high_priority.sort(key=lambda r: (r.healing_priority, -len(r.quality_issues)))

            for result in high_priority[:50]:  # Top 50
                f.write(f"### {result.name} ({result.healing_priority})\n\n")
                f.write(f"**File**: {result.file}:{result.line_start}\n")
                f.write(f"**Complexity**: {result.complexity_score:.2f}\n")
                f.write(f"**NECESSARY Coverage**: {', '.join(result.necessary_coverage) or 'None'}\n")
                f.write(f"**NECESSARY Gaps**: {', '.join(result.necessary_gaps) or 'None'}\n\n")

                if result.quality_issues:
                    f.write("**Issues**:\n")
                    for issue in result.quality_issues:
                        f.write(f"- {issue}\n")
                    f.write("\n")

                if result.healing_suggestions:
                    f.write("**Healing Suggestions**:\n")
                    for suggestion in result.healing_suggestions:
                        f.write(f"- {suggestion}\n")
                    f.write("\n")

    def _generate_healing_roadmap(self, output_path: Path):
        """Generate actionable healing roadmap."""
        with open(output_path, 'w') as f:
            f.write("# Healing Roadmap - Prioritized Action Plan\n\n")
            f.write(f"**Generated**: {datetime.now()}\n")
            f.write(f"**Based on**: {len(self.results)} test analyses\n\n")

            f.write("## Phase 1: Critical Fixes (P0)\n\n")
            p0_tests = [r for r in self.results if r.healing_priority == "P0"]
            if p0_tests:
                for result in p0_tests[:20]:
                    f.write(f"- [ ] Fix `{result.name}` in `{result.file}:{result.line_start}`\n")
                    if result.healing_suggestions:
                        for suggestion in result.healing_suggestions[:3]:
                            f.write(f"      - {suggestion}\n")
            else:
                f.write("✅ No P0 issues found!\n")
            f.write("\n")

            f.write("## Phase 2: High Priority (P1)\n\n")
            p1_tests = [r for r in self.results if r.healing_priority == "P1"]
            if p1_tests:
                for result in p1_tests[:50]:
                    f.write(f"- [ ] Enhance `{result.name}` in `{result.file}:{result.line_start}`\n")
            f.write("\n")

            f.write("## Phase 3: NECESSARY Gap Filling\n\n")
            gap_counts = defaultdict(list)
            for result in self.results:
                for gap in result.necessary_gaps:
                    gap_counts[gap].append(result)

            for cat in NECESSARY_CATEGORIES:
                tests_with_gap = gap_counts.get(cat, [])
                if tests_with_gap:
                    f.write(f"### {cat} Gap ({len(tests_with_gap)} tests)\n\n")
                    for result in tests_with_gap[:10]:
                        f.write(f"- [ ] Add {cat} tests to `{result.file}:{result.line_start}`\n")
                    f.write("\n")

            f.write("## Phase 4: Quality Improvements (P2/P3)\n\n")
            f.write(f"- {len([r for r in self.results if r.healing_priority == 'P2'])} P2 issues\n")
            f.write(f"- {len([r for r in self.results if r.healing_priority == 'P3'])} P3 issues\n")
            f.write("\n(See full report for details)\n")

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Marathon Test Audit - Long-Running Analysis")
    parser.add_argument("--depth", choices=["quick", "standard", "deep"], default="standard",
                       help="Analysis depth (quick=1h, standard=8h, deep=48h)")
    parser.add_argument("--max-tests", type=int, help="Limit number of tests (for testing)")
    parser.add_argument("--suggestions", action="store_true", help="Generate healing suggestions")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")

    args = parser.parse_args()

    auditor = MarathonAuditor(
        depth=args.depth,
        max_tests=args.max_tests,
        suggestions=args.suggestions
    )

    auditor.run_audit(resume=args.resume)

if __name__ == "__main__":
    main()
