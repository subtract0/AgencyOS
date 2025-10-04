"""
Trinity Protocol Core - Production-Ready Modules

All modules in this directory meet production criteria:
- 100% test coverage
- Strict Pydantic typing (no Dict[Any, Any])
- Constitutional compliance (all 5 articles)
- Result<T,E> error handling
- Functions <50 lines
- Comprehensive documentation
"""

from trinity_protocol.core.architect import ArchitectAgent
from trinity_protocol.core.executor import (
    ExecutionPlan,
    ExecutorAgent,
    SubAgentResult,
    SubAgentType,
)
from trinity_protocol.core.orchestrator import (
    TrinityBus,
    TrinityMessage,
    TrinityOrchestrator,
    initialize_trinity,
)
from trinity_protocol.core.witness import Signal, WitnessAgent

__all__ = [
    # Executor
    "ExecutorAgent",
    "SubAgentType",
    "SubAgentResult",
    "ExecutionPlan",
    # Architect
    "ArchitectAgent",
    # Witness
    "WitnessAgent",
    "Signal",
    # Orchestrator
    "TrinityOrchestrator",
    "TrinityBus",
    "TrinityMessage",
    "initialize_trinity",
]
