"""
Cost Tracking System for Trinity Protocol

Tracks LLM API costs across all agents with real-time monitoring.

Features:
- Per-agent cost tracking
- Per-task cost tracking
- Real-time cost dashboard
- Budget alerts
- Cost export (JSON/CSV)
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum


class ModelTier(Enum):
    """Model pricing tiers."""
    LOCAL = "local"  # Free (Ollama)
    CLOUD_MINI = "cloud_mini"  # GPT-4o-mini, Claude Haiku
    CLOUD_STANDARD = "cloud_standard"  # GPT-4, Claude Sonnet
    CLOUD_PREMIUM = "cloud_premium"  # GPT-5, Claude Opus


# Pricing (USD per 1K tokens)
PRICING = {
    ModelTier.LOCAL: {"input": 0.0, "output": 0.0},
    ModelTier.CLOUD_MINI: {"input": 0.00015, "output": 0.0006},  # GPT-4o-mini
    ModelTier.CLOUD_STANDARD: {"input": 0.0025, "output": 0.01},  # GPT-4
    ModelTier.CLOUD_PREMIUM: {"input": 0.005, "output": 0.015},  # GPT-5
}


@dataclass
class LLMCall:
    """Record of a single LLM API call."""

    timestamp: str
    agent: str
    task_id: Optional[str]
    correlation_id: Optional[str]
    model: str
    model_tier: ModelTier
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_seconds: float
    success: bool
    error: Optional[str] = None


@dataclass
class CostSummary:
    """Cost summary statistics."""

    total_cost_usd: float
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    by_agent: Dict[str, float] = field(default_factory=dict)
    by_model: Dict[str, float] = field(default_factory=dict)
    by_task: Dict[str, float] = field(default_factory=dict)
    success_rate: float = 1.0


class CostTracker:
    """
    Tracks LLM API costs with SQLite persistence.

    Features:
    - Real-time cost tracking
    - Per-agent/task/model breakdowns
    - Budget alerts
    - Export to JSON/CSV
    """

    def __init__(self, db_path: str = "trinity_costs.db", budget_usd: Optional[float] = None):
        """
        Initialize cost tracker.

        Args:
            db_path: Path to SQLite database
            budget_usd: Optional budget limit (triggers alerts)
        """
        # Handle in-memory database
        if db_path == ":memory:":
            self.db_path = ":memory:"
            self.conn = sqlite3.connect(":memory:")
        else:
            self.db_path = Path(db_path)
            self.conn = None

        self.budget_usd = budget_usd
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        if self.db_path == ":memory:":
            conn = self.conn
        else:
            conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent TEXT NOT NULL,
                task_id TEXT,
                correlation_id TEXT,
                model TEXT NOT NULL,
                model_tier TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                duration_seconds REAL NOT NULL,
                success INTEGER NOT NULL,
                error TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON llm_calls(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent ON llm_calls(agent)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task ON llm_calls(task_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_correlation ON llm_calls(correlation_id)
        """)

        conn.commit()
        if self.db_path != ":memory:":
            conn.close()

    def track_call(
        self,
        agent: str,
        model: str,
        model_tier: ModelTier,
        input_tokens: int,
        output_tokens: int,
        duration_seconds: float,
        success: bool = True,
        task_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> LLMCall:
        """
        Track a single LLM API call.

        Args:
            agent: Agent name (WITNESS, ARCHITECT, EXECUTOR, etc.)
            model: Model name (gpt-5, claude-sonnet-4.5, etc.)
            model_tier: Pricing tier
            input_tokens: Input token count
            output_tokens: Output token count
            duration_seconds: Call duration
            success: Whether call succeeded
            task_id: Optional task ID
            correlation_id: Optional correlation ID
            error: Optional error message

        Returns:
            LLMCall record
        """
        # Calculate cost
        pricing = PRICING[model_tier]
        cost_usd = (
            (input_tokens / 1000.0) * pricing["input"] +
            (output_tokens / 1000.0) * pricing["output"]
        )

        # Create record
        call = LLMCall(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            task_id=task_id,
            correlation_id=correlation_id,
            model=model,
            model_tier=model_tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            duration_seconds=duration_seconds,
            success=success,
            error=error
        )

        # Persist to database
        if self.db_path == ":memory:":
            conn = self.conn
        else:
            conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO llm_calls (
                timestamp, agent, task_id, correlation_id, model, model_tier,
                input_tokens, output_tokens, cost_usd, duration_seconds, success, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            call.timestamp,
            call.agent,
            call.task_id,
            call.correlation_id,
            call.model,
            call.model_tier.value,
            call.input_tokens,
            call.output_tokens,
            call.cost_usd,
            call.duration_seconds,
            1 if call.success else 0,
            call.error
        ))

        conn.commit()
        if self.db_path != ":memory:":
            conn.close()

        # Check budget
        if self.budget_usd:
            self._check_budget(cost_usd)

        return call

    def get_summary(
        self,
        agent: Optional[str] = None,
        task_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> CostSummary:
        """
        Get cost summary statistics.

        Args:
            agent: Filter by agent name
            task_id: Filter by task ID
            correlation_id: Filter by correlation ID
            since: Filter by timestamp

        Returns:
            CostSummary with statistics
        """
        if self.db_path == ":memory:":
            conn = self.conn
        else:
            conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Build query
        conditions = []
        params = []

        if agent:
            conditions.append("agent = ?")
            params.append(agent)
        if task_id:
            conditions.append("task_id = ?")
            params.append(task_id)
        if correlation_id:
            conditions.append("correlation_id = ?")
            params.append(correlation_id)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Total cost
        cursor.execute(f"""
            SELECT
                SUM(cost_usd),
                COUNT(*),
                SUM(input_tokens),
                SUM(output_tokens),
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END)
            FROM llm_calls
            WHERE {where_clause}
        """, params)

        row = cursor.fetchone()
        total_cost = row[0] or 0.0
        total_calls = row[1] or 0
        total_input_tokens = row[2] or 0
        total_output_tokens = row[3] or 0
        success_count = row[4] or 0

        success_rate = success_count / total_calls if total_calls > 0 else 1.0

        # By agent
        cursor.execute(f"""
            SELECT agent, SUM(cost_usd)
            FROM llm_calls
            WHERE {where_clause}
            GROUP BY agent
        """, params)

        by_agent = {row[0]: row[1] for row in cursor.fetchall()}

        # By model
        cursor.execute(f"""
            SELECT model, SUM(cost_usd)
            FROM llm_calls
            WHERE {where_clause}
            GROUP BY model
        """, params)

        by_model = {row[0]: row[1] for row in cursor.fetchall()}

        # By task
        cursor.execute(f"""
            SELECT task_id, SUM(cost_usd)
            FROM llm_calls
            WHERE {where_clause} AND task_id IS NOT NULL
            GROUP BY task_id
        """, params)

        by_task = {row[0]: row[1] for row in cursor.fetchall()}

        if self.db_path != ":memory:":
            conn.close()

        return CostSummary(
            total_cost_usd=total_cost,
            total_calls=total_calls,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            by_agent=by_agent,
            by_model=by_model,
            by_task=by_task,
            success_rate=success_rate
        )

    def get_recent_calls(self, limit: int = 10) -> List[LLMCall]:
        """
        Get recent LLM calls.

        Args:
            limit: Number of calls to return

        Returns:
            List of LLMCall records
        """
        if self.db_path == ":memory:":
            conn = self.conn
        else:
            conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                timestamp, agent, task_id, correlation_id, model, model_tier,
                input_tokens, output_tokens, cost_usd, duration_seconds, success, error
            FROM llm_calls
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        calls = []
        for row in cursor.fetchall():
            calls.append(LLMCall(
                timestamp=row[0],
                agent=row[1],
                task_id=row[2],
                correlation_id=row[3],
                model=row[4],
                model_tier=ModelTier(row[5]),
                input_tokens=row[6],
                output_tokens=row[7],
                cost_usd=row[8],
                duration_seconds=row[9],
                success=bool(row[10]),
                error=row[11]
            ))

        if self.db_path != ":memory:":
            conn.close()
        return calls

    def export_to_json(self, output_path: str) -> None:
        """Export all costs to JSON."""
        summary = self.get_summary()
        recent_calls = self.get_recent_calls(limit=100)

        data = {
            "summary": {
                "total_cost_usd": summary.total_cost_usd,
                "total_calls": summary.total_calls,
                "total_input_tokens": summary.total_input_tokens,
                "total_output_tokens": summary.total_output_tokens,
                "success_rate": summary.success_rate,
                "by_agent": summary.by_agent,
                "by_model": summary.by_model,
                "by_task": summary.by_task
            },
            "recent_calls": [
                {
                    "timestamp": call.timestamp,
                    "agent": call.agent,
                    "model": call.model,
                    "cost_usd": call.cost_usd,
                    "tokens": call.input_tokens + call.output_tokens
                }
                for call in recent_calls
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def print_dashboard(self) -> None:
        """Print real-time cost dashboard to console."""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("TRINITY PROTOCOL - COST DASHBOARD")
        print("=" * 60)

        print(f"\n💰 TOTAL COST: ${summary.total_cost_usd:.4f}")

        if self.budget_usd:
            remaining = self.budget_usd - summary.total_cost_usd
            percent = (summary.total_cost_usd / self.budget_usd) * 100
            print(f"📊 BUDGET: ${summary.total_cost_usd:.4f} / ${self.budget_usd:.2f} ({percent:.1f}%)")
            print(f"💵 REMAINING: ${remaining:.4f}")

        print(f"\n📞 TOTAL CALLS: {summary.total_calls}")
        print(f"✅ SUCCESS RATE: {summary.success_rate * 100:.1f}%")
        print(f"🔢 TOKENS: {summary.total_input_tokens:,} in + {summary.total_output_tokens:,} out")

        if summary.by_agent:
            print(f"\n📍 BY AGENT:")
            for agent, cost in sorted(summary.by_agent.items(), key=lambda x: -x[1]):
                print(f"  {agent:20s} ${cost:.4f}")

        if summary.by_model:
            print(f"\n🤖 BY MODEL:")
            for model, cost in sorted(summary.by_model.items(), key=lambda x: -x[1]):
                print(f"  {model:30s} ${cost:.4f}")

        print("\n" + "=" * 60 + "\n")

    def _check_budget(self, new_cost: float) -> None:
        """Check if budget exceeded and print warning."""
        if not self.budget_usd:
            return

        summary = self.get_summary()
        if summary.total_cost_usd > self.budget_usd:
            percent = (summary.total_cost_usd / self.budget_usd) * 100
            print(f"\n⚠️  BUDGET ALERT: ${summary.total_cost_usd:.4f} exceeds budget of ${self.budget_usd:.2f} ({percent:.1f}%)\n")

    def reset(self) -> None:
        """Reset all cost tracking (delete database)."""
        if self.db_path.exists():
            self.db_path.unlink()
        self._init_db()

    def close(self) -> None:
        """Close database connection."""
        if self.db_path == ":memory:" and self.conn:
            self.conn.close()
