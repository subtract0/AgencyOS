"""
DSPy Signatures for Agency Agents

This module defines the input/output signatures for all DSPy agents,
ensuring type safety and consistent interfaces.
"""

from .base import (
    AuditSignature,
    CodeTaskSignature,
    ConsolidationSignature,
    CoordinationSignature,
    ImplementationSignature,
    PatternExtractionSignature,
    PlanningSignature,
    PrioritizationSignature,
    ReportSignature,
    StorageSignature,
    StrategySignature,
    TaskBreakdownSignature,
    TaskRoutingSignature,
    UnderstandingSignature,
    VerificationSignature,
)

__all__ = [
    "CodeTaskSignature",
    "PlanningSignature",
    "ImplementationSignature",
    "VerificationSignature",
    "AuditSignature",
    "PrioritizationSignature",
    "ReportSignature",
    "UnderstandingSignature",
    "StrategySignature",
    "TaskBreakdownSignature",
    "PatternExtractionSignature",
    "ConsolidationSignature",
    "StorageSignature",
    "TaskRoutingSignature",
    "CoordinationSignature",
]
