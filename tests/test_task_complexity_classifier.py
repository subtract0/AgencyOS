"""Tests for TaskComplexityClassifier.

Per ADR-024 and Leap 3 Milestone 3.
"""

import pytest

from shared.task_complexity import TaskComplexity, TaskComplexityClassifier


class TestKeywordClassification:
    """Test keyword-based classification (Method 1)."""

    def test_p3_simple_typo_fix(self):
        """P3: Simple typo correction."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Fix typo in function name: calcualte_total → calculate_total",
            task_type="code_modification"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P3_SIMPLE
        assert classification.method == "keyword"
        assert classification.confidence >= 0.8

    def test_p3_remove_unused_import(self):
        """P3: Remove unused import."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Remove unused import statement from utils.py",
            task_type="code_modification"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P3_SIMPLE

    def test_p3_add_docstring(self):
        """P3: Add documentation."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Add docstring to calculate_total function",
            task_type="documentation"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P3_SIMPLE

    def test_p3_rename_variable(self):
        """P3: Rename variable for clarity."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Rename variable 'x' to 'user_count' for clarity",
            task_type="code_modification"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P3_SIMPLE

    def test_p3_format_code(self):
        """P3: Code formatting."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Format code with black formatter",
            task_type="code_modification"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P3_SIMPLE

    def test_p1_complex_adr_creation(self):
        """P1: Create ADR (architectural decision)."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Create ADR for database selection: PostgreSQL vs MongoDB",
            task_type="architecture"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P1_COMPLEX
        assert classification.method == "keyword"
        assert classification.confidence >= 0.8

    def test_p1_distributed_consensus(self):
        """P1: Distributed system design."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Design distributed consensus algorithm for multi-agent coordination",
            task_type="architecture"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P1_COMPLEX

    def test_p1_autonomous_healing(self):
        """P1: Autonomous healing system."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Implement autonomous self-healing for NoneType errors",
            task_type="architecture"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P1_COMPLEX

    def test_p1_constitutional_compliance(self):
        """P1: Constitutional compliance validation."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Design constitutional compliance validation framework",
            task_type="architecture"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P1_COMPLEX

    def test_p2_moderate_feature_impl(self):
        """P2: Feature implementation."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Implement user authentication with JWT tokens",
            task_type="feature_implementation"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P2_MODERATE

    def test_p2_bug_fix(self):
        """P2: Bug fix with business logic."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Fix bug: division by zero in calculate_average",
            task_type="bug_fix"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P2_MODERATE

    def test_p2_refactoring(self):
        """P2: Refactoring."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Refactor UserService to use dependency injection",
            task_type="code_modification"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P2_MODERATE


class TestASTClassification:
    """Test AST-based classification (Method 2)."""

    def test_ast_simple_code(self):
        """AST: Simple code with low complexity."""
        classifier = TaskComplexityClassifier()

        task = """
        Modify this code:
        ```python
        def calculate_total(items):
            return sum(item.price for item in items)
        ```
        """

        result = classifier.classify(task, task_type="code_modification")

        assert result.is_ok()
        classification = result.unwrap()
        # Simple code → P3 or P2
        assert classification.complexity in [TaskComplexity.P3_SIMPLE, TaskComplexity.P2_MODERATE]

    def test_ast_complex_code(self):
        """AST: Complex code with high complexity."""
        classifier = TaskComplexityClassifier()

        task = """
        Refactor this code:
        ```python
        def process_payment(user, amount):
            if user.is_active:
                if user.balance >= amount:
                    if user.has_permission("payment"):
                        for attempt in range(3):
                            try:
                                result = charge_card(user.card, amount)
                                if result.success:
                                    user.balance -= amount
                                    return True
                            except PaymentError:
                                if attempt == 2:
                                    raise
            return False
        ```
        """

        result = classifier.classify(task, task_type="code_modification")

        assert result.is_ok()
        classification = result.unwrap()
        # Complex code → P1 or P2
        assert classification.complexity in [TaskComplexity.P1_COMPLEX, TaskComplexity.P2_MODERATE]


class TestFallbackBehavior:
    """Test fallback classification behavior."""

    def test_empty_task_description(self):
        """Empty description → P2 default."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify("", task_type="general")

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P2_MODERATE
        # Method can be keyword or fallback
        assert classification.method in ["keyword", "fallback"]

    def test_unknown_task_type(self):
        """Unknown task without clear keywords → P2 default."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Do something with the system",
            task_type="general"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.complexity == TaskComplexity.P2_MODERATE

    def test_no_keyword_match(self):
        """Task with no keyword match → P2 default."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Update the user interface",
            task_type="general"
        )

        assert result.is_ok()
        classification = result.unwrap()
        # Could be P2 or P3 depending on exact wording
        assert classification.complexity in [TaskComplexity.P2_MODERATE, TaskComplexity.P3_SIMPLE]


class TestVectorStoreIntegration:
    """Test VectorStore-based classification (Method 3)."""

    def test_vectorstore_not_available(self):
        """Classification works without VectorStore."""
        classifier = TaskComplexityClassifier(vector_store=None)

        result = classifier.classify(
            "Fix typo in README",
            task_type="documentation"
        )

        assert result.is_ok()
        classification = result.unwrap()
        # Should fall back to keyword method
        assert classification.complexity == TaskComplexity.P3_SIMPLE
        assert classification.method == "keyword"

    def test_vectorstore_with_mock(self):
        """VectorStore integration with mock."""

        class MockVectorStore:
            def search(self, query, namespace, limit):
                # Simulate finding similar P2 tasks
                return [
                    {
                        "content": {
                            "classified_complexity": "P2",
                            "confidence": 0.8,
                            "success": True
                        }
                    },
                    {
                        "content": {
                            "classified_complexity": "P2",
                            "confidence": 0.9,
                            "success": True
                        }
                    }
                ]

        classifier = TaskComplexityClassifier(vector_store=MockVectorStore())

        result = classifier.classify(
            "Implement user signup endpoint",
            task_type="feature_implementation"
        )

        assert result.is_ok()
        classification = result.unwrap()
        # VectorStore should influence classification
        assert classification.complexity == TaskComplexity.P2_MODERATE


class TestConfidence:
    """Test classification confidence scores."""

    def test_high_confidence_p3(self):
        """P3 classification with high confidence."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Fix typo in variable name",
            task_type="code_modification"
        )

        assert result.is_ok()
        classification = result.unwrap()
        assert classification.confidence >= 0.8

    def test_high_confidence_p1(self):
        """P1 classification with high confidence."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Create ADR for architectural design decisions",
            task_type="architecture"
        )

        assert result.is_ok()
        classification = result.unwrap()
        # Should match P1 keyword pattern (adr + create)
        assert classification.complexity == TaskComplexity.P1_COMPLEX
        assert classification.confidence >= 0.8

    def test_low_confidence_fallback(self):
        """Fallback classification with lower confidence."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify(
            "Update something in the system",
            task_type="general"
        )

        assert result.is_ok()
        classification = result.unwrap()
        # Fallback typically has lower confidence
        assert classification.confidence <= 0.6
