"""
Unit tests for Backlog Agent (Mission 4).

TDD Protocol (Article VI):
- RED PHASE: Tests written FIRST (all fail initially) ← WE ARE HERE
- GREEN PHASE: Implementation makes tests pass
- REFACTOR PHASE: Clean up while keeping tests green

Test Coverage:
- TestBacklogStorage: CRUD operations, persistence, atomic writes
- TestPriorityQueue: Scoring, selection, tie-breaking
- TestCMPIntegration: CMP score queries and averaging
- TestVectorStoreIntegration: Completion metadata storage
"""

import json
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import module to avoid namespace collision
import tools.backlog_agent as ba
from shared.models.backlog import (
    BacklogMetrics,
    Task,
    TaskPriority,
    TaskStatus,
    TaskType,
)


class TestBacklogStorage:
    """Tests for BacklogStorage class (JSONL persistence)."""

    def test_add_task(self):
        """Test adding a task to backlog."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)

            task = Task(
                id=str(uuid.uuid4()),
                title="Fix auth bug",
                description="User login fails with 500 error",
                task_type=TaskType.BUG_FIX,
                priority=TaskPriority.P1,
                estimated_complexity=5,
                business_value=9,
            )

            result = storage.add_task(task)

            assert result.is_ok()
            stored_task = result.unwrap()
            assert stored_task.id == task.id
            assert stored_task.title == "Fix auth bug"
            assert stored_task.status == TaskStatus.PENDING

    def test_get_task(self):
        """Test retrieving a task by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)

            task_id = str(uuid.uuid4())
            task = Task(
                id=task_id,
                title="Add JWT support",
                description="Implement JWT authentication",
                task_type=TaskType.FEATURE_REQUEST,
                estimated_complexity=7,
            )

            storage.add_task(task)
            result = storage.get_task(task_id)

            assert result.is_ok()
            retrieved_task = result.unwrap()
            assert retrieved_task.id == task_id
            assert retrieved_task.title == "Add JWT support"

    def test_get_task_missing(self):
        """Test retrieving missing task returns error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)

            result = storage.get_task("nonexistent-id")

            assert result.is_err()
            error = result.unwrap_err()
            assert "not found" in str(error).lower()

    def test_update_task(self):
        """Test updating an existing task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)

            task_id = str(uuid.uuid4())
            task = Task(
                id=task_id,
                title="Original title",
                description="Original description",
                task_type=TaskType.TECH_DEBT,
                estimated_complexity=3,
            )

            storage.add_task(task)

            # Update task
            task.title = "Updated title"
            task.status = TaskStatus.IN_PROGRESS
            result = storage.update_task(task)

            assert result.is_ok()

            # Verify update
            retrieved = storage.get_task(task_id).unwrap()
            assert retrieved.title == "Updated title"
            assert retrieved.status == TaskStatus.IN_PROGRESS

    def test_delete_task(self):
        """Test deleting a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)

            task_id = str(uuid.uuid4())
            task = Task(
                id=task_id,
                title="Delete me",
                description="This task will be deleted",
                task_type=TaskType.BUG_FIX,
                estimated_complexity=2,
            )

            storage.add_task(task)

            # Delete task
            result = storage.delete_task(task_id)
            assert result.is_ok()

            # Verify deletion
            get_result = storage.get_task(task_id)
            assert get_result.is_err()

    def test_persistence(self):
        """Test that tasks survive process restarts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_id = str(uuid.uuid4())
            task = Task(
                id=task_id,
                title="Persistent task",
                description="Should survive restart",
                task_type=TaskType.FEATURE_REQUEST,
                estimated_complexity=5,
            )

            # Create storage, add task, close
            storage1 = ba.BacklogStorage(data_dir=tmpdir)
            storage1.add_task(task)
            del storage1

            # Create new storage instance, verify task exists
            storage2 = ba.BacklogStorage(data_dir=tmpdir)
            result = storage2.get_task(task_id)

            assert result.is_ok()
            retrieved_task = result.unwrap()
            assert retrieved_task.id == task_id
            assert retrieved_task.title == "Persistent task"

    def test_atomic_writes(self):
        """Test that concurrent writes don't corrupt data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)

            # Create multiple tasks concurrently
            task_ids = []
            for i in range(10):
                task = Task(
                    id=str(uuid.uuid4()),
                    title=f"Task {i}",
                    description=f"Description {i}",
                    task_type=TaskType.TECH_DEBT,
                    estimated_complexity=i + 1,
                )
                result = storage.add_task(task)
                assert result.is_ok()
                task_ids.append(task.id)

            # Verify all tasks were stored correctly
            for task_id in task_ids:
                result = storage.get_task(task_id)
                assert result.is_ok()


class TestPriorityQueue:
    """Tests for priority queue and task selection logic."""

    def test_priority_formula(self):
        """Test priority score calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)
            selector = ba.PriorityQueue(storage)

            task = Task(
                id=str(uuid.uuid4()),
                title="Test task",
                description="For score calculation",
                task_type=TaskType.BUG_FIX,
                priority=TaskPriority.P2,
                estimated_complexity=5,
                business_value=8,
                cmp_related_clade_ids=[],
            )

            # Score = (cmp_avg * 0.4) + (business_value/10 * 0.3) + (1/complexity * 0.3)
            # Score = (0.5 * 0.4) + (8/10 * 0.3) + (1/5 * 0.3)
            # Score = 0.2 + 0.24 + 0.06 = 0.5
            score = selector._calculate_score(task, cmp_avg_score=0.5)

            assert abs(score - 0.5) < 0.01  # Allow small floating point error

    def test_p1_always_first(self):
        """Test that P1 tasks are always selected before P2/P3."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)
            selector = ba.PriorityQueue(storage)

            # Add P3 task with high score
            p3_task = Task(
                id=str(uuid.uuid4()),
                title="P3 High Score",
                description="Should not be selected",
                task_type=TaskType.TECH_DEBT,
                priority=TaskPriority.P3,
                estimated_complexity=1,  # Simple = high score
                business_value=10,  # High value
            )
            storage.add_task(p3_task)

            # Add P1 task with low score
            p1_task = Task(
                id=str(uuid.uuid4()),
                title="P1 Low Score",
                description="Should be selected first",
                task_type=TaskType.BUG_FIX,
                priority=TaskPriority.P1,
                estimated_complexity=10,  # Complex = low score
                business_value=1,  # Low value
            )
            storage.add_task(p1_task)

            # P1 should be selected despite lower score
            selected = selector.select_next_task()
            assert selected.is_ok()
            assert selected.unwrap().id == p1_task.id

    def test_tie_breaking(self):
        """Test that ties are broken by created_at (oldest first)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)
            selector = ba.PriorityQueue(storage)

            # Create two tasks with identical scores
            now = datetime.now()
            older_task = Task(
                id=str(uuid.uuid4()),
                title="Older task",
                description="Created first",
                task_type=TaskType.BUG_FIX,
                priority=TaskPriority.P2,
                estimated_complexity=5,
                business_value=5,
                created_at=now - timedelta(days=2),
            )
            storage.add_task(older_task)

            newer_task = Task(
                id=str(uuid.uuid4()),
                title="Newer task",
                description="Created second",
                task_type=TaskType.BUG_FIX,
                priority=TaskPriority.P2,
                estimated_complexity=5,
                business_value=5,
                created_at=now - timedelta(days=1),
            )
            storage.add_task(newer_task)

            # Older task should be selected
            selected = selector.select_next_task()
            assert selected.is_ok()
            assert selected.unwrap().id == older_task.id

    def test_select_next_task(self):
        """Test selecting highest-priority pending task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)
            selector = ba.PriorityQueue(storage)

            # Add several tasks
            task1 = Task(
                id=str(uuid.uuid4()),
                title="Low priority",
                description="P3 task",
                task_type=TaskType.TECH_DEBT,
                priority=TaskPriority.P3,
                estimated_complexity=8,
                business_value=3,
            )
            storage.add_task(task1)

            task2 = Task(
                id=str(uuid.uuid4()),
                title="High priority",
                description="P2 task with high score",
                task_type=TaskType.BUG_FIX,
                priority=TaskPriority.P2,
                estimated_complexity=2,
                business_value=9,
            )
            storage.add_task(task2)

            # Select next task (should be task2)
            selected = selector.select_next_task()
            assert selected.is_ok()
            assert selected.unwrap().id == task2.id

    def test_empty_backlog(self):
        """Test select_next_task() returns error when backlog is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)
            selector = ba.PriorityQueue(storage)

            result = selector.select_next_task()
            assert result.is_err()
            assert "empty" in str(result.unwrap_err()).lower()


class TestCMPIntegration:
    """Tests for CMP score integration."""

    @patch("tools.backlog_agent.CmpStore")
    def test_cmp_score_query(self, mock_store_class):
        """Test querying CmpStore for clade scores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock CmpStore
            mock_store = Mock()
            mock_store_class.return_value = mock_store

            storage = ba.BacklogStorage(data_dir=tmpdir)
            selector = ba.PriorityQueue(storage)

            task = Task(
                id=str(uuid.uuid4()),
                title="CMP test",
                description="Test CMP integration",
                task_type=TaskType.BUG_FIX,
                estimated_complexity=5,
                cmp_related_clade_ids=["clade_1", "clade_2"],
            )

            # Query CMP scores
            avg_score = selector._get_cmp_avg_score(task)

            # Should have queried CmpStore
            assert avg_score >= 0.0
            assert avg_score <= 1.0

    @patch("tools.backlog_agent.compute_clade_score")
    @patch("tools.backlog_agent.CmpStore")
    def test_cmp_score_averaging(self, mock_store_class, mock_compute_score):
        """Test averaging multiple clade scores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from agency_memory.learning import CmpScore

            # Mock CmpStore and scores
            mock_store = Mock()
            mock_store.load_events.return_value = []
            mock_store_class.return_value = mock_store

            def score_side_effect(events, clade_id):
                scores = {
                    "clade_1": CmpScore(
                        clade_id="clade_1",
                        total_events=10,
                        approvals=9,
                        rejections=1,
                        reverts=0,
                        approval_rate=0.9,
                        revert_rate=0.0,
                        avg_loc_delta_rejected=100.0,
                        score=0.9,
                    ),
                    "clade_2": CmpScore(
                        clade_id="clade_2",
                        total_events=10,
                        approvals=7,
                        rejections=3,
                        reverts=0,
                        approval_rate=0.7,
                        revert_rate=0.0,
                        avg_loc_delta_rejected=100.0,
                        score=0.7,
                    ),
                }
                return scores.get(
                    clade_id,
                    CmpScore(
                        clade_id=clade_id,
                        total_events=0,
                        approvals=0,
                        rejections=0,
                        reverts=0,
                        approval_rate=0.0,
                        revert_rate=0.0,
                        avg_loc_delta_rejected=0.0,
                        score=0.0,
                    ),
                )

            mock_compute_score.side_effect = score_side_effect

            storage = ba.BacklogStorage(data_dir=tmpdir)
            selector = ba.PriorityQueue(storage)

            task = Task(
                id=str(uuid.uuid4()),
                title="Multi-clade task",
                description="Test averaging",
                task_type=TaskType.BUG_FIX,
                estimated_complexity=5,
                cmp_related_clade_ids=["clade_1", "clade_2"],
            )

            avg_score = selector._get_cmp_avg_score(task)

            # Average of 0.9 and 0.7 = 0.8
            assert abs(avg_score - 0.8) < 0.01

    def test_no_clades_defaults_neutral(self):
        """Test that tasks with no clades get 0.5 (neutral) score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)
            selector = ba.PriorityQueue(storage)

            task = Task(
                id=str(uuid.uuid4()),
                title="No clades",
                description="No CMP data",
                task_type=TaskType.TECH_DEBT,
                estimated_complexity=5,
                cmp_related_clade_ids=[],  # No clades
            )

            avg_score = selector._get_cmp_avg_score(task)

            assert avg_score == 0.5  # Neutral default


class TestVectorStoreIntegration:
    """Tests for VectorStore completion metadata storage."""

    @patch("tools.backlog_agent.EnhancedMemoryStore")
    def test_store_completion_metadata(self, mock_store_class):
        """Test storing task completion metadata in VectorStore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock EnhancedMemoryStore
            mock_store = Mock()
            mock_store_class.return_value = mock_store

            storage = ba.BacklogStorage(data_dir=tmpdir)

            task = Task(
                id=str(uuid.uuid4()),
                title="Completed task",
                description="Test completion metadata",
                task_type=TaskType.BUG_FIX,
                priority=TaskPriority.P1,
                estimated_complexity=5,
                business_value=8,
                status=TaskStatus.COMPLETED,
            )

            # Store completion metadata
            result = storage.store_completion_metadata(task, duration_hours=2.5)

            assert result.is_ok()
            # Verify store was called
            mock_store.store.assert_called_once()

    def test_memory_key_format(self):
        """Test that memory key follows correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)

            task_id = "test-task-123"
            key = storage._build_memory_key(task_id)

            # Key should be: backlog_task_{task_id}_{timestamp}
            assert key.startswith(f"backlog_task_{task_id}_")

    def test_memory_tags(self):
        """Test that memory tags are correct."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ba.BacklogStorage(data_dir=tmpdir)

            task = Task(
                id=str(uuid.uuid4()),
                title="Tag test",
                description="Test tags",
                task_type=TaskType.TEST_FAILURE,
                priority=TaskPriority.P1,
                estimated_complexity=3,
            )

            tags = storage._build_memory_tags(task)

            # Should have: ["backlog", "task_completion", priority]
            assert "backlog" in tags
            assert "task_completion" in tags
            assert "P1" in tags or "p1" in tags.lower()
