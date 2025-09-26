"""
Module and file scaffolding from templates.
"""
from __future__ import annotations

import dataclasses
import os
import re
from typing import Dict, List, Optional
from shared.types.json import JSONValue


@dataclasses.dataclass
class CreatedFile:
    """A scaffolded file."""
    path: str
    template: str
    status: str  # "created", "skipped", "error"


# Built-in templates
TOOL_MODULE_TEMPLATE = {
    "__init__.py": '''"""
{{name}} tool module.

TODO: Add module description.
"""
from .{{name}} import {{class_name}}

__all__ = ["{{class_name}}"]
''',
    "{{name}}.py": '''"""
{{name}} implementation.

TODO: Add implementation details.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from shared.types.json import JSONValue


class {{class_name}}:
    """{{class_name}} implementation."""

    def __init__(self) -> None:
        """Initialize {{name}}."""
        # TODO: Add initialization logic
        pass

    def run(self, **params: Any) -> Dict[str, JSONValue]:
        """
        Execute {{name}} operation.

        Args:
            **params: Operation parameters

        Returns:
            Result dictionary
        """
        # TODO: Implement main logic
        return {"status": "not_implemented", "message": "TODO: Implement {{name}}"}
''',
    "cli.py": '''"""
Command-line interface for {{name}}.
"""
import argparse
import json
import sys
from typing import Any, Dict

from .{{name}} import {{class_name}}


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="{{name}}",
        description="{{class_name}} command-line interface"
    )
    parser.add_argument("--format", choices=["json", "text"], default="text")
    # TODO: Add command-specific arguments

    args = parser.parse_args()

    try:
        # TODO: Initialize and run {{name}}
        tool = {{class_name}}()
        result = tool.run()

        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Status: {result.get('status', 'unknown')}")
            if result.get('message'):
                print(f"Message: {result['message']}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
'''
}

TESTS_MODULE_TEMPLATE = {
    "__init__.py": '# Test module for {{name}}\n',
    "test_{{name}}_basic.py": '''"""
Basic tests for {{name}}.
"""
import pytest

from {{module_path}}.{{name}} import {{class_name}}


class Test{{class_name}}:
    """Test suite for {{class_name}}."""

    def test_init(self):
        """Test {{class_name}} initialization."""
        tool = {{class_name}}()
        assert tool is not None

    def test_run_basic(self):
        """Test basic run operation."""
        tool = {{class_name}}()
        result = tool.run()
        assert isinstance(result, dict)
        assert "status" in result

    # TODO: Add more comprehensive tests
    # TODO: Add edge case tests
    # TODO: Add error condition tests


@pytest.fixture
def {{name}}_instance():
    """Fixture providing {{class_name}} instance."""
    return {{class_name}}()


# TODO: Add integration tests if needed
# TODO: Add property-based tests if applicable
'''
}

TEMPLATES = {
    "tool": TOOL_MODULE_TEMPLATE,
    "tests": TESTS_MODULE_TEMPLATE,
}


def scaffold_module(template: str, name: str, out_dir: str, params: Optional[Dict[str, JSONValue]] = None) -> List[CreatedFile]:
    """
    Create module scaffold from template.

    Args:
        template: Template name ("tool", "tests")
        name: Module name
        out_dir: Output directory
        params: Additional template parameters

    Returns:
        List of created files
    """
    if template not in TEMPLATES:
        return [CreatedFile(
            path="",
            template=template,
            status=f"error: Unknown template '{template}'"
        )]

    if params is None:
        params = {}

    # Prepare template variables
    variables = {
        "name": name,
        "class_name": _to_class_name(name),
        "module_path": params.get("module_path", f"tools.{name}"),
        **params
    }

    results: List[CreatedFile] = []
    template_files = TEMPLATES[template]

    # Create output directory
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as e:
        return [CreatedFile(
            path=out_dir,
            template=template,
            status=f"error: Could not create directory: {e}"
        )]

    # Generate each file from template
    for file_pattern, content_template in template_files.items():
        # Replace placeholders in filename
        filename = _render_template(file_pattern, variables)
        filepath = os.path.join(out_dir, filename)

        # Replace placeholders in content
        content = _render_template(content_template, variables)

        try:
            # Create parent directories if needed
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            results.append(CreatedFile(
                path=filepath,
                template=template,
                status="created"
            ))

        except OSError as e:
            results.append(CreatedFile(
                path=filepath,
                template=template,
                status=f"error: {e}"
            ))

    return results


def _to_class_name(name: str) -> str:
    """Convert module name to class name (PascalCase)."""
    words = re.split(r'[_\s-]+', name)
    return ''.join(word.capitalize() for word in words if word)


def _render_template(template: str, variables: Dict[str, JSONValue]) -> str:
    """Simple template rendering with {{var}} placeholders."""
    result = template
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))
    return result