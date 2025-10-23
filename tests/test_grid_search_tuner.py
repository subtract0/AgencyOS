#!/usr/bin/env python3
"""
Tests for Grid Search Tuner

Constitutional Article II: Tests written to verify 100% correct behavior.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from grid_search_tuner import (
    GridSearchTuner,
    WeightCandidate,
    SearchResult
)


@pytest.fixture
def temp_labeled_tests(tmp_path: Path) -> Path:
    """Create temporary labeled_tests.json for testing."""
    labeled_tests = {
        "labels": [
            {
                "test_id": "tests/test_example.py::test_high_value",
                "file_path": "tests/test_example.py",
                "test_name": "test_high_value",
                "line": 10,
                "score": 25.0,
                "bug_detection_score": 2.5,
                "critical_path_score": 2.0,
                "integration_score": 1.5,
                "runtime_penalty": 0.5,
                "maintenance_burden": 1.0,
                "manual_label": "KEEP",
                "reason": "Critical integration test",
                "timestamp": "2025-10-23T10:00:00",
                "category": "HIGH",
                "action": "KEEP",
                "lines_of_code": 50,
                "mock_count": 2,
                "assertion_count": 5
            },
            {
                "test_id": "tests/test_example.py::test_medium_value",
                "file_path": "tests/test_example.py",
                "test_name": "test_medium_value",
                "line": 30,
                "score": 15.0,
                "bug_detection_score": 1.5,
                "critical_path_score": 1.0,
                "integration_score": 0.5,
                "runtime_penalty": 1.0,
                "maintenance_burden": 2.0,
                "manual_label": "REVIEW",
                "reason": "Moderate value, review needed",
                "timestamp": "2025-10-23T10:05:00",
                "category": "MEDIUM",
                "action": "REVIEW",
                "lines_of_code": 30,
                "mock_count": 4,
                "assertion_count": 3
            },
            {
                "test_id": "tests/test_example.py::test_low_value",
                "file_path": "tests/test_example.py",
                "test_name": "test_low_value",
                "line": 50,
                "score": 5.0,
                "bug_detection_score": 0.3,
                "critical_path_score": 0.2,
                "integration_score": 0.1,
                "runtime_penalty": 2.0,
                "maintenance_burden": 5.0,
                "manual_label": "DELETE",
                "reason": "Mocking hell, tests implementation",
                "timestamp": "2025-10-23T10:10:00",
                "category": "LOW",
                "action": "DELETE",
                "lines_of_code": 80,
                "mock_count": 10,
                "assertion_count": 1
            },
            # Add more samples for diversity
            {
                "test_id": "tests/test_example.py::test_keep_2",
                "file_path": "tests/test_example.py",
                "test_name": "test_keep_2",
                "line": 70,
                "score": 22.0,
                "bug_detection_score": 2.2,
                "critical_path_score": 1.8,
                "integration_score": 1.2,
                "runtime_penalty": 0.8,
                "maintenance_burden": 1.5,
                "manual_label": "KEEP",
                "reason": "Security critical",
                "timestamp": "2025-10-23T10:15:00",
                "category": "HIGH",
                "action": "KEEP",
                "lines_of_code": 45,
                "mock_count": 3,
                "assertion_count": 4
            },
            {
                "test_id": "tests/test_example.py::test_review_2",
                "file_path": "tests/test_example.py",
                "test_name": "test_review_2",
                "line": 90,
                "score": 12.0,
                "bug_detection_score": 1.2,
                "critical_path_score": 0.8,
                "integration_score": 0.6,
                "runtime_penalty": 1.5,
                "maintenance_burden": 2.5,
                "manual_label": "REVIEW",
                "reason": "Edge case coverage",
                "timestamp": "2025-10-23T10:20:00",
                "category": "MEDIUM",
                "action": "REVIEW",
                "lines_of_code": 35,
                "mock_count": 5,
                "assertion_count": 2
            },
            {
                "test_id": "tests/test_example.py::test_delete_2",
                "file_path": "tests/test_example.py",
                "test_name": "test_delete_2",
                "line": 110,
                "score": 3.0,
                "bug_detection_score": 0.2,
                "critical_path_score": 0.1,
                "integration_score": 0.05,
                "runtime_penalty": 3.0,
                "maintenance_burden": 6.0,
                "manual_label": "DELETE",
                "reason": "Tests private method",
                "timestamp": "2025-10-23T10:25:00",
                "category": "LOW",
                "action": "DELETE",
                "lines_of_code": 100,
                "mock_count": 12,
                "assertion_count": 1
            },
            # Add more KEEP examples
            {
                "test_id": "tests/test_example.py::test_keep_3",
                "file_path": "tests/test_example.py",
                "test_name": "test_keep_3",
                "line": 130,
                "score": 28.0,
                "bug_detection_score": 2.8,
                "critical_path_score": 2.2,
                "integration_score": 1.8,
                "runtime_penalty": 0.3,
                "maintenance_burden": 0.8,
                "manual_label": "KEEP",
                "reason": "Catches regression bugs",
                "timestamp": "2025-10-23T10:30:00",
                "category": "HIGH",
                "action": "KEEP",
                "lines_of_code": 40,
                "mock_count": 1,
                "assertion_count": 6
            },
            {
                "test_id": "tests/test_example.py::test_keep_4",
                "file_path": "tests/test_example.py",
                "test_name": "test_keep_4",
                "line": 150,
                "score": 24.0,
                "bug_detection_score": 2.4,
                "critical_path_score": 1.9,
                "integration_score": 1.4,
                "runtime_penalty": 0.6,
                "maintenance_burden": 1.2,
                "manual_label": "KEEP",
                "reason": "E2E test",
                "timestamp": "2025-10-23T10:35:00",
                "category": "HIGH",
                "action": "KEEP",
                "lines_of_code": 55,
                "mock_count": 2,
                "assertion_count": 5
            },
            {
                "test_id": "tests/test_example.py::test_review_3",
                "file_path": "tests/test_example.py",
                "test_name": "test_review_3",
                "line": 170,
                "score": 14.0,
                "bug_detection_score": 1.4,
                "critical_path_score": 0.9,
                "integration_score": 0.7,
                "runtime_penalty": 1.2,
                "maintenance_burden": 2.2,
                "manual_label": "REVIEW",
                "reason": "Boundary conditions",
                "timestamp": "2025-10-23T10:40:00",
                "category": "MEDIUM",
                "action": "REVIEW",
                "lines_of_code": 38,
                "mock_count": 4,
                "assertion_count": 3
            },
            {
                "test_id": "tests/test_example.py::test_delete_3",
                "file_path": "tests/test_example.py",
                "test_name": "test_delete_3",
                "line": 190,
                "score": 4.0,
                "bug_detection_score": 0.25,
                "critical_path_score": 0.15,
                "integration_score": 0.08,
                "runtime_penalty": 2.5,
                "maintenance_burden": 5.5,
                "manual_label": "DELETE",
                "reason": "Redundant coverage",
                "timestamp": "2025-10-23T10:45:00",
                "category": "LOW",
                "action": "DELETE",
                "lines_of_code": 75,
                "mock_count": 11,
                "assertion_count": 1
            }
        ]
    }

    labeled_path = tmp_path / "labeled_tests.json"
    with open(labeled_path, 'w') as f:
        json.dump(labeled_tests, f, indent=2)

    return labeled_path


@pytest.fixture
def temp_weights_template(tmp_path: Path) -> Path:
    """Create temporary weights.yaml template."""
    weights = {
        'bug_detection_weight': 10.0,
        'critical_path_weight': 5.0,
        'integration_bonus_weight': 3.0,
        'penalties': {
            'runtime_penalty_threshold': 30,
            'runtime_penalty_multiplier': 0.1
        },
        'bonuses': {
            'failure_bonus_weight': 5.0
        },
        'maintenance': {
            'age_penalty_weight': 0.5,
            'churn_penalty_weight': 1.5,
            'external_mock_penalty': 0.3,
            'internal_mock_penalty': 0.8
        },
        'normalization': {
            'mode': 'z-score',
            'clip_outliers': 3.0
        },
        'thresholds': {
            'high_value': 20,
            'medium_value': 10
        }
    }

    weights_path = tmp_path / "weights.yaml"
    import yaml
    with open(weights_path, 'w') as f:
        yaml.dump(weights, f)

    return weights_path


class TestGridSearchTuner:
    """Test suite for GridSearchTuner."""

    def test_initialization_with_valid_data(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path,
        tmp_path: Path
    ):
        """Test tuner initializes correctly with valid data."""
        output_path = tmp_path / "weights_optimized.yaml"

        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template,
            output_path=output_path
        )

        assert len(tuner.labeled_tests) == 10
        assert tuner.output_path == output_path
        assert tuner.iterations_evaluated == 0

    def test_initialization_missing_labeled_tests(self, tmp_path: Path):
        """Test tuner raises error when labeled_tests.json is missing."""
        missing_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError) as exc_info:
            GridSearchTuner(labeled_tests_path=missing_path)

        assert "Labeled tests file not found" in str(exc_info.value)

    def test_initialization_insufficient_labels(self, tmp_path: Path):
        """Test tuner raises error when too few labels (<10)."""
        # Create file with only 5 labels
        insufficient_labels = {
            "labels": [
                {
                    "test_id": f"test_{i}",
                    "manual_label": "KEEP",
                    "score": 20.0,
                    "bug_detection_score": 2.0,
                    "critical_path_score": 1.5,
                    "integration_score": 1.0
                }
                for i in range(5)
            ]
        }

        insufficient_path = tmp_path / "insufficient.json"
        with open(insufficient_path, 'w') as f:
            json.dump(insufficient_labels, f)

        with pytest.raises(ValueError) as exc_info:
            GridSearchTuner(labeled_tests_path=insufficient_path)

        assert "Insufficient labeled tests" in str(exc_info.value)
        assert "need at least 10" in str(exc_info.value)

    def test_define_search_space_full(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path
    ):
        """Test full search space has expected dimensions."""
        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template
        )

        space = tuner.define_search_space(quick_search=False)

        assert len(space) == 6  # 6 weight dimensions
        assert 'bug_detection_weight' in space
        assert 'critical_path_weight' in space
        assert 'runtime_penalty_multiplier' in space
        assert 'failure_bonus_weight' in space
        assert 'churn_penalty_weight' in space
        assert 'age_penalty_weight' in space

        # Check each dimension has multiple values
        assert len(space['bug_detection_weight']) >= 3
        assert len(space['critical_path_weight']) >= 3

    def test_define_search_space_quick(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path
    ):
        """Test quick search space is smaller."""
        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template
        )

        space = tuner.define_search_space(quick_search=True)

        assert len(space) == 6
        # Quick search has only 2 values per dimension
        for values in space.values():
            assert len(values) == 2

    def test_calculate_score_with_weights(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path
    ):
        """Test score recalculation with candidate weights."""
        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template
        )

        # Test with first labeled test
        test = tuner.labeled_tests[0]

        # Create candidate weights
        weights = WeightCandidate(
            bug_detection_weight=10.0,
            critical_path_weight=5.0,
            runtime_penalty_multiplier=0.1,
            failure_bonus_weight=5.0,
            churn_penalty_weight=1.5,
            age_penalty_weight=0.5
        )

        score = tuner.calculate_score_with_weights(test, weights)

        # Score should be positive for high-value test
        assert score > 0
        # Should be roughly: 2.5*10 + 2.0*5 + 1.5*3 - penalties
        assert 20 < score < 40

    def test_classify_action(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path
    ):
        """Test action classification based on score."""
        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template
        )

        # High score -> KEEP
        assert tuner.classify_action(25.0) == "KEEP"

        # Medium score -> REVIEW
        assert tuner.classify_action(15.0) == "REVIEW"

        # Low score -> DELETE
        assert tuner.classify_action(5.0) == "DELETE"

    def test_evaluate_weights(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path
    ):
        """Test accuracy evaluation against manual labels."""
        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template
        )

        # Use default weights (should have decent accuracy)
        weights = WeightCandidate(
            bug_detection_weight=10.0,
            critical_path_weight=5.0,
            runtime_penalty_multiplier=0.1,
            failure_bonus_weight=5.0,
            churn_penalty_weight=1.5,
            age_penalty_weight=0.5
        )

        accuracy = tuner.evaluate_weights(weights)

        # Accuracy should be between 0 and 1
        assert 0.0 <= accuracy <= 1.0

        # With reasonable weights, accuracy should be >50%
        assert accuracy > 0.5

    def test_grid_search_quick(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path,
        tmp_path: Path
    ):
        """Test quick grid search completes successfully."""
        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template,
            output_path=tmp_path / "weights_opt.yaml"
        )

        # Run quick search (64 combinations)
        result = tuner.grid_search(quick_search=True)

        # Verify result structure
        assert isinstance(result, SearchResult)
        assert result.best_weights is not None
        assert 0.0 <= result.best_accuracy <= 1.0
        assert result.total_iterations > 0
        assert result.elapsed_seconds > 0
        assert result.samples_evaluated == 10

        # Confusion matrix should be populated
        assert 'KEEP' in result.confusion_matrix
        assert 'REVIEW' in result.confusion_matrix
        assert 'DELETE' in result.confusion_matrix

    def test_grid_search_max_iterations(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path,
        tmp_path: Path
    ):
        """Test grid search respects max_iterations limit."""
        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template,
            output_path=tmp_path / "weights_opt.yaml"
        )

        # Run with max 20 iterations
        result = tuner.grid_search(max_iterations=20)

        # Should evaluate at most 20 combinations
        assert result.total_iterations <= 20

    def test_save_optimized_weights(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path,
        tmp_path: Path
    ):
        """Test saving optimized weights to YAML."""
        output_path = tmp_path / "weights_optimized.yaml"

        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template,
            output_path=output_path
        )

        # Run quick search
        result = tuner.grid_search(quick_search=True)

        # Save optimized weights
        tuner.save_optimized_weights(result)

        # Verify file was created
        assert output_path.exists()

        # Load and verify structure
        import yaml
        with open(output_path, 'r') as f:
            optimized = yaml.safe_load(f)

        # Check optimized values are present
        assert 'bug_detection_weight' in optimized
        assert 'critical_path_weight' in optimized
        assert 'penalties' in optimized
        assert 'runtime_penalty_multiplier' in optimized['penalties']

        # Check metadata
        assert '_metadata' in optimized
        assert 'optimized_at' in optimized['_metadata']
        assert 'grid_search_accuracy' in optimized['_metadata']

    def test_edge_case_all_same_label(self, tmp_path: Path):
        """Test handling of edge case where all labels are the same."""
        # Create labeled tests where all are KEEP
        same_labels = {
            "labels": [
                {
                    "test_id": f"test_{i}",
                    "file_path": "tests/test.py",
                    "test_name": f"test_{i}",
                    "line": i * 10,
                    "manual_label": "KEEP",
                    "score": 25.0,
                    "bug_detection_score": 2.5,
                    "critical_path_score": 2.0,
                    "integration_score": 1.5,
                    "runtime_penalty": 0.5,
                    "maintenance_burden": 1.0,
                    "reason": "High value",
                    "timestamp": "2025-10-23T10:00:00",
                    "category": "HIGH",
                    "action": "KEEP",
                    "lines_of_code": 50,
                    "mock_count": 2,
                    "assertion_count": 5
                }
                for i in range(10)
            ]
        }

        same_path = tmp_path / "same_labels.json"
        with open(same_path, 'w') as f:
            json.dump(same_labels, f)

        # Should initialize with warning but not error
        tuner = GridSearchTuner(
            labeled_tests_path=same_path,
            output_path=tmp_path / "weights_opt.yaml"
        )

        # Grid search should still work (100% accuracy for all weights)
        result = tuner.grid_search(quick_search=True)

        # Accuracy should be 1.0 (all predictions match)
        assert result.best_accuracy == 1.0

    def test_normalize_consolidate_label(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path,
        tmp_path: Path
    ):
        """Test that CONSOLIDATE label is normalized to DELETE."""
        # Add a test with CONSOLIDATE label
        with open(temp_labeled_tests, 'r') as f:
            data = json.load(f)

        data['labels'].append({
            "test_id": "tests/test_example.py::test_consolidate",
            "file_path": "tests/test_example.py",
            "test_name": "test_consolidate",
            "line": 210,
            "score": 6.0,
            "bug_detection_score": 0.4,
            "critical_path_score": 0.3,
            "integration_score": 0.2,
            "runtime_penalty": 2.0,
            "maintenance_burden": 4.0,
            "manual_label": "CONSOLIDATE",
            "reason": "Duplicate test",
            "timestamp": "2025-10-23T10:50:00",
            "category": "LOW",
            "action": "DELETE",
            "lines_of_code": 60,
            "mock_count": 8,
            "assertion_count": 1
        })

        with open(temp_labeled_tests, 'w') as f:
            json.dump(data, f)

        # Initialize tuner
        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template,
            output_path=tmp_path / "weights_opt.yaml"
        )

        # Run search
        result = tuner.grid_search(quick_search=True)

        # CONSOLIDATE should be treated as DELETE
        assert 'DELETE' in result.label_distribution
        assert 'CONSOLIDATE' not in result.label_distribution

    def test_performance_quick_search(
        self,
        temp_labeled_tests: Path,
        temp_weights_template: Path,
        tmp_path: Path
    ):
        """Test that quick search completes in reasonable time (<10 seconds)."""
        import time

        tuner = GridSearchTuner(
            labeled_tests_path=temp_labeled_tests,
            weights_template_path=temp_weights_template,
            output_path=tmp_path / "weights_opt.yaml"
        )

        start = time.time()
        result = tuner.grid_search(quick_search=True)
        elapsed = time.time() - start

        # Quick search (64 combinations, 10 samples) should be fast
        assert elapsed < 10.0, f"Quick search took {elapsed:.1f}s (expected <10s)"

        # Should have evaluated 64 combinations
        assert result.total_iterations == 64


class TestWeightCandidate:
    """Test suite for WeightCandidate dataclass."""

    def test_weight_candidate_creation(self):
        """Test WeightCandidate can be created with valid values."""
        weights = WeightCandidate(
            bug_detection_weight=10.0,
            critical_path_weight=5.0,
            runtime_penalty_multiplier=0.1,
            failure_bonus_weight=5.0,
            churn_penalty_weight=1.5,
            age_penalty_weight=0.5
        )

        assert weights.bug_detection_weight == 10.0
        assert weights.critical_path_weight == 5.0

    def test_weight_candidate_to_dict(self):
        """Test WeightCandidate can be converted to dict."""
        weights = WeightCandidate(
            bug_detection_weight=10.0,
            critical_path_weight=5.0,
            runtime_penalty_multiplier=0.1,
            failure_bonus_weight=5.0,
            churn_penalty_weight=1.5,
            age_penalty_weight=0.5
        )

        weights_dict = weights.to_dict()

        assert isinstance(weights_dict, dict)
        assert 'bug_detection_weight' in weights_dict
        assert weights_dict['bug_detection_weight'] == 10.0


class TestSearchResult:
    """Test suite for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test SearchResult can be created with valid data."""
        weights = WeightCandidate(
            bug_detection_weight=10.0,
            critical_path_weight=5.0,
            runtime_penalty_multiplier=0.1,
            failure_bonus_weight=5.0,
            churn_penalty_weight=1.5,
            age_penalty_weight=0.5
        )

        result = SearchResult(
            best_weights=weights,
            best_accuracy=0.92,
            total_iterations=100,
            elapsed_seconds=45.5,
            samples_evaluated=50,
            confusion_matrix={
                'KEEP': {'KEEP': 10, 'REVIEW': 2, 'DELETE': 0},
                'REVIEW': {'KEEP': 1, 'REVIEW': 15, 'DELETE': 2},
                'DELETE': {'KEEP': 0, 'REVIEW': 1, 'DELETE': 19}
            },
            label_distribution={'KEEP': 12, 'REVIEW': 18, 'DELETE': 20}
        )

        assert result.best_accuracy == 0.92
        assert result.total_iterations == 100
        assert result.samples_evaluated == 50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
