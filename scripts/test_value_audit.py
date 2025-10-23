#!/usr/bin/env python3
"""
Test Value Scoring Audit - VALUE-FIRST Testing Philosophy

Constitutional Mandate (Article VI): Quality > Quantity
- High-value tests (integration, critical path, security)
- Delete low-value tests (mocking hell, implementation details)
- Goal: 2,000-3,000 tests that catch REAL bugs

Scoring Formula:
  value = (bug_detection * 10) + (critical_path * 5) - (runtime * 0.1) - (maintenance_burden * 2) + (integration_bonus * 3)

Categories:
  - HIGH (>20): Keep - Integration, critical path, security
  - MEDIUM (10-20): Review - Complex algorithms, edge cases
  - LOW (<10): DELETE - Mocking hell, implementation details, redundant
"""

import ast
import json
import re
import os
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional
from collections import defaultdict
import time

@dataclass
class TestScore:
    """Test value score with breakdown."""
    name: str
    file: str
    line: int

    # Score components
    bug_detection_score: float  # 0-10 (real bugs caught)
    critical_path_score: float  # 0-10 (tests core logic)
    integration_score: float    # 0-10 (tests real components)
    runtime_penalty: float      # Negative (slow tests penalized)
    maintenance_burden: float   # Negative (breaks on refactor)

    # Final score
    total_score: float
    category: str  # HIGH, MEDIUM, LOW

    # Recommendation
    action: str  # KEEP, REVIEW, DELETE, CONSOLIDATE
    reason: str

    # Metadata
    lines_of_code: int
    mock_count: int
    assertion_count: int
    has_fixtures: bool
    is_integration: bool
    is_e2e: bool

    # V5 additions (optional, defaults for backward compatibility)
    actual_runtime_seconds: float = 0.0
    runtime_source: str = "heuristic"
    ci_failures_total: int = 0
    ci_failures_fixed: int = 0
    is_flaky: bool = False
    failure_bonus: float = 0.0
    git_commits: int = 0
    git_co_changes: int = 0
    git_age_years: float = 0.0
    churn_burden: float = 0.0

class TestValueAuditor:
    """Score tests by actual value, not coverage."""

    def __init__(self, enable_v5: bool = True):
        """
        Initialize test value auditor.

        Args:
            enable_v5: Enable V5 empirical scoring if data available (default: True)
                      Set to False to force V4 heuristic mode.
        """
        self.tests: List[TestScore] = []
        self.stats = defaultdict(int)

        # V5 initialization (conditional)
        self.v5_enabled = enable_v5 and self._detect_v5_mode()

        # V5 component availability flags
        self.v5_runtime_available = False
        self.v5_failures_available = False
        self.v5_git_available = False
        self.weights = None
        self.runtime_parser = None
        self.failure_calculator = None
        self.git_analyzer = None
        self.normalizer = None

        # Runtime source for tracking
        self._runtime_source = "heuristic"

        if self.v5_enabled:
            self._initialize_v5_modules()
        else:
            logging.info("V5 mode disabled, using V4 heuristics")

    def _detect_v5_mode(self) -> bool:
        """
        Auto-detect if V5 mode should be enabled.

        Checks:
        1. Environment variable override (AUDIT_USE_V5)
        2. Presence of any V5 data sources
        """
        # Check environment variable override
        env_override = os.getenv('AUDIT_USE_V5', 'true').lower()
        if env_override == 'false':
            logging.info("V5 mode disabled via AUDIT_USE_V5 environment variable")
            return False

        # Check for any V5 data source (use cwd-relative paths)
        cwd = Path.cwd()
        has_weights = (cwd / 'weights.yaml').exists()
        has_runtime_cache = (cwd / '.audit' / 'runtime_cache.json').exists()
        has_ci_database = (cwd / '.audit' / 'failure_history.sqlite').exists()
        has_git = (cwd / '.git').exists()

        return has_weights or has_runtime_cache or has_ci_database or has_git

    def _initialize_v5_modules(self):
        """Initialize V5 modules with graceful fallback."""
        try:
            # Import V5 components (with sys.path adjustment)
            import sys
            from pathlib import Path
            scripts_path = Path(__file__).parent
            if str(scripts_path) not in sys.path:
                sys.path.insert(0, str(scripts_path))

            from weights_loader import WeightsLoader
            from runtime_data_parser import RuntimeDataParser
            from git_churn_analyzer import GitChurnAnalyzer
            from failure_bonus import FailureBonusCalculator
            try:
                from score_normalization import ScoreNormalizer
            except ImportError:
                ScoreNormalizer = None

            # Use cwd-relative paths for all data sources
            cwd = Path.cwd()

            # Load weights
            weights_path = cwd / 'weights.yaml'
            if weights_path.exists():
                loader = WeightsLoader(weights_path=weights_path)
                self.weights = loader.load()
                logging.info("✅ Loaded weights from weights.yaml")
            else:
                logging.info("ℹ️  weights.yaml not found, using default weights")

            # Initialize runtime parser
            runtime_cache_path = cwd / '.audit' / 'runtime_cache.json'
            if runtime_cache_path.exists():
                self.runtime_parser = RuntimeDataParser()
                self.runtime_parser.load_cached_runtimes(runtime_cache_path)
                self.v5_runtime_available = True
                logging.info("✅ Loaded runtime data from cache")
            else:
                logging.info("ℹ️  Runtime cache not found (.audit/runtime_cache.json)")
                logging.info("   Using heuristic runtime estimates")

            # Initialize CI failure calculator
            ci_db_path = cwd / '.audit' / 'failure_history.sqlite'
            if ci_db_path.exists():
                self.failure_calculator = FailureBonusCalculator(db_path=ci_db_path)
                self.v5_failures_available = True
                logging.info("✅ Loaded CI failure history")
            else:
                logging.info("ℹ️  CI failure database not found (.audit/failure_history.sqlite)")
                logging.info("   Tests will not receive CI failure bonuses")

            # Initialize git analyzer
            git_path = cwd / '.git'
            if git_path.exists():
                try:
                    import subprocess
                    result = subprocess.run(['git', 'status'], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        self.git_analyzer = GitChurnAnalyzer()
                        self.v5_git_available = True
                        logging.info("✅ Git repository detected (churn analysis enabled)")
                    else:
                        logging.info("ℹ️  Not a git repository (churn analysis skipped)")
                except Exception:
                    logging.info("ℹ️  Git command not available (churn analysis skipped)")
            else:
                logging.info("ℹ️  No .git directory (churn analysis skipped)")

            # Initialize normalizer
            if ScoreNormalizer:
                self.normalizer = ScoreNormalizer(mode='none')  # Default to no normalization
            else:
                self.normalizer = None

            logging.info(f"V5 mode active: runtime={self.v5_runtime_available}, "
                        f"ci={self.v5_failures_available}, git={self.v5_git_available}")

        except ImportError as e:
            logging.warning(f"V5 initialization failed: {e}, falling back to V4")
            self.v5_enabled = False
        except Exception as e:
            logging.warning(f"V5 initialization error: {e}, falling back to V4")
            self.v5_enabled = False

    def extract_test_functions(self, test_dir: Path = Path("tests")) -> List[Dict]:
        """Extract all test functions from test files."""
        print("🔍 Extracting test functions...")
        tests = []
        test_dir = test_dir.absolute()

        for test_file in test_dir.rglob("test_*.py"):
            if test_file.name.startswith("__"):
                continue

            try:
                with open(test_file, 'r') as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(test_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        tests.append({
                            'name': node.name,
                            'file': str(test_file.relative_to(Path.cwd())),
                            'line': node.lineno,
                            'code': ast.get_source_segment(content, node) or ast.unparse(node)
                        })

            except Exception as e:
                # Skip unparseable files silently
                continue

        print(f"  ✅ Found {len(tests)} test functions")
        return tests

    def _get_runtime(self, test_name: str, test_code: str) -> float:
        """Get runtime with V5/V4 fallback."""
        if self.v5_runtime_available and self.runtime_parser:
            test_id = f"tests/{test_name}"  # Simplified for now
            runtime = self.runtime_parser.get_runtime(test_id, test_code)
            if runtime > 0:
                self._runtime_source = "junitxml"
                return runtime

        # Fallback to heuristics
        self._runtime_source = "heuristic"
        return self.runtime_parser.estimate_runtime_from_heuristics(test_code, test_name) if self.runtime_parser else self._estimate_runtime_fallback(test_code, test_name)

    def _estimate_runtime_fallback(self, test_code: str, test_name: str) -> float:
        """Fallback runtime estimation when no parser available."""
        code_lower = test_code.lower()
        name_lower = test_name.lower()

        # Check code patterns first (more specific than name patterns)
        # E2E markers in code
        if any(k in code_lower for k in ['requests.', 'httpx.', 'selenium', 'playwright']):
            return 20.0

        # Database tests (check code, not just name)
        if any(k in code_lower for k in ['session.commit', 'db.', 'session.query', 'execute(']):
            return 5.0

        # Filesystem operations
        if any(k in code_lower for k in ['open(', 'path.write', 'path.read']):
            return 2.0

        # Mock-heavy tests (moderate)
        mock_count = code_lower.count('mock') + code_lower.count('patch')
        if mock_count > 5:
            return 1.0

        # E2E and integration tests (only check name if code didn't match specific patterns)
        if any(k in name_lower for k in ['e2e', 'end_to_end']):
            return 30.0
        # Integration is less specific, so use moderate estimate
        if 'integration' in name_lower:
            return 10.0

        # Simple unit tests (fast)
        return 0.1

    def _get_failure_bonus(self, test_id: str) -> float:
        """Get CI failure bonus with V5/V4 fallback."""
        if self.v5_failures_available and self.failure_calculator:
            return self.failure_calculator.calculate_bonus(test_id)
        return 0.0

    def _get_churn_burden(self, test_file: str) -> float:
        """Get git churn burden with V5/V4 fallback."""
        if self.v5_git_available and self.git_analyzer:
            try:
                metrics = self.git_analyzer.get_test_churn_metrics(Path(test_file))
                return self.git_analyzer.calculate_maintenance_burden(metrics)
            except Exception:
                return 0.0
        return 0.0

    def _get_scoring_mode(self) -> str:
        """Get current scoring mode."""
        if not self.v5_enabled:
            return "V4_FALLBACK"

        if self.v5_runtime_available and self.v5_failures_available and self.v5_git_available:
            return "V5_FULL"
        elif self.v5_runtime_available or self.v5_failures_available or self.v5_git_available:
            return "V5_PARTIAL"
        else:
            return "V4_FALLBACK"

    def _log_initialization(self):
        """Log initialization status."""
        mode = self._get_scoring_mode()
        print(f"Scoring mode: {mode}")

    def _log_data_sources(self):
        """Log data source availability."""
        print(f"Data sources: runtime={self.v5_runtime_available}, "
              f"ci={self.v5_failures_available}, git={self.v5_git_available}")

    def _log_fallback_warnings(self):
        """Log warnings about missing data sources."""
        if not self.v5_runtime_available:
            print("⚠️  Runtime cache not available, using heuristic estimates")
        if not self.v5_failures_available:
            print("⚠️  CI failure database not available")
        if not self.v5_git_available:
            print("⚠️  Git churn analysis not available")

    def score_test(self, test: Dict) -> TestScore:
        """Score a test's actual value."""
        name = test['name']
        file = test['file']
        code = test['code']
        test_id = f"{file}::{name}"

        # Count code metrics
        lines = len(code.split('\n'))
        mock_count = code.count('Mock') + code.count('mock') + code.count('patch')
        assertion_count = code.count('assert')
        has_fixtures = bool(re.search(r'def test_\w+\([^)]+\)', code))

        # Detect test type
        is_integration = self._is_integration_test(file, code)
        is_e2e = self._is_e2e_test(file, code, name)

        # Score components (V4 base)
        bug_detection = self._score_bug_detection(name, code, is_integration, is_e2e)
        critical_path = self._score_critical_path(file, name, code)
        integration = self._score_integration(code, mock_count, is_integration, is_e2e)

        # V5 enhancements with fallback
        actual_runtime = self._get_runtime(name, code)
        runtime_penalty = self._estimate_runtime_penalty(code, is_integration, is_e2e)
        failure_bonus = self._get_failure_bonus(test_id)
        churn_burden = self._get_churn_burden(file)

        # Maintenance burden (V4 + V5)
        base_burden = self._score_maintenance_burden(mock_count, lines, code)
        maintenance_burden = base_burden + churn_burden

        # Calculate total (V4 formula for now)
        total = (
            bug_detection * 10 +
            critical_path * 5 +
            integration * 3 -
            runtime_penalty * 0.1 -
            maintenance_burden * 2 +
            failure_bonus
        )

        # Categorize
        if total >= 20:
            category = "HIGH"
            action = "KEEP"
            reason = "High-value test (integration, critical path, or security)"
        elif total >= 10:
            category = "MEDIUM"
            action = "REVIEW"
            reason = "Medium value - consolidate or improve"
        else:
            category = "LOW"
            action = "DELETE"
            reason = self._deletion_reason(mock_count, lines, code, assertion_count)

        # Special cases
        if mock_count > 10 and assertion_count < 3:
            action = "DELETE"
            reason = "Mocking hell - mocks everything, tests nothing"

        if self._is_redundant_test(name):
            action = "CONSOLIDATE"
            reason = "Redundant test - parameterize similar tests"

        # Build V5-enhanced score
        return TestScore(
            name=name,
            file=file,
            line=test['line'],
            bug_detection_score=bug_detection,
            critical_path_score=critical_path,
            integration_score=integration,
            runtime_penalty=runtime_penalty,
            maintenance_burden=maintenance_burden,
            total_score=round(total, 2),
            category=category,
            action=action,
            reason=reason,
            lines_of_code=lines,
            mock_count=mock_count,
            assertion_count=assertion_count,
            has_fixtures=has_fixtures,
            is_integration=is_integration,
            is_e2e=is_e2e,
            # V5 additions
            actual_runtime_seconds=actual_runtime,
            runtime_source=self._runtime_source,
            failure_bonus=failure_bonus,
            churn_burden=churn_burden,
        )

    def _is_integration_test(self, file: str, code: str) -> bool:
        """Detect integration tests."""
        # Integration test patterns
        integration_markers = [
            'integration' in file.lower(),
            'e2e' in file.lower(),
            '@pytest.mark.integration' in code,
            'docker' in code.lower(),
            'real_' in code.lower(),
            'firestore' in code.lower() and 'Mock' not in code,
        ]
        return any(integration_markers)

    def _is_e2e_test(self, file: str, code: str, name: str) -> bool:
        """Detect end-to-end tests."""
        e2e_markers = [
            'e2e' in file.lower(),
            'end_to_end' in name.lower(),
            'workflow' in name.lower(),
            'primeA' in code or 'primeccc' in code,
            'orchestrator' in code.lower() and 'run(' in code,
        ]
        return any(e2e_markers)

    def _score_bug_detection(self, name: str, code: str, is_integration: bool, is_e2e: bool) -> float:
        """Score bug detection potential (0-10)."""
        score = 0.0

        # E2E tests catch the most bugs
        if is_e2e:
            score += 10.0
        # Integration tests catch many bugs
        elif is_integration:
            score += 8.0
        # Security tests catch critical bugs
        elif any(kw in name.lower() for kw in ['security', 'injection', 'xss', 'csrf', 'auth']):
            score += 9.0
        # Regression tests (verified bugs)
        elif 'regression' in name.lower() or 'bug' in name.lower():
            score += 7.0
        # Edge cases catch some bugs
        elif any(kw in name.lower() for kw in ['edge', 'boundary', 'limit']):
            score += 5.0
        # Error handling tests
        elif any(kw in code.lower() for kw in ['raises', 'exception', 'error']):
            score += 4.0
        # Basic unit tests
        else:
            score += 2.0

        return min(score, 10.0)

    def _score_critical_path(self, file: str, name: str, code: str) -> float:
        """Score if test covers critical business logic (0-10)."""
        score = 0.0

        # Core orchestrators
        if 'orchestrator' in file and any(kw in name for kw in ['primeA', 'primeccc']):
            score += 10.0
        # Authentication/authorization
        elif any(kw in file for kw in ['auth', 'security', 'permission']):
            score += 9.0
        # Data integrity
        elif any(kw in file for kw in ['memory', 'storage', 'persistence']):
            score += 8.0
        # Agent coordination
        elif 'agent' in file and 'integration' in file:
            score += 7.0
        # Core utilities
        elif any(kw in file for kw in ['result', 'type_definitions']):
            score += 6.0
        # Helper utilities
        else:
            score += 3.0

        return min(score, 10.0)

    def _score_integration(self, code: str, mock_count: int, is_integration: bool, is_e2e: bool) -> float:
        """Score integration level (0-10)."""
        if is_e2e:
            return 10.0
        if is_integration:
            return 8.0

        # More mocks = less integration = lower score
        if mock_count == 0:
            return 7.0  # No mocks = real components
        elif mock_count <= 2:
            return 5.0  # Few mocks = some integration
        elif mock_count <= 5:
            return 3.0  # Many mocks = low integration
        else:
            return 1.0  # Mocking hell = no integration

    def _estimate_runtime_penalty(self, code: str, is_integration: bool, is_e2e: bool) -> float:
        """Estimate runtime penalty (higher = slower)."""
        penalty = 0.0

        if is_e2e:
            penalty += 10.0  # E2E tests are slow but valuable
        elif is_integration:
            penalty += 5.0

        # Check for slow operations
        if 'sleep' in code.lower():
            penalty += 5.0
        if 'docker' in code.lower():
            penalty += 3.0
        if 'time.time()' in code:
            penalty += 1.0

        return penalty

    def _score_maintenance_burden(self, mock_count: int, lines: int, code: str) -> float:
        """Score maintenance burden (higher = more breakage)."""
        burden = 0.0

        # Mocking increases fragility
        burden += mock_count * 0.5

        # Long tests are hard to maintain
        if lines > 100:
            burden += 3.0
        elif lines > 50:
            burden += 1.5

        # Testing implementation details
        if 'assert_called' in code:
            burden += 2.0  # Tests HOW, not WHAT
        if '.call_count' in code:
            burden += 1.5

        # Magic numbers (brittle)
        magic_numbers = len(re.findall(r'== \d+', code))
        burden += magic_numbers * 0.3

        return burden

    def _deletion_reason(self, mock_count: int, lines: int, code: str, assertion_count: int) -> str:
        """Generate specific deletion reason."""
        reasons = []

        if mock_count > 10:
            reasons.append("Mocking hell (10+ mocks)")

        if assertion_count == 0:
            reasons.append("No assertions")

        if 'assert_called' in code and assertion_count < 3:
            reasons.append("Tests implementation, not behavior")

        if lines > 100 and mock_count > 5:
            reasons.append("Long + many mocks = fragile")

        if not reasons:
            reasons.append("Low value score")

        return "; ".join(reasons)

    def _is_redundant_test(self, name: str) -> bool:
        """Detect redundant tests (candidates for parameterization)."""
        # Pattern: test_foo_with_int, test_foo_with_string, etc.
        base_patterns = [
            r'test_\w+_with_\w+$',
            r'test_\w+_\d+$',
            r'test_\w+_when_\w+$',
        ]
        return any(re.match(pattern, name) for pattern in base_patterns)

    def run_audit(self, test_dir: Path = Path("tests")) -> Dict:
        """Run complete test value audit."""
        print("="*80)
        print("🎯 TEST VALUE AUDIT - VALUE-FIRST TESTING (Article VI)")
        print("="*80)
        print()
        print("Philosophy: Quality > Quantity")
        print("Goal: 2,000-3,000 HIGH-VALUE tests that catch REAL bugs")
        print()

        start_time = time.time()

        # Extract tests
        test_functions = self.extract_test_functions(test_dir)

        # Score each test
        print()
        print("📊 Scoring tests by value...")
        for i, test in enumerate(test_functions, 1):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(test_functions)} ({i*100//len(test_functions)}%)")

            score = self.score_test(test)
            self.tests.append(score)
            self.stats[score.action] += 1

        elapsed = time.time() - start_time

        # Generate report
        self._print_summary(elapsed)

        return self._generate_results()

    def _print_summary(self, elapsed: float):
        """Print audit summary."""
        total = len(self.tests)

        print()
        print("="*80)
        print("✅ AUDIT COMPLETE")
        print("="*80)
        print(f"Execution Time: {elapsed:.1f} seconds")
        print(f"Tests Analyzed: {total:,}")
        print()

        print("📊 VALUE DISTRIBUTION")
        print("-"*80)

        high = sum(1 for t in self.tests if t.category == "HIGH")
        medium = sum(1 for t in self.tests if t.category == "MEDIUM")
        low = sum(1 for t in self.tests if t.category == "LOW")

        high_pct = (high*100//total) if total > 0 else 0
        medium_pct = (medium*100//total) if total > 0 else 0
        low_pct = (low*100//total) if total > 0 else 0

        print(f"HIGH (>20):   {high:4,} ({high_pct:3}%) - KEEP - Integration, critical path")
        print(f"MEDIUM (10-20): {medium:4,} ({medium_pct:3}%) - REVIEW - Consolidate or improve")
        print(f"LOW (<10):    {low:4,} ({low_pct:3}%) - DELETE - Mocking hell, low value")
        print()

        print("🎯 RECOMMENDED ACTIONS")
        print("-"*80)
        keep = self.stats['KEEP']
        review = self.stats['REVIEW']
        delete = self.stats['DELETE']
        consolidate = self.stats['CONSOLIDATE']

        keep_pct = (keep*100//total) if total > 0 else 0
        review_pct = (review*100//total) if total > 0 else 0
        delete_pct = (delete*100//total) if total > 0 else 0
        consolidate_pct = (consolidate*100//total) if total > 0 else 0

        print(f"KEEP:        {keep:4,} ({keep_pct:3}%) - High-value tests")
        print(f"REVIEW:      {review:4,} ({review_pct:3}%) - Medium-value, improve")
        print(f"DELETE:      {delete:4,} ({delete_pct:3}%) - Low-value, remove")
        print(f"CONSOLIDATE: {consolidate:4,} ({consolidate_pct:3}%) - Redundant, parameterize")
        print()

        # Projected outcomes
        final_count = keep + review + (consolidate // 3)  # Consolidate reduces count by 2/3
        print("📈 PROJECTED OUTCOMES")
        print("-"*80)
        print(f"Current tests:     {total:,}")
        if total > 0:
            print(f"After deletion:    {total - delete:,} (-{delete*100//total}%)")
            if final_count > 0:
                print(f"After consolidation: {final_count:,} (-{(total-final_count)*100//total}%)")
                print(f"CI/CD speedup:     ~{total // final_count}x faster")
        else:
            print("  No tests found - check test directory")
        print()

    def _generate_results(self) -> Dict:
        """Generate results dict with V5 metadata."""
        # Build warnings list
        warnings = []
        if not self.v5_runtime_available:
            warnings.append("Runtime cache not found, using heuristic estimates")
        if not self.v5_failures_available:
            warnings.append("CI failure database not found, no failure bonuses")
        if not self.v5_git_available:
            warnings.append("Git repository not detected, no churn analysis")
        if not self.weights:
            warnings.append("weights.yaml not found, using default weights")

        return {
            'metadata': {
                'scoring_version': self._get_scoring_mode(),
                'v5_enabled': self.v5_enabled,
                'runtime_source': self._runtime_source if self.v5_runtime_available else 'heuristic',
                'ci_failures_source': 'sqlite' if self.v5_failures_available else 'none',
                'git_churn_source': 'git' if self.v5_git_available else 'none',
                'weights_source': 'weights.yaml' if self.weights else 'default',
                'data_availability': {
                    'runtime': self.v5_runtime_available,
                    'ci_failures': self.v5_failures_available,
                    'git_churn': self.v5_git_available,
                    'weights': self.weights is not None,
                },
                'warnings': warnings if warnings else [],
            },
            'summary': {
                'total_tests': len(self.tests),
                'high_value': sum(1 for t in self.tests if t.category == "HIGH"),
                'medium_value': sum(1 for t in self.tests if t.category == "MEDIUM"),
                'low_value': sum(1 for t in self.tests if t.category == "LOW"),
                'keep': self.stats['KEEP'],
                'review': self.stats['REVIEW'],
                'delete': self.stats['DELETE'],
                'consolidate': self.stats['CONSOLIDATE'],
            },
            'tests': [asdict(t) for t in self.tests]
        }

    def save_results(self, output_dir: Path = Path("audit_reports")):
        """Save audit results."""
        output_dir.mkdir(exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S')

        # JSON results
        json_path = output_dir / f"test_value_audit_{timestamp}.json"
        results = self._generate_results()
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"  ✅ JSON: {json_path}")

        # Deletion candidates
        delete_candidates = [t for t in self.tests if t.action == "DELETE"]
        delete_path = output_dir / f"candidates_to_delete_{timestamp}.txt"
        with open(delete_path, 'w') as f:
            f.write(f"# {len(delete_candidates)} tests to DELETE\n")
            f.write(f"# Low-value tests (score < 10)\n\n")
            for test in sorted(delete_candidates, key=lambda t: t.total_score):
                f.write(f"{test.file}::{test.name}\n")
                f.write(f"  Score: {test.total_score:.1f}\n")
                f.write(f"  Reason: {test.reason}\n\n")
        print(f"  ✅ Delete candidates: {delete_path}")

        # Consolidation candidates
        consolidate_candidates = [t for t in self.tests if t.action == "CONSOLIDATE"]
        consolidate_path = output_dir / f"candidates_to_consolidate_{timestamp}.txt"
        with open(consolidate_path, 'w') as f:
            f.write(f"# {len(consolidate_candidates)} tests to CONSOLIDATE\n")
            f.write(f"# Redundant tests (parameterize)\n\n")
            for test in consolidate_candidates:
                f.write(f"{test.file}::{test.name}\n")
        print(f"  ✅ Consolidate candidates: {consolidate_path}")

        # High-value tests
        high_value = [t for t in self.tests if t.action == "KEEP"]
        keep_path = output_dir / f"high_value_tests_{timestamp}.txt"
        with open(keep_path, 'w') as f:
            f.write(f"# {len(high_value)} HIGH-VALUE tests to KEEP\n")
            f.write(f"# Integration, critical path, security\n\n")
            for test in sorted(high_value, key=lambda t: -t.total_score):
                f.write(f"{test.file}::{test.name}\n")
                f.write(f"  Score: {test.total_score:.1f}\n")
                if test.is_e2e:
                    f.write(f"  Type: E2E\n")
                elif test.is_integration:
                    f.write(f"  Type: Integration\n")
                f.write("\n")
        print(f"  ✅ High-value tests: {keep_path}")

        print()
        print("📄 Audit complete. Review files above before deletion.")

def main():
    auditor = TestValueAuditor()
    auditor.run_audit()
    auditor.save_results()

    print()
    print("🎯 NEXT STEPS:")
    print("1. Review deletion candidates (audit_reports/candidates_to_delete_*.txt)")
    print("2. Manually verify top 100 deletions")
    print("3. Run: python scripts/batch_delete_tests.py --from approved_deletions.txt")
    print("4. Consolidate redundant tests (parameterize)")
    print("5. Verify test suite still passes: pytest tests/")
    print()
    print("Goal: 2,000-3,000 HIGH-VALUE tests that catch REAL bugs")
    print("Quality > Quantity. Always.")

if __name__ == "__main__":
    main()
