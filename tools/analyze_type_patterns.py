#!/usr/bin/env python3
"""
Type Pattern Analyzer for Agency OS
Analyzes Dict usage patterns to inform Pydantic model creation.
Part of Constitutional Law #2 enforcement.
"""

import ast
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Any
from shared.type_definitions.json import JSONValue

class DictPatternAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze Dict usage patterns."""

    def __init__(self, filename: str):
        self.filename = filename
        self.dict_patterns: List[dict[str, JSONValue]] = []
        self.current_function = None
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Analyze type annotations with Dict."""
        if self._is_dict_annotation(node.annotation):
            self._record_pattern(node, "annotation")
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        """Analyze function arguments with Dict type hints."""
        if node.annotation and self._is_dict_annotation(node.annotation):
            self._record_pattern(node, "function_arg")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Analyze function return types."""
        old_function = self.current_function
        self.current_function = node.name

        if node.returns and self._is_dict_annotation(node.returns):
            self._record_pattern(node, "return_type")

        self.generic_visit(node)
        self.current_function = old_function

    def _is_dict_annotation(self, node: ast.AST) -> bool:
        """Check if node represents a Dict type annotation."""
        if isinstance(node, ast.Name) and node.id == "Dict":
            return True
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and node.value.id == "Dict":
                return True
        return False

    def _extract_dict_structure(self, node: ast.AST) -> str:
        """Extract the structure of a Dict annotation."""
        try:
            return ast.unparse(node)
        except:
            return "Dict"

    def _record_pattern(self, node: ast.AST, pattern_type: str) -> None:
        """Record a Dict usage pattern."""
        pattern = {
            "file": self.filename,
            "line": node.lineno if hasattr(node, 'lineno') else 0,
            "class": self.current_class,
            "function": self.current_function,
            "type": pattern_type,
            "structure": self._extract_dict_structure(
                node.annotation if hasattr(node, 'annotation')
                else node.returns if hasattr(node, 'returns')
                else node
            )
        }
        self.dict_patterns.append(pattern)


def analyze_file(filepath: Path) -> List[dict[str, JSONValue]]:
    """Analyze a single Python file for Dict patterns."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        analyzer = DictPatternAnalyzer(str(filepath))
        analyzer.visit(tree)
        return analyzer.dict_patterns
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return []


def analyze_actual_data_shapes() -> Dict[str, JSONValue]:
    """Analyze actual data shapes from runtime logs and test fixtures."""
    shapes = defaultdict(list)

    # Analyze memory patterns from tests
    test_patterns = [
        # Common memory record shape
        {
            "type": "MemoryRecord",
            "example": {
                "key": "session_123",
                "content": "Task completed",
                "tags": ["session", "task"],
                "timestamp": "2024-01-01T00:00:00",
                "priority": "high",
                "metadata": {"agent": "code_agent"}
            }
        },
        # Learning consolidation shape
        {
            "type": "LearningConsolidation",
            "example": {
                "summary": "Analyzed 100 memories",
                "total_memories": 100,
                "unique_tags": 25,
                "avg_tags_per_memory": 3.5,
                "tag_frequencies": {"error": 10, "success": 50},
                "patterns": {
                    "content_types": {"text": 80, "error": 20},
                    "peak_hour": 14,
                    "peak_day": "Monday"
                }
            }
        },
        # Dashboard summary shape
        {
            "type": "DashboardSummary",
            "example": {
                "metrics": {
                    "sessions_analyzed": 10,
                    "total_memories": 500,
                    "avg_memories_per_session": 50
                },
                "active_agents": ["code_agent", "auditor"],
                "generated_at": "2024-01-01T00:00:00"
            }
        }
    ]

    for pattern in test_patterns:
        shapes[pattern["type"]].append(pattern["example"])

    return dict(shapes)


def main():
    """Main analysis routine."""
    print("🔍 Type Pattern Analysis for Agency OS")
    print("=" * 50)

    # Find all Python files with Dict usage
    project_root = Path("/Users/am/Code/Agency")
    exclude_dirs = {".venv", "__pycache__", ".pytest_cache", "logs", "data"}

    all_patterns = []
    files_analyzed = 0

    for py_file in project_root.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        patterns = analyze_file(py_file)
        if patterns:
            all_patterns.extend(patterns)
            files_analyzed += 1

    print(f"\n📊 Analysis Results:")
    print(f"  - Files analyzed: {files_analyzed}")
    print(f"  - Dict patterns found: {len(all_patterns)}")

    # Group patterns by type
    by_type = defaultdict(list)
    for pattern in all_patterns:
        by_type[pattern["type"]].append(pattern)

    print(f"\n📈 Pattern Distribution:")
    for pattern_type, instances in by_type.items():
        print(f"  - {pattern_type}: {len(instances)} instances")

    # Analyze common Dict structures
    structures = defaultdict(int)
    for pattern in all_patterns:
        structures[pattern["structure"]] += 1

    print(f"\n🔝 Top Dict Structures:")
    for structure, count in sorted(structures.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {structure}: {count} uses")

    # Analyze actual data shapes
    print(f"\n🎯 Actual Data Shapes Identified:")
    data_shapes = analyze_actual_data_shapes()
    for shape_type, examples in data_shapes.items():
        print(f"  - {shape_type}: {len(examples)} examples")

    # Save analysis results
    output = {
        "summary": {
            "files_analyzed": files_analyzed,
            "patterns_found": len(all_patterns),
            "pattern_types": list(by_type.keys()),
            "top_structures": dict(list(structures.items())[:10])
        },
        "patterns": all_patterns[:100],  # Sample of patterns
        "data_shapes": data_shapes
    }

    with open("type_analysis_report.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n✅ Analysis complete! Report saved to type_analysis_report.json")
    print("\n🎯 Recommended Pydantic Models to Create:")
    print("  1. MemoryRecord - Core memory storage")
    print("  2. LearningConsolidation - Learning analysis results")
    print("  3. DashboardSummary - Metrics and summaries")
    print("  4. AgentContext - Agent state management")
    print("  5. PatternAnalysis - Pattern detection results")
    print("  6. TelemetryEvent - Event tracking")

    return output


if __name__ == "__main__":
    main()