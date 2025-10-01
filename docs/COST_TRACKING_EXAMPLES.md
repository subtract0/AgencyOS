# Cost Tracking System - Usage Examples

This document provides practical examples and sample outputs for all cost tracking features.

## Table of Contents

1. [CLI Dashboard Examples](#cli-dashboard-examples)
2. [Web Dashboard Examples](#web-dashboard-examples)
3. [Alert System Examples](#alert-system-examples)
4. [Programmatic Usage Examples](#programmatic-usage-examples)
5. [Integration Examples](#integration-examples)

---

## CLI Dashboard Examples

### Example 1: Snapshot View

**Command:**
```bash
python agency.py cost-dashboard
```

**Output:**
```
======================================================================
TRINITY PROTOCOL - COST SNAPSHOT
Generated: 2025-10-01 15:30:45
======================================================================

💰 TOTAL COST: $12.4567
📊 BUDGET: $12.4567 / $100.00 (12.5%)
💵 REMAINING: $87.5433

📞 TOTAL CALLS: 1,234
✅ SUCCESS RATE: 99.8%
🔢 TOKENS: 345,678 in + 222,212 out

📈 SPENDING TRENDS:
  Hourly Rate:      $2.3456/hour
  Daily Projection: $56.29/day
  Last Hour Cost:   $2.3456
  Last Day Cost:    $48.2345

📍 BY AGENT:
  Planner                        $  5.2345 ( 42.0%)
  Coder                          $  3.1234 ( 25.1%)
  Auditor                        $  2.0123 ( 16.2%)
  TestGeneratorAgent             $  1.5432 ( 12.4%)
  ChiefArchitect                 $  0.3456 (  2.8%)
  LearningAgent                  $  0.1234 (  1.0%)
  MergerAgent                    $  0.0543 (  0.4%)
  ToolSmithAgent                 $  0.0100 (  0.1%)

🤖 BY MODEL:
  gpt-5-2025-08-07               $  8.7654 ( 70.4%)
  gpt-4o-mini-2024-07-18         $  2.3456 ( 18.8%)
  gpt-5-nano-2025-08-07          $  1.3457 ( 10.8%)

======================================================================
```

### Example 2: Live Dashboard with Budget Alert

**Command:**
```bash
python agency.py cost-dashboard --live --budget 50.0 --warning-pct 80
```

**Output (updates every 5 seconds):**
```
================================================================================
TRINITY PROTOCOL - REAL-TIME COST DASHBOARD
Updated: 2025-10-01 15:32:15
================================================================================

SUMMARY
  Total Spent:        $42.3456
  Total Calls:        5,678
  Total Tokens:       1,234,567
  Success Rate:       99.9%
  Hourly Rate:        $3.4567/hour
  Daily Projection:   $82.96/day

BUDGET
  Budget:             $50.00
  Spent:              $42.3456 (84.7%)
  Remaining:          $7.6544
  [█████████████████████████████████████████░░░░░░░░░░]

⚠️  WARNING: 84.7% of budget used!

PER-AGENT COSTS
  Planner              $18.2345 (43.1%) ████████████████████████████████
  Coder                $12.3456 (29.2%) █████████████████████████
  Auditor              $ 6.7890 (16.0%) ████████████
  TestGenerator        $ 3.4567 ( 8.2%) ██████
  LearningAgent        $ 1.1234 ( 2.7%) ██
  ChiefArchitect       $ 0.2345 ( 0.6%) ▓
  MergerAgent          $ 0.1234 ( 0.3%) ▓
  ToolSmith            $ 0.0385 ( 0.1%) ░

RECENT ACTIVITY
  15:32:15 | Planner              | $0.1234 | ✓
  15:32:12 | Coder                | $0.2345 | ✓
  15:32:09 | Auditor              | $0.0789 | ✓
  15:32:06 | TestGenerator        | $0.1456 | ✓
  15:32:03 | Planner              | $0.0987 | ✓

Controls: [Q]uit | [E]xport | [R]efresh
```

### Example 3: Export to CSV/JSON

**Command:**
```bash
python agency.py cost-dashboard --live
# Press 'E' while running
```

**Output:**
```
Exported: trinity_costs_20251001_153245.csv and trinity_costs_20251001_153245.json
```

**CSV Contents (sample):**
```csv
timestamp,agent,model,model_tier,input_tokens,output_tokens,cost_usd,duration_seconds,success,task_id,correlation_id
2025-10-01T15:30:45,Planner,gpt-5-2025-08-07,cloud_premium,234,156,0.0031,2.34,True,task-123,session-456
2025-10-01T15:30:42,Coder,gpt-4o-mini-2024-07-18,cloud_mini,567,234,0.0002,1.23,True,task-124,session-456
```

**JSON Contents (sample):**
```json
{
  "exported_at": "2025-10-01T15:32:45",
  "summary": {
    "total_cost_usd": 42.3456,
    "total_calls": 5678,
    "total_input_tokens": 834567,
    "total_output_tokens": 400000,
    "success_rate": 0.999,
    "by_agent": {
      "Planner": 18.2345,
      "Coder": 12.3456,
      "Auditor": 6.7890
    },
    "by_model": {
      "gpt-5-2025-08-07": 35.6789,
      "gpt-4o-mini-2024-07-18": 5.1234,
      "gpt-5-nano-2025-08-07": 1.5433
    }
  },
  "trends": {
    "hourly_rate": 3.4567,
    "daily_projection": 82.96,
    "last_hour_cost": 3.4567,
    "last_day_cost": 78.2345
  },
  "budget": {
    "limit": 50.0,
    "spent": 42.3456,
    "remaining": 7.6544,
    "percent_used": 84.69
  }
}
```

---

## Web Dashboard Examples

### Example 1: Basic Web Dashboard

**Command:**
```bash
python agency.py cost-web --port 8080 --budget 100
```

**Output:**
```
🚀 Starting Trinity Cost Dashboard
📊 Open http://localhost:8080 in your browser
🔄 Refresh interval: 5 seconds

Press Ctrl+C to stop

 * Serving Flask app 'cost_dashboard_web'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://192.168.1.100:8080
```

**Browser Screenshot Description:**

The web dashboard shows:

1. **Header Section** (gradient purple background)
   - Title: "Trinity Protocol Cost Dashboard" with green "● LIVE" indicator
   - Subtitle: "Real-time LLM cost monitoring and budget tracking"

2. **Summary Cards** (white cards with shadow)
   - **Total Spending Card:**
     - Total Cost: $12.4567
     - Total Calls: 1,234
     - Total Tokens: 567,890
     - Success Rate: 99.8% (green)

   - **Spending Trends Card:**
     - Hourly Rate: $2.3456/hr
     - Daily Projection: $56.29/day
     - Last Hour: $2.3456
     - Last 24h: $48.2345

   - **Budget Status Card:**
     - Budget: $100.00
     - Progress bar: 12.5% filled (green)
     - Remaining: $87.5433

3. **Agent Breakdown Section**
   - **Left Panel:** Sortable list with progress bars
     - Planner: $5.2345 (42.0%) [████████████]
     - Coder: $3.1234 (25.1%) [████████]
     - Auditor: $2.0123 (16.2%) [█████]

   - **Right Panel:** Interactive doughnut chart
     - Color-coded segments for each agent
     - Hover shows exact amounts

4. **Footer**
   - "Last updated: 15:32:45"
   - "Trinity Protocol • Real-time Cost Monitoring"

### Example 2: Budget Alert in Web Dashboard

When budget exceeds 80%, the budget card shows:
- Progress bar turns **yellow** (80-90%)
- Progress bar turns **red** (90%+)
- Warning message appears: "⚠️ WARNING: 84.7% of budget used!"

---

## Alert System Examples

### Example 1: Single Alert Check (No Alerts)

**Command:**
```bash
python agency.py cost-alerts --budget 100 --hourly-max 10
```

**Output:**
```
2025-10-01 15:35:00 - trinity.cost_alerts - INFO - Cost alert system initialized
✅ No alerts triggered. All costs within limits.
```

### Example 2: Budget Threshold Alert

**Command:**
```bash
python agency.py cost-alerts --budget 50
# (with current spend at $42.34)
```

**Output:**
```
2025-10-01 15:36:15 - trinity.cost_alerts - INFO - Cost alert system initialized
2025-10-01 15:36:15 - trinity.cost_alerts - WARNING - [WARNING] Budget 80% Threshold Exceeded: Spent $42.3456 of $50.00 budget (84.7%). Threshold: 80%

⚠️  1 alert(s) triggered:

[WARNING] Budget 80% Threshold Exceeded
  Spent $42.3456 of $50.00 budget (84.7%). Threshold: 80%
```

### Example 3: Multiple Alerts

**Command:**
```bash
python agency.py cost-alerts \
  --budget 50 \
  --hourly-max 2.0 \
  --daily-max 40.0
```

**Output (when thresholds exceeded):**
```
2025-10-01 15:37:30 - trinity.cost_alerts - INFO - Cost alert system initialized
2025-10-01 15:37:30 - trinity.cost_alerts - WARNING - [WARNING] Budget 80% Threshold Exceeded: Spent $42.3456 of $50.00 budget (84.7%). Threshold: 80%
2025-10-01 15:37:30 - trinity.cost_alerts - WARNING - [WARNING] Hourly Spending Rate Exceeded: Spent $3.4567 in the last hour. Limit: $2.00/hour
2025-10-01 15:37:30 - trinity.cost_alerts - WARNING - [WARNING] Daily Budget Projection Exceeded: Current spending rate projects to $82.96/day. Daily limit: $40.00

⚠️  3 alert(s) triggered:

[WARNING] Budget 80% Threshold Exceeded
  Spent $42.3456 of $50.00 budget (84.7%). Threshold: 80%

[WARNING] Hourly Spending Rate Exceeded
  Spent $3.4567 in the last hour. Limit: $2.00/hour

[WARNING] Daily Budget Projection Exceeded
  Current spending rate projects to $82.96/day. Daily limit: $40.00
```

### Example 4: Spending Spike Detection

**Command:**
```bash
python agency.py cost-alerts --budget 100
# (when current hourly rate is 3x baseline)
```

**Output:**
```
2025-10-01 15:38:45 - trinity.cost_alerts - INFO - Cost alert system initialized
2025-10-01 15:38:45 - trinity.cost_alerts - WARNING - [WARNING] Spending Spike Detected: Current spending rate ($6.7890/hour) is 3.2x baseline ($2.1234/hour)

⚠️  1 alert(s) triggered:

[WARNING] Spending Spike Detected
  Current spending rate ($6.7890/hour) is 3.2x baseline ($2.1234/hour)
```

### Example 5: Continuous Monitoring

**Command:**
```bash
python agency.py cost-alerts --continuous --interval 300 --budget 100
```

**Output:**
```
2025-10-01 15:40:00 - trinity.cost_alerts - INFO - Cost alert system initialized
Starting continuous cost monitoring (checking every 300s)
Press Ctrl+C to stop

⚠️  1 alert(s) triggered at 2025-10-01 15:45:00
  [WARNING] Budget 80% Threshold Exceeded

⚠️  2 alert(s) triggered at 2025-10-01 15:50:00
  [WARNING] Budget 90% Threshold Exceeded
  [WARNING] Hourly Spending Rate Exceeded

^C
Monitoring stopped by user.

Alert Summary:
  budget_80: 2 time(s)
  budget_90: 1 time(s)
  hourly_rate: 1 time(s)
```

### Example 6: Email Alert Configuration

**Setup:**
```bash
export EMAIL_ENABLED=true
export EMAIL_SMTP_HOST=smtp.gmail.com
export EMAIL_SMTP_PORT=587
export EMAIL_FROM=trinity-alerts@company.com
export EMAIL_TO=team@company.com,manager@company.com
export EMAIL_PASSWORD=your_app_password

python agency.py cost-alerts --continuous --budget 100
```

**Email Received:**
```
From: trinity-alerts@company.com
To: team@company.com, manager@company.com
Subject: [Trinity Alert] Budget 90% Threshold Exceeded

Spent $45.6789 of $50.00 budget (91.4%). Threshold: 90%

---
Trinity Protocol Cost Alert System
Sent at: 2025-10-01 15:52:30
```

---

## Programmatic Usage Examples

### Example 1: Basic Cost Tracking

```python
from trinity_protocol.cost_tracker import CostTracker
from shared.llm_cost_wrapper import wrap_openai_client
from openai import OpenAI

# Create cost tracker with $10 budget
tracker = CostTracker(db_path="my_project_costs.db", budget_usd=10.0)

# Enable tracking for all OpenAI calls
wrap_openai_client(tracker, agent_name="MyScript", task_id="experiment-1")

# Make API calls (automatically tracked)
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    max_completion_tokens=200,
    reasoning_effort="low"
)

print(f"Response: {response.choices[0].message.content}")

# View summary
summary = tracker.get_summary()
print(f"\n💰 Total cost: ${summary.total_cost_usd:.4f}")
print(f"📞 Total calls: {summary.total_calls}")
print(f"🔢 Total tokens: {summary.total_input_tokens + summary.total_output_tokens:,}")

# View recent calls
print("\nRecent calls:")
for call in tracker.get_recent_calls(limit=5):
    print(f"  {call.timestamp} | {call.agent} | ${call.cost_usd:.6f}")

tracker.close()
```

**Output:**
```
Response: Quantum computing leverages quantum mechanics principles...

💰 Total cost: $0.0134
📞 Total calls: 1
🔢 Total tokens: 589

Recent calls:
  2025-10-01T15:55:30 | MyScript | $0.013400
```

### Example 2: Multi-Agent Cost Comparison

```python
from trinity_protocol.cost_tracker import CostTracker, ModelTier
from shared.llm_cost_wrapper import wrap_openai_client
from openai import OpenAI

tracker = CostTracker(db_path=":memory:")
client = OpenAI()

# Test different models
models_to_test = [
    ("gpt-5", "low"),
    ("gpt-4o-mini", None),
]

for model, reasoning_effort in models_to_test:
    # Create separate tracking context for each model
    wrap_openai_client(tracker, agent_name=f"Test-{model}")

    params = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_completion_tokens": 10
    }

    if reasoning_effort:
        params["reasoning_effort"] = reasoning_effort

    response = client.chat.completions.create(**params)
    print(f"{model}: {response.choices[0].message.content}")

# Compare costs
summary = tracker.get_summary()
print("\n📊 Cost Comparison:")
for agent, cost in sorted(summary.by_agent.items()):
    print(f"  {agent:30s} ${cost:.6f}")

print(f"\nTotal: ${summary.total_cost_usd:.6f}")
```

**Output:**
```
gpt-5: Hello! How can I help you?
gpt-4o-mini: Hi there! How can I assist you?

📊 Cost Comparison:
  Test-gpt-5                     $0.000225
  Test-gpt-4o-mini               $0.000009

Total: $0.000234
```

### Example 3: Context Manager for Scoped Tracking

```python
from trinity_protocol.cost_tracker import CostTracker
from shared.llm_cost_wrapper import create_cost_tracking_context
from openai import OpenAI

tracker = CostTracker(db_path=":memory:")
client = OpenAI()

# Only track calls within this context
with create_cost_tracking_context(tracker, "ExperimentA"):
    response_a = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Test A"}]
    )

# This call is NOT tracked (outside context)
response_b = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Test B"}]
)

summary = tracker.get_summary()
print(f"Tracked calls: {summary.total_calls}")  # Shows 1, not 2
print(f"Total cost: ${summary.total_cost_usd:.6f}")
```

**Output:**
```
Tracked calls: 1
Total cost: $0.000009
```

### Example 4: Historical Cost Analysis

```python
from trinity_protocol.cost_tracker import CostTracker
from datetime import datetime, timedelta

tracker = CostTracker(db_path="trinity_costs.db")

# Get costs for different time periods
now = datetime.now()
one_hour_ago = now - timedelta(hours=1)
one_day_ago = now - timedelta(days=1)
one_week_ago = now - timedelta(weeks=1)

# Last hour
hourly = tracker.get_summary(since=one_hour_ago)
print(f"Last Hour:  ${hourly.total_cost_usd:.4f} ({hourly.total_calls} calls)")

# Last day
daily = tracker.get_summary(since=one_day_ago)
print(f"Last Day:   ${daily.total_cost_usd:.4f} ({daily.total_calls} calls)")

# Last week
weekly = tracker.get_summary(since=one_week_ago)
print(f"Last Week:  ${weekly.total_cost_usd:.4f} ({weekly.total_calls} calls)")

# All time
total = tracker.get_summary()
print(f"All Time:   ${total.total_cost_usd:.4f} ({total.total_calls} calls)")

# Calculate trends
hourly_rate = hourly.total_cost_usd
daily_projection = hourly_rate * 24
weekly_projection = daily_projection * 7

print(f"\n📈 Projections (based on last hour):")
print(f"  Daily:  ${daily_projection:.2f}")
print(f"  Weekly: ${weekly_projection:.2f}")
```

**Output:**
```
Last Hour:  $2.3456 (45 calls)
Last Day:   $48.2345 (1,234 calls)
Last Week:  $276.8901 (8,567 calls)
All Time:   $1,234.5678 (42,345 calls)

📈 Projections (based on last hour):
  Daily:  $56.29
  Weekly: $394.06
```

### Example 5: Task-Specific Cost Tracking

```python
from trinity_protocol.cost_tracker import CostTracker
from shared.llm_cost_wrapper import wrap_openai_client
from openai import OpenAI

tracker = CostTracker(db_path="feature_costs.db")
client = OpenAI()

# Feature A development
wrap_openai_client(tracker, agent_name="Coder", task_id="feature-auth")
# ... make API calls for auth feature ...

# Feature B development
wrap_openai_client(tracker, agent_name="Coder", task_id="feature-payments")
# ... make API calls for payments feature ...

# Compare feature costs
auth_costs = tracker.get_summary(task_id="feature-auth")
payments_costs = tracker.get_summary(task_id="feature-payments")

print("Feature Cost Comparison:")
print(f"  Authentication: ${auth_costs.total_cost_usd:.4f}")
print(f"  Payments:       ${payments_costs.total_cost_usd:.4f}")

# Find most expensive feature
total = tracker.get_summary()
print(f"\nAll Features:")
for task, cost in sorted(total.by_task.items(), key=lambda x: -x[1]):
    pct = (cost / total.total_cost_usd * 100) if total.total_cost_usd > 0 else 0
    print(f"  {task:25s} ${cost:.4f} ({pct:.1f}%)")
```

**Output:**
```
Feature Cost Comparison:
  Authentication: $12.3456
  Payments:       $8.7654

All Features:
  feature-auth              $12.3456 (58.5%)
  feature-payments          $ 8.7654 (41.5%)
```

---

## Integration Examples

### Example 1: Agency Agent with Cost Tracking

```python
from shared.agent_context import create_agent_context
from trinity_protocol.cost_tracker import CostTracker
from agency_code_agent.agency_code_agent import create_agency_code_agent

# Create shared cost tracker
tracker = CostTracker(db_path="agency_costs.db", budget_usd=100.0)

# Create agent context
context = create_agent_context()

# Create agent with cost tracking
agent = create_agency_code_agent(
    model="gpt-5",
    reasoning_effort="medium",
    agent_context=context,
    cost_tracker=tracker
)

print(f"✅ {agent.name} created with cost tracking")
print(f"   Budget: ${tracker.budget_usd:.2f}")
print(f"   Database: {tracker.db_path}")

# Verify integration
assert hasattr(context, 'cost_tracker')
assert context.cost_tracker is tracker
print(f"   Cost tracker attached to context: ✓")
```

**Output:**
```
✅ AgencyCodeAgent created with cost tracking
   Budget: $100.00
   Database: agency_costs.db
   Cost tracker attached to context: ✓
```

### Example 2: Multi-Agent System with Shared Tracker

```python
from trinity_protocol.cost_tracker import CostTracker
from shared.agent_context import create_agent_context
from agency_code_agent.agency_code_agent import create_agency_code_agent
from test_generator_agent.test_generator_agent import create_test_generator_agent
from toolsmith_agent.toolsmith_agent import create_toolsmith_agent

# Shared cost tracker for all agents
shared_tracker = CostTracker(db_path="team_costs.db", budget_usd=500.0)
shared_context = create_agent_context()

# Create multiple agents
agents = []
agent_factories = [
    (create_agency_code_agent, "gpt-5", "medium"),
    (create_test_generator_agent, "gpt-5", "high"),
    (create_toolsmith_agent, "gpt-4o-mini", "low"),
]

for factory, model, reasoning in agent_factories:
    agent = factory(
        model=model,
        reasoning_effort=reasoning,
        agent_context=shared_context,
        cost_tracker=shared_tracker
    )
    agents.append(agent)
    print(f"✅ {agent.name:30s} | {model:20s} | {reasoning}")

print(f"\n📊 All {len(agents)} agents share the same cost tracker")
print(f"   Any LLM calls will be tracked together")
print(f"   Shared budget: ${shared_tracker.budget_usd:.2f}")
```

**Output:**
```
✅ AgencyCodeAgent              | gpt-5                | medium
✅ TestGeneratorAgent           | gpt-5                | high
✅ ToolSmithAgent               | gpt-4o-mini          | low

📊 All 3 agents share the same cost tracker
   Any LLM calls will be tracked together
   Shared budget: $500.00
```

### Example 3: Cost Tracking with Real-Time Dashboard

```python
import threading
import time
from trinity_protocol.cost_tracker import CostTracker
from trinity_protocol.cost_dashboard import CostDashboard
from shared.llm_cost_wrapper import wrap_openai_client
from openai import OpenAI

# Create tracker
tracker = CostTracker(db_path=":memory:", budget_usd=10.0)

# Start dashboard in background thread
dashboard = CostDashboard(tracker, refresh_interval=2)

def run_dashboard():
    dashboard.run_terminal_dashboard()

dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
dashboard_thread.start()

# Make API calls while dashboard updates
wrap_openai_client(tracker, agent_name="LiveTest")
client = OpenAI()

for i in range(5):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Test {i}"}],
        max_tokens=10
    )
    print(f"Call {i+1}: {response.choices[0].message.content}")
    time.sleep(3)  # Dashboard updates between calls

# Dashboard continues updating in background
print("\nDashboard running in background. Press Ctrl+C to stop.")
time.sleep(30)
```

This example shows live cost updates as API calls are made.

---

## Summary

These examples demonstrate:

1. **CLI Dashboard**: Snapshot and live monitoring modes
2. **Web Dashboard**: Beautiful browser-based interface with real-time updates
3. **Alert System**: Multiple alert types (budget, rate, spike detection)
4. **Programmatic Usage**: Flexible API for custom integrations
5. **Multi-Agent Integration**: Shared cost tracking across agent teams

For more details, see the main documentation: [docs/COST_TRACKING.md](COST_TRACKING.md)
