# Trinity Protocol - 24-Hour Autonomous Operation Test Suite

Complete testing infrastructure for validating 24/7 autonomous operation with real cost tracking, pattern learning, and comprehensive monitoring.

---

## Overview

This test suite validates Trinity Protocol's production readiness by running all three agents (WITNESS, ARCHITECT, EXECUTOR) continuously for 24 hours with:

- **Real LLM calls** (local + cloud GPT-5)
- **Cost tracking** with budget enforcement
- **Pattern persistence** across sessions
- **Event simulation** with 5 realistic categories
- **Real-time monitoring** dashboards
- **Comprehensive reporting** with success criteria validation

---

## Test Components

### 1. Test Specification (`docs/trinity_protocol/24H_AUTONOMOUS_TEST.md`)

Complete test plan with:
- Success criteria (mandatory & performance)
- Event scenarios (5 categories × 48 cycles)
- Monitoring setup (3 dashboards)
- Budget planning ($5.76 estimated, $10 budget)
- Data collection structure
- Anomaly detection rules

### 2. Event Simulator (`event_simulator.py`)

Generates realistic events for testing:

```python
from trinity_protocol.event_simulator import EventSimulator

simulator = EventSimulator(seed=42)  # Deterministic
events = simulator.generate_continuous_stream(
    interval_minutes=30,
    duration_hours=24
)
```

**Event categories**:
- Critical errors (NoneType, crashes, security)
- Constitutional violations (type safety, TDD gaps)
- Feature requests (user intents, enhancements)
- Code quality (duplication, complexity)
- Test reliability (flaky tests, coverage gaps)

### 3. Test Execution Script (`run_24h_test.py`)

Main test controller with:
- Agent initialization and orchestration
- Event publishing every 30 minutes
- Hourly cost/pattern snapshots
- 5-minute system metrics
- Real-time anomaly detection
- Graceful shutdown and cleanup

**Usage**:
```bash
# Full 24-hour test
python trinity_protocol/run_24h_test.py --duration 24 --budget 10.00

# Quick 2-hour smoke test
python trinity_protocol/run_24h_test.py --duration 2 --budget 2.00

# Custom configuration
python trinity_protocol/run_24h_test.py \
  --duration 12 \
  --budget 5.00 \
  --event-interval 15 \
  --snapshot-interval 30
```

### 4. Real-Time Dashboards

#### Cost Dashboard (`cost_dashboard.py`)
- Total cost vs budget with progress bar
- Per-agent cost breakdown
- Per-model cost breakdown
- API call statistics
- Success rate tracking
- Recent activity log

```bash
# Live dashboard (5-second refresh)
python trinity_protocol/cost_dashboard.py --live --budget 10.00

# Single snapshot
python trinity_protocol/cost_dashboard.py --once

# Export data
python trinity_protocol/cost_dashboard.py --export costs.csv
```

#### Pattern Dashboard (`pattern_dashboard.py`)
- Events processed vs expected
- Detection rate and accuracy
- Pattern type distribution
- Top patterns by frequency
- Queue health monitoring

```bash
# Live dashboard (1-minute refresh)
python trinity_protocol/pattern_dashboard.py --live --expected-events 48

# Single snapshot
python trinity_protocol/pattern_dashboard.py --once
```

#### System Dashboard (`system_dashboard.py`)
- CPU and memory usage
- Disk I/O statistics
- Message queue backlogs
- Agent health status
- Uptime tracking

```bash
# Live dashboard (5-minute refresh)
python trinity_protocol/system_dashboard.py --live

# Single snapshot with custom refresh
python trinity_protocol/system_dashboard.py --live --refresh 60
```

### 5. Report Generator (`generate_24h_report.py`)

Generates comprehensive markdown report with:
- Test summary
- Success criteria validation (pass/fail)
- Performance metrics
- Cost analysis with trends
- Pattern detection statistics
- System health report
- Incidents and alerts
- Recommendations
- Production readiness conclusion

```bash
# Generate report
python trinity_protocol/generate_24h_report.py \
  --input logs/24h_test/ \
  --output reports/24h_test_$(date +%Y%m%d).md

# View report
cat reports/24h_test_*.md
```

---

## Quick Start

### Minimum Test (30 minutes, $0.50)

```bash
# Clean slate
rm -f trinity_*.db
rm -rf logs/24h_test/

# Run test
python trinity_protocol/run_24h_test.py --duration 0.5 --budget 0.50

# Monitor in separate terminal
python trinity_protocol/cost_dashboard.py --live --budget 0.50

# Generate report
python trinity_protocol/generate_24h_report.py \
  --input logs/24h_test/ \
  --output reports/smoke_test.md
```

### Full 24-Hour Test ($10 budget)

```bash
# Terminal 1: Test execution
python trinity_protocol/run_24h_test.py --duration 24 --budget 10.00

# Terminal 2: Cost monitoring
python trinity_protocol/cost_dashboard.py --live --budget 10.00

# Terminal 3: Pattern monitoring
python trinity_protocol/pattern_dashboard.py --live --expected-events 48

# Terminal 4: System monitoring
python trinity_protocol/system_dashboard.py --live

# After completion:
python trinity_protocol/generate_24h_report.py \
  --input logs/24h_test/ \
  --output reports/24h_test_production_validation.md
```

---

## Success Criteria

### Mandatory (All Must Pass)

| Criterion | Target | Measured By |
|-----------|--------|-------------|
| Zero crashes | 0 crashes | Process monitoring |
| Event detection | 100% | WITNESS stats |
| Pattern persistence | All patterns restored | Database query |
| Cost tracking | 100% calls tracked | CostTracker audit |
| Memory stability | <500MB | System metrics |
| Queue health | <50 backlog | MessageBus stats |

### Performance (Target >90%)

| Criterion | Target | Measured By |
|-----------|--------|-------------|
| Detection accuracy | >90% | Manual validation |
| Detection latency | <2 seconds | Timestamp analysis |
| Pattern confidence | >0.75 | PatternDetector stats |
| Cost efficiency | >70% local | Model routing stats |

---

## Output Structure

```
logs/24h_test/
├── costs/
│   ├── cost_snapshot_000000.json      # Hour 0
│   ├── cost_snapshot_010000.json      # Hour 1
│   └── ...                             # Hour 2-24
├── patterns/
│   ├── pattern_stats_000000.json
│   └── ...
├── metrics/
│   ├── system_metrics_000000.json     # Every 5 minutes
│   ├── system_metrics_000500.json
│   └── ...
├── trinity.log                         # Main event log
├── alerts.log                          # Alerts and warnings
└── test_config.json                    # Test configuration

reports/
└── 24h_test_YYYYMMDD.md               # Validation report
```

---

## Budget Planning

### Estimated Costs

**24-hour test (48 events)**:

| Component | Events | Cost per Event | Total |
|-----------|--------|----------------|-------|
| WITNESS | 48 | $0.00 (local) | $0.00 |
| ARCHITECT | 48 | $0.04 | $1.92 |
| EXECUTOR | 48 | $0.08 | $3.84 |
| **Total** | | | **$5.76** |

**Recommended budget**: $10.00 (73% buffer)

### Budget Alerts

- 50% consumed → INFO
- 75% consumed → WARNING
- 90% consumed → ALERT

Test continues past budget but logs errors.

---

## Troubleshooting

### Test Fails to Start

```bash
# Check Ollama
ollama list

# Verify models
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5-coder:7b

# Check environment
echo $OPENAI_API_KEY

# Verify dependencies
python -c "import psutil, asyncio, sqlite3; print('OK')"
```

### High Memory Usage

```bash
# Check system metrics
python trinity_protocol/system_dashboard.py --once

# If memory >500MB, investigate:
# 1. FAISS index size
# 2. Message queue backlog
# 3. SQLite cache size
```

### Cost Exceeds Budget

```bash
# Check cost breakdown
python trinity_protocol/cost_dashboard.py --once

# Identify expensive operations:
# 1. Which agent spending most?
# 2. Which model (local vs cloud)?
# 3. Cloud escalation frequency?

# Adjust test parameters:
python trinity_protocol/run_24h_test.py --duration 2 --budget 2.00
```

### Queue Backlog

```bash
# Check queue health
python trinity_protocol/pattern_dashboard.py --once

# If backlog >50:
# 1. Reduce event interval (--event-interval 60)
# 2. Check agent processing speed
# 3. Verify no infinite loops
```

---

## Continuous Testing

### Weekly Smoke Test (2 hours)

```bash
# Automated weekly test
0 0 * * 0 cd /path/to/Agency && python trinity_protocol/run_24h_test.py --duration 2 --budget 2.00
```

### Monthly Full Test (24 hours)

```bash
# First Sunday of month
0 0 1-7 * 0 cd /path/to/Agency && python trinity_protocol/run_24h_test.py --duration 24 --budget 10.00
```

### Regression Testing

After code changes:

```bash
# 1. Run unit tests
python -m pytest tests/trinity_protocol/ -o addopts="" -q

# 2. Run 30-minute smoke test
python trinity_protocol/run_24h_test.py --duration 0.5 --budget 0.50

# 3. Verify no regressions
python trinity_protocol/generate_24h_report.py \
  --input logs/24h_test/ \
  --output reports/regression_test.md
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              run_24h_test.py (Test Controller)              │
│  - Agent orchestration                                      │
│  - Event simulation loop                                    │
│  - Snapshot generation                                      │
│  - Anomaly detection                                        │
└─────────────┬───────────────────────────────────────────────┘
              │
              ├─→ EventSimulator ───→ telemetry_stream
              │
              ├─→ WITNESS Agent ───→ improvement_queue
              │
              ├─→ ARCHITECT Agent ───→ execution_queue
              │
              ├─→ EXECUTOR Agent ───→ telemetry_stream (loop closure)
              │
              ├─→ CostTracker ───→ logs/24h_test/costs/
              │
              ├─→ PatternStore ───→ logs/24h_test/patterns/
              │
              └─→ SystemMetrics ───→ logs/24h_test/metrics/
```

---

## Configuration

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional
export TRINITY_TEST_BUDGET=10.00
export TRINITY_TEST_DURATION=24
export TRINITY_EVENT_INTERVAL=30
export TRINITY_SNAPSHOT_INTERVAL=60
export TRINITY_METRICS_INTERVAL=5
```

### Test Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--duration` | 24 | Test duration (hours) |
| `--budget` | 10.00 | Budget limit (USD) |
| `--event-interval` | 30 | Minutes between events |
| `--snapshot-interval` | 60 | Minutes between snapshots |
| `--metrics-interval` | 5 | Minutes between metrics |

---

## Known Limitations

1. **Resume functionality** not yet implemented
2. **Agent heartbeat** checking is placeholder
3. **Detection accuracy** requires manual validation
4. **Mid-test restart** validation not automated
5. **Firestore integration** pending (using SQLite)

---

## Future Enhancements

1. **Resume from checkpoint** - Restart test from failure point
2. **Live charts** - Web dashboard with real-time graphs
3. **Alert webhooks** - Slack/Discord notifications
4. **A/B testing** - Compare different configurations
5. **Stress testing** - Higher event rates, budget limits
6. **Distributed testing** - Multi-node agent deployment

---

## References

- **Specification**: `docs/trinity_protocol/24H_AUTONOMOUS_TEST.md`
- **Quick Start**: `docs/trinity_protocol/QUICKSTART.md` (Phase 3)
- **Architecture**: `docs/trinity_protocol/README.md`
- **Cost Tracking**: `trinity_protocol/cost_tracker.py`
- **Pattern Store**: `trinity_protocol/persistent_store.py`

---

**Status**: Ready for Production Validation
**Version**: 1.0.0
**Last Updated**: 2025-10-01
