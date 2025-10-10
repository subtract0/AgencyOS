"""Skill evolution tracking with 384-dimensional vectors.

Per Leap 3 Milestone 4: Track agent skill development over time using
exponential moving average (EMA) for continuous learning.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


@dataclass
class SkillDimension:
    """Named skill dimension with semantic meaning.

    Maps 384-dim vector indices to interpretable skill categories.
    """

    index: int
    name: str
    category: str  # "technical", "strategic", "collaboration", "quality"
    description: str


# Skill dimension mappings (96 per category × 4 categories = 384)
SKILL_DIMENSIONS = {
    # Technical Skills (0-95)
    "code_quality": SkillDimension(0, "code_quality", "technical", "Clean, maintainable code"),
    "test_coverage": SkillDimension(1, "test_coverage", "technical", "Comprehensive testing"),
    "type_safety": SkillDimension(2, "type_safety", "technical", "Strict typing, no Any"),
    "error_handling": SkillDimension(3, "error_handling", "technical", "Result pattern usage"),
    "performance": SkillDimension(4, "performance", "technical", "Optimization, efficiency"),

    # Strategic Skills (96-191)
    "architectural_design": SkillDimension(96, "architectural_design", "strategic", "System architecture"),
    "adr_creation": SkillDimension(97, "adr_creation", "strategic", "ADR documentation"),
    "planning": SkillDimension(98, "planning", "strategic", "Task breakdown, planning"),
    "complexity_estimation": SkillDimension(99, "complexity_estimation", "strategic", "Accurate estimates"),

    # Collaboration Skills (192-287)
    "communication": SkillDimension(192, "communication", "collaboration", "Clear communication"),
    "context_awareness": SkillDimension(193, "context_awareness", "collaboration", "Understanding context"),
    "multi_agent_coordination": SkillDimension(194, "multi_agent_coordination", "collaboration", "Agent coordination"),

    # Quality Skills (288-383)
    "constitutional_compliance": SkillDimension(288, "constitutional_compliance", "quality", "Articles I-V"),
    "verification": SkillDimension(289, "verification", "quality", "100% test pass rate"),
    "learning": SkillDimension(290, "learning", "quality", "VectorStore usage"),
    "autonomy": SkillDimension(291, "autonomy", "quality", "Self-healing, adaptation"),
}


class SkillVector(BaseModel):
    """384-dimensional skill vector with exponential moving average.

    Tracks agent skill evolution over time across 4 categories:
    - Technical (code quality, testing, typing)
    - Strategic (architecture, planning, estimation)
    - Collaboration (communication, coordination)
    - Quality (compliance, verification, learning)

    Uses EMA for smooth skill progression that emphasizes recent performance
    while maintaining historical context.
    """

    model_config = ConfigDict(extra="forbid")

    agent_name: str
    session_id: str

    # 384-dim vector (numpy array serialized to list)
    vector: list[float] = Field(default_factory=lambda: [0.5] * 384)

    # EMA parameters
    alpha: float = Field(default=0.3, ge=0.0, le=1.0)  # Smoothing factor
    update_count: int = 0

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)

    # Aggregate metrics
    overall_skill_level: float = Field(default=0.5, ge=0.0, le=1.0)
    technical_skill: float = Field(default=0.5, ge=0.0, le=1.0)
    strategic_skill: float = Field(default=0.5, ge=0.0, le=1.0)
    collaboration_skill: float = Field(default=0.5, ge=0.0, le=1.0)
    quality_skill: float = Field(default=0.5, ge=0.0, le=1.0)

    def update_skill(
        self,
        skill_name: str,
        new_value: float,
        confidence: float = 1.0
    ) -> None:
        """Update a single skill dimension using EMA.

        Args:
            skill_name: Name of skill dimension (from SKILL_DIMENSIONS)
            new_value: New skill value (0.0-1.0)
            confidence: Confidence in measurement (0.0-1.0)

        Example:
            >>> sv = SkillVector(agent_name="coder", session_id="test")
            >>> sv.update_skill("code_quality", 0.9, confidence=0.85)
        """
        if skill_name not in SKILL_DIMENSIONS:
            raise ValueError(f"Unknown skill dimension: {skill_name}")

        dim = SKILL_DIMENSIONS[skill_name]
        index = dim.index

        # Weighted EMA: α_eff = α * confidence
        effective_alpha = self.alpha * confidence

        # EMA formula: V_new = α * new_value + (1 - α) * V_old
        old_value = self.vector[index]
        new_vector_value = (effective_alpha * new_value) + ((1 - effective_alpha) * old_value)

        self.vector[index] = new_vector_value
        self.update_count += 1
        self.last_updated = datetime.now()

        # Recalculate aggregate metrics
        self._update_aggregates()

    def update_from_task_result(
        self,
        task_type: str,
        success: bool,
        quality_score: float,
        complexity: str,
        duration_ms: float,
        confidence: float = 0.8
    ) -> None:
        """Update skill vector from task completion result.

        Args:
            task_type: Type of task (e.g., "code", "test", "architecture")
            success: Whether task succeeded
            quality_score: Quality assessment (0.0-1.0)
            complexity: Task complexity ("P1", "P2", "P3")
            duration_ms: Task duration
            confidence: Confidence in assessment

        Example:
            >>> sv = SkillVector(agent_name="coder", session_id="test")
            >>> sv.update_from_task_result(
            ...     task_type="code",
            ...     success=True,
            ...     quality_score=0.9,
            ...     complexity="P2",
            ...     duration_ms=5000.0
            ... )
        """
        # Map task type to skill dimensions
        skill_mappings = {
            "code": ["code_quality", "type_safety", "error_handling"],
            "test": ["test_coverage", "verification"],
            "architecture": ["architectural_design", "adr_creation"],
            "planning": ["planning", "complexity_estimation"],
            "coordination": ["multi_agent_coordination", "communication"],
        }

        skills_to_update = skill_mappings.get(task_type, ["code_quality"])

        # Success bonus
        success_multiplier = 1.0 if success else 0.7

        # Complexity multiplier (harder tasks = more skill gain)
        complexity_multipliers = {"P1": 1.2, "P2": 1.0, "P3": 0.8}
        complexity_mult = complexity_multipliers.get(complexity, 1.0)

        # Calculate final skill value
        final_value = quality_score * success_multiplier * complexity_mult

        # Clamp to [0, 1]
        final_value = max(0.0, min(1.0, final_value))

        # Update each mapped skill
        for skill_name in skills_to_update:
            if skill_name in SKILL_DIMENSIONS:
                self.update_skill(skill_name, final_value, confidence=confidence)

        # Update meta-skills (constitutional compliance, learning)
        if success:
            self.update_skill("constitutional_compliance", quality_score, confidence=0.7)
            self.update_skill("learning", 0.8, confidence=0.5)

    def _update_aggregates(self) -> None:
        """Recalculate aggregate skill metrics from vector."""
        # Convert to numpy for easier slicing
        vec = np.array(self.vector)

        # Category averages
        self.technical_skill = float(np.mean(vec[0:96]))
        self.strategic_skill = float(np.mean(vec[96:192]))
        self.collaboration_skill = float(np.mean(vec[192:288]))
        self.quality_skill = float(np.mean(vec[288:384]))

        # Overall average
        self.overall_skill_level = float(np.mean(vec))

    def get_skill_level(self, skill_name: str) -> float:
        """Get current level for a skill dimension.

        Args:
            skill_name: Name of skill dimension

        Returns:
            Current skill level (0.0-1.0)
        """
        if skill_name not in SKILL_DIMENSIONS:
            raise ValueError(f"Unknown skill dimension: {skill_name}")

        dim = SKILL_DIMENSIONS[skill_name]
        return self.vector[dim.index]

    def get_top_skills(self, n: int = 5) -> list[tuple[str, float]]:
        """Get top N skills by current level.

        Args:
            n: Number of top skills to return

        Returns:
            List of (skill_name, level) tuples
        """
        skills = [(name, self.vector[dim.index]) for name, dim in SKILL_DIMENSIONS.items()]
        skills.sort(key=lambda x: x[1], reverse=True)
        return skills[:n]

    def get_weakest_skills(self, n: int = 5) -> list[tuple[str, float]]:
        """Get bottom N skills by current level (areas for improvement).

        Args:
            n: Number of weakest skills to return

        Returns:
            List of (skill_name, level) tuples
        """
        skills = [(name, self.vector[dim.index]) for name, dim in SKILL_DIMENSIONS.items()]
        skills.sort(key=lambda x: x[1])
        return skills[:n]

    def calculate_skill_growth(self, other: "SkillVector") -> dict[str, float]:
        """Calculate skill growth compared to another vector.

        Args:
            other: Previous SkillVector to compare against

        Returns:
            Dict of skill_name → growth_percent
        """
        growth = {}

        for skill_name, dim in SKILL_DIMENSIONS.items():
            old_value = other.vector[dim.index]
            new_value = self.vector[dim.index]

            if old_value > 0:
                growth_percent = ((new_value - old_value) / old_value) * 100
            else:
                growth_percent = 0.0

            growth[skill_name] = growth_percent

        return growth

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary (for storage)."""
        return {
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "vector": self.vector,
            "alpha": self.alpha,
            "update_count": self.update_count,
            "last_updated": self.last_updated.isoformat(),
            "created_at": self.created_at.isoformat(),
            "overall_skill_level": self.overall_skill_level,
            "technical_skill": self.technical_skill,
            "strategic_skill": self.strategic_skill,
            "collaboration_skill": self.collaboration_skill,
            "quality_skill": self.quality_skill,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillVector":
        """Deserialize from dictionary."""
        # Parse datetime strings
        if isinstance(data.get("last_updated"), str):
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        return cls(**data)

    def save_to_vectorstore(self, vector_store: Any) -> None:
        """Save skill vector to VectorStore (Article IV).

        Args:
            vector_store: VectorStore instance
        """
        key = f"skill_vector_{self.agent_name}_{self.session_id}"

        content = self.to_dict()

        vector_store.add_memory(
            key,
            content,
            tags=[
                "skill_vector",
                f"agent:{self.agent_name}",
                f"session:{self.session_id}",
                "leap_3_m4"
            ],
            namespace="skill_evolution"
        )

    @classmethod
    def load_from_vectorstore(
        cls,
        vector_store: Any,
        agent_name: str,
        session_id: str
    ) -> "SkillVector | None":
        """Load skill vector from VectorStore.

        Args:
            vector_store: VectorStore instance
            agent_name: Agent name
            session_id: Session identifier

        Returns:
            SkillVector if found, None otherwise
        """
        key = f"skill_vector_{agent_name}_{session_id}"

        try:
            results = vector_store.search(
                query=key,
                namespace="skill_evolution",
                limit=1
            )

            if results:
                content = results[0].get("content", {})
                return cls.from_dict(content)

        except Exception:
            pass

        return None


class SkillEvolutionTracker:
    """Track skill evolution across multiple sessions.

    Maintains historical skill vectors and computes growth metrics.
    """

    def __init__(self, agent_name: str, vector_store: Any):
        """Initialize tracker.

        Args:
            agent_name: Agent name to track
            vector_store: VectorStore for persistence
        """
        self.agent_name = agent_name
        self.vector_store = vector_store
        self.history: list[SkillVector] = []

    def record_session(
        self,
        session_id: str,
        skill_vector: SkillVector
    ) -> None:
        """Record skill vector for a session.

        Args:
            session_id: Session identifier
            skill_vector: SkillVector for this session
        """
        skill_vector.save_to_vectorstore(self.vector_store)
        self.history.append(skill_vector)

    def get_skill_trend(
        self,
        skill_name: str,
        window_size: int = 10
    ) -> list[float]:
        """Get skill trend over recent sessions.

        Args:
            skill_name: Skill dimension name
            window_size: Number of recent sessions

        Returns:
            List of skill levels (most recent first)
        """
        if skill_name not in SKILL_DIMENSIONS:
            raise ValueError(f"Unknown skill: {skill_name}")

        dim = SKILL_DIMENSIONS[skill_name]

        # Get recent vectors
        recent = self.history[-window_size:]

        return [sv.vector[dim.index] for sv in recent]

    def calculate_velocity(self, skill_name: str) -> float:
        """Calculate skill improvement velocity (change per session).

        Args:
            skill_name: Skill dimension name

        Returns:
            Average change per session (positive = improving)
        """
        trend = self.get_skill_trend(skill_name, window_size=10)

        if len(trend) < 2:
            return 0.0

        # Linear regression slope
        x = np.arange(len(trend))
        y = np.array(trend)

        # Slope = Cov(x, y) / Var(x)
        slope = np.cov(x, y)[0, 1] / np.var(x) if np.var(x) > 0 else 0.0

        return float(slope)

    def generate_skill_report(self) -> dict[str, Any]:
        """Generate comprehensive skill evolution report.

        Returns:
            Dict with skill metrics, trends, and insights
        """
        if not self.history:
            return {"error": "No skill history available"}

        current = self.history[-1]

        # Calculate growth from first to last
        if len(self.history) > 1:
            first = self.history[0]
            growth = current.calculate_skill_growth(first)
        else:
            growth = {}

        # Top improving skills
        improving = sorted(growth.items(), key=lambda x: x[1], reverse=True)[:5]

        # Top declining skills
        declining = sorted(growth.items(), key=lambda x: x[1])[:5]

        return {
            "agent_name": self.agent_name,
            "sessions_tracked": len(self.history),
            "current_overall_skill": current.overall_skill_level,
            "current_breakdown": {
                "technical": current.technical_skill,
                "strategic": current.strategic_skill,
                "collaboration": current.collaboration_skill,
                "quality": current.quality_skill,
            },
            "top_skills": current.get_top_skills(5),
            "areas_for_improvement": current.get_weakest_skills(5),
            "most_improved_skills": improving,
            "declining_skills": declining,
            "update_count": current.update_count,
            "last_updated": current.last_updated.isoformat(),
        }
