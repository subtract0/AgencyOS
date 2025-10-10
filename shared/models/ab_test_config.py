"""
ABTestConfig model for ML vs rules-based routing.

Provides deterministic A/B testing for gradual ML rollout. Uses hash-based
routing to consistently assign tasks to ML or rules-based classification.

Constitutional compliance:
- Article I: Complete context (deterministic routing for reproducibility)
- Article II: 100% verification (strict typing, Pydantic validation)
- Article IV: VectorStore integration (A/B test results logged)
- Article V: Spec-driven (follows spec-007-phase3-ml-inference.md)

Reference: specs/spec-007-phase3-ml-inference.md Section 3.2
Author: CodeAgent
Date: 2025-10-10
"""

import hashlib

from pydantic import BaseModel, Field


class ABTestConfig(BaseModel):
    """
    A/B testing configuration for ML rollout.

    Provides deterministic hash-based routing to gradually introduce ML
    classification while maintaining rules-based fallback. Same task_id
    always routes to same method (ML or rules).

    Fields:
        enabled: Enable/disable A/B testing
        ml_percentage: Percentage of tasks routed to ML (0-100)
        random_seed: Seed for hash-based routing (determinism)

    Example:
        >>> # 50% ML, 50% rules (default)
        >>> config = ABTestConfig()
        >>> config.should_use_ml("task-123")  # Deterministic
        True
        >>> config.should_use_ml("task-123")  # Same result
        True
        >>>
        >>> # 100% ML rollout
        >>> config = ABTestConfig(ml_percentage=100)
        >>> config.should_use_ml("any-task")
        True
        >>>
        >>> # Disable A/B testing (all rules-based)
        >>> config = ABTestConfig(enabled=False)
        >>> config.should_use_ml("any-task")
        False
    """

    enabled: bool = Field(
        True,
        description="Enable A/B testing (False = use rules-based only)",
    )

    ml_percentage: int = Field(
        50,
        ge=0,
        le=100,
        description="Percentage of tasks routed to ML (0-100)",
    )

    random_seed: int = Field(
        42,
        description="Seed for hash-based routing (determinism)",
    )

    def should_use_ml(self, task_id: str) -> bool:
        """
        Determine if task should use ML classification.

        Uses deterministic hash-based routing to ensure same task_id
        always routes to same method (ML or rules). This enables:
        - Reproducible results (same task_id = same route)
        - Gradual ML rollout (control via ml_percentage)
        - A/B testing analysis (compare ML vs rules performance)

        Algorithm:
        1. If not enabled, return False (rules-based only)
        2. Hash task_id with MD5 + random_seed
        3. Convert hash to integer (0-99)
        4. Return True if hash % 100 < ml_percentage

        Args:
            task_id: Unique task identifier

        Returns:
            True if task should use ML, False for rules-based

        Example:
            >>> config = ABTestConfig(enabled=True, ml_percentage=50)
            >>> config.should_use_ml("task-123")  # Deterministic
            True
            >>> config.should_use_ml("task-123")  # Same result
            True
            >>> config.should_use_ml("task-456")  # Different task
            False  # Hash % 100 >= 50
        """
        if not self.enabled:
            return False

        # Hash task_id with seed for deterministic routing
        combined_input = f"{task_id}-{self.random_seed}"
        hash_digest = hashlib.md5(combined_input.encode()).hexdigest()

        # Convert hash to integer (0-99)
        hash_int = int(hash_digest, 16) % 100

        # Route to ML if hash < ml_percentage
        return hash_int < self.ml_percentage

    def to_dict(self) -> dict:
        """
        Export A/B test config to dictionary.

        Used for:
        - JSON serialization (config persistence)
        - VectorStore storage (A/B test metadata)
        - Dashboard display (current config)

        Returns:
            Dictionary with all fields

        Example:
            >>> config = ABTestConfig(ml_percentage=75)
            >>> config.to_dict()
            {'enabled': True, 'ml_percentage': 75, 'random_seed': 42}
        """
        return {
            "enabled": self.enabled,
            "ml_percentage": self.ml_percentage,
            "random_seed": self.random_seed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ABTestConfig":
        """
        Deserialize A/B test config from dictionary.

        Used for:
        - JSON deserialization (config loading)
        - VectorStore retrieval (historical configs)

        Args:
            data: Dictionary with config fields (all optional with defaults)

        Returns:
            ABTestConfig instance

        Example:
            >>> data = {"enabled": True, "ml_percentage": 80}
            >>> config = ABTestConfig.from_dict(data)
            >>> config.ml_percentage
            80
            >>> config.random_seed  # Uses default
            42
        """
        return cls(**data)
