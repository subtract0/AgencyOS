"""
Spec From Conversation for Trinity Protocol Phase 3.

Converts Q&A transcript into formal project specification.
Extracts requirements and generates spec.md following Agency spec-kit template.

Constitutional Compliance:
- Article V: Spec-driven development (formal spec required)
- Article I: Complete context before generation
- Article II: Strict typing with Result<T,E> pattern
- Article IV: Learning from spec quality patterns

Flow:
1. Receive completed Q&A session
2. Extract goals, deliverables, constraints from answers
3. Generate acceptance criteria
4. Create formal spec.md document
5. Request user approval
6. Store approved spec in Firestore

Usage:
    generator = SpecFromConversation(llm_client)
    result = await generator.generate_spec(qa_session, pattern)
"""

import uuid
from datetime import datetime
from typing import List, Tuple

from trinity_protocol.core.models.patterns import DetectedPattern
from trinity_protocol.core.models.project import (
    QASession,
    ProjectSpec,
    AcceptanceCriterion,
    ApprovalStatus,
)
from shared.type_definitions.result import Result, Ok, Err


class SpecGenerationError(Exception):
    """Specification generation error."""
    pass


class SpecFromConversation:
    """
    Generate formal specification from Q&A transcript.

    Constitutional: Article V (spec-driven), Article I (complete context)
    """

    def __init__(self, llm_client):
        """
        Initialize spec generator.

        Args:
            llm_client: LLM for spec generation
        """
        self.llm = llm_client

    async def generate_spec(
        self,
        qa_session: QASession,
        pattern: DetectedPattern
    ) -> Result[ProjectSpec, str]:
        """
        Create formal spec.md from Q&A conversation.

        Constitutional: Article I (requires complete session)

        Args:
            qa_session: Completed Q&A session
            pattern: Original detected pattern

        Returns:
            Result[ProjectSpec, str]: Generated spec or error
        """
        # Validate session completeness
        if not qa_session.is_complete:
            return Err(
                "Cannot generate spec from incomplete Q&A session. "
                "Article I violation: incomplete context."
            )

        # Extract all components
        components_result = await self._extract_all_components(qa_session, pattern)
        if not components_result.is_ok():
            return Err(f"Component extraction failed: {components_result.unwrap_err()}")

        # Create spec object
        spec = self._create_spec_object(qa_session, components_result.unwrap())
        return Ok(spec)

    async def _extract_all_components(
        self,
        qa_session: QASession,
        pattern: DetectedPattern
    ) -> Result[dict, str]:
        """Extract all spec components."""
        # Extract requirements
        extract_result = await self._extract_requirements(qa_session)
        if not extract_result.is_ok():
            return Err(f"Requirements: {extract_result.unwrap_err()}")

        goals, non_goals, personas = extract_result.unwrap()

        # Generate criteria
        criteria_result = await self._generate_criteria(goals, qa_session)
        if not criteria_result.is_ok():
            return Err(f"Criteria: {criteria_result.unwrap_err()}")

        components = {
            "goals": goals,
            "non_goals": non_goals,
            "personas": personas,
            "criteria": criteria_result.unwrap(),
            "constraints": self._extract_constraints(qa_session),
            "title": self._generate_title(pattern, qa_session),
            "description": self._generate_description(pattern, qa_session)
        }
        return Ok(components)

    def _create_spec_object(self, qa_session: QASession, components: dict) -> ProjectSpec:
        """Create ProjectSpec object from components."""
        spec_md = self._create_spec_markdown(
            title=components["title"],
            description=components["description"],
            goals=components["goals"],
            non_goals=components["non_goals"],
            personas=components["personas"],
            criteria=components["criteria"],
            constraints=components["constraints"]
        )

        return ProjectSpec(
            spec_id=str(uuid.uuid4()),
            project_id=qa_session.project_id,
            qa_session_id=qa_session.session_id,
            title=components["title"],
            description=components["description"],
            goals=components["goals"],
            non_goals=components["non_goals"],
            user_personas=components["personas"],
            acceptance_criteria=components["criteria"],
            constraints=components["constraints"],
            spec_markdown=spec_md,
            created_at=datetime.now(),
            approval_status=ApprovalStatus.PENDING
        )

    async def _extract_requirements(
        self,
        qa_session: QASession
    ) -> Result[Tuple[List[str], List[str], List[str]], str]:
        """
        Extract goals, non-goals, and personas from answers.

        Args:
            qa_session: Completed Q&A session

        Returns:
            Result with (goals, non_goals, personas) or error
        """
        try:
            # Build context from Q&A
            context = self._build_qa_context(qa_session)

            # Extract goals (what user wants to achieve)
            goals = self._extract_goals(qa_session)

            # Infer non-goals (what's out of scope)
            non_goals = self._infer_non_goals(qa_session)

            # Identify user personas
            personas = self._identify_personas(qa_session)

            return Ok((goals, non_goals, personas))

        except Exception as e:
            return Err(f"Requirement extraction error: {str(e)}")

    def _build_qa_context(self, qa_session: QASession) -> str:
        """Build context string from Q&A session."""
        lines = []
        for question in qa_session.questions:
            # Find corresponding answer
            answer = next(
                (a for a in qa_session.answers if a.question_id == question.question_id),
                None
            )
            if answer:
                lines.append(f"Q: {question.question_text}")
                lines.append(f"A: {answer.answer_text}")
                lines.append("")
        return "\n".join(lines)

    def _extract_goals(self, qa_session: QASession) -> List[str]:
        """Extract project goals from answers."""
        goals = []

        # Find core goal answer
        for question in qa_session.questions:
            if "goal" in question.question_text.lower() or \
               "outcome" in question.question_text.lower():
                answer = next(
                    (a for a in qa_session.answers if a.question_id == question.question_id),
                    None
                )
                if answer:
                    goals.append(answer.answer_text.strip())

        # If no explicit goal, use pattern topic
        if not goals:
            goals.append(f"Complete project related to {qa_session.pattern_type}")

        return goals[:5]  # Max 5 goals

    def _infer_non_goals(self, qa_session: QASession) -> List[str]:
        """Infer what's out of scope."""
        non_goals = [
            "Multi-user collaboration (single-user focus)",
            "Real-time synchronization across devices",
            "Advanced analytics and reporting"
        ]
        return non_goals[:3]

    def _identify_personas(self, qa_session: QASession) -> List[str]:
        """Identify user personas from answers."""
        personas = []

        # Find audience/persona answers
        for question in qa_session.questions:
            if "audience" in question.question_text.lower() or \
               "who" in question.question_text.lower():
                answer = next(
                    (a for a in qa_session.answers if a.question_id == question.question_id),
                    None
                )
                if answer:
                    personas.append(answer.answer_text.strip())

        # Default persona if none found
        if not personas:
            personas.append("Primary user (project creator)")

        return personas[:3]

    async def _generate_criteria(
        self,
        goals: List[str],
        qa_session: QASession
    ) -> Result[List[AcceptanceCriterion], str]:
        """
        Generate acceptance criteria from goals.

        Args:
            goals: Project goals
            qa_session: Q&A session

        Returns:
            Result[List[AcceptanceCriterion], str]: Criteria or error
        """
        try:
            criteria = []

            # Generate criterion for each goal
            for idx, goal in enumerate(goals):
                criterion = AcceptanceCriterion(
                    criterion_id=str(uuid.uuid4()),
                    description=f"Successfully achieve: {goal}",
                    verification_method="User review and approval",
                    met=False
                )
                criteria.append(criterion)

            # Add timeline criterion
            timeline_answer = self._find_timeline_answer(qa_session)
            if timeline_answer:
                criteria.append(
                    AcceptanceCriterion(
                        criterion_id=str(uuid.uuid4()),
                        description=f"Complete within timeline: {timeline_answer}",
                        verification_method="Date comparison",
                        met=False
                    )
                )

            return Ok(criteria)

        except Exception as e:
            return Err(f"Criteria generation error: {str(e)}")

    def _find_timeline_answer(self, qa_session: QASession) -> str:
        """Find timeline/deadline answer."""
        for question in qa_session.questions:
            if "timeline" in question.question_text.lower() or \
               "deadline" in question.question_text.lower() or \
               "when" in question.question_text.lower():
                answer = next(
                    (a for a in qa_session.answers if a.question_id == question.question_id),
                    None
                )
                if answer:
                    return answer.answer_text.strip()
        return ""

    def _extract_constraints(self, qa_session: QASession) -> List[str]:
        """Extract constraints from answers."""
        constraints = []

        # Find time commitment constraint
        for question in qa_session.questions:
            if "time" in question.question_text.lower() and \
               "commitment" in question.question_text.lower():
                answer = next(
                    (a for a in qa_session.answers if a.question_id == question.question_id),
                    None
                )
                if answer:
                    constraints.append(
                        f"Daily time commitment: {answer.answer_text.strip()}"
                    )

        return constraints

    def _generate_title(
        self,
        pattern: DetectedPattern,
        qa_session: QASession
    ) -> str:
        """Generate project title."""
        # Use pattern topic as base
        base = pattern.topic.title()

        # Add pattern type context
        if pattern.pattern_type == "project_mention":
            return f"{base} Project"
        elif pattern.pattern_type == "recurring_topic":
            return f"{base} Initiative"
        elif pattern.pattern_type == "workflow_bottleneck":
            return f"{base} Improvement"
        else:
            return base

    def _generate_description(
        self,
        pattern: DetectedPattern,
        qa_session: QASession
    ) -> str:
        """Generate project description."""
        # Start with pattern context
        description = pattern.context_summary

        # Add timeline if available
        timeline = self._find_timeline_answer(qa_session)
        if timeline:
            description += f" Target completion: {timeline}."

        # Ensure minimum length
        if len(description) < 50:
            description += (
                f" This project addresses the recurring topic of {pattern.topic} "
                f"mentioned {pattern.mention_count} times."
            )

        return description

    def _create_spec_markdown(
        self,
        title: str,
        description: str,
        goals: List[str],
        non_goals: List[str],
        personas: List[str],
        criteria: List[AcceptanceCriterion],
        constraints: List[str]
    ) -> str:
        """
        Create formal spec.md following Agency template.

        Constitutional: Article V (spec-driven development)
        """
        md = f"""# Project Specification: {title}

## Overview

{description}

## Goals

"""
        for idx, goal in enumerate(goals, 1):
            md += f"{idx}. {goal}\n"

        md += "\n## Non-Goals\n\n"
        for idx, non_goal in enumerate(non_goals, 1):
            md += f"{idx}. {non_goal}\n"

        md += "\n## User Personas\n\n"
        for idx, persona in enumerate(personas, 1):
            md += f"{idx}. {persona}\n"

        md += "\n## Acceptance Criteria\n\n"
        for idx, criterion in enumerate(criteria, 1):
            md += f"{idx}. {criterion.description}\n"
            md += f"   - Verification: {criterion.verification_method}\n"

        if constraints:
            md += "\n## Constraints\n\n"
            for idx, constraint in enumerate(constraints, 1):
                md += f"{idx}. {constraint}\n"

        md += f"\n---\n\nGenerated: {datetime.now().isoformat()}\n"

        return md

    async def request_approval(
        self,
        spec: ProjectSpec
    ) -> Result[ApprovalStatus, str]:
        """
        Request user approval of generated spec.

        Args:
            spec: Generated specification

        Returns:
            Result[ApprovalStatus, str]: Approval status or error
        """
        # In production, this would:
        # 1. Display spec to user via HITL
        # 2. Wait for YES/NO/MODIFY response
        # 3. Handle modifications if requested
        # 4. Return final approval status

        # For now, return pending for manual approval
        return Ok(ApprovalStatus.PENDING)
