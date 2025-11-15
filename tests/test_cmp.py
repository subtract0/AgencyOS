"""
Unit tests for CMP (Clade Metaproductivity) system.

Tests CmpEvent, CmpScore, CmpStore, and CladeSelector components.
"""

import json
import tempfile
from pathlib import Path

import pytest

from agency_memory.learning import (
    CladeSelector,
    CmpEvent,
    CmpScore,
    CmpStore,
    compute_clade_score,
)


class TestCmpEvent:
    """Tests for CmpEvent dataclass."""

    def test_create_event(self):
        """Test creating a CmpEvent."""
        event = CmpEvent(
            id="cmp_001",
            pr_id=142,
            branch_name="autogen/selfheal-v1-qwen32b-prompt_small_diff-v1-minimal-9f2a",
            agent_id="self_healer_v1",
            clade_id="self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
            task_type="self_heal",
            created_at=1731423052,
            closed_at=1731425280,
            reinforcement_signal="approved",
            reverted=False,
            size_loc_delta=47,
            files_touched=["tests/test_validation.py", "shared/validation.py"],
            test_status="pass",
            test_suites=["unit"],
            human_review_time_sec=2228,
            extra_metadata={"fix_type": "NoneType_AttributeError", "test_failures_fixed": 3},
        )

        assert event.id == "cmp_001"
        assert event.pr_id == 142
        assert event.agent_id == "self_healer_v1"
        assert event.reinforcement_signal == "approved"
        assert event.reverted is False
        assert event.size_loc_delta == 47
        assert len(event.files_touched) == 2
        assert event.test_status == "pass"

    def test_event_to_dict(self):
        """Test converting CmpEvent to dictionary."""
        event = CmpEvent(
            id="cmp_001",
            pr_id=142,
            branch_name="autogen/selfheal-v1-qwen32b-prompt_small_diff-v1-minimal-9f2a",
            agent_id="self_healer_v1",
            clade_id="self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
            task_type="self_heal",
            created_at=1731423052,
            closed_at=1731425280,
            reinforcement_signal="approved",
            reverted=False,
            size_loc_delta=47,
            files_touched=["test.py"],
            test_status="pass",
        )

        event_dict = event.to_dict()

        assert event_dict["id"] == "cmp_001"
        assert event_dict["pr_id"] == 142
        assert event_dict["reinforcement_signal"] == "approved"
        assert isinstance(event_dict["files_touched"], list)

    def test_event_from_dict(self):
        """Test creating CmpEvent from dictionary."""
        event_dict = {
            "id": "cmp_001",
            "pr_id": 142,
            "branch_name": "autogen/selfheal-v1-qwen32b-prompt_small_diff-v1-minimal-9f2a",
            "agent_id": "self_healer_v1",
            "clade_id": "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
            "task_type": "self_heal",
            "created_at": 1731423052,
            "closed_at": 1731425280,
            "reinforcement_signal": "approved",
            "reverted": False,
            "size_loc_delta": 47,
            "files_touched": ["test.py"],
            "test_status": "pass",
        }

        event = CmpEvent.from_dict(event_dict)

        assert event.id == "cmp_001"
        assert event.pr_id == 142
        assert event.reinforcement_signal == "approved"

    def test_event_roundtrip(self):
        """Test to_dict → from_dict roundtrip."""
        original = CmpEvent(
            id="cmp_001",
            pr_id=142,
            branch_name="autogen/test",
            agent_id="self_healer_v1",
            clade_id="self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
            task_type="self_heal",
            created_at=1731423052,
            closed_at=1731425280,
            reinforcement_signal="approved",
            reverted=False,
            size_loc_delta=47,
            files_touched=["test.py"],
            test_status="pass",
        )

        # Roundtrip
        reconstructed = CmpEvent.from_dict(original.to_dict())

        assert reconstructed.id == original.id
        assert reconstructed.pr_id == original.pr_id
        assert reconstructed.reinforcement_signal == original.reinforcement_signal


class TestCmpScore:
    """Tests for CmpScore dataclass."""

    def test_create_score(self):
        """Test creating a CmpScore."""
        score = CmpScore(
            clade_id="self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
            total_events=15,
            approvals=12,
            rejections=3,
            reverts=1,
            approval_rate=0.8,
            revert_rate=0.083,
            avg_loc_delta_rejected=234.67,
            score=0.633,
        )

        assert score.total_events == 15
        assert score.approvals == 12
        assert score.rejections == 3
        assert score.reverts == 1
        assert abs(score.approval_rate - 0.8) < 0.01
        assert abs(score.score - 0.633) < 0.01

    def test_score_to_dict(self):
        """Test converting CmpScore to dictionary."""
        score = CmpScore(
            clade_id="test_clade",
            total_events=10,
            approvals=8,
            rejections=2,
            reverts=0,
            approval_rate=0.8,
            revert_rate=0.0,
            avg_loc_delta_rejected=100.0,
            score=0.7,
        )

        score_dict = score.to_dict()

        assert score_dict["total_events"] == 10
        assert score_dict["approvals"] == 8
        assert score_dict["score"] == 0.7


class TestComputeCladeScore:
    """Tests for compute_clade_score function."""

    def test_compute_score_no_events(self):
        """Test computing score with no events."""
        score = compute_clade_score([], "nonexistent_clade")

        assert score.total_events == 0
        assert score.approvals == 0
        assert score.rejections == 0
        assert score.score == 0.0

    def test_compute_score_all_approved(self):
        """Test computing score with all approved PRs."""
        events = [
            CmpEvent(
                id=f"cmp_{i}",
                pr_id=100 + i,
                branch_name="test",
                agent_id="test_agent",
                clade_id="test_clade",
                task_type="test",
                created_at=1000000 + i,
                closed_at=1000100 + i,
                reinforcement_signal="approved",
                reverted=False,
                size_loc_delta=50,
                files_touched=["test.py"],
                test_status="pass",
            )
            for i in range(10)
        ]

        score = compute_clade_score(events, "test_clade")

        assert score.total_events == 10
        assert score.approvals == 10
        assert score.rejections == 0
        assert score.reverts == 0
        assert score.approval_rate == 1.0
        assert score.revert_rate == 0.0
        # Score formula: approval_rate - 2*revert_rate - 0.5*(avg_loc_delta_rejected/500)
        # 1.0 - 0 - 0 = 1.0 (no rejections)
        assert abs(score.score - 1.0) < 0.01

    def test_compute_score_with_rejections(self):
        """Test computing score with some rejected PRs."""
        events = [
            # 8 approved
            *[
                CmpEvent(
                    id=f"cmp_approved_{i}",
                    pr_id=100 + i,
                    branch_name="test",
                    agent_id="test_agent",
                    clade_id="test_clade",
                    task_type="test",
                    created_at=1000000 + i,
                    closed_at=1000100 + i,
                    reinforcement_signal="approved",
                    reverted=False,
                    size_loc_delta=50,
                    files_touched=["test.py"],
                    test_status="pass",
                )
                for i in range(8)
            ],
            # 2 rejected with LOC delta 200
            *[
                CmpEvent(
                    id=f"cmp_rejected_{i}",
                    pr_id=200 + i,
                    branch_name="test",
                    agent_id="test_agent",
                    clade_id="test_clade",
                    task_type="test",
                    created_at=1000000 + i,
                    closed_at=1000100 + i,
                    reinforcement_signal="rejected",
                    reverted=False,
                    size_loc_delta=200,
                    files_touched=["test.py"],
                    test_status="fail",
                )
                for i in range(2)
            ],
        ]

        score = compute_clade_score(events, "test_clade")

        assert score.total_events == 10
        assert score.approvals == 8
        assert score.rejections == 2
        assert score.approval_rate == 0.8
        assert score.avg_loc_delta_rejected == 200.0
        # Score: 0.8 - 0 - 0.5*(200/500) = 0.8 - 0.2 = 0.6
        assert abs(score.score - 0.6) < 0.01

    def test_compute_score_with_reverts(self):
        """Test computing score with reverted PRs."""
        events = [
            # 10 approved
            *[
                CmpEvent(
                    id=f"cmp_approved_{i}",
                    pr_id=100 + i,
                    branch_name="test",
                    agent_id="test_agent",
                    clade_id="test_clade",
                    task_type="test",
                    created_at=1000000 + i,
                    closed_at=1000100 + i,
                    reinforcement_signal="approved",
                    reverted=False,
                    size_loc_delta=50,
                    files_touched=["test.py"],
                    test_status="pass",
                )
                for i in range(10)
            ],
            # 1 approved but reverted
            CmpEvent(
                id="cmp_reverted",
                pr_id=200,
                branch_name="test",
                agent_id="test_agent",
                clade_id="test_clade",
                task_type="test",
                created_at=1000000,
                closed_at=1000100,
                reinforcement_signal="approved",
                reverted=True,  # Reverted!
                size_loc_delta=50,
                files_touched=["test.py"],
                test_status="pass",
            ),
        ]

        score = compute_clade_score(events, "test_clade")

        assert score.total_events == 11
        assert score.approvals == 11
        assert score.reverts == 1
        assert score.revert_rate == 1 / 11  # 1 revert out of 11 approvals
        # Score: 1.0 - 2*(1/11) - 0 ≈ 1.0 - 0.182 = 0.818
        assert abs(score.score - 0.818) < 0.01


class TestCmpStore:
    """Tests for CmpStore class."""

    def test_create_store(self):
        """Test creating a CmpStore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CmpStore(data_dir=tmpdir)
            assert store.events_file == Path(tmpdir) / "cmp_events.jsonl"

    def test_record_and_load_event(self):
        """Test recording and loading events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CmpStore(data_dir=tmpdir)

            # Record event
            event = CmpEvent(
                id="cmp_001",
                pr_id=142,
                branch_name="test",
                agent_id="test_agent",
                clade_id="test_clade",
                task_type="test",
                created_at=1000000,
                closed_at=1000100,
                reinforcement_signal="approved",
                reverted=False,
                size_loc_delta=47,
                files_touched=["test.py"],
                test_status="pass",
            )

            store.record_event(event)

            # Load events
            loaded_events = store.load_events()

            assert len(loaded_events) == 1
            assert loaded_events[0].id == "cmp_001"
            assert loaded_events[0].pr_id == 142

    def test_load_events_with_task_type_filter(self):
        """Test loading events with task_type filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CmpStore(data_dir=tmpdir)

            # Record events with different task types
            event1 = CmpEvent(
                id="cmp_001",
                pr_id=1,
                branch_name="test",
                agent_id="test_agent",
                clade_id="test_clade",
                task_type="self_heal",
                created_at=1000000,
                closed_at=1000100,
                reinforcement_signal="approved",
                reverted=False,
                size_loc_delta=50,
                files_touched=["test.py"],
                test_status="pass",
            )

            event2 = CmpEvent(
                id="cmp_002",
                pr_id=2,
                branch_name="test",
                agent_id="test_agent",
                clade_id="test_clade",
                task_type="backlog",
                created_at=1000000,
                closed_at=1000100,
                reinforcement_signal="approved",
                reverted=False,
                size_loc_delta=50,
                files_touched=["test.py"],
                test_status="pass",
            )

            store.record_event(event1)
            store.record_event(event2)

            # Load with filter
            self_heal_events = store.load_events(task_type="self_heal")
            backlog_events = store.load_events(task_type="backlog")
            all_events = store.load_events()

            assert len(self_heal_events) == 1
            assert len(backlog_events) == 1
            assert len(all_events) == 2

    def test_get_all_clade_ids(self):
        """Test getting all unique clade IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CmpStore(data_dir=tmpdir)

            # Record events with different clades
            for i in range(3):
                event = CmpEvent(
                    id=f"cmp_{i}",
                    pr_id=i,
                    branch_name="test",
                    agent_id="test_agent",
                    clade_id=f"clade_{i % 2}",  # 2 unique clades
                    task_type="test",
                    created_at=1000000,
                    closed_at=1000100,
                    reinforcement_signal="approved",
                    reverted=False,
                    size_loc_delta=50,
                    files_touched=["test.py"],
                    test_status="pass",
                )
                store.record_event(event)

            clade_ids = store.get_all_clade_ids()

            assert len(clade_ids) == 2
            assert "clade_0" in clade_ids
            assert "clade_1" in clade_ids


class TestCladeSelector:
    """Tests for CladeSelector class."""

    def test_select_clade_explore(self):
        """Test epsilon-greedy exploration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CmpStore(data_dir=tmpdir)
            selector = CladeSelector(store)

            available_clades = ["clade_1", "clade_2", "clade_3"]

            # With epsilon=1.0, should always explore (random)
            selected = selector.select_clade(
                task_type="test",
                available_clades=available_clades,
                epsilon=1.0,
            )

            assert selected in available_clades

    def test_select_clade_exploit_best(self):
        """Test epsilon-greedy exploitation (choose best clade)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CmpStore(data_dir=tmpdir)

            # Create events for different clades with different scores
            # clade_1: 100% approval (score ≈ 1.0)
            for i in range(10):
                event = CmpEvent(
                    id=f"cmp_clade1_{i}",
                    pr_id=i,
                    branch_name="test",
                    agent_id="test_agent",
                    clade_id="clade_1",
                    task_type="test",
                    created_at=1000000,
                    closed_at=1000100,
                    reinforcement_signal="approved",
                    reverted=False,
                    size_loc_delta=50,
                    files_touched=["test.py"],
                    test_status="pass",
                )
                store.record_event(event)

            # clade_2: 50% approval (score ≈ 0.5)
            for i in range(10):
                event = CmpEvent(
                    id=f"cmp_clade2_{i}",
                    pr_id=100 + i,
                    branch_name="test",
                    agent_id="test_agent",
                    clade_id="clade_2",
                    task_type="test",
                    created_at=1000000,
                    closed_at=1000100,
                    reinforcement_signal="approved" if i < 5 else "rejected",
                    reverted=False,
                    size_loc_delta=50,
                    files_touched=["test.py"],
                    test_status="pass",
                )
                store.record_event(event)

            selector = CladeSelector(store)

            # With epsilon=0.0, should always exploit (choose best)
            selected = selector.select_clade(
                task_type="test",
                available_clades=["clade_1", "clade_2"],
                epsilon=0.0,
            )

            # Should always select clade_1 (higher score)
            assert selected == "clade_1"

    def test_select_clade_empty_raises(self):
        """Test that selecting from empty clade list raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CmpStore(data_dir=tmpdir)
            selector = CladeSelector(store)

            with pytest.raises(ValueError, match="available_clades must not be empty"):
                selector.select_clade(
                    task_type="test",
                    available_clades=[],
                    epsilon=0.1,
                )
