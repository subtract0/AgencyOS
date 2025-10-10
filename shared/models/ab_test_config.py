"""
A/B Test Configuration for ML Model Routing.

Provides deterministic hash-based routing for A/B testing ML models.

Constitutional Compliance:
- Article III: Automated routing (no manual overrides)
- Article IV: VectorStore integration (routing decisions logged)
- Law #2: Strict typing (Pydantic model)

Author: QualityEnforcer
Date: 2025-10-10
"""

import hashlib

from pydantic import BaseModel, Field


class ABTestConfig(BaseModel):
    """
    A/B test configuration for deterministic ML model routing.

    Uses hash-based routing to ensure consistent routing for same task_id.
    Critical for A/B rollout validation (prevents routing instability).

    Attributes:
        enabled: Whether A/B testing is active
        ml_percentage: Percentage of traffic routed to ML model (0-100)
        random_seed: Seed for deterministic hashing
    """

    enabled: bool = Field(..., description="Whether A/B testing is active")
    ml_percentage: int = Field(
        ..., ge=0, le=100, description="Percentage of traffic to ML model (0-100)"
    )
    random_seed: int = Field(42, description="Seed for deterministic hashing")

    def should_use_ml(self, task_id: str) -> bool:
        """
        Determine if task should use ML model via deterministic hash.

        Hash-based routing ensures:
        - Same task_id always gets same routing decision
        - Stable A/B split (no routing drift)
        - Statistical validity (uniform distribution)

        Args:
            task_id: Unique task identifier

        Returns:
            True if task should use ML model, False otherwise
        """
        if not self.enabled:
            return False

        # Deterministic hash: task_id + seed → 0-99 bucket
        hash_input = f"{task_id}:{self.random_seed}"
        hash_digest = hashlib.md5(hash_input.encode()).hexdigest()
        bucket = int(hash_digest[:8], 16) % 100  # 0-99 bucket

        # ML if bucket < ml_percentage (e.g., 10% → buckets 0-9 use ML)
        return bucket < self.ml_percentage
