"""
Pattern Intelligence Module

The Infinite Intelligence Amplifier - AI that gets smarter every day through
systematic extraction, storage, and application of coding patterns.

This module provides:
- CodingPattern: Core pattern data structure
- PatternStore: VectorStore-backed pattern repository
- Pattern Extractors: Mine patterns from code, commits, sessions
- PatternApplicator: Automatic pattern application
- MetaLearning: Recursive self-improvement
"""

from .coding_pattern import CodingPattern, ProblemContext, SolutionApproach, EffectivenessMetric
from .pattern_store import PatternStore, PatternSearchResult

__version__ = "1.0.0"

__all__ = [
    "CodingPattern",
    "ProblemContext",
    "SolutionApproach",
    "EffectivenessMetric",
    "PatternStore",
    "PatternSearchResult",
]