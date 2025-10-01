"""
Event Simulator for Trinity Protocol 24-Hour Test

Generates realistic telemetry and context events with controlled
timing and variety for comprehensive autonomous operation testing.

Event Categories:
1. Critical errors (NoneType, fatal crashes, security)
2. Constitutional violations (type safety, test gaps, code smells)
3. Feature requests (user intents, enhancements)
4. Code quality (duplication, complexity, refactoring)
5. Test reliability (flaky tests, coverage gaps)
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum


class EventCategory(Enum):
    """Event categories for test simulation."""
    CRITICAL_ERROR = "critical_error"
    CONSTITUTION_VIOLATION = "constitution_violation"
    FEATURE_REQUEST = "feature_request"
    CODE_QUALITY = "code_quality"
    TEST_RELIABILITY = "test_reliability"


class EventSimulator:
    """
    Generates realistic events for Trinity Protocol testing.

    Events are deterministic (seeded) for reproducibility while
    maintaining realistic variety and edge cases.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize event simulator.

        Args:
            seed: Random seed for reproducibility (None = random)
        """
        self.seed = seed or 42
        self.rng = random.Random(self.seed)
        self.event_count = 0

    def generate_event(self, category: Optional[EventCategory] = None) -> Dict[str, Any]:
        """
        Generate a single event.

        Args:
            category: Specific category (None = random rotation)

        Returns:
            Event dict with realistic metadata
        """
        self.event_count += 1

        # Rotate through categories if not specified
        if category is None:
            categories = list(EventCategory)
            category = categories[self.event_count % len(categories)]

        # Generate based on category
        if category == EventCategory.CRITICAL_ERROR:
            return self._generate_critical_error()
        elif category == EventCategory.CONSTITUTION_VIOLATION:
            return self._generate_constitution_violation()
        elif category == EventCategory.FEATURE_REQUEST:
            return self._generate_feature_request()
        elif category == EventCategory.CODE_QUALITY:
            return self._generate_code_quality()
        elif category == EventCategory.TEST_RELIABILITY:
            return self._generate_test_reliability()

        raise ValueError(f"Unknown category: {category}")

    def generate_batch(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate batch of events with category rotation.

        Args:
            count: Number of events to generate

        Returns:
            List of event dicts
        """
        return [self.generate_event() for _ in range(count)]

    def _generate_critical_error(self) -> Dict[str, Any]:
        """Generate critical error event."""
        error_templates = [
            {
                "message": "Fatal error: NoneType attribute access in payment processing",
                "file": "payments/stripe.py",
                "line": 142,
                "error_type": "AttributeError",
                "keywords": ["NoneType", "critical", "payment"],
            },
            {
                "message": "Database connection pool exhausted - 503 Service Unavailable",
                "file": "database/pool.py",
                "line": 89,
                "error_type": "PoolExhausted",
                "keywords": ["database", "critical", "connection"],
            },
            {
                "message": "Security breach detected: SQL injection attempt",
                "file": "api/users.py",
                "line": 234,
                "error_type": "SecurityViolation",
                "keywords": ["security", "sql", "critical"],
            },
            {
                "message": "Memory allocation failed: Out of memory",
                "file": "core/worker.py",
                "line": 56,
                "error_type": "MemoryError",
                "keywords": ["memory", "critical", "oom"],
            },
            {
                "message": "Unhandled exception in request handler: division by zero",
                "file": "api/analytics.py",
                "line": 178,
                "error_type": "ZeroDivisionError",
                "keywords": ["exception", "critical", "handler"],
            },
        ]

        template = self.rng.choice(error_templates)
        return {
            **template,
            "severity": "critical",
            "timestamp": datetime.now().isoformat(),
            "event_id": f"error_{self.event_count:04d}",
            "stack_trace": self._generate_stack_trace(),
            "impact": "production_down" if self.rng.random() > 0.7 else "degraded_performance",
        }

    def _generate_constitution_violation(self) -> Dict[str, Any]:
        """Generate constitutional violation event."""
        violation_templates = [
            {
                "message": "Type safety violation: Dict[Any, Any] detected in user model",
                "file": "models/user.py",
                "line": 23,
                "violation_type": "strict_typing",
                "keywords": ["type_safety", "constitution", "Dict"],
            },
            {
                "message": "Test coverage gap: UserService has 0 tests",
                "file": "services/user_service.py",
                "line": 1,
                "violation_type": "tdd_violation",
                "keywords": ["testing", "tdd", "coverage"],
            },
            {
                "message": "Repository pattern violated: direct database access in controller",
                "file": "controllers/payment_controller.py",
                "line": 67,
                "violation_type": "architecture",
                "keywords": ["repository", "architecture", "database"],
            },
            {
                "message": "Function exceeds 50 lines: refactor_payment (78 lines)",
                "file": "services/payment.py",
                "line": 142,
                "violation_type": "code_quality",
                "keywords": ["complexity", "refactor", "lines"],
            },
            {
                "message": "Missing input validation: API endpoint accepts unvalidated JSON",
                "file": "api/endpoints.py",
                "line": 45,
                "violation_type": "validation",
                "keywords": ["validation", "security", "api"],
            },
        ]

        template = self.rng.choice(violation_templates)
        return {
            **template,
            "severity": "high",
            "timestamp": datetime.now().isoformat(),
            "event_id": f"violation_{self.event_count:04d}",
            "article": f"Article {self.rng.randint(1, 5)}",
        }

    def _generate_feature_request(self) -> Dict[str, Any]:
        """Generate feature request event."""
        feature_templates = [
            {
                "message": "User requests dark mode toggle in application settings",
                "priority": "NORMAL",
                "user_intent": "ui_enhancement",
                "keywords": ["dark_mode", "ui", "settings"],
                "complexity": "medium",
            },
            {
                "message": "Add export to CSV functionality for analytics dashboard",
                "priority": "NORMAL",
                "user_intent": "data_export",
                "keywords": ["export", "csv", "analytics"],
                "complexity": "low",
            },
            {
                "message": "Implement two-factor authentication for user accounts",
                "priority": "HIGH",
                "user_intent": "security_enhancement",
                "keywords": ["2fa", "security", "auth"],
                "complexity": "high",
            },
            {
                "message": "Add real-time notifications for payment events",
                "priority": "NORMAL",
                "user_intent": "notification_system",
                "keywords": ["realtime", "notifications", "websocket"],
                "complexity": "high",
            },
            {
                "message": "Create admin dashboard for user management",
                "priority": "NORMAL",
                "user_intent": "admin_tooling",
                "keywords": ["admin", "dashboard", "management"],
                "complexity": "medium",
            },
        ]

        template = self.rng.choice(feature_templates)
        return {
            **template,
            "source": "personal_context_stream",
            "timestamp": datetime.now().isoformat(),
            "event_id": f"feature_{self.event_count:04d}",
            "estimated_effort": f"{self.rng.randint(1, 8)} days",
        }

    def _generate_code_quality(self) -> Dict[str, Any]:
        """Generate code quality event."""
        quality_templates = [
            {
                "message": "Duplicate validation logic found in 3 files",
                "files": ["auth.py", "api.py", "utils.py"],
                "duplication_ratio": round(self.rng.uniform(0.7, 0.95), 2),
                "pattern": "refactoring_opportunity",
                "keywords": ["duplication", "refactor"],
            },
            {
                "message": "High cyclomatic complexity: calculate_price (CC=18)",
                "file": "services/pricing.py",
                "line": 89,
                "complexity_score": self.rng.randint(15, 25),
                "pattern": "complexity_refactor",
                "keywords": ["complexity", "refactor"],
            },
            {
                "message": "Dead code detected: unused function format_legacy_date",
                "file": "utils/date_utils.py",
                "line": 234,
                "pattern": "dead_code",
                "keywords": ["dead_code", "cleanup"],
            },
            {
                "message": "Missing error handling: network calls without try/catch",
                "file": "services/api_client.py",
                "line": 67,
                "pattern": "error_handling",
                "keywords": ["error_handling", "resilience"],
            },
            {
                "message": "Inconsistent naming: camelCase and snake_case mixed in module",
                "file": "models/product.py",
                "line": 1,
                "pattern": "style_violation",
                "keywords": ["naming", "style", "consistency"],
            },
        ]

        template = self.rng.choice(quality_templates)
        return {
            **template,
            "severity": "medium",
            "timestamp": datetime.now().isoformat(),
            "event_id": f"quality_{self.event_count:04d}",
            "technical_debt": f"{self.rng.randint(1, 4)}h to fix",
        }

    def _generate_test_reliability(self) -> Dict[str, Any]:
        """Generate test reliability event."""
        test_templates = [
            {
                "message": "Flaky test: test_concurrent_transactions fails 40% of the time",
                "test_file": "tests/test_payments.py",
                "test_name": "test_concurrent_transactions",
                "failure_rate": f"{self.rng.randint(20, 60)}%",
                "last_10_runs": [self.rng.choice([True, False]) for _ in range(10)],
                "keywords": ["flaky", "test", "concurrency"],
            },
            {
                "message": "Test timeout: test_large_dataset_processing exceeds 30s",
                "test_file": "tests/test_data.py",
                "test_name": "test_large_dataset_processing",
                "timeout_seconds": self.rng.randint(30, 120),
                "keywords": ["timeout", "test", "performance"],
            },
            {
                "message": "Test coverage dropped: UserService now at 45% (was 85%)",
                "file": "services/user_service.py",
                "current_coverage": round(self.rng.uniform(0.4, 0.6), 2),
                "previous_coverage": 0.85,
                "keywords": ["coverage", "test", "regression"],
            },
            {
                "message": "Integration test failure: external API mock is stale",
                "test_file": "tests/integration/test_external_api.py",
                "test_name": "test_user_sync",
                "failure_reason": "mock_response_mismatch",
                "keywords": ["integration", "mock", "api"],
            },
            {
                "message": "Missing test: new feature PaymentSplit has no tests",
                "file": "features/payment_split.py",
                "lines_of_code": self.rng.randint(50, 200),
                "keywords": ["missing_test", "tdd", "feature"],
            },
        ]

        template = self.rng.choice(test_templates)
        return {
            **template,
            "severity": "medium",
            "timestamp": datetime.now().isoformat(),
            "event_id": f"test_{self.event_count:04d}",
        }

    def _generate_stack_trace(self) -> str:
        """Generate realistic stack trace."""
        frames = [
            "  File 'payments/stripe.py', line 142, in process_payment",
            "  File 'services/payment_service.py', line 89, in handle_transaction",
            "  File 'api/payment_controller.py', line 234, in create_payment",
            "  File 'middleware/auth.py', line 67, in verify_token",
        ]
        selected_frames = self.rng.sample(frames, k=self.rng.randint(2, 4))
        return "\n".join(selected_frames)

    def generate_continuous_stream(
        self,
        interval_minutes: int = 30,
        duration_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Generate events for continuous operation test.

        Args:
            interval_minutes: Minutes between events
            duration_hours: Total test duration

        Returns:
            List of events with calculated timestamps
        """
        events_per_hour = 60 // interval_minutes
        total_events = events_per_hour * duration_hours

        events = []
        start_time = datetime.now()

        for i in range(total_events):
            event = self.generate_event()
            event_time = start_time + timedelta(minutes=i * interval_minutes)
            event["scheduled_time"] = event_time.isoformat()
            event["cycle_number"] = i + 1
            events.append(event)

        return events

    def get_statistics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for event batch.

        Args:
            events: List of events

        Returns:
            Statistics dict
        """
        category_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}

        for event in events:
            # Count by category (infer from event_id prefix)
            event_id = event.get("event_id", "")
            category = event_id.split("_")[0]
            category_counts[category] = category_counts.get(category, 0) + 1

            # Count by severity
            severity = event.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_events": len(events),
            "by_category": category_counts,
            "by_severity": severity_counts,
            "categories": len(category_counts),
            "earliest": events[0]["timestamp"] if events else None,
            "latest": events[-1]["timestamp"] if events else None,
        }


def demo():
    """Demonstrate event simulator."""
    print("Trinity Protocol - Event Simulator Demo")
    print("=" * 60)

    simulator = EventSimulator(seed=42)

    # Generate one of each category
    print("\nGenerating sample events (one per category):")
    print("-" * 60)

    for category in EventCategory:
        event = simulator.generate_event(category)
        print(f"\n{category.value.upper()}:")
        print(f"  Message: {event['message'][:60]}...")
        print(f"  Severity: {event.get('severity', 'N/A')}")
        print(f"  Event ID: {event['event_id']}")

    # Generate 24-hour test batch
    print("\n\n24-Hour Test Event Generation:")
    print("-" * 60)

    simulator_test = EventSimulator(seed=42)
    events = simulator_test.generate_continuous_stream(
        interval_minutes=30,
        duration_hours=24
    )

    stats = simulator_test.get_statistics(events)
    print(f"\nGenerated {stats['total_events']} events")
    print(f"Categories: {stats['by_category']}")
    print(f"Severities: {stats['by_severity']}")
    print(f"\nFirst event: {events[0]['scheduled_time']}")
    print(f"Last event: {events[-1]['scheduled_time']}")


if __name__ == "__main__":
    demo()
