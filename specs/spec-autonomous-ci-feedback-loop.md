# Spec: Autonomous CI Feedback Loop

## Goals
- **G1**: Agent autonomously monitors CI status without user intervention
- **G2**: Agent reads CI logs directly via GitHub API when failures occur
- **G3**: Agent automatically retriggers CI after pushing fixes
- **G4**: Agent provides summary only when all checks pass or intervention needed

## Personas
- **Developer**: Wants to delegate PR fixes to agent, get notified only when done or blocked
- **Agent (Me)**: Should monitor → diagnose → fix → verify autonomously

## Current Gaps (What Made You Intervene)
1. I waited for you to paste error logs instead of fetching them via `gh run view --log`
2. I asked "should I retrigger?" instead of automatically pushing empty commit
3. I didn't implement retry loop (monitor → fix → verify → repeat)

## Proposed Solution: Autonomous CI Monitor

### Pattern: Watch-Diagnose-Fix-Verify Loop
```python
while not all_checks_passing:
    # 1. WATCH: Poll CI status every 30s
    status = gh_pr_checks(pr_number)
    
    # 2. DIAGNOSE: Fetch logs for failures
    for check in status.failed_checks:
        logs = gh_run_view_log(check.run_id)
        errors = parse_errors(logs)
    
    # 3. FIX: Apply fixes based on error patterns
    fixes = generate_fixes(errors)
    apply_fixes(fixes)
    git_commit_and_push(fixes)
    
    # 4. VERIFY: Wait for new CI run
    wait_for_ci_start()
    
    # 5. REPEAT or EXIT
    if max_attempts_reached or user_intervention_needed:
        notify_user(summary)
        break
```

## Acceptance Criteria

### AC-1: Autonomous Monitoring
- [ ] Agent polls `gh pr checks <pr>` every 30 seconds after pushing
- [ ] Agent waits for all checks to reach terminal state (success/failure)
- [ ] No user interaction required during monitoring

### AC-2: Autonomous Log Fetching
- [ ] Agent automatically runs `gh run view <run_id> --log` for failed checks
- [ ] Agent extracts error messages via grep/parsing
- [ ] User never needs to copy/paste CI logs

### AC-3: Autonomous Retrigger
- [ ] After pushing fix, agent automatically waits for CI to start
- [ ] If CI doesn't start within 60s, agent creates empty commit to retrigger
- [ ] No "should I retrigger CI?" questions

### AC-4: Smart Notification
- [ ] Agent only notifies user when:
  - All checks pass (success summary)
  - Stuck/blocked (needs human decision)
  - Max retry attempts reached (5 fix cycles)
- [ ] Agent does NOT notify for each individual fix attempt

### AC-5: Error Pattern Recognition
- [ ] Recognizes common errors: missing deps, lint, format, type errors
- [ ] Applies known fixes automatically (ruff format, pip install, etc.)
- [ ] Learns new patterns via VectorStore

## Success Criteria
- **Before**: User intervened 2 times in PR #86 (paste logs, retrigger CI)
- **After**: User intervenes 0 times for common CI failures
- **Target**: 90% of CI failures resolved autonomously

## Implementation Plan

### Phase 1: Autonomous Monitoring Tool
```bash
tools/ci_monitor.py
- poll_until_complete(pr_number, max_wait=600)
- fetch_failure_logs(run_id) 
- parse_common_errors(logs)
```

### Phase 2: Auto-Fix Integration
```bash
tools/ci_auto_fix.py
- fix_missing_dependencies(error)
- fix_lint_errors(error)
- fix_format_errors(error)
- apply_fix_and_push(fixes)
```

### Phase 3: Retry Loop
```bash
tools/ci_feedback_loop.py
- autonomous_ci_fix_loop(pr_number, max_attempts=5)
- wait_for_ci_retrigger(pr_number, timeout=120)
- should_notify_user(status) -> bool
```

## Constitutional Alignment
- **Article I**: Complete context (fetch all logs automatically)
- **Article III**: Automated enforcement (no manual intervention)
- **Article IV**: Learn patterns (store successful fixes to VectorStore)

## Related Work
- PR #86: Manual intervention required 2 times
- GitHub CLI: `gh run view --log` provides full log access
- Existing: `gh pr checks` provides status polling
