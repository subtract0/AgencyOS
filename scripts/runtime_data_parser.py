#!/usr/bin/env python3
"""
Runtime Data Parser - Extract actual test execution times from pytest outputs.

Supports multiple formats:
- JUnit XML (pytest --junitxml)
- pytest-reportlog JSON (pytest-reportlog plugin)
- Fallback to heuristics if no data available

Constitutional Article I: Idempotency - Safe to re-run without corrupting data.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
import re


@dataclass
class TestRuntime:
    """Test runtime data extracted from execution logs."""
    test_id: str  # Full test identifier (file::class::method)
    duration_seconds: float  # Actual execution time
    source: str  # 'junitxml', 'reportlog', 'heuristic'
    timestamp: Optional[str] = None


class RuntimeDataParser:
    """Parse pytest execution reports for actual test runtimes."""

    def __init__(self):
        self.runtimes: Dict[str, TestRuntime] = {}

    def parse_junitxml(self, xml_path: Path) -> Dict[str, float]:
        """
        Parse JUnit XML file from pytest --junitxml output.

        Format:
        <testsuites>
          <testsuite name="pytest" tests="100">
            <testcase classname="tests.test_foo" name="test_bar" time="0.123"/>
          </testsuite>
        </testsuites>

        Returns:
            dict[test_id, runtime_seconds]
        """
        if not xml_path.exists():
            return {}

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            runtimes = {}

            # Handle both <testsuites> wrapper and direct <testsuite>
            testsuites = root.findall('.//testsuite')
            if not testsuites:
                testsuites = [root] if root.tag == 'testsuite' else []

            for testsuite in testsuites:
                for testcase in testsuite.findall('testcase'):
                    classname = testcase.get('classname', '')
                    name = testcase.get('name', '')
                    time_str = testcase.get('time', '0')

                    # Convert time to float (handle missing/malformed)
                    try:
                        duration = float(time_str)
                    except (ValueError, TypeError):
                        duration = 0.0

                    # Build test_id in pytest format: file::class::method or file::method
                    # JUnit classname format: tests.test_module.TestClass
                    # Convert to pytest: tests/test_module.py::TestClass::test_method

                    if classname:
                        # Convert dotted path to file path
                        file_path = classname.replace('.', '/') + '.py'
                        test_id = f"{file_path}::{name}"
                    else:
                        test_id = name

                    runtimes[test_id] = duration

                    # Store as TestRuntime object
                    self.runtimes[test_id] = TestRuntime(
                        test_id=test_id,
                        duration_seconds=duration,
                        source='junitxml'
                    )

            return runtimes

        except ET.ParseError as e:
            print(f"⚠️  Failed to parse JUnit XML {xml_path}: {e}")
            return {}

    def parse_reportlog(self, json_path: Path) -> Dict[str, float]:
        """
        Parse pytest-reportlog JSON output.

        Format (newline-delimited JSON):
        {"nodeid": "tests/test_foo.py::test_bar", "when": "call", "duration": 0.123}

        Returns:
            dict[test_id, runtime_seconds]
        """
        if not json_path.exists():
            return {}

        try:
            runtimes = {}

            with open(json_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        entry = json.loads(line)

                        # Only use "call" phase (not setup/teardown)
                        if entry.get('when') == 'call':
                            nodeid = entry.get('nodeid', '')
                            duration = entry.get('duration', 0.0)

                            if nodeid:
                                runtimes[nodeid] = duration

                                self.runtimes[nodeid] = TestRuntime(
                                    test_id=nodeid,
                                    duration_seconds=duration,
                                    source='reportlog'
                                )

                    except json.JSONDecodeError:
                        continue

            return runtimes

        except Exception as e:
            print(f"⚠️  Failed to parse reportlog {json_path}: {e}")
            return {}

    def estimate_runtime_from_heuristics(self, test_code: str, test_name: str) -> float:
        """
        Fallback: Estimate runtime from test code heuristics.

        Heuristics (CODE patterns checked first - more specific than NAME):
        - E2E/integration tests: 30s default
        - Database tests: 5s
        - Mock-heavy tests: 1s
        - Simple unit tests: 0.1s
        """
        code_lower = test_code.lower()
        name_lower = test_name.lower()

        # Check CODE patterns first (more specific than name patterns)
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

        # E2E and integration tests (only check NAME if code didn't match specific patterns)
        if any(k in name_lower for k in ['e2e', 'end_to_end']):
            return 30.0
        # Integration is less specific, so use moderate estimate
        if 'integration' in name_lower:
            return 10.0

        # Simple unit tests (fast)
        return 0.1

    def parse_all_sources(
        self,
        junitxml_paths: Optional[List[Path]] = None,
        reportlog_paths: Optional[List[Path]] = None,
        fallback_to_heuristics: bool = True
    ) -> Dict[str, float]:
        """
        Parse all available runtime data sources.

        Priority:
        1. pytest-reportlog (most accurate, includes setup/teardown separately)
        2. JUnit XML (standard pytest output)
        3. Heuristics (fallback if no data)

        Args:
            junitxml_paths: List of paths to JUnit XML files
            reportlog_paths: List of paths to reportlog JSON files
            fallback_to_heuristics: If True, estimate missing runtimes

        Returns:
            dict[test_id, runtime_seconds]
        """
        all_runtimes = {}

        # Parse reportlog files (highest priority)
        if reportlog_paths:
            for path in reportlog_paths:
                runtimes = self.parse_reportlog(path)
                all_runtimes.update(runtimes)
                print(f"  ✅ Parsed {len(runtimes)} runtimes from {path.name}")

        # Parse JUnit XML files (fallback if reportlog missing)
        if junitxml_paths:
            for path in junitxml_paths:
                runtimes = self.parse_junitxml(path)
                # Only add if not already present from reportlog
                for test_id, duration in runtimes.items():
                    if test_id not in all_runtimes:
                        all_runtimes[test_id] = duration
                print(f"  ✅ Parsed {len(runtimes)} runtimes from {path.name}")

        return all_runtimes

    def get_runtime(self, test_id: str, test_code: str = "") -> float:
        """
        Get runtime for a specific test.

        Falls back to heuristics if no data available.
        """
        if test_id in self.runtimes:
            return self.runtimes[test_id].duration_seconds

        # Fallback to heuristics
        return self.estimate_runtime_from_heuristics(test_code, test_id)

    def export_runtimes(self, output_path: Path) -> None:
        """Export parsed runtimes to JSON for caching."""
        data = {
            test_id: {
                'duration_seconds': rt.duration_seconds,
                'source': rt.source,
                'timestamp': rt.timestamp
            }
            for test_id, rt in self.runtimes.items()
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Exported {len(data)} runtimes to {output_path}")

    def load_cached_runtimes(self, cache_path: Path) -> bool:
        """
        Load previously parsed runtimes from cache.

        Returns:
            True if cache was successfully parsed (even if empty)
            False if cache failed to parse (corrupt JSON)
        """
        if not cache_path.exists():
            return False

        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)

            # Handle both formats: direct dict or nested under 'runtimes' key
            if 'runtimes' in data:
                # New format with metadata
                runtimes_data = data['runtimes']
            else:
                # Legacy format (direct dict)
                runtimes_data = data

            for test_id, rt_data in runtimes_data.items():
                self.runtimes[test_id] = TestRuntime(
                    test_id=test_id,
                    duration_seconds=rt_data['duration_seconds'],
                    source=rt_data['source'],
                    timestamp=rt_data.get('timestamp')
                )

            print(f"✅ Loaded {len(runtimes_data)} runtimes from cache")
            return True

        except Exception as e:
            print(f"⚠️  Failed to load cache {cache_path}: {e}")
            return False


def find_pytest_outputs(search_dirs: Optional[List[Path]] = None) -> Dict[str, List[Path]]:
    """
    Find all pytest output files in typical locations.

    Returns:
        {'junitxml': [...], 'reportlog': [...]}
    """
    if search_dirs is None:
        search_dirs = [
            Path.cwd(),
            Path.cwd() / '.pytest_cache',
            Path.cwd() / 'test-results',
            Path.cwd() / 'logs',
        ]

    found = {
        'junitxml': [],
        'reportlog': []
    }

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        # Find JUnit XML files
        for xml_file in search_dir.rglob('*.xml'):
            # Check if it's a JUnit XML (has <testsuites> or <testsuite> root)
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                if root.tag in ['testsuites', 'testsuite']:
                    found['junitxml'].append(xml_file)
            except:
                continue

        # Find reportlog JSON files
        for json_file in search_dir.rglob('*.jsonl'):
            found['reportlog'].append(json_file)

        for json_file in search_dir.rglob('*reportlog*.json'):
            found['reportlog'].append(json_file)

    return found


if __name__ == '__main__':
    # Demo: Parse runtime data
    parser = RuntimeDataParser()

    # Find pytest outputs
    outputs = find_pytest_outputs()
    print(f"Found {len(outputs['junitxml'])} JUnit XML files")
    print(f"Found {len(outputs['reportlog'])} reportlog files")

    # Parse all sources
    runtimes = parser.parse_all_sources(
        junitxml_paths=outputs['junitxml'],
        reportlog_paths=outputs['reportlog']
    )

    print(f"\n✅ Parsed {len(runtimes)} test runtimes")

    # Show sample
    if runtimes:
        print("\nSample runtimes:")
        for test_id, duration in list(runtimes.items())[:10]:
            print(f"  {test_id}: {duration:.3f}s")

    # Cache results
    cache_path = Path('.audit') / 'runtime_cache.json'
    cache_path.parent.mkdir(exist_ok=True)
    parser.export_runtimes(cache_path)
