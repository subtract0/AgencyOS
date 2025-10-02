"""
Demo: Trinity Protocol Preference Learning System

Demonstrates how the system learns Alex's preferences from response history
and generates actionable recommendations for ARCHITECT.

Shows:
- 2 weeks of realistic simulated response data
- Pattern analysis by topic, time, and question type
- Recommendation generation from learned preferences
- Preference persistence and retrieval

Usage:
    python trinity_protocol/demos/demo_preferences.py
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trinity_protocol.core.models import (
    QuestionType,
    ResponseType,
    TopicCategory,
)
from shared.preference_learning import (
    AlexPreferenceLearner,
    create_response_record,
    PreferenceStore
)


def generate_realistic_response_data() -> List:
    """
    Generate realistic response data simulating 2 weeks of Trinity asking Alex questions.

    Simulates realistic patterns:
    - High acceptance for coaching/book questions during work hours
    - Low acceptance for food/entertainment questions
    - Better responses in morning than evening
    - Better responses early in week than late
    """
    responses = []
    base_time = datetime.now() - timedelta(days=14)

    question_id = 0

    # Pattern 1: Coaching questions (HIGH acceptance: 85%)
    for day in range(14):
        for hour in [9, 11, 14]:  # Morning and early afternoon
            question_id += 1
            timestamp = base_time + timedelta(days=day, hours=hour)

            # 85% YES
            response_type = ResponseType.YES if random.random() < 0.85 else ResponseType.NO

            responses.append(
                create_response_record(
                    question_id=f"q_coaching_{question_id}",
                    question_text="I noticed you've been discussing coaching frameworks. Want me to help organize the patterns into a structured approach?",
                    question_type=QuestionType.HIGH_VALUE,
                    topic_category=TopicCategory.COACHING,
                    response_type=response_type,
                    timestamp=timestamp,
                    response_time_seconds=random.uniform(3.0, 8.0),
                    context_before="Alex mentioned coaching in recent conversation"
                )
            )

    # Pattern 2: Book project questions (HIGH acceptance: 80%)
    for day in range(14):
        if day % 2 == 0:  # Every other day
            question_id += 1
            timestamp = base_time + timedelta(days=day, hours=10)

            response_type = ResponseType.YES if random.random() < 0.80 else ResponseType.NO

            responses.append(
                create_response_record(
                    question_id=f"q_book_{question_id}",
                    question_text="Want to outline the next chapter of the builder's guide?",
                    question_type=QuestionType.HIGH_VALUE,
                    topic_category=TopicCategory.BOOK_PROJECT,
                    response_type=response_type,
                    timestamp=timestamp,
                    response_time_seconds=random.uniform(4.0, 10.0),
                    context_before="Alex working on book project"
                )
            )

    # Pattern 3: Client work questions (MEDIUM acceptance: 60%)
    for day in range(14):
        if day % 3 == 0:  # Every 3 days
            question_id += 1
            timestamp = base_time + timedelta(days=day, hours=13)

            response_type = ResponseType.YES if random.random() < 0.60 else ResponseType.NO

            responses.append(
                create_response_record(
                    question_id=f"q_client_{question_id}",
                    question_text="I can help prepare the client presentation. Should I draft the slides?",
                    question_type=QuestionType.TASK_SUGGESTION,
                    topic_category=TopicCategory.CLIENT_WORK,
                    response_type=response_type,
                    timestamp=timestamp,
                    response_time_seconds=random.uniform(5.0, 12.0),
                    context_before="Alex has client meeting scheduled"
                )
            )

    # Pattern 4: Food suggestions (LOW acceptance: 15%)
    for day in range(14):
        if day % 2 == 0:
            question_id += 1
            timestamp = base_time + timedelta(days=day, hours=12)

            # 15% YES (mostly NO)
            response_type = ResponseType.YES if random.random() < 0.15 else ResponseType.NO

            responses.append(
                create_response_record(
                    question_id=f"q_food_{question_id}",
                    question_text="Want to order sushi for lunch?",
                    question_type=QuestionType.LOW_STAKES,
                    topic_category=TopicCategory.FOOD,
                    response_type=response_type,
                    timestamp=timestamp,
                    response_time_seconds=random.uniform(1.0, 3.0),
                    context_before="Lunchtime"
                )
            )

    # Pattern 5: System improvement questions (HIGH acceptance: 75% - increasing over time)
    for day in range(14):
        if day >= 7:  # Only second week (showing increasing trend)
            question_id += 1
            timestamp = base_time + timedelta(days=day, hours=16)

            response_type = ResponseType.YES if random.random() < 0.85 else ResponseType.NO

            responses.append(
                create_response_record(
                    question_id=f"q_system_{question_id}",
                    question_text="I can optimize the agent orchestration flow. Want me to implement it?",
                    question_type=QuestionType.PROACTIVE_OFFER,
                    topic_category=TopicCategory.SYSTEM_IMPROVEMENT,
                    response_type=response_type,
                    timestamp=timestamp,
                    response_time_seconds=random.uniform(4.0, 9.0),
                    context_before="Trinity observed bottleneck in system"
                )
            )

    # Pattern 6: Entertainment (LOW acceptance: 20%)
    for day in range(14):
        if day % 4 == 0:
            question_id += 1
            timestamp = base_time + timedelta(days=day, hours=20)  # Evening

            response_type = ResponseType.YES if random.random() < 0.20 else ResponseType.IGNORED

            responses.append(
                create_response_record(
                    question_id=f"q_entertainment_{question_id}",
                    question_text="Want to watch a movie tonight?",
                    question_type=QuestionType.LOW_STAKES,
                    topic_category=TopicCategory.ENTERTAINMENT,
                    response_type=response_type,
                    timestamp=timestamp,
                    response_time_seconds=None if response_type == ResponseType.IGNORED else random.uniform(1.0, 5.0),
                    context_before="End of day"
                )
            )

    return responses


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def demo_preference_learning():
    """Run complete preference learning demonstration."""
    print_section("Trinity Protocol: Preference Learning Demo")

    print("This demo simulates 2 weeks of Trinity asking Alex questions and learning")
    print("what he finds helpful vs. what wastes his time.\n")

    # Step 1: Generate realistic data
    print_section("Step 1: Generating 2 Weeks of Response Data")
    responses = generate_realistic_response_data()
    print(f"Generated {len(responses)} question/response pairs")

    # Show sample responses
    print("\nSample responses:")
    for i, r in enumerate(responses[:5]):
        response_type_str = r.response_type if isinstance(r.response_type, str) else r.response_type.value
        print(f"  {i+1}. [{response_type_str}] {r.question_text[:60]}...")

    # Step 2: Store responses
    print_section("Step 2: Storing Responses")
    store = PreferenceStore(use_firestore=False)

    for response in responses:
        store.store_response(response)

    stats = store.get_stats()
    print(f"Stored {stats['response_count']} responses in {stats['backend']} backend")

    # Step 3: Learn preferences
    print_section("Step 3: Analyzing Response Patterns")
    learner = AlexPreferenceLearner(
        min_confidence_threshold=0.6,
        min_sample_size=5,
        trend_window_days=7
    )

    preferences = learner.analyze_responses(responses)

    print(f"Total responses analyzed: {preferences.total_responses}")
    print(f"Overall acceptance rate: {preferences.overall_acceptance_rate:.1%}")

    # Step 4: Show learned patterns
    print_section("Step 4: Learned Preferences")

    print("📊 QUESTION TYPE PREFERENCES:\n")
    for q_type_key, pref in sorted(
        preferences.question_preferences.items(),
        key=lambda x: x[1].acceptance_rate,
        reverse=True
    ):
        q_type_str = pref.question_type if isinstance(pref.question_type, str) else pref.question_type.value
        print(f"  {q_type_str.upper().replace('_', ' ')}:")
        print(f"    Acceptance Rate: {pref.acceptance_rate:.1%}")
        print(f"    Total Asked: {pref.total_asked}")
        print(f"    YES: {pref.yes_count}, NO: {pref.no_count}, LATER: {pref.later_count}, IGNORED: {pref.ignored_count}")
        print(f"    Confidence: {pref.confidence:.1%}")
        if pref.avg_response_time_seconds:
            print(f"    Avg Response Time: {pref.avg_response_time_seconds:.1f}s")
        print()

    print("📅 TIMING PREFERENCES:\n")
    time_order = ["early_morning", "morning", "afternoon", "evening", "night", "late_night"]
    for time_key in time_order:
        if time_key in preferences.timing_preferences:
            pref = preferences.timing_preferences[time_key]
            time_str = pref.time_of_day if isinstance(pref.time_of_day, str) else pref.time_of_day.value
            print(f"  {time_str.upper().replace('_', ' ')}:")
            print(f"    Acceptance Rate: {pref.acceptance_rate:.1%}")
            print(f"    Questions Asked: {pref.total_asked}")
            print(f"    Confidence: {pref.confidence:.1%}")
            print()

    print("📚 TOPIC PREFERENCES:\n")
    for topic_key, pref in sorted(
        preferences.topic_preferences.items(),
        key=lambda x: x[1].acceptance_rate,
        reverse=True
    ):
        topic_str = pref.topic_category if isinstance(pref.topic_category, str) else pref.topic_category.value
        print(f"  {topic_str.upper().replace('_', ' ')}:")
        print(f"    Acceptance Rate: {pref.acceptance_rate:.1%}")
        print(f"    Total Asked: {pref.total_asked}")
        print(f"    Trend: {pref.trend}")
        print(f"    Confidence: {pref.confidence:.1%}")
        print()

    # Step 5: Show recommendations
    print_section("Step 5: Actionable Recommendations for ARCHITECT")

    if preferences.recommendations:
        print(f"Generated {len(preferences.recommendations)} recommendations:\n")

        for i, rec in enumerate(preferences.recommendations[:10], 1):
            priority_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }
            emoji = priority_emoji.get(rec.priority, "⚪")

            print(f"{i}. {emoji} [{rec.priority.upper()}] {rec.title}")
            print(f"   Type: {rec.recommendation_type.replace('_', ' ').title()}")
            print(f"   {rec.description}")
            print(f"   Evidence:")
            for evidence in rec.evidence:
                print(f"     • {evidence}")
            print(f"   Confidence: {rec.confidence:.1%}\n")
    else:
        print("No recommendations generated (insufficient data or confidence)")

    # Step 6: Store learned preferences
    print_section("Step 6: Persisting Learned Preferences")
    snapshot_id = store.store_preferences(
        preferences,
        snapshot_reason="demo_learning_session"
    )
    print(f"Stored preference snapshot: {snapshot_id}")

    # Retrieve and verify
    current = store.get_current_preferences()
    if current:
        print(f"\n✓ Verified: Current preferences loaded")
        print(f"  Total responses: {current.total_responses}")
        print(f"  Overall acceptance: {current.overall_acceptance_rate:.1%}")
        print(f"  Recommendations: {len(current.recommendations)}")

    # Step 7: Key insights
    print_section("Step 7: Key Insights for Trinity")

    print("✅ WHAT ALEX VALUES (ask more):")
    high_value_topics = [
        (topic, pref)
        for topic, pref in preferences.topic_preferences.items()
        if pref.acceptance_rate >= 0.7 and pref.confidence >= 0.6
    ]
    for topic, pref in sorted(high_value_topics, key=lambda x: x[1].acceptance_rate, reverse=True):
        print(f"  • {topic.replace('_', ' ').title()}: {pref.acceptance_rate:.0%} acceptance")

    print("\n❌ WHAT ALEX DOESN'T VALUE (ask less):")
    low_value_topics = [
        (topic, pref)
        for topic, pref in preferences.topic_preferences.items()
        if pref.acceptance_rate <= 0.3 and pref.confidence >= 0.6
    ]
    for topic, pref in sorted(low_value_topics, key=lambda x: x[1].acceptance_rate):
        print(f"  • {topic.replace('_', ' ').title()}: {pref.acceptance_rate:.0%} acceptance")

    print("\n📈 EMERGING TRENDS:")
    increasing_topics = [
        (topic, pref)
        for topic, pref in preferences.topic_preferences.items()
        if pref.trend == "increasing"
    ]
    for topic, pref in increasing_topics:
        print(f"  • {topic.replace('_', ' ').title()}: Increasing interest ({pref.acceptance_rate:.0%} recent)")

    print("\n⏰ BEST TIMES TO ASK:")
    best_times = sorted(
        preferences.timing_preferences.items(),
        key=lambda x: x[1].acceptance_rate,
        reverse=True
    )[:3]
    for time_key, pref in best_times:
        if pref.confidence >= 0.5:
            print(f"  • {time_key.replace('_', ' ').title()}: {pref.acceptance_rate:.0%} acceptance")

    print_section("Demo Complete")
    print("The preference learning system is ready to help Trinity understand")
    print("Alex's preferences and optimize proactive assistance.\n")

    print("Next steps:")
    print("  1. Integrate with ARCHITECT for recommendation-driven question selection")
    print("  2. Deploy with Firestore backend for production persistence")
    print("  3. Implement automatic preference updates after every 5-10 responses")
    print("  4. Use recommendations to improve question timing and relevance\n")


if __name__ == "__main__":
    demo_preference_learning()
