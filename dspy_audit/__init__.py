"""
DSPy-based Audit and Refactoring System

A dynamic, self-optimizing audit system that learns from historical patterns
and improves with each execution.
"""

from .metrics import (
    audit_effectiveness_metric,
    constitutional_compliance_metric,
    refactoring_success_metric,
)
from .modules import (
    AuditRefactorModule,
    MultiAgentAuditModule,
)
from .optimize import (
    evaluate_module_performance,
    load_optimized_module,
    optimize_audit_module,
)
from .signatures import (
    AuditSignature,
    Issue,
    PrioritizationSignature,
    RefactoringPlan,
    RefactorSignature,
    VerificationSignature,
)

__version__ = "0.1.0"

__all__ = [
    # Signatures
    "AuditSignature",
    "PrioritizationSignature",
    "RefactorSignature",
    "VerificationSignature",
    "Issue",
    "RefactoringPlan",
    # Modules
    "AuditRefactorModule",
    "MultiAgentAuditModule",
    # Metrics
    "audit_effectiveness_metric",
    "refactoring_success_metric",
    "constitutional_compliance_metric",
    # Optimization
    "optimize_audit_module",
    "load_optimized_module",
    "evaluate_module_performance",
]
