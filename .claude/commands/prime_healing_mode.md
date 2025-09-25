## Mission: Autonomous Self-Healing

Your context is now focused on activating and managing the autonomous self-healing functions of the system.

### Workflow
1. **Check System Status:** Run `./agency_cli health` to determine current health state.
2. **Analyze Telemetry:** Call `/agent learning_agent` with focus on telemetry pattern analysis.
3. **Identify Errors:** Use `core/self_healing.py` to detect current issues.
4. **Healing Process:** Call `/agent quality_enforcer` to fix identified problems.
5. **Verification:** Run `python run_tests.py --run-all` - 100% success rate required.
6. **Learn Patterns:** Store successful healing patterns for future application.

### Start Context
- `/read constitution.md`
- `/read core/self_healing.py`
- `/read core/telemetry.py`
- `/read core/patterns.py`

### Activated Feature Flags
```bash
export ENABLE_UNIFIED_CORE=true
export PERSIST_PATTERNS=true
```