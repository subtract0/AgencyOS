"""
Question Delivery System for Trinity Protocol HITL

Delivers questions to Alex via terminal (MVP) with future extension
points for web interface and voice assistant.

Constitutional Compliance:
- Article II: Strict typing - Pydantic models
- Privacy: Non-intrusive, respectful of focus time
- User-centric: Clear, actionable questions

Flow:
1. Subscribe to human_review_queue
2. Present question to user via terminal (MVP)
3. Capture response (YES/NO/LATER + optional comment)
4. Route to ResponseHandler for processing

Future Extensions:
- Web interface delivery
- Voice assistant integration
- Slack/Discord notifications
- Context-aware timing (quiet hours, focus mode)
"""

import asyncio
from typing import Optional
from datetime import datetime

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.human_review_queue import HumanReviewQueue
from trinity_protocol.response_handler import ResponseHandler
from trinity_protocol.core.models.hitl import HumanResponse, QuestionDeliveryConfig


class QuestionDelivery:
    """
    Terminal-based question delivery system (MVP).

    Presents questions to Alex via terminal and captures responses.
    """

    def __init__(
        self,
        message_bus: MessageBus,
        review_queue: HumanReviewQueue,
        response_handler: ResponseHandler,
        config: Optional[QuestionDeliveryConfig] = None
    ):
        """
        Initialize question delivery system.

        Args:
            message_bus: MessageBus for subscribing to questions
            review_queue: HumanReviewQueue for question lookup
            response_handler: ResponseHandler for routing responses
            config: Configuration (delivery method, rate limits, quiet hours)
        """
        self.message_bus = message_bus
        self.review_queue = review_queue
        self.response_handler = response_handler
        self.config = config or QuestionDeliveryConfig()
        self._running = False
        self._questions_asked_this_hour = 0
        self._last_hour_reset = datetime.now()

    async def run(self) -> None:
        """
        Main loop: subscribe to human_review_queue and deliver questions.

        Respects rate limits and quiet hours configured in config.
        """
        self._running = True

        try:
            async for message in self.message_bus.subscribe("human_review_queue"):
                if not self._running:
                    break

                question_id = message.get("question_id")
                if not question_id:
                    # Acknowledge and skip invalid messages
                    await self.message_bus.ack(message["_message_id"])
                    continue

                # Check rate limits
                if not self._should_ask_now():
                    # Acknowledge but skip (question remains in queue)
                    await self.message_bus.ack(message["_message_id"])
                    continue

                # Deliver question and get response
                try:
                    await self._deliver_question(question_id)
                    self._questions_asked_this_hour += 1

                except Exception as e:
                    # Log error but continue processing
                    print(f"Error delivering question {question_id}: {e}")

                finally:
                    # Acknowledge message
                    await self.message_bus.ack(message["_message_id"])

        except asyncio.CancelledError:
            pass  # Expected on shutdown

    async def stop(self) -> None:
        """Stop the delivery system gracefully."""
        self._running = False

    def _should_ask_now(self) -> bool:
        """
        Check if we should ask a question now.

        Respects:
        - Rate limits (max questions per hour)
        - Quiet hours (night time)

        Returns:
            True if question should be asked, False otherwise
        """
        now = datetime.now()

        # Reset hourly counter
        if (now - self._last_hour_reset).total_seconds() >= 3600:
            self._questions_asked_this_hour = 0
            self._last_hour_reset = now

        # Check rate limit
        if self._questions_asked_this_hour >= self.config.max_questions_per_hour:
            return False

        # Check quiet hours
        current_hour = now.hour
        if self.config.quiet_hours_start and self.config.quiet_hours_end:
            start = self.config.quiet_hours_start
            end = self.config.quiet_hours_end

            if start > end:  # Wraps around midnight (e.g., 22:00 - 08:00)
                if current_hour >= start or current_hour < end:
                    return False
            else:  # Normal range (e.g., 02:00 - 08:00)
                if start <= current_hour < end:
                    return False

        return True

    async def _deliver_question(self, question_id: int) -> None:
        """
        Deliver a single question via terminal and capture response.

        Args:
            question_id: Question ID to deliver
        """
        # Get question from review queue
        question = await self._get_question(question_id)
        if not question:
            print(f"Question {question_id} not found")
            return

        # Present question to user
        self._print_question(question)

        # Get response (would be async input in full implementation)
        # For MVP, we'll use synchronous input
        response = await self._get_user_response(question)

        if response:
            # Process response
            await self.response_handler.process_response(question_id, response)

    def _print_question(self, question) -> None:
        """
        Print question to terminal in clear, readable format.

        Args:
            question: HumanReviewRequest to display
        """
        print("\n" + "=" * 70)
        print("TRINITY PROTOCOL: Human Review Required")
        print("=" * 70)
        print(f"\nQuestion Type: {question.question_type.upper()}")
        print(f"Priority: {question.priority}/10")
        print(f"\nQuestion: {question.question_text}")

        if question.suggested_action:
            print(f"\nSuggested Action: {question.suggested_action}")

        print(f"\nPattern Context:")
        print(f"  Topic: {question.pattern_context.topic}")
        print(f"  Confidence: {question.pattern_context.confidence:.2f}")
        print(f"  Mentions: {question.pattern_context.mention_count}")

        print(f"\nExpires: {question.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "-" * 70)

    async def _get_user_response(self, question) -> Optional[HumanResponse]:
        """
        Get user response via terminal input.

        Args:
            question: HumanReviewRequest being responded to

        Returns:
            HumanResponse or None if input invalid
        """
        print("\nYour response (YES/NO/LATER): ", end="", flush=True)

        # In async context, we'd use aioconsole or similar
        # For MVP, using synchronous input in thread pool
        loop = asyncio.get_event_loop()
        response_type = await loop.run_in_executor(None, input)

        response_type = response_type.strip().upper()

        if response_type not in ["YES", "NO", "LATER"]:
            print(f"Invalid response: {response_type}. Skipping question.")
            return None

        # Get optional comment
        print("Optional comment (press Enter to skip): ", end="", flush=True)
        comment_text = await loop.run_in_executor(None, input)
        comment = comment_text.strip() if comment_text.strip() else None

        # Calculate response time
        response_time = (datetime.now() - question.created_at).total_seconds()

        response = HumanResponse(
            correlation_id=question.correlation_id,
            response_type=response_type,
            comment=comment,
            response_time_seconds=response_time
        )

        return response

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
        from trinity_protocol.core.models.hitl import HumanReviewRequest

        pattern_context = DetectedPattern.model_validate_json(row['pattern_context'])

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


class WebQuestionDelivery(QuestionDelivery):
    """
    Future: Web-based question delivery via FastAPI/WebSockets.

    Extension point for delivering questions via web interface
    with richer UI and better UX.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Future: Initialize WebSocket connections, FastAPI app, etc.
        raise NotImplementedError("Web delivery not yet implemented")


class VoiceQuestionDelivery(QuestionDelivery):
    """
    Future: Voice assistant delivery via Whisper/TTS.

    Extension point for delivering questions via voice with
    natural language response capture.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Future: Initialize voice recognition, TTS, etc.
        raise NotImplementedError("Voice delivery not yet implemented")
