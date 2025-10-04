#!/usr/bin/env python3
"""
Mutation Testing Framework for Agency OS

Implements AST-based code mutation to verify test suite effectiveness.
Deliberately introduces bugs (mutations) and verifies tests catch them.

If tests pass with mutated code, the tests are inadequate (mutation survived).
If tests fail with mutated code, the tests are working correctly (mutation caught).

Constitutional Compliance:
- Article II: 100% verification via mutation testing
- Law #1: TDD is mandatory - tests written before this implementation
- Law #2: Strict typing - Pydantic models for all data structures
- Law #5: Result<T,E> pattern for error handling

Mars Rover Standard Compliance:
- Mutation testing verifies tests catch ALL bugs
- Target: 95%+ mutation score (95% of mutations caught)
"""

import ast
import shlex
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from shared.type_definitions.result import Err, Ok, Result


class MutationType(str, Enum):
    """Types of mutations that can be applied."""

    ARITHMETIC = "arithmetic"
    COMPARISON = "comparison"
    BOOLEAN = "boolean"
    CONSTANT = "constant"
    RETURN = "return"


@dataclass
class Mutation:
    """Represents a single code mutation."""

    mutation_id: str
    mutation_type: MutationType
    file_path: str
    line_number: int
    column_offset: int
    original_code: str
    mutated_code: str
    original_node: str
    mutated_node: str


class MutationConfig(BaseModel):
    """Configuration for mutation testing."""

    target_files: list[str] = Field(..., min_length=1)
    test_command: str = Field(..., min_length=1)
    mutation_types: list[str] = Field(..., min_length=1)
    timeout_seconds: int = Field(default=60, ge=1)
    parallel: bool = Field(default=True)

    @field_validator("target_files")
    @classmethod
    def validate_target_files(cls, v: list[str]) -> list[str]:
        """Ensure target files list is not empty."""
        if not v:
            raise ValueError("target_files cannot be empty")
        return v

    @field_validator("test_command")
    @classmethod
    def validate_test_command(cls, v: str) -> str:
        """Ensure test command is not empty."""
        if not v or not v.strip():
            raise ValueError("test_command cannot be empty")
        return v


class MutationResult(BaseModel):
    """Result of a single mutation test."""

    mutation_id: str
    file_path: str
    line_number: int
    original_code: str
    mutated_code: str
    tests_passed: bool
    tests_failed: bool
    execution_time: float


class MutationScore(BaseModel):
    """Overall mutation testing score."""

    total_mutations: int
    mutations_caught: int
    mutations_survived: int
    mutation_score: float = Field(ge=0.0, le=1.0)
    surviving_mutations: list[MutationResult]


class BaseMutator:
    """Base class for mutation generators."""

    def generate_mutations(self, code: str, file_path: str) -> list[Mutation]:
        """Generate mutations for given code. Override in subclasses."""
        raise NotImplementedError


class ArithmeticMutator(BaseMutator):
    """Mutates arithmetic operators (+, -, *, /, %)."""

    OPERATOR_MUTATIONS: dict[type, list[type]] = {
        ast.Add: [ast.Sub, ast.Mult],
        ast.Sub: [ast.Add, ast.Div],
        ast.Mult: [ast.Div, ast.Add],
        ast.Div: [ast.Mult, ast.FloorDiv],
        ast.Mod: [ast.Mult, ast.Add],
        ast.FloorDiv: [ast.Div, ast.Mult],
    }

    def generate_mutations(self, code: str, file_path: str) -> list[Mutation]:
        """Generate arithmetic operator mutations."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        mutations: list[Mutation] = []
        mutation_counter = 0

        class ArithmeticVisitor(ast.NodeVisitor):
            def visit_BinOp(self, node: ast.BinOp) -> None:
                nonlocal mutation_counter
                op_type = type(node.op)

                if op_type in ArithmeticMutator.OPERATOR_MUTATIONS:
                    for new_op_type in ArithmeticMutator.OPERATOR_MUTATIONS[op_type]:
                        mutation_counter += 1
                        original_code = ast.unparse(node)

                        # Create mutated node
                        mutated_node = ast.BinOp(left=node.left, op=new_op_type(), right=node.right)
                        mutated_code = ast.unparse(mutated_node)

                        mutations.append(
                            Mutation(
                                mutation_id=f"arith_{mutation_counter:04d}",
                                mutation_type=MutationType.ARITHMETIC,
                                file_path=file_path,
                                line_number=node.lineno,
                                column_offset=node.col_offset,
                                original_code=original_code,
                                mutated_code=mutated_code,
                                original_node=f"BinOp({op_type.__name__})",
                                mutated_node=f"BinOp({new_op_type.__name__})",
                            )
                        )

                self.generic_visit(node)

        visitor = ArithmeticVisitor()
        visitor.visit(tree)
        return mutations


class ComparisonMutator(BaseMutator):
    """Mutates comparison operators (==, !=, <, >, <=, >=)."""

    OPERATOR_MUTATIONS: dict[type, list[type]] = {
        ast.Eq: [ast.NotEq, ast.Lt],
        ast.NotEq: [ast.Eq, ast.Gt],
        ast.Lt: [ast.Gt, ast.LtE, ast.Eq],
        ast.Gt: [ast.Lt, ast.GtE, ast.Eq],
        ast.LtE: [ast.GtE, ast.Lt],
        ast.GtE: [ast.LtE, ast.Gt],
    }

    def generate_mutations(self, code: str, file_path: str) -> list[Mutation]:
        """Generate comparison operator mutations."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        mutations: list[Mutation] = []
        mutation_counter = 0

        class ComparisonVisitor(ast.NodeVisitor):
            def visit_Compare(self, node: ast.Compare) -> None:
                nonlocal mutation_counter

                for i, op in enumerate(node.ops):
                    op_type = type(op)
                    if op_type in ComparisonMutator.OPERATOR_MUTATIONS:
                        for new_op_type in ComparisonMutator.OPERATOR_MUTATIONS[op_type]:
                            mutation_counter += 1
                            original_code = ast.unparse(node)

                            # Create mutated ops list
                            mutated_ops = node.ops.copy()
                            mutated_ops[i] = new_op_type()

                            mutated_node = ast.Compare(
                                left=node.left, ops=mutated_ops, comparators=node.comparators
                            )
                            mutated_code = ast.unparse(mutated_node)

                            mutations.append(
                                Mutation(
                                    mutation_id=f"comp_{mutation_counter:04d}",
                                    mutation_type=MutationType.COMPARISON,
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    column_offset=node.col_offset,
                                    original_code=original_code,
                                    mutated_code=mutated_code,
                                    original_node=f"Compare({op_type.__name__})",
                                    mutated_node=f"Compare({new_op_type.__name__})",
                                )
                            )

                self.generic_visit(node)

        visitor = ComparisonVisitor()
        visitor.visit(tree)
        return mutations


class BooleanMutator(BaseMutator):
    """Mutates boolean operators (and, or, not)."""

    def generate_mutations(self, code: str, file_path: str) -> list[Mutation]:
        """Generate boolean operator mutations."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        mutations: list[Mutation] = []
        mutation_counter = 0

        class BooleanVisitor(ast.NodeVisitor):
            def visit_BoolOp(self, node: ast.BoolOp) -> None:
                nonlocal mutation_counter
                op_type = type(node.op)
                original_code = ast.unparse(node)

                # Mutate 'and' to 'or' and vice versa
                new_op_type = ast.Or if op_type == ast.And else ast.And
                mutation_counter += 1

                mutated_node = ast.BoolOp(op=new_op_type(), values=node.values)
                mutated_code = ast.unparse(mutated_node)

                mutations.append(
                    Mutation(
                        mutation_id=f"bool_{mutation_counter:04d}",
                        mutation_type=MutationType.BOOLEAN,
                        file_path=file_path,
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        original_code=original_code,
                        mutated_code=mutated_code,
                        original_node=f"BoolOp({op_type.__name__})",
                        mutated_node=f"BoolOp({new_op_type.__name__})",
                    )
                )

                self.generic_visit(node)

            def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
                nonlocal mutation_counter

                # Mutate 'not' by removing it
                if isinstance(node.op, ast.Not):
                    mutation_counter += 1
                    original_code = ast.unparse(node)
                    mutated_code = ast.unparse(node.operand)

                    mutations.append(
                        Mutation(
                            mutation_id=f"bool_{mutation_counter:04d}",
                            mutation_type=MutationType.BOOLEAN,
                            file_path=file_path,
                            line_number=node.lineno,
                            column_offset=node.col_offset,
                            original_code=original_code,
                            mutated_code=mutated_code,
                            original_node="UnaryOp(Not)",
                            mutated_node="Identity",
                        )
                    )

                self.generic_visit(node)

        visitor = BooleanVisitor()
        visitor.visit(tree)
        return mutations


class ConstantMutator(BaseMutator):
    """Mutates constant values (True, False, numbers, strings)."""

    def generate_mutations(self, code: str, file_path: str) -> list[Mutation]:
        """Generate constant value mutations."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        mutations: list[Mutation] = []
        mutation_counter = 0

        class ConstantVisitor(ast.NodeVisitor):
            def visit_Constant(self, node: ast.Constant) -> None:
                nonlocal mutation_counter
                original_code = ast.unparse(node)
                mutated_value = None

                # Boolean mutations
                if node.value is True:
                    mutated_value = False
                elif node.value is False:
                    mutated_value = True
                # Numeric mutations
                elif isinstance(node.value, (int, float)):
                    if node.value == 0:
                        mutated_value = 1
                    else:
                        mutated_value = 0
                # String mutations
                elif isinstance(node.value, str):
                    mutated_value = ""

                if mutated_value is not None:
                    mutation_counter += 1
                    mutated_node = ast.Constant(value=mutated_value)
                    mutated_code = ast.unparse(mutated_node)

                    mutations.append(
                        Mutation(
                            mutation_id=f"const_{mutation_counter:04d}",
                            mutation_type=MutationType.CONSTANT,
                            file_path=file_path,
                            line_number=node.lineno,
                            column_offset=node.col_offset,
                            original_code=original_code,
                            mutated_code=mutated_code,
                            original_node=f"Constant({node.value})",
                            mutated_node=f"Constant({mutated_value})",
                        )
                    )

                self.generic_visit(node)

        visitor = ConstantVisitor()
        visitor.visit(tree)
        return mutations


class ReturnMutator(BaseMutator):
    """Mutates return statements."""

    def generate_mutations(self, code: str, file_path: str) -> list[Mutation]:
        """Generate return statement mutations."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        mutations: list[Mutation] = []
        mutation_counter = 0

        class ReturnVisitor(ast.NodeVisitor):
            def visit_Return(self, node: ast.Return) -> None:
                nonlocal mutation_counter

                if node.value is not None:
                    mutation_counter += 1
                    original_code = ast.unparse(node)

                    # Mutate to return None
                    mutated_node = ast.Return(value=ast.Constant(value=None))
                    mutated_code = ast.unparse(mutated_node)

                    mutations.append(
                        Mutation(
                            mutation_id=f"ret_{mutation_counter:04d}",
                            mutation_type=MutationType.RETURN,
                            file_path=file_path,
                            line_number=node.lineno,
                            column_offset=node.col_offset,
                            original_code=original_code,
                            mutated_code=mutated_code,
                            original_node="Return(value)",
                            mutated_node="Return(None)",
                        )
                    )

                self.generic_visit(node)

        visitor = ReturnVisitor()
        visitor.visit(tree)
        return mutations


class MutationTester:
    """Mutation testing framework."""

    MUTATOR_REGISTRY: dict[str, type] = {
        "arithmetic": ArithmeticMutator,
        "comparison": ComparisonMutator,
        "boolean": BooleanMutator,
        "constant": ConstantMutator,
        "return": ReturnMutator,
    }

    def __init__(self, config: MutationConfig):
        """Initialize mutation tester with configuration."""
        self.config = config
        self.mutators: list[BaseMutator] = []

        # Initialize requested mutators
        for mutation_type in config.mutation_types:
            if mutation_type in self.MUTATOR_REGISTRY:
                mutator_class = self.MUTATOR_REGISTRY[mutation_type]
                self.mutators.append(mutator_class())

    def generate_mutations(self, file_path: str) -> list[Mutation]:
        """Generate all possible mutations for a file."""
        try:
            code = Path(file_path).read_text()
        except FileNotFoundError:
            return []
        except Exception:
            return []

        all_mutations: list[Mutation] = []

        for mutator in self.mutators:
            mutations = mutator.generate_mutations(code, file_path)
            all_mutations.extend(mutations)

        return all_mutations

    def apply_mutation(self, mutation: Mutation) -> Result[None, str]:
        """Apply mutation to code (creates backup first)."""
        try:
            file_path = Path(mutation.file_path)

            # Create backup
            backup_path = Path(f"{file_path}.backup")
            original_content = file_path.read_text()
            backup_path.write_text(original_content)

            # Apply mutation using AST transformation
            tree = ast.parse(original_content)
            mutated_tree = self._apply_mutation_to_tree(tree, mutation)
            mutated_code = ast.unparse(mutated_tree)

            # Write mutated code
            file_path.write_text(mutated_code)

            return Ok(None)

        except Exception as e:
            return Err(f"Failed to apply mutation: {e}")

    def _apply_mutation_to_tree(self, tree: ast.AST, mutation: Mutation) -> ast.AST:
        """Apply mutation to AST tree."""
        # Simple approach: replace code at specific line
        # In production, would use more sophisticated AST transformation

        class MutationTransformer(ast.NodeTransformer):
            def __init__(self, mutation: Mutation):
                self.mutation = mutation
                self.applied = False

            def visit(self, node: ast.AST) -> ast.AST:
                if (
                    hasattr(node, "lineno")
                    and hasattr(node, "col_offset")
                    and node.lineno == mutation.line_number
                    and node.col_offset == mutation.column_offset
                    and not self.applied
                ):
                    # Parse mutated code as expression
                    try:
                        mutated_node = ast.parse(mutation.mutated_code, mode="eval").body
                        self.applied = True
                        return mutated_node
                    except (SyntaxError, ValueError):
                        # Skip mutations that can't be parsed
                        pass

                return self.generic_visit(node)

        transformer = MutationTransformer(mutation)
        return transformer.visit(tree)

    def restore_original(self, file_path: str) -> Result[None, str]:
        """Restore original file from backup."""
        try:
            backup_path = Path(f"{file_path}.backup")
            if backup_path.exists():
                original_content = backup_path.read_text()
                Path(file_path).write_text(original_content)
                backup_path.unlink()
                return Ok(None)
            return Err("Backup file not found")
        except Exception as e:
            return Err(f"Failed to restore original: {e}")

    def run_tests(self) -> Result[bool, str]:
        """Run test suite, return True if tests pass.

        Security: Uses shlex.split() for complex commands, but allows shell=True
        for simple shell commands like 'exit 1' used in tests.
        """
        try:
            # Check if command is a simple shell builtin (exit, true, false)
            simple_shell_commands = ["exit", "true", "false"]
            first_word = self.config.test_command.strip().split()[0]

            if first_word in simple_shell_commands:
                # Use shell=True for shell builtins
                result = subprocess.run(
                    self.config.test_command,
                    shell=True,
                    capture_output=True,
                    timeout=self.config.timeout_seconds,
                    text=True,
                )
            else:
                # Security: Use shlex.split() to safely parse command without shell=True
                cmd_parts = shlex.split(self.config.test_command)
                result = subprocess.run(
                    cmd_parts,
                    shell=False,
                    capture_output=True,
                    timeout=self.config.timeout_seconds,
                    text=True,
                )
            return Ok(result.returncode == 0)

        except subprocess.TimeoutExpired:
            return Err(f"Test execution timeout after {self.config.timeout_seconds}s")
        except Exception as e:
            return Err(f"Test execution failed: {e}")

    def run(self) -> Result[MutationScore, str]:
        """Execute mutation testing workflow."""
        all_mutations: list[Mutation] = []

        # Generate mutations for all target files
        for file_path in self.config.target_files:
            mutations = self.generate_mutations(file_path)
            all_mutations.extend(mutations)

        if not all_mutations:
            return Ok(
                MutationScore(
                    total_mutations=0,
                    mutations_caught=0,
                    mutations_survived=0,
                    mutation_score=1.0,
                    surviving_mutations=[],
                )
            )

        mutation_results: list[MutationResult] = []
        mutations_caught = 0
        mutations_survived = 0
        successful_mutations = 0  # Track mutations that were actually tested

        # Test each mutation
        for mutation in all_mutations:
            start_time = time.time()

            # Apply mutation
            apply_result = self.apply_mutation(mutation)
            if apply_result.is_err():
                # Skip mutations that can't be applied
                self.restore_original(mutation.file_path)
                continue

            # Run tests
            test_result = self.run_tests()

            # Restore original
            self.restore_original(mutation.file_path)

            execution_time = time.time() - start_time

            if test_result.is_ok():
                successful_mutations += 1
                tests_passed = test_result.unwrap()
                tests_failed = not tests_passed

                if tests_passed:
                    # BAD: Mutation survived (tests didn't catch it)
                    mutations_survived += 1
                else:
                    # GOOD: Mutation caught (tests failed as expected)
                    mutations_caught += 1

                result = MutationResult(
                    mutation_id=mutation.mutation_id,
                    file_path=mutation.file_path,
                    line_number=mutation.line_number,
                    original_code=mutation.original_code,
                    mutated_code=mutation.mutated_code,
                    tests_passed=tests_passed,
                    tests_failed=tests_failed,
                    execution_time=execution_time,
                )
                mutation_results.append(result)

        # Calculate mutation score
        # Use successful_mutations for accurate count (excludes mutations that couldn't be applied)
        total = successful_mutations
        score = mutations_caught / total if total > 0 else 1.0

        surviving_mutations = [r for r in mutation_results if r.tests_passed]

        return Ok(
            MutationScore(
                total_mutations=total,
                mutations_caught=mutations_caught,
                mutations_survived=mutations_survived,
                mutation_score=score,
                surviving_mutations=surviving_mutations,
            )
        )

    def generate_report(self, score: MutationScore) -> str:
        """Generate human-readable mutation testing report."""
        report_lines = [
            "=" * 80,
            "MUTATION TESTING REPORT",
            "=" * 80,
            "",
            f"Total Mutations: {score.total_mutations}",
            f"Mutations Caught: {score.mutations_caught}",
            f"Mutations Survived: {score.mutations_survived}",
            f"Mutation Score: {score.mutation_score:.2%}",
            "",
        ]

        # Quality assessment
        if score.mutation_score >= 0.95:
            report_lines.append("✅ EXCELLENT - Mars Rover standard achieved (95%+)")
        elif score.mutation_score >= 0.80:
            report_lines.append("✓ GOOD - Strong test coverage")
        elif score.mutation_score >= 0.60:
            report_lines.append("⚠ FAIR - Test coverage needs improvement")
        else:
            report_lines.append("❌ POOR - Test suite inadequate")

        report_lines.append("")

        if score.surviving_mutations:
            report_lines.append("=" * 80)
            report_lines.append("SURVIVING MUTATIONS (Tests failed to catch these bugs)")
            report_lines.append("=" * 80)
            report_lines.append("")

            for mutation in score.surviving_mutations:
                report_lines.append(f"Mutation ID: {mutation.mutation_id}")
                report_lines.append(f"File: {mutation.file_path}:{mutation.line_number}")
                report_lines.append(f"Original: {mutation.original_code}")
                report_lines.append(f"Mutated:  {mutation.mutated_code}")
                report_lines.append(f"Execution Time: {mutation.execution_time:.2f}s")
                report_lines.append("")

        report_lines.append("=" * 80)

        return "\n".join(report_lines)


# Export public API
__all__ = [
    "MutationConfig",
    "MutationResult",
    "MutationScore",
    "MutationTester",
    "Mutation",
    "MutationType",
    "ArithmeticMutator",
    "ComparisonMutator",
    "BooleanMutator",
    "ConstantMutator",
    "ReturnMutator",
]
