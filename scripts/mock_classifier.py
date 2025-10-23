#!/usr/bin/env python3
"""
Mock Classifier - Distinguish external vs internal mocks.

External mocks (DB, API, filesystem) = acceptable test isolation.
Internal mocks (project classes) = tests implementation details (code smell).

Performance SLA: <10ms per test function.
"""

import ast
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class MockAnalysis:
    """Mock usage analysis for a test."""
    test_name: str
    external_mock_count: int  # DB, API, filesystem mocks (acceptable)
    internal_mock_count: int  # Project class mocks (code smell)
    external_targets: List[str]  # List of external mock targets
    internal_targets: List[str]  # List of internal mock targets


class MockClassifier:
    """Classify mocks as external vs internal."""

    # External mock patterns (acceptable)
    EXTERNAL_PATTERNS = {
        'requests', 'httpx', 'urllib', 'aiohttp',  # HTTP clients
        'psycopg2', 'pymongo', 'redis', 'sqlalchemy',  # Databases
        'boto3', 'google.cloud', 'azure',  # Cloud SDKs
        'Path', 'open', 'os.', 'shutil',  # Filesystem
        'subprocess', 'socket',  # System calls
        'datetime', 'time',  # Time mocking
        'environ', 'getenv',  # Environment variables
    }

    def __init__(self, project_modules: List[str] = None):
        """
        Initialize mock classifier.

        Args:
            project_modules: List of project module prefixes (e.g., ['agency', 'shared', 'tools'])
        """
        if project_modules is None:
            project_modules = ['agency', 'shared', 'tools', 'coding_agent', 'planner_agent']

        self.project_modules = project_modules

    def analyze_test(self, test_code: str, test_name: str) -> MockAnalysis:
        """
        Analyze mock usage in test code.

        Args:
            test_code: Test function source code
            test_name: Test function name

        Returns:
            MockAnalysis object with external/internal counts
        """
        external_targets = []
        internal_targets = []

        try:
            tree = ast.parse(test_code)

            for node in ast.walk(tree):
                # Check for MagicMock(spec=...) or Mock(spec=...)
                if isinstance(node, ast.Call):
                    if self._is_mock_call(node):
                        target = self._extract_mock_target(node)
                        if target:
                            if self._is_external(target):
                                external_targets.append(target)
                            else:
                                internal_targets.append(target)

                # Check for patch('module.path')
                elif isinstance(node, ast.Call):
                    if self._is_patch_call(node):
                        target = self._extract_patch_target(node)
                        if target:
                            if self._is_external(target):
                                external_targets.append(target)
                            else:
                                internal_targets.append(target)

        except Exception:
            # If parsing fails, fall back to string matching
            return self._fallback_analysis(test_code, test_name)

        return MockAnalysis(
            test_name=test_name,
            external_mock_count=len(external_targets),
            internal_mock_count=len(internal_targets),
            external_targets=external_targets,
            internal_targets=internal_targets
        )

    def _is_mock_call(self, node: ast.Call) -> bool:
        """Check if node is a Mock() or MagicMock() call."""
        if isinstance(node.func, ast.Name):
            return node.func.id in ('Mock', 'MagicMock', 'AsyncMock')
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr in ('Mock', 'MagicMock', 'AsyncMock')
        return False

    def _is_patch_call(self, node: ast.Call) -> bool:
        """Check if node is a patch() or patch.object() call."""
        if isinstance(node.func, ast.Name):
            return node.func.id == 'patch'
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr in ('patch', 'patch_object')
        return False

    def _extract_mock_target(self, node: ast.Call) -> str:
        """Extract target from Mock(spec=...) call."""
        for keyword in node.keywords:
            if keyword.arg in ('spec', 'spec_set'):
                if isinstance(keyword.value, ast.Name):
                    return keyword.value.id
                elif isinstance(keyword.value, ast.Attribute):
                    return ast.unparse(keyword.value)
        return None

    def _extract_patch_target(self, node: ast.Call) -> str:
        """Extract target from patch('module.path') call."""
        if node.args and isinstance(node.args[0], ast.Constant):
            return node.args[0].value
        return None

    def _is_external(self, target: str) -> bool:
        """Determine if mock target is external (not project code)."""
        # Check external patterns
        for pattern in self.EXTERNAL_PATTERNS:
            if pattern in target.lower():
                return True

        # Check if it's a project module
        for module in self.project_modules:
            if target.startswith(module):
                return False

        # Default: assume external if not recognized as internal
        return True

    def _fallback_analysis(self, test_code: str, test_name: str) -> MockAnalysis:
        """Fallback mock analysis using string matching."""
        external_count = 0
        internal_count = 0

        # Count external patterns
        for pattern in self.EXTERNAL_PATTERNS:
            external_count += test_code.count(f"'{pattern}") + test_code.count(f'"{pattern}')

        # Count internal patterns
        for module in self.project_modules:
            internal_count += test_code.count(f"'{module}") + test_code.count(f'"{module}')

        return MockAnalysis(
            test_name=test_name,
            external_mock_count=external_count,
            internal_mock_count=internal_count,
            external_targets=[],
            internal_targets=[]
        )

    def calculate_mock_penalty(self, analysis: MockAnalysis, config: Dict = None) -> float:
        """
        Calculate maintenance burden from mock usage.

        Formula: burden = (external_mocks * EXTERNAL_WEIGHT) + (internal_mocks * INTERNAL_WEIGHT)

        Args:
            analysis: MockAnalysis object
            config: Optional config with external_mock_weight (default: 0.3) and internal_mock_weight (default: 0.8)

        Returns:
            Mock penalty (higher = more brittle)
        """
        if config is None:
            config = {}

        external_weight = config.get('external_mock_weight', 0.3)
        internal_weight = config.get('internal_mock_weight', 0.8)

        external_penalty = analysis.external_mock_count * external_weight
        internal_penalty = analysis.internal_mock_count * internal_weight

        return external_penalty + internal_penalty


if __name__ == '__main__':
    # Demo: Classify mocks
    classifier = MockClassifier()

    test_cases = [
        ("External DB mock", """
def test_database(session):
    mock_session = MagicMock(spec=Session)
    mock_session.query.return_value.first.return_value = User(name="Alice")
    assert True
"""),
        ("Internal class mock", """
def test_agent_context():
    mock_context = MagicMock(spec=AgentContext)
    mock_context.get_metadata.return_value = {"foo": "bar"}
    assert True
"""),
        ("Mixed mocks", """
def test_api_call():
    with patch('requests.get') as mock_get:  # External
        with patch('agency.tools.bash.run_command') as mock_run:  # Internal
            mock_get.return_value.status_code = 200
            mock_run.return_value = "output"
            assert True
"""),
    ]

    print("Mock Classification Analysis")
    print("=" * 80)
    print(f"{'Test':<25} {'External':<12} {'Internal':<12} {'Penalty':<10}")
    print("-" * 80)

    for name, code in test_cases:
        analysis = classifier.analyze_test(code, name)
        penalty = classifier.calculate_mock_penalty(analysis)

        print(f"{name:<25} {analysis.external_mock_count:<12} {analysis.internal_mock_count:<12} {penalty:<10.1f}")

    print("=" * 80)
    print("External weight: 0.3 (acceptable overhead)")
    print("Internal weight: 0.8 (tests implementation, code smell)")
