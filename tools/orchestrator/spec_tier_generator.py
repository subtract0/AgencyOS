"""
SpecTierGenerator - Deterministic tier extraction from specifications.

Generates three-tier progressive disclosure summaries from specification files:
- Tier 1: Executive summary (<25 lines, 30-second read)
- Tier 2: Key decisions (<50 lines, 2-minute read)
- Tier 3: Full spec reference (file path, line count, interactive view)

**Performance Requirement**: <2 seconds generation time (deterministic parsing, no LLM)

Constitutional Compliance:
- Article I: Complete context (all tiers generated or clear error)
- Article II: Test summary required in Tier 1 (100% verification)
- Article V: Spec-driven (deterministic extraction, no hallucination)

Architecture:
    SpecTierGenerator.generate_tiered_spec(spec_path)
        ↓
    parse_spec_structure(content) → dict
        ↓
    extract_tier1_summary(structure) → Tier1Summary
    extract_tier2_decisions(structure) → Tier2Summary
    create_tier3_reference(path, lines, sections) → Tier3Reference
        ↓
    TieredSpec(tier1, tier2, tier3)

Usage:
    from tools.orchestrator.spec_tier_generator import SpecTierGenerator

    generator = SpecTierGenerator()
    result = generator.generate_tiered_spec(Path("spec.md"))

    if result.is_ok():
        tiered_spec = result.unwrap()
        print(f"Tier 1: {tiered_spec.tier1.mission}")
    else:
        error = result.unwrap_err()
        print(f"Generation failed: {error.reason}")

Reference:
    - Spec: specs/spec-034-tiered-spec-review.md
    - Models: shared/models/orchestrator_models.py
    - Tests: tests/orchestrator/test_spec_tier_generator.py

Version: 1.0.0
Created: 2025-10-15
"""

import html
import logging
import re
from pathlib import Path
from typing import Any

from shared.models.orchestrator_models import (
    ArchitecturalDecision,
    ConstitutionalStatus,
    RiskLevel,
    Tier1Summary,
    Tier2Summary,
    Tier3Reference,
    TieredSpec,
    TierGenerationError,
)
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class SpecTierGenerator:
    """
    Deterministic tier generator for specification progressive disclosure.

    Parses specification markdown files and extracts three tiers of information:
    1. Executive summary (<25 lines)
    2. Key architectural decisions (<50 lines)
    3. Full specification reference

    Performance: <2 seconds (template-based parsing, no LLM calls)
    """

    def __init__(self) -> None:
        """Initialize tier generator."""
        pass

    def generate_tiered_spec(self, spec_path: Path) -> Result[TieredSpec, TierGenerationError]:
        """
        Generate tiered specification from file.

        Args:
            spec_path: Path to specification markdown file

        Returns:
            Ok(TieredSpec) if successful
            Err(TierGenerationError) if parsing fails

        Performance: <2 seconds (deterministic parsing)

        Example:
            >>> generator = SpecTierGenerator()
            >>> result = generator.generate_tiered_spec(Path("spec.md"))
            >>> if result.is_ok():
            ...     tiered_spec = result.unwrap()
        """
        try:
            # Read spec file
            if not spec_path.exists():
                return Err(
                    TierGenerationError(
                        reason=f"Specification file not found: {spec_path}",
                        file_path=spec_path,
                        recovery_hint="Check file path and ensure spec file exists",
                    )
                )

            content = spec_path.read_text(encoding="utf-8")

            # Check for empty file
            if not content.strip():
                return Err(
                    TierGenerationError(
                        reason="Specification file is empty",
                        file_path=spec_path,
                        recovery_hint="Add Executive Summary section to spec",
                    )
                )

            # Parse spec structure
            structure = parse_spec_structure(content)

            # Extract tiers
            tier1 = extract_tier1_summary(structure)
            tier2 = extract_tier2_decisions(structure)

            # Count lines and sections for Tier 3
            line_count = len(content.splitlines())
            section_count = len(re.findall(r"^##\s+", content, re.MULTILINE))

            tier3 = create_tier3_reference(spec_path, line_count, section_count)

            # Combine into TieredSpec
            tiered_spec = TieredSpec(tier1=tier1, tier2=tier2, tier3=tier3)

            logger.info(
                f"Generated tiered spec: Tier1 ({tier1.line_count} lines), "
                f"Tier2 ({tier2.line_count} lines), "
                f"Tier3 ({tier3.line_count} lines total)"
            )

            return Ok(tiered_spec)

        except Exception as e:
            logger.error(f"Tier generation failed: {e}")
            return Err(
                TierGenerationError(
                    reason=f"Tier generation failed: {str(e)}",
                    file_path=spec_path,
                    recovery_hint="Check spec file format and ensure valid markdown",
                )
            )


def parse_spec_structure(content: str) -> dict[str, Any]:
    """
    Parse specification markdown into structured dictionary.

    Extracts key sections using regex patterns:
    - Executive Summary
    - Goals
    - Acceptance Criteria
    - Technical Approach / Approach
    - Architectural Decisions
    - Security Implications
    - Dependencies
    - Effort Estimate
    - Risk Level / Risk

    Args:
        content: Specification markdown content

    Returns:
        Dictionary with extracted sections

    Example:
        >>> structure = parse_spec_structure(spec_content)
        >>> print(structure["executive_summary"])
    """
    # Sanitize HTML/JS to prevent XSS (security requirement)
    content = html.escape(content, quote=False)  # Escape HTML tags but preserve structure

    structure: dict[str, Any] = {}

    # Extract Executive Summary (first paragraph or explicit section)
    exec_summary_match = re.search(
        r"##\s+Executive Summary\s*\n\s*(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if exec_summary_match:
        structure["executive_summary"] = exec_summary_match.group(1).strip()
    else:
        # Fallback: Use first paragraph after title
        first_para_match = re.search(r"^#\s+.+?\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL)
        if first_para_match:
            structure["executive_summary"] = first_para_match.group(1).strip()
        else:
            structure["executive_summary"] = "No executive summary found"

    # Extract Goals
    goals_match = re.search(r"##\s+Goals?\s*\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if goals_match:
        goals_text = goals_match.group(1).strip()
        structure["goals"] = [line.strip("- ").strip() for line in goals_text.splitlines() if line.strip().startswith("-")]
    else:
        structure["goals"] = []

    # Extract Acceptance Criteria
    criteria_match = re.search(
        r"##\s+Acceptance Criteria\s*\n\s*(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if criteria_match:
        criteria_text = criteria_match.group(1).strip()
        # Extract numbered or bulleted criteria
        criteria_lines = [
            re.sub(r"^\d+\.\s*|\-\s*", "", line.strip())
            for line in criteria_text.splitlines()
            if re.match(r"^\d+\.|^\-", line.strip())
        ]
        structure["acceptance_criteria"] = criteria_lines
    else:
        structure["acceptance_criteria"] = []

    # Extract Approach
    approach_match = re.search(
        r"##\s+(Technical Approach|Approach)\s*\n\s*(.+?)(?=\n##|\n###|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if approach_match:
        structure["approach"] = approach_match.group(2).strip()
    else:
        structure["approach"] = "Approach details not specified"

    # Extract Test Plan
    test_match = re.search(
        r"##\s+Test Plan\s*\n\s*(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if test_match:
        structure["test_plan"] = test_match.group(1).strip()
    else:
        # Fallback: Look for test mention in acceptance criteria
        structure["test_plan"] = f"{len(structure.get('acceptance_criteria', []))} acceptance criteria defined"

    # Extract Architectural Decisions
    decisions_match = re.findall(
        r"###\s+(.+?)\n\s*\*\*Choice\*\*:\s*(.+?)\n\s*\*\*Rationale\*\*:\s*(.+?)\n\s*\*\*Trade-?off\*\*:\s*(.+?)(?=\n###|\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )

    if not decisions_match:
        # Alternative pattern: "#### Decision N:"
        decisions_match = re.findall(
            r"####\s+Decision\s+\d+:\s+(.+?)\n\s*\*\*Choice\*\*:\s*(.+?)\n\s*\*\*Rationale\*\*:\s*(.+?)\n\s*\*\*Trade-?off\*\*:\s*(.+?)(?=\n####|\n###|\n##|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )

    structure["decisions"] = [
        {
            "title": title.strip(),
            "choice": choice.strip(),
            "rationale": rationale.strip(),
            "tradeoffs": tradeoffs.strip(),
        }
        for title, choice, rationale, tradeoffs in decisions_match
    ]

    # Extract Security Implications
    security_match = re.search(
        r"##\s+Security Implications?\s*\n\s*(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if security_match:
        structure["security"] = security_match.group(1).strip()
    else:
        structure["security"] = "No security implications specified"

    # Extract Dependencies
    deps_match = re.search(
        r"##\s+Dependencies\s*\n\s*(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if deps_match:
        structure["dependencies"] = deps_match.group(1).strip()
    else:
        structure["dependencies"] = "No dependencies specified"

    # Extract Effort Estimate
    effort_match = re.search(
        r"##\s+Effort Estimate\s*\n\s*(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if effort_match:
        effort_text = effort_match.group(1).strip().split("\n")[0]  # First line only
        # Extract just the time estimate (e.g., "6-8 hours" from "6-8 hours (details)")
        time_pattern = re.search(r"(\d+[-–]\d+\s+(hours?|days?|weeks?))", effort_text, re.IGNORECASE)
        if time_pattern:
            structure["effort"] = time_pattern.group(1)
        else:
            structure["effort"] = effort_text
    else:
        # Fallback: Look for time patterns in content (e.g., "4-6 hours", "2-3 days")
        time_match = re.search(r"(\d+[-–]\d+\s+(hours?|days?|weeks?))", content, re.IGNORECASE)
        if time_match:
            structure["effort"] = time_match.group(1)
        else:
            structure["effort"] = "Effort not estimated"

    # Extract Risk Level
    risk_match = re.search(
        r"##\s+Risk Level\s*\n\s*(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if risk_match:
        risk_text = risk_match.group(1).strip().lower()
        if "low" in risk_text:
            structure["risk"] = "low"
        elif "high" in risk_text:
            structure["risk"] = "high"
        else:
            structure["risk"] = "medium"
    else:
        # Infer risk from keywords
        if any(keyword in content.lower() for keyword in ["critical", "security", "authentication", "encryption"]):
            structure["risk"] = "medium"
        else:
            structure["risk"] = "low"

    # Extract Deliverables
    deliverables_match = re.search(
        r"##\s+Deliverables\s*\n\s*(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if deliverables_match:
        deliverables_text = deliverables_match.group(1).strip()
        structure["deliverables"] = [
            line.strip("- ").strip()
            for line in deliverables_text.splitlines()
            if line.strip().startswith("-") or line.strip().startswith("*")
        ]
    else:
        # Infer from file mentions in content (e.g., `file.py`, `path/to/file.ts`)
        file_matches = re.findall(r"`([a-zA-Z0-9_/.-]+\.(?:py|ts|tsx|js|jsx|md|yml|yaml))`", content)
        structure["deliverables"] = list(set(file_matches))[:5]  # Max 5 files

    if not structure["deliverables"]:
        structure["deliverables"] = ["Implementation files (details in spec)"]

    # Constitutional compliance check
    has_goals = len(structure.get("goals", [])) > 0
    has_criteria = len(structure.get("acceptance_criteria", [])) > 0
    has_tests = "test" in structure.get("test_plan", "").lower() or len(structure.get("acceptance_criteria", [])) > 0

    if has_goals and has_criteria and has_tests:
        structure["constitutional_compliance"] = True
    else:
        structure["constitutional_compliance"] = False

    return structure


def extract_tier1_summary(structure: dict[str, Any]) -> Tier1Summary:
    """
    Extract Tier 1 executive summary from spec structure.

    Generates <25 line summary with:
    - Mission (from executive summary)
    - Approach (from technical approach section)
    - Test summary
    - Deliverables
    - Constitutional status
    - Effort estimate
    - Risk level

    Args:
        structure: Parsed spec structure from parse_spec_structure()

    Returns:
        Tier1Summary model

    Example:
        >>> tier1 = extract_tier1_summary(structure)
        >>> print(tier1.mission)
    """
    # Mission: First sentence of executive summary
    exec_summary = structure.get("executive_summary", "")
    mission = exec_summary.split(".")[0].strip() + "." if exec_summary else "Mission not specified"

    # Approach: Truncate to 1-2 sentences
    approach = structure.get("approach", "Approach not specified")
    approach_sentences = approach.split(".")[:2]  # Max 2 sentences
    approach = ". ".join(s.strip() for s in approach_sentences if s.strip()) + "."

    # Test summary
    test_plan = structure.get("test_plan", "")
    test_criteria_count = len(structure.get("acceptance_criteria", []))
    test_summary = test_plan if test_plan else f"{test_criteria_count} acceptance criteria to verify"

    # Deliverables
    deliverables = structure.get("deliverables", ["Implementation files"])

    # Constitutional status
    if structure.get("constitutional_compliance", False):
        const_status = ConstitutionalStatus.COMPLIANT
    elif structure.get("executive_summary", "") == "No executive summary found":
        const_status = ConstitutionalStatus.NON_COMPLIANT
    else:
        const_status = ConstitutionalStatus.NEEDS_REVIEW

    # Effort estimate
    effort = structure.get("effort", "Effort not estimated")

    # Risk level
    risk_str = structure.get("risk", "low")
    risk_level = RiskLevel.LOW if risk_str == "low" else (RiskLevel.HIGH if risk_str == "high" else RiskLevel.MEDIUM)

    # Calculate line count (estimate: ~4 lines per field)
    line_count = min(7 + len(deliverables), 25)  # 7 fields + deliverables, capped at 25

    return Tier1Summary(
        mission=mission[:500],  # Enforce max length
        approach=approach[:500],
        test_summary=test_summary[:300],
        deliverables=deliverables[:10],  # Max 10 deliverables
        constitutional_status=const_status,
        effort_estimate=effort[:50],
        risk_level=risk_level,
        line_count=line_count,
    )


def extract_tier2_decisions(structure: dict[str, Any]) -> Tier2Summary:
    """
    Extract Tier 2 key decisions from spec structure.

    Generates <50 line summary with:
    - 4-6 architectural decisions (title, choice, rationale, trade-offs)
    - Security implications
    - Dependencies

    Args:
        structure: Parsed spec structure from parse_spec_structure()

    Returns:
        Tier2Summary model

    Example:
        >>> tier2 = extract_tier2_decisions(structure)
        >>> print(len(tier2.decisions))
    """
    # Architectural decisions
    decision_dicts = structure.get("decisions", [])
    decisions = [
        ArchitecturalDecision(
            title=d["title"][:100],
            choice=d["choice"][:100],
            rationale=d["rationale"][:500],
            tradeoffs=d["tradeoffs"][:500],
        )
        for d in decision_dicts[:6]  # Max 6 decisions
    ]

    # Ensure at least 1 decision (use placeholder if none found)
    if not decisions:
        decisions = [
            ArchitecturalDecision(
                title="Implementation Approach",
                choice="Details in full specification",
                rationale="Architectural decisions not explicitly documented in spec",
                tradeoffs="See Tier 3 (full spec) for detailed implementation notes",
            )
        ]

    # Security implications (handle both string and list)
    security_raw = structure.get("security", "No security implications specified")
    if isinstance(security_raw, list):
        security = ", ".join(security_raw) if security_raw else "No security implications specified"
    else:
        security = security_raw

    # Dependencies (handle both string and list)
    dependencies_raw = structure.get("dependencies", "No dependencies specified")
    if isinstance(dependencies_raw, list):
        dependencies = ", ".join(dependencies_raw) if dependencies_raw else "No dependencies specified"
    else:
        dependencies = dependencies_raw

    # Calculate line count (estimate: ~6 lines per decision + security + deps)
    line_count = min(len(decisions) * 6 + 4, 50)  # Capped at 50

    return Tier2Summary(
        decisions=decisions,
        security_implications=security[:1000],
        dependencies=dependencies[:500],
        performance_notes=None,  # Optional field
        line_count=line_count,
    )


def create_tier3_reference(file_path: Path, line_count: int, section_count: int) -> Tier3Reference:
    """
    Create Tier 3 reference to full specification.

    Args:
        file_path: Path to full spec file (will be normalized to prevent path traversal)
        line_count: Total lines in specification
        section_count: Number of ## sections

    Returns:
        Tier3Reference model

    Security: Path normalized to prevent traversal attacks

    Example:
        >>> tier3 = create_tier3_reference(Path("spec.md"), 250, 8)
    """
    # Security: Normalize path to prevent traversal (e.g., ../../../etc/passwd)
    normalized_path = file_path.resolve()

    return Tier3Reference(
        file_path=normalized_path,
        line_count=line_count,
        section_count=section_count,
    )


__all__ = [
    "SpecTierGenerator",
    "parse_spec_structure",
    "extract_tier1_summary",
    "extract_tier2_decisions",
    "create_tier3_reference",
]
