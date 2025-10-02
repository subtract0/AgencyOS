"""Trinity Protocol - Multi-Agent Project Execution System

⚠️ DEPRECATION NOTICE ⚠️
The Trinity Protocol has been reorganized for production readiness.

Old import patterns are deprecated and will be removed after 2025-11-02 (30 days).

**Deprecated Imports** (still work, but show warnings):
- from trinity_protocol.executor_agent import ExecutorAgent
- from trinity_protocol.architect_agent import ArchitectAgent
- from trinity_protocol.witness_agent import WitnessAgent
- from trinity_protocol import orchestrator
- from trinity_protocol.models import Project, Pattern

**New Import Patterns** (recommended):
- from trinity_protocol.core import ExecutorAgent, ArchitectAgent, WitnessAgent, TrinityOrchestrator
- from trinity_protocol.core.models import Project, PatternType, HumanReviewRequest
- from trinity_protocol.experimental import AudioCapture, AmbientListener (⚠️ EXPERIMENTAL)
- from trinity_protocol.demos import demo_complete, demo_hitl, demo_preferences

See: trinity_protocol/README_REORGANIZATION.md for migration guide
"""

import warnings
from typing import Any

__version__ = "0.1.0"

# Production imports (new structure)
from trinity_protocol.core import (
    ExecutorAgent,
    ArchitectAgent,
    WitnessAgent,
    TrinityOrchestrator,
    Signal,
    SubAgentType,
    SubAgentResult,
    ExecutionPlan,
    TrinityBus,
    TrinityMessage,
    initialize_trinity,
)

# Backward compatibility exports (with deprecation warnings)
def __getattr__(name: str) -> Any:
    """Provide backward compatibility for old import patterns."""

    deprecated_map = {
        # Old module-level imports (for "from trinity_protocol import X" pattern)
        "executor_agent": ("trinity_protocol.core.executor", "ExecutorAgent"),
        "architect_agent": ("trinity_protocol.core.architect", "ArchitectAgent"),
        "witness_agent": ("trinity_protocol.core.witness", "WitnessAgent"),
        "orchestrator": ("trinity_protocol.core.orchestrator", "TrinityOrchestrator"),

        # Old model imports (for "from trinity_protocol import models" pattern)
        "models": ("trinity_protocol.core.models", "__module__"),

        # Direct class aliases (backward compat for "from trinity_protocol.executor_agent import ExecutorAgent")
        "ExecutorAgent": ("trinity_protocol.core.executor", "ExecutorAgent"),
        "ArchitectAgent": ("trinity_protocol.core.architect", "ArchitectAgent"),
        "WitnessAgent": ("trinity_protocol.core.witness", "WitnessAgent"),
    }

    if name in deprecated_map:
        module_path, attr_name = deprecated_map[name]

        # Determine recommendation based on what's being imported
        if attr_name == "__module__":
            recommendation = f"from {module_path} import Project, PatternType, ..."
        elif name in ["executor_agent", "architect_agent", "witness_agent", "orchestrator"]:
            recommendation = f"from trinity_protocol.core import {attr_name}"
        else:
            recommendation = f"from {module_path} import {attr_name}"

        warnings.warn(
            f"\n⚠️ DEPRECATION WARNING ⚠️\n"
            f"  Importing '{name}' from 'trinity_protocol' is deprecated.\n"
            f"  Recommended: {recommendation}\n"
            f"  Deprecated imports will be removed after 2025-11-02 (30 days).\n"
            f"  See: trinity_protocol/README_REORGANIZATION.md\n",
            DeprecationWarning,
            stacklevel=2
        )

        # Import and return the new module/class
        if attr_name == "__module__":
            # For models, return the module itself
            import importlib
            return importlib.import_module(module_path)
        else:
            # For classes, return the class
            import importlib
            module = importlib.import_module(module_path)
            return getattr(module, attr_name)

    raise AttributeError(f"module 'trinity_protocol' has no attribute '{name}'")


__all__ = [
    # Production core (recommended - no warnings)
    "ExecutorAgent",
    "ArchitectAgent",
    "WitnessAgent",
    "TrinityOrchestrator",
    "Signal",
    "SubAgentType",
    "SubAgentResult",
    "ExecutionPlan",
    "TrinityBus",
    "TrinityMessage",
    "initialize_trinity",
]
