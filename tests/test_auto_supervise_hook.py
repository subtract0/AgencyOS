"""
Tests for tools/auto_supervise_hook.py - CMP Learning Coach

Mission 2.2: PR metadata parser and CmpEvent recorder

Test-Driven Development (Article VI):
- Tests written FIRST (RED phase)
- Implementation written SECOND (GREEN phase)
- Refactor for quality (REFACTOR phase)

Test coverage:
- PR metadata parsing from GitHub API
- PR body comment extraction (agent_id, clade_id, task_type, memory_ids)
- CmpEvent construction with all required fields
- CmpStore.record_event() integration
- EnhancedMemoryStore.set_reinforcement() integration
- Error handling (missing metadata, API failures)
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from agency_memory.learning import CmpEvent, CmpStore
from tools.auto_supervise_hook import (
    parse_pr_body_metadata,
    fetch_pr_data_from_github,
    build_cmp_event,
    record_cmp_event_and_update_memories,
    main,
)


class TestParsePRBodyMetadata:
    """Test extraction of metadata comments from PR body."""

    def test_parse_all_metadata_fields(self):
        """Should extract agent_id, clade_id, task_type, memory_ids from comments."""
        pr_body = """
        Fix test failures in validation module

        <!-- agent_id: self_healer_v1 -->
        <!-- clade_id: self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal -->
        <!-- task_type: self_heal -->
        <!-- memory_ids: ["mem_001", "mem_002", "mem_003"] -->

        Changes:
        - Fixed NoneType AttributeError in validate_input()
        - Added null check for optional parameters
        """

        metadata = parse_pr_body_metadata(pr_body)

        assert metadata["agent_id"] == "self_healer_v1"
        assert metadata["clade_id"] == "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal"
        assert metadata["task_type"] == "self_heal"
        assert metadata["memory_ids"] == ["mem_001", "mem_002", "mem_003"]

    def test_parse_missing_memory_ids(self):
        """Should return empty list if memory_ids comment missing."""
        pr_body = """
        <!-- agent_id: backlog_v1 -->
        <!-- clade_id: backlog_v1::gpt-5::prompt_full_context::strategy_careful -->
        <!-- task_type: backlog -->
        """

        metadata = parse_pr_body_metadata(pr_body)

        assert metadata["agent_id"] == "backlog_v1"
        assert metadata["memory_ids"] == []

    def test_parse_missing_required_metadata(self):
        """Should raise ValueError if required metadata missing."""
        pr_body = "Regular PR body without metadata comments"

        with pytest.raises(ValueError, match="Missing required metadata"):
            parse_pr_body_metadata(pr_body)

    def test_parse_malformed_memory_ids_json(self):
        """Should handle malformed memory_ids JSON gracefully."""
        pr_body = """
        <!-- agent_id: test_agent -->
        <!-- clade_id: test_agent::model::prompt::strategy -->
        <!-- task_type: test -->
        <!-- memory_ids: [invalid json -->
        """

        metadata = parse_pr_body_metadata(pr_body)
        assert metadata["memory_ids"] == []  # Fallback to empty list


class TestFetchPRDataFromGitHub:
    """Test GitHub API integration for PR metadata."""

    @patch("tools.auto_supervise_hook.requests.get")
    def test_fetch_pr_data_success(self, mock_get):
        """Should fetch PR data from GitHub API with retry."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "number": 142,
            "title": "Fix validation tests",
            "body": "<!-- agent_id: self_healer_v1 -->",
            "head": {"ref": "autogen/selfheal-v1-qwen32b-prompt_small_diff-v1-minimal-9f2a"},
            "created_at": "2024-11-12T14:30:52Z",
            "closed_at": "2024-11-12T15:08:00Z",
            "state": "closed",
            "merged": True,
            "additions": 25,
            "deletions": 22,
            "changed_files": 2,
        }
        mock_response.json.side_effect = None  # Allow multiple calls

        # Mock files endpoint
        mock_files_response = MagicMock()
        mock_files_response.status_code = 200
        mock_files_response.json.return_value = [
            {"filename": "tests/test_validation.py"},
            {"filename": "shared/validation.py"}
        ]

        mock_get.side_effect = [mock_response, mock_files_response]

        pr_data = fetch_pr_data_from_github(142, "fake-token")

        assert pr_data["pr_id"] == 142
        assert pr_data["branch_name"] == "autogen/selfheal-v1-qwen32b-prompt_small_diff-v1-minimal-9f2a"
        assert pr_data["size_loc_delta"] == 47  # 25 + 22
        assert pr_data["files_touched"] == ["tests/test_validation.py", "shared/validation.py"]
        assert pr_data["created_at"] > 0  # Unix timestamp
        assert pr_data["closed_at"] > 0

    @patch("tools.auto_supervise_hook.requests.get")
    def test_fetch_pr_data_retry_on_timeout(self, mock_get):
        """Should retry on timeout per Article I (complete context)."""
        # First call: timeout, Second call: success (PR), Third call: success (files)
        timeout_response = MagicMock(status_code=504)

        success_pr_response = MagicMock(status_code=200)
        success_pr_response.json.return_value = {
            "number": 142,
            "head": {"ref": "test-branch"},
            "body": "test",
            "created_at": "2024-11-12T14:30:52Z",
            "closed_at": "2024-11-12T15:08:00Z",
            "additions": 10,
            "deletions": 5,
        }

        success_files_response = MagicMock(status_code=200)
        success_files_response.json.return_value = [{"filename": "test.py"}]

        mock_get.side_effect = [
            timeout_response,  # First PR call fails
            success_pr_response,  # Retry PR call succeeds
            success_files_response,  # Files call succeeds
        ]

        pr_data = fetch_pr_data_from_github(142, "fake-token")

        assert pr_data["pr_id"] == 142
        assert mock_get.call_count == 3  # Initial (timeout) + retry (PR) + files

    @patch("tools.auto_supervise_hook.requests.get")
    def test_fetch_pr_data_fail_after_retries(self, mock_get):
        """Should raise error after max retries."""
        mock_get.side_effect = [
            MagicMock(status_code=504),
            MagicMock(status_code=504),
            MagicMock(status_code=504),
        ]

        with pytest.raises(Exception, match="Failed to fetch PR data after 3 retries"):
            fetch_pr_data_from_github(142, "fake-token")


class TestBuildCmpEvent:
    """Test CmpEvent construction from PR data and metadata."""

    def test_build_event_approved(self):
        """Should build CmpEvent for approved (merged) PR."""
        pr_data = {
            "pr_id": 142,
            "branch_name": "autogen/selfheal-v1-qwen32b-9f2a",
            "created_at": 1731423052,
            "closed_at": 1731425280,
            "size_loc_delta": 47,
            "files_touched": ["test.py", "shared.py"],
        }

        metadata = {
            "agent_id": "self_healer_v1",
            "clade_id": "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
            "task_type": "self_heal",
        }

        event = build_cmp_event(
            pr_data=pr_data,
            metadata=metadata,
            signal="approved",
            reverted=False
        )

        assert isinstance(event, CmpEvent)
        assert event.pr_id == 142
        assert event.agent_id == "self_healer_v1"
        assert event.clade_id == "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal"
        assert event.task_type == "self_heal"
        assert event.reinforcement_signal == "approved"
        assert event.reverted == False
        assert event.size_loc_delta == 47
        assert event.files_touched == ["test.py", "shared.py"]
        assert event.test_status == "unknown"  # Default when not specified

    def test_build_event_rejected(self):
        """Should build CmpEvent for rejected (closed without merge) PR."""
        pr_data = {
            "pr_id": 143,
            "branch_name": "autogen/backlog-v1-gpt5-abc",
            "created_at": 1731423000,
            "closed_at": 1731423500,
            "size_loc_delta": 150,
            "files_touched": ["feature.py"],
        }

        metadata = {
            "agent_id": "backlog_v1",
            "clade_id": "backlog_v1::gpt-5::prompt_full_context::strategy_careful",
            "task_type": "backlog",
        }

        event = build_cmp_event(
            pr_data=pr_data,
            metadata=metadata,
            signal="rejected",
            reverted=False
        )

        assert event.reinforcement_signal == "rejected"
        assert event.pr_id == 143


class TestRecordCmpEventAndUpdateMemories:
    """Test integration with CmpStore and EnhancedMemoryStore."""

    def test_record_event_and_update_memories(self):
        """Should record CmpEvent to store and update memory reinforcement signals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary CMP store
            store_path = Path(tmpdir) / "cmp_events.jsonl"

            event = CmpEvent(
                id="cmp_test_001",
                pr_id=142,
                branch_name="autogen/test-branch",
                agent_id="test_agent",
                clade_id="test_agent::model::prompt::strategy",
                task_type="test",
                created_at=1731423052,
                closed_at=1731425280,
                reinforcement_signal="approved",
                reverted=False,
                size_loc_delta=47,
                files_touched=["test.py"],
                test_status="pass",
                test_suites=["unit"],
            )

            memory_ids = ["mem_001", "mem_002"]

            with patch("tools.auto_supervise_hook.CmpStore") as mock_store_class:
                with patch("tools.auto_supervise_hook.EnhancedMemoryStore") as mock_memory_class:
                    mock_store = MagicMock()
                    mock_memory = MagicMock()
                    mock_store_class.return_value = mock_store
                    mock_memory_class.return_value = mock_memory

                    record_cmp_event_and_update_memories(event, memory_ids)

                    # Verify CmpStore.record_event() called
                    mock_store.record_event.assert_called_once_with(event)

                    # Verify set_reinforcement() called for each memory
                    assert mock_memory.set_reinforcement.call_count == 2
                    mock_memory.set_reinforcement.assert_any_call("mem_001", "approved")
                    mock_memory.set_reinforcement.assert_any_call("mem_002", "approved")

    def test_record_event_no_memories(self):
        """Should record event even if memory_ids list is empty."""
        event = CmpEvent(
            id="cmp_test_002",
            pr_id=143,
            branch_name="autogen/test-branch-2",
            agent_id="test_agent",
            clade_id="test_agent::model::prompt::strategy",
            task_type="test",
            created_at=1731423052,
            closed_at=1731425280,
            reinforcement_signal="rejected",
            reverted=False,
            size_loc_delta=100,
            files_touched=["test2.py"],
            test_status="fail",
        )

        with patch("tools.auto_supervise_hook.CmpStore") as mock_store_class:
            with patch("tools.auto_supervise_hook.EnhancedMemoryStore") as mock_memory_class:
                mock_store = MagicMock()
                mock_memory = MagicMock()
                mock_store_class.return_value = mock_store
                mock_memory_class.return_value = mock_memory

                record_cmp_event_and_update_memories(event, memory_ids=[])

                # Should still record event
                mock_store.record_event.assert_called_once()

                # But not update any memories
                mock_memory.set_reinforcement.assert_not_called()


class TestMainCLI:
    """Test main() CLI entry point."""

    @patch("tools.auto_supervise_hook.fetch_pr_data_from_github")
    @patch("tools.auto_supervise_hook.parse_pr_body_metadata")
    @patch("tools.auto_supervise_hook.build_cmp_event")
    @patch("tools.auto_supervise_hook.record_cmp_event_and_update_memories")
    @patch("os.getenv")
    def test_main_cli_approved(
        self,
        mock_getenv,
        mock_record,
        mock_build,
        mock_parse,
        mock_fetch,
    ):
        """Should orchestrate full workflow for approved PR."""
        mock_getenv.return_value = "fake-github-token"

        mock_fetch.return_value = {
            "pr_id": 142,
            "branch_name": "autogen/test",
            "body": "<!-- agent_id: test_agent -->",
            "created_at": 1731423052,
            "closed_at": 1731425280,
            "size_loc_delta": 50,
            "files_touched": ["test.py"],
        }

        mock_parse.return_value = {
            "agent_id": "test_agent",
            "clade_id": "test_agent::model::prompt::strategy",
            "task_type": "test",
            "memory_ids": ["mem_001"],
        }

        mock_event = MagicMock(spec=CmpEvent)
        mock_event.id = "cmp_test_001"
        mock_event.clade_id = "test_agent::model::prompt::strategy"
        mock_event.reinforcement_signal = "approved"
        mock_build.return_value = mock_event

        import sys
        with patch.object(sys, "argv", ["auto_supervise_hook.py", "--signal=approved", "--pr-id=142"]):
            exit_code = main()

        assert exit_code == 0
        mock_fetch.assert_called_once_with(142, "fake-github-token")
        mock_parse.assert_called_once()
        mock_build.assert_called_once()
        mock_record.assert_called_once_with(mock_event, ["mem_001"])

    @patch("os.getenv")
    def test_main_cli_missing_github_token(self, mock_getenv):
        """Should fail gracefully if GITHUB_TOKEN not set."""
        mock_getenv.return_value = None

        import sys
        with patch.object(sys, "argv", ["auto_supervise_hook.py", "--signal=approved", "--pr-id=142"]):
            exit_code = main()

        assert exit_code == 1  # Error exit code


class TestIntegrationEndToEnd:
    """Integration tests for complete CMP pipeline (end-to-end)."""

    def test_full_pipeline_approved_pr(self):
        """
        Should record complete CmpEvent workflow:
        PR metadata → CmpEvent → CmpStore → EnhancedMemoryStore

        Integration test (no mocks for core components):
        - Real CmpEvent construction
        - Real CmpStore file I/O
        - Real EnhancedMemoryStore integration (mocked only for isolation)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup temporary CMP store (CmpStore creates cmp_events.jsonl in data_dir)
            events_file = Path(tmpdir) / "cmp_events.jsonl"

            # Simulate PR data (from GitHub API)
            pr_data = {
                "pr_id": 999,
                "branch_name": "autogen/integration-test-branch",
                "created_at": 1731423052,
                "closed_at": 1731425280,
                "size_loc_delta": 87,
                "files_touched": ["tools/test_tool.py", "tests/test_tool.py"],
            }

            # Simulate parsed metadata (from PR body)
            metadata = {
                "agent_id": "integration_test_agent",
                "clade_id": "integration_test_agent::gpt-5::prompt_standard::strategy_careful",
                "task_type": "integration_test",
            }

            # Build CmpEvent (real construction, no mocks)
            event = build_cmp_event(
                pr_data=pr_data,
                metadata=metadata,
                signal="approved",
                reverted=False
            )

            # Verify event structure
            assert event.pr_id == 999
            assert event.agent_id == "integration_test_agent"
            assert event.clade_id == "integration_test_agent::gpt-5::prompt_standard::strategy_careful"
            assert event.reinforcement_signal == "approved"
            assert event.reverted == False
            assert event.size_loc_delta == 87
            assert len(event.files_touched) == 2

            # Record to CmpStore (real file I/O)
            with patch("tools.auto_supervise_hook.CmpStore") as mock_store_class:
                # Use real CmpStore but in temp directory
                from agency_memory.learning import CmpStore as RealCmpStore
                real_store = RealCmpStore(data_dir=tmpdir)  # CmpStore uses data_dir parameter
                mock_store_class.return_value = real_store

                # Mock EnhancedMemoryStore (external dependency)
                with patch("tools.auto_supervise_hook.EnhancedMemoryStore") as mock_memory_class:
                    mock_memory = MagicMock()
                    mock_memory_class.return_value = mock_memory

                    # Execute full recording workflow
                    record_cmp_event_and_update_memories(event, memory_ids=[])

            # Verify CmpEvent written to file
            assert events_file.exists(), "CmpStore file should exist after recording"

            # Verify event can be read back
            with open(events_file) as f:
                lines = f.readlines()
                assert len(lines) == 1, "Should have exactly one event recorded"

                recorded_event = json.loads(lines[0])
                assert recorded_event["pr_id"] == 999
                assert recorded_event["agent_id"] == "integration_test_agent"
                assert recorded_event["reinforcement_signal"] == "approved"
                assert recorded_event["reverted"] == False

    def test_full_pipeline_with_memory_updates(self):
        """
        Should update memory reinforcement signals after recording CmpEvent.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "cmp_events.jsonl"

            pr_data = {
                "pr_id": 1000,
                "branch_name": "autogen/memory-test-branch",
                "created_at": 1731423052,
                "closed_at": 1731425280,
                "size_loc_delta": 42,
                "files_touched": ["agency_memory/test.py"],
            }

            metadata = {
                "agent_id": "memory_test_agent",
                "clade_id": "memory_test_agent::gpt-5-mini::prompt_small::strategy_fast",
                "task_type": "memory_test",
            }

            event = build_cmp_event(
                pr_data=pr_data,
                metadata=metadata,
                signal="rejected",
                reverted=False
            )

            memory_ids = ["mem_test_001", "mem_test_002", "mem_test_003"]

            with patch("tools.auto_supervise_hook.CmpStore") as mock_store_class:
                from agency_memory.learning import CmpStore as RealCmpStore
                real_store = RealCmpStore(data_dir=tmpdir)  # CmpStore uses data_dir parameter
                mock_store_class.return_value = real_store

                with patch("tools.auto_supervise_hook.EnhancedMemoryStore") as mock_memory_class:
                    mock_memory = MagicMock()
                    mock_memory_class.return_value = mock_memory

                    # Execute with memory updates
                    record_cmp_event_and_update_memories(event, memory_ids)

                    # Verify set_reinforcement() called for each memory
                    assert mock_memory.set_reinforcement.call_count == 3
                    mock_memory.set_reinforcement.assert_any_call("mem_test_001", "rejected")
                    mock_memory.set_reinforcement.assert_any_call("mem_test_002", "rejected")
                    mock_memory.set_reinforcement.assert_any_call("mem_test_003", "rejected")

            # Verify event recorded to file
            assert events_file.exists()
            with open(events_file) as f:
                lines = f.readlines()
                assert len(lines) == 1
                recorded_event = json.loads(lines[0])
                assert recorded_event["reinforcement_signal"] == "rejected"
