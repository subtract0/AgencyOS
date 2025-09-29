"""
DSPy Signatures for Agency Agents

This module defines the input/output signatures for all DSPy agents,
ensuring type safety and consistent interfaces.
"""

from .base import (
    CodeTaskSignature,
    PlanningSignature,
    ImplementationSignature,
    VerificationSignature,
    AuditSignature,
    PrioritizationSignature,
    ReportSignature,
    UnderstandingSignature,
    StrategySignature,
    TaskBreakdownSignature,
    PatternExtractionSignature,
    ConsolidationSignature,
    StorageSignature,
    TaskRoutingSignature,
    CoordinationSignature,
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