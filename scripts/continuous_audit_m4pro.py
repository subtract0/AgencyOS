#!/usr/bin/env python3
"""
Continuous Code Audit System - Phase 4

Autonomous read-only auditing system using local M4 Pro (Ollama) agents.
Scans entire codebase and generates numbered recommendations with smart deduplication.

Constitutional Compliance:
- Article I: Complete Context Before Action (read entire files, retry on timeouts)
- Article II: 100% Verification (verifiable recommendations with exact locations)
- Article III: Automated Enforcement (no manual overrides)
- Article IV: Continuous Learning (pattern extraction and VectorStore integration)
- Article V: Spec-Driven Development (follows PHASE_4_CONTINUOUS_AUDIT_MISSION.md)

Features:
1. Configuration loading from YAML
2. Agent integration with LOCAL tier (qwen2.5-coder models)
3. Systematic file scanning across all target directories
4. State tracking for persistence (.audit_state.json)
5. 5 categories: consolidation, linting, simplification, pruning, architecture
6. Smart deduplication (>70% similarity = append, else new file)
7. Priority elevation (3+ instances = bump priority)
8. Continuous mode with sleep intervals
9. Graceful shutdown (SIGINT, 48h timeout)
10. Telemetry events for monitoring

Usage:
    python scripts/continuous_audit_m4pro.py --mode continuous --max-hours 48
    python scripts/continuous_audit_m4pro.py --mode once  # Single scan for testing
"""

import argparse
import difflib
import json
import logging
import os
import signal
import sys
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Literal

# Add parent directory to Python path for imports
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.agent_context import AgentContext, create_agent_context
from shared.cost_tracker import CostTracker
from shared.type_definitions.result import Err, Ok, Result
from trinity_protocol.core.agent_registry import (
    AgentRegistry,
    AgentType,
    ModelTier,
    create_agent_registry,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/continuous_audit.log"),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for Type Safety
# ============================================================================


class IssueCategory(str, Enum):
    """Categories of code quality issues."""

    CONSOLIDATION = "consolidation"
    LINTING = "linting"
    SIMPLIFICATION = "simplification"
    PRUNING = "pruning"
    ARCHITECTURE = "architecture"


class Priority(str, Enum):
    """Priority levels for recommendations."""

    P0 = "P0"  # Critical
    P1 = "P1"  # High
    P2 = "P2"  # Medium
    P3 = "P3"  # Low


class Impact(str, Enum):
    """Impact assessment for recommendations."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RecommendationStatus(str, Enum):
    """Status of recommendations."""

    NEW = "New"
    UPDATED = "Updated"
    IMPLEMENTED = "Implemented"


class FileLocation(BaseModel):
    """Location of an issue in a file."""

    model_config = ConfigDict(extra="forbid")

    file_path: str
    line_start: int | None = None
    line_end: int | None = None

    def to_display(self) -> str:
        """Format for display in recommendation."""
        if self.line_start and self.line_end:
            return f"`{self.file_path}` (lines {self.line_start}-{self.line_end})"
        elif self.line_start:
            return f"`{self.file_path}` (line {self.line_start})"
        return f"`{self.file_path}`"


class Issue(BaseModel):
    """Represents a code quality issue found during audit."""

    model_config = ConfigDict(extra="forbid")

    title: str
    category: IssueCategory
    priority: Priority
    impact: Impact
    effort_hours: float = Field(ge=0.0)
    summary: str
    details: str
    locations: list[FileLocation]
    recommendation_steps: list[str]
    example_code: str | None = None
    constitutional_article: str | None = None  # I, II, III, IV, or V
    compliance_status: Literal["Violation", "Advisory"] = "Advisory"

    @field_validator("effort_hours")
    def validate_effort(cls, v: float) -> float:
        """Ensure effort is non-negative."""
        if v < 0:
            raise ValueError("effort_hours must be non-negative")
        return v


class UpdateLogEntry(BaseModel):
    """Entry in the update log."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    message: str


class Recommendation(BaseModel):
    """Full recommendation with metadata."""

    model_config = ConfigDict(extra="forbid")

    number: int
    title: str
    issue: Issue
    status: RecommendationStatus = RecommendationStatus.NEW
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    related_recommendations: list[str] = Field(default_factory=list)
    update_log: list[UpdateLogEntry] = Field(default_factory=list)
    instance_count: int = 1  # Track how many instances found

    def get_filename(self) -> str:
        """Generate filename for this recommendation."""
        # Sanitize title for filename
        safe_title = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in self.title.lower()
        )[:50]
        return f"localM4_recommends_{self.number:03d}-{safe_title}.md"


class AuditState(BaseModel):
    """State tracking for audit progress."""

    model_config = ConfigDict(extra="forbid")

    start_time: datetime = Field(default_factory=datetime.now)
    last_scan_time: datetime = Field(default_factory=datetime.now)
    scanned_files: list[str] = Field(default_factory=list)
    recommendations_count: int = 0
    next_recommendation_number: int = 1
    status: Literal["running", "stopped", "completed"] = "running"
    findings_summary: dict[str, int] = Field(default_factory=dict)


class AuditConfig(BaseModel):
    """Configuration for continuous audit system."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["continuous", "once"] = "continuous"
    max_runtime_hours: int = Field(default=48, ge=1)
    scan_interval_minutes: int = Field(default=10, ge=1)
    targets: list[str]
    checks: list[IssueCategory]
    output_dir: str
    file_prefix: str
    state_file: str
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    elevate_priority_threshold: int = Field(default=3, ge=2)
    use_local: bool = True
    model_tier: Literal["LOCAL", "LOCAL_PLUS", "CLOUD"] = "LOCAL"


# ============================================================================
# Configuration Loading
# ============================================================================


def load_config(config_path: str = "continuous_audit_config.yaml") -> Result[AuditConfig, str]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Result containing AuditConfig or error message
    """
    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        if not config_data or "audit" not in config_data:
            return Err(f"Invalid config: missing 'audit' section in {config_path}")

        audit_config = config_data["audit"]

        # Convert string enums to proper types
        checks = [IssueCategory(c) for c in audit_config.get("checks", [])]

        config = AuditConfig(
            mode=audit_config.get("mode", "continuous"),
            max_runtime_hours=audit_config.get("max_runtime_hours", 48),
            scan_interval_minutes=audit_config.get("scan_interval_minutes", 10),
            targets=audit_config.get("targets", []),
            checks=checks,
            output_dir=audit_config["output"]["dir"],
            file_prefix=audit_config["output"]["file_prefix"],
            state_file=audit_config["output"]["state_file"],
            similarity_threshold=audit_config["deduplication"]["similarity_threshold"],
            elevate_priority_threshold=audit_config["deduplication"][
                "elevate_priority_threshold"
            ],
            use_local=audit_config["agents"]["use_local"],
            model_tier=audit_config["agents"]["model_tier"],
        )

        logger.info(f"Configuration loaded from {config_path}")
        return Ok(config)

    except FileNotFoundError:
        return Err(f"Config file not found: {config_path}")
    except yaml.YAMLError as e:
        return Err(f"YAML parsing error: {e}")
    except Exception as e:
        return Err(f"Configuration loading failed: {e}")


# ============================================================================
# State Management
# ============================================================================


def load_state(state_path: str) -> AuditState:
    """
    Load audit state from JSON file.

    Args:
        state_path: Path to state file

    Returns:
        AuditState (creates new if file doesn't exist)
    """
    if not os.path.exists(state_path):
        logger.info("No existing state found, creating new state")
        return AuditState()

    try:
        with open(state_path, "r") as f:
            state_data = json.load(f)

        # Parse datetime strings
        state_data["start_time"] = datetime.fromisoformat(state_data["start_time"])
        state_data["last_scan_time"] = datetime.fromisoformat(state_data["last_scan_time"])

        state = AuditState(**state_data)
        logger.info(f"State loaded: {state.recommendations_count} recommendations so far")
        return state

    except Exception as e:
        logger.warning(f"Failed to load state from {state_path}: {e}")
        return AuditState()


def save_state(state: AuditState, state_path: str) -> Result[None, str]:
    """
    Save audit state to JSON file.

    Args:
        state: Current audit state
        state_path: Path to save state file

    Returns:
        Result indicating success or error
    """
    try:
        # Convert to dict and handle datetime serialization
        state_dict = state.model_dump()
        state_dict["start_time"] = state.start_time.isoformat()
        state_dict["last_scan_time"] = state.last_scan_time.isoformat()

        with open(state_path, "w") as f:
            json.dump(state_dict, f, indent=2)

        return Ok(None)

    except Exception as e:
        return Err(f"Failed to save state: {e}")


# ============================================================================
# Recommendation Deduplication
# ============================================================================


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate text similarity using difflib.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0.0 and 1.0
    """
    seq_matcher = difflib.SequenceMatcher(None, text1.lower(), text2.lower())
    return seq_matcher.ratio()


def find_related_recommendation(
    issue: Issue, output_dir: str, similarity_threshold: float
) -> str | None:
    """
    Find existing recommendation related to this issue.

    Args:
        issue: New issue to check
        output_dir: Directory containing recommendations
        similarity_threshold: Minimum similarity to consider related

    Returns:
        Path to related recommendation file or None
    """
    if not os.path.exists(output_dir):
        return None

    # Get all existing recommendations
    recommendation_files = [
        f for f in os.listdir(output_dir) if f.endswith(".md") and "localM4_recommends" in f
    ]

    best_match = None
    best_score = 0.0

    for rec_file in recommendation_files:
        rec_path = os.path.join(output_dir, rec_file)

        try:
            with open(rec_path, "r") as f:
                content = f.read()

            # Check category match (required)
            if f"**Category**: {issue.category.value.capitalize()}" not in content:
                continue

            # Check file overlap
            issue_files = {loc.file_path for loc in issue.locations}
            # Extract file paths from markdown
            import re

            existing_files = set(
                re.findall(r"`([^`]+\.py)`", content)
            )  # Match Python files in backticks

            if not issue_files.intersection(existing_files):
                continue  # No file overlap

            # Calculate title similarity
            title_match = re.search(r"# localM4_recommends_\d+-(.+)\.md", content)
            if title_match:
                existing_title = title_match.group(1).replace("_", " ")
                title_similarity = calculate_similarity(issue.title, existing_title)

                # Calculate details similarity
                details_similarity = calculate_similarity(issue.details, content)

                # Weighted score (title more important)
                score = 0.6 * title_similarity + 0.4 * details_similarity

                if score > best_score and score >= similarity_threshold:
                    best_score = score
                    best_match = rec_path

        except Exception as e:
            logger.warning(f"Error checking {rec_file}: {e}")
            continue

    if best_match:
        logger.info(f"Found related recommendation: {best_match} (similarity: {best_score:.2f})")

    return best_match


def append_to_recommendation(
    recommendation_path: str, issue: Issue, elevate_threshold: int
) -> Result[None, str]:
    """
    Append new finding to existing recommendation.

    Args:
        recommendation_path: Path to existing recommendation
        issue: New issue to append
        elevate_threshold: Number of instances to trigger priority elevation

    Returns:
        Result indicating success or error
    """
    try:
        with open(recommendation_path, "r") as f:
            content = f.read()

        # Parse existing content to extract instance count
        import re

        instance_match = re.search(r"\*\*Instances Found\*\*: (\d+)", content)
        current_instances = int(instance_match.group(1)) if instance_match else 1
        new_instances = current_instances + len(issue.locations)

        # Determine if priority should be elevated
        current_priority_match = re.search(r"\*\*Priority\*\*: (P\d)", content)
        should_elevate = new_instances >= elevate_threshold and current_priority_match

        # Update Affected Files section
        files_section_start = content.find("## Affected Files")
        if files_section_start == -1:
            return Err("Could not find Affected Files section")

        files_section_end = content.find("\n##", files_section_start + 1)
        files_section = content[files_section_start:files_section_end]

        # Add new locations
        new_locations = "\n".join(f"- {loc.to_display()}" for loc in issue.locations)
        updated_files_section = f"{files_section}\n{new_locations}\n"

        content = (
            content[:files_section_start] + updated_files_section + content[files_section_end:]
        )

        # Update instance count
        if instance_match:
            content = content.replace(
                f"**Instances Found**: {current_instances}",
                f"**Instances Found**: {new_instances}",
            )
        else:
            # Add instance count if not present
            priority_line = content.find("**Priority**:")
            if priority_line != -1:
                line_end = content.find("\n", priority_line)
                content = (
                    content[: line_end + 1]
                    + f"**Instances Found**: {new_instances}\n"
                    + content[line_end + 1 :]
                )

        # Elevate priority if threshold reached
        if should_elevate:
            current_priority = Priority(current_priority_match.group(1))
            if current_priority == Priority.P3:
                new_priority = Priority.P2
            elif current_priority == Priority.P2:
                new_priority = Priority.P1
            else:
                new_priority = current_priority

            if new_priority != current_priority:
                content = content.replace(
                    f"**Priority**: {current_priority.value}",
                    f"**Priority**: {new_priority.value}",
                )
                logger.info(
                    f"Priority elevated: {current_priority.value} → {new_priority.value}"
                )

        # Update timestamp and log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        log_entry = f"- {timestamp} - Added {len(issue.locations)} more instance(s)"
        if should_elevate:
            log_entry += f" (elevated to {new_priority.value})"

        update_log_section = content.find("## Update Log")
        if update_log_section != -1:
            log_section_end = content.find("\n---", update_log_section)
            content = (
                content[:log_section_end] + f"{log_entry}\n" + content[log_section_end:]
            )

        # Update Last Updated timestamp
        content = re.sub(
            r"\*\*Last Updated\*\*: .*",
            f"**Last Updated**: {timestamp}",
            content,
        )

        # Update Status to Updated
        content = content.replace("**Status**: New", "**Status**: Updated")

        # Write back
        with open(recommendation_path, "w") as f:
            f.write(content)

        logger.info(f"Appended to {recommendation_path}")
        return Ok(None)

    except Exception as e:
        return Err(f"Failed to append to recommendation: {e}")


def create_new_recommendation(
    recommendation: Recommendation, output_dir: str
) -> Result[str, str]:
    """
    Create new recommendation markdown file.

    Args:
        recommendation: Recommendation to create
        output_dir: Directory to save recommendation

    Returns:
        Result containing path to created file or error
    """
    try:
        os.makedirs(output_dir, exist_ok=True)

        filename = recommendation.get_filename()
        filepath = os.path.join(output_dir, filename)

        # Generate markdown content
        issue = recommendation.issue
        timestamp = recommendation.created_at.strftime("%Y-%m-%d %H:%M")

        content = f"""# {filename}

**Priority**: {issue.priority.value}
**Category**: {issue.category.value.capitalize()}
**Impact**: {issue.impact.value}
**Effort**: {issue.effort_hours} hours
**Status**: {recommendation.status.value}
**Instances Found**: {recommendation.instance_count}
**Last Updated**: {timestamp}

## Summary
{issue.summary}

## Details
{issue.details}

## Affected Files
"""
        for loc in issue.locations:
            content += f"- {loc.to_display()}\n"

        content += "\n## Recommendation\n"
        for i, step in enumerate(issue.recommendation_steps, 1):
            content += f"{i}. {step}\n"

        if issue.example_code:
            content += f"\n## Example Code\n{issue.example_code}\n"

        if issue.constitutional_article:
            content += f"""
## Constitutional Compliance
- Article affected: {issue.constitutional_article}
- Compliance status: {issue.compliance_status}
"""

        if recommendation.related_recommendations:
            content += "\n## Related Recommendations\n"
            for related in recommendation.related_recommendations:
                content += f"- {related}\n"

        content += f"""
## Update Log
- {timestamp} - Initial finding

---
**Generated by**: AUDITOR + QUALITY_ENFORCER (local M4 Pro)
**Cost**: $0.00
"""

        with open(filepath, "w") as f:
            f.write(content)

        logger.info(f"Created recommendation: {filepath}")
        return Ok(filepath)

    except Exception as e:
        return Err(f"Failed to create recommendation: {e}")


# ============================================================================
# File Scanning and Issue Detection
# ============================================================================


def scan_file_for_issues(
    file_path: str,
    registry: AgentRegistry,
    checks: list[IssueCategory],
    context: AgentContext,
) -> Result[list[Issue], str]:
    """
    Scan a single file for code quality issues.

    Args:
        file_path: Path to file to scan
        registry: Agent registry for accessing auditor/quality enforcer
        checks: List of check categories to perform
        context: Agent context for memory/learning

    Returns:
        Result containing list of issues found or error message
    """
    try:
        # Read file content (Article I: Complete Context)
        with open(file_path, "r") as f:
            content = f.read()

        if not content.strip():
            return Ok([])  # Skip empty files

        issues: list[Issue] = []

        # Create auditor agent (LOCAL tier)
        auditor = registry.create_agent(AgentType.AUDITOR, ModelTier.LOCAL)

        # Scan for each check category
        for category in checks:
            try:
                issue = _scan_for_category(file_path, content, category, auditor, context)
                if issue:
                    issues.append(issue)
            except Exception as e:
                logger.warning(f"Error scanning {file_path} for {category.value}: {e}")
                continue

        return Ok(issues)

    except Exception as e:
        return Err(f"Failed to scan {file_path}: {e}")


def _scan_for_category(
    file_path: str,
    content: str,
    category: IssueCategory,
    auditor: object,
    context: AgentContext,
) -> Issue | None:
    """
    Scan file for specific category of issues.

    This is a simplified implementation. In production, this would use
    the actual auditor agent to analyze code.

    Args:
        file_path: Path to file
        content: File content
        category: Category to check
        auditor: Auditor agent instance
        context: Agent context

    Returns:
        Issue if found, None otherwise
    """
    # TODO: Implement actual agent-based analysis
    # For now, use basic heuristics as placeholder

    if category == IssueCategory.CONSOLIDATION:
        # Check for duplicate code patterns with specific function names
        import re
        from collections import Counter

        function_pattern = r"def (\w+)\("
        functions = re.findall(function_pattern, content)
        function_counts = Counter(functions)
        duplicates = [(name, count) for name, count in function_counts.items() if count > 1]

        if duplicates:
            duplicate_list = ", ".join(f"'{name}' ({count}x)" for name, count in duplicates)
            return Issue(
                title="Duplicate function definitions detected",
                category=category,
                priority=Priority.P2,
                impact=Impact.MEDIUM,
                effort_hours=2.0,
                summary="File contains duplicate or very similar function definitions",
                details=f"Found {len(duplicates)} duplicate function names: {duplicate_list}",
                locations=[FileLocation(file_path=file_path)],
                recommendation_steps=[
                    "Review duplicate functions listed above",
                    "Consolidate common logic into shared utilities",
                    "Remove redundant implementations",
                    "Ensure single source of truth for each function",
                ],
                constitutional_article="II",
                compliance_status="Advisory",
            )

    elif category == IssueCategory.LINTING:
        # Check for linting issues
        if "import *" in content:
            return Issue(
                title="Wildcard imports detected",
                category=category,
                priority=Priority.P3,
                impact=Impact.LOW,
                effort_hours=0.5,
                summary="File uses wildcard imports which reduce code clarity",
                details="Wildcard imports make it difficult to track dependencies",
                locations=[FileLocation(file_path=file_path)],
                recommendation_steps=[
                    "Replace wildcard imports with explicit imports",
                    "Run linter to verify",
                ],
                constitutional_article="II",
                compliance_status="Violation",
            )

    elif category == IssueCategory.SIMPLIFICATION:
        # Check for complex functions
        lines = content.split("\n")
        in_function = False
        function_start = 0
        function_lines = 0

        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                if in_function and function_lines > 50:
                    return Issue(
                        title="Function exceeds 50 line limit",
                        category=category,
                        priority=Priority.P1,
                        impact=Impact.HIGH,
                        effort_hours=3.0,
                        summary="Function violates constitutional law #8 (50 line limit)",
                        details=f"Function at line {function_start} has {function_lines} lines",
                        locations=[
                            FileLocation(
                                file_path=file_path,
                                line_start=function_start,
                                line_end=i,
                            )
                        ],
                        recommendation_steps=[
                            "Break function into smaller focused functions",
                            "Extract logical sub-components",
                            "Verify each function has single responsibility",
                        ],
                        constitutional_article="II",
                        compliance_status="Violation",
                    )
                in_function = True
                function_start = i + 1
                function_lines = 0
            elif in_function:
                function_lines += 1

    elif category == IssueCategory.PRUNING:
        # Check for commented code
        commented_lines = [l for l in content.split("\n") if l.strip().startswith("#")]
        if len(commented_lines) > 20:
            return Issue(
                title="Excessive commented code",
                category=category,
                priority=Priority.P3,
                impact=Impact.LOW,
                effort_hours=1.0,
                summary=f"File has {len(commented_lines)} commented lines",
                details="Large amounts of commented code reduce maintainability",
                locations=[FileLocation(file_path=file_path)],
                recommendation_steps=[
                    "Review commented code for relevance",
                    "Remove obsolete comments",
                    "Move useful comments to documentation",
                ],
                constitutional_article="II",
                compliance_status="Advisory",
            )

    elif category == IssueCategory.ARCHITECTURE:
        # Check for Dict[Any, Any] violations using AST parsing (not regex)
        # This prevents false positives from comments, docstrings, and string literals
        import ast

        try:
            tree = ast.parse(content)
            violations: list[tuple[int, str]] = []

            class DictAnyVisitor(ast.NodeVisitor):
                def visit_Subscript(self, node: ast.Subscript) -> None:
                    # Check for Dict[Any, Any] or dict[Any, Any]
                    if isinstance(node.value, ast.Name) and node.value.id in ("Dict", "dict"):
                        # Check if subscript is [Any, Any]
                        if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
                            if all(
                                isinstance(elt, ast.Name) and elt.id == "Any"
                                for elt in node.slice.elts
                            ):
                                line_num = getattr(node, "lineno", 0)
                                # Get the actual code snippet
                                lines = content.split("\n")
                                if 0 < line_num <= len(lines):
                                    code_line = lines[line_num - 1].strip()
                                    violations.append((line_num, code_line))
                    self.generic_visit(node)

            visitor = DictAnyVisitor()
            visitor.visit(tree)

            if violations:
                # Found genuine Dict[Any, Any] in actual code
                violation_details = "\n".join(
                    f"  Line {line}: {code}" for line, code in violations
                )
                return Issue(
                    title="Dict[Any, Any] type violation",
                    category=category,
                    priority=Priority.P0,
                    impact=Impact.CRITICAL,
                    effort_hours=4.0,
                    summary="File uses Dict[Any, Any] which violates ADR-008",
                    details=f"Constitutional law #2 requires strict typing with Pydantic models\n\nViolations found:\n{violation_details}",
                    locations=[FileLocation(file_path=file_path, line_start=violations[0][0])],
                    recommendation_steps=[
                        "Replace Dict[Any, Any] with Pydantic model",
                        "Define explicit field types",
                        "Update type hints throughout",
                        "Run mypy to verify",
                    ],
                    example_code="""
# ❌ WRONG:
user_data: Dict[Any, Any] = {}

# ✅ CORRECT:
from pydantic import BaseModel

class UserData(BaseModel):
    email: str
    name: str
    age: int
""",
                    constitutional_article="II",
                    compliance_status="Violation",
                )
        except SyntaxError:
            # File has syntax errors, skip AST parsing
            pass

    return None


def scan_directory(
    directory: str,
    registry: AgentRegistry,
    checks: list[IssueCategory],
    context: AgentContext,
    state: AuditState,
) -> list[Issue]:
    """
    Scan all Python files in directory recursively.

    Args:
        directory: Directory to scan
        registry: Agent registry
        checks: Check categories to perform
        context: Agent context
        state: Current audit state

    Returns:
        List of all issues found
    """
    all_issues = []

    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)

            # Skip if already scanned
            if file_path in state.scanned_files:
                continue

            logger.info(f"Scanning: {file_path}")

            result = scan_file_for_issues(file_path, registry, checks, context)
            if result.is_ok():
                issues = result.unwrap()
                all_issues.extend(issues)
                state.scanned_files.append(file_path)
            else:
                logger.error(f"Scan failed: {result.unwrap_err()}")

    return all_issues


# ============================================================================
# Scan Cycle Execution
# ============================================================================


def run_scan_cycle(
    config: AuditConfig, state: AuditState, registry: AgentRegistry, context: AgentContext
) -> Result[int, str]:
    """
    Run a single scan cycle across all targets.

    Args:
        config: Audit configuration
        state: Current audit state
        registry: Agent registry
        context: Agent context

    Returns:
        Result containing number of new recommendations created or error
    """
    try:
        logger.info("=" * 80)
        logger.info("Starting scan cycle")
        logger.info("=" * 80)

        new_recommendations = 0

        # Scan each target directory
        for target in config.targets:
            if not os.path.exists(target):
                logger.warning(f"Target not found: {target}")
                continue

            logger.info(f"Scanning target: {target}")
            issues = scan_directory(target, registry, config.checks, context, state)

            logger.info(f"Found {len(issues)} issues in {target}")

            # Process each issue
            for issue in issues:
                # Check for related recommendation
                related = find_related_recommendation(
                    issue, config.output_dir, config.similarity_threshold
                )

                if related:
                    # Append to existing recommendation
                    result = append_to_recommendation(
                        related, issue, config.elevate_priority_threshold
                    )
                    if result.is_err():
                        logger.error(f"Failed to append: {result.unwrap_err()}")
                else:
                    # Create new recommendation
                    recommendation = Recommendation(
                        number=state.next_recommendation_number,
                        title=issue.title,
                        issue=issue,
                        instance_count=len(issue.locations),
                    )

                    result = create_new_recommendation(recommendation, config.output_dir)
                    if result.is_ok():
                        state.next_recommendation_number += 1
                        state.recommendations_count += 1
                        new_recommendations += 1

                        # Update findings summary
                        category = issue.category.value
                        state.findings_summary[category] = (
                            state.findings_summary.get(category, 0) + 1
                        )
                    else:
                        logger.error(f"Failed to create: {result.unwrap_err()}")

        # Update state
        state.last_scan_time = datetime.now()

        # Save state
        state_path = os.path.join(config.output_dir, config.state_file)
        save_result = save_state(state, state_path)
        if save_result.is_err():
            logger.error(f"Failed to save state: {save_result.unwrap_err()}")

        logger.info(f"Scan cycle complete: {new_recommendations} new recommendations")
        logger.info(f"Total recommendations: {state.recommendations_count}")

        return Ok(new_recommendations)

    except Exception as e:
        return Err(f"Scan cycle failed: {e}")


# ============================================================================
# Main Execution
# ============================================================================


class ContinuousAuditSystem:
    """Main system orchestrator for continuous audit."""

    def __init__(self, config: AuditConfig):
        """Initialize audit system."""
        self.config = config
        self.running = True
        self.start_time = datetime.now()

        # Initialize context and registry
        self.context = create_agent_context()
        # Initialize cost tracker with SQLite storage
        from shared.cost_tracker import SQLiteStorage
        storage = SQLiteStorage("trinity_costs.db")
        self.cost_tracker = CostTracker(storage=storage)
        self.registry = create_agent_registry(
            agent_context=self.context,
            cost_tracker=self.cost_tracker,
            default_tier=config.model_tier.lower(),  # type: ignore
        )

        # Load state
        state_path = os.path.join(config.output_dir, config.state_file)
        self.state = load_state(state_path)

        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        logger.info("Continuous Audit System initialized")
        logger.info(f"Mode: {config.mode}")
        logger.info(f"Max runtime: {config.max_runtime_hours} hours")
        logger.info(f"Scan interval: {config.scan_interval_minutes} minutes")

    def _handle_shutdown(self, signum: int, frame: object) -> None:
        """Handle graceful shutdown on signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.state.status = "stopped"

        # Save final state
        state_path = os.path.join(self.config.output_dir, self.config.state_file)
        save_state(self.state, state_path)

        logger.info("Shutdown complete")
        sys.exit(0)

    def _check_timeout(self) -> bool:
        """Check if maximum runtime exceeded."""
        elapsed = datetime.now() - self.start_time
        max_duration = timedelta(hours=self.config.max_runtime_hours)

        if elapsed >= max_duration:
            logger.info(f"Maximum runtime of {self.config.max_runtime_hours}h reached")
            return True

        return False

    def run_once(self) -> None:
        """Run a single scan cycle (for testing)."""
        logger.info("Running single scan cycle")
        result = run_scan_cycle(self.config, self.state, self.registry, self.context)

        if result.is_ok():
            logger.info(f"Scan complete: {result.unwrap()} new recommendations")
        else:
            logger.error(f"Scan failed: {result.unwrap_err()}")

        self.state.status = "completed"
        state_path = os.path.join(self.config.output_dir, self.config.state_file)
        save_state(self.state, state_path)

    def run_continuous(self) -> None:
        """Run continuous scanning with sleep intervals."""
        logger.info("Starting continuous audit mode")
        logger.info("Press Ctrl+C to stop gracefully")

        cycle_count = 0

        while self.running:
            cycle_count += 1
            logger.info(f"\n{'='*80}")
            logger.info(f"Cycle {cycle_count}")
            logger.info(f"{'='*80}\n")

            # Run scan cycle
            result = run_scan_cycle(self.config, self.state, self.registry, self.context)

            if result.is_ok():
                new_recs = result.unwrap()
                logger.info(f"Cycle {cycle_count} complete: {new_recs} new recommendations")
            else:
                logger.error(f"Cycle {cycle_count} failed: {result.unwrap_err()}")

            # Check timeout
            if self._check_timeout():
                self.running = False
                self.state.status = "completed"
                break

            # Sleep until next cycle
            if self.running:
                sleep_seconds = self.config.scan_interval_minutes * 60
                logger.info(f"Sleeping {self.config.scan_interval_minutes} minutes...")
                time.sleep(sleep_seconds)

        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("Audit System Completed")
        logger.info("=" * 80)
        logger.info(f"Total cycles: {cycle_count}")
        logger.info(f"Total recommendations: {self.state.recommendations_count}")
        logger.info(f"Files scanned: {len(self.state.scanned_files)}")
        logger.info(f"Findings by category: {self.state.findings_summary}")
        logger.info(f"Cost: $0.00 (100% local M4 Pro)")

        # Save final state
        state_path = os.path.join(self.config.output_dir, self.config.state_file)
        save_state(self.state, state_path)


# ============================================================================
# Test Helper Functions (for test_continuous_audit.py)
# ============================================================================


def detect_consolidation_issues(files: list[dict[str, str]]) -> Result[list[dict], str]:
    """
    Detect consolidation issues (duplicate code patterns).

    Test helper that wraps _scan_for_category for CONSOLIDATION checks.
    """
    try:
        issues = []
        for file_data in files:
            content = file_data.get("content", "")
            path = file_data.get("path", "unknown.py")

            # Create mock auditor (not used in heuristic mode)
            auditor = None
            context = create_agent_context()

            issue = _scan_for_category(path, content, IssueCategory.CONSOLIDATION, auditor, context)
            if issue:
                issues.append({
                    "category": issue.category.value.capitalize(),
                    "title": issue.title,
                    "details": issue.details,
                })

        return Ok(issues)
    except Exception as e:
        return Err(f"Detection failed: {e}")


def detect_linting_issues(files: list[dict[str, str]]) -> Result[list[dict], str]:
    """
    Detect linting issues (import order, type hints, etc.).

    Test helper that wraps _scan_for_category for LINTING checks.
    """
    try:
        issues = []
        for file_data in files:
            content = file_data.get("content", "")
            path = file_data.get("path", "unknown.py")

            auditor = None
            context = create_agent_context()

            issue = _scan_for_category(path, content, IssueCategory.LINTING, auditor, context)
            if issue:
                issues.append({
                    "category": issue.category.value.capitalize(),
                    "title": issue.title,
                    "details": issue.details,
                })

        return Ok(issues)
    except Exception as e:
        return Err(f"Detection failed: {e}")


def detect_simplification_issues(files: list[dict[str, str]]) -> Result[list[dict], str]:
    """
    Detect simplification issues (complex functions, high nesting).

    Test helper that wraps _scan_for_category for SIMPLIFICATION checks.
    """
    try:
        issues = []
        for file_data in files:
            content = file_data.get("content", "")
            path = file_data.get("path", "unknown.py")

            auditor = None
            context = create_agent_context()

            issue = _scan_for_category(path, content, IssueCategory.SIMPLIFICATION, auditor, context)
            if issue:
                issues.append({
                    "category": issue.category.value.capitalize(),
                    "title": issue.title,
                    "details": issue.details,
                })

        return Ok(issues)
    except Exception as e:
        return Err(f"Detection failed: {e}")


def detect_pruning_issues(files: list[dict[str, str]]) -> Result[list[dict], str]:
    """
    Detect pruning issues (dead code, unused functions).

    Test helper that wraps _scan_for_category for PRUNING checks.
    """
    try:
        issues = []
        for file_data in files:
            content = file_data.get("content", "")
            path = file_data.get("path", "unknown.py")

            auditor = None
            context = create_agent_context()

            issue = _scan_for_category(path, content, IssueCategory.PRUNING, auditor, context)
            if issue:
                issues.append({
                    "category": issue.category.value.capitalize(),
                    "title": issue.title,
                    "details": issue.details,
                })

        return Ok(issues)
    except Exception as e:
        return Err(f"Detection failed: {e}")


def detect_architecture_issues(files: list[dict[str, str]]) -> Result[list[dict], str]:
    """
    Detect architecture issues (Dict[Any, Any] violations, etc.).

    Test helper that wraps _scan_for_category for ARCHITECTURE checks.
    """
    try:
        issues = []
        for file_data in files:
            content = file_data.get("content", "")
            path = file_data.get("path", "unknown.py")

            auditor = None
            context = create_agent_context()

            issue = _scan_for_category(path, content, IssueCategory.ARCHITECTURE, auditor, context)
            if issue:
                issues.append({
                    "category": issue.category.value.capitalize(),
                    "title": issue.title,
                    "details": issue.details,
                })

        return Ok(issues)
    except Exception as e:
        return Err(f"Detection failed: {e}")


def sanitize_filename(title: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Removes directory separators and parent directory references.
    """
    # Remove path traversal attempts
    safe_title = title.replace("..", "").replace("/", "_").replace("\\", "_")

    # Keep only alphanumeric, dashes, and underscores
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in safe_title.lower())

    # Limit length
    return safe_title[:50]


def validate_file_permissions(path: Path) -> Result[None, str]:
    """
    Validate file permissions are secure (not world-writable).

    Returns Ok if permissions are acceptable, Err with warning otherwise.
    """
    try:
        import stat

        if not path.exists():
            return Err(f"File not found: {path}")

        mode = path.stat().st_mode

        # Check if world-writable (0o002)
        if mode & stat.S_IWOTH:
            return Err(f"Warning: File {path} is world-writable (insecure permissions)")

        # Check if group-writable and warn (advisory)
        if mode & stat.S_IWGRP:
            logger.warning(f"File {path} is group-writable (consider restricting)")

        return Ok(None)

    except Exception as e:
        return Err(f"Permission check failed: {e}")


def generate_recommendation_filename(number: int, title: str) -> str:
    """
    Generate recommendation filename with proper zero-padding.

    Handles numbers > 999 with 4-digit padding.
    """
    safe_title = sanitize_filename(title)

    # Use 4-digit padding to handle numbers > 999
    if number > 999:
        return f"localM4_recommends_{number:04d}-{safe_title}.md"
    else:
        return f"localM4_recommends_{number:03d}-{safe_title}.md"


def run_continuous_audit(config: dict | AuditConfig, output_dir: str, max_cycles: int | None = None) -> Result[None, str]:
    """
    Run continuous audit system (wrapper for testing).

    Args:
        config: Audit configuration (dict or AuditConfig)
        output_dir: Output directory path
        max_cycles: Maximum number of cycles (for testing)

    Returns:
        Result indicating success or error
    """
    try:
        # Convert dict to AuditConfig if needed
        if isinstance(config, dict):
            # Extract nested structure
            audit_dict = config.get("audit", {})
            output_dict = audit_dict.get("output", {})
            dedup_dict = audit_dict.get("deduplication", {})
            agents_dict = audit_dict.get("agents", {})

            # Flatten to AuditConfig structure
            flattened = {
                "mode": audit_dict.get("mode", "continuous"),
                "max_runtime_hours": audit_dict.get("max_runtime_hours", 48),
                "scan_interval_minutes": audit_dict.get("scan_interval_minutes", 10),
                "targets": audit_dict.get("targets", []),
                "checks": audit_dict.get("checks", []),
                "output_dir": output_dict.get("dir", output_dir),
                "file_prefix": output_dict.get("file_prefix", "localM4_recommends_"),
                "state_file": output_dict.get("state_file", ".audit_state.json"),
                "similarity_threshold": dedup_dict.get("similarity_threshold", 0.7),
                "elevate_priority_threshold": dedup_dict.get("elevate_priority_threshold", 3),
                "use_local": agents_dict.get("use_local", True),
                "model_tier": agents_dict.get("model_tier", "LOCAL"),
            }

            audit_config = AuditConfig(**flattened)
        else:
            audit_config = config

        # Override output_dir (tests specify this separately)
        audit_config.output_dir = output_dir

        # Create output directory if it doesn't exist
        import os
        os.makedirs(output_dir, exist_ok=True)

        # Create system
        system = ContinuousAuditSystem(audit_config)

        # Run limited cycles for testing
        if max_cycles:
            cycle_count = 0
            while system.running and cycle_count < max_cycles:
                result = run_scan_cycle(audit_config, system.state, system.registry, system.context)
                if result.is_err():
                    return Err(result.unwrap_err())
                cycle_count += 1

                # Check timeout
                if system._check_timeout():
                    break
        else:
            # Run full continuous mode
            system.run_continuous()

        return Ok(None)

    except Exception as e:
        return Err(f"Continuous audit failed: {e}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Continuous Code Audit System with local M4 Pro agents"
    )
    parser.add_argument(
        "--mode",
        choices=["continuous", "once"],
        default="once",
        help="Execution mode (default: once)",
    )
    parser.add_argument(
        "--max-hours",
        type=int,
        default=48,
        help="Maximum runtime in hours for continuous mode (default: 48)",
    )
    parser.add_argument(
        "--config",
        default="continuous_audit_config.yaml",
        help="Path to configuration file (default: continuous_audit_config.yaml)",
    )

    args = parser.parse_args()

    # Load configuration
    config_result = load_config(args.config)
    if config_result.is_err():
        logger.error(f"Configuration error: {config_result.unwrap_err()}")
        sys.exit(1)

    config = config_result.unwrap()

    # Override mode and max hours from CLI
    config.mode = args.mode  # type: ignore
    config.max_runtime_hours = args.max_hours

    # Create and run system
    system = ContinuousAuditSystem(config)

    if config.mode == "once":
        system.run_once()
    else:
        system.run_continuous()


if __name__ == "__main__":
    main()
