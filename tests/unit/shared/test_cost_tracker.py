"""
Unit tests for generic cost tracker.

Tests cover:
- Cost tracking with pluggable storage
- Summary generation with filters
- Budget management and alerts
- Trend calculations
- Export functionality
- Error handling with Result pattern
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile

from shared.cost_tracker import (
    CostTracker,
    CostEntry,
    CostSummary,
    BudgetStatus,
    BudgetAlert,
    ModelTier,
    StorageBackend,
    SQLiteStorage,
    MemoryStorage,
    CostTrackerError,
)
from shared.type_definitions.result import Ok, Err


class TestCostEntry:
    """Test CostEntry Pydantic model."""

    def test_creates_entry_with_all_fields(self):
        """Should create cost entry with all required fields."""
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            operation="test_op",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.015,
            duration_seconds=1.5,
            success=True,
            metadata={"agent": "test_agent"}
        )

        assert entry.operation == "test_op"
        assert entry.model == "gpt-4"
        assert entry.tokens_in == 100
        assert entry.tokens_out == 200
        assert entry.cost_usd == 0.015

    def test_validates_positive_tokens(self):
        """Should reject negative token counts."""
        with pytest.raises(ValueError):
            CostEntry(
                timestamp=datetime.now().isoformat(),
                operation="test",
                model="gpt-4",
                model_tier=ModelTier.CLOUD_STANDARD,
                tokens_in=-100,
                tokens_out=200,
                cost_usd=0.01,
                duration_seconds=1.0,
                success=True
            )

    def test_validates_positive_cost(self):
        """Should reject negative costs."""
        with pytest.raises(ValueError):
            CostEntry(
                timestamp=datetime.now().isoformat(),
                operation="test",
                model="gpt-4",
                model_tier=ModelTier.CLOUD_STANDARD,
                tokens_in=100,
                tokens_out=200,
                cost_usd=-0.01,
                duration_seconds=1.0,
                success=True
            )


class TestMemoryStorage:
    """Test in-memory storage backend."""

    def test_stores_and_retrieves_entries(self):
        """Should store and retrieve cost entries."""
        storage = MemoryStorage()
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            operation="test",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.015,
            duration_seconds=1.0,
            success=True
        )

        result = storage.store(entry)
        assert result.is_ok()

        entries = storage.get_all()
        assert len(entries) == 1
        assert entries[0].operation == "test"

    def test_filters_by_operation(self):
        """Should filter entries by operation."""
        storage = MemoryStorage()

        storage.store(CostEntry(
            timestamp=datetime.now().isoformat(),
            operation="op1",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.01,
            duration_seconds=1.0,
            success=True
        ))

        storage.store(CostEntry(
            timestamp=datetime.now().isoformat(),
            operation="op2",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.02,
            duration_seconds=1.0,
            success=True
        ))

        entries = storage.get_by_operation("op1")
        assert len(entries) == 1
        assert entries[0].operation == "op1"

    def test_filters_by_date_range(self):
        """Should filter entries by date range."""
        storage = MemoryStorage()
        now = datetime.now()

        # Old entry
        storage.store(CostEntry(
            timestamp=(now - timedelta(days=2)).isoformat(),
            operation="old",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.01,
            duration_seconds=1.0,
            success=True
        ))

        # Recent entry
        storage.store(CostEntry(
            timestamp=now.isoformat(),
            operation="recent",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.02,
            duration_seconds=1.0,
            success=True
        ))

        start = now - timedelta(days=1)
        entries = storage.get_by_date_range(start, now)
        assert len(entries) == 1
        assert entries[0].operation == "recent"

    def test_clears_all_entries(self):
        """Should clear all stored entries."""
        storage = MemoryStorage()
        storage.store(CostEntry(
            timestamp=datetime.now().isoformat(),
            operation="test",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.01,
            duration_seconds=1.0,
            success=True
        ))

        assert len(storage.get_all()) == 1
        storage.clear()
        assert len(storage.get_all()) == 0


class TestSQLiteStorage:
    """Test SQLite storage backend."""

    def test_creates_database_and_schema(self):
        """Should create database with proper schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            storage = SQLiteStorage(str(db_path))

            assert db_path.exists()
            storage.close()

    def test_stores_and_retrieves_entries(self):
        """Should persist entries to SQLite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            storage = SQLiteStorage(str(db_path))

            entry = CostEntry(
                timestamp=datetime.now().isoformat(),
                operation="test",
                model="gpt-4",
                model_tier=ModelTier.CLOUD_STANDARD,
                tokens_in=100,
                tokens_out=200,
                cost_usd=0.015,
                duration_seconds=1.0,
                success=True,
                metadata={"key": "value"}
            )

            result = storage.store(entry)
            assert result.is_ok()

            entries = storage.get_all()
            assert len(entries) == 1
            assert entries[0].operation == "test"
            assert entries[0].metadata == {"key": "value"}

            storage.close()

    def test_handles_in_memory_database(self):
        """Should support in-memory SQLite database."""
        storage = SQLiteStorage(":memory:")

        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            operation="test",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.01,
            duration_seconds=1.0,
            success=True
        )

        storage.store(entry)
        entries = storage.get_all()
        assert len(entries) == 1

        storage.close()

    def test_filters_by_metadata(self):
        """Should filter entries by metadata fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            storage = SQLiteStorage(str(db_path))

            storage.store(CostEntry(
                timestamp=datetime.now().isoformat(),
                operation="op1",
                model="gpt-4",
                model_tier=ModelTier.CLOUD_STANDARD,
                tokens_in=100,
                tokens_out=200,
                cost_usd=0.01,
                duration_seconds=1.0,
                success=True,
                metadata={"agent": "agent1"}
            ))

            storage.store(CostEntry(
                timestamp=datetime.now().isoformat(),
                operation="op2",
                model="gpt-4",
                model_tier=ModelTier.CLOUD_STANDARD,
                tokens_in=100,
                tokens_out=200,
                cost_usd=0.02,
                duration_seconds=1.0,
                success=True,
                metadata={"agent": "agent2"}
            ))

            entries = storage.get_by_metadata({"agent": "agent1"})
            assert len(entries) == 1
            assert entries[0].metadata["agent"] == "agent1"

            storage.close()


class TestCostTracker:
    """Test main CostTracker class."""

    def test_tracks_operation_successfully(self):
        """Should track operation and calculate cost."""
        tracker = CostTracker(storage=MemoryStorage())

        result = tracker.track(
            operation="test_op",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=1000,
            tokens_out=2000,
            duration_seconds=2.5,
            success=True
        )

        assert result.is_ok()
        entry = result.unwrap()
        assert entry.operation == "test_op"
        assert entry.cost_usd > 0
        assert entry.tokens_in == 1000
        assert entry.tokens_out == 2000

    def test_calculates_cost_correctly(self):
        """Should calculate cost based on model tier pricing."""
        tracker = CostTracker(storage=MemoryStorage())

        # CLOUD_STANDARD: $0.0025/1K input, $0.01/1K output
        result = tracker.track(
            operation="test",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=1000,
            tokens_out=1000,
            duration_seconds=1.0,
            success=True
        )

        entry = result.unwrap()
        expected_cost = (1000 / 1000 * 0.0025) + (1000 / 1000 * 0.01)
        assert entry.cost_usd == pytest.approx(expected_cost)

    def test_tracks_with_metadata(self):
        """Should store custom metadata with entry."""
        tracker = CostTracker(storage=MemoryStorage())

        result = tracker.track(
            operation="test",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=100,
            tokens_out=200,
            duration_seconds=1.0,
            success=True,
            metadata={"agent": "test_agent", "task_id": "123"}
        )

        entry = result.unwrap()
        assert entry.metadata["agent"] == "test_agent"
        assert entry.metadata["task_id"] == "123"

    def test_returns_error_for_invalid_tokens(self):
        """Should return error for negative token counts."""
        tracker = CostTracker(storage=MemoryStorage())

        result = tracker.track(
            operation="test",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=-100,
            tokens_out=200,
            duration_seconds=1.0,
            success=True
        )

        assert result.is_err()
        assert "token" in str(result.unwrap_err()).lower()

    def test_generates_summary(self):
        """Should generate cost summary statistics."""
        tracker = CostTracker(storage=MemoryStorage())

        tracker.track("op1", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)
        tracker.track("op2", "gpt-4", ModelTier.CLOUD_STANDARD, 2000, 2000, 1.0, True)

        result = tracker.get_summary()
        assert result.is_ok()

        summary = result.unwrap()
        assert summary.total_cost_usd > 0
        assert summary.total_calls == 2
        assert summary.total_tokens_in == 3000
        assert summary.total_tokens_out == 3000
        assert summary.success_rate == 1.0

    def test_summary_groups_by_operation(self):
        """Should group costs by operation."""
        tracker = CostTracker(storage=MemoryStorage())

        tracker.track("op1", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)
        tracker.track("op1", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)
        tracker.track("op2", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)

        summary = tracker.get_summary().unwrap()
        assert "op1" in summary.by_operation
        assert "op2" in summary.by_operation
        assert summary.by_operation["op1"] > summary.by_operation["op2"]

    def test_summary_groups_by_model(self):
        """Should group costs by model."""
        tracker = CostTracker(storage=MemoryStorage())

        tracker.track("op", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)
        tracker.track("op", "gpt-5", ModelTier.CLOUD_PREMIUM, 1000, 1000, 1.0, True)

        summary = tracker.get_summary().unwrap()
        assert "gpt-4" in summary.by_model
        assert "gpt-5" in summary.by_model
        # Premium tier should cost more
        assert summary.by_model["gpt-5"] > summary.by_model["gpt-4"]

    def test_filters_summary_by_date(self):
        """Should filter summary by date range."""
        tracker = CostTracker(storage=MemoryStorage())
        now = datetime.now()

        # Old entry (manually set timestamp)
        old_entry = CostEntry(
            timestamp=(now - timedelta(days=2)).isoformat(),
            operation="old",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=1000,
            tokens_out=1000,
            cost_usd=0.0125,
            duration_seconds=1.0,
            success=True
        )
        tracker.storage.store(old_entry)

        # Recent entry
        tracker.track("recent", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)

        start_date = now - timedelta(days=1)
        summary = tracker.get_summary(start_date=start_date).unwrap()

        assert summary.total_calls == 1
        assert "recent" in summary.by_operation

    def test_calculates_success_rate(self):
        """Should calculate success rate from successful and failed operations."""
        tracker = CostTracker(storage=MemoryStorage())

        tracker.track("op", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)
        tracker.track("op", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)
        tracker.track("op", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, False)

        summary = tracker.get_summary().unwrap()
        assert summary.success_rate == pytest.approx(2/3)


class TestBudgetManagement:
    """Test budget tracking and alerts."""

    def test_sets_budget_limit(self):
        """Should set budget limit and threshold."""
        tracker = CostTracker(storage=MemoryStorage())

        result = tracker.set_budget(limit_usd=10.0, alert_threshold_pct=80.0)
        assert result.is_ok()

        status = tracker.get_budget_status().unwrap()
        assert status.limit_usd == 10.0
        assert status.alert_threshold_pct == 80.0

    def test_validates_budget_parameters(self):
        """Should reject invalid budget parameters."""
        tracker = CostTracker(storage=MemoryStorage())

        result = tracker.set_budget(limit_usd=-10.0, alert_threshold_pct=80.0)
        assert result.is_err()

        result = tracker.set_budget(limit_usd=10.0, alert_threshold_pct=150.0)
        assert result.is_err()

    def test_tracks_budget_status(self):
        """Should calculate budget status correctly."""
        tracker = CostTracker(storage=MemoryStorage())
        tracker.set_budget(limit_usd=10.0, alert_threshold_pct=80.0)

        tracker.track("op", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)

        status = tracker.get_budget_status().unwrap()
        assert status.spent_usd > 0
        assert status.remaining_usd == status.limit_usd - status.spent_usd
        assert status.percent_used == (status.spent_usd / status.limit_usd) * 100

    def test_detects_budget_threshold_exceeded(self):
        """Should detect when budget threshold is exceeded."""
        tracker = CostTracker(storage=MemoryStorage())
        tracker.set_budget(limit_usd=0.01, alert_threshold_pct=50.0)

        # Track operation that exceeds threshold
        tracker.track("op", "gpt-4", ModelTier.CLOUD_STANDARD, 10000, 10000, 1.0, True)

        status = tracker.get_budget_status().unwrap()
        assert status.alert_triggered is True
        assert status.percent_used > 50.0

    def test_detects_budget_limit_exceeded(self):
        """Should detect when budget limit is exceeded."""
        tracker = CostTracker(storage=MemoryStorage())
        tracker.set_budget(limit_usd=0.01, alert_threshold_pct=80.0)

        # Track expensive operation
        tracker.track("op", "gpt-5", ModelTier.CLOUD_PREMIUM, 10000, 10000, 1.0, True)

        status = tracker.get_budget_status().unwrap()
        assert status.limit_exceeded is True

    def test_returns_none_when_no_budget_set(self):
        """Should indicate no budget when not configured."""
        tracker = CostTracker(storage=MemoryStorage())

        status = tracker.get_budget_status().unwrap()
        assert status.limit_usd is None
        assert status.alert_triggered is False
        assert status.limit_exceeded is False


class TestTrendCalculations:
    """Test spending trend calculations."""

    def test_calculates_hourly_rate(self):
        """Should calculate hourly spending rate."""
        tracker = CostTracker(storage=MemoryStorage())
        now = datetime.now()

        # Add entries in last hour
        for i in range(3):
            entry = CostEntry(
                timestamp=(now - timedelta(minutes=i*10)).isoformat(),
                operation="op",
                model="gpt-4",
                model_tier=ModelTier.CLOUD_STANDARD,
                tokens_in=1000,
                tokens_out=1000,
                cost_usd=0.0125,
                duration_seconds=1.0,
                success=True
            )
            tracker.storage.store(entry)

        result = tracker.get_hourly_rate()
        assert result.is_ok()
        assert result.unwrap() == pytest.approx(0.0125 * 3)

    def test_projects_daily_spending(self):
        """Should project daily spending from hourly rate."""
        tracker = CostTracker(storage=MemoryStorage())
        now = datetime.now()

        # Simulate $1/hour rate
        for i in range(4):
            entry = CostEntry(
                timestamp=(now - timedelta(minutes=i*15)).isoformat(),
                operation="op",
                model="gpt-4",
                model_tier=ModelTier.CLOUD_STANDARD,
                tokens_in=1000,
                tokens_out=1000,
                cost_usd=0.25,
                duration_seconds=1.0,
                success=True
            )
            tracker.storage.store(entry)

        result = tracker.get_daily_projection()
        assert result.is_ok()
        # $1/hour * 24 hours = $24/day
        assert result.unwrap() == pytest.approx(24.0)


class TestExportFunctionality:
    """Test export to JSON/CSV."""

    def test_exports_to_json(self):
        """Should export cost data to JSON format."""
        tracker = CostTracker(storage=MemoryStorage())
        tracker.track("op1", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)
        tracker.track("op2", "gpt-5", ModelTier.CLOUD_PREMIUM, 2000, 2000, 1.5, True)

        result = tracker.export_json()
        assert result.is_ok()

        data = json.loads(result.unwrap())
        assert "summary" in data
        assert "entries" in data
        assert data["summary"]["total_calls"] == 2
        assert len(data["entries"]) == 2

    def test_exports_filtered_data(self):
        """Should export filtered subset of data."""
        tracker = CostTracker(storage=MemoryStorage())
        now = datetime.now()

        # Old entry
        old_entry = CostEntry(
            timestamp=(now - timedelta(days=2)).isoformat(),
            operation="old",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=1000,
            tokens_out=1000,
            cost_usd=0.0125,
            duration_seconds=1.0,
            success=True
        )
        tracker.storage.store(old_entry)

        # Recent entry
        tracker.track("recent", "gpt-4", ModelTier.CLOUD_STANDARD, 1000, 1000, 1.0, True)

        start_date = now - timedelta(days=1)
        result = tracker.export_json(start_date=start_date)
        data = json.loads(result.unwrap())

        assert len(data["entries"]) == 1
        assert data["entries"][0]["operation"] == "recent"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_handles_zero_token_operations(self):
        """Should handle operations with zero tokens."""
        tracker = CostTracker(storage=MemoryStorage())

        result = tracker.track(
            operation="empty",
            model="gpt-4",
            model_tier=ModelTier.CLOUD_STANDARD,
            tokens_in=0,
            tokens_out=0,
            duration_seconds=0.1,
            success=True
        )

        assert result.is_ok()
        assert result.unwrap().cost_usd == 0.0

    def test_handles_local_model_zero_cost(self):
        """Should correctly calculate zero cost for local models."""
        tracker = CostTracker(storage=MemoryStorage())

        result = tracker.track(
            operation="local",
            model="ollama-llama3",
            model_tier=ModelTier.LOCAL,
            tokens_in=1000,
            tokens_out=1000,
            duration_seconds=2.0,
            success=True
        )

        assert result.is_ok()
        assert result.unwrap().cost_usd == 0.0

    def test_returns_empty_summary_when_no_data(self):
        """Should return empty summary when no operations tracked."""
        tracker = CostTracker(storage=MemoryStorage())

        result = tracker.get_summary()
        assert result.is_ok()

        summary = result.unwrap()
        assert summary.total_cost_usd == 0.0
        assert summary.total_calls == 0
        assert summary.success_rate == 1.0  # 100% when no data

    def test_handles_storage_backend_errors(self):
        """Should propagate storage backend errors."""
        class FailingStorage(StorageBackend):
            def store(self, entry):
                return Err(CostTrackerError("Storage failed"))
            def get_all(self):
                return []
            def get_by_operation(self, operation):
                return []
            def get_by_date_range(self, start, end):
                return []
            def get_by_metadata(self, filters):
                return []
            def clear(self):
                pass
            def close(self):
                pass

        tracker = CostTracker(storage=FailingStorage())
        result = tracker.track("op", "gpt-4", ModelTier.CLOUD_STANDARD, 100, 100, 1.0, True)

        assert result.is_err()
        assert "Storage failed" in str(result.unwrap_err())


class TestPluggableBackends:
    """Test pluggable storage backend architecture."""

    def test_uses_custom_storage_backend(self):
        """Should work with custom storage backend implementation."""
        # Custom in-memory backend for testing
        class CustomStorage(StorageBackend):
            def __init__(self):
                self.entries = []

            def store(self, entry):
                self.entries.append(entry)
                return Ok(None)

            def get_all(self):
                return self.entries

            def get_by_operation(self, operation):
                return [e for e in self.entries if e.operation == operation]

            def get_by_date_range(self, start, end):
                return [
                    e for e in self.entries
                    if start <= datetime.fromisoformat(e.timestamp) <= end
                ]

            def get_by_metadata(self, filters):
                return self.entries

            def clear(self):
                self.entries = []

            def close(self):
                pass

        tracker = CostTracker(storage=CustomStorage())
        tracker.track("test", "gpt-4", ModelTier.CLOUD_STANDARD, 100, 100, 1.0, True)

        summary = tracker.get_summary().unwrap()
        assert summary.total_calls == 1

    def test_switches_storage_backends(self):
        """Should allow switching between storage backends."""
        # Start with memory
        memory_storage = MemoryStorage()
        tracker = CostTracker(storage=memory_storage)
        tracker.track("op1", "gpt-4", ModelTier.CLOUD_STANDARD, 100, 100, 1.0, True)

        # Get entries from memory
        entries = memory_storage.get_all()
        assert len(entries) == 1

        # Switch to SQLite
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            sqlite_storage = SQLiteStorage(str(db_path))

            # Migrate entries
            for entry in entries:
                sqlite_storage.store(entry)

            # Create new tracker with SQLite
            tracker2 = CostTracker(storage=sqlite_storage)
            summary = tracker2.get_summary().unwrap()
            assert summary.total_calls == 1

            sqlite_storage.close()
