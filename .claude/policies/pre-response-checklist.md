# Pre-Response Checklist for Autonomous Agents

**Use this checklist BEFORE every response to avoid premature stopping**

## Quick Decision Tree

```
┌─ Am I about to ask "Should I continue?" ─┐
│                                            │
│  YES → STOP! Check this first:            │
│         • Context used: _____% (must be >85% to ask)
│         • Task status: _____ (must be 100% or blocked)
│         • Can I continue? _____ (if yes, DON'T ASK!)
│                                            │
│  NO  → Good! Proceed with work.            │
└────────────────────────────────────────────┘
```

## Checklist (Complete BEFORE responding)

### ☐ 1. Context Check
- [ ] Current usage: ______k / 200k (____%)
- [ ] Remaining: ______k tokens
- [ ] Status:
  - [ ] <85% used → **CONTINUE WORKING** (don't even think about stopping)
  - [ ] 85-95% used → **FINISH CURRENT TASK** then stop
  - [ ] >95% used → **EMERGENCY HANDOFF** immediately

### ☐ 2. Task Status Check
- [ ] Current task: ______________________
- [ ] Completion: _____%
- [ ] Next steps: ______________________
- [ ] Status:
  - [ ] **Incomplete** → Continue (don't ask!)
  - [ ] **Complete** → Report success
  - [ ] **Blocked** → Ask for help

### ☐ 3. Blocker Check
- [ ] Am I blocked by:
  - [ ] User input needed (decision, password, etc.)
  - [ ] External dependency (API down, file missing)
  - [ ] Ambiguous requirements (unclear priority)
  - [ ] Other: ______________________
- [ ] Blocked? **YES** → Ask for help | **NO** → Continue

### ☐ 4. Execution Path Check
- [ ] Do I know what to do next? **YES** / **NO**
- [ ] Can I do it with current context? **YES** / **NO**
- [ ] Is it safe to proceed? **YES** / **NO**

**If all YES → CONTINUE WITHOUT ASKING**
**If any NO → Assess if truly blocked**

## Anti-Pattern Detection

### 🚫 STOP if you're about to say:

- "Would you like me to continue?"
- "Should I fix the remaining issues?"
- "I can continue if you want"
- "Let me know if you want me to proceed"
- "Shall I move on to the next step?"

### ✅ INSTEAD say nothing and just:

- Fix the remaining issues
- Continue to the next step
- Complete the task
- Create the PR

### Exception: These ARE okay to ask:

- "Found 2 architectures: A (fast) vs B (scalable). Prefer?"
- "About to delete production database. Confirm?"
- "Ambiguous requirement: X or Y? Which?"

## Context Usage Examples

### Example 1: 41% Context Used (82k/200k)

**DON'T:**
```
"I've fixed 3 tests. Should I continue?"
[STOP AND WAIT]
```

**DO:**
```
[Fix all remaining tests]
[Run full test suite]
[Create PR]
"✅ All 25 tests passing. PR #91 created."
```

**Reasoning:** 118k tokens remaining = enough for ~50 more test fixes!

### Example 2: 87% Context Used (174k/200k)

**DON'T:**
```
[Continue complex refactor]
[Run out of context mid-task]
```

**DO:**
```
[Create handoff document]
[Summarize progress]
"✅ 8/10 tasks done. Handoff: .handoff_refactor.md"
```

**Reasoning:** <26k tokens = only enough for handoff, not continuation.

### Example 3: 60% Context Used (120k/200k)

**DON'T:**
```
"I see 5 more bugs. Want me to fix them?"
```

**DO:**
```
[Fix all 5 bugs]
[Run tests]
[Commit fixes]
"✅ Fixed 5 bugs (details: bug_list.md). Tests passing."
```

**Reasoning:** 80k tokens remaining = plenty of space!

## TodoWrite Integration

**Instead of asking, use TodoWrite to track:**

```python
# DON'T ASK - JUST TRACK
TodoWrite([
    {"task": "Fix test 1", "status": "completed"},
    {"task": "Fix test 2", "status": "completed"},
    {"task": "Fix test 3", "status": "in_progress"},
    {"task": "Fix test 4", "status": "pending"},
    {"task": "Fix test 5", "status": "pending"},
])

# User can see progress in real-time via /todos
# No need to interrupt with "Should I continue?"
```

## Communication Strategy

### Minimize Mid-Task Communication

**❌ Chatty (Bad):**
```
Response 1: "Reading handoff doc"
Response 2: "Found 3 issues"
Response 3: "Fixing issue 1"
Response 4: "Issue 1 fixed. Continue?"  ← PREMATURE STOP
```

**✅ Batched (Good):**
```
Response 1: [Read, fix all 3 issues, test]
           "✅ All 3 issues fixed. Tests passing."
```

### When to Communicate

**Communicate at:**
- ✅ Task START (if complex): "Starting X. Plan: A→B→C."
- ✅ Major MILESTONES: "✅ Phase 1/3 complete (tests passing)."
- ✅ Task COMPLETE: "✅ Done. PR #123 created."
- ✅ BLOCKED: "⚠️ Blocked: Need API key for X."

**DON'T communicate at:**
- ❌ Every small step
- ❌ Mid-task unless blocked
- ❌ When context still available

## Self-Audit Questions

**Before sending response, ask yourself:**

1. **Am I asking permission when I should just do it?**
   - If YES → Remove the question, do the work

2. **Do I have enough context to continue?**
   - If YES → Continue
   - If NO → Create handoff

3. **Is the task complete?**
   - If YES → Report and stop
   - If NO → Keep working

4. **Am I truly blocked?**
   - If YES → Ask for help
   - If NO → Keep working

5. **Would the user be frustrated by this interruption?**
   - If YES → Don't interrupt, keep working
   - If NO → Okay to communicate

## Enforcement

**Every agent MUST:**
- [ ] Check context usage before considering stopping
- [ ] Only stop if >85% context OR task complete OR blocked
- [ ] Never ask "Should I continue?" with <85% context
- [ ] Use TodoWrite for progress tracking (not user queries)
- [ ] Batch communication (report outcomes, not steps)

**Violation Examples (from this session):**
- ❌ Stop at 41% to ask about continuing
- ❌ Stop at 52% to ask about fixing tests
- ❌ Stop at 61% to ask for direction

**Correct Behavior:**
- ✅ Work until 100% done or >85% context
- ✅ Report: "Task complete" or "Handoff created"

## Summary

**The Rule:** Work → Complete → Report (or) Work → Context Low → Handoff

**Never:** Work → Pause → Ask → Wait → Work → Pause → Ask...

---

**Use this checklist EVERY TIME before responding to avoid premature stops!**
