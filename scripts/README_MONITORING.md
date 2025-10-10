# Dashboard Snapshot Monitoring Setup

## Overview

Automated hourly snapshot generation for the Quality Feedback Loop accuracy dashboard. Supports both **crontab** (macOS/Linux) and **systemd** (Linux) schedulers.

## Quick Start

```bash
# Test snapshot generation (recommended first step)
./scripts/setup_monitoring_cron.sh test

# Install automated monitoring
./scripts/setup_monitoring_cron.sh install

# Check monitoring status
./scripts/setup_monitoring_cron.sh status

# Remove monitoring
./scripts/setup_monitoring_cron.sh uninstall
```

## Features

- ✅ **Auto-detection**: Automatically selects crontab or systemd based on system
- ✅ **Environment validation**: Checks Python virtualenv and dependencies before install
- ✅ **Pre-flight testing**: Runs snapshot generation test before installing cron
- ✅ **Graceful error handling**: Informative messages with setup logs
- ✅ **Safe uninstall**: Complete cleanup of monitoring configuration

## Commands

### `install`

Install hourly automated snapshot generation.

**Process:**
1. Validates Python environment (virtualenv + pydantic dependency)
2. Tests snapshot generation (dry run)
3. Detects scheduler (systemd or crontab)
4. Installs hourly trigger
5. Logs setup to `logs/monitoring/setup.log`

**Example:**
```bash
$ ./scripts/setup_monitoring_cron.sh install
[INFO] === Installing Dashboard Snapshot Monitoring ===
[INFO] Initializing monitoring setup...
[SUCCESS] Log directory created: /Users/am/Code/Agency/logs/monitoring
[INFO] Validating Python environment...
[SUCCESS] Virtual environment detected: /Users/am/Code/Agency/.venv
[INFO] Python version: 3.13.7
[INFO] Checking required dependencies...
[SUCCESS] Python environment validated
[INFO] Testing snapshot generation...
✅ Snapshot generated: logs/monitoring/snapshots/snapshot_20251010_101645.json
[SUCCESS] Snapshot generation test passed
[INFO] Detecting available scheduler...
[INFO] crontab available
[INFO] Installing crontab entry...
[SUCCESS] Crontab installed: 0 * * * * cd /Users/am/Code/Agency && ...
[SUCCESS] === Monitoring installation complete ===

Dashboard snapshots will be generated hourly at:
  /Users/am/Code/Agency/logs/monitoring/snapshots/
```

### `uninstall`

Remove automated monitoring configuration.

**Example:**
```bash
$ ./scripts/setup_monitoring_cron.sh uninstall
[INFO] === Uninstalling Dashboard Snapshot Monitoring ===
[INFO] Uninstalling crontab entry...
[SUCCESS] Crontab entry removed
[SUCCESS] === Monitoring uninstallation complete ===
```

### `status`

Check monitoring status and recent snapshots.

**Example:**
```bash
$ ./scripts/setup_monitoring_cron.sh status
[INFO] Checking crontab status...
✓ Crontab monitoring is ACTIVE
Entry:
0 * * * * cd /Users/am/Code/Agency && /Users/am/Code/Agency/.venv/bin/python -m tools.quality_feedback.dashboard_snapshot >> /Users/am/Code/Agency/logs/monitoring/cron.log 2>&1 # Agency Dashboard Snapshot

Recent snapshots:
total 16
-rw-r--r--  1 am  staff   423B 10 Okt. 12:17 snapshot_20251010_101702.json
-rw-r--r--  1 am  staff   423B 10 Okt. 12:16 snapshot_20251010_101645.json
```

### `test`

Test snapshot generation without installing cron.

**Example:**
```bash
$ ./scripts/setup_monitoring_cron.sh test
[INFO] === Testing Snapshot Generation ===
[INFO] Validating Python environment...
[SUCCESS] Python environment validated
[INFO] Testing snapshot generation...
✅ Snapshot generated: logs/monitoring/snapshots/snapshot_20251010_101645.json

📊 Snapshot Summary:
   Timestamp: 2025-10-10T10:16:45.601149+00:00
   Dashboard Available: False
   Total Tasks: 0
   Accuracy Rate: 0.00%
[SUCCESS] === Test complete ===
```

### `help`

Show usage information and examples.

## Files

### `/scripts/setup_monitoring_cron.sh`

Main setup script with all installation logic.

**Key functions:**
- `validate_python_environment()` - Checks virtualenv and dependencies
- `test_snapshot_generation()` - Pre-flight snapshot test
- `detect_scheduler()` - Auto-detects crontab vs systemd
- `install_crontab()` / `install_systemd()` - Scheduler-specific installation
- `uninstall_crontab()` / `uninstall_systemd()` - Cleanup

### `/scripts/monitoring_snapshot.service`

Systemd service unit (Linux only).

**Configuration:**
- Type: `oneshot` (run once per trigger)
- Command: `python -m tools.quality_feedback.dashboard_snapshot --verbose`
- Logging: `logs/monitoring/systemd.log`
- Resource limits: 512MB memory, 50% CPU quota
- Security hardening: PrivateTmp, NoNewPrivileges, ProtectSystem

**Template variables:**
- `{{AGENCY_ROOT}}` - Replaced with repository path
- `{{PYTHON_CMD}}` - Replaced with virtualenv Python path
- `{{LOG_DIR}}` - Replaced with logs/monitoring path

### `/scripts/monitoring_snapshot.timer`

Systemd timer unit (Linux only).

**Configuration:**
- Schedule: `OnCalendar=hourly` (every hour at minute 0)
- Boot delay: `OnBootSec=5min` (first run 5 minutes after boot)
- Accuracy: `AccuracySec=1min` (±1 minute tolerance)
- Persistent: `Persistent=true` (catch up missed runs after downtime)

## Cron Configuration (macOS/Linux)

**Schedule:** `0 * * * *` (every hour at minute 0)

**Command:**
```bash
cd /Users/am/Code/Agency && /Users/am/Code/Agency/.venv/bin/python -m tools.quality_feedback.dashboard_snapshot >> /Users/am/Code/Agency/logs/monitoring/cron.log 2>&1
```

**Marker:** `# Agency Dashboard Snapshot` (used for safe uninstall)

## Systemd Configuration (Linux)

**Installation location:** `~/.config/systemd/user/`

**Enable timer:**
```bash
systemctl --user enable monitoring_snapshot.timer
systemctl --user start monitoring_snapshot.timer
```

**Check status:**
```bash
systemctl --user status monitoring_snapshot.timer
journalctl --user -u monitoring_snapshot.service -f
```

**Manual trigger:**
```bash
systemctl --user start monitoring_snapshot.service
```

## Logs

### `logs/monitoring/setup.log`

Setup script execution log (install/uninstall/test operations).

**Example:**
```
[2025-10-10 12:16:43] INFO: === Testing Snapshot Generation ===
[2025-10-10 12:16:43] INFO: Initializing monitoring setup...
[2025-10-10 12:16:43] SUCCESS: Log directory created
[2025-10-10 12:16:43] INFO: Validating Python environment...
[2025-10-10 12:16:43] SUCCESS: Virtual environment detected
[2025-10-10 12:16:43] INFO: Testing snapshot generation...
[2025-10-10 12:16:45] SUCCESS: Snapshot generation test passed
```

### `logs/monitoring/cron.log` (crontab)

Hourly cron execution log (snapshot generation output).

**Example:**
```
✅ Snapshot generated: logs/monitoring/snapshots/snapshot_20251010_110000.json

📊 Snapshot Summary:
   Timestamp: 2025-10-10T11:00:00.123456+00:00
   Dashboard Available: True
   Total Tasks: 47
   Accuracy Rate: 95.74%
```

### `logs/monitoring/systemd.log` (systemd)

Systemd service execution log (snapshot generation output).

## Snapshot Output

**Directory:** `logs/monitoring/snapshots/`

**Filename format:** `snapshot_YYYYMMDD_HHMMSS.json`

**Example snapshot:**
```json
{
  "metadata": {
    "generated_at": "2025-10-10T10:16:45.601149+00:00",
    "snapshot_version": "1.0",
    "dashboard_available": true,
    "data_directory": "/Users/am/.agency/dashboard"
  },
  "snapshot": {
    "timestamp": "2025-10-10T10:16:45.601159+00:00",
    "total_tasks": 47,
    "correct_classifications": 45,
    "misclassifications": 2,
    "accuracy_rate": 0.9574,
    "misclassifications_detected": 8,
    "refinements_applied": 5,
    "refinement_success_rate": 0.625,
    "top_misclassified_patterns": [
      {"pattern": "complex_refactor", "count": 3},
      {"pattern": "ambiguous_requirements", "count": 2}
    ],
    "trend_7d": {
      "accuracy_change": 0.0423,
      "tasks_per_day": 6.7
    }
  }
}
```

## Troubleshooting

### No virtualenv found

**Error:**
```
[ERROR] No Python virtual environment found. Please create one:
  python -m venv .venv
  source .venv/bin/activate
```

**Solution:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Missing pydantic dependency

**Error:**
```
[ERROR] Missing required dependency: pydantic
  pip install pydantic
```

**Solution:**
```bash
source .venv/bin/activate
pip install pydantic
```

### Snapshot generation test failed

**Error:**
```
[ERROR] Snapshot generation test failed
[ERROR] Check logs at: /Users/am/Code/Agency/logs/monitoring/setup.log
```

**Solution:**
```bash
# Check detailed error in setup log
cat logs/monitoring/setup.log

# Try manual snapshot generation for debugging
source .venv/bin/activate
python -m tools.quality_feedback.dashboard_snapshot --verbose
```

### Cron not running (macOS)

**Check crontab:**
```bash
crontab -l | grep "Agency Dashboard Snapshot"
```

**Check cron log:**
```bash
tail -f logs/monitoring/cron.log
```

**Common issues:**
- Virtualenv path changed → Reinstall: `./scripts/setup_monitoring_cron.sh install`
- Permissions issue → Ensure logs directory is writable: `chmod -R 755 logs/monitoring`

### Systemd timer not running (Linux)

**Check timer status:**
```bash
systemctl --user status monitoring_snapshot.timer
```

**Check service logs:**
```bash
journalctl --user -u monitoring_snapshot.service -n 50
```

**Common issues:**
- Timer not enabled → Enable: `systemctl --user enable monitoring_snapshot.timer`
- Service failed → Check logs: `journalctl --user -u monitoring_snapshot.service -e`

## Constitutional Compliance

This monitoring setup adheres to Agency constitutional requirements:

### Article I: Complete Context Before Action

- ✅ **Pre-flight validation**: Tests snapshot generation before installing cron
- ✅ **Environment validation**: Checks Python version and dependencies
- ✅ **Retry logic**: Retries on timeout (implemented in dashboard_snapshot.py)

### Article II: 100% Verification and Stability

- ✅ **Test-before-install**: Dry run ensures snapshots work before automation
- ✅ **Pydantic validation**: All snapshot data validated with strict typing
- ✅ **Safe uninstall**: Complete cleanup with verification

### Article IV: Continuous Learning

- ✅ **Automated snapshots**: Hourly data collection for trend analysis
- ✅ **Historical tracking**: Snapshots stored indefinitely for learning extraction
- ✅ **Pattern detection**: Enables misclassification trend analysis

### Article V: Spec-Driven Development

- ✅ **Spec-004 traceability**: Implements monitoring requirements from spec
- ✅ **Documented behavior**: Clear documentation of all features
- ✅ **Logging**: Comprehensive setup and execution logs

## Advanced Usage

### Custom snapshot frequency

**Edit cron schedule:**
```bash
# Every 30 minutes
*/30 * * * * cd /Users/am/Code/Agency && ...

# Every 4 hours
0 */4 * * * cd /Users/am/Code/Agency && ...

# Daily at 2 AM
0 2 * * * cd /Users/am/Code/Agency && ...
```

**Edit systemd timer:**
```ini
# Every 30 minutes
OnCalendar=*:0/30

# Every 4 hours
OnCalendar=0/4:00

# Daily at 2 AM
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
```

### Custom output directory

**Modify setup script:**
```bash
# In setup_monitoring_cron.sh, change:
SNAPSHOT_OUTPUT_DIR="${LOG_DIR}/snapshots"
# To:
SNAPSHOT_OUTPUT_DIR="/custom/path/snapshots"
```

### Manual snapshot generation

```bash
# Default (24-hour window)
python -m tools.quality_feedback.dashboard_snapshot --verbose

# Custom time window (7 days)
python -m tools.quality_feedback.dashboard_snapshot --window-hours 168 --verbose

# Custom output directory
python -m tools.quality_feedback.dashboard_snapshot \
  --output-dir /custom/path \
  --verbose
```

## Integration with Monitoring Tools

### Prometheus exporter (future)

```python
# Export snapshot metrics to Prometheus
from prometheus_client import Gauge, start_http_server
import json

accuracy_gauge = Gauge('agency_accuracy_rate', 'Current accuracy rate')

def export_metrics():
    with open('logs/monitoring/snapshots/latest.json') as f:
        snapshot = json.load(f)
    accuracy_gauge.set(snapshot['snapshot']['accuracy_rate'])

start_http_server(8000)
```

### Grafana dashboard (future)

```json
{
  "dashboard": {
    "title": "Agency Quality Metrics",
    "panels": [
      {
        "title": "Accuracy Rate",
        "targets": [
          {
            "expr": "agency_accuracy_rate",
            "legendFormat": "Accuracy"
          }
        ]
      }
    ]
  }
}
```

## License

Part of AgencyOS - see root LICENSE file.

## Related Files

- `tools/quality_feedback/dashboard_snapshot.py` - Snapshot generation logic
- `tools/quality_feedback/accuracy_dashboard.py` - Dashboard data models
- `specs/spec-004-quality-feedback-loop.md` - Monitoring requirements specification
- `docs/adr/ADR-025-quality-feedback-loop.md` - Architectural decision record
