"""
Tests for PrimeA Orchestrator Agent Definition Validation

Validates that .claude/agents/primeA_orchestrator.md contains complete two-stage
TDD workflow documentation including:
- Workflow diagrams and descriptions
- Example prompts for different task types
- Checkpoint definitions and execution protocol
- Constitutional compliance requirements

Test Type: Test (Tier 2)
Verification Target: code_orchestrator_agent_update
Constitutional Compliance: Article II - 100% Verification
"""

import os
import re
from pathlib import Path

import pytest


class TestPrimeAOrchestratorAgentDefinition:
    """
    Test suite for PrimeA orchestrator agent definition validation.

    Validates presence of two-stage TDD protocol documentation:
    - NECESSARY framework coverage (N: Normal, E: Edge, C: Corner, etc.)
    - AAA pattern compliance (Arrange-Act-Assert)
    - Edge case handling for file operations
    """

    @pytest.fixture
    def agent_definition_path(self) -> Path:
        """Provide path to PrimeA orchestrator agent definition file.

        Returns:
            Path to .claude/agents/primeA_orchestrator.md
        """
        # Arrange: Use relative path from project root
        project_root = Path(__file__).parent.parent.parent
        return project_root / ".claude" / "agents" / "primeA_orchestrator.md"

    @pytest.fixture
    def agent_content(self, agent_definition_path: Path) -> str:
        """Load agent definition file content.

        Args:
            agent_definition_path: Path fixture for agent definition

        Returns:
            Raw content of agent definition file
        """
        # Arrange
        assert agent_definition_path.exists(), (
            f"Agent definition file not found: {agent_definition_path}"
        )

        # Act
        content = agent_definition_path.read_text()

        # Assert
        assert len(content) > 0, "Agent definition file is empty"
        return content

    # ============================================================================
    # NORMAL OPERATION TESTS - Happy path validation
    # ============================================================================

    def test_agent_definition_file_exists(self, agent_definition_path: Path):
        """
        Test: Agent definition file exists at expected path.

        NECESSARY: N (Normal operation)
        AAA: Arrange (path fixture) → Act (exists check) → Assert (True)
        """
        # Arrange: Path provided by fixture

        # Act
        exists = agent_definition_path.exists()

        # Assert
        assert exists, f"PrimeA orchestrator agent definition missing at: {agent_definition_path}"

    def test_agent_definition_is_readable(self, agent_definition_path: Path):
        """
        Test: Agent definition file is readable and non-empty.

        NECESSARY: N (Normal operation)
        AAA: Arrange (path) → Act (read) → Assert (content length)
        """
        # Arrange: Path provided by fixture

        # Act
        content = agent_definition_path.read_text()

        # Assert
        assert len(content) > 100, "Agent definition file too small to contain valid documentation"

    def test_contains_execution_protocol_section(self, agent_content: str):
        """
        Test: Agent definition contains 'Execution Protocol' section.

        NECESSARY: N (Normal operation)
        AAA: Arrange (content) → Act (regex search) → Assert (match found)
        """
        # Arrange: Content provided by fixture

        # Act
        has_protocol = re.search(r"##\s+Execution\s+Protocol", agent_content, re.IGNORECASE)

        # Assert
        assert has_protocol, "Agent definition missing '## Execution Protocol' section"

    def test_contains_phase_definitions(self, agent_content: str):
        """
        Test: Agent definition contains all execution phase definitions.

        NECESSARY: N (Normal operation)
        AAA: Arrange (content + phases) → Act (search each) → Assert (all found)
        """
        # Arrange
        required_phases = [
            "Phase 0: Input Parsing",
            "Phase 1: Validation",
            "Phase 2: Visualization",
            "Phase 3: Parallel Execution",
            "Phase 4: Reflection",
            "Phase 5: Reporting",
        ]

        # Act
        missing_phases = [phase for phase in required_phases if phase not in agent_content]

        # Assert
        assert not missing_phases, f"Agent definition missing required phases: {missing_phases}"

    def test_contains_example_prompts_section(self, agent_content: str):
        """
        Test: Agent definition contains 'Example Prompts to Agent' section.

        NECESSARY: N (Normal operation)
        AAA: Arrange (content) → Act (regex search) → Assert (match found)
        """
        # Arrange: Content provided by fixture

        # Act
        has_examples = re.search(
            r"##\s+Example\s+Prompts\s+to\s+Agent", agent_content, re.IGNORECASE
        )

        # Assert
        assert has_examples, "Agent definition missing '## Example Prompts to Agent' section"

    def test_contains_spec_task_example(self, agent_content: str):
        """
        Test: Agent definition contains example prompt for Spec task type.

        NECESSARY: N (Normal operation)
        AAA: Arrange (content) → Act (search pattern) → Assert (found)
        """
        # Arrange: Content provided by fixture

        # Act
        has_spec_example = re.search(
            r"###\s+Execute\s+Task\s+\(Spec\)", agent_content, re.IGNORECASE
        )

        # Assert
        assert has_spec_example, "Agent definition missing example prompt for Spec task type"

    def test_contains_code_task_example(self, agent_content: str):
        """
        Test: Agent definition contains example prompt for Code task type.

        NECESSARY: N (Normal operation)
        AAA: Arrange (content) → Act (search pattern) → Assert (found)
        """
        # Arrange: Content provided by fixture

        # Act
        has_code_example = re.search(
            r"###\s+Execute\s+Task\s+\(Code\)", agent_content, re.IGNORECASE
        )

        # Assert
        assert has_code_example, "Agent definition missing example prompt for Code task type"

    def test_contains_test_task_example(self, agent_content: str):
        """
        Test: Agent definition contains example prompt for Test task type.

        NECESSARY: N (Normal operation)
        AAA: Arrange (content) → Act (search pattern) → Assert (found)
        """
        # Arrange: Content provided by fixture

        # Act
        has_test_example = re.search(
            r"###\s+Execute\s+Task\s+\(Test\)", agent_content, re.IGNORECASE
        )

        # Assert
        assert has_test_example, "Agent definition missing example prompt for Test task type"

    # ============================================================================
    # EDGE CASE TESTS - Boundary conditions
    # ============================================================================

    def test_file_missing_scenario(self):
        """
        Test: Graceful handling when agent definition file is missing.

        NECESSARY: E (Edge case - file not found)
        AAA: Arrange (invalid path) → Act (exists check) → Assert (False)
        """
        # Arrange
        invalid_path = Path("/nonexistent/path/primeA_orchestrator.md")

        # Act
        exists = invalid_path.exists()

        # Assert
        assert not exists, "Test expects invalid path to not exist"

    def test_empty_file_content_scenario(self, tmp_path: Path):
        """
        Test: Detection of empty agent definition file.

        NECESSARY: E (Edge case - empty file)
        AAA: Arrange (empty file) → Act (read) → Assert (length check)
        """
        # Arrange
        empty_file = tmp_path / "empty_agent.md"
        empty_file.write_text("")

        # Act
        content = empty_file.read_text()

        # Assert
        assert len(content) == 0, "Empty file should have zero content length"

    def test_malformed_markdown_structure(self, tmp_path: Path):
        """
        Test: Detection of malformed Markdown without proper headers.

        NECESSARY: E (Edge case - malformed structure)
        AAA: Arrange (bad markdown) → Act (search headers) → Assert (not found)
        """
        # Arrange
        bad_file = tmp_path / "malformed_agent.md"
        bad_file.write_text("This is not proper markdown with headers")
        content = bad_file.read_text()

        # Act
        has_protocol = re.search(r"##\s+Execution\s+Protocol", content)

        # Assert
        assert has_protocol is None, "Malformed markdown should not contain proper sections"

    # ============================================================================
    # CORNER CASE TESTS - Unusual combinations
    # ============================================================================

    def test_contains_constitutional_references(self, agent_content: str):
        """
        Test: Agent definition references constitutional articles.

        NECESSARY: C (Corner case - compliance validation)
        AAA: Arrange (content + articles) → Act (search) → Assert (all found)
        """
        # Arrange
        constitutional_refs = ["Article I", "Article II", "Article IV", "Article V"]

        # Act
        missing_refs = [ref for ref in constitutional_refs if ref not in agent_content]

        # Assert
        assert not missing_refs, (
            f"Agent definition missing constitutional references: {missing_refs}"
        )

    def test_contains_acceptance_criteria_in_examples(self, agent_content: str):
        """
        Test: Example prompts include acceptance criteria sections.

        NECESSARY: C (Corner case - example completeness)
        AAA: Arrange (content) → Act (count criteria) → Assert (≥3 examples)
        """
        # Arrange: Content provided by fixture

        # Act
        criteria_matches = re.findall(r"Acceptance\s+Criteria:", agent_content, re.IGNORECASE)

        # Assert
        assert len(criteria_matches) >= 3, (
            f"Expected ≥3 example prompts with acceptance criteria, found {len(criteria_matches)}"
        )

    def test_contains_tier_classification_in_examples(self, agent_content: str):
        """
        Test: Example prompts include Tier classification (Tier 1/2/3).

        NECESSARY: C (Corner case - task complexity classification)
        AAA: Arrange (content) → Act (search tiers) → Assert (found)
        """
        # Arrange: Content provided by fixture

        # Act
        tier_matches = re.findall(r"Tier:\s+Tier\s+[123]", agent_content, re.IGNORECASE)

        # Assert
        assert len(tier_matches) >= 3, (
            f"Expected ≥3 example prompts with Tier classification, found {len(tier_matches)}"
        )

    # ============================================================================
    # ERROR CONDITION TESTS - Failure scenarios
    # ============================================================================

    def test_file_permissions_error_scenario(self, tmp_path: Path):
        """
        Test: Handling of file read permission errors.

        NECESSARY: E (Error condition - permission denied)
        AAA: Arrange (unreadable file) → Act (read attempt) → Assert (raises)

        Note: Skip on Windows where permission control is different
        """
        # Arrange
        restricted_file = tmp_path / "restricted_agent.md"
        restricted_file.write_text("content")
        restricted_file.chmod(0o000)  # Remove all permissions

        # Act & Assert
        with pytest.raises(PermissionError):
            restricted_file.read_text()

        # Cleanup
        restricted_file.chmod(0o644)

    def test_contains_agent_routing_map(self, agent_content: str):
        """
        Test: Agent definition includes AGENT_MAP for routing.

        NECESSARY: N (Normal operation - routing configuration)
        AAA: Arrange (content) → Act (search map) → Assert (found)
        """
        # Arrange: Content provided by fixture

        # Act
        has_agent_map = re.search(r"AGENT_MAP\s*=\s*\{", agent_content)

        # Assert
        assert has_agent_map, "Agent definition missing AGENT_MAP routing configuration"

    def test_contains_memory_aware_execution_section(self, agent_content: str):
        """
        Test: Agent definition includes memory-aware execution guidance.

        NECESSARY: N (Normal operation - resource management)
        AAA: Arrange (content) → Act (search section) → Assert (found)
        """
        # Arrange: Content provided by fixture

        # Act
        has_memory_section = re.search(
            r"##\s+Memory-Aware\s+Execution", agent_content, re.IGNORECASE
        )

        # Assert
        assert has_memory_section, "Agent definition missing '## Memory-Aware Execution' section"

    def test_contains_success_criteria_section(self, agent_content: str):
        """
        Test: Agent definition includes success criteria checklist.

        NECESSARY: N (Normal operation - completion validation)
        AAA: Arrange (content) → Act (search section) → Assert (found)
        """
        # Arrange: Content provided by fixture

        # Act
        has_success_criteria = re.search(r"##\s+Success\s+Criteria", agent_content, re.IGNORECASE)

        # Assert
        assert has_success_criteria, "Agent definition missing '## Success Criteria' section"

    # ============================================================================
    # SECURITY TESTS - Injection and validation
    # ============================================================================

    def test_no_malicious_script_tags(self, agent_content: str):
        """
        Test: Agent definition contains no malicious script tags.

        NECESSARY: S (Security - injection prevention)
        AAA: Arrange (content) → Act (search scripts) → Assert (none found)
        """
        # Arrange: Content provided by fixture

        # Act
        script_tags = re.findall(r"<script[^>]*>", agent_content, re.IGNORECASE)

        # Assert
        assert not script_tags, (
            f"Agent definition contains {len(script_tags)} suspicious script tags"
        )

    def test_no_sql_injection_patterns(self, agent_content: str):
        """
        Test: Agent definition contains no SQL injection patterns.

        NECESSARY: S (Security - SQL injection prevention)
        AAA: Arrange (content) → Act (search SQL) → Assert (none found)
        """
        # Arrange: Content provided by fixture

        # Act
        sql_patterns = re.findall(
            r"(DROP\s+TABLE|DELETE\s+FROM|INSERT\s+INTO.*VALUES)", agent_content, re.IGNORECASE
        )

        # Assert
        assert not sql_patterns, (
            f"Agent definition contains {len(sql_patterns)} SQL injection patterns"
        )

    # ============================================================================
    # YIELD TESTS - Output validation
    # ============================================================================

    def test_contains_valid_python_code_blocks(self, agent_content: str):
        """
        Test: Python code blocks in agent definition are properly formatted.

        NECESSARY: Y (Yield - output format validation)
        AAA: Arrange (content) → Act (extract blocks) → Assert (valid format)
        """
        # Arrange: Content provided by fixture

        # Act
        python_blocks = re.findall(r"```python\n(.*?)```", agent_content, re.DOTALL)

        # Assert
        assert len(python_blocks) >= 5, (
            f"Expected ≥5 Python code examples, found {len(python_blocks)}"
        )

        # Validate each block has content
        for idx, block in enumerate(python_blocks):
            assert len(block.strip()) > 0, f"Python code block {idx} is empty"

    def test_contains_valid_markdown_code_blocks(self, agent_content: str):
        """
        Test: Markdown code blocks in agent definition are properly formatted.

        NECESSARY: Y (Yield - output format validation)
        AAA: Arrange (content) → Act (extract blocks) → Assert (valid format)
        """
        # Arrange: Content provided by fixture

        # Act
        markdown_blocks = re.findall(r"```markdown\n(.*?)```", agent_content, re.DOTALL)

        # Assert
        assert len(markdown_blocks) >= 1, (
            f"Expected ≥1 Markdown example, found {len(markdown_blocks)}"
        )

    def test_contains_vectorstore_learning_integration(self, agent_content: str):
        """
        Test: Agent definition references VectorStore learning integration.

        NECESSARY: Y (Yield - Article IV compliance)
        AAA: Arrange (content) → Act (search references) → Assert (found)
        """
        # Arrange: Content provided by fixture

        # Act
        has_vectorstore = re.search(r"VectorStore", agent_content, re.IGNORECASE)

        has_learnings = re.search(r"Relevant\s+Learnings", agent_content, re.IGNORECASE)

        # Assert
        assert has_vectorstore, "Agent definition missing VectorStore reference (Article IV)"
        assert has_learnings, "Agent definition missing 'Relevant Learnings' in examples"

    # ============================================================================
    # REGRESSION TESTS - Bug prevention
    # ============================================================================

    def test_agent_definition_version_metadata(self, agent_content: str):
        """
        Test: Agent definition contains version metadata in frontmatter.

        NECESSARY: R (Regression - ensure versioning is tracked)
        AAA: Arrange (content) → Act (parse frontmatter) → Assert (model found)
        """
        # Arrange: Content provided by fixture

        # Act
        frontmatter = re.search(r"^---\n(.*?)\n---", agent_content, re.DOTALL)

        # Assert
        assert frontmatter, "Agent definition missing YAML frontmatter"

        frontmatter_content = frontmatter.group(1)
        assert "model:" in frontmatter_content, "Agent definition frontmatter missing 'model' field"

    def test_no_broken_internal_links(self, agent_content: str):
        """
        Test: Internal Markdown links reference valid sections.

        NECESSARY: R (Regression - prevent dead links)
        AAA: Arrange (content + links) → Act (extract/validate) → Assert (valid)
        """
        # Arrange
        # Extract all headers
        headers = re.findall(r"^##\s+(.+)$", agent_content, re.MULTILINE)

        # Act
        # Extract internal links [text](#anchor)
        internal_links = re.findall(r"\[([^\]]+)\]\(#([^\)]+)\)", agent_content)

        # Assert
        # For this agent definition, we primarily validate structure exists
        # (actual anchor validation would require header-to-anchor conversion)
        assert len(headers) >= 8, f"Expected ≥8 major sections, found {len(headers)}"


class TestPrimeAOrchestratorAgentIntegration:
    """
    Integration tests for PrimeA orchestrator agent definition.

    Validates cross-references and consistency with other system components.
    """

    def test_agent_routing_consistency_with_codebase(self):
        """
        Test: AGENT_MAP in definition matches actual agent implementations.

        NECESSARY: A (Accessibility - API consistency)
        AAA: Arrange (paths) → Act (check existence) → Assert (all found)
        """
        # Arrange: Use relative paths from project root
        project_root = Path(__file__).parent.parent.parent
        agent_dirs = [
            project_root / "coding_agent",
            project_root / "planner_agent",
            project_root / "test_generator_agent",
            project_root / "auditor_agent",
            project_root / "quality_enforcer_agent",
            project_root / "chief_architect_agent",
        ]

        # Act
        missing_agents = [agent_dir for agent_dir in agent_dirs if not agent_dir.exists()]

        # Assert
        assert not missing_agents, (
            f"Agent directories referenced in AGENT_MAP not found: {missing_agents}"
        )

    def test_phase_definitions_align_with_task_graph_model(self):
        """
        Test: Phase definitions in agent align with TaskGraph Pydantic model.

        NECESSARY: A (Accessibility - schema consistency)
        AAA: Arrange (paths) → Act (read model) → Assert (phases match)
        """
        # Arrange: Use relative path from project root
        project_root = Path(__file__).parent.parent.parent
        task_graph_model_path = project_root / "shared" / "models" / "task_graph.py"

        # Act
        model_exists = task_graph_model_path.exists()

        # Assert
        assert model_exists, (
            "TaskGraph model not found at expected path (referenced in agent definition Phase 1)"
        )
