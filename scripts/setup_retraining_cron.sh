#!/bin/bash
# Setup TRM Router Automated Retraining Cron Job
#
# Installs cron job to run retraining every 2 weeks (bi-weekly)
# Runs at 2 AM on 1st and 15th of every month
#
# Usage:
#   bash scripts/setup_retraining_cron.sh [--dry-run]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENCY_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "DRY RUN MODE: Will not modify crontab"
fi

# Cron job configuration
CRON_SCHEDULE="0 2 1,15 * *"  # 2 AM on 1st and 15th of every month
RETRAINING_SCRIPT="$SCRIPT_DIR/auto_retrain_loop.py"
LOG_DIR="$AGENCY_ROOT/logs/retraining"
DISAGREEMENTS_LOG="$AGENCY_ROOT/logs/shadow_mode/disagreements.jsonl"

# Create log directory
mkdir -p "$LOG_DIR"

# Generate cron command
TIMESTAMP='$(date +\%Y\%m\%d_\%H\%M\%S)'
OUTPUT_DIR="$AGENCY_ROOT/models/trm_router_lora_retrain_$TIMESTAMP"
LOG_FILE="$LOG_DIR/retrain_$TIMESTAMP.log"

CRON_COMMAND="cd $AGENCY_ROOT && python $RETRAINING_SCRIPT \\
  --disagreements $DISAGREEMENTS_LOG \\
  --output $OUTPUT_DIR \\
  --sample-count 150 \\
  --base-model qwen3coder-30b \\
  --existing-train learning/trm_labels_train.jsonl \\
  --val-data learning/trm_labels_val.jsonl \\
  --min-disagreements 100 \\
  --max-age-days 14 \\
  >> $LOG_FILE 2>&1"

CRON_ENTRY="$CRON_SCHEDULE $CRON_COMMAND"

echo "========================================================================"
echo "TRM ROUTER AUTOMATED RETRAINING - CRON SETUP"
echo "========================================================================"
echo ""
echo "Schedule: $CRON_SCHEDULE (2 AM on 1st and 15th of every month)"
echo "Script: $RETRAINING_SCRIPT"
echo "Disagreements: $DISAGREEMENTS_LOG"
echo "Log directory: $LOG_DIR"
echo ""

if $DRY_RUN; then
    echo "DRY RUN: Cron entry that would be added:"
    echo ""
    echo "$CRON_ENTRY"
    echo ""
    exit 0
fi

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "auto_retrain_loop.py"; then
    echo "⚠️  Cron entry already exists!"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "auto_retrain_loop.py"
    echo ""
    read -p "Remove existing entry and re-add? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi

    # Remove existing entry
    crontab -l | grep -v "auto_retrain_loop.py" | crontab -
    echo "✅ Removed existing entry"
fi

# Add new cron entry
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job installed successfully!"
echo ""
echo "Verify with: crontab -l"
echo ""
echo "Next retraining runs:"
# Calculate next 3 execution times
python3 - <<EOF
from datetime import datetime, timedelta

now = datetime.now()
year, month = now.year, now.month

# Find next 3 occurrences of 1st or 15th
next_runs = []
for _ in range(6):  # Check next 6 potential dates
    for day in [1, 15]:
        candidate = datetime(year, month, day, 2, 0, 0)
        if candidate > now:
            next_runs.append(candidate)
        if len(next_runs) == 3:
            break
    if len(next_runs) == 3:
        break
    month += 1
    if month > 12:
        month = 1
        year += 1

for i, run_time in enumerate(next_runs, 1):
    print(f"  {i}. {run_time.strftime('%Y-%m-%d %H:%M:%S')}")
EOF
echo ""
echo "Logs will be written to: $LOG_DIR/retrain_YYYYMMDD_HHMMSS.log"
echo ""
echo "To remove cron job:"
echo "  crontab -l | grep -v 'auto_retrain_loop.py' | crontab -"
echo "========================================================================" echo ""

# Create README for logs directory
cat > "$LOG_DIR/README.md" <<'README_EOF'
# TRM Router Retraining Logs

This directory contains logs from automated retraining runs.

## Log Format

- `retrain_YYYYMMDD_HHMMSS.log` - Full retraining log with timestamps

## Monitoring

Check recent logs:
```bash
tail -50 logs/retraining/retrain_*.log | tail -50
```

Check for errors:
```bash
grep -i error logs/retraining/retrain_*.log
```

## Manual Retraining

To run retraining manually (outside of cron):
```bash
python scripts/auto_retrain_loop.py \
  --disagreements logs/shadow_mode/disagreements.jsonl \
  --output models/trm_router_lora_retrain_$(date +%Y%m%d) \
  --sample-count 150
```
README_EOF

echo "✅ Created README: $LOG_DIR/README.md"
echo ""
echo "Setup complete! 🚀"
