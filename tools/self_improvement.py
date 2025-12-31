"""
Self-Improvement Engine - Autonomous system enhancement.

Enables the system to improve itself through:
- Performance analysis and optimization
- Pattern extraction from successful operations
- Configuration tuning
- Tool capability enhancement
- Knowledge base expansion

Constitutional Compliance:
- Article IV: Continuous learning (core mandate)
- Article II: 100% verification (validates improvements)
- Article III: Automated enforcement (applies improvements safely)
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


class ImprovementType(Enum):
    """Types of improvements."""

    PERFORMANCE = "performance"
    QUALITY = "quality"
    CAPABILITY = "capability"
    CONFIGURATION = "configuration"
    PATTERN = "pattern"
    KNOWLEDGE = "knowledge"


class ImprovementStatus(Enum):
    """Status of an improvement proposal."""

    PROPOSED = "proposed"
    ANALYZING = "analyzing"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLYING = "applying"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class ImprovementProposal:
    """A proposed improvement to the system."""

    id: str
    title: str
    description: str
    improvement_type: ImprovementType
    source: str  # Where this improvement came from
    confidence: float  # 0.0-1.0
    estimated_impact: float  # 0.0-1.0
    status: ImprovementStatus = ImprovementStatus.PROPOSED
    created_at: datetime = field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None
    evidence: list[dict] = field(default_factory=list)
    changes: list[dict] = field(default_factory=list)
    metrics_before: Optional[dict] = None
    metrics_after: Optional[dict] = None
    rollback_info: Optional[dict] = None


@dataclass
class PerformanceMetrics:
    """System performance metrics."""

    task_success_rate: float
    avg_task_duration_ms: float
    error_rate: float
    memory_usage_mb: float
    patterns_learned: int
    improvements_applied: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningOutcome:
    """Outcome of a learning attempt."""

    pattern_id: str
    pattern_type: str
    success: bool
    confidence: float
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    context: dict = field(default_factory=dict)


class PatternAnalyzer:
    """
    Analyzes patterns from system operations.

    Extracts learnable patterns from:
    - Successful task completions
    - Error recovery sequences
    - Performance optimizations
    - User feedback
    """

    def __init__(self):
        """Initialize the pattern analyzer."""
        self._patterns: dict[str, LearningOutcome] = {}
        self._pattern_counter = 0

    def analyze_success(
        self,
        task_type: str,
        context: dict,
        duration_ms: float,
    ) -> Result[LearningOutcome, str]:
        """
        Analyze a successful task completion.

        Args:
            task_type: Type of task completed
            context: Task context
            duration_ms: Task duration

        Returns:
            Result containing extracted pattern
        """
        pattern_id = f"success-{task_type}-{self._pattern_counter:04d}"
        self._pattern_counter += 1

        outcome = LearningOutcome(
            pattern_id=pattern_id,
            pattern_type="success",
            success=True,
            confidence=0.7,  # Base confidence
            occurrences=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            context={
                "task_type": task_type,
                "duration_ms": duration_ms,
                **context,
            },
        )

        # Check if similar pattern exists
        similar = self._find_similar(task_type, context)
        if similar:
            # Reinforce existing pattern
            similar.occurrences += 1
            similar.last_seen = datetime.now()
            similar.confidence = min(0.99, similar.confidence + 0.05)
            return Ok(similar)

        self._patterns[pattern_id] = outcome
        return Ok(outcome)

    def analyze_failure(
        self,
        task_type: str,
        error: str,
        context: dict,
    ) -> Result[LearningOutcome, str]:
        """
        Analyze a task failure.

        Args:
            task_type: Type of task that failed
            error: Error message
            context: Task context

        Returns:
            Result containing failure pattern
        """
        pattern_id = f"failure-{task_type}-{self._pattern_counter:04d}"
        self._pattern_counter += 1

        outcome = LearningOutcome(
            pattern_id=pattern_id,
            pattern_type="failure",
            success=False,
            confidence=0.6,
            occurrences=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            context={
                "task_type": task_type,
                "error": error,
                **context,
            },
        )

        self._patterns[pattern_id] = outcome
        return Ok(outcome)

    def _find_similar(self, task_type: str, context: dict) -> Optional[LearningOutcome]:
        """Find a similar pattern in the store."""
        for pattern in self._patterns.values():
            if pattern.context.get("task_type") == task_type:
                return pattern
        return None

    def get_high_confidence_patterns(
        self, min_confidence: float = 0.8
    ) -> list[LearningOutcome]:
        """Get patterns with high confidence."""
        return [
            p for p in self._patterns.values()
            if p.confidence >= min_confidence
        ]

    def get_stats(self) -> dict:
        """Get pattern analysis statistics."""
        success_patterns = [p for p in self._patterns.values() if p.success]
        failure_patterns = [p for p in self._patterns.values() if not p.success]

        return {
            "total_patterns": len(self._patterns),
            "success_patterns": len(success_patterns),
            "failure_patterns": len(failure_patterns),
            "high_confidence": len(self.get_high_confidence_patterns()),
        }


class SelfImprovement:
    """
    Autonomous self-improvement engine.

    Continuously analyzes system performance and applies
    improvements based on learned patterns.
    """

    IMPROVEMENT_STORE = PROJECT_ROOT / "logs" / "improvements.json"
    MIN_CONFIDENCE_FOR_AUTO_APPLY = 0.9

    def __init__(self):
        """Initialize the self-improvement engine."""
        self._proposals: dict[str, ImprovementProposal] = {}
        self._applied: list[str] = []
        self._pattern_analyzer = PatternAnalyzer()
        self._proposal_counter = 0
        self._metrics_history: list[PerformanceMetrics] = []
        self._load_state()

    def _load_state(self) -> None:
        """Load state from disk."""
        if self.IMPROVEMENT_STORE.exists():
            try:
                data = json.loads(self.IMPROVEMENT_STORE.read_text())
                self._applied = data.get("applied", [])
            except Exception:
                pass

    def _save_state(self) -> None:
        """Save state to disk."""
        self.IMPROVEMENT_STORE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "applied": self._applied,
            "proposals": [p.id for p in self._proposals.values()],
            "last_updated": datetime.now().isoformat(),
        }
        self.IMPROVEMENT_STORE.write_text(json.dumps(data, indent=2))

    def propose_improvement(
        self,
        title: str,
        description: str,
        improvement_type: ImprovementType,
        source: str,
        confidence: float,
        estimated_impact: float,
        evidence: Optional[list[dict]] = None,
    ) -> Result[ImprovementProposal, str]:
        """
        Propose a new improvement.

        Args:
            title: Improvement title
            description: Detailed description
            improvement_type: Type of improvement
            source: Where this came from
            confidence: Confidence level (0-1)
            estimated_impact: Expected impact (0-1)
            evidence: Supporting evidence

        Returns:
            Result containing ImprovementProposal
        """
        if not title:
            return Err("Title is required")

        if confidence < 0 or confidence > 1:
            return Err("Confidence must be between 0 and 1")

        self._proposal_counter += 1
        proposal_id = f"imp-{self._proposal_counter:06d}"

        proposal = ImprovementProposal(
            id=proposal_id,
            title=title,
            description=description,
            improvement_type=improvement_type,
            source=source,
            confidence=confidence,
            estimated_impact=estimated_impact,
            evidence=evidence or [],
        )

        self._proposals[proposal_id] = proposal
        return Ok(proposal)

    def analyze_improvement(
        self, proposal_id: str
    ) -> Result[dict, str]:
        """
        Analyze a proposed improvement.

        Args:
            proposal_id: ID of proposal to analyze

        Returns:
            Result containing analysis
        """
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return Err(f"Proposal not found: {proposal_id}")

        proposal.status = ImprovementStatus.ANALYZING

        # Analyze based on type
        analysis = {
            "proposal_id": proposal_id,
            "type": proposal.improvement_type.value,
            "confidence": proposal.confidence,
            "estimated_impact": proposal.estimated_impact,
            "risk_level": self._assess_risk(proposal),
            "prerequisites": self._check_prerequisites(proposal),
            "recommendation": self._make_recommendation(proposal),
        }

        # Auto-approve high-confidence improvements
        if (
            proposal.confidence >= self.MIN_CONFIDENCE_FOR_AUTO_APPLY
            and analysis["risk_level"] == "low"
        ):
            proposal.status = ImprovementStatus.APPROVED
            analysis["auto_approved"] = True
        else:
            analysis["auto_approved"] = False

        return Ok(analysis)

    def _assess_risk(self, proposal: ImprovementProposal) -> str:
        """Assess risk level of an improvement."""
        # Higher impact = higher risk
        if proposal.estimated_impact > 0.8:
            return "high"
        if proposal.estimated_impact > 0.5:
            return "medium"
        return "low"

    def _check_prerequisites(self, proposal: ImprovementProposal) -> list[str]:
        """Check prerequisites for an improvement."""
        prereqs = []

        if proposal.improvement_type == ImprovementType.CAPABILITY:
            prereqs.append("Run test suite before and after")

        if proposal.improvement_type == ImprovementType.CONFIGURATION:
            prereqs.append("Backup current configuration")

        if proposal.confidence < 0.7:
            prereqs.append("Gather additional evidence")

        return prereqs

    def _make_recommendation(self, proposal: ImprovementProposal) -> str:
        """Make a recommendation for a proposal."""
        if proposal.confidence >= 0.9:
            return "approve"
        if proposal.confidence >= 0.7:
            return "review"
        if proposal.confidence >= 0.5:
            return "gather_evidence"
        return "reject"

    def approve_improvement(self, proposal_id: str) -> Result[bool, str]:
        """Approve an improvement proposal."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return Err(f"Proposal not found: {proposal_id}")

        if proposal.status not in (ImprovementStatus.PROPOSED, ImprovementStatus.ANALYZING):
            return Err(f"Cannot approve proposal in state: {proposal.status.value}")

        proposal.status = ImprovementStatus.APPROVED
        return Ok(True)

    def reject_improvement(self, proposal_id: str, reason: str) -> Result[bool, str]:
        """Reject an improvement proposal."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return Err(f"Proposal not found: {proposal_id}")

        proposal.status = ImprovementStatus.REJECTED
        proposal.rollback_info = {"rejection_reason": reason}
        return Ok(True)

    def apply_improvement(self, proposal_id: str) -> Result[dict, str]:
        """
        Apply an approved improvement.

        Args:
            proposal_id: ID of approved proposal

        Returns:
            Result containing application result
        """
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return Err(f"Proposal not found: {proposal_id}")

        if proposal.status != ImprovementStatus.APPROVED:
            return Err(f"Proposal not approved: {proposal.status.value}")

        proposal.status = ImprovementStatus.APPLYING

        try:
            # Record metrics before
            proposal.metrics_before = self._collect_metrics()

            # Apply the improvement (type-specific logic)
            apply_result = self._apply_by_type(proposal)
            if apply_result.is_err():
                proposal.status = ImprovementStatus.FAILED
                return Err(apply_result.unwrap_err())

            # Record metrics after
            proposal.metrics_after = self._collect_metrics()

            # Mark as applied
            proposal.status = ImprovementStatus.APPLIED
            proposal.applied_at = datetime.now()
            self._applied.append(proposal_id)
            self._save_state()

            return Ok({
                "proposal_id": proposal_id,
                "applied_at": proposal.applied_at.isoformat(),
                "metrics_improved": self._compare_metrics(
                    proposal.metrics_before, proposal.metrics_after
                ),
            })

        except Exception as e:
            proposal.status = ImprovementStatus.FAILED
            return Err(f"Failed to apply: {e}")

    def _apply_by_type(self, proposal: ImprovementProposal) -> Result[bool, str]:
        """Apply improvement based on type."""
        # Simulate application (in real implementation, this would
        # actually apply the changes)

        if proposal.improvement_type == ImprovementType.PATTERN:
            # Store pattern for future use
            return Ok(True)

        if proposal.improvement_type == ImprovementType.CONFIGURATION:
            # Update configuration
            return Ok(True)

        if proposal.improvement_type == ImprovementType.PERFORMANCE:
            # Apply performance optimization
            return Ok(True)

        return Ok(True)

    def _collect_metrics(self) -> dict:
        """Collect current system metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "patterns_learned": len(self._pattern_analyzer._patterns),
            "improvements_applied": len(self._applied),
            "proposals_pending": sum(
                1 for p in self._proposals.values()
                if p.status == ImprovementStatus.PROPOSED
            ),
        }

    def _compare_metrics(self, before: dict, after: dict) -> bool:
        """Compare metrics to determine if improvement was successful."""
        # Simple comparison - in reality would be more sophisticated
        return after.get("improvements_applied", 0) >= before.get("improvements_applied", 0)

    def rollback_improvement(self, proposal_id: str) -> Result[bool, str]:
        """Rollback an applied improvement."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return Err(f"Proposal not found: {proposal_id}")

        if proposal.status != ImprovementStatus.APPLIED:
            return Err(f"Cannot rollback proposal in state: {proposal.status.value}")

        # Perform rollback (type-specific)
        proposal.status = ImprovementStatus.ROLLED_BACK
        self._applied.remove(proposal_id)
        self._save_state()

        return Ok(True)

    def learn_from_outcome(
        self,
        task_type: str,
        success: bool,
        context: dict,
        duration_ms: float = 0,
        error: Optional[str] = None,
    ) -> Result[LearningOutcome, str]:
        """
        Learn from a task outcome.

        Args:
            task_type: Type of task
            success: Whether task succeeded
            context: Task context
            duration_ms: Task duration
            error: Error message if failed

        Returns:
            Result containing learning outcome
        """
        if success:
            return self._pattern_analyzer.analyze_success(
                task_type, context, duration_ms
            )
        else:
            return self._pattern_analyzer.analyze_failure(
                task_type, error or "Unknown error", context
            )

    def suggest_improvements(self) -> list[ImprovementProposal]:
        """
        Suggest improvements based on learned patterns.

        Returns:
            List of suggested improvements
        """
        suggestions = []
        patterns = self._pattern_analyzer.get_high_confidence_patterns()

        for pattern in patterns:
            # Create improvement proposals from high-confidence patterns
            if pattern.success and pattern.occurrences >= 3:
                result = self.propose_improvement(
                    title=f"Optimize {pattern.context.get('task_type', 'task')}",
                    description=f"Pattern observed {pattern.occurrences} times with {pattern.confidence:.1%} confidence",
                    improvement_type=ImprovementType.PATTERN,
                    source="pattern_analyzer",
                    confidence=pattern.confidence,
                    estimated_impact=0.3,
                    evidence=[{"pattern_id": pattern.pattern_id}],
                )
                if result.is_ok():
                    suggestions.append(result.unwrap())

        return suggestions

    def get_proposal(self, proposal_id: str) -> Optional[ImprovementProposal]:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)

    def get_pending_proposals(self) -> list[ImprovementProposal]:
        """Get all pending proposals."""
        return [
            p for p in self._proposals.values()
            if p.status == ImprovementStatus.PROPOSED
        ]

    def get_stats(self) -> dict:
        """Get self-improvement statistics."""
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}

        for proposal in self._proposals.values():
            status = proposal.status.value
            by_status[status] = by_status.get(status, 0) + 1

            imp_type = proposal.improvement_type.value
            by_type[imp_type] = by_type.get(imp_type, 0) + 1

        return {
            "total_proposals": len(self._proposals),
            "applied_count": len(self._applied),
            "by_status": by_status,
            "by_type": by_type,
            "pattern_stats": self._pattern_analyzer.get_stats(),
            "auto_apply_threshold": self.MIN_CONFIDENCE_FOR_AUTO_APPLY,
        }


# Global instance
_engine: Optional[SelfImprovement] = None


def get_engine() -> SelfImprovement:
    """Get the global self-improvement engine."""
    global _engine
    if _engine is None:
        _engine = SelfImprovement()
    return _engine


def main():
    """Command-line interface for self-improvement."""
    import argparse

    parser = argparse.ArgumentParser(description="Self-improvement engine CLI")
    parser.add_argument("--propose", help="Propose improvement with title")
    parser.add_argument("--description", help="Improvement description")
    parser.add_argument("--analyze", help="Analyze proposal by ID")
    parser.add_argument("--apply", help="Apply proposal by ID")
    parser.add_argument("--suggest", action="store_true", help="Suggest improvements")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    args = parser.parse_args()

    engine = get_engine()

    if args.propose:
        result = engine.propose_improvement(
            title=args.propose,
            description=args.description or "No description",
            improvement_type=ImprovementType.QUALITY,
            source="cli",
            confidence=0.7,
            estimated_impact=0.5,
        )

        if result.is_ok():
            proposal = result.unwrap()
            print(f"\n✅ Created proposal: {proposal.id}")
            print(f"   Title: {proposal.title}")
            print(f"   Confidence: {proposal.confidence:.1%}")
        else:
            print(f"\n❌ Failed: {result.unwrap_err()}")

    elif args.analyze:
        result = engine.analyze_improvement(args.analyze)

        if result.is_ok():
            analysis = result.unwrap()
            print(f"\n📊 Analysis for {args.analyze}")
            print("=" * 50)
            print(f"Confidence: {analysis['confidence']:.1%}")
            print(f"Risk level: {analysis['risk_level']}")
            print(f"Recommendation: {analysis['recommendation']}")
            print(f"Auto-approved: {analysis['auto_approved']}")
        else:
            print(f"\n❌ Failed: {result.unwrap_err()}")

    elif args.apply:
        result = engine.apply_improvement(args.apply)

        if result.is_ok():
            application = result.unwrap()
            print(f"\n✅ Applied: {application['proposal_id']}")
            print(f"   At: {application['applied_at']}")
        else:
            print(f"\n❌ Failed: {result.unwrap_err()}")

    elif args.suggest:
        suggestions = engine.suggest_improvements()
        print(f"\n💡 Suggested Improvements ({len(suggestions)})")
        print("=" * 50)
        for s in suggestions:
            print(f"\n{s.id}: {s.title}")
            print(f"   Type: {s.improvement_type.value}")
            print(f"   Confidence: {s.confidence:.1%}")

    elif args.stats:
        stats = engine.get_stats()
        print("\n📊 Self-Improvement Statistics")
        print("=" * 50)
        print(f"Total proposals: {stats['total_proposals']}")
        print(f"Applied: {stats['applied_count']}")
        print(f"Auto-apply threshold: {stats['auto_apply_threshold']:.1%}")
        if stats['by_status']:
            print("\nBy status:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")
        print(f"\nPatterns: {stats['pattern_stats']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
