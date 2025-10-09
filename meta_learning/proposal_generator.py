"""
ProposalGenerator - EPIC 4.2 Component 4: Statistical Analysis and ADR Generation.

Analyzes A/B test results and generates ADR proposals for agent promotions.

Constitutional Compliance:
- Article I: Complete context - validates ALL data before analysis
- Article II: 100% verification - uses statistical tests when available
- Law #2: Strict typing - Pydantic models, no Dict[Any,Any]
- Law #5: Result pattern for all error handling
- Law #8: Focused functions <50 lines each
"""

import json
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result

# Try to import scipy for statistical tests
try:
    from scipy import stats  # type: ignore

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class AgentMetrics(BaseModel):
    """
    Statistical metrics for agent performance.

    Law #2: Strict typing with Pydantic, no Dict[Any,Any]
    """

    agent_id: str
    mean_score: float = Field(ge=0.0, le=1.0)
    std_dev_score: float = Field(ge=0.0)
    mean_duration: float = Field(gt=0.0)
    mean_cost: float = Field(ge=0.0)
    sample_size: int = Field(ge=3)
    raw_scores: list[float] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    """
    Comparison results between challenger and incumbent.

    Law #2: Explicit types for all fields
    """

    challenger_id: str
    incumbent_id: str
    score_improvement: float  # Positive = challenger better
    duration_improvement: float  # Negative = challenger faster
    cost_improvement: float  # Negative = challenger cheaper
    p_value: float | None = None  # Statistical significance (if scipy available)


class ProposalReport(BaseModel):
    """
    Complete proposal report for ADR generation.

    Law #2: Strict typing throughout
    """

    challenger: AgentMetrics
    incumbent: AgentMetrics
    comparison: ComparisonResult
    recommendation: str  # "PROMOTE", "REJECT", "INCONCLUSIVE"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class BenchmarkResult:
    """Single benchmark result from JSONL."""

    agent_id: str
    score: float
    duration_s: float
    cost_usd: float


class ProposalGenerator:
    """
    Generate ADR proposals based on A/B test statistical analysis.

    Constitutional compliance:
    - Article I: Complete context validation before processing
    - Article II: Statistical verification when possible
    - Law #5: Result pattern for all fallible operations
    """

    def __init__(self, min_samples: int = 3, significance_level: float = 0.05):
        """
        Initialize ProposalGenerator.

        Args:
            min_samples: Minimum samples per agent (default 3)
            significance_level: P-value threshold for significance (default 0.05)
        """
        self.min_samples = min_samples
        self.significance_level = significance_level

    def analyze_results(self, results_file: Path) -> Result[ProposalReport, str]:
        """
        Analyze A/B test results from JSONL file.

        Law #5: Result pattern for error handling
        Article I: Complete context - validates ALL data

        Args:
            results_file: Path to JSONL results file

        Returns:
            Result with ProposalReport or error message
        """
        # Validate file exists (Article I: Complete context)
        if not results_file.exists():
            return Err(f"Results file not found: {results_file}")

        # Load and parse JSONL data
        parse_result = self._parse_jsonl(results_file)
        if parse_result.is_err():
            return Err(parse_result.unwrap_err())

        results = parse_result.unwrap()

        # Group by agent_id
        agent_results = self._group_by_agent(results)

        # Validate minimum samples (Article I: Complete context)
        validation_result = self._validate_samples(agent_results)
        if validation_result.is_err():
            return Err(validation_result.unwrap_err())

        # Identify challenger and incumbent (highest vs second-highest mean)
        ranking_result = self._rank_agents(agent_results)
        if ranking_result.is_err():
            return Err(ranking_result.unwrap_err())

        challenger_id, incumbent_id = ranking_result.unwrap()

        # Calculate statistics for each agent
        challenger_metrics = self._calculate_statistics(agent_results[challenger_id], challenger_id)
        incumbent_metrics = self._calculate_statistics(agent_results[incumbent_id], incumbent_id)

        # Compare agents
        comparison = self._compare_agents(challenger_metrics, incumbent_metrics)

        # Determine recommendation
        recommendation = self._determine_recommendation(comparison)

        return Ok(
            ProposalReport(
                challenger=challenger_metrics,
                incumbent=incumbent_metrics,
                comparison=comparison,
                recommendation=recommendation,
            )
        )

    def _parse_jsonl(self, file_path: Path) -> Result[list[BenchmarkResult], str]:
        """
        Parse JSONL file into BenchmarkResult objects.

        Law #8: Focused function <50 lines
        """
        results = []

        try:
            with open(file_path) as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as e:
                        return Err(f"Invalid JSON on line {line_num}: {e}")

                    # Validate required fields
                    if "agent_id" not in data:
                        return Err(f"Missing 'agent_id' on line {line_num}")
                    if "scores" not in data or "aggregate" not in data.get("scores", {}):
                        return Err(f"Missing 'scores.aggregate' on line {line_num}")

                    results.append(
                        BenchmarkResult(
                            agent_id=str(data["agent_id"]),
                            score=float(data["scores"]["aggregate"]),
                            duration_s=float(data.get("duration_s", 0.0)),
                            cost_usd=float(data.get("cost_usd", 0.0)),
                        )
                    )

        except OSError as e:
            return Err(f"Failed to read file: {e}")

        if not results:
            return Err("No valid results found in file")

        return Ok(results)

    def _group_by_agent(self, results: list[BenchmarkResult]) -> dict[str, list[dict[str, object]]]:
        """
        Group results by agent_id.

        Law #8: Single responsibility
        """
        grouped: dict[str, list[dict[str, object]]] = {}

        for result in results:
            if result.agent_id not in grouped:
                grouped[result.agent_id] = []

            grouped[result.agent_id].append(
                {
                    "scores": {"aggregate": result.score},
                    "duration_s": result.duration_s,
                    "cost_usd": result.cost_usd,
                }
            )

        return grouped

    def _validate_samples(
        self, agent_results: dict[str, list[dict[str, object]]]
    ) -> Result[None, str]:
        """
        Validate minimum sample size per agent.

        Article I: Complete context validation
        """
        if len(agent_results) < 2:
            return Err(f"Need at least 2 agents for comparison, found {len(agent_results)}")

        for agent_id, results in agent_results.items():
            if len(results) < self.min_samples:
                return Err(
                    f"Insufficient samples for {agent_id}: "
                    f"need {self.min_samples}, got {len(results)}"
                )

        return Ok(None)

    def _rank_agents(
        self, agent_results: dict[str, list[dict[str, object]]]
    ) -> Result[tuple[str, str], str]:
        """
        Rank agents by mean score to identify challenger and incumbent.

        Law #8: Focused function
        """
        # Calculate mean scores
        mean_scores = {}
        for agent_id, results in agent_results.items():
            scores = []
            for r in results:
                scores_dict = r.get("scores")
                if isinstance(scores_dict, dict):
                    agg = scores_dict.get("aggregate")
                    if isinstance(agg, (int, float)):
                        scores.append(float(agg))
            mean_scores[agent_id] = statistics.mean(scores) if scores else 0.0

        # Sort by mean score (descending)
        sorted_agents = sorted(mean_scores.items(), key=lambda x: x[1], reverse=True)

        if len(sorted_agents) < 2:
            return Err("Need at least 2 agents for comparison")

        # Challenger = highest, incumbent = second highest
        challenger_id = sorted_agents[0][0]
        incumbent_id = sorted_agents[1][0]

        return Ok((challenger_id, incumbent_id))

    def _calculate_statistics(
        self, results: list[dict[str, object]], agent_id: str
    ) -> AgentMetrics:
        """
        Calculate statistical metrics for agent results.

        Article II: Statistical verification
        Law #8: Single responsibility <50 lines

        Args:
            results: List of result dictionaries
            agent_id: Agent identifier
        """
        # Extract values
        scores = []
        durations = []
        costs = []

        for r in results:
            # Extract score
            scores_dict = r.get("scores")
            if isinstance(scores_dict, dict):
                agg = scores_dict.get("aggregate")
                if isinstance(agg, (int, float)):
                    scores.append(float(agg))

            # Extract duration
            dur = r.get("duration_s")
            if isinstance(dur, (int, float)):
                durations.append(float(dur))

            # Extract cost
            cost = r.get("cost_usd")
            if isinstance(cost, (int, float)):
                costs.append(float(cost))

        # Calculate statistics
        mean_score = statistics.mean(scores) if scores else 0.0
        std_dev_score = statistics.stdev(scores) if len(scores) > 1 else 0.0
        mean_duration = statistics.mean(durations) if durations else 0.0
        mean_cost = statistics.mean(costs) if costs else 0.0

        return AgentMetrics(
            agent_id=agent_id,
            mean_score=mean_score,
            std_dev_score=std_dev_score,
            mean_duration=mean_duration,
            mean_cost=mean_cost,
            sample_size=len(scores),
            raw_scores=scores,
        )

    def _compare_agents(
        self, challenger: AgentMetrics, incumbent: AgentMetrics
    ) -> ComparisonResult:
        """
        Compare challenger vs incumbent with statistical tests.

        Article II: Statistical verification when scipy available
        Law #8: Focused comparison logic
        """
        # Calculate improvements (positive = challenger better)
        score_improvement = challenger.mean_score - incumbent.mean_score
        duration_improvement = (
            challenger.mean_duration - incumbent.mean_duration
        )  # Negative = faster
        cost_improvement = challenger.mean_cost - incumbent.mean_cost  # Negative = cheaper

        # Calculate p-value if scipy available (Article II: Verification)
        p_value = None
        if HAS_SCIPY and len(challenger.raw_scores) >= 3 and len(incumbent.raw_scores) >= 3:
            # Two-sample t-test
            t_stat, p_val = stats.ttest_ind(challenger.raw_scores, incumbent.raw_scores)
            p_value = float(p_val)

        return ComparisonResult(
            challenger_id=challenger.agent_id,
            incumbent_id=incumbent.agent_id,
            score_improvement=score_improvement,
            duration_improvement=duration_improvement,
            cost_improvement=cost_improvement,
            p_value=p_value,
        )

    def _determine_recommendation(self, comparison: ComparisonResult) -> str:
        """
        Determine recommendation based on comparison results.

        Logic:
        - PROMOTE: Significant score improvement + statistical significance
        - REJECT: No improvement or worse performance
        - INCONCLUSIVE: Marginal improvement without significance
        """
        # Thresholds
        min_score_improvement = 0.05  # 5% minimum
        max_acceptable_pvalue = self.significance_level

        # Check score improvement
        if comparison.score_improvement < min_score_improvement:
            return "REJECT"

        # Check statistical significance if available
        if comparison.p_value is not None:
            if comparison.p_value <= max_acceptable_pvalue:
                return "PROMOTE"
            else:
                return "INCONCLUSIVE"

        # Without scipy, use heuristic: >10% improvement = promote
        if comparison.score_improvement >= 0.10:
            return "PROMOTE"

        return "INCONCLUSIVE"

    def generate_adr(
        self, report: ProposalReport, output_dir: Path | None = None
    ) -> Result[Path, str]:
        """
        Generate ADR document from proposal report.

        Law #5: Result pattern for file operations
        Law #8: Focused ADR generation

        Args:
            report: ProposalReport with analysis results
            output_dir: Output directory (default: docs/adr/)

        Returns:
            Result with Path to generated ADR or error
        """
        if output_dir is None:
            output_dir = Path("docs/adr")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find next ADR number
        next_number = self._get_next_adr_number(output_dir)

        # Generate filename
        slug = f"agent-promotion-{report.challenger.agent_id}"
        filename = f"ADR-{next_number:03d}-{slug}.md"
        adr_path = output_dir / filename

        # Generate content
        content = self._generate_adr_content(report, next_number)

        # Write file
        try:
            adr_path.write_text(content)
        except OSError as e:
            return Err(f"Failed to write ADR: {e}")

        return Ok(adr_path)

    def _get_next_adr_number(self, output_dir: Path) -> int:
        """Get next ADR number by scanning existing files."""
        existing = list(output_dir.glob("ADR-*.md"))
        if not existing:
            return 1

        # Extract numbers
        numbers = []
        for adr_file in existing:
            try:
                # Format: ADR-XXX-slug.md
                parts = adr_file.stem.split("-")
                if len(parts) >= 2:
                    numbers.append(int(parts[1]))
            except (ValueError, IndexError):
                continue

        return max(numbers) + 1 if numbers else 1

    def _generate_adr_content(self, report: ProposalReport, adr_number: int) -> str:
        """
        Generate ADR markdown content.

        Law #8: Template-based generation <50 lines
        """
        status = "Proposed" if report.recommendation != "REJECT" else "Rejected"

        # Format statistics
        challenger_stats = (
            f"- Mean Score: {report.challenger.mean_score:.3f} "
            f"(±{report.challenger.std_dev_score:.3f})\n"
            f"- Mean Duration: {report.challenger.mean_duration:.2f}s\n"
            f"- Mean Cost: ${report.challenger.mean_cost:.4f}\n"
            f"- Sample Size: {report.challenger.sample_size}"
        )

        incumbent_stats = (
            f"- Mean Score: {report.incumbent.mean_score:.3f} "
            f"(±{report.incumbent.std_dev_score:.3f})\n"
            f"- Mean Duration: {report.incumbent.mean_duration:.2f}s\n"
            f"- Mean Cost: ${report.incumbent.mean_cost:.4f}\n"
            f"- Sample Size: {report.incumbent.sample_size}"
        )

        # Statistical significance
        p_value_text = (
            f"p-value: {report.comparison.p_value:.4f}"
            if report.comparison.p_value is not None
            else "Statistical test not available (scipy not installed)"
        )

        # Implementation steps (avoid f-string backslash issue in Python 3.11)
        if report.recommendation == "PROMOTE":
            implementation_steps = (
                f"1. Update agent registry to promote {report.challenger.agent_id}\n"
                "2. Deploy to production\n"
                "3. Monitor metrics for 48 hours\n"
                "4. Rollback if regression detected"
            )
        else:
            implementation_steps = "No implementation required - reject proposal"

        return f"""# ADR-{adr_number:03d}: Agent Promotion - {report.challenger.agent_id}

## Status
**{status}** - {datetime.utcnow().strftime("%Y-%m-%d")}

## Context
A/B testing framework evaluated challenger agent `{report.challenger.agent_id}` against incumbent `{report.incumbent.agent_id}`.

### Challenger Performance ({report.challenger.agent_id})
{challenger_stats}

### Incumbent Performance ({report.incumbent.agent_id})
{incumbent_stats}

## Decision
**Recommendation: {report.recommendation}**

### Statistical Analysis
- Score Improvement: {report.comparison.score_improvement:+.3f} ({report.comparison.score_improvement * 100:+.1f}%)
- Duration Change: {report.comparison.duration_improvement:+.2f}s
- Cost Change: ${report.comparison.cost_improvement:+.4f}
- {p_value_text}

### Rationale
{"The challenger demonstrates statistically significant improvement in aggregate score metrics." if report.recommendation == "PROMOTE" else "Insufficient evidence to warrant promotion. " + ("Score improvement below threshold." if report.comparison.score_improvement < 0.05 else "Statistical significance not established.")}

## Consequences

### If Promoted
- **Positive**: Higher quality outputs, {"faster execution, " if report.comparison.duration_improvement < 0 else ""}{"lower costs" if report.comparison.cost_improvement < 0 else ""}
- **Negative**: {"Increased costs" if report.comparison.cost_improvement > 0 else "Minimal risks identified"}

### If Rejected
- Maintain current performance level
- Continue monitoring for future improvements

## Implementation
{implementation_steps}

## References
- A/B Testing Framework: EPIC 4.2
- Benchmark Results: Generated {report.timestamp}
- Article IV: Continuous Learning (Constitution)

## Review
- Generated by: ProposalGenerator
- Timestamp: {report.timestamp}
- Constitutional Compliance: Articles I, II, IV ✓

---

*"Data-driven evolution through rigorous statistical validation."*
"""
