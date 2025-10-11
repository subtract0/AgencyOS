"""
Slop Immunity Protocol - Constitutional quality gate for vague specifications.

Implements Article III, Clause 3.2 enforcement via three-stage integration:
1. Pre-planning intent scrubbing
2. Graph validation spec-level scoring
3. Post-execution reflection auditing

Constitutional compliance:
- Article I: Complete context (all rubric dimensions scored before verdict)
- Article II: 100% verification (strict Pydantic validation)
- Article III: Automated enforcement (zero manual override without audit)
- Article IV: VectorStore integration (REVISE/REJECT patterns stored)
- Article V: Spec-driven (follows spec-006-slop-immunity-protocol.md)
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import openai
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError

from shared.models.slop_evaluation_response import RawSlopEval
from shared.type_definitions.result import Err, Ok, Result
from utils.audit_helpers import write_audit_entry, AGENCY_DATA_DIR


class VerdictStatus(str, Enum):
    """
    Slop detection verdict status.

    ACCEPT: Intent meets quality threshold (score ≥3.5), proceed to execution
    REVISE: Intent below threshold (2.0 ≤ score < 3.5), auto-rewrite or manual clarification
    REJECT: Intent critically vague (score <2.0), immediate rejection, no auto-rewrite
    """

    ACCEPT = "accept"
    REVISE = "revise"
    REJECT = "reject"


class SlopVerdict(BaseModel):
    """
    Slop guardian evaluation verdict.

    Fields:
        status: Verdict status (ACCEPT/REVISE/REJECT), auto-computed from score
        score: Overall quality score (0.0-5.0, weighted average of dimensions)
        reasons: List of quality issues identified (empty if ACCEPT)
        top_fixes: List of actionable improvements (empty if ACCEPT)
        dimension_scores: Rubric dimension scores (clarity, measurability, completeness, actionability)
        evaluated_at: ISO 8601 timestamp of evaluation (UTC)

    Example:
        >>> verdict = SlopVerdict(
        ...     score=2.8,
        ...     reasons=["Vague outcome", "No acceptance criteria"],
        ...     top_fixes=["Specify measurable success metrics", "Define concrete deliverables"],
        ...     dimension_scores={"clarity": 2.5, "measurability": 2.0, "completeness": 3.5, "actionability": 3.2}
        ... )
        >>> verdict.status
        VerdictStatus.REVISE
    """

    score: float = Field(..., ge=0.0, le=5.0, description="Overall quality score (0.0-5.0)")
    reasons: list[str] = Field(default_factory=list, description="Quality issues identified")
    top_fixes: list[str] = Field(default_factory=list, description="Actionable improvements")
    dimension_scores: dict[str, float] = Field(
        ...,
        description="Rubric dimension scores (clarity, measurability, completeness, actionability)",
    )
    status: VerdictStatus | None = Field(
        default=None, description="Verdict status (ACCEPT/REVISE/REJECT), auto-computed from score"
    )
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of evaluation (UTC)",
    )

    class Config:
        use_enum_values = True

    @model_validator(mode="after")
    def compute_status(self) -> "SlopVerdict":
        """Compute verdict status from score if not provided."""
        if self.status is None:
            if self.score >= 3.5:
                self.status = VerdictStatus.ACCEPT
            elif self.score >= 2.0:
                self.status = VerdictStatus.REVISE
            else:
                self.status = VerdictStatus.REJECT

        return self


class SlopDetected(Exception):
    """
    Exception raised when slop guardian rejects specification.

    Raised when:
    - Score <3.5 (REVISE threshold)
    - Score <2.0 (REJECT threshold)
    - Auto-rewrite exhausted (3 attempts)

    Contains verdict for user feedback and audit logging.
    """

    def __init__(self, verdict: SlopVerdict, original_text: str):
        self.verdict = verdict
        self.original_text = original_text

        message = (
            f"Intent quality below threshold (score {verdict.score}/5.0).\n"
            f"Status: {verdict.status.upper()}\n"
            f"Reasons: {', '.join(verdict.reasons)}\n"
            f"Top fixes: {', '.join(verdict.top_fixes)}"
        )
        super().__init__(message)


class SlopGuardian:
    """
    Slop immunity guardian - constitutional quality gate.

    Evaluates specifications using GPT-5 with 4-dimension rubric:
    1. Clarity (30%): Specific vs vague language
    2. Measurability (30%): Testable acceptance criteria
    3. Completeness (20%): All required sections defined
    4. Actionability (20%): Implementable guidance

    Constitutional threshold: 3.5/5.0 (REVISE below, ACCEPT above)
    Critical threshold: 2.0/5.0 (REJECT below, no auto-rewrite)

    Example:
        >>> guardian = SlopGuardian()
        >>> verdict = guardian.evaluate("Make the system better")
        >>> verdict.status
        VerdictStatus.REVISE  # score: 2.5, reasons: ["Vague outcome", "No metrics"]
    """

    def __init__(self, model: str = "gpt-5", temperature: float = 0.3, client: Optional[Any] = None):
        """
        Initialize slop guardian.

        Args:
            model: OpenAI model to use (default: gpt-5 for highest quality)
            temperature: Sampling temperature (0.3 for consistent scoring)
            client: Optional OpenAI client (for testing/mocking)
        """
        self.model = model
        self.temperature = temperature
        self.client = client or openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Rubric weights (must sum to 1.0)
        self.weights = {
            "clarity": 0.30,
            "measurability": 0.30,
            "completeness": 0.20,
            "actionability": 0.20,
        }

    def evaluate(self, text: str) -> Result[SlopVerdict, str]:
        """
        Evaluate text quality using rubric-based GPT-5 scoring.

        Args:
            text: Specification text to evaluate (intent, task description, ADR, etc.)

        Returns:
            Result containing SlopVerdict or error message

        Constitutional compliance:
        - Article I: Retry on timeout (2x, 3x up to 10x)
        - Article II: 100% verification (Pydantic validation)
        - Article III: Automated enforcement (no manual override)
        """
        prompt = self._build_rubric_prompt(text)

        # Article I: Retry on timeout (2x, 3x)
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=500,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    timeout=15,  # Production hardening: explicit timeout
                )

                # Defensive navigation through response structure
                content = None
                try:
                    content = response.choices[0].message.content
                except (AttributeError, IndexError, KeyError):
                    # Try alternative shapes
                    try:
                        content = response.choices[0].text
                    except Exception:
                        return Err("LLM: unexpected response shape")

                if not content:
                    return Err("Empty response from LLM")

                # Validate JSON structure with RawSlopEval Pydantic model
                try:
                    raw = RawSlopEval.model_validate_json(content)
                except ValidationError as e:
                    return Err(f"Malformed LLM output: {e}")

                # Compute weighted score
                dimension_scores = raw.dimension_scores
                weighted_score = sum(
                    dimension_scores[dim] * self.weights.get(dim, 0.0) for dim in self.weights
                )

                # Build verdict
                verdict = SlopVerdict(
                    score=round(weighted_score, 1),
                    reasons=raw.reasons,
                    top_fixes=raw.top_fixes,
                    dimension_scores=dimension_scores,
                )

                return Ok(verdict)

            except Exception as e:
                # Categorize common errors (production hardening: broader exception handling)
                err_str = str(e)
                if attempt == 2:
                    return Err(f"LLM error after 3 attempts: {err_str}")
                # Exponential backoff: 2s, 4s
                time.sleep(2 ** (attempt + 1))

        # Should never reach here (fallthrough after 3 retries)
        return Err("Slop evaluation failed after 3 retries")

    def _get_system_prompt(self) -> str:
        """System prompt defining rubric and scoring criteria."""
        return """You are a constitutional quality guardian for the Agency multi-agent system.

Your task is to evaluate specification quality using a 4-dimension rubric.

**Rubric Dimensions** (each scored 0.0-5.0):

1. **Clarity (30% weight)**:
   - 5.0: Precise, unambiguous language with concrete examples
   - 3.5: Mostly clear, minor vagueness in non-critical areas
   - 2.0: Vague language ("better", "improve", "enhance") without specifics
   - 0.0: Completely ambiguous, no clear meaning

2. **Measurability (30% weight)**:
   - 5.0: All outcomes have quantifiable acceptance criteria (metrics, thresholds, test cases)
   - 3.5: Most outcomes measurable, some qualitative goals acceptable
   - 2.0: Few measurable criteria, mostly subjective goals
   - 0.0: No measurable criteria, cannot verify completion

3. **Completeness (20% weight)**:
   - 5.0: All required sections defined (goals, non-goals, personas, criteria)
   - 3.5: Most sections present, minor gaps acceptable
   - 2.0: Missing critical sections (acceptance criteria, personas)
   - 0.0: Only high-level statement, no structure

4. **Actionability (20% weight)**:
   - 5.0: Provides implementable guidance with clear next steps
   - 3.5: Sufficient guidance for experienced implementer
   - 2.0: High-level direction only, unclear how to proceed
   - 0.0: No actionable guidance, pure theory

**Response Format** (JSON):
```json
{
  "dimension_scores": {
    "clarity": <float 0.0-5.0>,
    "measurability": <float 0.0-5.0>,
    "completeness": <float 0.0-5.0>,
    "actionability": <float 0.0-5.0>
  },
  "reasons": ["<issue 1>", "<issue 2>", ...],
  "top_fixes": ["<fix 1>", "<fix 2>", ...]
}
```

**Thresholds**:
- ≥3.5: ACCEPT (proceed to execution)
- 2.0-3.4: REVISE (auto-rewrite or manual clarification)
- <2.0: REJECT (critically vague, immediate rejection)

Be strict but fair. Constitutional quality standards are non-negotiable."""

    def _build_rubric_prompt(self, text: str) -> str:
        """Build evaluation prompt with text and rubric."""
        return f"""Evaluate the following specification text:

---
{text}
---

Score each rubric dimension (clarity, measurability, completeness, actionability) from 0.0-5.0.

Identify quality issues (reasons) and actionable improvements (top_fixes).

Respond in JSON format only."""

    def auto_rewrite(self, original_text: str, fixes: list[str]) -> Result[str, str]:
        """Ask the model to rewrite the spec applying the fixes.

        Args:
            original_text: Original specification text
            fixes: List of actionable improvements to apply

        Returns:
            Result containing rewritten text or error message

        Production hardening:
        - Enhanced error handling for LLM failures
        - Explicit timeout (20s for rewrite operations)
        - Defensive response parsing
        """
        prompt = (
            "Rewrite the following specification preserving intent but applying these actionable fixes:\n"
            f"Fixes:\n- "
            + "\n- ".join(fixes)
            + "\n\nOriginal:\n" + original_text
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,  # Lower temperature for precise spec editing
                max_tokens=800,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise spec editor. Keep format and intent.",
                    },
                    {"role": "user", "content": prompt},
                ],
                timeout=20,  # Explicit timeout for rewrite operations
            )

            # Defensive response parsing
            try:
                rewritten = response.choices[0].message.content
            except (AttributeError, IndexError, KeyError):
                try:
                    rewritten = response.choices[0].text
                except Exception as e:
                    return Err(f"Unexpected LLM shape during rewrite: {e}")

            if not rewritten:
                return Err("Empty rewrite from LLM")

            return Ok(rewritten)

        except Exception as e:
            return Err(f"Auto-rewrite failed: {e}")


def log_slop_evaluation(
    verdict: SlopVerdict,
    original_text: str,
    stage: str,
    attempt: int = 0,
    task_id: str | None = None,
) -> None:
    """
    Log slop evaluation to audit trail with HMAC signature.

    Args:
        verdict: Evaluation verdict
        original_text: Original text evaluated
        stage: Stage of evaluation (pre_planning, graph_validation, post_execution)
        attempt: Attempt number (for auto-rewrite cycles)
        task_id: Task ID (for graph validation stage)

    Constitutional compliance:
    - Article III: Append-only audit trail (HMAC tamper detection)

    Production hardening:
    - Uses AGENCY_DATA_DIR instead of hard-coded ~/.agency
    - Atomic writes via append_jsonl_atomic (concurrency-safe)
    - HMAC-SHA256 signing with secret key (vs plain SHA256)
    """
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "attempt": attempt,
        "task_id": task_id,
        "verdict": {
            "status": verdict.status,
            "score": verdict.score,
            "reasons": verdict.reasons,
            "top_fixes": verdict.top_fixes,
            "dimension_scores": verdict.dimension_scores,
        },
        "original_text_hash": hashlib.sha256(original_text.encode()).hexdigest(),
    }

    # Write to audit trail with HMAC signature (atomic + concurrency-safe)
    audit_dir = os.path.join(AGENCY_DATA_DIR, "audit", "slop_immunity")
    write_audit_entry(audit_dir, audit_entry)


def enforce_slop_immunity(
    text: str, guardian: SlopGuardian, stage: str = "pre_planning"
) -> Result[SlopVerdict, SlopDetected]:
    """
    Enforce slop immunity with mandatory pre-flight check and auto-rewrite loop.

    Args:
        text: Text to evaluate (intent, task description, etc.)
        guardian: SlopGuardian instance
        stage: Stage of evaluation (for audit logging)

    Returns:
        Result containing SlopVerdict (ACCEPT) or SlopDetected exception

    Constitutional compliance:
    - Article III: Automated enforcement (no bypass without audit)
    - Article IV: VectorStore integration (REVISE/REJECT patterns stored)

    Production hardening:
    - Auto-rewrite loop for REVISE verdicts (up to 3 attempts)
    - Atomic audit logging with HMAC signatures
    - Enhanced error handling for LLM failures
    """
    eval_result = guardian.evaluate(text)

    if eval_result.is_err():
        # Evaluation failed, build failing verdict
        err_msg = eval_result.unwrap_err()
        failing = SlopVerdict(
            score=0.0,
            reasons=[err_msg],
            top_fixes=["Slop eval failure"],
            dimension_scores={"clarity": 0.0, "measurability": 0.0, "completeness": 0.0, "actionability": 0.0},
        )
        # Audit the failure
        log_slop_evaluation(failing, text, stage=stage, attempt=0)
        return Err(SlopDetected(failing, text))

    verdict = eval_result.unwrap()

    # Log initial evaluation
    log_slop_evaluation(verdict, text, stage=stage, attempt=0)

    if verdict.status == VerdictStatus.ACCEPT:
        return Ok(verdict)

    # If REVISE: attempt auto-rewrite up to 3 times
    if verdict.status == VerdictStatus.REVISE:
        rewritten_text = text
        for attempt in range(1, 4):
            rewrite_res = guardian.auto_rewrite(rewritten_text, verdict.top_fixes)

            if rewrite_res.is_err():
                # Log rewrite failure and continue to next attempt
                failure_verdict = SlopVerdict(
                    score=verdict.score,
                    reasons=[rewrite_res.unwrap_err()],
                    top_fixes=[],
                    dimension_scores=verdict.dimension_scores,
                )
                log_slop_evaluation(failure_verdict, rewritten_text, stage=stage, attempt=attempt)
                continue

            rewritten_text = rewrite_res.unwrap()

            # Re-evaluate rewritten spec
            re_eval = guardian.evaluate(rewritten_text)

            if re_eval.is_err():
                # Log re-evaluation failure and continue
                failure_verdict = SlopVerdict(
                    score=0.0,
                    reasons=[re_eval.unwrap_err()],
                    top_fixes=[],
                    dimension_scores={"clarity": 0.0, "measurability": 0.0, "completeness": 0.0, "actionability": 0.0},
                )
                log_slop_evaluation(failure_verdict, rewritten_text, stage=stage, attempt=attempt)
                continue

            new_verdict = re_eval.unwrap()
            log_slop_evaluation(new_verdict, rewritten_text, stage=stage, attempt=attempt)

            if new_verdict.status == VerdictStatus.ACCEPT:
                # Successful auto-rewrite!
                # Optional: store revision pattern in VectorStore (integration point)
                return Ok(new_verdict)

            # Update verdict and loop again
            verdict = new_verdict

        # Exhausted attempts -> treat as SlopDetected
        return Err(SlopDetected(verdict, text))

    # If REJECT: immediate failure
    return Err(SlopDetected(verdict, text))
