"""
Learning Agent Tools

Core tools for analyzing session data, extracting insights, consolidating learnings,
and storing knowledge in the VectorStore for future retrieval and application.

Tools:
- AnalyzeSession: Analyze session transcripts to extract patterns and insights
- ExtractInsights: Extract actionable insights from analyzed session data
- ConsolidateLearning: Consolidate insights into structured learning objects
- StoreKnowledge: Store consolidated learnings in the VectorStore
"""

from .analyze_session import AnalyzeSession
from .extract_insights import ExtractInsights
from .consolidate_learning import ConsolidateLearning
from .store_knowledge import StoreKnowledge

__all__ = [
    "AnalyzeSession",
    "ExtractInsights",
    "ConsolidateLearning",
    "StoreKnowledge"
]

# Tool workflow documentation
WORKFLOW_DESCRIPTION = """
Learning Agent Tool Workflow:

1. AnalyzeSession: Parse session transcript files to identify patterns
   - Input: Session file path (from /logs/sessions/)
   - Output: Structured analysis JSON with tool usage, errors, workflows

2. ExtractInsights: Extract actionable insights from analysis
   - Input: Analysis JSON from AnalyzeSession
   - Output: Insights JSON with categorized learning opportunities

3. ConsolidateLearning: Structure insights into learning objects
   - Input: Insights JSON from ExtractInsights
   - Output: Standardized learning objects with metadata

4. StoreKnowledge: Store learnings in VectorStore
   - Input: Learning objects JSON from ConsolidateLearning
   - Output: Storage confirmation with IDs and statistics

Example Usage:
```python
# 1. Analyze a session
analysis = AnalyzeSession(session_file="session_20240101_120000.json").run()

# 2. Extract insights
insights = ExtractInsights(session_analysis=analysis, insight_type="auto").run()

# 3. Consolidate into learning objects
learnings = ConsolidateLearning(insights=insights, learning_type="auto").run()

# 4. Store in vector database
result = StoreKnowledge(learning=learnings, storage_mode="standard").run()
```
"""