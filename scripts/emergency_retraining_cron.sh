#!/usr/bin/env bash
#
# Emergency Retraining Cron Script
#
# Hourly drift detection and emergency retraining trigger.
# Called by cron/systemd timer every hour to check for accuracy drift.
#
# Workflow:
# 1. Check drift via AccuracyDriftDetector
# 2. If drift detected (accuracy drop >5%), trigger WeeklyRetrainingScheduler
# 3. Pass skip_ab_rollout=True for immediate 100% deployment
# 4. Log event to VectorStore (tags: ["emergency", "retraining", "drift_recovery"])
#
# Cron Schedule: 0 * * * * (every hour on the hour)
# Systemd Timer: OnCalendar=hourly
#
# Constitutional Compliance:
# - Article I: Complete context (full 7-day drift check)
# - Article III: Automated enforcement (zero manual intervention)
# - Article IV: VectorStore logging (emergency events)
#
# Reference: specs/spec-009-misclassification-detection.md Section 6.2
# Author: AgencyCodeAgent
# Date: 2025-10-10
#

set -euo pipefail

# Configuration
AGENCY_DIR="/Users/am/Code/Agency"
LOG_DIR="/var/log/agency"
LOG_FILE="${LOG_DIR}/emergency_retraining.log"

# Create log directory if not exists
mkdir -p "${LOG_DIR}"

# Activate virtual environment
cd "${AGENCY_DIR}"
source .venv/bin/activate

# Timestamp for logging
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "[$TIMESTAMP] Starting emergency retraining trigger check..." >> "${LOG_FILE}"

# Run emergency retraining trigger
python3 << 'EOF'
from shared.agent_context import create_agent_context
from tools.ml_routing.emergency_retraining_trigger import (
    EmergencyRetrainingTrigger,
    TriggerConfig,
)

# Create agent context
context = create_agent_context("emergency_retraining_cron")

# Configure trigger (defaults: hourly, 5% threshold, 300 samples)
config = TriggerConfig()

# Initialize trigger
trigger = EmergencyRetrainingTrigger(context=context, config=config)

# Run check and trigger
result = trigger.check_and_trigger()

if result.is_ok():
    report = result.unwrap()

    if report.triggered:
        print(f"✅ Emergency retraining triggered!")
        print(f"   Current accuracy: {report.current_accuracy:.3f}")
        print(f"   Accuracy drop: {report.accuracy_drop_pct:.1f}%")
        print(f"   New model: {report.new_model_version}")
        print(f"   New accuracy: {report.new_model_accuracy:.3f}")
        print(f"   Samples used: {report.samples_used}")
    elif report.drift_detected:
        print(f"⚠️  Drift detected but alert deduplicated")
        print(f"   Current accuracy: {report.current_accuracy:.3f}")
    else:
        print(f"✅ No drift detected")
        print(f"   Current accuracy: {report.current_accuracy:.3f}")
else:
    error = result.unwrap_err()
    print(f"❌ Emergency retraining check failed: {error}")
    exit(1)
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] Emergency retraining check completed successfully" >> "${LOG_FILE}"
else
    echo "[$TIMESTAMP] Emergency retraining check failed with exit code $EXIT_CODE" >> "${LOG_FILE}"
fi

exit $EXIT_CODE
