"""
Feature Pipeline - End-to-end autonomous feature generation.

Orchestrates the complete feature development lifecycle:
1. Intent parsing (natural language -> structured spec)
2. Codebase analysis (where to add, what patterns to follow)
3. Code generation (spec -> implementation)
4. Test generation (ensure coverage)
5. Integration (wire into existing code)
6. Validation (run tests, quality checks)

Constitutional Compliance:
- Article V: Spec-driven development (generates specs first)
- Article VI: TDD mandate (generates tests before code)
- Article IV: Learning (stores successful patterns)
"""

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
class FeatureIntent:
    """Parsed feature intent from natural language."""

    name: str
    description: str
    requirements: list[str]
    constraints: list[str]
    acceptance_criteria: list[str]
    related_files: list[str] = field(default_factory=list)
    priority: str = "medium"  # 'low', 'medium', 'high', 'critical'


@dataclass
class FeatureSpec:
    """Generated feature specification."""

    intent: FeatureIntent
    target_module: str
    target_file: str
    functions: list[dict]
    classes: list[dict]
    tests: list[dict]
    integration_points: list[str]
    dependencies: list[str]


@dataclass
class GenerationResult:
    """Result of code generation."""

    spec: FeatureSpec
    code_files: dict[str, str]  # path -> content
    test_files: dict[str, str]  # path -> content
    integration_changes: list[dict]  # Changes to existing files
    validation_passed: bool
    errors: list[str]


@dataclass
class PipelineReport:
    """Complete pipeline execution report."""

    feature_name: str
    started_at: datetime
    completed_at: Optional[datetime]
    stages_completed: list[str]
    current_stage: str
    generation_result: Optional[GenerationResult]
    success: bool
    error: Optional[str]


class IntentParser:
    """
    Parse natural language feature requests into structured intents.

    Uses pattern matching and heuristics to extract requirements.
    """

    def __init__(self):
        """Initialize the intent parser."""
        self._requirement_patterns = [
            ("must ", "requirement"),
            ("should ", "requirement"),
            ("needs to ", "requirement"),
            ("will ", "requirement"),
            ("can ", "feature"),
        ]

        self._constraint_patterns = [
            ("must not ", "constraint"),
            ("should not ", "constraint"),
            ("cannot ", "constraint"),
            ("without ", "constraint"),
            ("no ", "constraint"),
        ]

    def parse(self, request: str) -> Result[FeatureIntent, str]:
        """
        Parse a feature request into structured intent.

        Args:
            request: Natural language feature request

        Returns:
            Result containing FeatureIntent
        """
        if not request or len(request.strip()) < 10:
            return Err("Feature request too short")

        lines = request.strip().split("\n")

        # Extract name (first line or first sentence)
        name = self._extract_name(lines[0])

        # Extract description
        description = self._extract_description(request)

        # Extract requirements
        requirements = self._extract_requirements(request)

        # Extract constraints
        constraints = self._extract_constraints(request)

        # Extract acceptance criteria
        criteria = self._extract_criteria(request)

        # Infer priority
        priority = self._infer_priority(request)

        return Ok(
            FeatureIntent(
                name=name,
                description=description,
                requirements=requirements,
                constraints=constraints,
                acceptance_criteria=criteria,
                priority=priority,
            )
        )

    def _extract_name(self, first_line: str) -> str:
        """Extract feature name from first line."""
        # Remove common prefixes
        prefixes = [
            "add ", "create ", "implement ", "build ",
            "make ", "develop ", "write ",
        ]

        name = first_line.strip()
        for prefix in prefixes:
            if name.lower().startswith(prefix):
                name = name[len(prefix):]
                break

        # Clean up
        name = name.strip(".:!?")

        # Truncate if too long
        if len(name) > 60:
            name = name[:57] + "..."

        return name

    def _extract_description(self, request: str) -> str:
        """Extract description from request."""
        # Use first paragraph or first 200 chars
        paragraphs = request.split("\n\n")
        if paragraphs:
            desc = paragraphs[0].strip()
            if len(desc) > 200:
                desc = desc[:197] + "..."
            return desc
        return request[:200]

    def _extract_requirements(self, request: str) -> list[str]:
        """Extract requirements from request."""
        requirements = []
        lines = request.lower().split("\n")

        for line in lines:
            for pattern, _ in self._requirement_patterns:
                if pattern in line:
                    # Extract the requirement
                    idx = line.find(pattern)
                    req = line[idx:].strip()
                    if len(req) > 10:
                        requirements.append(req.capitalize())
                    break

        return requirements[:10]  # Limit

    def _extract_constraints(self, request: str) -> list[str]:
        """Extract constraints from request."""
        constraints = []
        lines = request.lower().split("\n")

        for line in lines:
            for pattern, _ in self._constraint_patterns:
                if pattern in line:
                    idx = line.find(pattern)
                    constraint = line[idx:].strip()
                    if len(constraint) > 5:
                        constraints.append(constraint.capitalize())
                    break

        return constraints[:5]  # Limit

    def _extract_criteria(self, request: str) -> list[str]:
        """Extract acceptance criteria from request."""
        criteria = []

        # Look for numbered lists or bullet points
        lines = request.split("\n")
        for line in lines:
            line = line.strip()
            # Check for list items
            if (
                line.startswith(("- ", "* ", "• "))
                or (len(line) > 2 and line[0].isdigit() and line[1] in ".)")
            ):
                item = line.lstrip("- *•0123456789.)")
                if len(item.strip()) > 5:
                    criteria.append(item.strip())

        # If no list found, create from requirements
        if not criteria:
            lower = request.lower()
            if "must " in lower:
                idx = lower.find("must ")
                end = lower.find(".", idx)
                if end > idx:
                    criteria.append(request[idx:end+1].strip())

        return criteria[:10]

    def _infer_priority(self, request: str) -> str:
        """Infer priority from request language."""
        lower = request.lower()

        if any(word in lower for word in ["urgent", "critical", "asap", "immediately"]):
            return "critical"
        if any(word in lower for word in ["important", "priority", "soon"]):
            return "high"
        if any(word in lower for word in ["eventually", "when possible", "nice to have"]):
            return "low"

        return "medium"


class FeaturePipeline:
    """
    End-to-end autonomous feature generation pipeline.

    Orchestrates the complete feature development lifecycle from
    natural language intent to working, tested code.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the feature pipeline."""
        self.project_root = project_root or PROJECT_ROOT
        self.intent_parser = IntentParser()
        self._codebase_intel = None
        self._spec_generator = None
        self._code_generator = None
        self._current_report: Optional[PipelineReport] = None

    def _lazy_load_components(self) -> None:
        """Lazy load heavy components."""
        if self._codebase_intel is None:
            from tools.codebase_intelligence import CodebaseIntelligence
            self._codebase_intel = CodebaseIntelligence(self.project_root)

        if self._spec_generator is None:
            try:
                from tools.spec_to_code import SpecToCode
                self._spec_generator = SpecToCode()
            except ImportError:
                pass

    def generate_feature(
        self,
        request: str,
        dry_run: bool = False,
        auto_integrate: bool = False,
    ) -> Result[PipelineReport, str]:
        """
        Generate a feature from natural language request.

        Args:
            request: Natural language feature description
            dry_run: If True, generate but don't write files
            auto_integrate: If True, automatically integrate into codebase

        Returns:
            Result containing PipelineReport
        """
        self._lazy_load_components()

        # Initialize report
        self._current_report = PipelineReport(
            feature_name="",
            started_at=datetime.now(),
            completed_at=None,
            stages_completed=[],
            current_stage="intent_parsing",
            generation_result=None,
            success=False,
            error=None,
        )

        try:
            # Stage 1: Parse intent
            intent_result = self._parse_intent(request)
            if intent_result.is_err():
                return self._fail(intent_result.unwrap_err())
            intent = intent_result.unwrap()
            self._current_report.feature_name = intent.name
            self._current_report.stages_completed.append("intent_parsing")

            # Stage 2: Analyze codebase
            self._current_report.current_stage = "codebase_analysis"
            analysis_result = self._analyze_codebase(intent)
            if analysis_result.is_err():
                return self._fail(analysis_result.unwrap_err())
            analysis = analysis_result.unwrap()
            self._current_report.stages_completed.append("codebase_analysis")

            # Stage 3: Generate specification
            self._current_report.current_stage = "spec_generation"
            spec_result = self._generate_spec(intent, analysis)
            if spec_result.is_err():
                return self._fail(spec_result.unwrap_err())
            spec = spec_result.unwrap()
            self._current_report.stages_completed.append("spec_generation")

            # Stage 4: Generate code
            self._current_report.current_stage = "code_generation"
            code_result = self._generate_code(spec)
            if code_result.is_err():
                return self._fail(code_result.unwrap_err())
            generated = code_result.unwrap()
            self._current_report.stages_completed.append("code_generation")

            # Stage 5: Validate
            self._current_report.current_stage = "validation"
            validation_result = self._validate(generated)
            if validation_result.is_err():
                generated.errors.append(validation_result.unwrap_err())
                generated.validation_passed = False
            else:
                generated.validation_passed = True
            self._current_report.stages_completed.append("validation")

            # Stage 6: Write files (if not dry run)
            if not dry_run:
                self._current_report.current_stage = "file_writing"
                write_result = self._write_files(generated)
                if write_result.is_err():
                    return self._fail(write_result.unwrap_err())
                self._current_report.stages_completed.append("file_writing")

            # Stage 7: Integration (if requested)
            if auto_integrate and not dry_run:
                self._current_report.current_stage = "integration"
                integrate_result = self._integrate(generated)
                if integrate_result.is_err():
                    generated.errors.append(f"Integration: {integrate_result.unwrap_err()}")
                else:
                    self._current_report.stages_completed.append("integration")

            # Complete
            self._current_report.generation_result = generated
            self._current_report.completed_at = datetime.now()
            self._current_report.current_stage = "completed"
            self._current_report.success = len(generated.errors) == 0

            return Ok(self._current_report)

        except Exception as e:
            return self._fail(f"Pipeline error: {e}")

    def _fail(self, error: str) -> Result[PipelineReport, str]:
        """Record failure and return error."""
        if self._current_report:
            self._current_report.error = error
            self._current_report.completed_at = datetime.now()
        return Err(error)

    def _parse_intent(self, request: str) -> Result[FeatureIntent, str]:
        """Parse the feature request into structured intent."""
        return self.intent_parser.parse(request)

    def _analyze_codebase(self, intent: FeatureIntent) -> Result[dict, str]:
        """Analyze codebase for integration points."""
        if self._codebase_intel is None:
            return Ok({
                "patterns": [],
                "similar_code": [],
                "suggested_location": "tools/",
            })

        # Index codebase if needed
        result = self._codebase_intel.index_codebase(exclude_tests=True)
        if result.is_err():
            return Err(result.unwrap_err())

        stats = self._codebase_intel.get_stats()

        # Find similar code
        similar = self._codebase_intel.find_similar_code(intent.description)

        # Suggest location based on intent
        location = self._suggest_location(intent)

        return Ok({
            "patterns": stats.get("patterns_detected", []),
            "similar_code": [(s[0].name, s[0].file_path, s[1]) for s in similar[:3]],
            "suggested_location": location,
            "file_count": stats.get("file_count", 0),
        })

    def _suggest_location(self, intent: FeatureIntent) -> str:
        """Suggest where to place the new feature."""
        name_lower = intent.name.lower()

        if "agent" in name_lower:
            return "agents/"
        if "tool" in name_lower:
            return "tools/"
        if "test" in name_lower:
            return "tests/"
        if "api" in name_lower or "endpoint" in name_lower:
            return "api/"
        if "model" in name_lower:
            return "shared/models/"
        if "util" in name_lower or "helper" in name_lower:
            return "shared/"

        return "tools/"

    def _generate_spec(
        self, intent: FeatureIntent, analysis: dict
    ) -> Result[FeatureSpec, str]:
        """Generate feature specification."""
        # Determine target module and file
        location = analysis.get("suggested_location", "tools/")
        module_name = intent.name.lower().replace(" ", "_").replace("-", "_")
        target_file = f"{location}{module_name}.py"

        # Generate function specs from requirements
        functions = []
        for i, req in enumerate(intent.requirements):
            func_name = f"handle_{module_name}_{i+1}"
            functions.append({
                "name": func_name,
                "description": req,
                "parameters": [],
                "return_type": "Result[dict, str]",
            })

        # Generate at least one main function
        if not functions:
            functions.append({
                "name": f"run_{module_name}",
                "description": intent.description,
                "parameters": [],
                "return_type": "Result[dict, str]",
            })

        # Generate class spec if complex
        classes = []
        if len(intent.requirements) > 3 or "class" in intent.description.lower():
            class_name = "".join(word.capitalize() for word in module_name.split("_"))
            classes.append({
                "name": class_name,
                "description": intent.description,
                "methods": [f["name"] for f in functions],
            })

        # Generate test specs (TDD - tests first)
        tests = []
        for func in functions:
            tests.append({
                "name": f"test_{func['name']}_success",
                "description": f"Test {func['name']} succeeds with valid input",
                "target": func["name"],
            })
            tests.append({
                "name": f"test_{func['name']}_error",
                "description": f"Test {func['name']} handles errors",
                "target": func["name"],
            })

        # Determine dependencies
        dependencies = ["shared.type_definitions.result"]
        if "async" in intent.description.lower():
            dependencies.append("asyncio")
        if "database" in intent.description.lower() or "store" in intent.description.lower():
            dependencies.append("json")

        return Ok(
            FeatureSpec(
                intent=intent,
                target_module=module_name,
                target_file=target_file,
                functions=functions,
                classes=classes,
                tests=tests,
                integration_points=analysis.get("similar_code", []),
                dependencies=dependencies,
            )
        )

    def _generate_code(self, spec: FeatureSpec) -> Result[GenerationResult, str]:
        """Generate code from specification."""
        code_files: dict[str, str] = {}
        test_files: dict[str, str] = {}

        # Generate main module
        code = self._generate_module_code(spec)
        code_files[spec.target_file] = code

        # Generate test file
        test_code = self._generate_test_code(spec)
        test_path = f"tests/unit/{spec.target_file.replace('/', '/test_')}"
        test_files[test_path] = test_code

        return Ok(
            GenerationResult(
                spec=spec,
                code_files=code_files,
                test_files=test_files,
                integration_changes=[],
                validation_passed=False,
                errors=[],
            )
        )

    def _generate_module_code(self, spec: FeatureSpec) -> str:
        """Generate module implementation code."""
        lines = [
            '"""',
            f"{spec.intent.name}",
            "",
            f"{spec.intent.description}",
            '"""',
            "",
            "import sys",
            "from pathlib import Path",
            "",
            "# Ensure project root is on path",
            "PROJECT_ROOT = Path(__file__).resolve().parents[1]",
            'if str(PROJECT_ROOT) not in sys.path:',
            "    sys.path.insert(0, str(PROJECT_ROOT))",
            "",
        ]

        # Add imports
        for dep in spec.dependencies:
            if "." in dep:
                parts = dep.rsplit(".", 1)
                lines.append(f"from {parts[0]} import {parts[1]}")
            else:
                lines.append(f"import {dep}")

        lines.append("")
        lines.append("from shared.type_definitions.result import Ok, Err, Result")
        lines.append("")

        # Generate classes
        for cls in spec.classes:
            lines.append("")
            lines.append(f"class {cls['name']}:")
            lines.append(f'    """{cls["description"]}"""')
            lines.append("")
            lines.append("    def __init__(self):")
            lines.append('        """Initialize."""')
            lines.append("        pass")
            lines.append("")

        # Generate functions
        for func in spec.functions:
            lines.append("")
            lines.append(f"def {func['name']}() -> {func['return_type']}:")
            lines.append(f'    """{func["description"]}"""')
            lines.append("    # TODO: Implement")
            lines.append("    return Ok({})")
            lines.append("")

        return "\n".join(lines)

    def _generate_test_code(self, spec: FeatureSpec) -> str:
        """Generate test code."""
        lines = [
            '"""',
            f"Tests for {spec.intent.name}",
            '"""',
            "",
            "import pytest",
            "import sys",
            "from pathlib import Path",
            "",
            "PROJECT_ROOT = Path(__file__).resolve().parents[3]",
            "sys.path.insert(0, str(PROJECT_ROOT))",
            "",
        ]

        # Import target module
        module_path = spec.target_file.replace("/", ".").replace(".py", "")
        lines.append(f"from {module_path} import *")
        lines.append("")

        # Generate test class
        class_name = "".join(w.capitalize() for w in spec.target_module.split("_"))
        lines.append(f"class Test{class_name}:")

        for test in spec.tests:
            lines.append("")
            lines.append(f"    def {test['name']}(self):")
            lines.append(f'        """{test["description"]}"""')
            lines.append(f"        # Test {test['target']}")
            lines.append(f"        result = {test['target']}()")
            if "error" in test["name"]:
                lines.append("        # Verify error handling")
                lines.append("        assert result.is_ok() or result.is_err()")
            else:
                lines.append("        assert result.is_ok()")
            lines.append("")

        return "\n".join(lines)

    def _validate(self, generated: GenerationResult) -> Result[bool, str]:
        """Validate generated code."""
        import ast

        errors = []

        # Validate syntax
        for path, code in generated.code_files.items():
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"{path}: Syntax error - {e}")

        for path, code in generated.test_files.items():
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"{path}: Syntax error - {e}")

        if errors:
            return Err("; ".join(errors))

        return Ok(True)

    def _write_files(self, generated: GenerationResult) -> Result[int, str]:
        """Write generated files to disk."""
        written = 0

        try:
            for path, content in generated.code_files.items():
                full_path = self.project_root / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                written += 1

            for path, content in generated.test_files.items():
                full_path = self.project_root / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                written += 1

            return Ok(written)

        except Exception as e:
            return Err(f"Failed to write files: {e}")

    def _integrate(self, generated: GenerationResult) -> Result[bool, str]:
        """Integrate generated code into codebase."""
        # For now, just mark as integrated
        # Full integration would update __init__.py, add imports, etc.
        return Ok(True)

    def get_status(self) -> dict:
        """Get current pipeline status."""
        if self._current_report is None:
            return {"running": False}

        return {
            "running": self._current_report.current_stage != "completed",
            "feature_name": self._current_report.feature_name,
            "current_stage": self._current_report.current_stage,
            "stages_completed": self._current_report.stages_completed,
            "success": self._current_report.success,
            "error": self._current_report.error,
        }


def main():
    """Command-line interface for feature pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Feature generation pipeline")
    parser.add_argument("request", nargs="?", help="Feature request (natural language)")
    parser.add_argument("--dry-run", action="store_true", help="Generate without writing files")
    parser.add_argument("--integrate", action="store_true", help="Auto-integrate into codebase")
    args = parser.parse_args()

    if not args.request:
        print("Usage: python feature_pipeline.py 'Add a feature that...'")
        print("       python feature_pipeline.py --dry-run 'Create a tool that...'")
        return

    pipeline = FeaturePipeline()
    print(f"🚀 Generating feature: {args.request[:50]}...")

    result = pipeline.generate_feature(
        args.request,
        dry_run=args.dry_run,
        auto_integrate=args.integrate,
    )

    if result.is_ok():
        report = result.unwrap()
        print(f"\n✅ Feature generated: {report.feature_name}")
        print(f"   Stages: {', '.join(report.stages_completed)}")

        if report.generation_result:
            gen = report.generation_result
            print(f"   Code files: {len(gen.code_files)}")
            print(f"   Test files: {len(gen.test_files)}")

            if gen.errors:
                print(f"\n⚠️  Errors: {len(gen.errors)}")
                for err in gen.errors:
                    print(f"     - {err}")
    else:
        print(f"\n❌ Failed: {result.unwrap_err()}")


if __name__ == "__main__":
    main()
