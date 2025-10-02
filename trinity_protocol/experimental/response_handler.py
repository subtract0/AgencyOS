"""
Response Handler for Trinity Protocol HITL System

Processes user responses (YES/NO/LATER) and routes them appropriately:
- YES: Route to EXECUTOR for immediate action
- NO: Store for learning, do not execute
- LATER: Schedule reminder, do not execute immediately

Constitutional Compliance:
- Article II: Strict typing - Pydantic models, no Dict[Any, Any]
- Article IV: Continuous learning - track all responses
- Privacy: Respect user decisions, never bypass NO responses

Flow:
1. Receive response from QuestionDelivery
2. Validate correlation ID matches question
3. Route based on response_type:
   - YES → execution_queue (EXECUTOR picks up)
   - NO → telemetry_stream (learning agent analyzes)
   - LATER → telemetry_stream + schedule reminder
4. Mark question as answered in review queue
5. Calculate and store response time for learning
"""

from datetime import datetime, timedelta
from typing import Optional

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.human_review_queue import HumanReviewQueue
from trinity_protocol.core.models.hitl import HumanResponse


class ResponseHandler:
    """
    Handler for processing user responses to questions.

    Routes responses to appropriate queues based on decision type.
    """

    def __init__(
        self,
        message_bus: MessageBus,
        review_queue: HumanReviewQueue,
        execution_queue_name: str = "execution_queue",
        telemetry_queue_name: str = "telemetry_stream",
        later_delay_hours: int = 4
    ):
        """
        Initialize response handler.

        Args:
            message_bus: MessageBus for routing
            review_queue: HumanReviewQueue for question lookup
            execution_queue_name: Queue for approved tasks
            telemetry_queue_name: Queue for learning signals
            later_delay_hours: Hours to wait before re-asking LATER questions
        """
        self.message_bus = message_bus
        self.review_queue = review_queue
        self.execution_queue_name = execution_queue_name
        self.telemetry_queue_name = telemetry_queue_name
        self.later_delay_hours = later_delay_hours

    async def process_response(
        self,
        question_id: int,
        response: HumanResponse
    ) -> None:
        """
        Process a user response.

        Args:
            question_id: Question ID from review queue
            response: HumanResponse with user's decision

        Raises:
            ValueError: If question not found or correlation ID mismatch
        """
        # Get original question
        question = await self._get_question(question_id)
        if not question:
            raise ValueError(f"Question with ID {question_id} not found")

        # Validate correlation ID
        if question.correlation_id != response.correlation_id:
            raise ValueError(
                f"Correlation ID mismatch: question has '{question.correlation_id}', "
                f"response has '{response.correlation_id}'"
            )

        # Calculate response time if not provided
        if response.response_time_seconds is None:
            response_time = (response.responded_at - question.created_at).total_seconds()
            # Create new response with calculated time
            response = HumanResponse(
                correlation_id=response.correlation_id,
                response_type=response.response_type,
                comment=response.comment,
                responded_at=response.responded_at,
                response_time_seconds=response_time
            )

        # Mark question as answered
        await self.review_queue.mark_answered(question_id, response)

        # Route based on response type
        if response.response_type == "YES":
            await self._handle_yes_response(question, response)
        elif response.response_type == "NO":
            await self._handle_no_response(question, response)
        elif response.response_type == "LATER":
            await self._handle_later_response(question, response)
        else:
            raise ValueError(f"Unknown response type: {response.response_type}")

    async def _handle_yes_response(
        self,
        question,
        response: HumanResponse
    ) -> None:
        """
        Handle YES response: route to EXECUTOR.

        Args:
            question: Original HumanReviewRequest
            response: HumanResponse with YES decision
        """
        # Prepare task for EXECUTOR (all values must be JSON serializable)
        pattern_dict = question.pattern_context.model_dump(mode='json')

        task_spec = {
            "correlation_id": question.correlation_id,
            "approved": True,
            "question_text": question.question_text,
            "suggested_action": question.suggested_action,
            "pattern_context": pattern_dict,
            "user_comment": response.comment,
            "response_time_seconds": response.response_time_seconds,
            "approved_at": response.responded_at.isoformat()
        }

        # Publish to execution queue
        await self.message_bus.publish(
            queue_name=self.execution_queue_name,
            message=task_spec,
            priority=question.priority,
            correlation_id=question.correlation_id
        )

        # Also publish to telemetry for learning (acceptance signal)
        await self._publish_learning_signal(
            correlation_id=question.correlation_id,
            event_type="response_yes",
            question=question,
            response=response
        )

    async def _handle_no_response(
        self,
        question,
        response: HumanResponse
    ) -> None:
        """
        Handle NO response: store for learning, do not execute.

        Args:
            question: Original HumanReviewRequest
            response: HumanResponse with NO decision
        """
        # Publish to telemetry for learning (rejection signal)
        await self._publish_learning_signal(
            correlation_id=question.correlation_id,
            event_type="response_no",
            question=question,
            response=response,
            additional_data={
                "reason": response.comment or "No reason provided",
                "learn_from_rejection": True
            }
        )

        # NOTE: Intentionally do NOT publish to execution_queue
        # This respects the user's NO decision

    async def _handle_later_response(
        self,
        question,
        response: HumanResponse
    ) -> None:
        """
        Handle LATER response: schedule reminder, do not execute immediately.

        Args:
            question: Original HumanReviewRequest
            response: HumanResponse with LATER decision
        """
        # Publish to telemetry for learning (deferral signal)
        reminder_time = datetime.now() + timedelta(hours=self.later_delay_hours)

        await self._publish_learning_signal(
            correlation_id=question.correlation_id,
            event_type="response_later",
            question=question,
            response=response,
            additional_data={
                "reminder_scheduled_for": reminder_time.isoformat(),
                "delay_hours": self.later_delay_hours,
                "reason": response.comment or "Ask again later"
            }
        )

        # NOTE: In full implementation, would also publish to a reminders queue
        # or store in a scheduler database for future resubmission

    async def _publish_learning_signal(
        self,
        correlation_id: str,
        event_type: str,
        question,
        response: HumanResponse,
        additional_data: Optional[dict] = None
    ) -> None:
        """
        Publish learning signal to telemetry stream.

        Args:
            correlation_id: Correlation ID
            event_type: Type of event (response_yes, response_no, response_later)
            question: Original HumanReviewRequest
            response: HumanResponse
            additional_data: Optional additional data
        """
        learning_signal = {
            "event_type": event_type,
            "correlation_id": correlation_id,
            "question_type": question.question_type,
            "question_priority": question.priority,
            "pattern_type": question.pattern_context.pattern_type,
            "pattern_topic": question.pattern_context.topic,
            "response_type": response.response_type,
            "response_time_seconds": response.response_time_seconds,
            "timestamp": response.responded_at.isoformat()
        }

        if additional_data:
            learning_signal.update(additional_data)

        await self.message_bus.publish(
            queue_name=self.telemetry_queue_name,
            message=learning_signal,
            priority=5,  # Medium priority for learning signals
            correlation_id=correlation_id
        )

    async def _get_question(self, question_id: int):
        """
        Get question from review queue by ID.

        Args:
            question_id: Question ID

        Returns:
            HumanReviewRequest or None if not found
        """
        # Query database for question
        if not self.review_queue.conn:
            raise RuntimeError("Review queue database not initialized")

        cursor = self.review_queue.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM questions
            WHERE id = ?
        """, (question_id,))

        row = cursor.fetchone()
        if not row:
            return None

        # Convert to HumanReviewRequest
        from trinity_protocol.core.models.patterns import DetectedPattern

        pattern_context = DetectedPattern.model_validate_json(row['pattern_context'])

        from trinity_protocol.core.models.hitl import HumanReviewRequest

        question = HumanReviewRequest(
            correlation_id=row['correlation_id'],
            question_text=row['question_text'],
            question_type=row['question_type'],
            pattern_context=pattern_context,
            priority=row['priority'],
            expires_at=datetime.fromisoformat(row['expires_at']),
            created_at=datetime.fromisoformat(row['created_at']),
            suggested_action=row['suggested_action']
        )

        return question
