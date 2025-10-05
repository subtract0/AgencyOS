#!/usr/bin/env python3
"""
Test Signal Injection - Manual Trigger for Phase 1 Validation

This script manually injects an IMPROVEMENT_SIGNAL into Trinity's message bus
to test the Witness → Architect → Executor flow without requiring full Witness implementation.

Usage:
    python scripts/inject_test_signal.py

This will trigger Trinity to:
1. Receive IMPROVEMENT_SIGNAL about missing test file
2. Spawn ARCHITECT (qwen2.5-coder:7b) to create plan
3. Spawn EXECUTOR (codestral:22b) to generate test
4. (Future) Auto-commit with constitutional message
"""

import sys
from pathlib import Path

from trinity_protocol.core.orchestrator import TrinityBus

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def inject_test_signal():
    """Inject IMPROVEMENT_SIGNAL for missing test file."""

    bus = TrinityBus()

    # Don't clear - let messages accumulate (timestamp-based detection)
    # bus.clear()  # Removed - breaks timestamp tracking

    # Create improvement signal
    signal_data = {
        "pattern": "missing_tests",
        "priority": "HIGH",
        "source": "manual",
        "file": "trinity_protocol/core/orchestrator.py",
        "reason": "New Ollama integration added - needs test coverage",
        "suggested_tests": [
            "test_ollama_client_initialization",
            "test_spawn_architect_success",
            "test_spawn_architect_timeout_retry"
        ]
    }

    # Publish to message bus
    bus.publish("ORCHESTRATOR", "IMPROVEMENT_SIGNAL", signal_data)

    print("✅ IMPROVEMENT_SIGNAL injected successfully!")
    print(f"📋 Message bus: {bus.path}")
    print(f"🎯 Signal data: {signal_data}")
    print("\n📊 Check Trinity logs:")
    print("  tail -f ~/.trinity-local/logs/trinity_local/trinity.log")
    print("\n Expected flow:")
    print("  1. Trinity reads IMPROVEMENT_SIGNAL from bus")
    print("  2. Spawns ARCHITECT (qwen2.5-coder:7b) to create plan")
    print("  3. Publishes ARCHITECT_READY to bus")
    print("  4. Spawns EXECUTOR (codestral:22b) to implement")
    print("  5. Publishes EXECUTOR_COMPLETE to bus")

if __name__ == "__main__":
    inject_test_signal()
