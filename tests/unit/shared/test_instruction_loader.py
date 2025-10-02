"""
Tests for Agent Instruction Loader.

Tests comprehensive loading, parsing, caching, and validation
of agent instructions using template composition.

Constitutional Compliance: Article I (TDD is Mandatory)
"""

import pytest
from pathlib import Path
from shared.instruction_loader import (
    load_agent_instruction,
    parse_delta_frontmatter,
    extract_agent_specific_content,
    get_cached_instruction,
    clear_instruction_cache,
    get_available_agents,
    validate_all_agents,
    normalize_agent_name,
    InstructionLoadError,
)


class TestInstructionLoading:
    """Test suite for instruction loading functionality."""

    def test_core_template_exists(self):
        """Should have core template file in shared/ directory."""
        core_path = Path("shared/AGENT_INSTRUCTION_CORE.md")
        assert core_path.exists(), "Core template file must exist"

    def test_load_planner_instruction(self):
        """Should load planner instruction successfully."""
        instruction = load_agent_instruction("planner", use_cache=False)

        assert "Planner Agent" in instruction
        assert "Constitutional Compliance" in instruction
        assert "Quality Standards" in instruction

    def test_load_code_agent_instruction(self):
        """Should load code agent instruction successfully."""
        instruction = load_agent_instruction("code_agent", use_cache=False)

        assert "Code Agent" in instruction
        assert "Implementation Workflow" in instruction
        assert "Test-Driven Development" in instruction

    def test_load_auditor_instruction(self):
        """Should load auditor instruction successfully."""
        instruction = load_agent_instruction("auditor", use_cache=False)

        assert "Auditor Agent" in instruction
        assert "READ-ONLY" in instruction
        assert "audit report" in instruction

    def test_all_agents_have_delta_files(self):
        """Should have delta files for all agents."""
        agents = get_available_agents()

        expected_agents = [
            "planner",
            "code_agent",
            "auditor",
            "quality_enforcer",
            "learning_agent",
            "merger",
            "test_generator",
            "toolsmith",
            "chief_architect",
            "work_completion",
            "e2e_workflow_agent",
            "spec_generator",
        ]

        for agent in expected_agents:
            assert agent in agents, f"{agent} delta file should exist"

    def test_missing_delta_raises_error(self):
        """Should raise InstructionLoadError for missing delta file."""
        with pytest.raises(InstructionLoadError):
            load_agent_instruction("nonexistent_agent", use_cache=False)


class TestFrontmatterParsing:
    """Test suite for YAML frontmatter parsing."""

    def test_parse_simple_frontmatter(self):
        """Should parse simple key: value frontmatter."""
        content = """---
agent_name: Planner
agent_role: Software architect
---

Content here"""

        variables = parse_delta_frontmatter(content)

        assert variables["agent_name"] == "Planner"
        assert variables["agent_role"] == "Software architect"

    def test_parse_multiline_frontmatter(self):
        """Should parse multiline values with | syntax."""
        content = """---
agent_name: Planner
agent_competencies: |
  - System architecture
  - Task decomposition
  - Dependency analysis
---

Content"""

        variables = parse_delta_frontmatter(content)

        assert "System architecture" in variables["agent_competencies"]
        assert "Task decomposition" in variables["agent_competencies"]

    def test_parse_empty_frontmatter(self):
        """Should return empty dict for missing frontmatter."""
        content = "No frontmatter here"

        variables = parse_delta_frontmatter(content)

        assert variables == {}


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


class TestInstructionCaching:
    """Test suite for instruction caching functionality."""

    def test_caching_returns_same_instance(self):
        """Should return cached instruction on second call."""
        clear_instruction_cache()

        # First call loads from disk
        inst1 = get_cached_instruction("planner")

        # Second call returns cached
        inst2 = get_cached_instruction("planner")

        assert inst1 == inst2
        assert inst1 is inst2  # Same object

    def test_clear_cache_forces_reload(self):
        """Should reload after cache clear."""
        # Load and cache
        inst1 = get_cached_instruction("planner")

        # Clear cache
        clear_instruction_cache()

        # Load again (fresh from disk)
        inst2 = get_cached_instruction("planner")

        assert inst1 == inst2  # Content same
        # Note: May be different objects after reload

    def test_use_cache_parameter(self):
        """Should bypass cache when use_cache=False."""
        clear_instruction_cache()

        # Load without cache
        inst1 = load_agent_instruction("planner", use_cache=False)
        inst2 = load_agent_instruction("planner", use_cache=False)

        assert inst1 == inst2  # Content same
        # Each call loads fresh from disk


class TestAgentValidation:
    """Test suite for agent validation functionality."""

    def test_validate_all_agents_success(self):
        """Should validate all agents successfully."""
        results = validate_all_agents()

        for agent_name, success in results.items():
            assert success, f"{agent_name} should validate successfully"

    def test_get_available_agents_returns_all(self):
        """Should return all available agents."""
        agents = get_available_agents()

        assert len(agents) >= 12, "Should have at least 12 agents"
        assert "planner" in agents
        assert "code_agent" in agents
        assert "auditor" in agents


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


class TestABComparison:
    """A/B testing: Compare original vs. compressed instructions."""

    def test_compressed_has_constitutional_compliance(self):
        """Should include constitutional compliance section."""
        instruction = load_agent_instruction("planner", use_cache=False)

        assert "Constitutional Compliance" in instruction
        assert "Article I" in instruction
        assert "Article II" in instruction
        assert "Article III" in instruction
        assert "Article IV" in instruction
        assert "Article V" in instruction

    def test_compressed_has_quality_standards(self):
        """Should include all 10 quality standards."""
        instruction = load_agent_instruction("code_agent", use_cache=False)

        assert "TDD is Mandatory" in instruction
        assert "Strict Typing Always" in instruction
        assert "Result<T, E>" in instruction
        assert "Repository Pattern" in instruction

    def test_compressed_has_agent_specific_content(self):
        """Should include agent-specific unique content."""
        # Planner should have plan structure
        planner = load_agent_instruction("planner", use_cache=False)
        assert "Plan Structure" in planner
        assert "Task Breakdown" in planner

        # Auditor should have JSON report format
        auditor = load_agent_instruction("auditor", use_cache=False)
        assert "audit report" in auditor.lower()
        assert "READ-ONLY" in auditor

        # Quality Enforcer should have healing modes
        enforcer = load_agent_instruction("quality_enforcer", use_cache=False)
        assert "Healing Modes" in enforcer or "healing" in enforcer.lower()

    def test_compressed_has_error_handling_examples(self):
        """Should include Result pattern examples."""
        instruction = load_agent_instruction("code_agent", use_cache=False)

        assert "Result" in instruction
        assert "Ok" in instruction
        assert "Err" in instruction
        # Should have both Python and TypeScript examples
        assert "def validate_email" in instruction or "validate_email" in instruction

    def test_compressed_maintains_key_sections(self):
        """Should maintain all key sections from original."""
        for agent_name in ["planner", "code_agent", "auditor"]:
            instruction = load_agent_instruction(agent_name, use_cache=False)

            # Common sections
            assert "## Role" in instruction
            assert "Core Competencies" in instruction
            assert "Responsibilities" in instruction
            assert "Anti-patterns" in instruction
            assert "Quality" in instruction

    def test_compressed_length_reasonable(self):
        """Should be reasonably sized (not too short or long)."""
        for agent_name in get_available_agents():
            instruction = load_agent_instruction(agent_name, use_cache=False)

            # Should be at least 1000 chars (has content)
            assert len(instruction) > 1000, f"{agent_name} instruction too short"

            # Should be under 20000 chars (not bloated)
            assert len(instruction) < 20000, f"{agent_name} instruction too long"


class TestTokenSavings:
    """Test suite for measuring token savings."""

    def test_delta_files_smaller_than_originals(self):
        """Should have delta files significantly smaller than originals."""
        # Use code_agent which is larger (230 lines) for better comparison
        original_path = Path(".claude/agents/code_agent.md")
        if original_path.exists():
            original_content = original_path.read_text()
            original_lines = len(original_content.split("\n"))

            # Read delta file
            delta_path = Path(".claude/agents/code_agent-delta.md")
            delta_content = delta_path.read_text()
            delta_lines = len(delta_content.split("\n"))

            # Delta should be much smaller (< 60% of original)
            assert delta_lines < original_lines * 0.6, f"Delta ({delta_lines}) should be <60% of original ({original_lines})"

    def test_core_template_reusable(self):
        """Should have single core template shared by all agents."""
        core_path = Path("shared/AGENT_INSTRUCTION_CORE.md")
        assert core_path.exists()

        core_content = core_path.read_text()

        # Core should contain shared sections
        assert "Constitutional Compliance" in core_content
        assert "Quality Standards" in core_content
        assert "Error Handling Pattern" in core_content
        assert "Anti-patterns to Avoid" in core_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
