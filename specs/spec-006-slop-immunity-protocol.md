# Specification: Slop Immunity Protocol

**Spec ID**: `spec-006-slop-immunity-protocol`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-11
**Last Updated**: 2025-10-11
**Related Plan**: `plan-006-slop-immunity-protocol.md` (to be created after spec approval)
**Related ADR**: `ADR-003: Automated Merge Enforcement`
**Constitutional Article**: `Article III, Clause 3.2: Slop Immunity`

---

## Executive Summary

Define a constitutional-grade quality gate to prevent vague, unmeasurable specifications from entering the /primeA orchestrator execution pipeline. The Slop Immunity Protocol establishes three-stage integration (pre-planning intent scrubbing, graph validation spec-level scoring, post-execution reflection auditing) with automated REVISE workflow, halt conditions (<3.5 score threshold), and cryptographic audit trail for all quality checks.

This specification implements **Constitutional Article III, Clause 3.2** - establishing slop immunity as a fundamental enforcement mechanism preventing quality degradation through automated, technically-enforced barriers to low-quality inputs.

---

## Goals

### Primary Goals

- **Goal 1**: Prevent vague, unmeasurable specifications from entering execution pipeline via automated quality scoring (<3.5 threshold halts execution)
- **Goal 2**: Implement three-stage integration points with clear workflows (pre-planning, graph validation, post-execution auditing)
- **Goal 3**: Establish REVISE workflow with auto-rewrite capability, retry limits (max 3 attempts), and human escalation path
- **Goal 4**: Ensure constitutional compliance with Article III enforcement (zero manual override capabilities, automated rejection)
- **Goal 5**: Achieve >95% slop detection accuracy (true positives) and <5% false positive rate on validation set

### Success Metrics

- **Detection Accuracy**: >95% of vague specs correctly flagged (score <3.5)
- **False Positive Rate**: <5% of well-defined specs incorrectly rejected
- **Auto-Rewrite Success**: >70% of REVISE cases reach ≥3.5 score within 3 attempts
- **Latency**: Quality scoring completes <200ms p99 (no blocking delay for user)
- **Constitutional Compliance**: 100% of executions pass through slop guardian (zero bypass mechanisms)

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Natural language understanding improvements (use existing LLM capabilities, no custom NLP models)
- **Non-Goal 2**: User education on spec-writing (focus on automated detection and rewrite, not training materials)
- **Non-Goal 3**: Fine-tuning custom models for slop detection (use GPT-5 with rubric-based prompting)
- **Non-Goal 4**: Real-time monitoring dashboard (CLI feedback sufficient for MVP, dashboard is future enhancement)

### Future Considerations

- **Future Enhancement 1**: Machine learning model fine-tuned on historical slop detection patterns (VectorStore-based)
- **Future Enhancement 2**: User-facing spec quality dashboard with live scoring and improvement suggestions
- **Future Enhancement 3**: Integration with IDE/editor for real-time spec quality feedback during writing
- **Future Enhancement 4**: Cross-organization slop pattern learning (public dataset of high/low quality specs)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: /primeA Orchestrator Agent

- **Description**: Autonomous execution engine that generates task graphs from natural language intent or backlog items
- **Goals**: Execute only well-defined, measurable specifications to prevent downstream failures and rework
- **Pain Points**: Current system accepts vague specs → graph generation succeeds but execution fails → wasted compute and time
- **Technical Proficiency**: Autonomous agent with graph generation and execution capabilities

#### Persona 2: Development Team (Human User)

- **Description**: Engineers providing natural language intent for feature development or bug fixes
- **Goals**: Quick task execution without being blocked by overly strict quality gates
- **Pain Points**: May write vague initial specs due to time pressure, need fast feedback on clarity issues
- **Technical Proficiency**: Senior engineers familiar with Agency constitution and spec-kit methodology

#### Persona 3: Quality Enforcer Agent

- **Description**: Constitutional compliance guardian monitoring all execution pipelines
- **Goals**: Prevent Article II violations (quality standards) through automated enforcement
- **Pain Points**: Current system lacks pre-flight quality checks, violations detected only after execution starts
- **Technical Proficiency**: Agent with constitutional validation and audit trail capabilities

### User Journeys

#### Journey 1: Pre-Planning Intent Scrubbing (Primary Use Case - Mode 1/2)

```
1. User starts with: Natural language intent "Make the system better"
2. System needs to: Evaluate intent clarity before generating task graph
3. System performs:
   - Call slop_guardian.evaluate(intent_text)
   - Compute score using GPT-5 with rubric (5-point scale)
   - Analyze verdict: ACCEPT (≥3.5), REVISE (<3.5), REJECT (<2.0)
4. System encounters: REVISE verdict (score 2.8, reasons: "Vague outcome", "No acceptance criteria")
5. System responds:
   - IF auto_rewrite_enabled: Spawn planner agent to rewrite intent with precision
   - ELSE: Return JSON verdict to user with top_fixes recommendations
   - Re-evaluate rewritten intent (max 3 attempts)
6. User achieves:
   - Well-defined intent with score ≥3.5 proceeds to graph generation
   - OR clear feedback on clarity issues requiring manual intervention
   - Zero vague specs enter execution pipeline (constitutional enforcement)
```

#### Journey 2: Graph Validation Spec-Level Scoring (Secondary Use Case)

```
1. System starts with: Generated TaskGraph with 15 Spec tasks
2. System needs to: Validate all Spec tasks meet quality threshold before execution
3. System performs:
   - Iterate through all tasks where task.type == "Spec"
   - Call slop_guardian.evaluate(task.description) for each
   - Collect scores and identify tasks <3.5 threshold
4. System encounters: 3/15 Spec tasks below threshold (scores: 2.9, 3.1, 2.5)
5. System responds:
   - Raise SlopDetected exception with task IDs, scores, and reasons
   - Log critical_gaps to audit trail with SHA256 signature
   - Halt execution, require user intervention or auto-rewrite
6. System achieves:
   - Only high-quality Spec tasks execute (zero downstream quality failures)
   - Clear audit trail of rejected tasks for learning extraction
   - Constitutional Article III compliance (automated enforcement)
```

#### Journey 3: Post-Execution Reflection Auditing (Tertiary Use Case)

```
1. System starts with: Completed execution with generated ADRs and pattern learnings
2. System needs to: Validate learning quality to prevent pattern pollution
3. System performs:
   - Extract ADR text from Phase 6 learning loop
   - Call slop_guardian.evaluate(adr_text)
   - Score learning actionability and specificity
4. System encounters: ADR with score 3.2 (WARNING threshold)
5. System responds:
   - Flag ADR as non-actionable (don't store in VectorStore with high confidence)
   - Store with reduced confidence (0.4 instead of 0.6)
   - Log quality signal to telemetry for monitoring
6. System achieves:
   - VectorStore contains only high-quality, actionable patterns
   - Learning quality metrics tracked for continuous improvement
   - Cross-session learning maintains institutional memory standards
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: Slop Guardian Core

- [ ] **AC-1.1**: `SlopGuardian` class with `evaluate(text: str) -> SlopVerdict` method using GPT-5 with rubric-based prompting
- [ ] **AC-1.2**: 5-point rubric implemented: 5.0 (exceptional), 4.0-4.9 (good), 3.5-3.9 (acceptable), 2.0-3.4 (REVISE), <2.0 (REJECT)
- [ ] **AC-1.3**: `SlopVerdict` Pydantic model with fields: status (ACCEPT/REVISE/REJECT), score (float 0.0-5.0), reasons (list[str]), top_fixes (list[str])
- [ ] **AC-1.4**: Rubric evaluates: clarity (specific vs vague), measurability (testable criteria), completeness (all sections defined), actionability (implementable guidance)
- [ ] **AC-1.5**: Evaluation completes <200ms p99 (GPT-5 API call with 500 token max output)

#### Feature Component 2: Three-Stage Integration

- [ ] **AC-2.1**: **Stage 1 (Pre-Planning)**: Integrated into `/primeA` orchestrator before planner agent spawned (Modes 1 & 2)
- [ ] **AC-2.2**: **Stage 2 (Graph Validation)**: Integrated into `TaskGraph` executor after generation, before execution (all Spec tasks scored)
- [ ] **AC-2.3**: **Stage 3 (Post-Execution)**: Integrated into Phase 6 learning loop after ADR generation (learning quality audit)
- [ ] **AC-2.4**: All three stages log evaluation results to audit trail with SHA256 signatures
- [ ] **AC-2.5**: Stage 1 and Stage 2 are BLOCKING (halt execution on REVISE/REJECT), Stage 3 is NON-BLOCKING (flag only)

#### Feature Component 3: REVISE Workflow

- [ ] **AC-3.1**: Auto-rewrite enabled by default (configurable via `SLOP_AUTO_REWRITE=true` env var)
- [ ] **AC-3.2**: Auto-rewrite spawns planner agent task: "Rewrite intent with precision following rubric: [top_fixes]"
- [ ] **AC-3.3**: Re-evaluation after rewrite (same rubric, same threshold)
- [ ] **AC-3.4**: Retry limit enforced: max 3 rewrite attempts, human escalation after exhaustion
- [ ] **AC-3.5**: Manual REVISE path: Return JSON verdict to user with top_fixes, halt execution, require clarification

#### Feature Component 4: Halt Conditions

- [ ] **AC-4.1**: Constitutional threshold: score <3.5 triggers halt (REVISE verdict)
- [ ] **AC-4.2**: Critical threshold: score <2.0 triggers immediate rejection (REJECT verdict, no auto-rewrite)
- [ ] **AC-4.3**: Override flag: `--skip-slop-check` allows bypass (emergency only, logged to audit with WARNING severity)
- [ ] **AC-4.4**: Halt raises `SlopDetected` exception with verdict, score, reasons, and original_text
- [ ] **AC-4.5**: Exception message includes actionable guidance: "Intent too vague (score 2.8/5.0). Top fixes: [list]"

#### Feature Component 5: Rubric-Based Evaluation

- [ ] **AC-5.1**: Rubric has 4 dimensions: clarity, measurability, completeness, actionability (each scored 0.0-5.0)
- [ ] **AC-5.2**: Final score is weighted average: clarity (30%), measurability (30%), completeness (20%), actionability (20%)
- [ ] **AC-5.3**: Dimension scoring criteria clearly defined in prompt engineering (examples for each score level)
- [ ] **AC-5.4**: Rubric prompt includes examples: 5.0 (exceptional spec), 3.5 (acceptable spec), 2.0 (vague spec)
- [ ] **AC-5.5**: GPT-5 response schema validated with Pydantic: {score: float, reasons: list[str], dimension_scores: dict}

### Non-Functional Requirements

#### Performance

- [ ] **AC-P.1**: Evaluation latency <200ms p99 (GPT-5 API call, 500 token output limit)
- [ ] **AC-P.2**: Auto-rewrite latency <5 seconds p99 (includes planner agent spawn, rewrite, re-evaluation)
- [ ] **AC-P.3**: Stage 2 graph validation <1 second for graphs with 50 Spec tasks (parallel evaluation)

#### Quality

- [ ] **AC-Q.1**: Detection accuracy >95% on 100-spec validation set (true positives)
- [ ] **AC-Q.2**: False positive rate <5% on 100-spec validation set (well-defined specs incorrectly rejected)
- [ ] **AC-Q.3**: Auto-rewrite success rate >70% (REVISE cases reaching ≥3.5 within 3 attempts)
- [ ] **AC-Q.4**: Inter-rater reliability >0.85 (GPT-5 scoring consistent across repeated evaluations)

#### Security

- [ ] **AC-S.1**: Audit trail entries signed with SHA256 (tamper detection)
- [ ] **AC-S.2**: Override flag usage logged to audit with user_id, timestamp, and reason
- [ ] **AC-S.3**: GPT-5 API key secured via environment variable (no hardcoded credentials)
- [ ] **AC-S.4**: Input sanitization prevents prompt injection attacks (escape special characters in intent text)

### Constitutional Compliance

#### Article I: Complete Context Before Action

- [ ] **AC-CI.1**: Evaluation retries on API timeout (2x, 3x up to 10x with exponential backoff)
- [ ] **AC-CI.2**: All evaluation dimensions scored (no partial rubric evaluation)
- [ ] **AC-CI.3**: Rewrite cycle includes full context (original intent + verdict + top_fixes)

#### Article II: 100% Verification and Stability

- [ ] **AC-CII.1**: 100% test coverage for `SlopGuardian` class (unit tests)
- [ ] **AC-CII.2**: All threshold branches tested (score 2.0, 3.4, 3.5, 5.0)
- [ ] **AC-CII.3**: Integration tests with real GPT-5 API (end-to-end validation)
- [ ] **AC-CII.4**: Validation set with ground truth labels (100 specs manually scored)

#### Article III: Automated Merge Enforcement

- [ ] **AC-CIII.1**: Slop guardian is MANDATORY pre-flight check (zero manual override without audit)
- [ ] **AC-CIII.2**: Constitutional threshold (3.5) enforced automatically (no runtime modification)
- [ ] **AC-CIII.3**: Override flag requires explicit user action (not bypassed accidentally)
- [ ] **AC-CIII.4**: All enforcement actions logged to audit trail (append-only ledger)

#### Article IV: Continuous Learning and Improvement

- [ ] **AC-CIV.1**: REVISE/REJECT cases stored in VectorStore with verdict and reasons (learning patterns)
- [ ] **AC-CIV.2**: Auto-rewrite patterns extracted after successful conversions (score <3.5 → ≥3.5)
- [ ] **AC-CIV.3**: Rubric dimension weights tunable based on VectorStore learning (future: adaptive weighting)
- [ ] **AC-CIV.4**: Slop detection patterns queryable for similar future intents (semantic search)

#### Article V: Spec-Driven Development

- [ ] **AC-CV.1**: Implementation follows this specification (no deviation without spec update)
- [ ] **AC-CV.2**: Rubric versioned (breaking changes require new spec version and migration path)
- [ ] **AC-CV.3**: This spec serves as authoritative source for slop immunity behavior

---

## Technical Design

### 6.1 Slop Guardian Core (Rubric-Based GPT-5 Evaluation)

```python
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

from enum import Enum
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import openai
import os


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
        status: Verdict status (ACCEPT/REVISE/REJECT)
        score: Overall quality score (0.0-5.0, weighted average of dimensions)
        reasons: List of quality issues identified (empty if ACCEPT)
        top_fixes: List of actionable improvements (empty if ACCEPT)
        dimension_scores: Rubric dimension scores (clarity, measurability, completeness, actionability)
        evaluated_at: ISO 8601 timestamp of evaluation (UTC)

    Example:
        >>> verdict = SlopVerdict(
        ...     status=VerdictStatus.REVISE,
        ...     score=2.8,
        ...     reasons=["Vague outcome", "No acceptance criteria"],
        ...     top_fixes=["Specify measurable success metrics", "Define concrete deliverables"],
        ...     dimension_scores={"clarity": 2.5, "measurability": 2.0, "completeness": 3.5, "actionability": 3.2}
        ... )
    """
    status: VerdictStatus = Field(..., description="Verdict status (ACCEPT/REVISE/REJECT)")
    score: float = Field(..., ge=0.0, le=5.0, description="Overall quality score (0.0-5.0)")
    reasons: list[str] = Field(default_factory=list, description="Quality issues identified")
    top_fixes: list[str] = Field(default_factory=list, description="Actionable improvements")
    dimension_scores: dict[str, float] = Field(
        ...,
        description="Rubric dimension scores (clarity, measurability, completeness, actionability)"
    )
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 timestamp of evaluation (UTC)"
    )

    class Config:
        use_enum_values = True

    @field_validator("status", mode="before")
    @classmethod
    def compute_status(cls, v: VerdictStatus | None, info) -> VerdictStatus:
        """Compute verdict status from score."""
        if v is not None:
            return v

        score = info.data.get("score", 0.0)

        if score >= 3.5:
            return VerdictStatus.ACCEPT
        elif score >= 2.0:
            return VerdictStatus.REVISE
        else:
            return VerdictStatus.REJECT


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

    def __init__(self, model: str = "gpt-5", temperature: float = 0.3):
        """
        Initialize slop guardian.

        Args:
            model: OpenAI model to use (default: gpt-5 for highest quality)
            temperature: Sampling temperature (0.3 for consistent scoring)
        """
        self.model = model
        self.temperature = temperature
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Rubric weights (must sum to 1.0)
        self.weights = {
            "clarity": 0.30,
            "measurability": 0.30,
            "completeness": 0.20,
            "actionability": 0.20
        }

    def evaluate(self, text: str) -> SlopVerdict:
        """
        Evaluate text quality using rubric-based GPT-5 scoring.

        Args:
            text: Specification text to evaluate (intent, task description, ADR, etc.)

        Returns:
            SlopVerdict with status, score, reasons, and top_fixes

        Raises:
            openai.APIError: On API failure (retried 3x per Article I)
        """
        prompt = self._build_rubric_prompt(text)

        # Article I: Retry on timeout (2x, 3x up to 10x)
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=500,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )

                # Parse GPT-5 response
                result = response.choices[0].message.content
                import json
                evaluation = json.loads(result)

                # Compute weighted score
                dimension_scores = evaluation["dimension_scores"]
                weighted_score = sum(
                    dimension_scores[dim] * self.weights[dim]
                    for dim in self.weights
                )

                # Build verdict
                return SlopVerdict(
                    score=round(weighted_score, 1),
                    reasons=evaluation["reasons"],
                    top_fixes=evaluation["top_fixes"],
                    dimension_scores=dimension_scores
                )

            except openai.APIError as e:
                if attempt == 2:
                    raise
                # Exponential backoff: 2s, 4s
                import time
                time.sleep(2 ** (attempt + 1))

        # Should never reach here (fallthrough after 3 retries)
        raise RuntimeError("Slop evaluation failed after 3 retries")

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
```

### 6.2 Three-Stage Integration

#### **Stage 1: Pre-Planning Intent Scrubbing** (Modes 1 & 2)

```python
# Integration point: tools/orchestrator/primeA.py (before graph generation)

from shared.slop_guardian import SlopGuardian, SlopDetected, VerdictStatus
from shared.type_definitions.result import Result, Ok, Err

def execute_primeA(intent: str, auto_rewrite: bool = True) -> Result[TaskGraph, str]:
    """
    Execute primeA orchestration with slop immunity.

    Args:
        intent: Natural language intent or backlog item description
        auto_rewrite: Enable auto-rewrite on REVISE verdict (default: True)

    Returns:
        Result with TaskGraph or error message

    Raises:
        SlopDetected: If intent quality below threshold after 3 rewrite attempts
    """
    guardian = SlopGuardian()

    # Stage 1: Pre-planning slop check
    for attempt in range(3):
        verdict = guardian.evaluate(intent)

        # Log to audit trail (with SHA256 signature)
        log_slop_evaluation(verdict, intent, stage="pre_planning", attempt=attempt)

        if verdict.status == VerdictStatus.ACCEPT:
            # Proceed to graph generation
            break

        elif verdict.status == VerdictStatus.REJECT:
            # Critical failure, no auto-rewrite
            raise SlopDetected(verdict, intent)

        elif verdict.status == VerdictStatus.REVISE:
            if not auto_rewrite:
                # Manual clarification required
                raise SlopDetected(verdict, intent)

            # Auto-rewrite with planner agent
            rewrite_prompt = _build_rewrite_prompt(intent, verdict)
            intent_v2 = spawn_planner_agent(rewrite_prompt)

            # Re-evaluate rewritten intent
            intent = intent_v2

            if attempt == 2:
                # Max 3 attempts, escalate to human
                raise SlopDetected(verdict, intent)

    # Generate task graph (slop check passed)
    graph = generate_task_graph(intent)

    return Ok(graph)


def _build_rewrite_prompt(original_intent: str, verdict: SlopVerdict) -> str:
    """Build rewrite prompt with clarity improvements."""
    return f"""Rewrite the following intent with precision to address quality issues:

**Original Intent:**
{original_intent}

**Quality Issues:**
{', '.join(verdict.reasons)}

**Required Improvements:**
{', '.join(verdict.top_fixes)}

**Rubric Requirements:**
- Clarity: Use specific, unambiguous language
- Measurability: Define quantifiable acceptance criteria
- Completeness: Include goals, non-goals, personas, criteria
- Actionability: Provide implementable guidance

Rewrite intent to achieve score ≥3.5/5.0."""
```

#### **Stage 2: Graph Validation Spec-Level Scoring**

```python
# Integration point: tools/orchestrator/graph_executor.py (after graph generation)

def validate_spec_tasks(graph: TaskGraph) -> Result[None, str]:
    """
    Validate all Spec tasks in graph meet quality threshold.

    Args:
        graph: Generated task graph

    Returns:
        Result with None (success) or error message

    Raises:
        SlopDetected: If any Spec task below 3.5 threshold
    """
    guardian = SlopGuardian()
    critical_gaps = []

    # Iterate all Spec tasks
    for task in graph.tasks:
        if task.type != "Spec":
            continue

        verdict = guardian.evaluate(task.description)

        # Log to audit trail
        log_slop_evaluation(verdict, task.description, stage="graph_validation", task_id=task.id)

        if verdict.status != VerdictStatus.ACCEPT:
            critical_gaps.append({
                "task_id": task.id,
                "score": verdict.score,
                "reasons": verdict.reasons
            })

    if critical_gaps:
        # Raise exception with all failed tasks
        raise SlopDetected(
            verdict=SlopVerdict(
                score=min(gap["score"] for gap in critical_gaps),
                reasons=[f"Task {gap['task_id']}: {', '.join(gap['reasons'])}" for gap in critical_gaps],
                top_fixes=["Review Spec task descriptions for clarity and measurability"],
                dimension_scores={}
            ),
            original_text=f"{len(critical_gaps)} Spec tasks below threshold"
        )

    return Ok(None)
```

#### **Stage 3: Post-Execution Reflection Auditing**

```python
# Integration point: tools/orchestrator/learning_extractor.py (Phase 6)

def audit_learning_quality(adr_text: str, context: AgentContext) -> float:
    """
    Audit learning quality to prevent VectorStore pattern pollution.

    Args:
        adr_text: Generated ADR or learning text
        context: AgentContext for VectorStore access

    Returns:
        Confidence score (0.0-1.0) for VectorStore storage
    """
    guardian = SlopGuardian()
    verdict = guardian.evaluate(adr_text)

    # Log to audit trail (non-blocking)
    log_slop_evaluation(verdict, adr_text, stage="post_execution", severity="info")

    # Map score to confidence (3.5+ → 0.6+, <3.5 → 0.4)
    if verdict.score >= 4.0:
        confidence = 0.8
    elif verdict.score >= 3.5:
        confidence = 0.6
    else:
        confidence = 0.4  # Low confidence, flag for review

    return confidence
```

### 6.3 REVISE Workflow (Auto-Rewrite Cycle)

```
┌─────────────────────────────────────────────────────────────┐
│  REVISE Workflow                                            │
│                                                             │
│  ┌──────────────┐                                          │
│  │ Evaluate     │                                          │
│  │ Intent       │                                          │
│  └──────┬───────┘                                          │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐       score ≥3.5                        │
│  │ Check Score  │──────────────────────► [ACCEPT] Proceed │
│  └──────┬───────┘                                          │
│         │                                                  │
│         │ score <2.0                                       │
│         ├──────────────────────► [REJECT] Halt            │
│         │                                                  │
│         │ 2.0 ≤ score <3.5                                 │
│         ▼                                                  │
│  ┌──────────────┐                                          │
│  │ Auto-Rewrite?│                                          │
│  └──────┬───────┘                                          │
│         │                                                  │
│    ┌────┴────┐                                             │
│    │ Yes     │ No                                          │
│    ▼         ▼                                             │
│  ┌────────┐ ┌──────────────┐                              │
│  │ Spawn  │ │ Return JSON  │                              │
│  │ Planner│ │ Verdict      │                              │
│  │ Agent  │ │ to User      │                              │
│  └───┬────┘ └──────────────┘                              │
│      │                                                     │
│      ▼                                                     │
│  ┌────────────┐                                            │
│  │ Rewrite    │                                            │
│  │ Intent     │                                            │
│  └─────┬──────┘                                            │
│        │                                                   │
│        ▼                                                   │
│  ┌────────────┐      attempt < 3                          │
│  │ Re-Evaluate├──────────────────────► Loop back          │
│  └─────┬──────┘                                            │
│        │                                                   │
│        │ attempt ≥ 3                                       │
│        ▼                                                   │
│  [ESCALATE] Human intervention required                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.4 Halt Conditions & Override Mechanism

```python
# Threshold constants (constitutional enforcement)
CONSTITUTIONAL_THRESHOLD = 3.5  # REVISE below, ACCEPT above
CRITICAL_THRESHOLD = 2.0        # REJECT below, no auto-rewrite

# Override flag (emergency only, logged to audit)
def check_override_flag(args: argparse.Namespace) -> bool:
    """
    Check if slop check override flag is set.

    Args:
        args: Command-line arguments

    Returns:
        True if --skip-slop-check flag present

    Side effects:
        Logs WARNING to audit trail if override used
    """
    if args.skip_slop_check:
        log_audit_event(
            event_type="slop_override",
            severity="WARNING",
            message="Slop check bypassed with --skip-slop-check flag",
            user_id=os.getenv("USER"),
            timestamp=datetime.now(UTC).isoformat()
        )
        return True

    return False


# Halt logic
def enforce_slop_immunity(intent: str, args: argparse.Namespace) -> None:
    """
    Enforce slop immunity with halt conditions.

    Args:
        intent: Natural language intent
        args: Command-line arguments

    Raises:
        SlopDetected: If score <3.5 and no override flag
    """
    if check_override_flag(args):
        return  # Emergency bypass (logged)

    guardian = SlopGuardian()
    verdict = guardian.evaluate(intent)

    if verdict.status != VerdictStatus.ACCEPT:
        raise SlopDetected(verdict, intent)
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `openai>=1.0.0` - GPT-5 API for rubric-based evaluation
- **Dependency 2**: `tools/orchestrator/primeA.py` - /primeA orchestrator integration point (Stage 1)
- **Dependency 3**: `tools/orchestrator/graph_executor.py` - Task graph executor integration point (Stage 2)
- **Dependency 4**: `tools/orchestrator/learning_extractor.py` - Learning loop integration point (Stage 3)
- **Dependency 5**: `shared/agent_context.py` - VectorStore access for pattern storage (Article IV)
- **Dependency 6**: `tools/audit_signing.py` - Cryptographic audit trail for slop evaluations

### External Dependencies

- **External Dep 1**: OpenAI API with GPT-5 model access
- **External Dep 2**: Internet connectivity for API calls (no offline mode)

### Technical Constraints

- **Constraint 1**: Evaluation latency must be <200ms p99 (no blocking delay for user experience)
- **Constraint 2**: GPT-5 API rate limits (500 requests/minute, must handle 429 errors)
- **Constraint 3**: Rubric prompt length <2000 tokens (fits within GPT-5 context window with intent)
- **Constraint 4**: Auto-rewrite cycle max 3 attempts (prevent infinite loops)

### Business Constraints

- **Constraint 1**: False positive rate must be <5% (avoid blocking valid specs)
- **Constraint 2**: Detection accuracy must be >95% (catch truly vague specs)
- **Constraint 3**: Auto-rewrite success rate >70% (most REVISE cases resolved automatically)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **GPT-5 API failures during critical path** - *Mitigation*: Retry with exponential backoff (Article I), fallback to manual review after 3 failures
- **Risk 2**: **False positives blocking valid specs** - *Mitigation*: Conservative threshold (3.5 tuned on validation set), override flag for emergencies

### Medium Risk Items

- **Risk 3**: **Rubric drift over time (GPT-5 scoring inconsistency)** - *Mitigation*: Inter-rater reliability testing, rubric versioning with examples
- **Risk 4**: **Auto-rewrite quality degradation** - *Mitigation*: Track rewrite success rate, alert if <70%

### Constitutional Risks

- **Constitutional Risk 1**: **Article III violation (manual override without audit)** - *Mitigation*: All overrides logged to audit trail with SHA256 signatures
- **Constitutional Risk 2**: **Article IV violation (REVISE patterns not stored)** - *Mitigation*: Assert VectorStore update for all REVISE/REJECT cases in tests

---

## Integration Points

### Agent Integration

- **PlannerAgent**: Auto-rewrite orchestration, receives rewrite prompts with top_fixes
- **QualityEnforcerAgent**: Constitutional compliance monitoring, validates slop immunity enforcement
- **LearningAgent**: Pattern extraction from REVISE/REJECT cases for continuous improvement
- **/primeA Orchestrator**: Primary integration point for Stage 1 (pre-planning) and Stage 2 (graph validation)

### System Integration

- **VectorStore**: Stores REVISE/REJECT patterns with verdict and reasons (Article IV)
- **Audit Trail**: Logs all slop evaluations with SHA256 signatures (Article III)
- **Telemetry System**: Tracks evaluation latency, false positive/negative rates, auto-rewrite success

### External Integration

- **OpenAI GPT-5 API**: Rubric-based evaluation engine
- **Command-line Interface**: `--skip-slop-check` override flag for emergency bypass

---

## Testing Strategy

### Test Categories

- **Unit Tests** (100% coverage): `SlopGuardian` class, verdict status computation, rubric scoring logic
- **Integration Tests**: End-to-end with real GPT-5 API, three-stage integration workflows
- **Validation Tests**: 100-spec validation set with ground truth labels (human-scored)
- **Performance Tests**: Evaluation latency <200ms p99, auto-rewrite cycle <5s p99
- **Constitutional Compliance Tests**: Article I retry logic, Article III enforcement, Article IV VectorStore storage

### Test Data Requirements

- **Test Data 1**: 100-spec validation set with ground truth scores (manual scoring by senior engineers)
- **Test Data 2**: Edge cases (empty intent, extremely long intent, special characters)
- **Test Data 3**: Historical vague specs from past sessions (VectorStore query)

### Test Environment Requirements

- **Environment 1**: OpenAI API key with GPT-5 access
- **Environment 2**: VectorStore backend for pattern storage testing
- **Environment 3**: Audit trail with writable append-only ledger

---

## Implementation Phases

### Phase 1: Core Guardian Implementation (Week 1, Day 1-2)

- **Scope**: `SlopGuardian` class with rubric-based GPT-5 evaluation
- **Deliverables**:
  - `shared/slop_guardian.py` with `SlopGuardian`, `SlopVerdict`, `SlopDetected`
  - Rubric prompt engineering with examples
  - Unit tests for verdict status computation
- **Success Criteria**: 100% test pass, evaluation latency <200ms p99

### Phase 2: Three-Stage Integration (Week 1, Day 3-4)

- **Scope**: Stage 1 (pre-planning), Stage 2 (graph validation), Stage 3 (post-execution)
- **Deliverables**:
  - Integration code in `primeA.py`, `graph_executor.py`, `learning_extractor.py`
  - REVISE workflow with auto-rewrite cycle
  - Audit trail logging for all evaluations
- **Success Criteria**: All three stages operational, integration tests pass

### Phase 3: Validation & Tuning (Week 2, Day 1-2)

- **Scope**: Validation set testing, threshold tuning, false positive/negative analysis
- **Deliverables**:
  - 100-spec validation set with ground truth
  - Detection accuracy >95%, false positive rate <5%
  - Rubric dimension weight tuning
- **Success Criteria**: Accuracy targets met, inter-rater reliability >0.85

### Phase 4: Production Hardening (Week 2, Day 3-5)

- **Scope**: Override flag implementation, VectorStore pattern storage, telemetry integration
- **Deliverables**:
  - `--skip-slop-check` flag with audit logging
  - Article IV VectorStore integration for REVISE/REJECT patterns
  - Telemetry dashboard for monitoring
- **Success Criteria**: Constitutional compliance 100%, production ready

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: QualityEnforcerAgent, PlannerAgent, /primeA Orchestrator
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), LearningAgent (VectorStore integration)

### Review Criteria

- [ ] **Completeness**: All three stages defined with clear workflows
- [ ] **Clarity**: Rubric dimensions and thresholds are unambiguous
- [ ] **Feasibility**: GPT-5 evaluation latency <200ms p99 achievable
- [ ] **Constitutional Compliance**: Article III enforcement (no manual override), Article IV VectorStore storage
- [ ] **Quality Standards**: Detection accuracy >95%, false positive rate <5%

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **Constitutional Compliance**: Pending QualityEnforcer validation
- [ ] **Final Approval**: Pending after Phase 1 implementation

---

## Appendices

### Appendix A: Glossary

- **Slop**: Vague, unmeasurable specifications lacking clarity, acceptance criteria, or actionable guidance
- **Slop Guardian**: Constitutional quality gate evaluating specifications using rubric-based GPT-5 scoring
- **Rubric**: 4-dimension evaluation framework (clarity, measurability, completeness, actionability)
- **REVISE Verdict**: Score 2.0-3.4, triggers auto-rewrite or manual clarification
- **REJECT Verdict**: Score <2.0, immediate rejection, no auto-rewrite
- **Constitutional Threshold**: 3.5/5.0 score, REVISE below, ACCEPT above

### Appendix B: References

- **ADR-003**: Automated Merge Enforcement (Article III foundation)
- **Article I**: Complete Context Before Action (retry logic for API calls)
- **Article II**: 100% Verification and Stability (test coverage requirements)
- **Article III**: Automated Merge Enforcement (zero manual override)
- **Article IV**: Continuous Learning and Improvement (VectorStore pattern storage)
- **Article V**: Spec-Driven Development (follows spec-006)

### Appendix C: Related Documents

- **Spec**: `specs/spec-004-quality-feedback-loop.md` (quality signals for adaptive router)
- **Plan**: `plan-006-slop-immunity-protocol.md` (to be created after spec approval)
- **Mission**: `missions/leap_6_bulletproof_orchestrator.json` (Leap 6 Phase 1 tasks)

---

## Revision History

| Version | Date       | Author       | Changes                                              |
|---------|------------|--------------|------------------------------------------------------|
| 1.0     | 2025-10-11 | PlannerAgent | Initial specification with three-stage integration   |

---

*"Precision is the foundation of autonomy. Vagueness is the enemy of excellence."* - Slop Immunity Protocol Principle
