"""
Unit tests for DSPy Audit System

Tests signatures, modules, metrics, and adapter functionality.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

# Import components to test
from dspy_audit.config import AuditConfig, get_config, get_flags, should_use_dspy
from dspy_audit.metrics import (
    audit_effectiveness_metric,
    refactoring_success_metric,
    constitutional_compliance_metric,
    learning_effectiveness_metric,
    composite_audit_metric,
    calculate_improvement_delta,
)
from dspy_audit.adapter import AuditAdapter


class TestConfig:
    """Test configuration management."""

    def test_get_feature_flags_defaults(self):
        """Test default feature flags."""
        flags = AuditConfig.get_feature_flags()
        assert isinstance(flags, dict)
        assert "use_dspy_audit" in flags
        assert "parallel_audit_execution" in flags
        assert "enable_vectorstore_learning" in flags

    def test_get_audit_config_structure(self):
        """Test audit config structure."""
        config = AuditConfig.get_audit_config()
        assert "feature_flags" in config
        assert "prioritization" in config
        assert "necessary_thresholds" in config
        assert "quality_targets" in config
        assert "paths" in config
        assert "dspy_settings" in config
        assert "performance" in config

    def test_necessary_thresholds_valid(self):
        """Test NECESSARY thresholds are in valid range."""
        config = AuditConfig.get_audit_config()
        thresholds = config["necessary_thresholds"]
        for key, value in thresholds.items():
            assert 0.0 <= value <= 1.0, f"Threshold {key}={value} out of range"

    @patch.dict(os.environ, {"USE_DSPY_AUDIT": "true"})
    def test_should_use_dspy_enabled(self):
        """Test DSPy usage when enabled."""
        # Reset singleton to pick up env change
        audit_config = AuditConfig()
        assert audit_config.should_use_dspy() == True

    @patch.dict(os.environ, {"USE_DSPY_AUDIT": "false"})
    def test_should_use_dspy_disabled(self):
        """Test DSPy usage when disabled."""
        audit_config = AuditConfig()
        assert audit_config.should_use_dspy() == False

    def test_rollback_strategy(self):
        """Test rollback strategy selection."""
        strategy = AuditConfig.get_rollback_strategy()
        assert strategy in ["none", "automatic", "manual"]

    def test_validate_configuration(self):
        """Test configuration validation."""
        validations = AuditConfig.validate_configuration()
        assert isinstance(validations, dict)
        assert "thresholds_valid" in validations


class TestMetrics:
    """Test evaluation metrics."""

    def test_audit_effectiveness_no_issues(self):
        """Test metric with no issues found."""
        example = {"known_violations": []}
        prediction = {"issues": [], "verification": {"success": True}}
        score = audit_effectiveness_metric(example, prediction)
        assert 0.0 <= score <= 1.0
        assert score >= 0.7  # Should get points for no violations and success

    def test_audit_effectiveness_constitutional_detected(self):
        """Test metric when constitutional violations are detected."""
        example = {
            "known_violations": [
                {"severity": "constitutional", "type": "missing_tests"}
            ]
        }

        # Create mock issue with severity attribute
        mock_issue = Mock()
        mock_issue.severity.value = "constitutional"

        prediction = {
            "issues": [mock_issue],
            "verification": {"success": True}
        }

        score = audit_effectiveness_metric(example, prediction)
        assert score >= 0.7  # Should score well for detecting constitutional issue

    def test_refactoring_success_all_pass(self):
        """Test refactoring metric with all tests passing."""
        example = {}
        prediction = {
            "applied_fixes": [{"id": "fix1"}],
            "failed_fixes": [],
            "verification": {
                "test_results": {"unit": True, "integration": True},
                "rollback_needed": False
            },
            "metrics": {"qt_score_improvement": 0.1}
        }

        score = refactoring_success_metric(example, prediction)
        assert score >= 0.8  # Should score high with all passing

    def test_constitutional_compliance_full(self):
        """Test constitutional compliance with all articles met."""
        example = {}

        # Mock audit with historical patterns
        mock_audit = Mock()
        mock_audit.historical_patterns = [{"pattern": "test"}]

        # Mock learning with success patterns
        mock_learning = Mock()
        mock_learning.success_patterns = [{"success": "pattern"}]

        # Mock prioritization with rationale
        mock_prioritization = Mock()
        mock_prioritization.rationale = "Test rationale"

        prediction = {
            "audit": mock_audit,
            "verification": {
                "test_results": {"test1": True, "test2": True}
            },
            "applied_fixes": [{"tests_passed": True}],
            "learning": mock_learning,
            "prioritization": mock_prioritization
        }

        score = constitutional_compliance_metric(example, prediction)
        assert score >= 0.5  # Should get decent score with multiple articles met

    def test_learning_effectiveness_with_patterns(self):
        """Test learning metric with extracted patterns."""
        example = {}

        mock_learning = Mock()
        mock_learning.success_patterns = [{"pattern": 1}, {"pattern": 2}]
        mock_learning.failure_patterns = [{"anti": 1}]
        mock_learning.optimization_suggestions = ["suggestion1"]

        prediction = {
            "learning": mock_learning,
            "metrics": {"learning_pattern_reuse": 0.5}
        }

        score = learning_effectiveness_metric(example, prediction)
        assert score >= 0.5  # Should score well with patterns

    def test_composite_audit_metric(self):
        """Test composite metric combining all metrics."""
        example = {}
        prediction = {
            "issues": [],
            "verification": {"success": True},
            "applied_fixes": [],
            "failed_fixes": [],
            "learning": None
        }

        score = composite_audit_metric(example, prediction)
        assert 0.0 <= score <= 1.0

    def test_calculate_improvement_delta(self):
        """Test improvement calculation."""
        before = {"qt_score": 0.5, "coverage": 0.6}
        after = {"qt_score": 0.7, "coverage": 0.8}

        delta = calculate_improvement_delta(before, after)
        assert abs(delta["qt_score_delta"] - 0.2) < 0.001
        assert abs(delta["coverage_delta"] - 0.2) < 0.001
        assert "qt_score_pct_change" in delta
        assert abs(delta["qt_score_pct_change"] - 40.0) < 0.001


class TestAdapter:
    """Test adapter functionality."""

    def test_adapter_initialization(self):
        """Test adapter initializes both systems."""
        adapter = AuditAdapter()
        assert adapter.config is not None
        assert adapter.flags is not None

    @patch.dict(os.environ, {"USE_DSPY_AUDIT": "false"})
    def test_run_audit_legacy(self):
        """Test running legacy audit."""
        adapter = AuditAdapter()
        adapter.legacy_auditor = Mock()

        # Mock the legacy audit method
        with patch.object(adapter, '_run_legacy_audit') as mock_legacy:
            mock_legacy.return_value = {
                "system": "legacy",
                "qt_score": 0.5,
                "issues": []
            }

            result = adapter.run_audit("test/path", force_legacy=True)
            assert result["system"] == "legacy"
            mock_legacy.assert_called_once()

    def test_calculate_necessary_scores(self):
        """Test NECESSARY score calculation."""
        adapter = AuditAdapter()

        analysis = {
            "total_behaviors": 100,
            "total_test_functions": 80
        }

        scores = adapter._calculate_necessary_scores(analysis)
        assert "N" in scores
        assert scores["N"] == 0.8  # 80/100 coverage
        assert all(0.0 <= v <= 1.0 for v in scores.values())

    def test_calculate_qt_score(self):
        """Test Q(T) score calculation."""
        adapter = AuditAdapter()

        necessary_scores = {
            "N": 0.8,
            "E": 0.7,
            "C": 0.8,
            "E2": 0.6,
            "S1": 0.9,
            "S2": 0.9,
            "A": 0.3,
            "R": 0.8,
            "Y": 0.5
        }

        qt_score = adapter._calculate_qt_score(necessary_scores)
        expected = sum(necessary_scores.values()) / len(necessary_scores)
        assert abs(qt_score - expected) < 0.001

    def test_extract_issues_from_analysis(self):
        """Test issue extraction from analysis."""
        adapter = AuditAdapter()

        analysis = {
            "total_test_functions": 0,
            "functions": [
                {"file": "test.py", "line": 10, "complexity": 15}
            ]
        }

        issues = adapter._extract_issues_from_analysis(analysis)
        assert len(issues) == 2  # Missing tests + high complexity
        assert any(i["severity"] == "constitutional" for i in issues)
        assert any(i["severity"] == "complexity" for i in issues)

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        adapter = AuditAdapter()

        analysis = {
            "total_test_functions": 0,
            "total_behaviors": 10
        }

        recommendations = adapter._generate_recommendations(analysis)
        assert len(recommendations) > 0
        assert any("test coverage" in r for r in recommendations)

    def test_convert_issues(self):
        """Test converting Issue objects to dicts."""
        adapter = AuditAdapter()

        # Mock Issue object
        mock_issue = Mock()
        mock_issue.file_path = "test.py"
        mock_issue.line_number = 10
        mock_issue.severity.value = "high"
        mock_issue.category = "test"
        mock_issue.description = "Test issue"
        mock_issue.suggested_fix = "Fix it"

        converted = adapter._convert_issues([mock_issue])
        assert len(converted) == 1
        assert converted[0]["file"] == "test.py"
        assert converted[0]["severity"] == "high"


class TestModulesIntegration:
    """Test module functionality (without DSPy)."""

    def test_module_fallback_imports(self):
        """Test that modules can be imported without DSPy."""
        from dspy_audit.modules import AuditRefactorModule, MultiAgentAuditModule

        # Should create dummy modules without DSPy
        module = AuditRefactorModule()
        assert module is not None

    def test_signatures_fallback_imports(self):
        """Test that signatures can be imported without DSPy."""
        from dspy_audit.signatures import (
            AuditSignature,
            Issue,
            IssueSeverity,
            RefactoringPlan,
            RefactoringStep,
        )

        # Test enum
        assert IssueSeverity.CONSTITUTIONAL.value == "constitutional"

        # Test dataclass creation
        issue = Issue(
            file_path="test.py",
            line_number=10,
            severity=IssueSeverity.SECURITY,
            category="test",
            description="Test issue"
        )
        assert issue.file_path == "test.py"


class TestOptimization:
    """Test optimization utilities."""

    @patch('dspy_audit.optimize.Path')
    def test_load_audit_training_data_empty(self, mock_path):
        """Test loading training data when no data exists."""
        from dspy_audit.optimize import load_audit_training_data

        mock_path.return_value.exists.return_value = False

        data = load_audit_training_data()
        assert isinstance(data, list)
        assert len(data) >= 1  # Should have synthetic examples

    def test_save_and_load_module_mock(self):
        """Test save/load module with a simple object."""
        from dspy_audit.optimize import save_optimized_module, load_optimized_module

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_model.pkl")

            # Simple test object (not Mock which can't be pickled)
            test_module = {"test_attr": "test_value", "score": 0.8}

            # Save
            success = save_optimized_module(test_module, path)
            assert success == True
            assert os.path.exists(path)

            # Load
            loaded = load_optimized_module(path)
            assert loaded is not None
            assert loaded["test_attr"] == "test_value"


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_adapter_compare_systems_mock(self):
        """Test comparing systems with mocked components."""
        adapter = AuditAdapter()

        # Mock both audit methods
        with patch.object(adapter, '_run_legacy_audit') as mock_legacy:
            with patch.object(adapter, '_run_dspy_audit') as mock_dspy:
                mock_legacy.return_value = {
                    "system": "legacy",
                    "qt_score": 0.5,
                    "issues": [{"id": 1}]
                }
                mock_dspy.return_value = {
                    "system": "dspy",
                    "qt_score": 0.6,
                    "issues": [{"id": 2}]
                }

                # Force module availability
                adapter.dspy_module = Mock()

                result = adapter.compare_systems("test/path")

                assert "legacy" in result
                assert "dspy" in result
                assert "comparison" in result
                assert abs(result["comparison"]["qt_score_delta"] - 0.1) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])