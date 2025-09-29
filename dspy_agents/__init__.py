"""
DSPy Agents Module for AgencyOS

This module provides the DSPy-based implementation of Agency agents,
migrating from static markdown instructions to dynamic, optimizable modules.
"""

from typing import TYPE_CHECKING

__version__ = "0.1.0"

if TYPE_CHECKING:
    from .registry import AgentRegistry
    from .modules.code_agent import DSPyCodeAgent

__all__ = [
    "AgentRegistry",
    "DSPyCodeAgent",
]