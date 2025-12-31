"""
Spec to Code Generator - Transform specifications into implementation.

Converts formal specifications (spec.md) into executable code with:
- Function signature generation
- Type inference from spec
- Test scaffolding
- Documentation generation

Constitutional Compliance:
- Article V: Spec-Driven Development (spec → plan → code)
- Article VI: TDD (generates tests before implementation)
"""

import ast
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


@dataclass
class FunctionSpec:
    """Specification for a function to generate."""

    name: str
    description: str
    parameters: list[dict]  # [{name, type, description, default?}]
    return_type: str
    return_description: str
    examples: list[dict]  # [{input, expected_output}]
    raises: list[dict]  # [{exception, condition}]
    tags: list[str] = field(default_factory=list)


@dataclass
class ClassSpec:
    """Specification for a class to generate."""

    name: str
    description: str
    attributes: list[dict]  # [{name, type, description, default?}]
    methods: list[FunctionSpec]
    parent_classes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ModuleSpec:
    """Specification for a module to generate."""

    name: str
    description: str
    imports: list[str]
    functions: list[FunctionSpec]
    classes: list[ClassSpec]
    constants: list[dict]  # [{name, type, value, description}]
    file_path: str = ""


@dataclass
class GeneratedCode:
    """Generated code from specification."""

    source_code: str
    test_code: str
    documentation: str
    spec_hash: str
    generated_at: datetime
    warnings: list[str] = field(default_factory=list)


class SpecParser:
    """Parse specification markdown files."""

    def parse_spec_file(self, spec_path: str) -> Result[ModuleSpec, str]:
        """
        Parse a specification file.

        Args:
            spec_path: Path to spec.md file

        Returns:
            Result containing ModuleSpec or error
        """
        try:
            path = Path(spec_path)
            if not path.exists():
                return Err(f"Spec file not found: {spec_path}")

            content = path.read_text()
            return self.parse_spec_content(content, path.stem)

        except Exception as e:
            return Err(f"Failed to parse spec: {e}")

    def parse_spec_content(self, content: str, module_name: str) -> Result[ModuleSpec, str]:
        """
        Parse specification content.

        Args:
            content: Markdown content
            module_name: Name for the module

        Returns:
            Result containing ModuleSpec
        """
        try:
            # Extract sections
            sections = self._extract_sections(content)

            # Parse description
            description = sections.get("description", sections.get("overview", ""))

            # Parse functions
            functions = self._parse_functions(sections.get("functions", ""))

            # Parse classes
            classes = self._parse_classes(sections.get("classes", ""))

            # Parse imports
            imports = self._parse_imports(sections.get("imports", sections.get("dependencies", "")))

            # Parse constants
            constants = self._parse_constants(sections.get("constants", ""))

            return Ok(ModuleSpec(
                name=module_name,
                description=description.strip(),
                imports=imports,
                functions=functions,
                classes=classes,
                constants=constants,
            ))

        except Exception as e:
            return Err(f"Failed to parse spec content: {e}")

    def _extract_sections(self, content: str) -> dict[str, str]:
        """Extract sections from markdown."""
        sections = {}
        current_section = "description"
        current_content = []

        for line in content.split("\n"):
            # Check for section header
            if line.startswith("## "):
                # Save previous section
                sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip().lower().replace(" ", "_")
                current_content = []
            elif line.startswith("# "):
                # Title - add to description
                if current_section == "description":
                    current_content.append(line[2:].strip())
            else:
                current_content.append(line)

        # Save last section
        sections[current_section] = "\n".join(current_content)

        return sections

    def _parse_functions(self, content: str) -> list[FunctionSpec]:
        """Parse function specifications."""
        functions = []

        # Look for function definitions in markdown
        func_pattern = r"###\s+`?(\w+)`?\s*\((.*?)\)"
        matches = re.finditer(func_pattern, content, re.MULTILINE)

        for match in matches:
            name = match.group(1)
            params_str = match.group(2)

            # Extract description (text after the header until next header)
            start = match.end()
            end_match = re.search(r"\n###\s+", content[start:])
            end = start + end_match.start() if end_match else len(content)
            description = content[start:end].strip()

            # Parse parameters
            parameters = self._parse_parameters(params_str, description)

            # Parse return type
            return_match = re.search(r"Returns?:\s*`?(\w+(?:\[.*?\])?)`?", description)
            return_type = return_match.group(1) if return_match else "None"

            # Parse examples
            examples = self._parse_examples(description)

            functions.append(FunctionSpec(
                name=name,
                description=description.split("\n")[0] if description else "",
                parameters=parameters,
                return_type=return_type,
                return_description="",
                examples=examples,
                raises=[],
            ))

        return functions

    def _parse_parameters(self, params_str: str, description: str) -> list[dict]:
        """Parse function parameters."""
        parameters = []

        if not params_str.strip():
            return parameters

        # Simple parameter parsing
        for param in params_str.split(","):
            param = param.strip()
            if not param:
                continue

            # Handle type annotations
            if ":" in param:
                name, type_hint = param.split(":", 1)
                name = name.strip()
                type_hint = type_hint.strip()

                # Handle default values
                if "=" in type_hint:
                    type_hint, default = type_hint.split("=", 1)
                    default = default.strip()
                else:
                    default = None
            else:
                name = param
                type_hint = "Any"
                default = None

            parameters.append({
                "name": name,
                "type": type_hint,
                "description": "",
                "default": default,
            })

        return parameters

    def _parse_examples(self, description: str) -> list[dict]:
        """Parse examples from description."""
        examples = []

        # Look for code blocks
        code_blocks = re.findall(r"```(?:python)?\n(.*?)```", description, re.DOTALL)

        for block in code_blocks:
            # Try to extract input/output pairs
            lines = block.strip().split("\n")
            for i, line in enumerate(lines):
                if ">>>" in line:
                    input_code = line.replace(">>>", "").strip()
                    # Next line might be output
                    if i + 1 < len(lines) and not lines[i + 1].startswith(">>>"):
                        output = lines[i + 1].strip()
                        examples.append({
                            "input": input_code,
                            "expected_output": output,
                        })

        return examples

    def _parse_classes(self, content: str) -> list[ClassSpec]:
        """Parse class specifications."""
        classes = []

        # Look for class definitions
        class_pattern = r"###\s+`?class\s+(\w+)`?"
        matches = re.finditer(class_pattern, content, re.MULTILINE | re.IGNORECASE)

        for match in matches:
            name = match.group(1)

            # Extract class content
            start = match.end()
            end_match = re.search(r"\n###\s+class", content[start:], re.IGNORECASE)
            end = start + end_match.start() if end_match else len(content)
            class_content = content[start:end]

            # Parse attributes
            attributes = self._parse_attributes(class_content)

            # Parse methods (reuse function parsing)
            methods = self._parse_functions(class_content)

            classes.append(ClassSpec(
                name=name,
                description=class_content.split("\n")[0].strip() if class_content else "",
                attributes=attributes,
                methods=methods,
            ))

        return classes

    def _parse_attributes(self, content: str) -> list[dict]:
        """Parse class attributes."""
        attributes = []

        # Look for attribute definitions
        attr_pattern = r"-\s+`?(\w+)`?\s*:\s*`?(\w+(?:\[.*?\])?)`?"
        matches = re.finditer(attr_pattern, content)

        for match in matches:
            attributes.append({
                "name": match.group(1),
                "type": match.group(2),
                "description": "",
            })

        return attributes

    def _parse_imports(self, content: str) -> list[str]:
        """Parse import statements."""
        imports = []

        # Look for import-like patterns
        import_pattern = r"(?:from\s+\S+\s+)?import\s+\S+"
        matches = re.findall(import_pattern, content)
        imports.extend(matches)

        # Also look for dependency lists
        dep_pattern = r"-\s+`?(\w+(?:\.\w+)*)`?"
        for match in re.finditer(dep_pattern, content):
            dep = match.group(1)
            if "." in dep:
                imports.append(f"import {dep}")

        return imports

    def _parse_constants(self, content: str) -> list[dict]:
        """Parse constants."""
        constants = []

        # Look for constant definitions
        const_pattern = r"`?([A-Z_][A-Z0-9_]*)`?\s*=\s*(.+)"
        matches = re.finditer(const_pattern, content)

        for match in matches:
            constants.append({
                "name": match.group(1),
                "value": match.group(2).strip(),
                "type": "Any",
                "description": "",
            })

        return constants


class CodeGenerator:
    """Generate code from specifications."""

    def generate(self, spec: ModuleSpec) -> Result[GeneratedCode, str]:
        """
        Generate code from a module specification.

        Args:
            spec: Module specification

        Returns:
            Result containing generated code
        """
        try:
            warnings = []

            # Generate source code
            source_code = self._generate_source(spec)

            # Generate test code
            test_code = self._generate_tests(spec)

            # Generate documentation
            documentation = self._generate_docs(spec)

            # Calculate spec hash
            import hashlib
            spec_hash = hashlib.md5(str(spec).encode()).hexdigest()[:8]

            return Ok(GeneratedCode(
                source_code=source_code,
                test_code=test_code,
                documentation=documentation,
                spec_hash=spec_hash,
                generated_at=datetime.now(),
                warnings=warnings,
            ))

        except Exception as e:
            return Err(f"Failed to generate code: {e}")

    def _generate_source(self, spec: ModuleSpec) -> str:
        """Generate source code."""
        lines = []

        # Module docstring
        lines.append(f'"""')
        lines.append(spec.description or f"{spec.name} module.")
        lines.append("")
        lines.append("Generated from specification.")
        lines.append('"""')
        lines.append("")

        # Imports
        lines.append("from typing import Any, Optional")
        for imp in spec.imports:
            lines.append(imp)
        lines.append("")

        # Constants
        for const in spec.constants:
            lines.append(f"{const['name']} = {const['value']}")
        if spec.constants:
            lines.append("")

        # Classes
        for cls in spec.classes:
            lines.extend(self._generate_class(cls))
            lines.append("")

        # Functions
        for func in spec.functions:
            lines.extend(self._generate_function(func))
            lines.append("")

        return "\n".join(lines)

    def _generate_function(self, func: FunctionSpec, indent: str = "") -> list[str]:
        """Generate a function."""
        lines = []

        # Signature
        params = []
        for param in func.parameters:
            param_str = param["name"]
            if param.get("type"):
                param_str += f": {param['type']}"
            if param.get("default") is not None:
                param_str += f" = {param['default']}"
            params.append(param_str)

        params_str = ", ".join(params)
        return_type = f" -> {func.return_type}" if func.return_type else ""

        lines.append(f"{indent}def {func.name}({params_str}){return_type}:")

        # Docstring
        lines.append(f'{indent}    """')
        lines.append(f"{indent}    {func.description}")
        if func.parameters:
            lines.append(f"{indent}")
            lines.append(f"{indent}    Args:")
            for param in func.parameters:
                lines.append(f"{indent}        {param['name']}: {param.get('description', 'Parameter')}")
        if func.return_type and func.return_type != "None":
            lines.append(f"{indent}")
            lines.append(f"{indent}    Returns:")
            lines.append(f"{indent}        {func.return_description or func.return_type}")
        lines.append(f'{indent}    """')

        # Placeholder implementation
        lines.append(f"{indent}    # TODO: Implement {func.name}")
        if func.return_type == "None":
            lines.append(f"{indent}    pass")
        elif func.return_type == "bool":
            lines.append(f"{indent}    return False")
        elif func.return_type in ("int", "float"):
            lines.append(f"{indent}    return 0")
        elif func.return_type == "str":
            lines.append(f'{indent}    return ""')
        elif func.return_type.startswith("list"):
            lines.append(f"{indent}    return []")
        elif func.return_type.startswith("dict"):
            lines.append(f"{indent}    return {{}}")
        else:
            lines.append(f"{indent}    raise NotImplementedError")

        return lines

    def _generate_class(self, cls: ClassSpec) -> list[str]:
        """Generate a class."""
        lines = []

        # Class definition
        parent_str = f"({', '.join(cls.parent_classes)})" if cls.parent_classes else ""
        lines.append(f"class {cls.name}{parent_str}:")

        # Docstring
        lines.append(f'    """')
        lines.append(f"    {cls.description}")
        lines.append(f'    """')
        lines.append("")

        # __init__ if attributes exist
        if cls.attributes:
            init_params = ["self"]
            for attr in cls.attributes:
                param = attr["name"]
                if attr.get("type"):
                    param += f": {attr['type']}"
                if attr.get("default") is not None:
                    param += f" = {attr['default']}"
                init_params.append(param)

            lines.append(f"    def __init__({', '.join(init_params)}):")
            lines.append(f'        """Initialize {cls.name}."""')
            for attr in cls.attributes:
                lines.append(f"        self.{attr['name']} = {attr['name']}")
            lines.append("")

        # Methods
        for method in cls.methods:
            # Add self parameter if not present
            if not method.parameters or method.parameters[0]["name"] != "self":
                method.parameters.insert(0, {"name": "self", "type": None})
            lines.extend(self._generate_function(method, indent="    "))
            lines.append("")

        return lines

    def _generate_tests(self, spec: ModuleSpec) -> str:
        """Generate test code."""
        lines = []

        # Test file header
        lines.append(f'"""')
        lines.append(f"Tests for {spec.name}.")
        lines.append("")
        lines.append("Generated from specification.")
        lines.append('"""')
        lines.append("")
        lines.append("import pytest")
        lines.append(f"from {spec.name} import *")
        lines.append("")

        # Test class
        class_name = "".join(word.capitalize() for word in spec.name.split("_"))
        lines.append(f"class Test{class_name}:")
        lines.append(f'    """Tests for {spec.name} module."""')
        lines.append("")

        # Tests for functions
        for func in spec.functions:
            lines.extend(self._generate_function_test(func))
            lines.append("")

        # Tests for classes
        for cls in spec.classes:
            lines.extend(self._generate_class_tests(cls))
            lines.append("")

        return "\n".join(lines)

    def _generate_function_test(self, func: FunctionSpec) -> list[str]:
        """Generate test for a function."""
        lines = []

        lines.append(f"    def test_{func.name}_exists(self):")
        lines.append(f'        """Test that {func.name} exists."""')
        lines.append(f"        assert callable({func.name})")
        lines.append("")

        # Generate tests from examples
        for i, example in enumerate(func.examples):
            lines.append(f"    def test_{func.name}_example_{i + 1}(self):")
            lines.append(f'        """Test {func.name} with example input."""')
            lines.append(f"        result = {example['input']}")
            lines.append(f"        assert result == {example['expected_output']}")
            lines.append("")

        return lines

    def _generate_class_tests(self, cls: ClassSpec) -> list[str]:
        """Generate tests for a class."""
        lines = []

        lines.append(f"    def test_{cls.name.lower()}_instantiation(self):")
        lines.append(f'        """Test that {cls.name} can be instantiated."""')

        # Generate constructor call
        if cls.attributes:
            args = ", ".join(f"{attr['name']}=None" for attr in cls.attributes)
            lines.append(f"        obj = {cls.name}({args})")
        else:
            lines.append(f"        obj = {cls.name}()")

        lines.append(f"        assert obj is not None")

        return lines

    def _generate_docs(self, spec: ModuleSpec) -> str:
        """Generate documentation."""
        lines = []

        lines.append(f"# {spec.name}")
        lines.append("")
        lines.append(spec.description)
        lines.append("")

        if spec.functions:
            lines.append("## Functions")
            lines.append("")
            for func in spec.functions:
                lines.append(f"### `{func.name}`")
                lines.append("")
                lines.append(func.description)
                lines.append("")

        if spec.classes:
            lines.append("## Classes")
            lines.append("")
            for cls in spec.classes:
                lines.append(f"### `{cls.name}`")
                lines.append("")
                lines.append(cls.description)
                lines.append("")

        return "\n".join(lines)


class SpecToCode:
    """
    High-level interface for spec-to-code transformation.

    Combines parsing and generation with validation.
    """

    def __init__(self):
        """Initialize spec to code transformer."""
        self.parser = SpecParser()
        self.generator = CodeGenerator()

    def transform(self, spec_path: str, output_dir: Optional[str] = None) -> Result[GeneratedCode, str]:
        """
        Transform a specification file into code.

        Args:
            spec_path: Path to specification file
            output_dir: Optional output directory

        Returns:
            Result containing generated code
        """
        # Parse specification
        parse_result = self.parser.parse_spec_file(spec_path)
        if parse_result.is_err():
            return Err(parse_result.unwrap_err())

        spec = parse_result.unwrap()

        # Generate code
        gen_result = self.generator.generate(spec)
        if gen_result.is_err():
            return Err(gen_result.unwrap_err())

        generated = gen_result.unwrap()

        # Write files if output directory specified
        if output_dir:
            self._write_output(spec, generated, output_dir)

        return Ok(generated)

    def transform_spec(self, spec: ModuleSpec, output_dir: Optional[str] = None) -> Result[GeneratedCode, str]:
        """
        Transform a ModuleSpec directly into code.

        Args:
            spec: Module specification
            output_dir: Optional output directory

        Returns:
            Result containing generated code
        """
        # Generate code
        gen_result = self.generator.generate(spec)
        if gen_result.is_err():
            return Err(gen_result.unwrap_err())

        generated = gen_result.unwrap()

        # Write files if output directory specified
        if output_dir:
            self._write_output(spec, generated, output_dir)

        return Ok(generated)

    def _write_output(self, spec: ModuleSpec, generated: GeneratedCode, output_dir: str) -> None:
        """Write generated code to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write source
        source_file = output_path / f"{spec.name}.py"
        source_file.write_text(generated.source_code)

        # Write tests
        test_file = output_path / f"test_{spec.name}.py"
        test_file.write_text(generated.test_code)

        # Write docs
        doc_file = output_path / f"{spec.name}.md"
        doc_file.write_text(generated.documentation)

    def validate_spec(self, spec_path: str) -> Result[list[str], str]:
        """
        Validate a specification file.

        Args:
            spec_path: Path to specification

        Returns:
            Result containing list of warnings/errors
        """
        parse_result = self.parser.parse_spec_file(spec_path)
        if parse_result.is_err():
            return Err(parse_result.unwrap_err())

        spec = parse_result.unwrap()
        issues = []

        # Check for missing descriptions
        if not spec.description:
            issues.append("Missing module description")

        for func in spec.functions:
            if not func.description:
                issues.append(f"Function {func.name} missing description")
            if not func.return_type:
                issues.append(f"Function {func.name} missing return type")

        for cls in spec.classes:
            if not cls.description:
                issues.append(f"Class {cls.name} missing description")

        return Ok(issues)


def main():
    """Command-line interface for spec to code."""
    import argparse

    parser = argparse.ArgumentParser(description="Transform specs to code")
    parser.add_argument("spec", help="Path to specification file")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--validate", action="store_true", help="Validate only")
    parser.add_argument("--preview", action="store_true", help="Preview generated code")
    args = parser.parse_args()

    transformer = SpecToCode()

    if args.validate:
        result = transformer.validate_spec(args.spec)
        if result.is_ok():
            issues = result.unwrap()
            if issues:
                print("Validation issues:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("✅ Specification is valid")
        else:
            print(f"Error: {result.unwrap_err()}")
        return

    result = transformer.transform(args.spec, args.output)

    if result.is_ok():
        generated = result.unwrap()
        if args.preview:
            print("=== Source Code ===")
            print(generated.source_code)
            print("\n=== Test Code ===")
            print(generated.test_code)
        elif args.output:
            print(f"✅ Generated code written to {args.output}")
        else:
            print(generated.source_code)
    else:
        print(f"Error: {result.unwrap_err()}")


if __name__ == "__main__":
    main()
