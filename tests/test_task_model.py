"""
Tests for Task model Pydantic validation.

Tests validate Task model schema compliance, field validation, and serialization
following NECESSARY pattern (Normal, Edge, Cascading, Essential, Security,
Spec, Accessibility, Resilience, Year-round).

Constitutional Compliance:
- Article I: Complete context (all Task fields validated)
- Article II: 100% verification (comprehensive test coverage)
- Article IV: Learning integration (pydantic_model_instantiation pattern)

Test Coverage:
- Normal: Valid Task creation with all required fields
- Edge: Invalid task IDs, unknown agents, missing fields
- Essential: Pydantic validation enforcement
- Spec: Article II TDD requirement (Test tasks need verification_target)
"""

import pytest
from pydantic import ValidationError

from shared.models.task_graph import Task, TaskTier, TaskType


class TestTaskCreation:
    """Test normal Task model instantiation with valid data."""

    def test_task_creation_with_all_required_fields(self):
        """Test Task creation with all required fields (Normal case)."""
        # Arrange
        task_data = {
            "id": "test_auth_implementation",
            "title": "Implement JWT authentication",
            "type": TaskType.CODE,
            "tier": TaskTier.TIER_2,
            "agent": "coder",
            "description": "Implement JWT authentication with RSA-256 signing",
        }

        # Act
        task = Task(**task_data)

        # Assert
        assert task.id == "test_auth_implementation"
        assert task.title == "Implement JWT authentication"
        assert task.type == TaskType.CODE
        assert task.tier == TaskTier.TIER_2
        assert task.agent == "coder"
        assert task.description == "Implement JWT authentication with RSA-256 signing"
        assert task.dependencies == []  # Default empty list
        assert task.acceptance_criteria == []  # Default empty list
        assert task.estimated_tokens is None
        assert task.verification_target is None
        assert task.result is None
        assert task.metadata == {}  # Default empty dict

    def test_task_creation_with_optional_fields(self):
        """Test Task creation with optional fields populated."""
        # Arrange
        task_data = {
            "id": "test_api_endpoint",
            "title": "Test API endpoint",
            "type": TaskType.TEST,
            "tier": TaskTier.TIER_3,
            "agent": "test_generator",
            "description": "Generate comprehensive tests for API endpoint",
            "dependencies": ["implement_api_endpoint"],
            "acceptance_criteria": ["100% code coverage", "All edge cases tested"],
            "estimated_tokens": 3000,
            "verification_target": "implement_api_endpoint",
            "result": {"tests_passed": True, "coverage": 0.98},
            "metadata": {"priority": "high", "spec_id": "spec-042"},
        }

        # Act
        task = Task(**task_data)

        # Assert
        assert task.dependencies == ["implement_api_endpoint"]
        assert task.acceptance_criteria == ["100% code coverage", "All edge cases tested"]
        assert task.estimated_tokens == 3000
        assert task.verification_target == "implement_api_endpoint"
        assert task.result == {"tests_passed": True, "coverage": 0.98}
        assert task.metadata == {"priority": "high", "spec_id": "spec-042"}

    def test_task_creation_with_spec_type(self):
        """Test Spec task creation with acceptance criteria."""
        # Arrange
        spec_task_data = {
            "id": "spec_authentication",
            "title": "Design authentication specification",
            "type": TaskType.SPEC,
            "tier": TaskTier.TIER_1,
            "agent": "planner",
            "description": "Create comprehensive authentication specification",
            "acceptance_criteria": [
                "Security requirements defined",
                "Token lifecycle documented",
                "Error handling specified",
            ],
        }

        # Act
        task = Task(**spec_task_data)

        # Assert
        assert task.type == TaskType.SPEC
        assert len(task.acceptance_criteria) == 3
        assert "Security requirements defined" in task.acceptance_criteria

    def test_task_creation_all_tier_levels(self):
        """Test Task creation for all tier levels (Tier 1, 2, 3)."""
        # Arrange & Act & Assert
        for tier in [TaskTier.TIER_1, TaskTier.TIER_2, TaskTier.TIER_3]:
            task = Task(
                id=f"task_{tier.value.lower().replace(' ', '_')}",
                title=f"Task for {tier.value}",
                type=TaskType.CODE,
                tier=tier,
                agent="coder",
                description=f"Task at {tier.value} complexity",
            )
            assert task.tier == tier

    def test_task_creation_all_agent_types(self):
        """Test Task creation for all valid agent types."""
        # Arrange
        valid_agents = [
            "planner",
            "chief_architect",
            "coder",
            "auditor",
            "test_generator",
            "quality_enforcer",
            "learning",
            "merger",
            "toolsmith",
            "summary",
        ]

        # Act & Assert
        for agent_name in valid_agents:
            task = Task(
                id=f"task_{agent_name}",
                title=f"Task for {agent_name}",
                type=TaskType.CODE,
                tier=TaskTier.TIER_2,
                agent=agent_name,
                description=f"Task assigned to {agent_name}",
            )
            assert task.agent == agent_name


class TestTaskValidation:
    """Test Task model validation rules (Edge cases and error handling)."""

    def test_edge_invalid_task_id_with_special_characters(self):
        """Test Task validation rejects IDs with special characters (Edge case)."""
        # Arrange
        invalid_task_data = {
            "id": "test-auth-impl!@#",  # Special characters not allowed
            "title": "Test task",
            "type": TaskType.CODE,
            "tier": TaskTier.TIER_2,
            "agent": "coder",
            "description": "Test description",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Task(**invalid_task_data)

        # Assert validation message
        assert "Task ID must be alphanumeric with underscores" in str(exc_info.value)

    def test_edge_invalid_task_id_with_spaces(self):
        """Test Task validation rejects IDs with spaces (Edge case)."""
        # Arrange
        invalid_task_data = {
            "id": "test auth impl",  # Spaces not allowed
            "title": "Test task",
            "type": TaskType.CODE,
            "tier": TaskTier.TIER_2,
            "agent": "coder",
            "description": "Test description",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Task(**invalid_task_data)

        assert "Task ID must be alphanumeric with underscores" in str(exc_info.value)

    def test_edge_unknown_agent_name(self):
        """Test Task validation rejects unknown agent names (Edge case)."""
        # Arrange
        invalid_task_data = {
            "id": "test_task",
            "title": "Test task",
            "type": TaskType.CODE,
            "tier": TaskTier.TIER_2,
            "agent": "unknown_agent",  # Not in valid agent list
            "description": "Test description",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Task(**invalid_task_data)

        assert "Unknown agent" in str(exc_info.value)
        assert "unknown_agent" in str(exc_info.value)

    def test_edge_test_task_missing_verification_target(self):
        """Test Task validation enforces verification_target for Test tasks (Edge case, Article II)."""
        # Arrange
        invalid_test_task = {
            "id": "test_feature",
            "title": "Test feature",
            "type": TaskType.TEST,
            "tier": TaskTier.TIER_3,
            "agent": "test_generator",
            "description": "Test description",
            # Missing verification_target - violates Article II
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Task(**invalid_test_task)

        # Assert Article II enforcement
        assert "missing verification_target" in str(exc_info.value)
        assert "Article II" in str(exc_info.value)

    def test_edge_missing_required_field_id(self):
        """Test Task validation rejects missing required field 'id' (Edge case)."""
        # Arrange
        invalid_task_data = {
            # Missing "id" field
            "title": "Test task",
            "type": TaskType.CODE,
            "tier": TaskTier.TIER_2,
            "agent": "coder",
            "description": "Test description",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Task(**invalid_task_data)

        assert "Field required" in str(exc_info.value)

    def test_edge_missing_required_field_agent(self):
        """Test Task validation rejects missing required field 'agent' (Edge case)."""
        # Arrange
        invalid_task_data = {
            "id": "test_task",
            "title": "Test task",
            "type": TaskType.CODE,
            "tier": TaskTier.TIER_2,
            # Missing "agent" field
            "description": "Test description",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Task(**invalid_task_data)

        assert "Field required" in str(exc_info.value)

    def test_edge_missing_required_field_description(self):
        """Test Task validation rejects missing required field 'description' (Edge case)."""
        # Arrange
        invalid_task_data = {
            "id": "test_task",
            "title": "Test task",
            "type": TaskType.CODE,
            "tier": TaskTier.TIER_2,
            "agent": "coder",
            # Missing "description" field
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Task(**invalid_task_data)

        assert "Field required" in str(exc_info.value)

    def test_spec_task_without_acceptance_criteria_warning_only(self):
        """Test Spec task without acceptance criteria (warning, not error)."""
        # Arrange
        spec_task_data = {
            "id": "spec_feature",
            "title": "Feature specification",
            "type": TaskType.SPEC,
            "tier": TaskTier.TIER_1,
            "agent": "planner",
            "description": "Specification description",
            # Missing acceptance_criteria (should warn, not error)
        }

        # Act
        task = Task(**spec_task_data)

        # Assert - Should create successfully (backward compatibility)
        assert task.type == TaskType.SPEC
        assert task.acceptance_criteria == []  # Empty list default


class TestTaskSerialization:
    """Test Task model serialization and deserialization (Pydantic patterns)."""

    def test_task_serialization_to_dict(self):
        """Test Task serialization to dictionary (model_dump)."""
        # Arrange
        task = Task(
            id="test_serialization",
            title="Test serialization",
            type=TaskType.CODE,
            tier=TaskTier.TIER_2,
            agent="coder",
            description="Test Pydantic serialization",
            dependencies=["task_1", "task_2"],
            estimated_tokens=5000,
            metadata={"priority": "high"},
        )

        # Act
        task_dict = task.model_dump()

        # Assert
        assert isinstance(task_dict, dict)
        assert task_dict["id"] == "test_serialization"
        assert task_dict["type"] == "Code"  # Enum serialized to value
        assert task_dict["tier"] == "Tier 2"  # Enum serialized to value
        assert task_dict["agent"] == "coder"
        assert task_dict["dependencies"] == ["task_1", "task_2"]
        assert task_dict["estimated_tokens"] == 5000
        assert task_dict["metadata"] == {"priority": "high"}

    def test_task_deserialization_from_dict(self):
        """Test Task deserialization from dictionary (model_validate)."""
        # Arrange
        task_dict = {
            "id": "test_deserialization",
            "title": "Test deserialization",
            "type": "Code",  # String value, will be converted to enum
            "tier": "Tier 2",  # String value, will be converted to enum
            "agent": "coder",
            "description": "Test Pydantic deserialization",
            "dependencies": ["dep_1"],
            "acceptance_criteria": [],
            "estimated_tokens": 3000,
            "verification_target": None,
            "result": None,
            "metadata": {},
        }

        # Act
        task = Task.model_validate(task_dict)

        # Assert
        assert task.id == "test_deserialization"
        assert task.type == TaskType.CODE
        assert task.tier == TaskTier.TIER_2
        assert task.agent == "coder"
        assert task.dependencies == ["dep_1"]
        assert task.estimated_tokens == 3000

    def test_task_serialization_json_round_trip(self):
        """Test Task JSON serialization round-trip (model_dump_json + model_validate_json)."""
        # Arrange
        original_task = Task(
            id="test_json_roundtrip",
            title="JSON round trip test",
            type=TaskType.TEST,
            tier=TaskTier.TIER_3,
            agent="test_generator",
            description="Test JSON serialization round trip",
            dependencies=["code_task"],
            verification_target="code_task",
            metadata={"test_framework": "pytest"},
        )

        # Act - Serialize to JSON
        task_json = original_task.model_dump_json()

        # Act - Deserialize from JSON
        restored_task = Task.model_validate_json(task_json)

        # Assert - Round trip preserves data
        assert restored_task.id == original_task.id
        assert restored_task.title == original_task.title
        assert restored_task.type == original_task.type
        assert restored_task.tier == original_task.tier
        assert restored_task.agent == original_task.agent
        assert restored_task.description == original_task.description
        assert restored_task.dependencies == original_task.dependencies
        assert restored_task.verification_target == original_task.verification_target
        assert restored_task.metadata == original_task.metadata

    def test_task_serialization_with_result_field(self):
        """Test Task serialization with result field (dict[str, Any])."""
        # Arrange
        task = Task(
            id="completed_task",
            title="Completed task",
            type=TaskType.CODE,
            tier=TaskTier.TIER_2,
            agent="coder",
            description="Task with result",
            result={
                "files_modified": ["auth.py", "test_auth.py"],
                "tests_passed": True,
                "coverage": 0.95,
            },
        )

        # Act
        task_dict = task.model_dump()

        # Assert
        assert "result" in task_dict
        assert task_dict["result"]["files_modified"] == ["auth.py", "test_auth.py"]
        assert task_dict["result"]["tests_passed"] is True
        assert task_dict["result"]["coverage"] == 0.95


class TestTaskTypeAssertions:
    """Test Task model type assertions and Pydantic enforcement."""

    def test_essential_pydantic_validation_enforces_types(self):
        """Test Pydantic enforces type validation (Essential case)."""
        # Arrange
        invalid_task_data = {
            "id": "test_task",
            "title": "Test task",
            "type": "InvalidType",  # Invalid enum value
            "tier": TaskTier.TIER_2,
            "agent": "coder",
            "description": "Test description",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Task(**invalid_task_data)

        # Assert Pydantic validation
        assert "Input should be" in str(exc_info.value)

    def test_essential_task_type_enum_values(self):
        """Test TaskType enum has expected values (Essential case)."""
        # Assert
        assert TaskType.SPEC == "Spec"
        assert TaskType.CODE == "Code"
        assert TaskType.TEST == "Test"

    def test_essential_task_tier_enum_values(self):
        """Test TaskTier enum has expected values (Essential case)."""
        # Assert
        assert TaskTier.TIER_1 == "Tier 1"
        assert TaskTier.TIER_2 == "Tier 2"
        assert TaskTier.TIER_3 == "Tier 3"

    def test_essential_dependencies_default_to_empty_list(self):
        """Test dependencies field defaults to empty list (Essential case)."""
        # Arrange & Act
        task = Task(
            id="test_task",
            title="Test task",
            type=TaskType.CODE,
            tier=TaskTier.TIER_2,
            agent="coder",
            description="Test description",
        )

        # Assert
        assert task.dependencies == []
        assert isinstance(task.dependencies, list)

    def test_essential_metadata_default_to_empty_dict(self):
        """Test metadata field defaults to empty dict (Essential case)."""
        # Arrange & Act
        task = Task(
            id="test_task",
            title="Test task",
            type=TaskType.CODE,
            tier=TaskTier.TIER_2,
            agent="coder",
            description="Test description",
        )

        # Assert
        assert task.metadata == {}
        assert isinstance(task.metadata, dict)


class TestTaskArticleIICompliance:
    """Test Article II TDD compliance (Test tasks require verification_target)."""

    def test_spec_test_task_with_verification_target_valid(self):
        """Test Test task with verification_target passes validation (Spec case, Article II)."""
        # Arrange
        test_task_data = {
            "id": "test_auth",
            "title": "Test authentication",
            "type": TaskType.TEST,
            "tier": TaskTier.TIER_3,
            "agent": "test_generator",
            "description": "Generate authentication tests",
            "verification_target": "implement_auth",  # Required for Test tasks
        }

        # Act
        task = Task(**test_task_data)

        # Assert
        assert task.type == TaskType.TEST
        assert task.verification_target == "implement_auth"

    def test_spec_code_task_without_verification_target_valid(self):
        """Test Code task without verification_target is valid (Spec case)."""
        # Arrange
        code_task_data = {
            "id": "implement_feature",
            "title": "Implement feature",
            "type": TaskType.CODE,
            "tier": TaskTier.TIER_2,
            "agent": "coder",
            "description": "Implement new feature",
            # verification_target not required for Code tasks
        }

        # Act
        task = Task(**code_task_data)

        # Assert
        assert task.type == TaskType.CODE
        assert task.verification_target is None
