from __future__ import annotations

"""
Generic Cost Tracking System

A reusable, pluggable cost tracking system for LLM operations with:
- Multiple storage backends (SQLite, memory, custom)
- Budget management and alerts
- Cost summaries and trend analysis
- Result<T,E> error handling pattern
- Strict Pydantic typing (no Dict[Any, Any])

Example:
    from shared.cost_tracker import CostTracker, MemoryStorage, ModelTier

    tracker = CostTracker(storage=MemoryStorage())
    tracker.set_budget(limit_usd=10.0, alert_threshold_pct=80.0)

    result = tracker.track(
        operation="code_generation",
        model="gpt-4",
        model_tier=ModelTier.CLOUD_STANDARD,
        tokens_in=1000,
        tokens_out=2000,
        duration_seconds=2.5,
        success=True,
        metadata={"agent": "coder"}
    )

    if result.is_ok():
        summary = tracker.get_summary()
        status = tracker.get_budget_status()
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator
from shared.type_definitions.result import Result, Ok, Err
from shared.type_definitions.json_value import JSONValue


class ModelTier(str, Enum):
    """Model pricing tiers."""
    LOCAL = "local"
    CLOUD_MINI = "cloud_mini"
    CLOUD_STANDARD = "cloud_standard"
    CLOUD_PREMIUM = "cloud_premium"


# Pricing (USD per 1K tokens)
PRICING = {
    ModelTier.LOCAL: {"input": 0.0, "output": 0.0},
    ModelTier.CLOUD_MINI: {"input": 0.00015, "output": 0.0006},
    ModelTier.CLOUD_STANDARD: {"input": 0.0025, "output": 0.01},
    ModelTier.CLOUD_PREMIUM: {"input": 0.005, "output": 0.015},
}


class CostTrackerError(Exception):
    """Base exception for cost tracker errors."""
    pass


class CostEntry(BaseModel):
    """Record of a single cost-tracked operation."""

    timestamp: str
    operation: str
    model: str
    model_tier: ModelTier
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    success: bool
    metadata: JSONValue = Field(default_factory=dict)
    error: Optional[str] = None

    @validator('tokens_in', 'tokens_out')
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError("Token counts must be non-negative")
        return v

    @validator('cost_usd')
    def validate_cost(cls, v):
        if v < 0:
            raise ValueError("Cost must be non-negative")
        return v


class CostSummary(BaseModel):
    """Cost summary statistics."""

    total_cost_usd: float
    total_calls: int
    total_tokens_in: int
    total_tokens_out: int
    success_rate: float
    by_operation: Dict[str, float] = Field(default_factory=dict)
    by_model: Dict[str, float] = Field(default_factory=dict)
    by_metadata: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class BudgetStatus(BaseModel):
    """Budget status information."""

    limit_usd: Optional[float]
    alert_threshold_pct: Optional[float]
    spent_usd: float
    remaining_usd: float
    percent_used: float
    alert_triggered: bool
    limit_exceeded: bool


class BudgetAlert(BaseModel):
    """Budget alert notification."""

    timestamp: datetime
    level: str  # "warning" or "critical"
    message: str
    spent_usd: float
    limit_usd: float
    percent_used: float


class StorageBackend(ABC):
    """Abstract base class for cost storage backends."""

    @abstractmethod
    def store(self, entry: CostEntry) -> Result[None, CostTrackerError]:
        """Store a cost entry."""
        pass

    @abstractmethod
    def get_all(self) -> List[CostEntry]:
        """Get all cost entries."""
        pass

    @abstractmethod
    def get_by_operation(self, operation: str) -> List[CostEntry]:
        """Get entries for specific operation."""
        pass

    @abstractmethod
    def get_by_date_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[CostEntry]:
        """Get entries within date range."""
        pass

    @abstractmethod
    def get_by_metadata(
        self,
        filters: Dict[str, str]
    ) -> List[CostEntry]:
        """Get entries matching metadata filters."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all entries."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close storage backend."""
        pass


class MemoryStorage(StorageBackend):
    """In-memory storage backend."""

    def __init__(self):
        self._entries: List[CostEntry] = []

    def store(self, entry: CostEntry) -> Result[None, CostTrackerError]:
        """Store entry in memory."""
        try:
            self._entries.append(entry)
            return Ok(None)
        except Exception as e:
            return Err(CostTrackerError(f"Failed to store entry: {e}"))

    def get_all(self) -> List[CostEntry]:
        """Get all entries."""
        return self._entries.copy()

    def get_by_operation(self, operation: str) -> List[CostEntry]:
        """Filter by operation."""
        return [e for e in self._entries if e.operation == operation]

    def get_by_date_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[CostEntry]:
        """Filter by date range."""
        return [
            e for e in self._entries
            if start <= datetime.fromisoformat(e.timestamp) <= end
        ]

    def get_by_metadata(
        self,
        filters: Dict[str, str]
    ) -> List[CostEntry]:
        """Filter by metadata."""
        result = []
        for entry in self._entries:
            match = all(
                entry.metadata.get(k) == v
                for k, v in filters.items()
            )
            if match:
                result.append(entry)
        return result

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()

    def close(self) -> None:
        """No-op for memory storage."""
        pass


class SQLiteStorage(StorageBackend):
    """SQLite storage backend."""

    def __init__(self, db_path: str):
        """Initialize SQLite storage."""
        self.db_path = db_path
        self.is_memory = db_path == ":memory:"

        if self.is_memory:
            self.conn = sqlite3.connect(":memory:")
        else:
            self.db_file = Path(db_path)
            self.conn = None

        self._init_schema()

    def _init_schema(self) -> None:
        """Create database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                operation TEXT NOT NULL,
                model TEXT NOT NULL,
                model_tier TEXT NOT NULL,
                tokens_in INTEGER NOT NULL,
                tokens_out INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                duration_seconds REAL NOT NULL,
                success INTEGER NOT NULL,
                metadata TEXT,
                error TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON cost_entries(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_operation
            ON cost_entries(operation)
        """)

        conn.commit()
        if not self.is_memory:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self.is_memory:
            return self.conn
        return sqlite3.connect(str(self.db_file))

    def store(self, entry: CostEntry) -> Result[None, CostTrackerError]:
        """Store entry in SQLite."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO cost_entries (
                    timestamp, operation, model, model_tier,
                    tokens_in, tokens_out, cost_usd,
                    duration_seconds, success, metadata, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.timestamp,
                entry.operation,
                entry.model,
                entry.model_tier.value,
                entry.tokens_in,
                entry.tokens_out,
                entry.cost_usd,
                entry.duration_seconds,
                1 if entry.success else 0,
                json.dumps(entry.metadata) if entry.metadata else None,
                entry.error
            ))

            conn.commit()
            if not self.is_memory:
                conn.close()

            return Ok(None)
        except Exception as e:
            return Err(CostTrackerError(f"Storage error: {e}"))

    def get_all(self) -> List[CostEntry]:
        """Get all entries."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, operation, model, model_tier,
                   tokens_in, tokens_out, cost_usd,
                   duration_seconds, success, metadata, error
            FROM cost_entries
            ORDER BY timestamp
        """)

        entries = self._rows_to_entries(cursor.fetchall())
        if not self.is_memory:
            conn.close()
        return entries

    def get_by_operation(self, operation: str) -> List[CostEntry]:
        """Get entries by operation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, operation, model, model_tier,
                   tokens_in, tokens_out, cost_usd,
                   duration_seconds, success, metadata, error
            FROM cost_entries
            WHERE operation = ?
            ORDER BY timestamp
        """, (operation,))

        entries = self._rows_to_entries(cursor.fetchall())
        if not self.is_memory:
            conn.close()
        return entries

    def get_by_date_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[CostEntry]:
        """Get entries in date range."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, operation, model, model_tier,
                   tokens_in, tokens_out, cost_usd,
                   duration_seconds, success, metadata, error
            FROM cost_entries
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp
        """, (start.isoformat(), end.isoformat()))

        entries = self._rows_to_entries(cursor.fetchall())
        if not self.is_memory:
            conn.close()
        return entries

    def get_by_metadata(
        self,
        filters: Dict[str, str]
    ) -> List[CostEntry]:
        """Get entries by metadata filters."""
        all_entries = self.get_all()
        result = []

        for entry in all_entries:
            match = all(
                entry.metadata.get(k) == v
                for k, v in filters.items()
            )
            if match:
                result.append(entry)

        return result

    def clear(self) -> None:
        """Clear all entries."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cost_entries")
        conn.commit()
        if not self.is_memory:
            conn.close()

    def close(self) -> None:
        """Close connection."""
        if self.is_memory and self.conn:
            self.conn.close()

    def _rows_to_entries(self, rows) -> List[CostEntry]:
        """Convert database rows to CostEntry objects."""
        entries = []
        for row in rows:
            metadata = json.loads(row[9]) if row[9] else {}
            entries.append(CostEntry(
                timestamp=row[0],
                operation=row[1],
                model=row[2],
                model_tier=ModelTier(row[3]),
                tokens_in=row[4],
                tokens_out=row[5],
                cost_usd=row[6],
                duration_seconds=row[7],
                success=bool(row[8]),
                metadata=metadata,
                error=row[10]
            ))
        return entries


class CostTracker:
    """
    Generic cost tracker with pluggable storage.

    Tracks LLM operation costs with budget management and analytics.
    """

    def __init__(self, storage: StorageBackend):
        """Initialize cost tracker with storage backend."""
        self.storage = storage
        self.budget_limit: Optional[float] = None
        self.budget_threshold: Optional[float] = None

    def track(
        self,
        operation: str,
        model: str,
        model_tier: ModelTier,
        tokens_in: int,
        tokens_out: int,
        duration_seconds: float,
        success: bool,
        metadata: Optional[JSONValue] = None,
        error: Optional[str] = None
    ) -> Result[CostEntry, CostTrackerError]:
        """Track a single operation cost."""
        try:
            # Validate inputs
            if tokens_in < 0 or tokens_out < 0:
                return Err(
                    CostTrackerError("Token counts must be non-negative")
                )

            # Calculate cost
            cost_usd = self._calculate_cost(
                model_tier,
                tokens_in,
                tokens_out
            )

            # Create entry
            entry = CostEntry(
                timestamp=datetime.now().isoformat(),
                operation=operation,
                model=model,
                model_tier=model_tier,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=cost_usd,
                duration_seconds=duration_seconds,
                success=success,
                metadata=metadata or {},
                error=error
            )

            # Store entry
            store_result = self.storage.store(entry)
            if store_result.is_err():
                return Err(store_result.unwrap_err())

            return Ok(entry)

        except Exception as e:
            return Err(CostTrackerError(f"Tracking failed: {e}"))

    def get_summary(
        self,
        operation: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metadata_filters: Optional[Dict[str, str]] = None
    ) -> Result[CostSummary, CostTrackerError]:
        """Get cost summary with optional filters."""
        try:
            # Get filtered entries
            if metadata_filters:
                entries = self.storage.get_by_metadata(metadata_filters)
            elif operation:
                entries = self.storage.get_by_operation(operation)
            elif start_date and end_date:
                entries = self.storage.get_by_date_range(
                    start_date,
                    end_date
                )
            elif start_date:
                entries = self.storage.get_by_date_range(
                    start_date,
                    datetime.now()
                )
            else:
                entries = self.storage.get_all()

            # Calculate summary
            total_cost = sum(e.cost_usd for e in entries)
            total_calls = len(entries)
            total_tokens_in = sum(e.tokens_in for e in entries)
            total_tokens_out = sum(e.tokens_out for e in entries)

            success_count = sum(1 for e in entries if e.success)
            success_rate = (
                success_count / total_calls if total_calls > 0 else 1.0
            )

            # Group by operation
            by_operation: Dict[str, float] = {}
            for entry in entries:
                by_operation[entry.operation] = (
                    by_operation.get(entry.operation, 0.0) + entry.cost_usd
                )

            # Group by model
            by_model: Dict[str, float] = {}
            for entry in entries:
                by_model[entry.model] = (
                    by_model.get(entry.model, 0.0) + entry.cost_usd
                )

            summary = CostSummary(
                total_cost_usd=total_cost,
                total_calls=total_calls,
                total_tokens_in=total_tokens_in,
                total_tokens_out=total_tokens_out,
                success_rate=success_rate,
                by_operation=by_operation,
                by_model=by_model
            )

            return Ok(summary)

        except Exception as e:
            return Err(CostTrackerError(f"Summary failed: {e}"))

    def set_budget(
        self,
        limit_usd: float,
        alert_threshold_pct: float
    ) -> Result[None, CostTrackerError]:
        """Set budget limit and alert threshold."""
        if limit_usd < 0:
            return Err(CostTrackerError("Budget limit must be positive"))
        if alert_threshold_pct < 0 or alert_threshold_pct > 100:
            return Err(
                CostTrackerError("Threshold must be between 0 and 100")
            )

        self.budget_limit = limit_usd
        self.budget_threshold = alert_threshold_pct
        return Ok(None)

    def get_budget_status(self) -> Result[BudgetStatus, CostTrackerError]:
        """Get current budget status."""
        try:
            summary_result = self.get_summary()
            if summary_result.is_err():
                return Err(summary_result.unwrap_err())

            summary = summary_result.unwrap()
            spent = summary.total_cost_usd

            if self.budget_limit is None:
                return Ok(BudgetStatus(
                    limit_usd=None,
                    alert_threshold_pct=None,
                    spent_usd=spent,
                    remaining_usd=0.0,
                    percent_used=0.0,
                    alert_triggered=False,
                    limit_exceeded=False
                ))

            remaining = self.budget_limit - spent
            percent_used = (spent / self.budget_limit) * 100

            alert_triggered = (
                self.budget_threshold is not None and
                percent_used >= self.budget_threshold
            )

            limit_exceeded = spent > self.budget_limit

            return Ok(BudgetStatus(
                limit_usd=self.budget_limit,
                alert_threshold_pct=self.budget_threshold,
                spent_usd=spent,
                remaining_usd=remaining,
                percent_used=percent_used,
                alert_triggered=alert_triggered,
                limit_exceeded=limit_exceeded
            ))

        except Exception as e:
            return Err(CostTrackerError(f"Budget status failed: {e}"))

    def get_hourly_rate(self) -> Result[float, CostTrackerError]:
        """Calculate hourly spending rate."""
        try:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            summary = self.get_summary(start_date=one_hour_ago).unwrap()
            return Ok(summary.total_cost_usd)
        except Exception as e:
            return Err(CostTrackerError(f"Hourly rate failed: {e}"))

    def get_daily_projection(self) -> Result[float, CostTrackerError]:
        """Project daily spending from hourly rate."""
        hourly_result = self.get_hourly_rate()
        if hourly_result.is_err():
            return Err(hourly_result.unwrap_err())

        daily_projection = hourly_result.unwrap() * 24
        return Ok(daily_projection)

    def export_json(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Result[str, CostTrackerError]:
        """Export cost data to JSON."""
        try:
            summary_result = self.get_summary(
                start_date=start_date,
                end_date=end_date
            )
            if summary_result.is_err():
                return Err(summary_result.unwrap_err())

            summary = summary_result.unwrap()

            # Get entries for export
            if start_date and end_date:
                entries = self.storage.get_by_date_range(
                    start_date,
                    end_date
                )
            elif start_date:
                entries = self.storage.get_by_date_range(
                    start_date,
                    datetime.now()
                )
            else:
                entries = self.storage.get_all()

            data = {
                "summary": summary.dict(),
                "entries": [e.dict() for e in entries]
            }

            return Ok(json.dumps(data, indent=2))

        except Exception as e:
            return Err(CostTrackerError(f"Export failed: {e}"))

    def _calculate_cost(
        self,
        tier: ModelTier,
        tokens_in: int,
        tokens_out: int
    ) -> float:
        """Calculate cost based on model tier and tokens."""
        pricing = PRICING[tier]
        input_cost = (tokens_in / 1000.0) * pricing["input"]
        output_cost = (tokens_out / 1000.0) * pricing["output"]
        return input_cost + output_cost
