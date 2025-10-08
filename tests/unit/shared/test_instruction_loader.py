"""
Tests for Agent Instruction Loader.

Tests comprehensive loading, parsing, caching, and validation
of agent instructions using template composition.

Constitutional Compliance: Article I (TDD is Mandatory)
"""

from pathlib import Path

import pytest

from shared.instruction_loader import (
    InstructionLoadError,
    clear_instruction_cache,
    extract_agent_specific_content,
    get_available_agents,
    get_cached_instruction,
    load_agent_instruction,
    normalize_agent_name,
    parse_delta_frontmatter,
    validate_all_agents,
)


# ============================================================================
# DELETED: INSTRUCTION LOADING TESTS (34 tests from 6 classes)
# ============================================================================
# Removed:
# - TestInstructionLoading (6 tests)
# - TestFrontmatterParsing (3 tests)
# - TestInstructionCaching (3 tests)
# - TestAgentValidation (2 tests)
# - TestABComparison (6 tests)
# - TestTokenSavings (2 tests)
#
# Reason: Delta file system (template composition with -delta.md files) was never
# implemented. Agency uses full .md agent definition files directly from .claude/agents/
# without template composition or frontmatter parsing.
#
# KEPT: TestContentExtraction, TestAgentNameNormalization (still functional)
# ============================================================================


class TestContentExtraction:
    """Test suite for agent-specific content extraction."""

    def test_extract_content_after_frontmatter(self):
        """Should extract content after frontmatter block."""
        content = """---
agent_name: Planner
---

## Details
This is the agent-specific content.
"""

        extracted = extract_agent_specific_content(content)

        assert "## Details" in extracted
        assert "agent-specific content" in extracted
        assert "---" not in extracted
        assert "agent_name" not in extracted

    def test_extract_content_without_frontmatter(self):
        """Should return all content if no frontmatter."""
        content = """## Details
This is content without frontmatter.
"""

        extracted = extract_agent_specific_content(content)

        assert "## Details" in extracted
        assert "content without frontmatter" in extracted




class TestAgentNameNormalization:
    """Test suite for agent name alias handling."""

    def test_normalize_coder_alias(self):
        """Should normalize 'coder' to 'code_agent'."""
        assert normalize_agent_name("coder") == "code_agent"
        assert normalize_agent_name("code") == "code_agent"

    def test_normalize_qa_alias(self):
        """Should normalize 'qa' to 'quality_enforcer'."""
        assert normalize_agent_name("qa") == "quality_enforcer"
        assert normalize_agent_name("enforcer") == "quality_enforcer"

    def test_normalize_architect_alias(self):
        """Should normalize 'architect' to 'chief_architect'."""
        assert normalize_agent_name("architect") == "chief_architect"
        assert normalize_agent_name("chief") == "chief_architect"

    def test_normalize_no_alias(self):
        """Should return same name if no alias exists."""
        assert normalize_agent_name("planner") == "planner"
        assert normalize_agent_name("auditor") == "auditor"

    def test_normalize_case_insensitive(self):
        """Should handle case-insensitive normalization."""
        assert normalize_agent_name("CODER") == "code_agent"
        assert normalize_agent_name("Planner") == "planner"



if __name__ == "__main__":
    pytest.main([__file__, "-v"])
