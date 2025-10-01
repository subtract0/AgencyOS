# Trinity Protocol Cost Dashboard - Complete Guide

**Version**: 1.0.0
**Status**: Production Ready
**Date**: October 1, 2025

---

## Overview

Trinity Protocol includes a comprehensive cost monitoring system with three dashboards:

1. **Terminal Dashboard** - Real-time curses-based CLI interface
2. **Web Dashboard** - Browser-based visual dashboard with charts
3. **Cost Alerts** - Automated budget monitoring and notifications

All dashboards share the same underlying `CostTracker` infrastructure and SQLite database.

---

## Quick Start

### Installation

No additional dependencies required for terminal dashboard:

```bash
# Terminal and alerts only
# (uses built-in Python libraries)
```

For web dashboard, install Flask:

```bash
pip install flask
```

For Slack alerts, install requests:

```bash
pip install requests
```

### Unified CLI Interface

The easiest way to use all dashboard features is through the unified CLI:

```bash
# Terminal dashboard (live updates)
python trinity_protocol/dashboard_cli.py terminal --live

# Web dashboard
python trinity_protocol/dashboard_cli.py web --port 8080

# Cost alerts
python trinity_protocol/dashboard_cli.py alerts --continuous

# Quick snapshot
python trinity_protocol/dashboard_cli.py snapshot

# Export data
python trinity_protocol/dashboard_cli.py export
```

---

## Terminal Dashboard

### Features

- **Live Updates**: Real-time refresh every 5 seconds (configurable)
- **Budget Visualization**: Visual progress bar with color-coded warnings
- **Agent Breakdown**: Cost per agent with visual bars
- **Spending Trends**: Hourly rate and daily projections
- **Recent Activity**: Last 5 API calls
- **Interactive Controls**: Keyboard-driven interface

### Usage

#### Live Mode (Recommended)

```bash
# Basic live dashboard
python trinity_protocol/cost_dashboard.py --live

# Custom refresh interval (10 seconds)
python trinity_protocol/cost_dashboard.py --live --interval 10

# With budget tracking
python trinity_protocol/cost_dashboard.py --live --budget 10.0

# Custom database path
python trinity_protocol/cost_dashboard.py --live --db /path/to/costs.db
```

#### Single Snapshot Mode

```bash
# Print snapshot to console
python trinity_protocol/cost_dashboard.py

# With budget
python trinity_protocol/cost_dashboard.py --budget 10.0
```

#### Export Mode

```bash
# Export to CSV and JSON
python trinity_protocol/cost_dashboard.py --export costs
# Creates: costs.csv and costs.json
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| `Q` | Quit dashboard |
| `E` | Export data to CSV/JSON |
| `R` | Force refresh |

### Display Sections

#### 1. Summary Section
```
SUMMARY
  Total Spent:        $0.1234
  Total Calls:        42
  Total Tokens:       12,345
  Success Rate:       98.5%
  Hourly Rate:        $0.0123/hour
  Daily Projection:   $0.30/day
```

#### 2. Budget Section (if budget configured)
```
BUDGET
  Budget:             $10.00
  Spent:              $0.1234 (1.2%)
  Remaining:          $9.8766
  [████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 1.2%
```

**Color Coding**:
- **Green**: < 80% of budget
- **Yellow**: 80-90% of budget
- **Red**: > 90% of budget

#### 3. Per-Agent Costs
```
PER-AGENT COSTS
  EXECUTOR              $0.0456 (37.0%) ██████████████████░░░░░░░░░░░
  ARCHITECT             $0.0345 (28.0%) ████████████████░░░░░░░░░░░░░
  WITNESS               $0.0234 (19.0%) ███████████░░░░░░░░░░░░░░░░░░
  ...
```

#### 4. Recent Activity
```
RECENT ACTIVITY
  14:32:15 | EXECUTOR             | $0.0012 | ✓
  14:31:58 | ARCHITECT            | $0.0008 | ✓
  14:31:42 | WITNESS              | $0.0005 | ✓
```

### Configuration Options

```bash
python trinity_protocol/cost_dashboard.py \
    --live \                        # Enable live mode
    --interval 10 \                 # Refresh every 10 seconds
    --db trinity_costs.db \         # Database path
    --budget 10.0 \                 # Budget limit ($)
    --warning-pct 75.0              # Warning threshold (%)
```

---

## Web Dashboard

### Features

- **Real-Time Updates**: Server-Sent Events (SSE) for live data
- **Interactive Charts**: Doughnut chart for cost distribution
- **Mobile-Friendly**: Responsive design
- **Budget Visualization**: Animated progress bars
- **Agent Breakdown**: Sortable agent list with bars
- **Auto-Refresh**: Configurable refresh interval

### Usage

#### Start Web Server

```bash
# Default (http://localhost:8080)
python trinity_protocol/cost_dashboard_web.py

# Custom port
python trinity_protocol/cost_dashboard_web.py --port 5000

# Custom host and port
python trinity_protocol/cost_dashboard_web.py --host 0.0.0.0 --port 8080

# With budget tracking
python trinity_protocol/cost_dashboard_web.py --budget 10.0

# Custom refresh interval
python trinity_protocol/cost_dashboard_web.py --interval 10
```

#### Access Dashboard

Open your browser to:
```
http://localhost:8080
```

Or from another device on your network:
```
http://<your-ip>:8080
```

### Dashboard Components

#### 1. Total Spending Card
- Total cost (USD)
- Total API calls
- Total tokens (input + output)
- Success rate (%)

#### 2. Spending Trends Card
- Hourly rate ($/hour)
- Daily projection ($/day)
- Last hour cost ($)
- Last 24h cost ($)

#### 3. Budget Status Card (if configured)
- Budget limit
- Animated progress bar
- Remaining budget
- Percentage used

#### 4. Cost by Agent List
- Sortable by cost
- Visual bars
- Percentage of total
- Auto-scrollable

#### 5. Cost Distribution Chart
- Interactive doughnut chart
- Legend with agent names
- Hover for details

### API Endpoints

The web dashboard exposes a REST API:

```bash
# Get current summary (JSON)
curl http://localhost:8080/api/summary

# Stream live updates (SSE)
curl http://localhost:8080/stream
```

### Configuration Options

```bash
python trinity_protocol/cost_dashboard_web.py \
    --host 0.0.0.0 \                # Bind to all interfaces
    --port 8080 \                   # Listen port
    --db trinity_costs.db \         # Database path
    --budget 10.0 \                 # Budget limit
    --interval 5 \                  # Refresh interval (seconds)
    --debug                         # Enable debug mode
```

### Deployment

For production deployment, use a WSGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 trinity_protocol.cost_dashboard_web:app
```

---

## Cost Alerts System

### Features

- **Budget Thresholds**: Alert at 80%, 90%, 100% of budget
- **Rate Limits**: Hourly and daily spending caps
- **Spike Detection**: Detect anomalous spending increases
- **Multi-Channel**: Console, email, Slack
- **Deduplication**: Cooldown period to prevent spam
- **Continuous Monitoring**: Background monitoring service

### Usage

#### Single Check

```bash
# Check all alerts once
python trinity_protocol/cost_alerts.py --db trinity_costs.db --budget 10.0

# With rate limits
python trinity_protocol/cost_alerts.py \
    --budget 10.0 \
    --hourly-max 1.0 \
    --daily-max 10.0
```

#### Continuous Monitoring

```bash
# Check every 5 minutes (300 seconds)
python trinity_protocol/cost_alerts.py \
    --continuous \
    --budget 10.0 \
    --interval 300 \
    --hourly-max 1.0
```

### Alert Types

#### 1. Budget Threshold Alerts

Triggered when spending crosses configured thresholds:

```python
AlertConfig(
    budget_threshold_pct=[80, 90, 100]  # Default
)
```

**Severity Levels**:
- `INFO`: 80% threshold
- `WARNING`: 90% threshold
- `CRITICAL`: 100% threshold

#### 2. Hourly Rate Alerts

Triggered when hourly spending exceeds limit:

```bash
python trinity_protocol/cost_alerts.py --hourly-max 1.0
# Alerts if last hour cost > $1.00
```

#### 3. Daily Projection Alerts

Triggered when projected daily spending exceeds limit:

```bash
python trinity_protocol/cost_alerts.py --daily-max 10.0
# Alerts if current rate projects to > $10/day
```

#### 4. Spending Spike Alerts

Detects anomalous cost increases:

```python
AlertConfig(
    spike_multiplier=3.0,  # Alert if 3x baseline
    spike_window_hours=1    # Compare last hour to 24h baseline
)
```

### Notification Channels

#### Console/Log (Always Enabled)

All alerts are logged to console and optionally to file:

```bash
python trinity_protocol/cost_alerts.py \
    --continuous \
    --log-file trinity_alerts.log
```

#### Email Alerts

```bash
python trinity_protocol/cost_alerts.py \
    --continuous \
    --budget 10.0 \
    --email-enabled \
    --email-smtp-host smtp.gmail.com \
    --email-smtp-port 587 \
    --email-from alerts@example.com \
    --email-to admin@example.com,dev@example.com \
    --email-password "your-app-password"
```

**Gmail Setup**:
1. Enable 2-factor authentication
2. Generate app-specific password
3. Use app password instead of account password

#### Slack Alerts

```bash
python trinity_protocol/cost_alerts.py \
    --continuous \
    --budget 10.0 \
    --slack-enabled \
    --slack-webhook "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**Slack Setup**:
1. Go to https://api.slack.com/apps
2. Create new app or use existing
3. Enable "Incoming Webhooks"
4. Create webhook for your channel
5. Copy webhook URL

### Alert Configuration

#### Programmatic Usage

```python
from trinity_protocol.cost_tracker import CostTracker
from trinity_protocol.cost_alerts import CostAlertSystem, AlertConfig

# Initialize tracker
tracker = CostTracker(db_path="trinity_costs.db", budget_usd=10.0)

# Configure alerts
config = AlertConfig(
    # Budget thresholds
    budget_threshold_pct=[75, 85, 95, 100],

    # Rate limits
    hourly_rate_max=1.0,
    daily_budget_max=10.0,

    # Spike detection
    spike_multiplier=3.0,
    spike_window_hours=1,

    # Deduplication
    alert_cooldown_minutes=60,

    # Email
    email_enabled=True,
    email_smtp_host="smtp.gmail.com",
    email_smtp_port=587,
    email_from="alerts@example.com",
    email_to=["admin@example.com"],
    email_password="app-password",

    # Slack
    slack_enabled=True,
    slack_webhook_url="https://hooks.slack.com/services/XXX/YYY/ZZZ"
)

# Create alert system
alerts = CostAlertSystem(tracker, config)

# Single check
triggered = alerts.check_all()

# Continuous monitoring
from trinity_protocol.cost_alerts import run_continuous_monitoring
run_continuous_monitoring(tracker, config, check_interval_seconds=300)
```

### Alert Cooldown

To prevent spam, alerts have a cooldown period (default: 60 minutes):

```bash
# Custom cooldown (30 minutes)
python trinity_protocol/cost_alerts.py \
    --continuous \
    --cooldown 30
```

Once an alert fires, it won't fire again for the same threshold until the cooldown expires.

---

## Data Export

### CSV Export

Exports detailed call history:

```bash
# Export to CSV
python trinity_protocol/dashboard_cli.py export --csv trinity_costs.csv
```

**CSV Columns**:
- `timestamp`: ISO 8601 timestamp
- `agent`: Agent name (WITNESS, ARCHITECT, EXECUTOR)
- `model`: Model name (gpt-5, claude-sonnet-4.5)
- `model_tier`: Pricing tier (cloud_premium, cloud_mini)
- `input_tokens`: Input token count
- `output_tokens`: Output token count
- `cost_usd`: Cost in USD
- `duration_seconds`: Call duration
- `success`: Boolean success flag
- `task_id`: Task identifier
- `correlation_id`: Correlation identifier

### JSON Export

Exports summary + recent calls:

```bash
# Export to JSON
python trinity_protocol/dashboard_cli.py export --json trinity_costs.json
```

**JSON Structure**:
```json
{
  "exported_at": "2025-10-01T14:30:00",
  "summary": {
    "total_cost_usd": 0.1234,
    "total_calls": 42,
    "total_input_tokens": 5000,
    "total_output_tokens": 3000,
    "success_rate": 0.98,
    "by_agent": {"EXECUTOR": 0.0456, ...},
    "by_model": {"gpt-5": 0.0890, ...},
    "by_task": {"task-123": 0.0234, ...}
  },
  "trends": {
    "hourly_rate": 0.0123,
    "daily_projection": 0.30,
    "last_hour_cost": 0.0123,
    "last_day_cost": 0.25
  },
  "budget": {
    "limit": 10.0,
    "spent": 0.1234,
    "remaining": 9.8766,
    "percent_used": 1.23
  },
  "recent_calls": [...]
}
```

### Automated Export

Export from live dashboard:

1. **Terminal Dashboard**: Press `E` key to export
2. **Web Dashboard**: Use API endpoint:
   ```bash
   curl http://localhost:8080/api/summary > costs.json
   ```

---

## Integration with Trinity Protocol

### Automatic Cost Tracking

CostTracker is integrated into all Trinity agents:

```python
# EXECUTOR tracks sub-agent costs
from trinity_protocol.executor_agent import ExecutorAgent
from trinity_protocol.cost_tracker import CostTracker

tracker = CostTracker(db_path="trinity_costs.db", budget_usd=10.0)
executor = ExecutorAgent(
    message_bus=bus,
    store=store,
    agent_context=context,
    cost_tracker=tracker  # Automatically tracks all sub-agent calls
)
```

### Viewing Costs During Autonomous Operation

While Trinity is running:

```bash
# Terminal 1: Run Trinity
python trinity_protocol/demo_complete_trinity.py

# Terminal 2: Monitor costs live
python trinity_protocol/dashboard_cli.py terminal --live

# Terminal 3: Web dashboard
python trinity_protocol/dashboard_cli.py web --port 8080
```

### Budget-Based Shutdown

Implement automatic shutdown when budget exceeded:

```python
from trinity_protocol.cost_tracker import CostTracker

tracker = CostTracker(db_path="trinity_costs.db", budget_usd=10.0)

# Check before each task
summary = tracker.get_summary()
if summary.total_cost_usd > tracker.budget_usd:
    print("Budget exceeded! Shutting down...")
    sys.exit(1)
```

---

## Advanced Usage

### Custom Alert Handlers

Extend alert system with custom notification channels:

```python
from trinity_protocol.cost_alerts import CostAlertSystem, Alert

class CustomAlertSystem(CostAlertSystem):
    def _send_alert(self, alert: Alert):
        # Call parent for default channels
        super()._send_alert(alert)

        # Add custom handler
        if alert.level == AlertLevel.CRITICAL:
            self._send_to_pagerduty(alert)

    def _send_to_pagerduty(self, alert: Alert):
        # Your PagerDuty integration
        pass
```

### Multi-Database Aggregation

Track costs across multiple environments:

```python
from trinity_protocol.cost_tracker import CostTracker

# Production
prod_tracker = CostTracker("prod_costs.db")
prod_summary = prod_tracker.get_summary()

# Development
dev_tracker = CostTracker("dev_costs.db")
dev_summary = dev_tracker.get_summary()

# Aggregate
total_cost = prod_summary.total_cost_usd + dev_summary.total_cost_usd
print(f"Total across environments: ${total_cost:.4f}")
```

### Scheduled Reports

Generate daily cost reports with cron:

```bash
# Add to crontab
0 9 * * * /usr/bin/python3 /path/to/trinity_protocol/dashboard_cli.py export --json /reports/daily_$(date +\%Y\%m\%d).json
```

---

## Troubleshooting

### Dashboard Not Updating

**Terminal Dashboard**:
- Check database path is correct
- Verify database file exists and is not empty
- Check terminal size (minimum 80x24)

**Web Dashboard**:
- Verify Flask is installed: `pip install flask`
- Check port is not in use: `lsof -i :8080`
- Check browser console for JavaScript errors
- Verify SSE connection in Network tab

### No Cost Data

Ensure CostTracker is wired to agents:

```bash
# Verify wiring
python trinity_protocol/verify_cost_tracking.py

# Expected output:
# ✅ AgencyCodeAgent: cost_tracker stored correctly
# ✅ TestGeneratorAgent: cost_tracker stored correctly
# ...
```

### Alerts Not Firing

- Check alert cooldown hasn't suppressed alerts
- Verify thresholds are configured correctly
- Check log file for errors: `trinity_alerts.log`
- Test email/Slack credentials separately

### Export Failures

- Check write permissions for output directory
- Verify database is not locked by another process
- Check disk space availability

---

## Performance Considerations

### Database Size

SQLite database grows with usage:

```bash
# Check database size
ls -lh trinity_costs.db

# Vacuum to reclaim space
sqlite3 trinity_costs.db "VACUUM;"
```

### Query Performance

For large databases (>100K calls), add indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_timestamp ON llm_calls(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent ON llm_calls(agent);
CREATE INDEX IF NOT EXISTS idx_task ON llm_calls(task_id);
```

(Indexes are created automatically by CostTracker)

### Memory Usage

- **Terminal Dashboard**: ~5-10 MB RAM
- **Web Dashboard**: ~20-30 MB RAM (Flask)
- **Alert System**: ~5 MB RAM

---

## Security

### Database Security

The cost database contains usage data but not API keys:

```bash
# Restrict permissions
chmod 600 trinity_costs.db
```

### Web Dashboard Security

For production deployment:

1. **Use HTTPS**: Deploy behind nginx/Apache with SSL
2. **Add Authentication**: Use Flask-Login or similar
3. **Firewall**: Restrict access to trusted IPs
4. **Rate Limiting**: Use Flask-Limiter

### Email Security

- Use app-specific passwords (not account password)
- Store credentials in environment variables:
  ```bash
  export EMAIL_PASSWORD="your-app-password"
  ```

---

## FAQ

**Q: Can I track costs across multiple Trinity instances?**
A: Yes, either use separate databases or add an `instance_id` field to track multiple instances in one database.

**Q: Does the web dashboard work on mobile?**
A: Yes, it's fully responsive and works on phones/tablets.

**Q: Can I customize budget thresholds?**
A: Yes, use `--warning-pct` to change the warning percentage (default 80%).

**Q: How accurate are the cost calculations?**
A: Costs are calculated using official pricing from model providers. Actual costs may vary slightly due to rounding.

**Q: Can I run multiple dashboards simultaneously?**
A: Yes! Run terminal, web, and alerts all at the same time. They share the same database.

**Q: What happens if I exceed my budget?**
A: You'll receive alerts, but Trinity won't automatically stop. Implement budget-based shutdown logic if needed.

---

## Next Steps

1. **Try the Terminal Dashboard**:
   ```bash
   python trinity_protocol/dashboard_cli.py terminal --live
   ```

2. **Set Up Web Dashboard**:
   ```bash
   pip install flask
   python trinity_protocol/dashboard_cli.py web
   ```

3. **Configure Alerts**:
   ```bash
   python trinity_protocol/dashboard_cli.py alerts --continuous --budget 10.0
   ```

4. **Integrate with Trinity**:
   - See `QUICKSTART.md` for Trinity setup
   - All agents auto-track costs when `cost_tracker` is provided

---

## Support

For issues or questions:
- Check existing documentation in `trinity_protocol/docs/`
- Review `PRODUCTION_WIRING.md` for integration details
- See `cost_tracking_integration.md` for Phase 2 implementation guide

---

*Trinity Protocol Cost Dashboard v1.0.0*
*Built for transparent, budget-conscious autonomous operation*
