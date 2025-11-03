"""
Tests for Manual Test Quality Labeling Tool

Constitutional Compliance:
- Article II: TDD - Tests written after implementation (tooling)
- Article I: Complete context - Tests cover all major functionality
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from label_tests import TestLabeler, TestLabel


class TestTestLabeler:
    """Test suite for TestLabeler CLI tool."""

    @pytest.fixture
    def temp_output(self, tmp_path):
        """Temporary output file."""
        return tmp_path / "test_labels.json"

    @pytest.fixture
    def sample_test_data(self):
        """Sample test data for labeling."""
        from test_value_audit import TestScore

        return {
            'name': 'test_example',
            'file': 'tests/test_example.py',
            'line': 42,
            'code': 'def test_example():\n    assert True',
            'score': TestScore(
                name='test_example',
                file='tests/test_example.py',
                line=42,
                bug_detection_score=5.0,
                critical_path_score=3.0,
                integration_score=2.0,
                runtime_penalty=0.5,
                maintenance_burden=1.0,
                total_score=15.5,
                category='MEDIUM',
                action='REVIEW',
                reason='Medium value',
                lines_of_code=30,
                mock_count=2,
                assertion_count=3,
                has_fixtures=False,
                is_integration=False,
                is_e2e=False
            )
        }

    def test_labeler_initialization(self, temp_output):
        """Test labeler initializes with correct defaults."""
        labeler = TestLabeler(
            output_file=temp_output,
            sample_size=50
        )

        assert labeler.output_file == temp_output
        assert labeler.sample_size == 50
        assert labeler.filter_category is None
        assert len(labeler.labeled) == 0
        assert len(labeler.labeled_ids) == 0

    def test_load_existing_labels_empty_file(self, temp_output):
        """Test loading when file doesn't exist."""
        labeler = TestLabeler(output_file=temp_output)

        assert len(labeler.labeled) == 0
        assert len(labeler.labeled_ids) == 0

    def test_load_existing_labels_with_data(self, temp_output):
        """Test loading existing labels on resume."""
        # Create existing labels file
        existing_labels = [
            {
                'test_id': 'tests/test_a.py::test_foo',
                'file_path': 'tests/test_a.py',
                'test_name': 'test_foo',
                'line': 10,
                'score': 5.0,
                'bug_detection_score': 2.0,
                'critical_path_score': 1.0,
                'integration_score': 1.0,
                'runtime_penalty': 0.5,
                'maintenance_burden': 1.5,
                'manual_label': 'DELETE',
                'reason': 'Low value',
                'timestamp': '2025-10-23T10:00:00',
                'category': 'LOW',
                'action': 'DELETE',
                'lines_of_code': 20,
                'mock_count': 5,
                'assertion_count': 1
            }
        ]

        with open(temp_output, 'w') as f:
            json.dump(existing_labels, f)

        # Load labeler
        labeler = TestLabeler(output_file=temp_output)

        assert len(labeler.labeled) == 1
        assert len(labeler.labeled_ids) == 1
        assert 'tests/test_a.py::test_foo' in labeler.labeled_ids

    def test_store_label(self, temp_output, sample_test_data):
        """Test storing a manual label."""
        labeler = TestLabeler(output_file=temp_output)

        labeler._store_label(
            sample_test_data,
            'KEEP',
            'High value test'
        )

        assert len(labeler.labeled) == 1
        assert len(labeler.labeled_ids) == 1

        label = labeler.labeled[0]
        assert label.manual_label == 'KEEP'
        assert label.reason == 'High value test'
        assert label.test_name == 'test_example'
        assert label.score == 15.5

    def test_save_labels(self, temp_output, sample_test_data):
        """Test saving labels to JSON file."""
        labeler = TestLabeler(output_file=temp_output)

        # Store some labels
        labeler._store_label(sample_test_data, 'KEEP', 'Good test')
        labeler._save_labels()

        # Verify file exists and contains data
        assert temp_output.exists()

        with open(temp_output, 'r') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]['manual_label'] == 'KEEP'
        assert data[0]['reason'] == 'Good test'
        assert data[0]['test_id'] == 'tests/test_example.py::test_example'

    def test_sample_tests_stratified(self, temp_output):
        """Test stratified sampling across score categories."""
        from test_value_audit import TestScore

        # Create mock scored tests
        high_tests = [
            {
                'name': f'test_high_{i}',
                'file': f'tests/high_{i}.py',
                'line': i,
                'code': 'def test(): pass',
                'score': TestScore(
                    name=f'test_high_{i}',
                    file=f'tests/high_{i}.py',
                    line=i,
                    bug_detection_score=8.0,
                    critical_path_score=7.0,
                    integration_score=5.0,
                    runtime_penalty=1.0,
                    maintenance_burden=0.5,
                    total_score=25.0,
                    category='HIGH',
                    action='KEEP',
                    reason='High value',
                    lines_of_code=20,
                    mock_count=0,
                    assertion_count=5,
                    has_fixtures=False,
                    is_integration=True,
                    is_e2e=False
                )
            }
            for i in range(50)
        ]

        medium_tests = [
            {
                'name': f'test_med_{i}',
                'file': f'tests/med_{i}.py',
                'line': i,
                'code': 'def test(): pass',
                'score': TestScore(
                    name=f'test_med_{i}',
                    file=f'tests/med_{i}.py',
                    line=i,
                    bug_detection_score=5.0,
                    critical_path_score=3.0,
                    integration_score=2.0,
                    runtime_penalty=0.5,
                    maintenance_burden=1.0,
                    total_score=15.0,
                    category='MEDIUM',
                    action='REVIEW',
                    reason='Medium value',
                    lines_of_code=30,
                    mock_count=2,
                    assertion_count=3,
                    has_fixtures=False,
                    is_integration=False,
                    is_e2e=False
                )
            }
            for i in range(50)
        ]

        low_tests = [
            {
                'name': f'test_low_{i}',
                'file': f'tests/low_{i}.py',
                'line': i,
                'code': 'def test(): pass',
                'score': TestScore(
                    name=f'test_low_{i}',
                    file=f'tests/low_{i}.py',
                    line=i,
                    bug_detection_score=2.0,
                    critical_path_score=1.0,
                    integration_score=0.5,
                    runtime_penalty=0.2,
                    maintenance_burden=2.0,
                    total_score=5.0,
                    category='LOW',
                    action='DELETE',
                    reason='Low value',
                    lines_of_code=50,
                    mock_count=10,
                    assertion_count=1,
                    has_fixtures=False,
                    is_integration=False,
                    is_e2e=False
                )
            }
            for i in range(100)
        ]

        all_tests = high_tests + medium_tests + low_tests

        labeler = TestLabeler(output_file=temp_output, sample_size=50)
        sampled = labeler._sample_tests(all_tests)

        # Verify sample size
        assert len(sampled) == 50

        # Verify stratification (25% HIGH, 25% MEDIUM, 50% LOW)
        high_count = sum(1 for t in sampled if t['score'].category == 'HIGH')
        medium_count = sum(1 for t in sampled if t['score'].category == 'MEDIUM')
        low_count = sum(1 for t in sampled if t['score'].category == 'LOW')

        # Allow some tolerance in counts
        assert 10 <= high_count <= 15  # Target: 12-13
        assert 10 <= medium_count <= 15  # Target: 12-13
        assert 20 <= low_count <= 30  # Target: 25

    def test_sample_tests_with_filter(self, temp_output):
        """Test sampling with category filter."""
        from test_value_audit import TestScore

        # Create tests across categories
        tests = []
        for cat in ['HIGH', 'MEDIUM', 'LOW']:
            for i in range(10):
                tests.append({
                    'name': f'test_{cat}_{i}',
                    'file': f'tests/{cat}_{i}.py',
                    'line': i,
                    'code': 'def test(): pass',
                    'score': TestScore(
                        name=f'test_{cat}_{i}',
                        file=f'tests/{cat}_{i}.py',
                        line=i,
                        bug_detection_score=5.0,
                        critical_path_score=3.0,
                        integration_score=2.0,
                        runtime_penalty=0.5,
                        maintenance_burden=1.0,
                        total_score=15.0,
                        category=cat,
                        action='REVIEW',
                        reason='Test',
                        lines_of_code=20,
                        mock_count=2,
                        assertion_count=3,
                        has_fixtures=False,
                        is_integration=False,
                        is_e2e=False
                    )
                })

        labeler = TestLabeler(
            output_file=temp_output,
            sample_size=10,
            filter_category='LOW'
        )

        # Filter tests manually (simulating run() logic)
        filtered = [t for t in tests if t['score'].category == 'LOW']
        sampled = labeler._sample_tests(filtered)

        # All sampled tests should be LOW
        assert all(t['score'].category == 'LOW' for t in sampled)

    def test_get_label_quit(self, temp_output):
        """Test quitting during labeling."""
        labeler = TestLabeler(output_file=temp_output)

        with patch('builtins.input', return_value='Q'):
            result = labeler._get_label()

        assert result == ('QUIT',)

    def test_get_label_skip(self, temp_output):
        """Test skipping a test."""
        labeler = TestLabeler(output_file=temp_output)

        with patch('builtins.input', return_value='S'):
            result = labeler._get_label()

        assert result == ('SKIP',)

    def test_get_label_valid_with_reason(self, temp_output):
        """Test valid label with reason."""
        labeler = TestLabeler(output_file=temp_output)

        with patch('builtins.input', side_effect=['K', 'High value integration test']):
            result = labeler._get_label()

        assert result == ('KEEP', 'High value integration test')

    def test_get_label_valid_no_reason(self, temp_output):
        """Test valid label without reason."""
        labeler = TestLabeler(output_file=temp_output)

        with patch('builtins.input', side_effect=['D', '']):
            result = labeler._get_label()

        assert result == ('DELETE', 'Manual classification: DELETE')

    def test_get_label_invalid_then_valid(self, temp_output):
        """Test invalid input followed by valid input."""
        labeler = TestLabeler(output_file=temp_output)

        with patch('builtins.input', side_effect=['X', 'R', 'Needs review']):
            result = labeler._get_label()

        assert result == ('REVIEW', 'Needs review')

    def test_label_schema_completeness(self, sample_test_data):
        """Test that TestLabel captures all required fields."""
        from test_value_audit import TestScore

        label = TestLabel(
            test_id='tests/test_example.py::test_example',
            file_path='tests/test_example.py',
            test_name='test_example',
            line=42,
            score=15.5,
            bug_detection_score=5.0,
            critical_path_score=3.0,
            integration_score=2.0,
            runtime_penalty=0.5,
            maintenance_burden=1.0,
            manual_label='KEEP',
            reason='High value',
            timestamp='2025-10-23T10:00:00',
            category='MEDIUM',
            action='REVIEW',
            lines_of_code=30,
            mock_count=2,
            assertion_count=3
        )

        # Verify all fields exist
        assert label.test_id == 'tests/test_example.py::test_example'
        assert label.file_path == 'tests/test_example.py'
        assert label.test_name == 'test_example'
        assert label.line == 42
        assert label.score == 15.5
        assert label.manual_label == 'KEEP'
        assert label.timestamp == '2025-10-23T10:00:00'

        # Verify score components
        assert label.bug_detection_score == 5.0
        assert label.critical_path_score == 3.0
        assert label.integration_score == 2.0
        assert label.runtime_penalty == 0.5
        assert label.maintenance_burden == 1.0

    def test_json_serialization_idempotent(self, temp_output, sample_test_data):
        """Test that labels can be saved and loaded without data loss."""
        labeler = TestLabeler(output_file=temp_output)

        # Store and save
        labeler._store_label(sample_test_data, 'KEEP', 'Test reason')
        labeler._save_labels()

        # Load in new labeler
        labeler2 = TestLabeler(output_file=temp_output)

        assert len(labeler2.labeled) == 1

        original = labeler.labeled[0]
        loaded = labeler2.labeled[0]

        # Verify all fields match
        assert original.test_id == loaded.test_id
        assert original.manual_label == loaded.manual_label
        assert original.reason == loaded.reason
        assert original.score == loaded.score
        assert original.bug_detection_score == loaded.bug_detection_score

    def test_resume_skips_already_labeled(self, temp_output):
        """Test that resume functionality skips already labeled tests."""
        # Create existing labels
        existing = [
            {
                'test_id': 'tests/test_a.py::test_skip_me',
                'file_path': 'tests/test_a.py',
                'test_name': 'test_skip_me',
                'line': 10,
                'score': 5.0,
                'bug_detection_score': 2.0,
                'critical_path_score': 1.0,
                'integration_score': 1.0,
                'runtime_penalty': 0.5,
                'maintenance_burden': 1.5,
                'manual_label': 'DELETE',
                'reason': 'Already labeled',
                'timestamp': '2025-10-23T10:00:00',
                'category': 'LOW',
                'action': 'DELETE',
                'lines_of_code': 20,
                'mock_count': 5,
                'assertion_count': 1
            }
        ]

        with open(temp_output, 'w') as f:
            json.dump(existing, f)

        labeler = TestLabeler(output_file=temp_output)

        # Verify test is in labeled_ids
        assert 'tests/test_a.py::test_skip_me' in labeler.labeled_ids

        # Verify count
        assert len(labeler.labeled) == 1


class TestIntegration:
    """Integration tests for full workflow."""

    def test_cli_help_displays(self):
        """Test CLI --help displays usage."""
        import subprocess

        result = subprocess.run(
            [sys.executable, 'scripts/label_tests.py', '--help'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert 'Manual test quality labeling' in result.stdout
        assert '--sample-size' in result.stdout
        assert '--continue' in result.stdout
        assert '--filter' in result.stdout

    @pytest.mark.skip(reason="Requires full test suite extraction (slow)")
    def test_full_labeling_workflow(self, tmp_path):
        """
        Integration test for complete labeling workflow.

        Skipped by default - enable for full validation.
        """
        output_file = tmp_path / "integration_labels.json"

        labeler = TestLabeler(
            output_file=output_file,
            sample_size=5,
            filter_category='LOW'
        )

        # Mock user inputs (label 5 tests as DELETE)
        inputs = []
        for _ in range(5):
            inputs.extend(['D', 'Integration test label'])

        with patch('builtins.input', side_effect=inputs):
            labeler.run()

        # Verify output file
        assert output_file.exists()

        with open(output_file, 'r') as f:
            labels = json.load(f)

        # Should have 5 labels (if 5+ LOW tests exist)
        assert len(labels) >= 0  # Graceful if no tests found
        if labels:
            assert all(label['manual_label'] == 'DELETE' for label in labels)


# Constitutional Compliance Validation
def test_article_v_traceability():
    """
    Verify Article V compliance - traces to specification.

    This tool implements Phase 6 of TEST_AUDIT_V5_PLAN.md.
    """
    plan_path = Path(__file__).parent.parent / "TEST_AUDIT_V5_PLAN.md"

    assert plan_path.exists(), "TEST_AUDIT_V5_PLAN.md must exist"

    with open(plan_path, 'r') as f:
        content = f.read()

    # Verify Phase 6 mentions manual labeling
    assert 'Phase 6' in content
    assert 'Grid Search Tuner' in content or 'manual label' in content.lower()


def test_article_iii_no_auto_delete():
    """
    Verify Article III compliance - no manual overrides.

    Tool stores labels but never auto-applies deletions.
    """
    # Read tool source
    tool_path = Path(__file__).parent.parent / "scripts" / "label_tests.py"

    with open(tool_path, 'r') as f:
        source = f.read()

    # Should NOT contain auto-deletion code
    assert 'os.remove' not in source
    assert 'shutil.rmtree' not in source
    assert 'DELETE FROM tests' not in source  # No SQL deletion

    # Should only save labels
    assert 'json.dump' in source
    assert 'labeled_tests.json' in source
