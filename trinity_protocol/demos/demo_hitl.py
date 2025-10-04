"""
Demo: Trinity Protocol Human-in-the-Loop (HITL) System

Demonstrates the complete question-answer flow:
1. ARCHITECT detects pattern → Formulates question
2. Submit to human_review_queue
3. QuestionDelivery presents to Alex (terminal)
4. Alex responds YES/NO/LATER
5. ResponseHandler routes based on decision:
   - YES → execution_queue (EXECUTOR picks up)
   - NO → telemetry_stream (learning only)
   - LATER → telemetry_stream + schedule reminder
6. PreferenceLearning analyzes responses

Run this to see HITL in action!

Usage:
    python trinity_protocol/demos/demo_hitl.py
    python trinity_protocol/demos/demo_hitl.py auto  # Automated mode
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.hitl_protocol import HumanReviewQueue
from shared.message_bus import MessageBus
from trinity_protocol.core.models import (
    DetectedPattern,
    HumanResponse,
    HumanReviewRequest,
    PatternType,
)
from trinity_protocol.experimental.response_handler import ResponseHandler


async def demo_hitl_flow():
    """
    Demonstrate complete HITL workflow.
    """
    print("\n" + "=" * 70)
    print("TRINITY PROTOCOL: HITL System Demo")
    print("=" * 70)
    print("\nThis demo shows the question-answer flow.")
    print("You'll be asked a question, and your response will be routed appropriately.")
    print("\n" + "-" * 70 + "\n")

    # Setup infrastructure
    temp_dir = Path("/tmp/trinity_hitl_demo")
    temp_dir.mkdir(exist_ok=True)

    message_bus = MessageBus(db_path=str(temp_dir / "demo_bus.db"))
    review_queue = HumanReviewQueue(
        message_bus=message_bus, db_path=str(temp_dir / "demo_queue.db")
    )
    response_handler = ResponseHandler(message_bus=message_bus, review_queue=review_queue)

    # Create sample pattern (simulating WITNESS detection)
    pattern = DetectedPattern(
        pattern_id="demo-pattern-001",
        pattern_type=PatternType.RECURRING_TOPIC,
        topic="HITL System Development",
        confidence=0.92,
        mention_count=5,
        first_mention=datetime.now() - timedelta(hours=6),
        last_mention=datetime.now() - timedelta(minutes=10),
        context_summary=(
            "Alex has mentioned wanting a better question-answer system "
            "for proactive assistance. Mentioned 5 times in the last 6 hours."
        ),
        keywords=["hitl", "questions", "proactive", "assistance"],
        sentiment="positive",
        urgency="high",
    )

    # Create question (simulating ARCHITECT formulation)
    question = HumanReviewRequest(
        correlation_id="demo-corr-001",
        question_text=(
            "I've noticed you mentioning HITL improvements 5 times today. "
            "Would you like me to implement the terminal-based question delivery system?"
        ),
        question_type="high_value",
        pattern_context=pattern,
        priority=8,
        expires_at=datetime.now() + timedelta(hours=24),
        suggested_action=("Build terminal delivery, response handler, and preference learning"),
    )

    # Submit question to queue
    print("ARCHITECT: Submitting question to human_review_queue...")
    question_id = await review_queue.submit_question(question)
    print(f"✓ Question submitted (ID: {question_id})")

    # Simulate question delivery (synchronous for demo)
    print("\n" + "=" * 70)
    print("QUESTION DELIVERY: Presenting question to Alex")
    print("=" * 70)

    # Get question from queue
    question_obj = await review_queue.get_question_by_correlation("demo-corr-001")
    if not question_obj:
        print("Error: Question not found!")
        return

    # Display question
    print(f"\nQuestion Type: {question_obj.question_type.upper()}")
    print(f"Priority: {question_obj.priority}/10")
    print(f"\nQuestion: {question_obj.question_text}")
    print(f"\nSuggested Action: {question_obj.suggested_action}")
    print("\nPattern Context:")
    print(f"  Topic: {question_obj.pattern_context.topic}")
    print(f"  Confidence: {question_obj.pattern_context.confidence:.2f}")
    print(f"  Mentions: {question_obj.pattern_context.mention_count}")
    print(f"  Summary: {question_obj.pattern_context.context_summary}")

    # Get user response
    print("\n" + "-" * 70)
    print("\nYour response (YES/NO/LATER): ", end="", flush=True)
    response_type = input().strip().upper()

    if response_type not in ["YES", "NO", "LATER"]:
        print(f"Invalid response: {response_type}")
        return

    print("Optional comment (press Enter to skip): ", end="", flush=True)
    comment_text = input().strip()
    comment = comment_text if comment_text else None

    # Create response
    response_time = (datetime.now() - question_obj.created_at).total_seconds()
    response = HumanResponse(
        correlation_id="demo-corr-001",
        response_type=response_type,
        comment=comment,
        response_time_seconds=response_time,
    )

    # Process response
    print(f"\nRESPONSE HANDLER: Processing {response_type} response...")
    await response_handler.process_response(question_id, response)

    # Show routing result
    print("\n" + "=" * 70)
    print("ROUTING RESULT")
    print("=" * 70)

    if response_type == "YES":
        print("\n✓ Task published to execution_queue")
        print("  EXECUTOR will pick up this task and implement the feature")

        # Verify in queue
        exec_pending = await message_bus.get_pending_count("execution_queue")
        print(f"  Pending tasks in execution_queue: {exec_pending}")

    elif response_type == "NO":
        print("\n✗ Task NOT published to execution_queue")
        print("  Your NO decision is respected")
        print("  Learning signal published to telemetry_stream")

        if comment:
            print(f"  Reason: {comment}")

    elif response_type == "LATER":
        print("\n⏰ Task deferred")
        print("  Reminder will be scheduled for later")
        print("  Learning signal published to telemetry_stream")

    # Show learning signal
    telem_pending = await message_bus.get_pending_count("telemetry_stream")
    print(f"  Learning signals in telemetry_stream: {telem_pending}")

    # Show queue statistics
    print("\n" + "=" * 70)
    print("QUEUE STATISTICS")
    print("=" * 70)

    stats = review_queue.get_stats()
    print(f"\nTotal Questions: {stats['total_questions']}")
    print(f"By Status: {stats['by_status']}")
    print(f"By Response: {stats['by_response']}")
    print(f"Acceptance Rate: {stats['acceptance_rate']:.1%}")
    print(f"Avg Response Time: {stats['avg_response_time_seconds']:.1f}s")

    # Cleanup
    review_queue.close()
    message_bus.close()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print(f"\nResponse time: {response_time:.1f} seconds")
    print(f"Database files created in: {temp_dir}")
    print("\n")


async def demo_automated_flow():
    """
    Demonstrate automated flow without user input (for testing).
    """
    print("\n" + "=" * 70)
    print("TRINITY PROTOCOL: Automated HITL Demo")
    print("=" * 70)
    print("\nThis demo simulates the complete flow with automated responses.")
    print("\n" + "-" * 70 + "\n")

    # Setup
    temp_dir = Path("/tmp/trinity_hitl_auto_demo")
    temp_dir.mkdir(exist_ok=True)

    message_bus = MessageBus(db_path=str(temp_dir / "auto_bus.db"))
    review_queue = HumanReviewQueue(
        message_bus=message_bus, db_path=str(temp_dir / "auto_queue.db")
    )
    response_handler = ResponseHandler(message_bus=message_bus, review_queue=review_queue)

    # Create multiple test scenarios
    scenarios = [
        {
            "question": "Implement feature X?",
            "type": "high_value",
            "priority": 8,
            "response": "YES",
            "comment": "Great idea!",
        },
        {
            "question": "Refactor module Y?",
            "type": "low_stakes",
            "priority": 4,
            "response": "NO",
            "comment": "Not now, too busy",
        },
        {
            "question": "Add integration Z?",
            "type": "high_value",
            "priority": 7,
            "response": "LATER",
            "comment": "Ask me tomorrow",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}/{len(scenarios)}: {scenario['question']}")

        # Create pattern
        pattern = DetectedPattern(
            pattern_id=f"auto-pattern-{i:03d}",
            pattern_type=PatternType.FEATURE_REQUEST,
            topic=f"Feature {i}",
            confidence=0.85,
            mention_count=3,
            first_mention=datetime.now() - timedelta(hours=2),
            last_mention=datetime.now(),
            context_summary=f"Context for feature {i}",
            keywords=["feature", "improvement"],
        )

        # Create question
        question = HumanReviewRequest(
            correlation_id=f"auto-corr-{i:03d}",
            question_text=scenario["question"],
            question_type=scenario["type"],
            pattern_context=pattern,
            priority=scenario["priority"],
            expires_at=datetime.now() + timedelta(hours=24),
        )

        # Submit
        question_id = await review_queue.submit_question(question)
        print(f"  ✓ Question {question_id} submitted")

        # Respond
        response = HumanResponse(
            correlation_id=f"auto-corr-{i:03d}",
            response_type=scenario["response"],
            comment=scenario["comment"],
            response_time_seconds=30.0 + (i * 10),
        )

        await response_handler.process_response(question_id, response)
        print(f"  ✓ Response: {scenario['response']} - '{scenario['comment']}'")

    # Show final statistics
    print("\n" + "=" * 70)
    print("FINAL STATISTICS")
    print("=" * 70)

    stats = review_queue.get_stats()
    print(f"\nTotal Questions: {stats['total_questions']}")
    print(f"Acceptance Rate: {stats['acceptance_rate']:.1%}")
    print("Response Rate: 100% (all answered)")
    print(f"Avg Response Time: {stats['avg_response_time_seconds']:.1f}s")

    print("\nBreakdown:")
    print(f"  YES: {stats['by_response'].get('YES', 0)}")
    print(f"  NO: {stats['by_response'].get('NO', 0)}")
    print(f"  LATER: {stats['by_response'].get('LATER', 0)}")

    # Verify routing
    exec_pending = await message_bus.get_pending_count("execution_queue")
    telem_pending = await message_bus.get_pending_count("telemetry_stream")

    print("\nRouting:")
    print(f"  Execution Queue: {exec_pending} tasks")
    print(f"  Telemetry Stream: {telem_pending} learning signals")

    # Cleanup
    review_queue.close()
    message_bus.close()

    print("\n" + "=" * 70)
    print("Automated Demo Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        # Automated demo (no user input)
        asyncio.run(demo_automated_flow())
    else:
        # Interactive demo (user input required)
        asyncio.run(demo_hitl_flow())
