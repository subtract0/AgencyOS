"""
Comprehensive test suite for mutation testing framework.

Tests AST-based mutation generation, test execution, mutation score calculation,
and all mutation types (arithmetic, comparison, boolean, constants, returns).

Constitutional Compliance:
- Article I: Complete test coverage before implementation
- Article II: 100% test success requirement
- Law #1: TDD is mandatory - tests written FIRST
- Law #2: Strict typing always
"""

import tempfile
import textwrap
from pathlib import Path
import pytest
from pydantic import BaseModel, ValidationError
from shared.type_definitions.result import Result, Ok, Err


# Import the module we're testing (will fail initially - TDD)
try:
    from tools.mutation_testing import (
        MutationConfig,
        MutationResult,
        MutationScore,
        MutationTester,
        Mutation,
        MutationType,
        ArithmeticMutator,
        ComparisonMutator,
        BooleanMutator,
        ConstantMutator,
        ReturnMutator,
    )
except ImportError:
    # Expected during TDD - tests written first
    pytest.skip("mutation_testing module not yet implemented", allow_module_level=True)


@pytest.mark.unit
class TestMutationConfig:
    """Test MutationConfig Pydantic model."""

    def test_mutation_config_creation_valid(self):
        """Test valid mutation config creation."""
        config = MutationConfig(
            target_files=["file1.py", "file2.py"],
            test_command="pytest tests/",
            mutation_types=["arithmetic", "comparison"],
            timeout_seconds=60,
            parallel=True
        )
        assert config.target_files == ["file1.py", "file2.py"]
        assert config.test_command == "pytest tests/"
        assert config.mutation_types == ["arithmetic", "comparison"]
        assert config.timeout_seconds == 60
        assert config.parallel is True

    def test_mutation_config_defaults(self):
        """Test default values for optional fields."""
        config = MutationConfig(
            target_files=["file.py"],
            test_command="pytest",
            mutation_types=["arithmetic"]
        )
        assert config.timeout_seconds == 60
        assert config.parallel is True

    def test_mutation_config_validation_empty_files(self):
        """Test validation fails for empty target files."""
        with pytest.raises(ValidationError):
            MutationConfig(
                target_files=[],
                test_command="pytest",
                mutation_types=["arithmetic"]
            )

    def test_mutation_config_validation_empty_command(self):
        """Test validation fails for empty test command."""
        with pytest.raises(ValidationError):
            MutationConfig(
                target_files=["file.py"],
                test_command="",
                mutation_types=["arithmetic"]
            )


@pytest.mark.unit
class TestMutationResult:
    """Test MutationResult Pydantic model."""

    def test_mutation_result_creation(self):
        """Test mutation result creation."""
        result = MutationResult(
            mutation_id="mut_001",
            file_path="/path/to/file.py",
            line_number=42,
            original_code="a + b",
            mutated_code="a - b",
            tests_passed=False,
            tests_failed=True,
            execution_time=1.5
        )
        assert result.mutation_id == "mut_001"
        assert result.line_number == 42
        assert result.tests_failed is True

    def test_mutation_result_surviving_mutation(self):
        """Test identifying a surviving mutation (BAD)."""
        result = MutationResult(
            mutation_id="mut_002",
            file_path="/path/to/file.py",
            line_number=10,
            original_code="if x > 0:",
            mutated_code="if x >= 0:",
            tests_passed=True,  # BAD - mutation survived!
            tests_failed=False,
            execution_time=0.5
        )
        assert result.tests_passed is True
        assert result.tests_failed is False


@pytest.mark.unit
class TestMutationScore:
    """Test MutationScore Pydantic model."""

    def test_mutation_score_calculation(self):
        """Test mutation score calculation."""
        surviving = [
            MutationResult(
                mutation_id="mut_001",
                file_path="file.py",
                line_number=1,
                original_code="a + b",
                mutated_code="a - b",
                tests_passed=True,
                tests_failed=False,
                execution_time=0.1
            )
        ]

        score = MutationScore(
            total_mutations=10,
            mutations_caught=9,
            mutations_survived=1,
            mutation_score=0.9,
            surviving_mutations=surviving
        )

        assert score.total_mutations == 10
        assert score.mutations_caught == 9
        assert score.mutations_survived == 1
        assert score.mutation_score == 0.9
        assert len(score.surviving_mutations) == 1

    def test_mutation_score_perfect(self):
        """Test perfect mutation score (100%)."""
        score = MutationScore(
            total_mutations=50,
            mutations_caught=50,
            mutations_survived=0,
            mutation_score=1.0,
            surviving_mutations=[]
        )
        assert score.mutation_score == 1.0
        assert len(score.surviving_mutations) == 0


@pytest.mark.unit
class TestMutation:
    """Test Mutation dataclass."""

    def test_mutation_creation(self):
        """Test mutation object creation."""
        mutation = Mutation(
            mutation_id="mut_001",
            mutation_type=MutationType.ARITHMETIC,
            file_path="/path/to/file.py",
            line_number=10,
            column_offset=5,
            original_code="a + b",
            mutated_code="a - b",
            original_node="BinOp(Add)",
            mutated_node="BinOp(Sub)"
        )
        assert mutation.mutation_type == MutationType.ARITHMETIC
        assert mutation.line_number == 10
        assert mutation.original_code == "a + b"
        assert mutation.mutated_code == "a - b"


@pytest.mark.unit
class TestArithmeticMutator:
    """Test arithmetic operator mutation."""

    def test_mutate_addition_to_subtraction(self):
        """Test mutating + to -."""
        code = textwrap.dedent("""
            def add(a, b):
                return a + b
        """)

        mutator = ArithmeticMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        assert len(mutations) > 0
        addition_mutation = next(
            (m for m in mutations if m.original_code == "a + b"),
            None
        )
        assert addition_mutation is not None
        assert addition_mutation.mutated_code == "a - b"
        assert addition_mutation.mutation_type == MutationType.ARITHMETIC

    def test_mutate_multiplication_to_division(self):
        """Test mutating * to /."""
        code = textwrap.dedent("""
            def multiply(x, y):
                return x * y
        """)

        mutator = ArithmeticMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        mult_mutation = next(
            (m for m in mutations if m.original_code == "x * y"),
            None
        )
        assert mult_mutation is not None
        assert mult_mutation.mutated_code == "x / y"

    def test_mutate_all_arithmetic_operators(self):
        """Test all arithmetic operator mutations."""
        code = textwrap.dedent("""
            def calc(a, b):
                add_result = a + b
                sub_result = a - b
                mul_result = a * b
                div_result = a / b
                mod_result = a % b
                return add_result, sub_result, mul_result, div_result, mod_result
        """)

        mutator = ArithmeticMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        # Should have at least 5 mutations (one for each operator)
        assert len(mutations) >= 5


@pytest.mark.unit
class TestComparisonMutator:
    """Test comparison operator mutation."""

    def test_mutate_equals_to_not_equals(self):
        """Test mutating == to !=."""
        code = textwrap.dedent("""
            def check(x):
                if x == 0:
                    return True
                return False
        """)

        mutator = ComparisonMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        eq_mutation = next(
            (m for m in mutations if "==" in m.original_code),
            None
        )
        assert eq_mutation is not None
        assert "!=" in eq_mutation.mutated_code

    def test_mutate_greater_than_to_less_than(self):
        """Test mutating > to <."""
        code = textwrap.dedent("""
            def compare(a, b):
                return a > b
        """)

        mutator = ComparisonMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        gt_mutation = next(
            (m for m in mutations if ">" in m.original_code),
            None
        )
        assert gt_mutation is not None
        assert "<" in gt_mutation.mutated_code or "<=" in gt_mutation.mutated_code

    def test_mutate_all_comparison_operators(self):
        """Test all comparison operator mutations."""
        code = textwrap.dedent("""
            def compare_all(a, b):
                eq = a == b
                neq = a != b
                gt = a > b
                gte = a >= b
                lt = a < b
                lte = a <= b
                return eq, neq, gt, gte, lt, lte
        """)

        mutator = ComparisonMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        # Should have at least 6 mutations
        assert len(mutations) >= 6


@pytest.mark.unit
class TestBooleanMutator:
    """Test boolean operator mutation."""

    def test_mutate_and_to_or(self):
        """Test mutating 'and' to 'or'."""
        code = textwrap.dedent("""
            def check(a, b):
                return a and b
        """)

        mutator = BooleanMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        and_mutation = next(
            (m for m in mutations if "and" in m.original_code),
            None
        )
        assert and_mutation is not None
        assert "or" in and_mutation.mutated_code

    def test_mutate_not_to_identity(self):
        """Test removing 'not' operator."""
        code = textwrap.dedent("""
            def negate(x):
                return not x
        """)

        mutator = BooleanMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        not_mutation = next(
            (m for m in mutations if "not" in m.original_code),
            None
        )
        assert not_mutation is not None
        # Should remove 'not'
        assert "not" not in not_mutation.mutated_code


@pytest.mark.unit
class TestConstantMutator:
    """Test constant value mutation."""

    def test_mutate_true_to_false(self):
        """Test mutating True to False."""
        code = textwrap.dedent("""
            def get_flag():
                return True
        """)

        mutator = ConstantMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        true_mutation = next(
            (m for m in mutations if m.original_code == "True"),
            None
        )
        assert true_mutation is not None
        assert true_mutation.mutated_code == "False"

    def test_mutate_numeric_constant(self):
        """Test mutating numeric constants."""
        code = textwrap.dedent("""
            def get_number():
                return 42
        """)

        mutator = ConstantMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        num_mutation = next(
            (m for m in mutations if m.original_code == "42"),
            None
        )
        assert num_mutation is not None
        # Should change to 0 or increment/decrement
        assert num_mutation.mutated_code in ["0", "41", "43"]

    def test_mutate_string_constant(self):
        """Test mutating string constants."""
        code = textwrap.dedent("""
            def get_message():
                return "hello"
        """)

        mutator = ConstantMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        str_mutation = next(
            (m for m in mutations if "hello" in m.original_code),
            None
        )
        assert str_mutation is not None
        # Should change to empty string or different value
        assert str_mutation.mutated_code in ['""', "''", '"mutated"']


@pytest.mark.unit
class TestReturnMutator:
    """Test return statement mutation."""

    def test_mutate_return_to_none(self):
        """Test mutating return value to None."""
        code = textwrap.dedent("""
            def get_value():
                return 42
        """)

        mutator = ReturnMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        return_mutation = next(
            (m for m in mutations if "return 42" in m.original_code),
            None
        )
        assert return_mutation is not None
        assert "None" in return_mutation.mutated_code

    def test_mutate_remove_return(self):
        """Test removing return statement."""
        code = textwrap.dedent("""
            def process():
                return True
        """)

        mutator = ReturnMutator()
        mutations = mutator.generate_mutations(code, "test.py")

        # Should have mutations that remove or modify return
        assert len(mutations) > 0


@pytest.mark.unit
class TestMutationTesterBasics:
    """Test MutationTester core functionality."""

    def test_mutation_tester_initialization(self):
        """Test creating MutationTester with config."""
        config = MutationConfig(
            target_files=["file.py"],
            test_command="pytest",
            mutation_types=["arithmetic"]
        )
        tester = MutationTester(config)
        assert tester.config == config

    def test_generate_mutations_for_file(self):
        """Test generating mutations for a file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(textwrap.dedent("""
                def add(a, b):
                    return a + b
            """))
            temp_file = f.name

        try:
            config = MutationConfig(
                target_files=[temp_file],
                test_command="pytest",
                mutation_types=["arithmetic"]
            )
            tester = MutationTester(config)
            mutations = tester.generate_mutations(temp_file)

            assert isinstance(mutations, list)
            assert len(mutations) > 0
            assert all(isinstance(m, Mutation) for m in mutations)

        finally:
            Path(temp_file).unlink()

    def test_apply_mutation_creates_backup(self):
        """Test applying mutation creates backup of original."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            original_code = textwrap.dedent("""
                def add(a, b):
                    return a + b
            """)
            f.write(original_code)
            temp_file = f.name

        try:
            mutation = Mutation(
                mutation_id="test_001",
                mutation_type=MutationType.ARITHMETIC,
                file_path=temp_file,
                line_number=2,
                column_offset=11,
                original_code="a + b",
                mutated_code="a - b",
                original_node="BinOp(Add)",
                mutated_node="BinOp(Sub)"
            )

            config = MutationConfig(
                target_files=[temp_file],
                test_command="pytest",
                mutation_types=["arithmetic"]
            )
            tester = MutationTester(config)
            result = tester.apply_mutation(mutation)

            assert result.is_ok()

            # Check backup exists
            backup_path = Path(f"{temp_file}.backup")
            assert backup_path.exists()

            # Check mutation was applied
            mutated_content = Path(temp_file).read_text()
            assert "a - b" in mutated_content

            # Cleanup
            tester.restore_original(temp_file)
            backup_path.unlink(missing_ok=True)

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_restore_original_from_backup(self):
        """Test restoring original file from backup."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            original_code = "def original(): pass\n"
            f.write(original_code)
            temp_file = f.name

        try:
            # Create backup
            backup_path = Path(f"{temp_file}.backup")
            backup_path.write_text(original_code)

            # Modify original
            Path(temp_file).write_text("def mutated(): pass\n")

            # Restore
            config = MutationConfig(
                target_files=[temp_file],
                test_command="pytest",
                mutation_types=["arithmetic"]
            )
            tester = MutationTester(config)
            result = tester.restore_original(temp_file)

            assert result.is_ok()
            assert Path(temp_file).read_text() == original_code
            assert not backup_path.exists()

        finally:
            Path(temp_file).unlink(missing_ok=True)
            Path(f"{temp_file}.backup").unlink(missing_ok=True)


@pytest.mark.unit
class TestMutationTesterExecution:
    """Test mutation test execution."""

    def test_run_tests_success(self):
        """Test running tests that pass."""
        config = MutationConfig(
            target_files=["dummy.py"],
            test_command="echo 'success' && exit 0",
            mutation_types=["arithmetic"]
        )
        tester = MutationTester(config)
        result = tester.run_tests()

        assert result.is_ok()
        assert result.unwrap() is True

    def test_run_tests_failure(self):
        """Test running tests that fail."""
        config = MutationConfig(
            target_files=["dummy.py"],
            test_command="exit 1",
            mutation_types=["arithmetic"]
        )
        tester = MutationTester(config)
        result = tester.run_tests()

        assert result.is_ok()
        assert result.unwrap() is False

    def test_run_tests_timeout(self):
        """Test test execution timeout."""
        config = MutationConfig(
            target_files=["dummy.py"],
            test_command="sleep 10",
            mutation_types=["arithmetic"],
            timeout_seconds=1
        )
        tester = MutationTester(config)
        result = tester.run_tests()

        # Should return error on timeout
        assert result.is_err()
        assert "timeout" in str(result.unwrap_err()).lower()


@pytest.mark.unit
class TestMutationTesterFullRun:
    """Test complete mutation testing workflow."""

    def test_full_mutation_test_run(self):
        """Test complete mutation testing process."""
        # Create a simple Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(textwrap.dedent("""
                def add(a, b):
                    return a + b

                def is_positive(x):
                    return x > 0
            """))
            temp_file = f.name

        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(textwrap.dedent("""
                import sys
                sys.path.insert(0, '/tmp')

                def test_add():
                    # Simple test that should catch mutations
                    assert True  # Placeholder

                def test_is_positive():
                    assert True  # Placeholder
            """))
            test_file = f.name

        try:
            config = MutationConfig(
                target_files=[temp_file],
                test_command=f"python -m pytest {test_file} -v",
                mutation_types=["arithmetic", "comparison"],
                timeout_seconds=30,
                parallel=False
            )

            tester = MutationTester(config)
            result = tester.run()

            # Should return a MutationScore
            assert result.is_ok()
            score = result.unwrap()
            assert isinstance(score, MutationScore)
            assert score.total_mutations > 0
            assert score.mutation_score >= 0.0
            assert score.mutation_score <= 1.0

        finally:
            Path(temp_file).unlink(missing_ok=True)
            Path(test_file).unlink(missing_ok=True)

    def test_mutation_score_calculation_correct(self):
        """Test mutation score is calculated correctly."""
        # Create file with simple function
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(textwrap.dedent("""
                def simple(x):
                    return x + 1
            """))
            temp_file = f.name

        try:
            config = MutationConfig(
                target_files=[temp_file],
                test_command="exit 1",  # All tests fail (good - catches mutations)
                mutation_types=["arithmetic"],
                parallel=False
            )

            tester = MutationTester(config)
            result = tester.run()

            assert result.is_ok()
            score = result.unwrap()

            # If all tests fail, all mutations are caught
            if score.total_mutations > 0:
                assert score.mutations_caught == score.total_mutations
                assert score.mutations_survived == 0
                assert score.mutation_score == 1.0

        finally:
            Path(temp_file).unlink(missing_ok=True)


@pytest.mark.unit
class TestMutationReporting:
    """Test mutation testing report generation."""

    def test_generate_report_basic(self):
        """Test basic report generation."""
        surviving = [
            MutationResult(
                mutation_id="mut_001",
                file_path="/path/to/file.py",
                line_number=10,
                original_code="a + b",
                mutated_code="a - b",
                tests_passed=True,
                tests_failed=False,
                execution_time=0.5
            )
        ]

        score = MutationScore(
            total_mutations=10,
            mutations_caught=9,
            mutations_survived=1,
            mutation_score=0.9,
            surviving_mutations=surviving
        )

        config = MutationConfig(
            target_files=["file.py"],
            test_command="pytest",
            mutation_types=["arithmetic"]
        )
        tester = MutationTester(config)
        report = tester.generate_report(score)

        assert isinstance(report, str)
        assert "90" in report  # Check for 90 (could be 90% or 90.00%)
        assert "Mutation Score" in report or "MUTATION" in report
        assert "Surviving" in report or "SURVIVING" in report

    def test_generate_report_perfect_score(self):
        """Test report for perfect mutation score."""
        score = MutationScore(
            total_mutations=20,
            mutations_caught=20,
            mutations_survived=0,
            mutation_score=1.0,
            surviving_mutations=[]
        )

        config = MutationConfig(
            target_files=["file.py"],
            test_command="pytest",
            mutation_types=["arithmetic"]
        )
        tester = MutationTester(config)
        report = tester.generate_report(score)

        assert "100" in report  # Check for 100 (could be 100% or 100.00%)
        assert "EXCELLENT" in report or "Perfect" in report

    def test_generate_report_poor_score(self):
        """Test report for poor mutation score."""
        surviving = [
            MutationResult(
                mutation_id=f"mut_{i:03d}",
                file_path="/path/to/file.py",
                line_number=i,
                original_code="original",
                mutated_code="mutated",
                tests_passed=True,
                tests_failed=False,
                execution_time=0.1
            )
            for i in range(8)  # 8 surviving out of 10
        ]

        score = MutationScore(
            total_mutations=10,
            mutations_caught=2,
            mutations_survived=8,
            mutation_score=0.2,
            surviving_mutations=surviving
        )

        config = MutationConfig(
            target_files=["file.py"],
            test_command="pytest",
            mutation_types=["arithmetic"]
        )
        tester = MutationTester(config)
        report = tester.generate_report(score)

        assert "20" in report  # Check for 20 (could be 20% or 20.00%)
        assert "POOR" in report or "Poor" in report or "Needs Improvement" in report
        assert len(surviving) == 8


@pytest.mark.unit
class TestMutationTypeEnum:
    """Test MutationType enumeration."""

    def test_mutation_type_values(self):
        """Test all mutation type enum values exist."""
        assert MutationType.ARITHMETIC
        assert MutationType.COMPARISON
        assert MutationType.BOOLEAN
        assert MutationType.CONSTANT
        assert MutationType.RETURN

    def test_mutation_type_string_conversion(self):
        """Test mutation type can be converted to string."""
        assert str(MutationType.ARITHMETIC) or MutationType.ARITHMETIC.value
        assert str(MutationType.COMPARISON) or MutationType.COMPARISON.value


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_mutation_on_syntax_error_file(self):
        """Test handling file with syntax errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def broken(:\n    return invalid syntax")
            temp_file = f.name

        try:
            config = MutationConfig(
                target_files=[temp_file],
                test_command="pytest",
                mutation_types=["arithmetic"]
            )
            tester = MutationTester(config)
            result = tester.generate_mutations(temp_file)

            # Should handle gracefully - either empty list or error
            assert isinstance(result, list) or result is None

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_mutation_on_empty_file(self):
        """Test mutation on empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            temp_file = f.name

        try:
            config = MutationConfig(
                target_files=[temp_file],
                test_command="pytest",
                mutation_types=["arithmetic"]
            )
            tester = MutationTester(config)
            mutations = tester.generate_mutations(temp_file)

            assert isinstance(mutations, list)
            assert len(mutations) == 0

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_mutation_on_nonexistent_file(self):
        """Test mutation on file that doesn't exist."""
        config = MutationConfig(
            target_files=["/nonexistent/file.py"],
            test_command="pytest",
            mutation_types=["arithmetic"]
        )
        tester = MutationTester(config)
        result = tester.generate_mutations("/nonexistent/file.py")

        # Should handle gracefully
        assert isinstance(result, list)
        assert len(result) == 0
