# Phase 2A Quick Reference - Test Bloat Removal

## One-Line Summary
**Delete 731 experimental tests (24.7% of suite) to achieve Mars-ready test efficiency.**

## Quick Stats
```
Current:  2,965 tests, 153 files, ~296s runtime
After:    2,234 tests, 118 files, ~223s runtime
Impact:   -731 tests (-24.7%), 1.33x faster
```

## Files to Delete (35 total)

### Trinity Protocol (19 files)
```
tests/trinity_protocol/test_pattern_detector.py (59 tests)
tests/trinity_protocol/test_project_models.py (46 tests)
tests/trinity_protocol/test_executor_agent.py (38 tests)
tests/trinity_protocol/test_witness_agent.py (38 tests)
tests/trinity_protocol/test_architect_agent.py (35 tests)
tests/trinity_protocol/test_preference_learning.py (28 tests)
tests/trinity_protocol/test_conversation_context.py (24 tests)
tests/trinity_protocol/test_persistent_store.py (23 tests)
tests/trinity_protocol/test_pattern_detector_ambient.py (21 tests)
tests/trinity_protocol/test_parameter_tuning.py (14 tests)
tests/trinity_protocol/test_phase3_constitutional.py (13 tests)
tests/trinity_protocol/test_ambient_listener_service.py (10 tests)
tests/trinity_protocol/test_transcription_service.py (10 tests)
tests/trinity_protocol/test_message_bus.py (7 tests)
tests/trinity_protocol/test_human_review_queue.py (6 tests)
tests/trinity_protocol/test_response_handler.py (6 tests)
tests/trinity_protocol/test_message_persistence_restart.py (5 tests)
tests/trinity_protocol/test_phase3_integration.py (5 tests)
tests/trinity_protocol/test_production_integration.py (3 tests)
```

### DSPy Agents (6 files)
```
tests/dspy_agents/test_auditor_agent.py (70 tests)
tests/dspy_agents/test_planner_agent.py (49 tests)
tests/dspy_agents/test_code_agent.py (48 tests)
tests/dspy_agents/test_toolsmith_agent.py (41 tests)
tests/dspy_agents/test_dspy_learning_agent.py (23 tests)
tests/dspy_agents/test_ab_framework_integration.py (17 tests)
```

### Archived (7 files)
```
tests/archived/trinity_legacy/test_foundation_verifier.py (20 tests)
tests/archived/trinity_legacy/test_project_initializer.py (4 tests)
tests/archived/trinity_legacy/test_project_executor.py (0 tests)
tests/archived/trinity_legacy/test_trinity_e2e_integration.py (0 tests)
tests/archived/trinity_legacy/test_daily_checkin.py (0 tests)
tests/archived/trinity_legacy/test_budget_enforcer.py (0 tests)
tests/archived/trinity_legacy/test_spec_from_conversation.py (0 tests)
```

### Other Experimental (3 files)
```
tests/test_bash_tool_infrastructure.py (79 tests)
tests/test_learning_loop_integration.py (23 tests)
tests/test_git_error_paths.py (4 tests)
```

## Duplicate Groups to Consolidate Later (10 groups)

1. **toolsmith_agent**: comprehensive ← dspy (keep legacy, delete dspy)
2. **agency_code_agent**: base ← fixed (merge into one)
3. **chief_architect_agent**: 3 files → 1 (consolidate)
4. **planner_agent**: legacy ← dspy (keep legacy, delete dspy)
5. **retry_controller**: base ← additional (merge)
6. **auditor_agent**: legacy ← dspy (keep legacy, delete dspy)
7. **message_bus**: trinity ← shared (keep shared, delete trinity)
8. **pattern_detector**: trinity ← shared (keep shared, delete trinity)
9. **persistent_store**: trinity ← shared (keep shared, delete trinity)
10. **preference_learning**: trinity ← shared (keep shared, delete trinity)

## NECESSARY Scores Distribution

| Score | Count | Verdict | Action |
|-------|-------|---------|--------|
| 7-9   | 140   | KEEP    | Keep (excellent tests) |
| 4-6   | 13    | KEEP    | Keep (good tests) |
| 2-3   | 0     | REFACTOR| Improve |
| 0-1   | 0     | DELETE  | Remove |

## Execution Commands

### Run Analysis (already done)
```bash
python analyze_test_bloat.py
```

### Execute Deletion
```bash
bash scripts/phase_2a_delete_bloat.sh
```

### Verify Tests Pass
```bash
python run_tests.py --run-all
# Expect: 2,234 tests passing
```

### Restore if Needed
```bash
cp -r .test_bloat_backup_<timestamp>/* tests/
```

## Key Files

- **Main Report**: `docs/testing/PHASE_2A_BLOAT_ANALYSIS.md`
- **JSON Data**: `docs/testing/phase_2a_bloat_detailed.json`
- **Summary**: `docs/testing/PHASE_2A_EXECUTIVE_SUMMARY.md`
- **This File**: `docs/testing/PHASE_2A_QUICK_REFERENCE.md`
- **Script**: `scripts/phase_2a_delete_bloat.sh`

## Safety Checklist

- [x] Backup created automatically by script
- [x] Only experimental/archived code affected
- [x] No production code tested by these tests
- [x] Easy rollback via backup or git history
- [x] Remaining 2,234 tests cover production
- [x] Script requires user confirmation

## Timeline

1. Review: 5 min
2. Execute script: 1 min
3. Verify tests: 5 min
4. Commit: 2 min
**Total: ~15 minutes**

## Success Criteria

After execution:
- [ ] 2,234 tests exist (down from 2,965)
- [ ] 118 test files exist (down from 153)
- [ ] All tests pass (100% success rate)
- [ ] Runtime ~223s (down from ~296s)
- [ ] Backup created in `.test_bloat_backup_<timestamp>/`

---

**Ready to execute?** Run: `bash scripts/phase_2a_delete_bloat.sh`
