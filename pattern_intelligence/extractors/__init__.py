"""
Pattern Extractors - Mine coding patterns from various sources.

Extractors discover patterns from:
- Local codebase analysis
- GitHub repository mining
- Agency session transcripts
- Self-healing system data
"""

from .base_extractor import BasePatternExtractor
from .local_codebase import LocalCodebaseExtractor
from .github_extractor import GitHubPatternExtractor
from .session_extractor import SessionPatternExtractor

__all__ = [
    "BasePatternExtractor",
    "LocalCodebaseExtractor",
    "GitHubPatternExtractor",
    "SessionPatternExtractor",
]