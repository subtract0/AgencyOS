"""
Tests for test generation module.
"""
import os
from tools.codegen.test_gen import generate_tests_from_spec


def test_generate_tests_from_spec_basic(tmp_path):
    """Test basic test generation from spec."""
    # Create a sample spec file
    spec_file = tmp_path / "spec-sample.md"
    spec_file.write_text("""
# Sample Specification

## Goals
This is a sample spec for testing.

## Acceptance Criteria
- AC1: System should handle basic operations correctly
- AC2: Error conditions should be properly managed
- AC3: Performance should meet specified thresholds

## Success Metrics
Some success metrics here.
""")

    out_dir = tmp_path / "tests_output"
    results = generate_tests_from_spec(str(spec_file), str(out_dir))

    # Should generate 3 test files (one per AC)
    assert len(results) == 3

    # Check that all tests were created successfully
    for result in results:
        assert result.status == "created"
        assert result.ac_id in ["AC1", "AC2", "AC3"]
        assert os.path.exists(result.path)

    # Verify test file structure
    test_dir = out_dir / "test_sample"
    assert test_dir.exists()

    # Check that test files contain expected content
    for result in results:
        with open(result.path, 'r') as f:
            content = f.read()
            assert f"def test_{result.name}():" in content
            assert result.ac_id in content
            assert "pytest.skip" in content
            assert "TODO" in content


def test_generate_tests_no_acceptance_criteria(tmp_path):
    """Test spec without acceptance criteria."""
    spec_file = tmp_path / "spec-no-ac.md"
    spec_file.write_text("""
# Specification Without AC

## Goals
Some goals here.

## Requirements
Some requirements.
""")

    out_dir = tmp_path / "tests_output"
    results = generate_tests_from_spec(str(spec_file), str(out_dir))

    # Should return error result
    assert len(results) == 1
    assert results[0].status == "error"


def test_generate_tests_file_not_found(tmp_path):
    """Test handling of missing spec file."""
    out_dir = tmp_path / "tests_output"
    results = generate_tests_from_spec("nonexistent.md", str(out_dir))

    assert len(results) == 1
    assert "error" in results[0].status
    assert "Could not read spec file" in results[0].status


def test_generate_tests_complex_ac_names(tmp_path):
    """Test handling of complex acceptance criteria descriptions."""
    spec_file = tmp_path / "spec-complex.md"
    spec_file.write_text("""
# Complex Spec

## Acceptance Criteria
- AC1: System should handle very long descriptions with special characters like @#$% and numbers 123
- AC10: Multi-word acceptance criteria with various punctuation marks!
""")

    out_dir = tmp_path / "tests_output"
    results = generate_tests_from_spec(str(spec_file), str(out_dir))

    assert len(results) == 2

    # Check that test names are valid Python identifiers
    for result in results:
        assert result.status == "created"
        # Test name should not contain special characters
        assert all(c.isalnum() or c == '_' for c in result.name)
        assert result.name.startswith("ac")