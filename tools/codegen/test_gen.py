"""
Test skeleton generation from specifications.
"""
from __future__ import annotations

import dataclasses
import os
import re
from typing import List, Optional


@dataclasses.dataclass
class GeneratedTest:
    """A generated test file."""
    path: str
    ac_id: str
    name: str
    status: str  # "created", "skipped", "error"


def generate_tests_from_spec(spec_path: str, out_dir: str) -> List[GeneratedTest]:
    """
    Generate pytest test skeletons from spec acceptance criteria.

    Args:
        spec_path: Path to the specification markdown file
        out_dir: Output directory for generated tests

    Returns:
        List of generated test files
    """
    results: List[GeneratedTest] = []

    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract spec name from filename
        spec_name = os.path.basename(spec_path).replace('.md', '').replace('spec-', '')

        # Parse acceptance criteria
        criteria = _parse_acceptance_criteria(content)

        if not criteria:
            return [GeneratedTest(
                path=spec_path,
                ac_id="",
                name="",
                status="error"
            )]

        # Create output directory
        test_dir = os.path.join(out_dir, f"test_{spec_name}")
        os.makedirs(test_dir, exist_ok=True)

        # Generate test file for each acceptance criterion
        for ac_id, description in criteria.items():
            test_name = _ac_to_test_name(ac_id, description)
            test_file = os.path.join(test_dir, f"test_{test_name}.py")

            test_content = _generate_test_content(spec_name, ac_id, description, test_name)

            try:
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_content)

                results.append(GeneratedTest(
                    path=test_file,
                    ac_id=ac_id,
                    name=test_name,
                    status="created"
                ))
            except OSError as e:
                results.append(GeneratedTest(
                    path=test_file,
                    ac_id=ac_id,
                    name=test_name,
                    status=f"error: {e}"
                ))

    except OSError as e:
        results.append(GeneratedTest(
            path=spec_path,
            ac_id="",
            name="",
            status=f"error: Could not read spec file: {e}"
        ))

    return results


def _parse_acceptance_criteria(content: str) -> dict[str, str]:
    """Extract acceptance criteria from spec markdown."""
    criteria = {}

    # Look for "Acceptance Criteria" section
    lines = content.split('\n')
    in_ac_section = False

    for line in lines:
        line = line.strip()

        # Check if we're entering acceptance criteria section
        if re.match(r'^#+\s*acceptance\s+criteria', line, re.IGNORECASE):
            in_ac_section = True
            continue

        # Check if we're leaving the section (new header)
        if in_ac_section and line.startswith('#') and not re.match(r'^#+\s*acceptance\s+criteria', line, re.IGNORECASE):
            break

        # Parse AC items (e.g., "- AC1: Description")
        if in_ac_section:
            match = re.match(r'^-\s*AC(\d+):\s*(.+)$', line, re.IGNORECASE)
            if match:
                ac_num = match.group(1)
                description = match.group(2)
                criteria[f"AC{ac_num}"] = description

    return criteria


def _ac_to_test_name(ac_id: str, description: str) -> str:
    """Convert acceptance criteria to test function name."""
    # Clean description and make it a valid Python identifier
    clean_desc = re.sub(r'[^\w\s]', '', description.lower())
    words = clean_desc.split()[:6]  # Limit to first 6 words
    test_name = f"ac{ac_id.lower().replace('ac', '')}_{('_'.join(words))}"
    return re.sub(r'[^\w]', '_', test_name)


def _generate_test_content(spec_name: str, ac_id: str, description: str, test_name: str) -> str:
    """Generate the actual test file content."""
    return f'''"""
Tests for {spec_name} - {ac_id}

Generated from specification acceptance criteria.
"""
import pytest


def test_{test_name}():
    """
    {ac_id}: {description}

    TODO: Implement test logic for this acceptance criterion.
    """
    # TODO: Add test setup
    # TODO: Add test execution
    # TODO: Add assertions
    pytest.skip("Test skeleton generated - needs implementation")


# TODO: Add additional test cases as needed
# TODO: Add fixtures if required
# TODO: Review and customize imports
'''