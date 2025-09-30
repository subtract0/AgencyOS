"""
Type definitions for DSPy agents.

This module provides type-safe definitions to replace Dict[str, Any] usage
in compliance with Agency's constitutional requirement to avoid Any types.
"""

from typing import TypedDict, Union, List, Optional, Literal
from pydantic import BaseModel


class DSPyContext(TypedDict, total=False):
    """Type-safe context for DSPy operations."""
    repository_root: str
    current_task: str
    agent_name: str
    memory_store: Optional[object]
    vector_store: Optional[object]
    historical_patterns: List[dict]
    quality_standards: List[str]
    constitutional_requirements: List[str]
    test_results: dict
    implementation_notes: str
    error_details: Optional[List[str]]
    metadata: dict


class AgentContext(TypedDict, total=False):
    """Type-safe agent context."""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    memory: Optional[object]
    vector_store: Optional[object]
    session_id: Optional[str]


class TestResults(TypedDict, total=False):
    """Type-safe test results."""
    passed: int
    failed: int
    skipped: int
    errors: List[str]
    duration: float
    coverage: Optional[float]


class ImplementationContext(TypedDict, total=False):
    """Type-safe implementation context."""
    files_modified: List[str]
    tests_added: List[str]
    dependencies_added: List[str]
    breaking_changes: bool
    migration_notes: Optional[str]


class PlannerContext(TypedDict, total=False):
    """Type-safe planner context."""
    specification_path: Optional[str]
    plan_type: Literal["feature", "bugfix", "refactor", "test"]
    priority: Literal["low", "medium", "high", "critical"]
    estimated_effort: Optional[str]
    dependencies: List[str]
    risks: List[str]


class AuditContext(TypedDict, total=False):
    """Type-safe audit context."""
    target_paths: List[str]
    audit_type: Literal["security", "performance", "quality", "compliance"]
    severity_threshold: Literal["low", "medium", "high", "critical"]
    findings: List[dict]
    recommendations: List[str]


class LearningContext(TypedDict, total=False):
    """Type-safe learning context."""
    patterns_learned: List[dict]
    success_rate: float
    failure_reasons: List[str]
    improvements_suggested: List[str]
    knowledge_base_updated: bool


# Union type for all contexts
Context = Union[
    DSPyContext,
    AgentContext,
    TestResults,
    ImplementationContext,
    PlannerContext,
    AuditContext,
    LearningContext,
    dict  # Fallback for compatibility
]


# Export all type definitions
__all__ = [
    "DSPyContext",
    "AgentContext",
    "TestResults",
    "ImplementationContext",
    "PlannerContext",
    "AuditContext",
    "LearningContext",
    "Context",
]