"""Trinity Protocol - Multi-Agent Project Execution System

Production-ready multi-agent coordination for autonomous project execution.

**Architecture**:
```
trinity_protocol/
├─ core/              Production agents (Executor, Architect, Witness, Orchestrator)
├─ experimental/      Audio capture, ambient listening (⚠️ NOT production-ready)
└─ demos/            Demo scripts showing capabilities
```

**Import Patterns**:
```python
# Production agents
from trinity_protocol.core import (
    ExecutorAgent,
    ArchitectAgent,
    WitnessAgent,
    TrinityOrchestrator
)

# Shared components (reusable infrastructure)
from shared.cost_tracker import CostTracker, ModelTier
from shared.message_bus import MessageBus
from shared.persistent_store import PersistentStore
from shared.hitl_protocol import HITLProtocol, HumanReviewQueue
from shared.preference_learning import PreferenceLearner

# Models
from trinity_protocol.core.models import (
    Project,
    DetectedPattern,
    PatternType,
    HumanReviewRequest,
    ResponseRecord
)

# Experimental (⚠️ NOT production-ready)
from trinity_protocol.experimental import AudioCapture, AmbientListener
```

**Documentation**: See trinity_protocol/README.md
"""

__version__ = "0.2.0"

# Direct exports from core for convenience
from trinity_protocol.core import (
    ArchitectAgent,
    ExecutionPlan,
    ExecutorAgent,
    Signal,
    SubAgentResult,
    SubAgentType,
    TrinityBus,
    TrinityMessage,
    TrinityOrchestrator,
    WitnessAgent,
    initialize_trinity,
)

__all__ = [
    # Production core
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
