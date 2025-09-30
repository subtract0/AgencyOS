"""
Type definitions for DSPy Audit System.

This module provides type-safe definitions to replace dict[str, Any] usage
in compliance with Agency's constitutional requirement to avoid Any types.
"""

from typing import TypedDict, Optional, List, Union, Literal
from enum import Enum


class SeverityLevel(str, Enum):
    """Severity levels for audit findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CONSTITUTIONAL = "constitutional"


class ViolationDict(TypedDict, total=False):
    """Type-safe violation dictionary."""
    id: str
    severity: str
    type: str
    message: str
    file: Optional[str]
    line: Optional[int]
    constitutional_law: Optional[str]


class IssueDict(TypedDict, total=False):
    """Type-safe issue dictionary."""
    severity: str
    type: str
    message: str
    file: Optional[str]
    line: Optional[int]
    fix: Optional[str]
    priority: int


class AuditResultDict(TypedDict, total=False):
    """Type-safe audit result dictionary."""
    issues: List[IssueDict]
    fixes_applied: List[str]
    constitutional_compliance: bool
    summary: str


class ExampleDict(TypedDict, total=False):
    """Type-safe example dictionary for metrics."""
    known_violations: List[ViolationDict]
    code: str
    context: str
    expected_fixes: List[str]


class PredictionDict(TypedDict, total=False):
    """Type-safe prediction dictionary."""
    issues: List[IssueDict]
    fixes_applied: List[str]
    constitutional_compliance: bool
    reasoning: str


class ConfigDict(TypedDict, total=False):
    """Type-safe configuration dictionary."""
    lm_model: str
    temperature: float
    max_tokens: int
    retry_count: int
    audit_mode: str
    enforce_constitution: bool
    repository_root: str
    test_command: str
    lint_command: str


class AgentConfigDict(TypedDict, total=False):
    """Type-safe agent configuration dictionary."""
    name: str
    version: str
    capabilities: List[str]
    constitutional_laws: List[str]
    preferences: dict


class OptimizationConfigDict(TypedDict, total=False):
    """Type-safe optimization configuration."""
    metric_threshold: float
    max_bootstrapped_demos: int
    max_labeled_demos: int
    num_threads: int
    compile_module: bool


class AdapterConfigDict(TypedDict, total=False):
    """Type-safe adapter configuration."""
    backend: str
    model_name: str
    api_key: Optional[str]
    endpoint: Optional[str]
    max_retries: int
    timeout: int


# Union types for flexibility
MetricsExample = Union[ExampleDict, dict]
MetricsPrediction = Union[PredictionDict, dict]
AuditConfig = Union[ConfigDict, dict]
AgentConfig = Union[AgentConfigDict, dict]
OptimizationConfig = Union[OptimizationConfigDict, dict]
AdapterConfig = Union[AdapterConfigDict, dict]


__all__ = [
    "SeverityLevel",
    "ViolationDict",
    "IssueDict",
    "AuditResultDict",
    "ExampleDict",
    "PredictionDict",
    "ConfigDict",
    "AgentConfigDict",
    "OptimizationConfigDict",
    "AdapterConfigDict",
    "MetricsExample",
    "MetricsPrediction",
    "AuditConfig",
    "AgentConfig",
    "OptimizationConfig",
    "AdapterConfig",
]