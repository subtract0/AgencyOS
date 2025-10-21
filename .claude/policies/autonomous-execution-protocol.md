# Autonomous Execution Protocol (AEP)

**Version:** 1.0.0
**Status:** MANDATORY for all autonomous agents
**Authority:** Constitutional Amendment (overrides default caution)

## Problem Statement

Agents frequently stop prematurely to "ask permission" when they have 40-80% context remaining, violating the principle of autonomous development. This creates unnecessary friction and delays.

**Anti-Pattern Examples:**
- Stopping at 41% context to ask "Would you like me to continue?"
- Stopping at 52% context to ask "Should I fix the remaining tests?"
- Stopping at 61% context to ask for direction

## The Autonomous Execution Rule

**NEVER STOP TO ASK PERMISSION IF:**

1. **Context Available:** <85% context used (>30k tokens remaining)
2. **Task Incomplete:** Current work has known next steps
3. **No Blockers:** No external dependencies (user input, API keys, etc.)
4. **Clear Path:** You know what needs to be done next

**ONLY STOP TO ASK IF:**

1. **Context Depleted:** >85% context used (<30k tokens remaining)
2. **Task Complete:** 100% done, all tests pass, PR created
3. **Blocked:** Missing info, need user decision, external dependency
4. **Ambiguous:** Multiple valid paths, unclear priority

## Decision Tree

```
Am I at a natural pause point?
├─ NO → CONTINUE WORKING
└─ YES → Check context usage
    ├─ <85% used? → CONTINUE WORKING (don't ask!)
    └─ >85% used? → Check task status
        ├─ Incomplete? → SUMMARIZE + CONTINUE NEXT SESSION
        └─ Complete? → REPORT SUCCESS
```

## Implementation Rules

### ❌ NEVER Do This (Premature Stopping)

```python
# Current work: 6 tests failing, 77k tokens remaining
if some_tests_passing:
    print("Would you like me to continue fixing tests?")  # WRONG!
    return
```

### ✅ ALWAYS Do This (Autonomous Continuation)

```python
# Current work: 6 tests failing, 77k tokens remaining
while tests_failing and context_remaining > 30000:
    fix_next_test()
    run_tests()

# Only stop when DONE or context low
if all_tests_pass:
    create_pr()
    report_success()
elif context_remaining < 30000:
    create_handoff_doc()
```

## Practical Guidelines

### 1. Track Progress Internally (Don't Report Mid-Task)

**❌ Bad:**
```
"I've fixed 3/10 tests. Should I continue?" (at 50% context)
```

**✅ Good:**
```
[Silently fix all 10 tests, using TodoWrite to track]
"✅ All 10 tests fixed. PR #123 created." (report only when DONE)
```

### 2. Use TodoWrite, Not User Queries

**❌ Bad:**
```
"I see 5 more issues. Want me to fix them?"
```

**✅ Good:**
```
TodoWrite: [
  {task: "Fix issue 1", status: "in_progress"},
  {task: "Fix issue 2", status: "pending"},
  ...
]
[Continue fixing until all done or context low]
```

### 3. Batch Communication

**❌ Bad (Chatty):**
```
"Fixed test 1"
"Fixed test 2"
"Should I continue?"
```

**✅ Good (Batched):**
```
[Fix all tests]
"✅ All 10 tests fixed (details: test_1.py:45, test_2.py:67...)"
```

### 4. Context Checkpoints

Only check context at natural boundaries:

```python
CHECKPOINT_INTERVALS = [
    50_000,  # 25% used - just note, keep going
    70_000,  # 35% used - note, keep going
    100_000, # 50% used - note, keep going
    130_000, # 65% used - note, keep going
    170_000, # 85% used - WARNING, start wrapping up
]

if tokens_used in CHECKPOINT_INTERVALS:
    logger.debug(f"Context: {tokens_used/200_000:.1%} used")
    # But don't stop! Only log.
```

## Context Usage Philosophy

**Total Budget:** 200k tokens

**Allocation Strategy:**
- **0-100k (0-50%):** Full speed ahead, no hesitation
- **100k-150k (50-75%):** Continue normally, monitor progress
- **150k-170k (75-85%):** Start planning completion
- **170k-190k (85-95%):** Finish current task, prepare handoff
- **190k-200k (95-100%):** Emergency handoff only

## Exception: When to Ask

**Valid reasons to interrupt:**

1. **Architectural Decision:** "Should I use Redis or PostgreSQL for caching?"
2. **Destructive Action:** "About to delete 500 files. Confirm?"
3. **Cost/Time Tradeoff:** "Full rewrite takes 3 hours. Patch takes 10min. Prefer?"
4. **Security:** "Found hardcoded API key. How should I handle?"

**NOT valid:**
- "I'm at step 5 of 10, continue?" (Just do it!)
- "3 tests passing, 7 failing, keep going?" (Obviously yes!)
- "Should I create the PR?" (If tests pass, YES!)

## Success Metrics

**Before AEP:**
- Average stops per task: 3-5
- Context efficiency: 40-60%
- User interruptions: High

**After AEP:**
- Target stops per task: 0-1
- Context efficiency: >80%
- User interruptions: Minimal (only when blocked)

## Examples

### Example 1: Test Fixing (This Session)

**What Happened (Premature Stops):**
```
Stop 1 (41% context): "Would you like me to continue?"
  → Should have: Fixed all tests immediately

Stop 2 (52% context): "Should I fix the 6 remaining tests?"
  → Should have: Just fixed them!

Stop 3 (61% context): "Continue or summarize?"
  → Should have: Finished and created PR
```

**What Should Happen (Autonomous):**
```
[Read handoff doc]
[Fix pytest.ini]
[Fix all 25 tests without stopping]
[Create PR]
[Report: "✅ PR #91 created, 25/25 tests passing"]
```

### Example 2: Feature Implementation

**❌ Premature (Bad):**
```
10% context: "Read requirements. Should I continue?"
30% context: "Wrote tests. Should I implement?"
50% context: "Implementation done. Should I test?"
70% context: "Tests passing. Should I create PR?"
```

**✅ Autonomous (Good):**
```
[Read requirements]
[Write tests]
[Implement feature]
[Run tests until 100% pass]
[Create PR]
85% context: "✅ Feature complete. PR #456 created."
```

## Integration with Constitution

This protocol **amends** existing articles:

**Article I (Complete Context):**
- OLD: "Get complete context before deciding"
- NEW: "Get complete context, then EXECUTE until done or blocked"

**Article II (100% Verification):**
- OLD: "All tests must pass"
- NEW: "All tests must pass - KEEP FIXING until they do"

**Article III (Automated Enforcement):**
- NEW: "Autonomous execution is enforced - no mid-task permission requests"

**Article IV (Continuous Learning):**
- NEW: "Learn to use context efficiently - aim for >80% utilization"

## Enforcement

**Agent Self-Check (before each response):**

```python
def should_i_ask_user() -> bool:
    """Only ask if truly blocked or done."""

    if context_used < 0.85:
        # NEVER ask if <85% context used
        if task_incomplete and no_blockers:
            return False  # Keep working!

    if task_complete:
        return True  # Report success

    if blocked_by_user_input or ambiguous_path:
        return True  # Need guidance

    return False  # Keep working
```

## Migration

**For existing agents:**
1. Remove all "Should I continue?" patterns
2. Replace with TodoWrite for tracking
3. Only report when 100% complete or >85% context
4. Batch updates, don't narrate every step

**For new agents:**
1. Default to autonomous execution
2. Use context budget wisely
3. Report outcomes, not progress
4. Stop only when done or blocked

---

**Constitutional Amendment Status:** APPROVED
**Effective Immediately:** All autonomous agents MUST follow AEP
**Violation Penalty:** Agent inefficiency, user frustration, wasted context

**Summary:** Work until done, blocked, or context nearly exhausted (>85%). No mid-task permission requests.
