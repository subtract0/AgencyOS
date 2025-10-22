"""
Parallel Development Rails - Make multi-agent coordination foolproof.

This package provides tools for safe parallel development across multiple
autonomous agents with automatic conflict detection and prevention.

Core Principle: "System suggests, user decides, system executes."

Components:
- ParallelWorkDetector: Detect parallel work across worktrees
- WorktreeManager: Manage worktree lifecycle safely
- ConflictAnalyzer: Predict conflict probability
- MergeGuardianLite: Orchestrate safe merges

Usage:
    from tools.parallel_dev import ParallelWorkDetector

    detector = ParallelWorkDetector()
    status = detector.scan_worktrees()
    conflicts = detector.analyze_conflicts(my_files)
"""

from .parallel_work_detector import ParallelWorkDetector, WorktreeInfo
from .worktree_manager import WorktreeManager

__all__ = [
    "ParallelWorkDetector",
    "WorktreeManager",
    "WorktreeInfo",
]

__version__ = "1.0.0"
