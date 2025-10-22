# Constitutional Guardian - Autonomous Codebase Health Agent

**Purpose**: 24/7 autonomous monitoring and fixing of broken windows, constitutional violations, and technical debt.

**Model**: Qwen3-Coder-30B (local, $0 cost)
**Runtime**: Continuous background daemon on M4 Pro 48GB
**Autonomy Level**: Full (operates without human approval for safe fixes)

---

## What It Does

**The Constitutional Guardian autonomously:**

1. **Monitors** (every 6 hours):
   - Compiled files (.pyc, __pycache__)
   - Misplaced output files (outside .output/)
   - TODO/FIXME comments without GitHub issues
   - Functions >50 lines
   - Bare exception handlers
   - Missing type hints
   - Skipped tests without justification

2. **Fixes** (automatically):
   - Remove compiled files
   - Organize misplaced outputs
   - Extract large functions
   - Add specific exception types
   - Add type hints
   - Document TODO reasons

3. **Reports** (to .output/guardian/):
   - Daily health reports
   - Auto-fix summaries
   - Escalation alerts (needs human review)

4. **Learns** (Article IV):
   - Stores fix patterns to VectorStore
   - Improves classification over time
   - Adapts to codebase conventions

---

## Usage

### Start Guardian Daemon
```bash
# Start 24/7 background monitoring
python tools/constitutional_guardian.py --daemon

# Start with custom interval (default: 6 hours)
python tools/constitutional_guardian.py --daemon --interval 4h

# One-time scan and fix
python tools/constitutional_guardian.py --once
```

### Check Guardian Status
```bash
# View current status
python tools/constitutional_guardian.py --status

# View recent fixes
cat .output/guardian/latest_fixes.json

# View health report
cat .output/guardian/health_report_$(date +%Y%m%d).md
```

### Using Slash Command
```bash
# Run guardian once (scan + auto-fix)
/constitutional-guardian

# Run with mission graph
/constitutional-guardian --graph missions/solidify_test_base_hanging_tests.json

# Visualize planned fixes before applying
/constitutional-guardian --dry-run --visualize
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Constitutional Guardian Daemon          │
│                                                 │
│  ┌──────────────┐    ┌───────────────────┐     │
│  │   Monitor    │───▶│  Classification   │     │
│  │   (6h cycle) │    │  (safe vs risky)  │     │
│  └──────────────┘    └───────────────────┘     │
│         │                     │                 │
│         ▼                     ▼                 │
│  ┌──────────────┐    ┌───────────────────┐     │
│  │  Safe Fixes  │    │  Human Review     │     │
│  │  (auto-apply)│    │  (escalate)       │     │
│  └──────────────┘    └───────────────────┘     │
│         │                     │                 │
│         ▼                     ▼                 │
│  ┌──────────────┐    ┌───────────────────┐     │
│  │ Git Commit   │    │ GitHub Issue      │     │
│  │ (auto)       │    │ (create)          │     │
│  └──────────────┘    └───────────────────┘     │
│         │                                       │
│         ▼                                       │
│  ┌──────────────┐                              │
│  │ VectorStore  │                              │
│  │ (learning)   │                              │
│  └──────────────┘                              │
└─────────────────────────────────────────────────┘
```

---

## Safety Classification

**Auto-Fix (Safe - No Review):**
- Remove compiled files
- Organize output files
- Run cleanup scripts
- Add docstring stubs
- Add type hints to simple functions
- Document TODOs with GitHub issues

**Escalate (Risky - Human Review):**
- Refactor functions >100 lines
- Change exception handling
- Modify test logic
- Update configuration
- Change API contracts

---

## Configuration

```python
# .agency/guardian_config.json
{
  "enabled": true,
  "interval_hours": 6,
  "model": "qwen3-coder:30b",
  "auto_commit": true,
  "escalation_webhook": null,
  "safety_threshold": 0.85,
  "max_fixes_per_run": 10
}
```

---

## Integration with Existing Tools

**Uses:**
- `scripts/cleanup_compiled_files.py` - File cleanup
- `tools/auditor_agent/auditor_agent.py` - Code analysis
- `shared/adaptive_model_router.py` - Task classification
- `shared/agent_context.py` - VectorStore learning

**Integrates With:**
- Pre-commit hooks (validates before commit)
- GitHub Actions (optional CI integration)
- VectorStore (Article IV learning)
- Local Ollama (Qwen3-Coder-30B)

---

## Metrics

**Success Criteria:**
- Zero compiled files in repo (daily)
- <10 TODOs without issues (weekly)
- <5 functions >50 lines (monthly)
- 100% test pass rate (always)
- >95% auto-fix success rate

**Cost:**
- Local model: $0/month
- Runtime: ~50MB RAM, 5% CPU
- Disk: <100MB logs/reports

---

## Constitutional Compliance

- **Article I**: Complete context (full codebase scan)
- **Article II**: 100% verification (test before commit)
- **Article III**: Automated enforcement (no manual vigilance)
- **Article IV**: Continuous learning (VectorStore patterns)
- **Article V**: Spec-driven (follows ADR-033 test maintenance)

---

## Example Session

```bash
$ python tools/constitutional_guardian.py --once

🛡️  Constitutional Guardian - Autonomous Codebase Health
═══════════════════════════════════════════════════════

📊 Scanning codebase...
   - 1,234 Python files
   - 5,743 tests (146 skipped)
   - 47 potential issues found

🔍 Classification (Qwen3-Coder-30B)...
   - 38 safe auto-fixes
   - 9 escalations (human review)

✅ Auto-Fixes Applied:
   1. Removed 12 compiled files
   2. Organized 3 misplaced outputs
   3. Added docstrings to 8 functions
   4. Created GitHub issues for 5 TODOs
   5. Added type hints to 10 functions

📝 Committed: "chore(guardian): Autonomous fixes (38 items)"

⚠️  Escalations Created:
   - Issue #42: Refactor system_hooks.py (987 lines)
   - Issue #43: Fix 146 skipped tests
   - Issue #44: Bare exception handlers in hooks

💾 Learning Patterns Stored:
   - Fix success rate: 95%
   - Time saved: 2.3 hours
   - Confidence: 0.89

✅ Guardian cycle complete
   Next run: 2025-10-22 22:30:00

Report: .output/guardian/health_report_20251022.md
```

---

## Installation

```bash
# Install as launchd service (macOS)
python tools/constitutional_guardian.py --install-daemon

# Start immediately
launchctl start com.agency.guardian

# Check status
launchctl list | grep guardian
```

---

**The Guardian Never Sleeps** - Exponential improvement while you code.
