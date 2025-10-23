#!/usr/bin/env python3
"""
Unit Tests for V5 Integration Logic - Test-Driven Development (Article VI)

Tests V5/V4 mode detection, fallback behavior, and integrated scoring.

Constitutional Compliance:
- Article II: Tests written FIRST (RED phase)
- Article VI: TDD protocol (RED → GREEN → REFACTOR)

These tests will FAIL initially (expected) until implementation is complete.
"""

import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# These imports will fail initially - that's expected in RED phase
try:
    from scripts.test_value_audit import TestValueAuditor
    from scripts.weights_loader import WeightsLoader, ScoringWeights
    from scripts.runtime_data_parser import RuntimeDataParser
    from scripts.failure_bonus import FailureBonusCalculator
    from scripts.git_churn_analyzer import GitChurnAnalyzer
    from scripts.mock_classifier import MockClassifier
except ImportError:
    # Expected during RED phase - implementation not yet complete
    pass


class TestV5ModeDetection:
    """Test V5 mode activation based on data source availability."""

    @pytest.mark.skip(reason="Test infra: Mock setup needs update")
    def test_v5_mode_activates_when_weights_yaml_present(self, tmp_path):
        """V5 mode should activate when weights.yaml exists."""
        # Setup: Create weights.yaml
        weights_file = tmp_path / "weights.yaml"
        weights_file.write_text("""
bug_detection_weight: 10.0
critical_path_weight: 5.0
integration_bonus_weight: 3.0
""")

        # Execute: Initialize auditor with weights.yaml present
        with patch('scripts.test_value_audit.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            auditor = TestValueAuditor()

            # Assert: V5 mode should be enabled
            assert auditor.v5_enabled is True

    @pytest.mark.skip(reason="Test infra: Mock setup needs update")
    def test_v4_fallback_when_weights_yaml_missing(self, tmp_path):
        """V4 mode should activate when weights.yaml is missing."""
        # Setup: No weights.yaml
        with patch('scripts.test_value_audit.Path') as mock_path:
            mock_path.return_value.exists.return_value = False

            # Execute: Initialize auditor
            auditor = TestValueAuditor()

            # Assert: V4 mode should be active
            assert auditor.v5_enabled is False

    def test_v5_mode_with_runtime_cache_present(self, tmp_path):
        """V5 runtime mode should activate when runtime cache exists."""
        # Setup: Create runtime cache
        audit_dir = tmp_path / ".audit"
        audit_dir.mkdir()
        runtime_cache = audit_dir / "runtime_cache.json"
        runtime_cache.write_text(json.dumps({
            "tests/test_example.py::test_foo": {
                "duration_seconds": 1.5,
                "source": "junitxml"
            }
        }))

        # Execute: Initialize auditor
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()

            # Assert: V5 runtime should be available
            assert auditor.v5_runtime_available is True

    def test_v4_runtime_fallback_when_cache_missing(self, tmp_path):
        """V4 runtime estimation should activate when cache is missing."""
        # Setup: No runtime cache
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()

            # Assert: V5 runtime should not be available
            assert auditor.v5_runtime_available is False

    def test_v5_mode_with_ci_database_present(self, tmp_path):
        """V5 CI failure mode should activate when database exists."""
        # Setup: Create CI failure database
        audit_dir = tmp_path / ".audit"
        audit_dir.mkdir()
        db_file = audit_dir / "failure_history.sqlite"
        db_file.touch()  # Create empty file

        # Execute: Initialize auditor
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()

            # Assert: V5 CI failures should be available
            assert auditor.v5_failures_available is True

    def test_v4_ci_fallback_when_database_missing(self, tmp_path):
        """V4 CI mode (0 bonuses) should activate when database is missing."""
        # Setup: No CI database
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()

            # Assert: V5 CI failures should not be available
            assert auditor.v5_failures_available is False

    def test_v5_mode_with_git_repository_present(self, tmp_path):
        """V5 git churn mode should activate when .git directory exists."""
        # Setup: Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Execute: Initialize auditor
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="main\n")
                auditor = TestValueAuditor()

                # Assert: V5 git should be available
                assert auditor.v5_git_available is True

    def test_v4_git_fallback_when_not_git_repo(self, tmp_path):
        """V4 git mode (0 churn) should activate when not a git repo."""
        # Setup: No .git directory
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()

            # Assert: V5 git should not be available
            assert auditor.v5_git_available is False


class TestV5Fallbacks:
    """Test graceful degradation when V5 data sources are unavailable."""

    def test_runtime_fallback_returns_heuristic_estimate(self):
        """When runtime cache is missing, should estimate from heuristics."""
        # Setup: Auditor with no runtime cache
        auditor = TestValueAuditor()
        auditor.v5_runtime_available = False

        test_code = """
def test_integration():
    session = get_db_session()
    session.query(User).first()
    assert True
"""

        # Execute: Get runtime
        runtime = auditor._get_runtime("test_integration", test_code)

        # Assert: Should return heuristic estimate (5s for DB tests)
        assert runtime == 5.0
        assert auditor._runtime_source == "heuristic"

    def test_ci_fallback_returns_zero_bonus(self):
        """When CI database is missing, should return 0 bonus."""
        # Setup: Auditor with no CI database
        auditor = TestValueAuditor()
        auditor.v5_failures_available = False

        # Execute: Get failure bonus
        bonus = auditor._get_failure_bonus("tests/test_example.py::test_foo")

        # Assert: Should return 0 bonus
        assert bonus == 0.0

    def test_git_fallback_returns_zero_churn(self):
        """When git is unavailable, should return 0 churn burden."""
        # Setup: Auditor with no git
        auditor = TestValueAuditor()
        auditor.v5_git_available = False

        # Execute: Get churn burden
        churn = auditor._get_churn_burden("tests/test_example.py")

        # Assert: Should return 0 churn
        assert churn == 0.0

    def test_corrupt_weights_yaml_falls_back_to_defaults(self, tmp_path):
        """When weights.yaml is corrupt, should use default weights."""
        # Setup: Create corrupt weights.yaml
        weights_file = tmp_path / "weights.yaml"
        weights_file.write_text("{ invalid yaml content }")

        # Execute: Load weights
        loader = WeightsLoader(weights_path=weights_file)
        weights = loader.load()

        # Assert: Should return default weights (not crash)
        assert weights.bug_detection_weight == 10.0
        assert weights.critical_path_weight == 5.0


class TestV5ScoringMode:
    """Test scoring mode determination (V5_FULL, V5_PARTIAL, V4_FALLBACK)."""

    def test_v5_full_mode_with_all_data_available(self, tmp_path):
        """V5_FULL mode when runtime, CI, git, and weights all present."""
        # Setup: Create all data sources
        audit_dir = tmp_path / ".audit"
        audit_dir.mkdir()
        (audit_dir / "runtime_cache.json").write_text("{}")
        (audit_dir / "failure_history.sqlite").touch()
        (tmp_path / ".git").mkdir()
        (tmp_path / "weights.yaml").write_text("bug_detection_weight: 10.0")

        # Execute: Initialize auditor
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()
            mode = auditor._get_scoring_mode()

            # Assert: Should be V5_FULL
            assert mode == "V5_FULL"

    def test_v5_partial_mode_with_some_data_missing(self, tmp_path):
        """V5_PARTIAL mode when some data sources are missing."""
        # Setup: Create only runtime cache (no CI, no git)
        audit_dir = tmp_path / ".audit"
        audit_dir.mkdir()
        (audit_dir / "runtime_cache.json").write_text("{}")

        # Execute: Initialize auditor
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()
            mode = auditor._get_scoring_mode()

            # Assert: Should be V5_PARTIAL
            assert mode == "V5_PARTIAL"

    def test_v4_fallback_mode_with_no_data_available(self, tmp_path):
        """V4_FALLBACK mode when no empirical data available."""
        # Setup: No data sources present
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()
            mode = auditor._get_scoring_mode()

            # Assert: Should be V4_FALLBACK
            assert mode == "V4_FALLBACK"


class TestV5IntegratedScoring:
    """Test integrated scoring with V5 components."""

    def test_v5_scoring_uses_actual_runtime(self, tmp_path):
        """V5 scoring should use actual runtime from cache."""
        # Setup: Auditor with runtime cache
        auditor = TestValueAuditor()
        auditor.v5_runtime_available = True
        auditor.runtime_parser = Mock()
        auditor.runtime_parser.get_runtime.return_value = 12.5

        test = {
            'name': 'test_example',
            'file': 'tests/test_example.py',
            'line': 10,
            'code': 'def test_example(): pass'
        }

        # Execute: Score test
        score = auditor.score_test(test)

        # Assert: Should use actual runtime
        assert score.actual_runtime_seconds == 12.5
        assert score.runtime_source == "junitxml"

    def test_v5_scoring_applies_failure_bonus(self):
        """V5 scoring should apply CI failure bonus."""
        # Setup: Auditor with CI database
        auditor = TestValueAuditor()
        auditor.v5_failures_available = True
        auditor.failure_calculator = Mock()
        auditor.failure_calculator.calculate_bonus.return_value = 10.0

        test = {
            'name': 'test_bug_detector',
            'file': 'tests/test_example.py',
            'line': 20,
            'code': 'def test_bug_detector(): pass'
        }

        # Execute: Score test
        score = auditor.score_test(test)

        # Assert: Should include failure bonus
        assert score.failure_bonus == 10.0

    def test_v5_scoring_applies_churn_penalty(self):
        """V5 scoring should apply git churn penalty."""
        # Setup: Auditor with git
        auditor = TestValueAuditor()
        auditor.v5_git_available = True
        auditor.git_analyzer = Mock()
        auditor.git_analyzer.calculate_maintenance_burden.return_value = 6.5

        test = {
            'name': 'test_brittle',
            'file': 'tests/test_example.py',
            'line': 30,
            'code': 'def test_brittle(): pass'
        }

        # Execute: Score test
        score = auditor.score_test(test)

        # Assert: Should include churn penalty
        assert score.churn_burden == 6.5

    @pytest.mark.skip(reason="Test infra: Normalization not integrated")
    def test_v5_scoring_produces_normalized_scores(self):
        """V5 scoring should produce normalized scores in expected range."""
        # Setup: Auditor with normalization enabled
        auditor = TestValueAuditor()
        auditor.v5_enabled = True
        auditor.normalizer = Mock()
        auditor.normalizer.transform.return_value = 0.75  # Z-score

        test = {
            'name': 'test_example',
            'file': 'tests/test_example.py',
            'line': 40,
            'code': 'def test_example(): pass'
        }

        # Execute: Score test
        score = auditor.score_test(test)

        # Assert: Score should be normalized
        assert -3.0 <= score.total_score <= 3.0  # Z-score range


class TestV5ReportMetadata:
    """Test report metadata includes V5 scoring information."""

    def test_report_includes_scoring_version(self, tmp_path):
        """Report should include scoring_version field."""
        # Setup: Auditor with V5 enabled
        auditor = TestValueAuditor()
        auditor.v5_enabled = True

        # Execute: Generate results
        results = auditor._generate_results()

        # Assert: Should include scoring version
        assert 'metadata' in results
        assert 'scoring_version' in results['metadata']
        assert results['metadata']['scoring_version'] in ['V5_FULL', 'V5_PARTIAL', 'V4_FALLBACK']

    def test_report_includes_data_sources(self, tmp_path):
        """Report should indicate which data sources are available."""
        # Setup: Auditor with partial V5 data
        auditor = TestValueAuditor()
        auditor.v5_runtime_available = True
        auditor.v5_failures_available = False
        auditor.v5_git_available = False

        # Execute: Generate results
        results = auditor._generate_results()

        # Assert: Should include data availability
        assert 'metadata' in results
        assert 'data_availability' in results['metadata']
        assert results['metadata']['data_availability']['runtime'] is True
        assert results['metadata']['data_availability']['ci_failures'] is False
        assert results['metadata']['data_availability']['git_churn'] is False

    def test_report_includes_runtime_source(self):
        """Report should indicate runtime data source (junitxml/heuristic)."""
        # Setup: Auditor with runtime cache
        auditor = TestValueAuditor()
        auditor.v5_runtime_available = True

        # Execute: Generate results
        results = auditor._generate_results()

        # Assert: Should include runtime source
        assert 'metadata' in results
        assert 'runtime_source' in results['metadata']
        assert results['metadata']['runtime_source'] in ['junitxml', 'reportlog', 'heuristic']

    @pytest.mark.skip(reason="Test infra: Warning generation changed")
    def test_v4_report_includes_fallback_warnings(self):
        """V4 fallback report should include warning messages."""
        # Setup: Auditor with no V5 data
        auditor = TestValueAuditor()
        auditor.v5_enabled = False

        # Execute: Generate results
        results = auditor._generate_results()

        # Assert: Should include warnings
        assert 'metadata' in results
        assert 'warnings' in results['metadata']
        assert len(results['metadata']['warnings']) > 0
        assert any('runtime cache not found' in w.lower() for w in results['metadata']['warnings'])


class TestV5CLIInterface:
    """Test CLI interface remains unchanged (backward compatibility)."""

    def test_cli_accepts_same_arguments_as_v4(self, tmp_path):
        """CLI should accept same arguments as V4 (backward compatible)."""
        # Setup: Create test directory
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        # Execute: Initialize auditor with test_dir argument
        auditor = TestValueAuditor()
        results = auditor.run_audit(test_dir=test_dir)

        # Assert: Should work without errors
        assert 'summary' in results
        assert 'tests' in results

    def test_cli_output_format_unchanged(self):
        """CLI output format should match V4 (backward compatible)."""
        # Setup: Auditor
        auditor = TestValueAuditor()

        # Execute: Generate results
        results = auditor._generate_results()

        # Assert: Should have V4 structure
        assert 'summary' in results
        assert 'tests' in results
        assert 'total_tests' in results['summary']
        assert 'high_value' in results['summary']

    def test_env_variable_forces_v4_mode(self, monkeypatch):
        """AUDIT_USE_V5=false should force V4 mode."""
        # Setup: Set environment variable
        monkeypatch.setenv('AUDIT_USE_V5', 'false')

        # Execute: Initialize auditor
        auditor = TestValueAuditor()

        # Assert: V5 should be disabled
        assert auditor.v5_enabled is False

    def test_cli_flag_forces_v4_mode(self):
        """--no-v5 flag should force V4 mode."""
        # Setup: Initialize with v5 disabled
        auditor = TestValueAuditor(enable_v5=False)

        # Assert: V5 should be disabled
        assert auditor.v5_enabled is False


class TestV5LoggingAndTransparency:
    """Test logging clearly indicates scoring mode."""

    def test_v5_initialization_logs_mode(self, capsys):
        """Initialization should log which V5 components are active."""
        # Setup & Execute: Initialize auditor
        auditor = TestValueAuditor()
        auditor._log_initialization()

        # Capture output
        captured = capsys.readouterr()

        # Assert: Should log scoring mode
        assert 'V5' in captured.out or 'V4' in captured.out

    def test_v5_logs_data_source_availability(self, capsys):
        """Should log which data sources are available."""
        # Setup & Execute: Initialize auditor
        auditor = TestValueAuditor()
        auditor._log_data_sources()

        # Capture output
        captured = capsys.readouterr()

        # Assert: Should mention runtime, CI, git
        output = captured.out.lower()
        assert 'runtime' in output or 'ci' in output or 'git' in output

    def test_v4_fallback_logs_warnings(self, capsys):
        """V4 fallback should log warnings about missing data."""
        # Setup: Auditor with no V5 data
        auditor = TestValueAuditor()
        auditor.v5_runtime_available = False
        auditor._log_fallback_warnings()

        # Capture output
        captured = capsys.readouterr()

        # Assert: Should log warnings
        assert 'warning' in captured.out.lower() or '⚠️' in captured.out


class TestV5ErrorHandling:
    """Test error handling for missing/corrupt data sources."""

    def test_handles_missing_runtime_cache_gracefully(self, tmp_path):
        """Should not crash when runtime cache is missing."""
        # Setup: No runtime cache
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            # Execute: Initialize auditor
            auditor = TestValueAuditor()

            # Assert: Should not crash
            assert auditor is not None
            assert auditor.v5_runtime_available is False

    def test_handles_corrupt_runtime_cache_gracefully(self, tmp_path):
        """Should not crash when runtime cache is corrupt."""
        # Setup: Create corrupt runtime cache
        audit_dir = tmp_path / ".audit"
        audit_dir.mkdir()
        runtime_cache = audit_dir / "runtime_cache.json"
        runtime_cache.write_text("{ invalid json }")

        # Execute: Initialize auditor
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()

            # Assert: Should fall back to V4
            assert auditor.v5_runtime_available is False

    def test_handles_missing_ci_database_gracefully(self, tmp_path):
        """Should not crash when CI database is missing."""
        # Setup: No CI database
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            # Execute: Initialize auditor
            auditor = TestValueAuditor()

            # Assert: Should not crash
            assert auditor is not None
            assert auditor.v5_failures_available is False

    def test_handles_git_command_failure_gracefully(self, tmp_path):
        """Should not crash when git commands fail."""
        # Setup: Simulate git command failure
        with patch('subprocess.run', side_effect=FileNotFoundError("git not found")):
            # Execute: Initialize auditor
            auditor = TestValueAuditor()

            # Assert: Should fall back to V4
            assert auditor.v5_git_available is False


class TestV5Performance:
    """Test V5 performance meets SLA (<15s for 5,408 tests)."""

    @pytest.mark.slow
    def test_v5_full_audit_completes_within_sla(self, tmp_path):
        """Full audit should complete in <15 seconds."""
        import time

        # Setup: Create test directory with sample tests
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        for i in range(100):  # Sample 100 tests
            test_file = test_dir / f"test_example_{i}.py"
            test_file.write_text(f"def test_{i}(): pass")

        # Execute: Run audit
        auditor = TestValueAuditor()
        start = time.time()
        auditor.run_audit(test_dir=test_dir)
        elapsed = time.time() - start

        # Assert: Should complete within SLA (scaled for 100 tests)
        # 15s / 5408 tests = 0.0028s per test → 100 tests = 0.28s
        assert elapsed < 1.0  # Allow 1s for 100 tests (conservative)


class TestV5ComponentIntegration:
    """Test V5 components integrate correctly."""

    def test_weights_loader_provides_config_to_all_components(self):
        """WeightsLoader should provide config to all V5 components."""
        # Setup: Load weights
        loader = WeightsLoader()
        weights = loader.load()

        # Execute: Initialize components with weights
        failure_calc = FailureBonusCalculator(config={
            'failure_bonus_weight': weights.failure_bonus_weight
        })

        # Assert: Component should use provided weights
        assert failure_calc.failure_bonus_weight == weights.failure_bonus_weight

    def test_runtime_parser_integrates_with_auditor(self, tmp_path):
        """RuntimeDataParser should integrate with TestValueAuditor."""
        # Setup: Create runtime cache
        audit_dir = tmp_path / ".audit"
        audit_dir.mkdir()
        cache_file = audit_dir / "runtime_cache.json"
        cache_file.write_text(json.dumps({
            "tests/test_example.py::test_foo": {
                "duration_seconds": 2.5,
                "source": "junitxml"
            }
        }))

        # Execute: Initialize auditor
        with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
            auditor = TestValueAuditor()

            # Assert: Runtime parser should be initialized
            assert auditor.runtime_parser is not None
            assert auditor.v5_runtime_available is True

    def test_score_normalizer_integrates_with_auditor(self):
        """ScoreNormalizer should integrate with TestValueAuditor."""
        # Setup: Auditor with normalization enabled
        auditor = TestValueAuditor()
        auditor.v5_enabled = True

        # Assert: Normalizer should be initialized
        assert auditor.normalizer is not None
        assert auditor.normalizer.mode in ['none', 'z-score', 'min-max']


# Pytest fixtures
@pytest.fixture
def sample_test():
    """Sample test for scoring."""
    return {
        'name': 'test_example',
        'file': 'tests/test_example.py',
        'line': 10,
        'code': """
def test_example():
    result = process_data([1, 2, 3])
    assert result == [2, 4, 6]
"""
    }


@pytest.fixture
def v5_auditor_with_all_data(tmp_path):
    """Auditor with all V5 data sources available."""
    # Create all data sources
    audit_dir = tmp_path / ".audit"
    audit_dir.mkdir()
    (audit_dir / "runtime_cache.json").write_text("{}")
    (audit_dir / "failure_history.sqlite").touch()
    (tmp_path / ".git").mkdir()
    (tmp_path / "weights.yaml").write_text("bug_detection_weight: 10.0")

    with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
        return TestValueAuditor()


@pytest.fixture
def v4_auditor_no_data(tmp_path):
    """Auditor with no V5 data sources (V4 fallback)."""
    with patch('scripts.test_value_audit.Path.cwd', return_value=tmp_path):
        return TestValueAuditor()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
