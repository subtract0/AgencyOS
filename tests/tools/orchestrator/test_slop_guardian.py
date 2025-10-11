"""
Tests for Slop Immunity Protocol - Constitutional quality gate.

Constitutional compliance:
- Article I: Complete context (all rubric dimensions tested)
- Article II: 100% verification (all threshold branches tested)
- Article III: Automated enforcement (no bypass mechanisms)
- Article IV: VectorStore integration (REVISE/REJECT patterns stored)
"""

import json
import os
from unittest.mock import MagicMock, Mock, patch

import openai
import pytest

from tools.orchestrator.slop_guardian import (
    SlopDetected,
    SlopGuardian,
    SlopVerdict,
    VerdictStatus,
    enforce_slop_immunity,
    log_slop_evaluation,
)


class TestSlopVerdict:
    """Test SlopVerdict Pydantic model."""

    def test_verdict_status_auto_computed_accept(self):
        """Test status auto-computed as ACCEPT when score >= 3.5."""
        verdict = SlopVerdict(
            score=4.0,
            reasons=[],
            top_fixes=[],
            dimension_scores={"clarity": 4.0, "measurability": 4.0, "completeness": 4.0, "actionability": 4.0},
        )

        assert verdict.status == VerdictStatus.ACCEPT

    def test_verdict_status_auto_computed_revise(self):
        """Test status auto-computed as REVISE when 2.0 <= score < 3.5."""
        verdict = SlopVerdict(
            score=2.8,
            reasons=["Vague outcome", "No acceptance criteria"],
            top_fixes=["Specify measurable success metrics", "Define concrete deliverables"],
            dimension_scores={"clarity": 2.5, "measurability": 2.0, "completeness": 3.5, "actionability": 3.2},
        )

        assert verdict.status == VerdictStatus.REVISE

    def test_verdict_status_auto_computed_reject(self):
        """Test status auto-computed as REJECT when score < 2.0."""
        verdict = SlopVerdict(
            score=1.5,
            reasons=["Completely vague", "No structure", "No measurable criteria"],
            top_fixes=["Start with clear goals", "Define acceptance criteria"],
            dimension_scores={"clarity": 1.0, "measurability": 1.5, "completeness": 2.0, "actionability": 1.5},
        )

        assert verdict.status == VerdictStatus.REJECT

    def test_verdict_threshold_boundary_accept(self):
        """Test boundary: score 3.5 exactly → ACCEPT."""
        verdict = SlopVerdict(
            score=3.5,
            reasons=[],
            top_fixes=[],
            dimension_scores={"clarity": 3.5, "measurability": 3.5, "completeness": 3.5, "actionability": 3.5},
        )

        assert verdict.status == VerdictStatus.ACCEPT

    def test_verdict_threshold_boundary_revise(self):
        """Test boundary: score 3.4 → REVISE."""
        verdict = SlopVerdict(
            score=3.4,
            reasons=["Minor vagueness"],
            top_fixes=["Clarify edge cases"],
            dimension_scores={"clarity": 3.4, "measurability": 3.4, "completeness": 3.4, "actionability": 3.4},
        )

        assert verdict.status == VerdictStatus.REVISE

    def test_verdict_threshold_boundary_reject(self):
        """Test boundary: score 2.0 exactly → REVISE (not REJECT)."""
        verdict = SlopVerdict(
            score=2.0,
            reasons=["Vague"],
            top_fixes=["Clarify"],
            dimension_scores={"clarity": 2.0, "measurability": 2.0, "completeness": 2.0, "actionability": 2.0},
        )

        assert verdict.status == VerdictStatus.REVISE

    def test_verdict_threshold_boundary_reject_below_2(self):
        """Test boundary: score 1.9 → REJECT."""
        verdict = SlopVerdict(
            score=1.9,
            reasons=["Critically vague"],
            top_fixes=["Rewrite completely"],
            dimension_scores={"clarity": 1.9, "measurability": 1.9, "completeness": 1.9, "actionability": 1.9},
        )

        assert verdict.status == VerdictStatus.REJECT


class TestSlopDetected:
    """Test SlopDetected exception."""

    def test_exception_message_format(self):
        """Test exception message includes score, status, reasons, and top fixes."""
        verdict = SlopVerdict(
            score=2.8,
            reasons=["Vague outcome", "No acceptance criteria"],
            top_fixes=["Specify measurable success metrics", "Define concrete deliverables"],
            dimension_scores={"clarity": 2.5, "measurability": 2.0, "completeness": 3.5, "actionability": 3.2},
        )

        exception = SlopDetected(verdict, "Make the system better")

        assert "score 2.8/5.0" in str(exception)
        assert "Status: REVISE" in str(exception)
        assert "Vague outcome" in str(exception)
        assert "No acceptance criteria" in str(exception)
        assert "Specify measurable success metrics" in str(exception)

    def test_exception_stores_verdict_and_original_text(self):
        """Test exception stores verdict and original text."""
        verdict = SlopVerdict(
            score=1.5,
            reasons=["Critically vague"],
            top_fixes=["Rewrite completely"],
            dimension_scores={"clarity": 1.0, "measurability": 1.5, "completeness": 2.0, "actionability": 1.5},
        )

        exception = SlopDetected(verdict, "Make it work")

        assert exception.verdict == verdict
        assert exception.original_text == "Make it work"


class TestSlopGuardian:
    """Test SlopGuardian core evaluation logic."""

    @patch("openai.OpenAI")
    def test_evaluate_accept_verdict(self, mock_openai):
        """Test evaluation returns ACCEPT verdict for high-quality spec."""
        # Mock GPT-5 response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "dimension_scores": {
                                "clarity": 4.5,
                                "measurability": 4.0,
                                "completeness": 4.2,
                                "actionability": 4.3,
                            },
                            "reasons": [],
                            "top_fixes": [],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        guardian = SlopGuardian()
        result = guardian.evaluate("Implement JWT authentication with RSA-256, 15-minute token expiry, and refresh token rotation")

        assert result.is_ok()
        verdict = result.unwrap()
        assert verdict.status == VerdictStatus.ACCEPT
        assert verdict.score >= 3.5

    @patch("openai.OpenAI")
    def test_evaluate_revise_verdict(self, mock_openai):
        """Test evaluation returns REVISE verdict for vague spec."""
        # Mock GPT-5 response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "dimension_scores": {
                                "clarity": 2.5,
                                "measurability": 2.0,
                                "completeness": 3.5,
                                "actionability": 3.2,
                            },
                            "reasons": ["Vague outcome", "No acceptance criteria"],
                            "top_fixes": ["Specify measurable success metrics", "Define concrete deliverables"],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        guardian = SlopGuardian()
        result = guardian.evaluate("Make the system better")

        assert result.is_ok()
        verdict = result.unwrap()
        assert verdict.status == VerdictStatus.REVISE
        assert 2.0 <= verdict.score < 3.5

    @patch("openai.OpenAI")
    def test_evaluate_reject_verdict(self, mock_openai):
        """Test evaluation returns REJECT verdict for critically vague spec."""
        # Mock GPT-5 response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "dimension_scores": {
                                "clarity": 1.0,
                                "measurability": 1.5,
                                "completeness": 2.0,
                                "actionability": 1.5,
                            },
                            "reasons": ["Completely vague", "No structure", "No measurable criteria"],
                            "top_fixes": ["Start with clear goals", "Define acceptance criteria"],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        guardian = SlopGuardian()
        result = guardian.evaluate("Do stuff")

        assert result.is_ok()
        verdict = result.unwrap()
        assert verdict.status == VerdictStatus.REJECT
        assert verdict.score < 2.0

    @patch("openai.OpenAI")
    def test_weighted_score_calculation(self, mock_openai):
        """Test weighted score calculation (30% clarity, 30% measurability, 20% completeness, 20% actionability)."""
        # Mock GPT-5 response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "dimension_scores": {
                                "clarity": 3.0,  # 30% weight
                                "measurability": 4.0,  # 30% weight
                                "completeness": 3.0,  # 20% weight
                                "actionability": 4.0,  # 20% weight
                            },
                            "reasons": [],
                            "top_fixes": [],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        guardian = SlopGuardian()
        result = guardian.evaluate("Test spec")

        assert result.is_ok()
        verdict = result.unwrap()

        # Expected score: (3.0 * 0.3) + (4.0 * 0.3) + (3.0 * 0.2) + (4.0 * 0.2) = 0.9 + 1.2 + 0.6 + 0.8 = 3.5
        assert verdict.score == 3.5

    @patch("openai.OpenAI")
    @patch("time.sleep")
    def test_retry_on_api_error(self, mock_sleep, mock_openai):
        """Test retry logic on API error (Article I: exponential backoff)."""
        # Mock GPT-5 client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # First 2 calls fail, 3rd succeeds
        mock_client.chat.completions.create.side_effect = [
            openai.APIError(message="Timeout", request=Mock(), body={}),
            openai.APIError(message="Timeout", request=Mock(), body={}),
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=json.dumps(
                                {
                                    "dimension_scores": {
                                        "clarity": 4.0,
                                        "measurability": 4.0,
                                        "completeness": 4.0,
                                        "actionability": 4.0,
                                    },
                                    "reasons": [],
                                    "top_fixes": [],
                                }
                            )
                        )
                    )
                ]
            ),
        ]

        guardian = SlopGuardian()
        result = guardian.evaluate("Test spec")

        assert result.is_ok()
        assert mock_client.chat.completions.create.call_count == 3

    @patch("openai.OpenAI")
    @patch("time.sleep")
    def test_error_after_max_retries(self, mock_sleep, mock_openai):
        """Test error returned after 3 retry attempts."""
        # Mock GPT-5 client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # All 3 calls fail
        mock_client.chat.completions.create.side_effect = openai.APIError(message="Timeout", request=Mock(), body={})

        guardian = SlopGuardian()
        result = guardian.evaluate("Test spec")

        assert result.is_err()
        assert "LLM error after 3 attempts" in result.unwrap_err()
        assert mock_client.chat.completions.create.call_count == 3


class TestEnforceSlopImmunity:
    """Test enforce_slop_immunity integration function."""

    @patch("openai.OpenAI")
    def test_enforce_accept_returns_ok(self, mock_openai):
        """Test enforce returns Ok for ACCEPT verdict."""
        # Mock GPT-5 response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "dimension_scores": {
                                "clarity": 4.0,
                                "measurability": 4.0,
                                "completeness": 4.0,
                                "actionability": 4.0,
                            },
                            "reasons": [],
                            "top_fixes": [],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        guardian = SlopGuardian()
        result = enforce_slop_immunity("Good spec", guardian, stage="pre_planning")

        assert result.is_ok()
        verdict = result.unwrap()
        assert verdict.status == VerdictStatus.ACCEPT

    @patch("openai.OpenAI")
    def test_enforce_revise_returns_err_with_exception(self, mock_openai):
        """Test enforce returns Err with SlopDetected for REVISE verdict."""
        # Mock GPT-5 response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "dimension_scores": {
                                "clarity": 2.5,
                                "measurability": 2.0,
                                "completeness": 3.5,
                                "actionability": 3.2,
                            },
                            "reasons": ["Vague outcome"],
                            "top_fixes": ["Clarify"],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        guardian = SlopGuardian()
        result = enforce_slop_immunity("Vague spec", guardian, stage="pre_planning")

        assert result.is_err()
        exception = result.unwrap_err()
        assert isinstance(exception, SlopDetected)
        assert exception.verdict.status == VerdictStatus.REVISE

    @patch("openai.OpenAI")
    def test_enforce_reject_returns_err_with_exception(self, mock_openai):
        """Test enforce returns Err with SlopDetected for REJECT verdict."""
        # Mock GPT-5 response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "dimension_scores": {
                                "clarity": 1.0,
                                "measurability": 1.5,
                                "completeness": 2.0,
                                "actionability": 1.5,
                            },
                            "reasons": ["Critically vague"],
                            "top_fixes": ["Rewrite"],
                        }
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        guardian = SlopGuardian()
        result = enforce_slop_immunity("Bad spec", guardian, stage="pre_planning")

        assert result.is_err()
        exception = result.unwrap_err()
        assert isinstance(exception, SlopDetected)
        assert exception.verdict.status == VerdictStatus.REJECT


class TestAuditLogging:
    """Test audit logging functionality."""

    def test_log_slop_evaluation_creates_audit_entry(self, tmp_path, monkeypatch):
        """Test audit log entry created with HMAC signature."""
        # Override AGENCY_DATA_DIR to use temp directory
        monkeypatch.setenv("AGENCY_DATA_DIR", str(tmp_path))

        # Re-import to pick up new env var
        import importlib
        import utils.audit_helpers
        importlib.reload(utils.audit_helpers)
        import tools.orchestrator.slop_guardian
        importlib.reload(tools.orchestrator.slop_guardian)

        from tools.orchestrator.slop_guardian import log_slop_evaluation, SlopVerdict

        verdict = SlopVerdict(
            score=2.8,
            reasons=["Vague"],
            top_fixes=["Clarify"],
            dimension_scores={"clarity": 2.5, "measurability": 2.0, "completeness": 3.5, "actionability": 3.2},
        )

        log_slop_evaluation(verdict, "Test spec", stage="pre_planning", attempt=0)

        # Verify audit file created
        audit_file = tmp_path / "audit" / "slop_immunity" / "slop_evaluations.jsonl"
        assert audit_file.exists()

        # Verify audit entry format
        with open(audit_file, "r") as f:
            entry = json.loads(f.read())

        assert "timestamp" in entry
        assert entry["stage"] == "pre_planning"
        assert entry["attempt"] == 0
        assert entry["verdict"]["score"] == 2.8
        assert "signature" in entry
        assert "original_text_hash" in entry

    def test_log_slop_evaluation_appends_to_existing_log(self, tmp_path, monkeypatch):
        """Test audit logging appends to existing file."""
        # Override AGENCY_DATA_DIR to use temp directory
        monkeypatch.setenv("AGENCY_DATA_DIR", str(tmp_path))

        # Re-import to pick up new env var
        import importlib
        import utils.audit_helpers
        importlib.reload(utils.audit_helpers)
        import tools.orchestrator.slop_guardian
        importlib.reload(tools.orchestrator.slop_guardian)

        from tools.orchestrator.slop_guardian import log_slop_evaluation, SlopVerdict

        verdict1 = SlopVerdict(
            score=2.8,
            reasons=["Vague"],
            top_fixes=["Clarify"],
            dimension_scores={"clarity": 2.5, "measurability": 2.0, "completeness": 3.5, "actionability": 3.2},
        )

        verdict2 = SlopVerdict(
            score=4.0,
            reasons=[],
            top_fixes=[],
            dimension_scores={"clarity": 4.0, "measurability": 4.0, "completeness": 4.0, "actionability": 4.0},
        )

        log_slop_evaluation(verdict1, "Spec 1", stage="pre_planning", attempt=0)
        log_slop_evaluation(verdict2, "Spec 2", stage="graph_validation", attempt=0)

        # Verify 2 entries in log
        audit_file = tmp_path / "audit" / "slop_immunity" / "slop_evaluations.jsonl"
        with open(audit_file, "r") as f:
            lines = f.readlines()

        assert len(lines) == 2
        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])

        assert entry1["verdict"]["score"] == 2.8
        assert entry2["verdict"]["score"] == 4.0
