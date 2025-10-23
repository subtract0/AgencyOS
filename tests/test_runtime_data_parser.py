#!/usr/bin/env python3
"""
Tests for runtime data parser (Phase 1: Actual Runtime Data Integration).

Validates:
- JUnit XML parsing
- pytest-reportlog JSON parsing
- Heuristic fallback estimation
- Non-linear penalty calculation
"""

import pytest
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

# Add scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from runtime_data_parser import RuntimeDataParser, TestRuntime, find_pytest_outputs
from runtime_penalty import RuntimePenaltyCalculator


class TestRuntimeDataParser:
    """Test runtime data parser functionality."""

    def test_parse_junitxml_basic(self, tmp_path):
        """Test parsing basic JUnit XML file."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" tests="3" time="1.234">
    <testcase classname="tests.test_foo" name="test_bar" time="0.123"/>
    <testcase classname="tests.test_foo" name="test_baz" time="0.456"/>
    <testcase classname="tests.test_qux" name="test_quux" time="0.789"/>
  </testsuite>
</testsuites>
"""
        xml_path = tmp_path / "junit.xml"
        xml_path.write_text(xml_content)

        parser = RuntimeDataParser()
        runtimes = parser.parse_junitxml(xml_path)

        assert len(runtimes) == 3
        assert runtimes["tests/test_foo.py::test_bar"] == 0.123
        assert runtimes["tests/test_foo.py::test_baz"] == 0.456
        assert runtimes["tests/test_qux.py::test_quux"] == 0.789

    def test_parse_junitxml_missing_time(self, tmp_path):
        """Test parsing JUnit XML with missing time fields."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" tests="2">
    <testcase classname="tests.test_foo" name="test_bar"/>
    <testcase classname="tests.test_foo" name="test_baz" time="0.5"/>
  </testsuite>
</testsuites>
"""
        xml_path = tmp_path / "junit.xml"
        xml_path.write_text(xml_content)

        parser = RuntimeDataParser()
        runtimes = parser.parse_junitxml(xml_path)

        assert len(runtimes) == 2
        assert runtimes["tests/test_foo.py::test_bar"] == 0.0  # Missing time = 0
        assert runtimes["tests/test_foo.py::test_baz"] == 0.5

    def test_parse_junitxml_malformed_xml(self, tmp_path):
        """Test graceful handling of malformed XML."""
        xml_path = tmp_path / "malformed.xml"
        xml_path.write_text("<not valid xml>")

        parser = RuntimeDataParser()
        runtimes = parser.parse_junitxml(xml_path)

        assert runtimes == {}  # Returns empty dict on parse error

    def test_parse_reportlog_json(self, tmp_path):
        """Test parsing pytest-reportlog JSON format."""
        json_content = """{"nodeid": "tests/test_foo.py::test_bar", "when": "call", "duration": 0.123}
{"nodeid": "tests/test_foo.py::test_baz", "when": "call", "duration": 0.456}
{"nodeid": "tests/test_qux.py::test_quux", "when": "setup", "duration": 0.01}
{"nodeid": "tests/test_qux.py::test_quux", "when": "call", "duration": 0.789}
"""
        json_path = tmp_path / "reportlog.jsonl"
        json_path.write_text(json_content)

        parser = RuntimeDataParser()
        runtimes = parser.parse_reportlog(json_path)

        assert len(runtimes) == 3
        assert runtimes["tests/test_foo.py::test_bar"] == 0.123
        assert runtimes["tests/test_foo.py::test_baz"] == 0.456
        assert runtimes["tests/test_qux.py::test_quux"] == 0.789  # Only "call" phase

    def test_parse_reportlog_empty_file(self, tmp_path):
        """Test parsing empty reportlog file."""
        json_path = tmp_path / "empty.jsonl"
        json_path.write_text("")

        parser = RuntimeDataParser()
        runtimes = parser.parse_reportlog(json_path)

        assert runtimes == {}

    def test_heuristic_estimation_e2e(self):
        """Test heuristic runtime estimation for E2E tests."""
        parser = RuntimeDataParser()

        e2e_code = """
def test_e2e_user_flow(browser):
    browser.get("http://localhost:8000")
    browser.find_element_by_id("login").click()
    assert "Dashboard" in browser.title
"""
        runtime = parser.estimate_runtime_from_heuristics(e2e_code, "test_e2e_user_flow")
        assert runtime == 30.0  # E2E default

    def test_heuristic_estimation_database(self):
        """Test heuristic runtime estimation for database tests."""
        parser = RuntimeDataParser()

        db_code = """
def test_create_user(session):
    user = User(name="Alice")
    session.add(user)
    session.commit()
    assert session.query(User).count() == 1
"""
        runtime = parser.estimate_runtime_from_heuristics(db_code, "test_create_user")
        assert runtime == 5.0  # Database default

    def test_heuristic_estimation_unit_test(self):
        """Test heuristic runtime estimation for simple unit tests."""
        parser = RuntimeDataParser()

        unit_code = """
def test_addition():
    assert 1 + 1 == 2
"""
        runtime = parser.estimate_runtime_from_heuristics(unit_code, "test_addition")
        assert runtime == 0.1  # Simple unit test default

    def test_get_runtime_with_cached_data(self):
        """Test get_runtime returns cached data when available."""
        parser = RuntimeDataParser()
        parser.runtimes["tests/test_foo.py::test_bar"] = TestRuntime(
            test_id="tests/test_foo.py::test_bar",
            duration_seconds=1.23,
            source="junitxml"
        )

        runtime = parser.get_runtime("tests/test_foo.py::test_bar", "")
        assert runtime == 1.23

    def test_get_runtime_falls_back_to_heuristics(self):
        """Test get_runtime falls back to heuristics when no data."""
        parser = RuntimeDataParser()

        e2e_code = "def test_e2e(): pass"
        runtime = parser.get_runtime("test_e2e", e2e_code)
        assert runtime == 30.0  # E2E heuristic

    def test_export_and_load_cache(self, tmp_path):
        """Test exporting and loading runtime cache."""
        parser = RuntimeDataParser()
        parser.runtimes["test1"] = TestRuntime("test1", 1.0, "junitxml")
        parser.runtimes["test2"] = TestRuntime("test2", 2.0, "reportlog")

        cache_path = tmp_path / "cache.json"
        parser.export_runtimes(cache_path)

        # Load into new parser
        parser2 = RuntimeDataParser()
        parser2.load_cached_runtimes(cache_path)

        assert len(parser2.runtimes) == 2
        assert parser2.runtimes["test1"].duration_seconds == 1.0
        assert parser2.runtimes["test2"].source == "reportlog"

    def test_idempotency(self, tmp_path):
        """Test parser is idempotent (re-running produces same results)."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest">
    <testcase classname="tests.test_foo" name="test_bar" time="0.5"/>
  </testsuite>
</testsuites>
"""
        xml_path = tmp_path / "junit.xml"
        xml_path.write_text(xml_content)

        parser = RuntimeDataParser()
        runtimes1 = parser.parse_junitxml(xml_path)
        runtimes2 = parser.parse_junitxml(xml_path)

        assert runtimes1 == runtimes2  # Identical results


class TestRuntimePenaltyCalculator:
    """Test non-linear runtime penalty calculator."""

    def test_fast_test_minimal_penalty(self):
        """Tests <10s should have minimal linear penalty."""
        calc = RuntimePenaltyCalculator()

        assert calc.calculate_penalty(0.1) < 1.0
        assert calc.calculate_penalty(5.0) < 1.0
        assert calc.calculate_penalty(10.0) == 1.0

    def test_moderate_test_linear_penalty(self):
        """Tests 10-30s should have moderate linear penalty."""
        calc = RuntimePenaltyCalculator()

        penalty_15s = calc.calculate_penalty(15.0)
        penalty_20s = calc.calculate_penalty(20.0)
        penalty_30s = calc.calculate_penalty(30.0)

        assert 1.0 < penalty_15s < 3.0
        assert 1.0 < penalty_20s < 3.0
        assert 3.0 <= penalty_30s < 5.0

    def test_slow_test_exponential_penalty(self):
        """Tests 30-60s should have steep exponential penalty."""
        calc = RuntimePenaltyCalculator()

        penalty_30s = calc.calculate_penalty(30.0)
        penalty_45s = calc.calculate_penalty(45.0)
        penalty_60s = calc.calculate_penalty(60.0)

        assert penalty_45s > penalty_30s * 10  # Exponential growth
        assert penalty_60s > penalty_45s * 2
        assert penalty_60s > 100  # Very high penalty

    def test_extreme_test_high_penalty(self):
        """Tests >60s should have extreme penalty."""
        calc = RuntimePenaltyCalculator()

        penalty_60s = calc.calculate_penalty(60.0)
        penalty_120s = calc.calculate_penalty(120.0)

        assert penalty_120s > 30  # At least 30 points
        assert penalty_120s > penalty_60s  # Higher than 60s

    def test_negative_runtime_returns_zero(self):
        """Negative runtimes should return 0 penalty."""
        calc = RuntimePenaltyCalculator()
        assert calc.calculate_penalty(-5.0) == 0.0

    def test_configurable_weights(self):
        """Test penalty calculator respects custom weights."""
        custom_config = {
            'fast_threshold': 5.0,
            'moderate_threshold': 20.0,
            'slow_threshold': 20.0,
            'extreme_threshold': 40.0,
            'base_weight': 0.2,
            'exponential_factor': 5.0
        }
        calc = RuntimePenaltyCalculator(custom_config)

        penalty = calc.calculate_penalty(5.0)
        assert penalty == 5.0 * 0.2  # Custom base_weight

    def test_penalty_breakdown(self):
        """Test get_penalty_breakdown returns correct metadata."""
        calc = RuntimePenaltyCalculator()

        breakdown = calc.get_penalty_breakdown(5.0)
        assert breakdown['category'] == 'fast'
        assert breakdown['runtime_seconds'] == 5.0
        assert 'explanation' in breakdown

        breakdown = calc.get_penalty_breakdown(45.0)
        assert breakdown['category'] == 'slow'
        assert breakdown['penalty'] > 100  # Exponential

    def test_v4_vs_v5_comparison(self):
        """Test comparison shows V5 penalties higher for slow tests."""
        calc = RuntimePenaltyCalculator()

        comparison = calc.compare_penalties(60.0)
        assert comparison['linear_v4'] == 6.0  # V4: 60 * 0.1
        assert comparison['nonlinear_v5'] > 100  # V5: Much higher
        assert comparison['difference'] > 0  # V5 > V4 for slow tests


class TestIntegration:
    """Integration tests combining parser and penalty calculator."""

    def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow: parse -> calculate penalty."""
        # Create sample JUnit XML
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest">
    <testcase classname="tests.test_fast" name="test_unit" time="0.1"/>
    <testcase classname="tests.test_slow" name="test_e2e" time="65.0"/>
  </testsuite>
</testsuites>
"""
        xml_path = tmp_path / "junit.xml"
        xml_path.write_text(xml_content)

        # Parse runtimes
        parser = RuntimeDataParser()
        runtimes = parser.parse_junitxml(xml_path)

        # Calculate penalties
        calc = RuntimePenaltyCalculator()
        penalties = {test_id: calc.calculate_penalty(runtime) for test_id, runtime in runtimes.items()}

        # Verify
        assert penalties["tests/test_fast.py::test_unit"] < 1.0  # Fast test
        assert penalties["tests/test_slow.py::test_e2e"] > 20.0  # Slow test extreme penalty

    def test_performance_large_dataset(self, tmp_path):
        """Test parser performance with large XML file (100+ tests)."""
        # Generate XML with 100 tests
        testcases = "\n".join([
            f'<testcase classname="tests.test_module{i//10}" name="test_func{i}" time="{i * 0.1}"/>'
            for i in range(100)
        ])
        xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" tests="100">
    {testcases}
  </testsuite>
</testsuites>
"""
        xml_path = tmp_path / "large.xml"
        xml_path.write_text(xml_content)

        parser = RuntimeDataParser()
        runtimes = parser.parse_junitxml(xml_path)

        assert len(runtimes) == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
