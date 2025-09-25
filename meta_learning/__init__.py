"""
MetaLearning System - Minimal viable implementation for recursive self-improvement.

Core principle: Every component adds measurable value to agent learning performance.
"""

__version__ = "0.1.0"

from .agent_registry import AgentRegistry, Agent, AgentInstance, AIQEvent

# Flask-dependent imports are optional
try:
    from .registry_api import create_app
    __all__ = ["AgentRegistry", "Agent", "AgentInstance", "AIQEvent", "create_app"]
except ImportError:
    # Flask not available - registry API won't be available
    __all__ = ["AgentRegistry", "Agent", "AgentInstance", "AIQEvent"]