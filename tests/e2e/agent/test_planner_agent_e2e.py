"""
Planner Agent E2E Tests - NECESSARY Pattern Compliance

End-to-end tests for PlannerAgent spec-to-plan workflow.

CONSTITUTIONAL MANDATE:
- Article IV: VectorStore integration (query patterns before planning)
- Article V: Spec-driven development (spec → plan transformation)
- ADR-037: E2E testing for multi-agent workflows

NECESSARY Coverage:
- Normal: Spec → Plan generation workflow
- Validation: VectorStore pattern reuse
- Edge: Complex specs, missing specs
- Error: Invalid spec format handling
"""

import pytest
from pathlib import Path


# =============================================================================
# NORMAL OPERATION TESTS
# =============================================================================


@pytest.mark.e2e
def test_planner_generates_plan_from_spec(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify PlannerAgent transforms spec.md into plan.md.

    Pattern: NECESSARY - Normal operation
    Workflow: spec.md → PlannerAgent → plan.md
    """
    from planner_agent.planner import PlannerAgent

    # Arrange: Create formal specification
    spec_file = tmp_git_repo / "specs" / "spec-001-user-auth.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("""
# Specification: User Authentication

## Goals
- Secure user login with JWT tokens
- Password hashing with bcrypt
- Session management

## Success Criteria
- Users can login with email/password
- Tokens expire after 24 hours
- Passwords are never stored in plaintext

## Personas
- End User: Needs secure login
- Admin: Needs to manage user accounts
""")

    # Act: Generate plan from spec
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan(
        spec_path=str(spec_file),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Plan generated successfully
    assert result.is_ok()
    plan_path = Path(result.unwrap())

    # Assert: Plan file exists
    assert plan_path.exists()
    assert plan_path.name == "plan-001-user-auth.md"

    # Assert: Plan contains required sections
    plan_content = plan_path.read_text()
    assert "## Architecture" in plan_content
    assert "## Implementation Steps" in plan_content
    assert "## Testing Strategy" in plan_content


@pytest.mark.e2e
def test_planner_generates_todowrite_tasks(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify PlannerAgent creates TodoWrite task breakdown.

    Pattern: NECESSARY - Normal operation
    Validates: Plan → TodoWrite integration
    """
    from planner_agent.planner import PlannerAgent

    # Arrange: Create spec
    spec_file = tmp_git_repo / "specs" / "spec-002-email-validation.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("""
# Specification: Email Validation

## Goals
- Validate email format
- Check for disposable email providers

## Success Criteria
- Rejects invalid formats
- Blocks disposable emails
""")

    # Act: Generate plan with tasks
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan_with_tasks(
        spec_path=str(spec_file),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Plan and tasks generated
    assert result.is_ok()
    plan_result = result.unwrap()

    assert "plan_path" in plan_result
    assert "tasks" in plan_result
    assert len(plan_result["tasks"]) > 0

    # Assert: Tasks follow TodoWrite format
    first_task = plan_result["tasks"][0]
    assert "content" in first_task
    assert "status" in first_task
    assert "activeForm" in first_task


# =============================================================================
# VALIDATION TESTS
# =============================================================================


@pytest.mark.e2e
def test_planner_queries_vectorstore_for_patterns(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify PlannerAgent queries VectorStore for similar plans (Article IV).

    Pattern: NECESSARY - Validation
    Constitutional: Article IV (VectorStore integration mandatory)
    """
    from planner_agent.planner import PlannerAgent

    # Arrange: Store successful plan pattern in VectorStore
    full_agent_context.store_memory(
        key="pattern_auth_plan",
        content={
            "pattern_type": "authentication_plan",
            "architecture": "JWT + bcrypt",
            "success_rate": 0.95,
            "steps": ["Model", "Repository", "Service", "API"]
        },
        tags=["planner", "pattern", "authentication", "success"]
    )

    # Arrange: Create auth spec
    spec_file = tmp_git_repo / "specs" / "spec-003-oauth.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("""
# Specification: OAuth Integration

## Goals
- Third-party authentication
- Google and GitHub providers
""")

    # Act: Generate plan
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan(
        spec_path=str(spec_file),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: VectorStore was queried
    assert result.is_ok()

    # Assert: Planner accessed stored patterns
    # (Verified through AgentContext telemetry)
    search_count = full_agent_context.get_metadata("vectorstore_searches", 0)
    assert search_count > 0


@pytest.mark.e2e
def test_planner_stores_successful_plan_pattern(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify PlannerAgent stores successful plans to VectorStore (Article IV).

    Pattern: NECESSARY - Validation
    Constitutional: Article IV (learning mandatory)
    """
    from planner_agent.planner import PlannerAgent

    # Arrange: Create spec
    spec_file = tmp_git_repo / "specs" / "spec-004-api-rate-limiting.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("""
# Specification: API Rate Limiting

## Goals
- Prevent API abuse
- 100 requests per minute per user
""")

    # Act: Generate plan
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan(
        spec_path=str(spec_file),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Plan generated
    assert result.is_ok()

    # Act: Search for stored pattern
    learnings = full_agent_context.search_memories(
        tags=["planner", "success"],
        query="rate limiting plan"
    )

    # Assert: Pattern was stored
    assert len(learnings) > 0
    assert any("rate" in str(learning).lower() for learning in learnings)


@pytest.mark.e2e
def test_planner_reuses_patterns_from_previous_plans(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify PlannerAgent reuses architecture patterns from past successful plans.

    Pattern: NECESSARY - Validation
    Validates: Cross-session learning
    """
    from planner_agent.planner import PlannerAgent

    planner = PlannerAgent(agent_context=full_agent_context)

    # Arrange: Generate first plan (establishes pattern)
    spec1 = tmp_git_repo / "specs" / "spec-005-crud-users.md"
    spec1.parent.mkdir(parents=True, exist_ok=True)
    spec1.write_text("""
# Specification: User CRUD

## Goals
- Create, Read, Update, Delete users
""")

    result1 = planner.generate_plan(
        spec_path=str(spec1),
        output_dir=str(tmp_git_repo / "plans")
    )
    assert result1.is_ok()

    # Act: Generate second similar plan (should reuse pattern)
    spec2 = tmp_git_repo / "specs" / "spec-006-crud-posts.md"
    spec2.write_text("""
# Specification: Post CRUD

## Goals
- Create, Read, Update, Delete blog posts
""")

    result2 = planner.generate_plan(
        spec_path=str(spec2),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Second plan generated
    assert result2.is_ok()

    # Assert: Second plan reused CRUD pattern
    plan2_content = Path(result2.unwrap()).read_text()
    assert "CRUD" in plan2_content or "Create, Read, Update, Delete" in plan2_content


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.e2e
def test_planner_handles_complex_multi_module_spec(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify PlannerAgent handles complex specifications with multiple modules.

    Pattern: NECESSARY - Edge case
    Validates: Scalability to large projects
    """
    from planner_agent.planner import PlannerAgent

    # Arrange: Complex spec with multiple modules
    spec_file = tmp_git_repo / "specs" / "spec-007-ecommerce-platform.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("""
# Specification: E-commerce Platform

## Goals
- User authentication
- Product catalog
- Shopping cart
- Payment processing
- Order management
- Inventory tracking

## Success Criteria
- 100+ concurrent users
- <200ms response time
- PCI compliance for payments
""")

    # Act: Generate plan
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan(
        spec_path=str(spec_file),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Plan handles complexity
    assert result.is_ok()
    plan_content = Path(result.unwrap()).read_text()

    # Assert: Plan includes all modules
    assert "authentication" in plan_content.lower()
    assert "catalog" in plan_content.lower()
    assert "cart" in plan_content.lower()
    assert "payment" in plan_content.lower()


@pytest.mark.e2e
def test_planner_handles_minimal_spec(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify PlannerAgent handles minimal specifications gracefully.

    Pattern: NECESSARY - Edge case
    Validates: Robustness to incomplete input
    """
    from planner_agent.planner import PlannerAgent

    # Arrange: Minimal spec
    spec_file = tmp_git_repo / "specs" / "spec-008-minimal.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("""
# Specification: Add Logging

## Goals
- Add logging to application
""")

    # Act: Generate plan
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan(
        spec_path=str(spec_file),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Plan generated despite minimal input
    assert result.is_ok()
    plan_content = Path(result.unwrap()).read_text()

    # Assert: Plan fills in reasonable defaults
    assert "logging" in plan_content.lower()
    assert len(plan_content) > 100  # Not just empty


# =============================================================================
# ERROR CONDITION TESTS
# =============================================================================


@pytest.mark.e2e
def test_planner_handles_missing_spec_file(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify PlannerAgent handles missing specification file gracefully.

    Pattern: NECESSARY - Error condition
    Validates: Input validation
    """
    from planner_agent.planner import PlannerAgent

    # Act: Try to generate plan from nonexistent spec
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan(
        spec_path=str(tmp_git_repo / "specs" / "nonexistent.md"),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Error reported
    assert result.is_err()
    error = result.error

    assert "not found" in str(error).lower() or "does not exist" in str(error).lower()


@pytest.mark.e2e
def test_planner_handles_invalid_spec_format(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify PlannerAgent handles invalid spec format.

    Pattern: NECESSARY - Error condition
    Validates: Format validation
    """
    from planner_agent.planner import PlannerAgent

    # Arrange: Invalid spec (not markdown, missing required sections)
    spec_file = tmp_git_repo / "specs" / "spec-009-invalid.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("""
This is not a valid specification format.
It has no sections or structure.
""")

    # Act: Try to generate plan
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan(
        spec_path=str(spec_file),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Plan still generated (or error is descriptive)
    if result.is_err():
        error = result.error
        assert "format" in str(error).lower() or "section" in str(error).lower()
    else:
        # Planner should attempt best-effort plan even with poor input
        assert result.is_ok()


# =============================================================================
# REGRESSION TESTS
# =============================================================================


@pytest.mark.e2e
def test_planner_maintains_spec_traceability(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify plan maintains traceability to original spec.

    Pattern: NECESSARY - Regression
    Validates: ADR-007 spec-driven development
    """
    from planner_agent.planner import PlannerAgent

    # Arrange: Create spec
    spec_file = tmp_git_repo / "specs" / "spec-010-feature-x.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("""
# Specification: Feature X

## Goals
- Goal 1
- Goal 2
""")

    # Act: Generate plan
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan(
        spec_path=str(spec_file),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Plan generated
    assert result.is_ok()
    plan_content = Path(result.unwrap()).read_text()

    # Assert: Plan references spec
    assert "spec-010" in plan_content or "Feature X" in plan_content

    # Assert: Plan goals trace to spec goals
    assert "Goal 1" in plan_content or "Goal 2" in plan_content


# =============================================================================
# ACCESSIBILITY TESTS
# =============================================================================


@pytest.mark.e2e
def test_planner_provides_human_readable_plan(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify plan is human-readable and well-structured.

    Pattern: NECESSARY - Accessibility
    Validates: Developer experience
    """
    from planner_agent.planner import PlannerAgent

    # Arrange: Create spec
    spec_file = tmp_git_repo / "specs" / "spec-011-readme.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("""
# Specification: Update README

## Goals
- Add installation instructions
- Add usage examples
""")

    # Act: Generate plan
    planner = PlannerAgent(agent_context=full_agent_context)

    result = planner.generate_plan(
        spec_path=str(spec_file),
        output_dir=str(tmp_git_repo / "plans")
    )

    # Assert: Plan is readable
    assert result.is_ok()
    plan_content = Path(result.unwrap()).read_text()

    # Assert: Proper markdown structure
    assert plan_content.startswith("#")
    assert "##" in plan_content  # Has sections

    # Assert: Clear step-by-step instructions
    assert "1." in plan_content or "-" in plan_content  # Numbered or bulleted lists
