"""
Spec Traceability Validation Tool

Validates that code implementations reference their specifications
and that all complex features have formal specs.

Constitutional Compliance: Article V - Spec-Driven Development
"""

import re
from pathlib import Path

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result


class SpecTraceabilityReport(BaseModel):
    """Report on spec traceability compliance."""

    total_files: int = Field(description="Total Python files checked")
    files_with_spec_refs: int = Field(description="Files with spec references")
    files_without_spec_refs: int = Field(description="Files without spec references")
    spec_coverage: float = Field(description="Percentage of files with spec refs")
    violations: list[str] = Field(
        default_factory=list, description="Files violating spec requirement"
    )
    compliant: bool = Field(description="Whether spec coverage meets threshold")


class SpecTraceabilityValidator(BaseModel):
    """Validates spec traceability across codebase."""

    min_coverage: float = Field(default=0.80, description="Minimum spec coverage required")
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["test_*.py", "*_test.py", "__init__.py"],
        description="File patterns to exclude from validation",
    )

    def validate_file(self, file_path: Path) -> bool:
        """Check if file contains spec reference.

        Valid spec references:
        - # Spec: specs/feature-name.md
        - # Specification: specs/feature-name.md
        - # See: specs/feature-name.md
        - Docstring with "Specification:" or "Spec:"
        """
        try:
            content = file_path.read_text()

            # Pattern 1: Comment-based spec reference
            comment_pattern = r"#\s*(Spec|Specification|See):\s*specs/[\w\-]+\.md"
            if re.search(comment_pattern, content, re.IGNORECASE):
                return True

            # Pattern 2: Docstring spec reference
            docstring_pattern = r'"""[\s\S]*?(Spec|Specification):\s*specs/[\w\-]+\.md'
            if re.search(docstring_pattern, content, re.IGNORECASE):
                return True

            return False
        except Exception:
            return False

    def should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from validation."""
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return True
        return False

    def validate_codebase(self, root_path: Path) -> Result[SpecTraceabilityReport, str]:
        """Validate spec traceability across entire codebase."""
        try:
            python_files = list(root_path.rglob("*.py"))

            total = 0
            with_refs = 0
            violations = []

            for file_path in python_files:
                if self.should_exclude(file_path):
                    continue

                total += 1
                if self.validate_file(file_path):
                    with_refs += 1
                else:
                    violations.append(str(file_path.relative_to(root_path)))

            coverage = (with_refs / total * 100) if total > 0 else 0.0
            compliant = coverage >= (self.min_coverage * 100)

            report = SpecTraceabilityReport(
                total_files=total,
                files_with_spec_refs=with_refs,
                files_without_spec_refs=total - with_refs,
                spec_coverage=coverage,
                violations=violations,
                compliant=compliant,
            )

            return Ok(report)
        except Exception as e:
            return Err(f"Spec traceability validation failed: {e}")


def main():
    """CLI entry point for spec traceability validation."""
    import sys

    validator = SpecTraceabilityValidator(min_coverage=0.60)
    result = validator.validate_codebase(Path.cwd())

    if result.is_err():
        print(f"❌ Validation error: {result.unwrap_err()}")
        sys.exit(1)

    report = result.unwrap()
    print("\n📊 Spec Traceability Report")
    print("━" * 50)
    print(f"Total files:        {report.total_files}")
    print(f"With spec refs:     {report.files_with_spec_refs}")
    print(f"Without spec refs:  {report.files_without_spec_refs}")
    print(f"Coverage:           {report.spec_coverage:.1f}%")
    print(f"Required:           {validator.min_coverage * 100:.1f}%")
    print(f"Status:             {'✅ PASS' if report.compliant else '❌ FAIL'}")

    if not report.compliant and report.violations:
        print("\n⚠️  Files missing spec references (showing first 10):")
        for violation in report.violations[:10]:
            print(f"  - {violation}")

    sys.exit(0 if report.compliant else 1)


if __name__ == "__main__":
    main()
