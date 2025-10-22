"""
Tests for SessionState task progress tracking and memory management.

Tests Pydantic model methods for:
- Task progress tracking (update_task_progress, get_task_progress)
- Active agent state queries (get_active_agent_states)
- Memory reference management (add_memory_reference)
- Task context resume (resume_task_context)

Constitutional Compliance:
- Article II (Law #1): TDD - tests written BEFORE implementation
- Article II (Law #2): Strict typing with Pydantic
- ADR-008: No Dict[Any, Any] usage
"""

from datetime import datetime

import pytest

from shared.models.session import SessionState, SessionStatus


class TestTaskProgressTracking:
    """Test suite for task progress tracking methods."""

    def test_get_task_progress_with_valid_data(self):
        """Test get_task_progress returns TaskProgress summary."""
        session = SessionState(
            session_id="session_test_001",
            agent_name="planner",
            status=SessionStatus.RUNNING,
            task_id="feat_auth",
            task_type="feature_implementation",
            task_progress_percent=45.0,
            completed_steps=["spec", "plan", "schema_design"],
            pending_steps=["implementation", "tests", "merge"],
        )

        progress = session.get_task_progress()

        assert progress.task_id == "feat_auth"
        assert progress.task_type == "feature_implementation"
        assert progress.progress_percent == 45.0
        assert progress.completed_steps == ["spec", "plan", "schema_design"]
        assert progress.pending_steps == ["implementation", "tests", "merge"]
        assert progress.total_steps == 6

    def test_get_task_progress_with_no_task(self):
        """Test get_task_progress when no task is active."""
        session = SessionState(
            session_id="session_test_002",
            agent_name="planner",
            status=SessionStatus.PENDING,
        )

        progress = session.get_task_progress()

        assert progress.task_id == ""
        assert progress.task_type == ""
        assert progress.progress_percent == 0.0
        assert progress.total_steps == 0

    def test_update_task_progress_marks_step_completed(self):
        """Test update_task_progress moves step from pending to completed."""
        session = SessionState(
            session_id="session_test_003",
            agent_name="coder",
            task_id="feat_auth",
            task_type="feature_implementation",
            task_progress_percent=45.0,
            completed_steps=["spec", "plan"],
            pending_steps=["implementation", "tests", "merge"],
        )

        session.update_task_progress("implementation")

        assert "implementation" in session.completed_steps
        assert "implementation" not in session.pending_steps
        assert session.completed_steps == ["spec", "plan", "implementation"]
        assert session.pending_steps == ["tests", "merge"]

    def test_update_task_progress_updates_percentage(self):
        """Test update_task_progress auto-calculates progress percentage."""
        session = SessionState(
            session_id="session_test_004",
            agent_name="coder",
            task_id="feat_auth",
            task_type="feature_implementation",
            task_progress_percent=0.0,
            completed_steps=[],
            pending_steps=["spec", "plan", "implementation", "tests"],
        )

        # Complete 1 of 4 steps = 25%
        session.update_task_progress("spec")
        assert session.task_progress_percent == 25.0

        # Complete 2 of 4 steps = 50%
        session.update_task_progress("plan")
        assert session.task_progress_percent == 50.0

        # Complete 3 of 4 steps = 75%
        session.update_task_progress("implementation")
        assert session.task_progress_percent == 75.0

        # Complete 4 of 4 steps = 100%
        session.update_task_progress("tests")
        assert session.task_progress_percent == 100.0

    def test_update_task_progress_idempotent(self):
        """Test update_task_progress is idempotent (no duplicates)."""
        session = SessionState(
            session_id="session_test_005",
            agent_name="coder",
            task_id="feat_auth",
            completed_steps=["spec"],
            pending_steps=["plan", "tests"],
        )

        # Update same step twice
        session.update_task_progress("plan")
        session.update_task_progress("plan")

        assert session.completed_steps.count("plan") == 1
        assert session.pending_steps == ["tests"]

    def test_update_task_progress_handles_nonexistent_step(self):
        """Test update_task_progress handles step not in pending list."""
        session = SessionState(
            session_id="session_test_006",
            agent_name="coder",
            task_id="feat_auth",
            completed_steps=["spec"],
            pending_steps=["plan"],
        )

        # Update step not in pending list (should still add to completed)
        session.update_task_progress("adhoc_refactor")

        assert "adhoc_refactor" in session.completed_steps
        assert session.pending_steps == ["plan"]


class TestMemoryReferenceManagement:
    """Test suite for memory reference management."""

    def test_add_memory_reference_appends_to_active_refs(self):
        """Test add_memory_reference adds key to active_memory_refs."""
        session = SessionState(
            session_id="session_test_007",
            agent_name="planner",
            active_memory_refs=[],
        )

        session.add_memory_reference("mem_context_plan", pinned=False)

        assert "mem_context_plan" in session.active_memory_refs
        assert "mem_context_plan" not in session.pinned_memories

    def test_add_memory_reference_with_pinned_flag(self):
        """Test add_memory_reference adds to pinned_memories when flagged."""
        session = SessionState(
            session_id="session_test_008",
            agent_name="planner",
            active_memory_refs=[],
            pinned_memories=[],
        )

        session.add_memory_reference("mem_constitution", pinned=True)

        assert "mem_constitution" in session.active_memory_refs
        assert "mem_constitution" in session.pinned_memories

    def test_add_memory_reference_no_duplicates(self):
        """Test add_memory_reference is idempotent (no duplicates)."""
        session = SessionState(
            session_id="session_test_009",
            agent_name="planner",
            active_memory_refs=["mem_existing"],
            pinned_memories=[],
        )

        session.add_memory_reference("mem_existing", pinned=False)
        session.add_memory_reference("mem_existing", pinned=False)

        assert session.active_memory_refs.count("mem_existing") == 1


class TestAgentStateQueries:
    """Test suite for agent state queries."""

    def test_get_active_agent_states_filters_terminated(self):
        """Test get_active_agent_states excludes TERMINATED agents."""
        from shared.models.learning import AgentStateLearning

        session = SessionState(
            session_id="session_test_010",
            agent_name="planner",
            agent_states={
                "planner": AgentStateLearning(
                    agent_id="planner",
                    agent_name="planner",
                    session_id="session_test_010",
                    status="completed",
                    skill_vector=[0.1] * 384,
                ),
                "coder": AgentStateLearning(
                    agent_id="coder",
                    agent_name="coding_agent",
                    session_id="session_test_010",
                    status="running",
                    skill_vector=[0.2] * 384,
                ),
                "terminated_agent": AgentStateLearning(
                    agent_id="terminated_agent",
                    agent_name="old_agent",
                    session_id="session_test_010",
                    status="terminated",
                    skill_vector=[0.3] * 384,
                ),
            },
        )

        active_states = session.get_active_agent_states()

        assert "planner" in active_states
        assert "coder" in active_states
        assert "terminated_agent" not in active_states
        assert len(active_states) == 2

    def test_get_active_agent_states_empty_when_no_agents(self):
        """Test get_active_agent_states returns empty dict when no agents."""
        session = SessionState(
            session_id="session_test_011",
            agent_name="planner",
            agent_states={},
        )

        active_states = session.get_active_agent_states()

        assert active_states == {}


class TestTaskContextResume:
    """Test suite for task context resume functionality."""

    def test_resume_task_context_creates_task_context(self):
        """Test resume_task_context creates TaskContext from session state."""
        session = SessionState(
            session_id="session_test_012",
            agent_name="planner",
            task_id="feat_auth",
            task_type="feature_implementation",
            task_progress_percent=60.0,
            completed_steps=["spec", "plan", "implementation"],
            pending_steps=["tests", "merge"],
            active_memory_refs=["mem_plan", "mem_adr"],
            pinned_memories=["mem_constitution"],
        )

        task_context = session.resume_task_context()

        assert task_context.session_id == "session_test_012"
        assert task_context.task_id == "feat_auth"
        assert task_context.task_type == "feature_implementation"
        assert task_context.progress_percent == 60.0
        assert task_context.completed_steps == ["spec", "plan", "implementation"]
        assert task_context.pending_steps == ["tests", "merge"]
        assert task_context.active_memory_refs == ["mem_plan", "mem_adr"]
        assert task_context.pinned_memories == ["mem_constitution"]

    def test_resume_task_context_handles_no_task(self):
        """Test resume_task_context handles session with no active task."""
        session = SessionState(
            session_id="session_test_013",
            agent_name="planner",
            task_id=None,
            task_type=None,
        )

        task_context = session.resume_task_context()

        assert task_context.session_id == "session_test_013"
        assert task_context.task_id == ""
        assert task_context.task_type == ""
        assert task_context.progress_percent == 0.0


class TestTaskProgressValidation:
    """Test suite for task progress validation rules."""

    def test_task_progress_percent_must_be_0_to_100(self):
        """Test task_progress_percent validates 0-100 range."""
        from pydantic import ValidationError

        # Valid: 0.0
        session = SessionState(
            session_id="session_test_014",
            agent_name="planner",
            task_progress_percent=0.0,
        )
        assert session.task_progress_percent == 0.0

        # Valid: 100.0
        session = SessionState(
            session_id="session_test_015",
            agent_name="planner",
            task_progress_percent=100.0,
        )
        assert session.task_progress_percent == 100.0

        # Invalid: -5.0
        with pytest.raises(ValidationError):
            SessionState(
                session_id="session_test_016",
                agent_name="planner",
                task_progress_percent=-5.0,
            )

        # Invalid: 105.0
        with pytest.raises(ValidationError):
            SessionState(
                session_id="session_test_017",
                agent_name="planner",
                task_progress_percent=105.0,
            )

    def test_session_id_must_be_nonempty(self):
        """Test session_id validates non-empty."""
        from pydantic import ValidationError

        # Valid: session_ prefix
        session = SessionState(
            session_id="session_123",
            agent_name="planner",
        )
        assert session.session_id == "session_123"

        # Valid: other patterns allowed for backward compatibility
        session = SessionState(
            session_id="test_session_001",
            agent_name="planner",
        )
        assert session.session_id == "test_session_001"

        # Invalid: empty
        with pytest.raises(ValidationError):
            SessionState(
                session_id="",
                agent_name="planner",
            )

    def test_agent_states_keys_must_match_agent_ids(self):
        """Test agent_states validates key matches state.agent_id."""
        from pydantic import ValidationError

        from shared.models.learning import AgentStateLearning

        # Valid: key matches agent_id
        session = SessionState(
            session_id="session_test_018",
            agent_name="planner",
            agent_states={
                "planner": AgentStateLearning(
                    agent_id="planner",
                    agent_name="planner",
                    session_id="session_test_018",
                    status="running",
                    skill_vector=[0.1] * 384,
                )
            },
        )
        assert "planner" in session.agent_states

        # Invalid: key does not match agent_id
        with pytest.raises(ValidationError):
            SessionState(
                session_id="session_test_019",
                agent_name="planner",
                agent_states={
                    "wrong_key": AgentStateLearning(
                        agent_id="planner",
                        agent_name="planner",
                        session_id="session_test_019",
                        status="running",
                        skill_vector=[0.1] * 384,
                    )
                },
            )
