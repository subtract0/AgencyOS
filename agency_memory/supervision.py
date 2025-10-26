"""
Supervision Module - RLHF and DPO training data management.

This module provides data structures and utilities for storing supervision signals
(reinforcement learning human feedback) and exporting training datasets for
DPO (Direct Preference Optimization) and RLHF training.

Constitutional Compliance:
- Article VIII: Supervision signal density ≥90%
- Article VIII: Quality score ≥0.8 tagged as "rl_training_data"
- Article VIII: Training data quality ≥0.80 average

Performance:
- Export formats: JSONL (streaming), CSV (analysis), Parquet (ML training)
- Compression: gzip support for large datasets
- Validation: Pydantic models ensure data quality

Example Usage:
    from agency_memory.supervision import SupervisionSignal, export_supervision_dataset

    # Create supervision signal
    signal = SupervisionSignal(
        memory_id="jwt_auth_success_123",
        outcome="approved",
        quality_score=0.95,
        learning_value=1.0,
        actor="human",
        reason="Excellent implementation, clean code"
    )

    # Export supervision dataset for DPO/RLHF training
    result = export_supervision_dataset(
        vector_store=vector_store,
        output_path="benchmarks/supervision_dataset.jsonl",
        min_quality_score=0.8,
        format="jsonl"
    )

    if result.is_ok():
        stats = result.unwrap()
        print(f"Exported {stats['total_records']} supervision signals")
"""

import gzip
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class SupervisionOutcome(str, Enum):
    """Supervision outcome categories for RLHF training."""

    APPROVED = "approved"  # Human/agent approved this action
    REJECTED = "rejected"  # Human/agent rejected this action
    NEUTRAL = "neutral"  # Neutral feedback (neither good nor bad)


class SupervisionSignal(BaseModel):
    """Supervision signal for RLHF-style feedback (Article VIII).

    Stores reinforcement signal (approved/rejected/neutral) for training data curation.
    This enables DPO/RLHF-style learning loops.

    Attributes:
        memory_id: Memory record identifier being supervised
        outcome: Supervision outcome (approved, rejected, neutral)
        quality_score: Quality assessment (0.0-1.0, ≥0.8 → "rl_training_data")
        learning_value: How valuable this is for future learning (0.0-1.0)
        actor: Who provided supervision (human, agent, automated)
        reason: Why this supervision was applied
        counterfactual: Optional alternative approach that would be better/worse
        preference: Optional preference data (e.g., "approach A > approach B")
        timestamp: ISO timestamp of supervision
        provenance: Provenance metadata (origin, actor, retention_policy)

    Article VIII Compliance:
        - Supervision signal density target: ≥90%
        - Quality score ≥0.8 tagged as "rl_training_data"
        - Counterfactuals enable what-if analysis
    """

    memory_id: str = Field(..., description="Memory record identifier")
    outcome: SupervisionOutcome = Field(..., description="Supervision outcome")
    quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Quality assessment (0.0-1.0)"
    )
    learning_value: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How valuable for future learning (0.0-1.0)",
    )
    actor: str = Field(default="automated", description="Who provided supervision")
    reason: str = Field(default="", description="Why this supervision was applied")
    counterfactual: dict[str, Any] | None = Field(
        default=None, description="Alternative approach (what-if analysis)"
    )
    preference: dict[str, Any] | None = Field(
        default=None, description="Preference data (approach A > approach B)"
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    provenance: dict[str, Any] = Field(
        default_factory=lambda: {
            "origin": "supervision",
            "actor": "automated",
            "timestamp": datetime.now().isoformat(),
            "retention_policy": "permanent",
        }
    )

    @field_validator("quality_score")
    @classmethod
    def validate_quality_score(cls, v: float) -> float:
        """Validate quality score is in range [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Quality score must be 0.0-1.0, got {v}")
        return v

    @field_validator("learning_value")
    @classmethod
    def validate_learning_value(cls, v: float) -> float:
        """Validate learning value is in range [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Learning value must be 0.0-1.0, got {v}")
        return v

    def is_high_quality(self) -> bool:
        """Check if supervision signal qualifies as high-quality training data.

        Article VIII Requirement: quality_score ≥0.8 → "rl_training_data" tag
        """
        return self.quality_score >= 0.8

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "memory_id": self.memory_id,
            "outcome": self.outcome.value,
            "quality_score": self.quality_score,
            "learning_value": self.learning_value,
            "actor": self.actor,
            "reason": self.reason,
            "counterfactual": self.counterfactual,
            "preference": self.preference,
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }

    def to_jsonl_record(self) -> str:
        """Convert to JSONL record for dataset export."""
        return json.dumps(self.to_dict())


class DPODatasetRecord(BaseModel):
    """DPO (Direct Preference Optimization) training record.

    Format:
        - prompt: Task description or context
        - chosen: Preferred response (higher quality)
        - rejected: Rejected response (lower quality)
        - metadata: Additional context for training

    DPO Training Formula:
        Loss = -log(σ(β * (log π_θ(chosen|prompt) - log π_θ(rejected|prompt))))
        where σ = sigmoid, β = temperature, π_θ = policy model

    Reference:
        https://arxiv.org/abs/2305.18290 (DPO: Direct Preference Optimization)
    """

    prompt: str = Field(..., description="Task description or context")
    chosen: str = Field(..., description="Preferred response (higher quality)")
    rejected: str = Field(..., description="Rejected response (lower quality)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "prompt": self.prompt,
            "chosen": self.chosen,
            "rejected": self.rejected,
            "metadata": self.metadata,
        }

    def to_jsonl_record(self) -> str:
        """Convert to JSONL record for dataset export."""
        return json.dumps(self.to_dict())


def export_supervision_dataset(
    vector_store: Any,
    output_path: str,
    min_quality_score: float = 0.8,
    format: str = "jsonl",
    compress: bool = False,
) -> Result[dict[str, Any], str]:
    """Export supervision signals to training dataset file.

    Exports all supervision signals from VectorStore that meet quality threshold
    to file in specified format (JSONL, CSV, Parquet).

    Args:
        vector_store: VectorStore instance containing supervision signals
        output_path: Output file path (e.g., "benchmarks/supervision_dataset.jsonl")
        min_quality_score: Minimum quality score to include (default: 0.8, Article VIII)
        format: Output format ("jsonl", "csv", "parquet")
        compress: Whether to gzip compress output (for JSONL/CSV)

    Returns:
        Result with export statistics dict:
            - total_records: Total supervision signals exported
            - avg_quality_score: Average quality score
            - high_quality_count: Records with quality ≥0.9
            - file_path: Output file path

    Article VIII Compliance:
        - Only exports signals with quality_score ≥ min_quality_score
        - Includes provenance metadata for all records
        - Counts as training data quality metric

    Example:
        >>> from agency_memory.supervision import export_supervision_dataset
        >>> result = export_supervision_dataset(
        ...     vector_store=vector_store,
        ...     output_path="benchmarks/supervision_dataset.jsonl",
        ...     min_quality_score=0.8,
        ...     format="jsonl",
        ...     compress=True
        ... )
        >>> if result.is_ok():
        ...     stats = result.unwrap()
        ...     print(f"Exported {stats['total_records']} records")
    """
    try:
        # Query all supervision signals
        supervision_signals = vector_store.search_by_tags(
            tags=["supervision", "rl_data"], min_confidence=0.0  # Get all
        )

        # Filter by quality score
        high_quality_signals = [
            s
            for s in supervision_signals
            if s.get("content", {}).get("signal", {}).get("quality_score", 0.0)
            >= min_quality_score
        ]

        if not high_quality_signals:
            return Err(
                f"No supervision signals found with quality_score ≥ {min_quality_score}"
            )

        # Create output directory if needed
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Export based on format
        if format == "jsonl":
            _export_jsonl(high_quality_signals, output_file, compress)
        elif format == "csv":
            _export_csv(high_quality_signals, output_file, compress)
        elif format == "parquet":
            _export_parquet(high_quality_signals, output_file)
        else:
            return Err(f"Unsupported format: {format} (use jsonl, csv, or parquet)")

        # Calculate statistics
        quality_scores = [
            s.get("content", {}).get("signal", {}).get("quality_score", 0.0)
            for s in high_quality_signals
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        high_quality_count = sum(1 for q in quality_scores if q >= 0.9)

        stats = {
            "total_records": len(high_quality_signals),
            "avg_quality_score": round(avg_quality, 2),
            "high_quality_count": high_quality_count,
            "file_path": str(output_file),
        }

        logger.info(
            f"Supervision dataset exported: {stats['total_records']} records "
            f"(avg quality: {stats['avg_quality_score']:.2f}, "
            f"high quality: {stats['high_quality_count']})"
        )

        return Ok(stats)

    except Exception as e:
        logger.error(f"Supervision dataset export failed: {e}")
        return Err(f"Export error: {e}")


def _export_jsonl(
    signals: list[dict[str, Any]], output_file: Path, compress: bool
) -> None:
    """Export supervision signals to JSONL format."""
    open_func = gzip.open if compress else open
    file_mode = "wt" if compress else "w"

    with open_func(output_file, file_mode) as f:
        for signal in signals:
            # Extract signal content
            signal_data = signal.get("content", {}).get("signal", {})

            # Create SupervisionSignal record
            record = {
                "memory_id": signal_data.get("memory_id", "unknown"),
                "outcome": signal_data.get("outcome", "neutral"),
                "quality_score": signal_data.get("quality_score", 0.0),
                "learning_value": signal_data.get("learning_value", 0.5),
                "actor": signal_data.get("actor", "automated"),
                "reason": signal_data.get("reason", ""),
                "counterfactual": signal_data.get("counterfactual"),
                "preference": signal_data.get("preference"),
                "timestamp": signal_data.get("timestamp", datetime.now().isoformat()),
                "provenance": signal_data.get(
                    "provenance",
                    {
                        "origin": "supervision",
                        "actor": "automated",
                        "timestamp": datetime.now().isoformat(),
                        "retention_policy": "permanent",
                    },
                ),
            }

            f.write(json.dumps(record) + "\n")


def _export_csv(
    signals: list[dict[str, Any]], output_file: Path, compress: bool
) -> None:
    """Export supervision signals to CSV format."""
    import csv

    open_func = gzip.open if compress else open
    file_mode = "wt" if compress else "w"

    with open_func(output_file, file_mode, newline="") as f:
        fieldnames = [
            "memory_id",
            "outcome",
            "quality_score",
            "learning_value",
            "actor",
            "reason",
            "timestamp",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for signal in signals:
            signal_data = signal.get("content", {}).get("signal", {})
            writer.writerow(
                {
                    "memory_id": signal_data.get("memory_id", "unknown"),
                    "outcome": signal_data.get("outcome", "neutral"),
                    "quality_score": signal_data.get("quality_score", 0.0),
                    "learning_value": signal_data.get("learning_value", 0.5),
                    "actor": signal_data.get("actor", "automated"),
                    "reason": signal_data.get("reason", ""),
                    "timestamp": signal_data.get("timestamp", datetime.now().isoformat()),
                }
            )


def _export_parquet(signals: list[dict[str, Any]], output_file: Path) -> None:
    """Export supervision signals to Parquet format (requires pyarrow).

    Parquet is preferred for ML training due to:
    - Columnar storage (faster filtering)
    - Compression (50-90% size reduction vs JSONL)
    - Type safety (schema enforcement)
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError("pyarrow required for Parquet export: pip install pyarrow")

    # Convert signals to tabular format
    records = []
    for signal in signals:
        signal_data = signal.get("content", {}).get("signal", {})
        records.append(
            {
                "memory_id": signal_data.get("memory_id", "unknown"),
                "outcome": signal_data.get("outcome", "neutral"),
                "quality_score": signal_data.get("quality_score", 0.0),
                "learning_value": signal_data.get("learning_value", 0.5),
                "actor": signal_data.get("actor", "automated"),
                "reason": signal_data.get("reason", ""),
                "timestamp": signal_data.get("timestamp", datetime.now().isoformat()),
            }
        )

    # Create PyArrow table
    table = pa.Table.from_pylist(records)

    # Write to Parquet with compression
    pq.write_table(table, output_file, compression="snappy")
