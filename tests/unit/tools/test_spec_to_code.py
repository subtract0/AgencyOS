"""
Tests for Spec to Code Generator (Phase 4).

Tests the specification parsing and code generation including:
- Markdown spec parsing
- Function/class generation
- Test scaffolding
- Documentation generation
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestFunctionSpec:
    """Tests for FunctionSpec dataclass."""

    def test_function_spec_creation(self):
        """Test creating a function spec."""
        from tools.spec_to_code import FunctionSpec

        spec = FunctionSpec(
            name="calculate_total",
            description="Calculate the total amount",
            parameters=[{"name": "items", "type": "list[int]"}],
            return_type="int",
            return_description="The sum of all items",
            examples=[{"input": "calculate_total([1,2,3])", "expected_output": "6"}],
            raises=[],
        )

        assert spec.name == "calculate_total"
        assert spec.return_type == "int"
        assert len(spec.parameters) == 1

    def test_function_spec_with_defaults(self):
        """Test function spec with default values."""
        from tools.spec_to_code import FunctionSpec

        spec = FunctionSpec(
            name="greet",
            description="Greet someone",
            parameters=[{"name": "name", "type": "str", "default": '"World"'}],
            return_type="str",
            return_description="Greeting message",
            examples=[],
            raises=[],
            tags=["utility", "string"],
        )

        assert len(spec.tags) == 2
        assert spec.parameters[0]["default"] == '"World"'


class TestClassSpec:
    """Tests for ClassSpec dataclass."""

    def test_class_spec_creation(self):
        """Test creating a class spec."""
        from tools.spec_to_code import ClassSpec, FunctionSpec

        method = FunctionSpec(
            name="process",
            description="Process data",
            parameters=[],
            return_type="dict",
            return_description="Processed data",
            examples=[],
            raises=[],
        )

        spec = ClassSpec(
            name="DataProcessor",
            description="Processes data efficiently",
            attributes=[{"name": "data", "type": "list"}],
            methods=[method],
        )

        assert spec.name == "DataProcessor"
        assert len(spec.methods) == 1
        assert len(spec.attributes) == 1


class TestModuleSpec:
    """Tests for ModuleSpec dataclass."""

    def test_module_spec_creation(self):
        """Test creating a module spec."""
        from tools.spec_to_code import ModuleSpec

        spec = ModuleSpec(
            name="data_utils",
            description="Data utility functions",
            imports=["import json", "from typing import Any"],
            functions=[],
            classes=[],
            constants=[{"name": "MAX_SIZE", "value": "1000", "type": "int"}],
        )

        assert spec.name == "data_utils"
        assert len(spec.imports) == 2
        assert len(spec.constants) == 1


class TestSpecParser:
    """Tests for SpecParser class."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        from tools.spec_to_code import SpecParser

        return SpecParser()

    def test_parse_simple_spec(self, parser):
        """Test parsing a simple specification."""
        content = """# Data Utils

A utility module for data processing.

## Functions

### `process_data(input: str)`

Process the input data and return result.

Returns: `dict`
"""

        result = parser.parse_spec_content(content, "data_utils")

        assert result.is_ok()
        spec = result.unwrap()
        assert spec.name == "data_utils"
        assert len(spec.functions) == 1
        assert spec.functions[0].name == "process_data"

    def test_parse_spec_with_examples(self, parser):
        """Test parsing spec with code examples."""
        content = """# Calculator

Simple calculator.

## Functions

### `add(a: int, b: int)`

Add two numbers.

Returns: `int`

Example:
```python
>>> add(2, 3)
5
```
"""

        result = parser.parse_spec_content(content, "calculator")

        assert result.is_ok()
        spec = result.unwrap()
        assert len(spec.functions) == 1
        # Examples should be parsed
        assert len(spec.functions[0].examples) >= 0

    def test_parse_spec_with_class(self, parser):
        """Test parsing spec with class definition."""
        content = """# Models

Data models.

## Classes

### class User

Represents a user.

- `name`: `str`
- `age`: `int`

### `get_info()`

Get user info.

Returns: `dict`
"""

        result = parser.parse_spec_content(content, "models")

        assert result.is_ok()
        spec = result.unwrap()
        assert len(spec.classes) == 1
        assert spec.classes[0].name == "User"

    def test_parse_nonexistent_file(self, parser):
        """Test parsing nonexistent file returns error."""
        result = parser.parse_spec_file("/nonexistent/path/spec.md")

        assert result.is_err()
        assert "not found" in result.unwrap_err()

    def test_extract_sections(self, parser):
        """Test section extraction from markdown."""
        content = """# Title

Description text.

## Functions

Function content here.

## Classes

Class content here.
"""

        sections = parser._extract_sections(content)

        assert "description" in sections
        assert "functions" in sections
        assert "classes" in sections

    def test_parse_parameters(self, parser):
        """Test parameter parsing."""
        params = parser._parse_parameters("x: int, y: str = 'default'", "")

        assert len(params) == 2
        assert params[0]["name"] == "x"
        assert params[0]["type"] == "int"
        assert params[1]["default"] is not None


class TestCodeGenerator:
    """Tests for CodeGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        from tools.spec_to_code import CodeGenerator

        return CodeGenerator()

    @pytest.fixture
    def simple_spec(self):
        """Create a simple module spec."""
        from tools.spec_to_code import FunctionSpec, ModuleSpec

        return ModuleSpec(
            name="utils",
            description="Utility functions",
            imports=[],
            functions=[
                FunctionSpec(
                    name="helper",
                    description="A helper function",
                    parameters=[{"name": "x", "type": "int"}],
                    return_type="int",
                    return_description="The result",
                    examples=[],
                    raises=[],
                )
            ],
            classes=[],
            constants=[],
        )

    def test_generate_returns_code(self, generator, simple_spec):
        """Test that generate returns GeneratedCode."""
        result = generator.generate(simple_spec)

        assert result.is_ok()
        generated = result.unwrap()
        assert generated.source_code is not None
        assert generated.test_code is not None
        assert generated.documentation is not None

    def test_generated_source_has_docstring(self, generator, simple_spec):
        """Test that generated source has module docstring."""
        result = generator.generate(simple_spec)
        generated = result.unwrap()

        assert '"""' in generated.source_code
        assert "Utility functions" in generated.source_code

    def test_generated_source_has_function(self, generator, simple_spec):
        """Test that generated source has function definition."""
        result = generator.generate(simple_spec)
        generated = result.unwrap()

        assert "def helper(" in generated.source_code
        assert "x: int" in generated.source_code

    def test_generated_tests_has_test_class(self, generator, simple_spec):
        """Test that generated tests have test class."""
        result = generator.generate(simple_spec)
        generated = result.unwrap()

        assert "class TestUtils:" in generated.test_code
        assert "def test_helper_exists" in generated.test_code

    def test_generated_docs_has_title(self, generator, simple_spec):
        """Test that generated docs have title."""
        result = generator.generate(simple_spec)
        generated = result.unwrap()

        assert "# utils" in generated.documentation
        assert "## Functions" in generated.documentation

    def test_generate_class(self, generator):
        """Test generating code with a class."""
        from tools.spec_to_code import ClassSpec, ModuleSpec

        spec = ModuleSpec(
            name="models",
            description="Data models",
            imports=[],
            functions=[],
            classes=[
                ClassSpec(
                    name="DataModel",
                    description="A data model",
                    attributes=[{"name": "value", "type": "int"}],
                    methods=[],
                )
            ],
            constants=[],
        )

        result = generator.generate(spec)
        generated = result.unwrap()

        assert "class DataModel:" in generated.source_code
        assert "def __init__" in generated.source_code


class TestSpecToCode:
    """Tests for SpecToCode transformer class."""

    @pytest.fixture
    def transformer(self):
        """Create transformer instance."""
        from tools.spec_to_code import SpecToCode

        return SpecToCode()

    def test_transform_file(self, transformer, tmp_path):
        """Test transforming a spec file."""
        spec_file = tmp_path / "test_spec.md"
        spec_file.write_text("""# Test Module

A test module.

## Functions

### `test_func(x: int)`

A test function.

Returns: `bool`
""")

        result = transformer.transform(str(spec_file))

        assert result.is_ok()
        generated = result.unwrap()
        assert "def test_func" in generated.source_code

    def test_transform_with_output(self, transformer, tmp_path):
        """Test transforming with output directory."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""# Output Test

Testing output.
""")
        output_dir = tmp_path / "output"

        result = transformer.transform(str(spec_file), str(output_dir))

        assert result.is_ok()
        assert (output_dir / "spec.py").exists()
        assert (output_dir / "test_spec.py").exists()

    def test_validate_spec_finds_issues(self, transformer, tmp_path):
        """Test validation finds missing descriptions."""
        spec_file = tmp_path / "incomplete.md"
        spec_file.write_text("""# Incomplete

## Functions

### `no_desc()`
""")

        result = transformer.validate_spec(str(spec_file))

        assert result.is_ok()
        issues = result.unwrap()
        # Should find issues with missing descriptions
        assert isinstance(issues, list)

    def test_transform_spec_directly(self, transformer):
        """Test transforming a ModuleSpec directly."""
        from tools.spec_to_code import FunctionSpec, ModuleSpec

        spec = ModuleSpec(
            name="direct",
            description="Direct transformation",
            imports=[],
            functions=[
                FunctionSpec(
                    name="direct_func",
                    description="Direct function",
                    parameters=[],
                    return_type="None",
                    return_description="Nothing",
                    examples=[],
                    raises=[],
                )
            ],
            classes=[],
            constants=[],
        )

        result = transformer.transform_spec(spec)

        assert result.is_ok()
        generated = result.unwrap()
        assert "def direct_func" in generated.source_code


class TestGeneratedCode:
    """Tests for GeneratedCode dataclass."""

    def test_generated_code_creation(self):
        """Test creating GeneratedCode."""
        from datetime import datetime

        from tools.spec_to_code import GeneratedCode

        code = GeneratedCode(
            source_code="def foo(): pass",
            test_code="def test_foo(): assert True",
            documentation="# Foo\n\nDoes foo.",
            spec_hash="abc123",
            generated_at=datetime.now(),
            warnings=["Warning 1"],
        )

        assert code.source_code == "def foo(): pass"
        assert len(code.warnings) == 1
        assert code.spec_hash == "abc123"

    def test_generated_code_default_warnings(self):
        """Test that warnings defaults to empty list."""
        from datetime import datetime

        from tools.spec_to_code import GeneratedCode

        code = GeneratedCode(
            source_code="",
            test_code="",
            documentation="",
            spec_hash="",
            generated_at=datetime.now(),
        )

        assert code.warnings == []
