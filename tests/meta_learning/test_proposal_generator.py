"""
Tests for ProposalGenerator - EPIC 4.2 Component 4.

Constitutional Laws:
- Law #1: TDD is mandatory - these tests written FIRST
- Law #2: Strict typing - no Dict[Any,Any]
- Law #5: Result pattern for error handling
"""

import json
import tempfile
from pathlib import Path

import pytest

from meta_learning.proposal_generator import (
    AgentMetrics,
    ComparisonResult,
    ProposalGenerator,
    ProposalReport,
)


class TestProposalGeneratorBasics:
    """Test basic functionality."""

    def test_init_creates_generator(self):
        """Test ProposalGenerator initialization."""
        generator = ProposalGenerator()
        assert generator is not None

    def test_analyze_results_returns_result_type(self):
        """Test analyze_results returns Result type."""
        # Arrange
        generator = ProposalGenerator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Valid minimal data
            json.dump(
                {
                    "agent_id": "agent_v1",
                    "scores": {"aggregate": 0.85},
                    "duration_s": 10.5,
                    "cost_usd": 0.10,
                },
                f,
            )
            f.write("\n")
            json.dump(
                {
                    "agent_id": "agent_v1",
                    "scores": {"aggregate": 0.90},
                    "duration_s": 11.0,
                    "cost_usd": 0.11,
                },
                f,
            )
            f.write("\n")
            json.dump(
                {
                    "agent_id": "agent_v1",
                    "scores": {"aggregate": 0.88},
                    "duration_s": 10.8,
                    "cost_usd": 0.108,
                },
                f,
            )
            f.write("\n")
            json.dump(
                {
                    "agent_id": "agent_v2",
                    "scores": {"aggregate": 0.75},
                    "duration_s": 12.0,
                    "cost_usd": 0.12,
                },
                f,
            )
            f.write("\n")
            json.dump(
                {
                    "agent_id": "agent_v2",
                    "scores": {"aggregate": 0.78},
                    "duration_s": 11.5,
                    "cost_usd": 0.115,
                },
                f,
            )
            f.write("\n")
            json.dump(
                {
                    "agent_id": "agent_v2",
                    "scores": {"aggregate": 0.77},
                    "duration_s": 11.8,
                    "cost_usd": 0.118,
                },
                f,
            )
            f.write("\n")
            temp_path = Path(f.name)

        # Act
        result = generator.analyze_results(temp_path)

        # Assert
        assert result.is_ok()
        temp_path.unlink()


class TestDataValidation:
    """Test data validation and error handling."""

    def test_analyze_results_fails_on_missing_file(self):
        """Test analyze_results fails gracefully on missing file."""
        # Arrange
        generator = ProposalGenerator()
        missing_path = Path("/nonexistent/file.jsonl")

        # Act
        result = generator.analyze_results(missing_path)

        # Assert
        assert result.is_err()
        assert "not found" in result.unwrap_err().lower()

    def test_analyze_results_fails_on_invalid_json(self):
        """Test analyze_results fails on invalid JSON."""
        # Arrange
        generator = ProposalGenerator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("not valid json\n")
            temp_path = Path(f.name)

        # Act
        result = generator.analyze_results(temp_path)

        # Assert
        assert result.is_err()
        assert "json" in result.unwrap_err().lower()
        temp_path.unlink()

    def test_analyze_results_fails_on_insufficient_samples(self):
        """Test analyze_results fails when < 3 samples per agent."""
        # Arrange
        generator = ProposalGenerator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Only 2 samples for agent_v1
            json.dump(
                {"agent_id": "agent_v1", "scores": {"aggregate": 0.85}, "duration_s": 10, "cost_usd": 0.1},
                f,
            )
            f.write("\n")
            json.dump(
                {"agent_id": "agent_v1", "scores": {"aggregate": 0.90}, "duration_s": 11, "cost_usd": 0.11},
                f,
            )
            f.write("\n")
            # Add agent_v2 with only 2 samples as well
            json.dump(
                {"agent_id": "agent_v2", "scores": {"aggregate": 0.75}, "duration_s": 12, "cost_usd": 0.12},
                f,
            )
            f.write("\n")
            json.dump(
                {"agent_id": "agent_v2", "scores": {"aggregate": 0.78}, "duration_s": 11.5, "cost_usd": 0.115},
                f,
            )
            f.write("\n")
            temp_path = Path(f.name)

        # Act
        result = generator.analyze_results(temp_path)

        # Assert
        assert result.is_err()
        assert "insufficient" in result.unwrap_err().lower() or "need" in result.unwrap_err().lower()
        temp_path.unlink()

    def test_analyze_results_fails_on_missing_required_fields(self):
        """Test analyze_results fails when required fields missing."""
        # Arrange
        generator = ProposalGenerator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Missing 'scores' field
            json.dump({"agent_id": "agent_v1", "duration_s": 10, "cost_usd": 0.1}, f)
            f.write("\n")
            temp_path = Path(f.name)

        # Act
        result = generator.analyze_results(temp_path)

        # Assert
        assert result.is_err()
        temp_path.unlink()


class TestStatisticalAnalysis:
    """Test statistical analysis methods."""

    def test_calculate_statistics_computes_mean(self):
        """Test _calculate_statistics computes mean correctly."""
        # Arrange
        generator = ProposalGenerator()
        results = [
            {"scores": {"aggregate": 0.80}, "duration_s": 10.0, "cost_usd": 0.10},
            {"scores": {"aggregate": 0.90}, "duration_s": 12.0, "cost_usd": 0.12},
            {"scores": {"aggregate": 0.85}, "duration_s": 11.0, "cost_usd": 0.11},
        ]

        # Act
        metrics = generator._calculate_statistics(results, "test_agent")

        # Assert
        assert metrics.mean_score == pytest.approx(0.85, abs=0.01)
        assert metrics.mean_duration == pytest.approx(11.0, abs=0.01)
        assert metrics.mean_cost == pytest.approx(0.11, abs=0.01)

    def test_calculate_statistics_computes_std_dev(self):
        """Test _calculate_statistics computes standard deviation."""
        # Arrange
        generator = ProposalGenerator()
        results = [
            {"scores": {"aggregate": 0.70}, "duration_s": 10.0, "cost_usd": 0.10},
            {"scores": {"aggregate": 0.80}, "duration_s": 12.0, "cost_usd": 0.12},
            {"scores": {"aggregate": 0.90}, "duration_s": 14.0, "cost_usd": 0.14},
        ]

        # Act
        metrics = generator._calculate_statistics(results, "test_agent")

        # Assert
        assert metrics.std_dev_score > 0
        assert metrics.sample_size == 3

    def test_compare_agents_detects_improvement(self):
        """Test _compare_agents detects significant improvement."""
        # Arrange
        generator = ProposalGenerator()
        incumbent = AgentMetrics(
            agent_id="agent_v1",
            mean_score=0.75,
            std_dev_score=0.05,
            mean_duration=12.0,
            mean_cost=0.12,
            sample_size=3,
        )
        challenger = AgentMetrics(
            agent_id="agent_v2",
            mean_score=0.90,
            std_dev_score=0.03,
            mean_duration=10.0,
            mean_cost=0.10,
            sample_size=3,
        )

        # Act
        comparison = generator._compare_agents(challenger, incumbent)

        # Assert
        assert comparison.score_improvement > 0
        assert comparison.duration_improvement < 0  # Faster is negative improvement
        assert comparison.cost_improvement < 0  # Cheaper is negative improvement

    def test_compare_agents_with_scipy_calculates_pvalue(self):
        """Test _compare_agents uses scipy for p-value if available."""
        # Arrange
        generator = ProposalGenerator()
        incumbent = AgentMetrics(
            agent_id="agent_v1",
            mean_score=0.70,
            std_dev_score=0.05,
            mean_duration=12.0,
            mean_cost=0.12,
            sample_size=5,
        )
        challenger = AgentMetrics(
            agent_id="agent_v2",
            mean_score=0.90,
            std_dev_score=0.03,
            mean_duration=10.0,
            mean_cost=0.10,
            sample_size=5,
        )

        # Act
        comparison = generator._compare_agents(challenger, incumbent)

        # Assert - if scipy available, p_value should be calculated
        # Otherwise it will be None
        assert comparison.p_value is None or isinstance(comparison.p_value, float)


class TestRecommendations:
    """Test recommendation logic."""

    def test_determine_recommendation_promotes_significant_improvement(self):
        """Test _determine_recommendation promotes on significant improvement."""
        # Arrange
        generator = ProposalGenerator()
        comparison = ComparisonResult(
            challenger_id="agent_v2",
            incumbent_id="agent_v1",
            score_improvement=0.20,  # 20% improvement
            duration_improvement=-2.0,
            cost_improvement=-0.02,
            p_value=0.01,  # Significant
        )

        # Act
        recommendation = generator._determine_recommendation(comparison)

        # Assert
        assert "promote" in recommendation.lower()

    def test_determine_recommendation_rejects_no_improvement(self):
        """Test _determine_recommendation rejects when no improvement."""
        # Arrange
        generator = ProposalGenerator()
        comparison = ComparisonResult(
            challenger_id="agent_v2",
            incumbent_id="agent_v1",
            score_improvement=-0.05,  # Worse performance
            duration_improvement=2.0,
            cost_improvement=0.02,
            p_value=0.50,
        )

        # Act
        recommendation = generator._determine_recommendation(comparison)

        # Assert
        assert "reject" in recommendation.lower() or "keep" in recommendation.lower()


class TestADRGeneration:
    """Test ADR generation."""

    def test_generate_adr_creates_file(self):
        """Test generate_adr creates ADR file."""
        # Arrange
        generator = ProposalGenerator()
        report = ProposalReport(
            challenger=AgentMetrics(
                agent_id="agent_v2",
                mean_score=0.90,
                std_dev_score=0.03,
                mean_duration=10.0,
                mean_cost=0.10,
                sample_size=5,
            ),
            incumbent=AgentMetrics(
                agent_id="agent_v1",
                mean_score=0.75,
                std_dev_score=0.05,
                mean_duration=12.0,
                mean_cost=0.12,
                sample_size=5,
            ),
            comparison=ComparisonResult(
                challenger_id="agent_v2",
                incumbent_id="agent_v1",
                score_improvement=0.15,
                duration_improvement=-2.0,
                cost_improvement=-0.02,
                p_value=0.01,
            ),
            recommendation="PROMOTE",
        )

        # Act
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate_adr(report, output_dir=Path(tmpdir))

            # Assert
            assert result.is_ok()
            adr_path = result.unwrap()
            assert adr_path.exists()
            assert adr_path.suffix == ".md"

            # Verify content
            content = adr_path.read_text()
            assert "agent_v2" in content
            assert "0.90" in content  # Mean score
            assert "PROMOTE" in content or "promote" in content

    def test_generate_adr_auto_increments_number(self):
        """Test generate_adr auto-increments ADR number."""
        # Arrange
        generator = ProposalGenerator()
        report = ProposalReport(
            challenger=AgentMetrics(
                agent_id="agent_v2",
                mean_score=0.90,
                std_dev_score=0.03,
                mean_duration=10.0,
                mean_cost=0.10,
                sample_size=5,
            ),
            incumbent=AgentMetrics(
                agent_id="agent_v1",
                mean_score=0.75,
                std_dev_score=0.05,
                mean_duration=12.0,
                mean_cost=0.12,
                sample_size=5,
            ),
            comparison=ComparisonResult(
                challenger_id="agent_v2",
                incumbent_id="agent_v1",
                score_improvement=0.15,
                duration_improvement=-2.0,
                cost_improvement=-0.02,
                p_value=0.01,
            ),
            recommendation="PROMOTE",
        )

        # Act
        with tempfile.TemporaryDirectory() as tmpdir:
            result1 = generator.generate_adr(report, output_dir=Path(tmpdir))
            result2 = generator.generate_adr(report, output_dir=Path(tmpdir))

            # Assert
            assert result1.is_ok()
            assert result2.is_ok()

            adr1 = result1.unwrap()
            adr2 = result2.unwrap()

            # Extract numbers from filenames
            num1 = int(adr1.stem.split("-")[1])
            num2 = int(adr2.stem.split("-")[1])

            assert num2 > num1


class TestEndToEnd:
    """Test complete workflow."""

    def test_full_workflow_with_valid_data(self):
        """Test complete workflow from JSONL to ADR."""
        # Arrange
        generator = ProposalGenerator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Agent v1 - lower performance
            for i in range(5):
                json.dump(
                    {
                        "agent_id": "agent_v1",
                        "scores": {"aggregate": 0.70 + i * 0.01},
                        "duration_s": 12.0,
                        "cost_usd": 0.12,
                    },
                    f,
                )
                f.write("\n")

            # Agent v2 - higher performance
            for i in range(5):
                json.dump(
                    {
                        "agent_id": "agent_v2",
                        "scores": {"aggregate": 0.85 + i * 0.01},
                        "duration_s": 10.0,
                        "cost_usd": 0.10,
                    },
                    f,
                )
                f.write("\n")
            jsonl_path = Path(f.name)

        # Act
        analysis_result = generator.analyze_results(jsonl_path)

        # Assert
        assert analysis_result.is_ok()
        report = analysis_result.unwrap()

        # Verify report structure
        assert report.challenger.mean_score > report.incumbent.mean_score
        assert report.comparison.score_improvement > 0

        # Generate ADR
        with tempfile.TemporaryDirectory() as tmpdir:
            adr_result = generator.generate_adr(report, output_dir=Path(tmpdir))
            assert adr_result.is_ok()

            adr_path = adr_result.unwrap()
            assert adr_path.exists()

        # Cleanup
        jsonl_path.unlink()
