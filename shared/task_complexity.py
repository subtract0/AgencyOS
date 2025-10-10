"""Task complexity classification for adaptive model routing.

Per ADR-024 and Leap 3 Milestone 3: Classify tasks as P1/P2/P3 for cost-optimized routing.
"""

import ast
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from shared.type_definitions.result import Err, Ok, Result


class TaskComplexity(str, Enum):
    """Task complexity classification for model routing.

    Per ADR-024:
    - P1: Complex architectural/strategic tasks → gpt-5 ($4/1M tokens)
    - P2: Moderate implementation/bug fixes → gpt-4o ($1.50/1M tokens)
    - P3: Simple formatting/proven patterns → local model ($0)
    """

    P1_COMPLEX = "P1"
    P2_MODERATE = "P2"
    P3_SIMPLE = "P3"

    @property
    def estimated_cost_per_1k_tokens(self) -> float:
        """Estimated cost per 1,000 tokens for this complexity tier."""
        return {
            "P1": 0.004,  # gpt-5: $4/1M tokens
            "P2": 0.0015,  # gpt-4o: $1.50/1M tokens
            "P3": 0.0,  # local model: FREE
        }[self.value]

    @property
    def recommended_model(self) -> str:
        """Default model for this complexity tier."""
        use_local = os.getenv("USE_LOCAL_MODEL", "true").lower() == "true"

        models = {
            "P1": "gpt-5",
            "P2": "gpt-4o",
            "P3": "ollama/qwen3-coder:30b" if use_local else "gpt-4o-mini",
        }
        return models[self.value]


class RoutingDecision(BaseModel):
    """Model routing decision with cost and performance metrics."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_description: str
    task_type: str

    # Classification results
    complexity: TaskComplexity
    classification_method: str  # "keyword", "ast", "vectorstore", "hybrid"
    classification_confidence: float = Field(ge=0.0, le=1.0)

    # Routing results
    selected_model: str
    fallback_used: bool = False
    environment_override: bool = False

    # Performance metrics
    routing_latency_ms: float
    classification_latency_ms: float
    vectorstore_query_latency_ms: float | None = None

    # Cost prediction
    estimated_cost_usd: float
    estimated_tokens: int

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_key: str
    session_id: str

    def to_telemetry_event(self) -> dict[str, Any]:
        """Convert to telemetry event for logging."""
        return {
            "event_type": "model_routing_decision",
            "task_id": self.task_id,
            "complexity": self.complexity.value,
            "model": self.selected_model,
            "cost_estimate_usd": self.estimated_cost_usd,
            "routing_latency_ms": self.routing_latency_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ClassificationResult:
    """Result of task complexity classification."""

    complexity: TaskComplexity
    method: str
    confidence: float
    details: dict[str, Any]


class TaskComplexityClassifier:
    """Classify task complexity using 3-method algorithm.

    Methods (in order):
    1. Keyword detection (fast, rule-based)
    2. AST analysis (for code modification tasks)
    3. VectorStore pattern matching (Article IV - learning from history)

    Per ADR-024 and constitution Article IV.
    """

    # P3 Simple patterns (typos, formatting, proven patterns)
    P3_KEYWORDS = [
        r"\b(typo|format|docstring|comment|readme|copyright)\b",
        r"\b(remove|delete|clean)\b.*\b(unused|dead code|import)\b",
        r"\b(update|add|fix)\b.*\b(comment|doc|documentation)\b",
        r"\b(rename|move)\b.*\b(variable|function|file)\b",
        r"\b(whitespace|indent|trailing)\b",
        r"\b(black|prettier|autopep8)\b",  # Formatters
    ]

    # P1 Complex patterns (architecture, ADRs, critical systems)
    P1_KEYWORDS = [
        r"\b(design|architect|adr|constitutional|compliance)\b",
        r"\b(consensus|distributed|multi-agent|coordination)\b",
        r"\b(autonomous|healing|critical|security)\b",
        r"\b(create|implement)\b.*\b(adr|specification|architecture)\b",
        r"\b(strategic|planning|roadmap)\b",
        r"\b(system design|high-level design)\b",
    ]

    def __init__(self, vector_store: Any | None = None):
        """Initialize classifier.

        Args:
            vector_store: VectorStore for pattern matching (Article IV).
                         If None, will use keyword/AST only.
        """
        self.vector_store = vector_store

        # Compile regex patterns once
        self.p3_patterns = [re.compile(p, re.IGNORECASE) for p in self.P3_KEYWORDS]
        self.p1_patterns = [re.compile(p, re.IGNORECASE) for p in self.P1_KEYWORDS]

    def classify(
        self, task_description: str, task_type: str = "general"
    ) -> Result[ClassificationResult, str]:
        """Classify task complexity using 3-method algorithm.

        Args:
            task_description: Task description text
            task_type: Task type (e.g., "code_modification", "architecture", "general")

        Returns:
            Result containing ClassificationResult or error
        """
        try:
            # Method 1: Keyword detection (fast path)
            keyword_result = self._classify_by_keywords(task_description)
            if keyword_result.confidence >= 0.8:
                return Ok(keyword_result)

            # Method 2: AST analysis (for code modification)
            if task_type == "code_modification":
                ast_result = self._classify_by_ast(task_description)
                if ast_result.confidence >= 0.7:
                    return Ok(ast_result)

            # Method 3: VectorStore pattern matching (Article IV)
            if self.vector_store is not None:
                vs_result = self._classify_by_vectorstore(task_description)
                if vs_result.confidence >= 0.6:
                    return Ok(vs_result)

            # Hybrid: Combine methods
            if keyword_result.confidence >= 0.5:
                return Ok(keyword_result)

            # Fallback: P2 moderate (safest default)
            return Ok(
                ClassificationResult(
                    complexity=TaskComplexity.P2_MODERATE,
                    method="fallback",
                    confidence=0.5,
                    details={"reason": "No high-confidence match, using P2 default"},
                )
            )

        except Exception as e:
            return Err(f"Classification failed: {e}")

    def _classify_by_keywords(self, task_description: str) -> ClassificationResult:
        """Method 1: Keyword-based classification."""
        # Check P3 (simple) first
        for pattern in self.p3_patterns:
            if pattern.search(task_description):
                return ClassificationResult(
                    complexity=TaskComplexity.P3_SIMPLE,
                    method="keyword",
                    confidence=0.9,
                    details={"matched_pattern": pattern.pattern},
                )

        # Check P1 (complex)
        for pattern in self.p1_patterns:
            if pattern.search(task_description):
                return ClassificationResult(
                    complexity=TaskComplexity.P1_COMPLEX,
                    method="keyword",
                    confidence=0.85,
                    details={"matched_pattern": pattern.pattern},
                )

        # No match → P2 moderate (with lower confidence)
        return ClassificationResult(
            complexity=TaskComplexity.P2_MODERATE,
            method="keyword",
            confidence=0.5,
            details={"reason": "No P1/P3 keyword match"},
        )

    def _classify_by_ast(self, task_description: str) -> ClassificationResult:
        """Method 2: AST-based complexity analysis.

        Estimates cyclomatic complexity from code snippets in task description.
        """
        try:
            # Extract code blocks from task description
            code_blocks = re.findall(r"```python\n(.*?)\n```", task_description, re.DOTALL)

            if not code_blocks:
                # No code blocks → use keyword method
                return ClassificationResult(
                    complexity=TaskComplexity.P2_MODERATE,
                    method="ast",
                    confidence=0.4,
                    details={"reason": "No code blocks found"},
                )

            # Parse first code block
            code = code_blocks[0]
            tree = ast.parse(code)

            # Estimate cyclomatic complexity
            complexity_score = self._estimate_complexity(tree)

            if complexity_score > 10:
                return ClassificationResult(
                    complexity=TaskComplexity.P1_COMPLEX,
                    method="ast",
                    confidence=0.8,
                    details={"complexity_score": complexity_score},
                )
            elif complexity_score > 5:
                return ClassificationResult(
                    complexity=TaskComplexity.P2_MODERATE,
                    method="ast",
                    confidence=0.75,
                    details={"complexity_score": complexity_score},
                )
            else:
                return ClassificationResult(
                    complexity=TaskComplexity.P3_SIMPLE,
                    method="ast",
                    confidence=0.7,
                    details={"complexity_score": complexity_score},
                )

        except SyntaxError:
            # Code parsing failed → fallback to keyword
            return ClassificationResult(
                complexity=TaskComplexity.P2_MODERATE,
                method="ast",
                confidence=0.3,
                details={"reason": "Code parsing failed"},
            )

    def _estimate_complexity(self, tree: ast.AST) -> int:
        """Estimate cyclomatic complexity from AST.

        Simplified McCabe complexity: count decision points.
        """
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            # Decision points
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _classify_by_vectorstore(self, task_description: str) -> ClassificationResult:
        """Method 3: VectorStore pattern matching (Article IV).

        Query VectorStore for similar past tasks and use historical classifications.
        """
        if self.vector_store is None:
            return ClassificationResult(
                complexity=TaskComplexity.P2_MODERATE,
                method="vectorstore",
                confidence=0.0,
                details={"reason": "VectorStore not available"},
            )

        try:
            start = time.perf_counter()

            # Query VectorStore for similar tasks
            similar_tasks = self.vector_store.search(
                query=task_description, namespace="task_classification", limit=5
            )

            query_latency_ms = (time.perf_counter() - start) * 1000

            if not similar_tasks:
                return ClassificationResult(
                    complexity=TaskComplexity.P2_MODERATE,
                    method="vectorstore",
                    confidence=0.3,
                    details={
                        "reason": "No similar tasks found",
                        "query_latency_ms": query_latency_ms,
                    },
                )

            # Weighted average of historical classifications
            complexity_scores = {"P1": 0.0, "P2": 0.0, "P3": 0.0}
            total_weight = 0.0

            for task in similar_tasks:
                content = task.get("content", {})
                complexity = content.get("classified_complexity", "P2")
                confidence = content.get("confidence", 0.5)
                success = content.get("success", True)

                # Weight by confidence and success
                weight = confidence * (1.0 if success else 0.5)
                complexity_scores[complexity] += weight
                total_weight += weight

            # Normalize scores
            if total_weight > 0:
                for key in complexity_scores:
                    complexity_scores[key] /= total_weight

            # Select highest scoring complexity
            best_complexity = max(complexity_scores, key=complexity_scores.get)
            best_confidence = complexity_scores[best_complexity]

            return ClassificationResult(
                complexity=TaskComplexity(best_complexity),
                method="vectorstore",
                confidence=min(best_confidence, 0.95),  # Cap at 0.95
                details={
                    "similar_tasks_found": len(similar_tasks),
                    "complexity_scores": complexity_scores,
                    "query_latency_ms": query_latency_ms,
                },
            )

        except Exception as e:
            return ClassificationResult(
                complexity=TaskComplexity.P2_MODERATE,
                method="vectorstore",
                confidence=0.2,
                details={"error": str(e)},
            )
