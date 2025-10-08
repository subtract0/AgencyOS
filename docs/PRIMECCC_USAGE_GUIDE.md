# PrimeCCC Usage Guide: Strategic Control + Tactical Autonomy

**Created:** 2025-10-08
**Purpose:** How to use Claude autonomously while staying firmly in the driver's seat

---

## TL;DR

```bash
# RECOMMENDED: Start fresh (clear context, optimal performance)
# [Click "Clear context" in UI or wait for auto-reset]

# Option 1: Zero arguments (auto-select from backlog)
/primeccc
# → I initialize from memory files (10k tokens)
# → I read TOP 5 PRIORITY QUEUE
# → I show you highest-value task
# → You confirm [Y/n]
# → I execute autonomously

# Option 2: Explicit intent (WHAT + WHY)
/primeccc "Add JWT authentication to API endpoints"

# Me: Autonomous execution (HOW + WHEN)
# → Load context (10k tokens, all from disk/memory)
# → Query memory/learnings (VectorStore + backlog)
# → Create plan → Ask approval
# → Execute with agents → Tests → Quality → Memory update
# → Deliver production code

# You: Review and approve
git diff && python run_tests.py --run-all
```

---

## 🆕 Fresh Session Mode (RECOMMENDED)

**Why clear context first:**
- ✅ **Faster:** 10k tokens loaded (not 120k from conversation history)
- ✅ **Cleaner:** No stale context from previous tasks
- ✅ **Cheaper:** Minimal prompt cache, faster API calls
- ✅ **Stateless:** Everything loaded from persistent files

**How `/primeccc` works in fresh sessions:**

```
[You clear context or start new session]

You: /primeccc

Me: [Initializing fresh session...]
    ✅ Loading constitution from constitution.md
    ✅ Connecting to Memory Tool at ~/.agency/memories/
    ✅ Reading backlog: 191 items, 5 prioritized
    ✅ Querying VectorStore: 47 patterns available
    ✅ Session ready! (9.8k tokens loaded)

    🎯 Auto-selected from backlog:
       Priority #1: Ollama Docker Compose Setup
       Value: High | Effort: 1-2h | ROI: 🔥 Highest
       ...

    Execute this task? [Y/n]: _
```

**What survives context reset:**
- ✅ Backlog priorities (file: `~/.agency/memories/agency_backlog/*.md`)
- ✅ VectorStore learnings (persistent backend: ChromaDB/Firestore)
- ✅ Memory patterns (file: `~/.agency/memories/patterns/*.md`)
- ✅ Session history (file: `~/.agency/memories/sessions/*/`)
- ✅ Constitution & agent definitions (git-tracked files)

**What doesn't matter after reset:**
- ❌ Conversation history (re-loaded from files as needed)
- ❌ Previous TodoWrite lists (task-specific, not persistent)
- ❌ Temporary session metadata (recreated fresh)

**Best practice workflow:**
```bash
# 1. Clear context (click UI button or wait for auto-reset)
# 2. Run /primeccc
# 3. Execute task
# 4. Review results
# 5. Repeat (clear again for next task)
```

---

## Your Role: Strategic Driver

### You Provide
1. **Strategic Intent** - WHAT needs to be done
   - "Add JWT authentication"
   - "Fix memory leak in MessageBus"
   - "Optimize local model memory usage"

2. **Constraints** - Strategic boundaries
   - "Must work with existing auth system"
   - "Performance critical, <100ms latency"
   - "Keep backward compatibility"

3. **Success Criteria** - HOW you measure done
   - "100% test coverage"
   - "Zero breaking changes"
   - "Documented in ADR"

4. **GO/NOGO Decisions** - Strategic checkpoints
   - Review plan before execution
   - Interrupt if direction wrong
   - Approve final PR

### You DON'T Provide
- ❌ File paths to edit
- ❌ Test cases to write
- ❌ Implementation details
- ❌ Agent orchestration sequence
- ❌ Quality checks to run

---

## My Role: Tactical Executor

### I Handle
1. **Context Loading** (10k tokens, optimized)
   - Constitution summaries
   - Memory backlog (related gaps)
   - VectorStore learnings
   - Relevant agent definitions

2. **Strategic Planning**
   - Query past similar work
   - Spawn Chief Architect (if architectural)
   - Spawn Planner (always)
   - Present plan for your approval

3. **Autonomous Execution Loop**
   ```
   while not done:
       scout_files()
       generate_tests_first()  # TDD
       implement_code()
       run_tests()
       quality_check()
       update_memory()
   ```

4. **Delivery**
   - Tests passing (100%)
   - Memory updated (backlog + learnings)
   - Report generated
   - Ready for your review

### I DON'T Do
- ❌ Change strategic direction without asking
- ❌ Skip your approval on plans
- ❌ Merge to main without your review
- ❌ Make architectural decisions without ADR

---

## Usage Patterns

### Pattern 0: Zero Arguments (Auto-Select from Backlog) 🆕

```bash
# You
/primeccc

# Me
# [2s] Reading TOP 5 PRIORITY QUEUE from backlog...
#
# 🎯 Auto-selected from backlog:
#    Priority #1: Ollama Docker Compose Setup
#    Value: High | Effort: 1-2h | ROI: 🔥 Highest
#    Unblocks: 140 tests (73% of all skipped)
#    Next Step: Create docker-compose.yml with Ollama service
#
# Execute this task? [Y/n]:

# You: Y

# Me
# [10s] Context loaded, memory checked
# [1m] Plan created: 4 tasks, simple complexity
# 🚦 Proceed? [Y/n]:

# You: Y

# Me
# [60m] ✅ All 4 tasks done
# ✅ docker-compose.yml created with Ollama + qwen3-coder
# ✅ Documentation updated
# ✅ 140/140 tests now passing!
# 🚀 Ready for review
```

**Time: ~60 minutes end-to-end**
**Your input: 2 confirmations (task selection + plan approval)**

**When to use:**
- ✅ You want to make progress but unsure what to prioritize
- ✅ You trust the backlog prioritization
- ✅ You want quick wins from pre-analyzed tasks

**How it works:**
1. I read `~/.agency/memories/agency_backlog/test_suite_gaps.md`
2. I find highest ROI task with Status = "Ready"
3. I show you task details + next step
4. You confirm [Y/n] or decline to see next priority
5. I execute autonomously

---

### Pattern 1: Simple Feature (2-5 files)

```bash
# You
/primeccc "Add rate limiting to API endpoints"

# Me
# [10s] Context loaded, memory checked
# [30s] Plan created: 3 tasks, moderate complexity
# 🚦 Proceed? [Y/n]:

# You: Y

# Me
# [5m] ✅ All 3 tasks done, 12/12 tests passing
# 🚀 Ready for review

# You
git diff  # Review changes
python run_tests.py --run-all  # Verify
git commit -m "feat: Add API rate limiting"
```

**Time: ~6 minutes end-to-end**

---

### Pattern 2: Complex Architecture (5+ files, needs ADR)

```bash
# You
/primeccc "Migrate authentication to OAuth2" --plan-only

# Me
# [10s] Context loaded
# [2m] 🏛️ Chief Architect spawned
# [2m] ✅ ADR created: docs/adr/ADR-024-oauth2-migration.md
# [2m] ✅ Plan created: 15 tasks, 8 files, 20+ tests
#
# Summary:
# - Replace JWT with OAuth2
# - Add refresh token rotation
# - Migrate existing users
# - Update all API endpoints
#
# ⏸️ Stopped at planning (--plan-only flag)

# You
cat docs/adr/ADR-024-oauth2-migration.md  # Review ADR
cat plans/oauth2_migration_plan.md        # Review plan
# Looks good!

# You
/primeccc "Migrate authentication to OAuth2" --execute-plan plans/oauth2_migration_plan.md

# Me
# [30m] ✅ All 15 tasks done, 87/87 tests passing
# 🚀 Ready for review

# You
python run_tests.py --run-all  # Full validation
git log --oneline -8           # Review commits
gh pr create                   # Create PR manually
```

**Time: ~35 minutes (plan + execution)**

---

### Pattern 3: Backlog Item Fix

```bash
# You
/primeccc "Fix Ollama integration tests (140 skipped)"

# Me
# [10s] Context loaded
# [5s] 📋 Found 1 backlog item: test_suite_gaps.md
# [5s] 🧠 Found 2 learnings: docker-compose, ollama setup
# [30s] ✅ Plan created: 4 tasks (learnings applied!)
# 🚦 Proceed? [Y/n]:

# You: Y

# Me
# [8m] ✅ Task 1: docker-compose.yml created
# [2m] ✅ Task 2: Test config updated
# [1m] ✅ Task 3: Skip markers removed
# [5m] ✅ Task 4: Tests running... 140/140 PASSING!
#
# 📝 Backlog updated:
#    Status: Ready to fix → Status: FIXED ✅ (2025-10-08)
#
# 🧠 Pattern stored: ollama_docker_setup
#
# 🚀 Ready for review

# You
python run_tests.py --run-all  # Verify
git commit -m "fix: Enable Ollama integration tests via Docker"
```

**Time: ~17 minutes end-to-end**

---

## When to Interrupt Me

### ✅ Let Me Run If
- Tests are passing, making progress
- Following approved plan
- No blocking errors
- Total time < 30 minutes

### ⛔ Interrupt If
- **Plan looks wrong** - STOP before Phase 3 (execution)
  - `Ctrl+C` then review plan manually
  - Re-run with `--plan-only` to revise

- **Stuck in retry loop** - >3 attempts on same task
  - I'll ask for guidance
  - You provide strategic direction (not code fix)

- **Cost concerns** - Burning >100k tokens
  - Check cost with `/cost-tracker status`
  - Consider `--plan-only` for review

- **Strategic direction changed** - New information
  - `Ctrl+C` immediately
  - Provide new intent: `/primeccc "NEW INTENT"`

---

## Agent Orchestration (Automatic)

I'll use these agents **automatically** based on task complexity:

| Task Type | Agents Used | Example |
|-----------|-------------|---------|
| **Simple fix** | Scout → Coder → Quality | "Fix typo in config" |
| **Feature** | Planner → Test Gen → Coder → Quality → Learning | "Add API endpoint" |
| **Architecture** | Chief Architect → Planner → Test Gen → Coder → Quality → Auditor → Learning | "New auth system" |
| **Refactor** | Auditor → Planner → Test Gen → Coder → Quality | "Optimize algorithm" |
| **PR** | Merger | "Create PR" (if `--auto-pr`) |

You **never** need to tell me which agent to use. I infer from:
- Task complexity (file count, architectural keywords)
- Memory backlog (related work)
- VectorStore learnings (past patterns)

---

## Memory Integration (Automatic)

### VectorStore (Article IV - MANDATORY)

**I query before acting:**
```python
# Before planning
learnings = search_memories(["jwt", "auth", "pattern"])
# Finds: "Use Result<T,E> for token errors" (confidence: 0.9)
# Applies to plan automatically
```

**I store after success:**
```python
# After completion
store_memory(
    "jwt_implementation_success_20251008",
    {"pattern": "OAuth2 with refresh tokens", "tests": 87},
    tags=["pattern", "auth", "success"]
)
```

### Memory Tool (Cross-Conversation Backlog)

**I check backlog:**
```bash
# Reads ~/.agency/memories/agency_backlog/test_suite_gaps.md
# Finds: "Ollama tests (140 skipped) - Status: Ready to fix"
# Links to this task automatically
```

**I update backlog:**
```bash
# After fixing
# Changes: "Status: Ready to fix" → "Status: FIXED ✅ (2025-10-08)"
# Adds: "PR: https://github.com/..."
```

**You always have full backlog visibility:**
```bash
cat ~/.agency/memories/agency_backlog/*.md
# See all gaps, priorities, status
```

---

## Flags & Options

### `--plan-only`
**Use when:** Complex tasks, want to review plan first

```bash
/primeccc "Big architectural change" --plan-only
# → Creates plan, ADR (if needed), then STOPS
# → Review manually
# → Continue with: /primeccc "..." --execute-plan <path>
```

### `--auto-pr`
**Use when:** You trust the automated process fully

```bash
/primeccc "Simple bugfix" --auto-pr
# → Executes plan
# → Creates PR automatically
# → Outputs PR URL for review
```

**⚠️ Recommended:** Review first, create PR manually until you're comfortable

---

## Cost Optimization

### Token Usage Comparison

| Command | Context Loaded | Typical Cost |
|---------|----------------|--------------|
| `/primecc` | 140k tokens | $0.56 (no cache) |
| `/primeccc` | 10k tokens | $0.04 (no cache) |
| **Savings** | **93% fewer tokens** | **93% cheaper** |

### With Prompt Caching

| Run | `/primecc` | `/primeccc` | Savings |
|-----|-----------|-------------|---------|
| First | $0.56 | $0.04 | 93% |
| Second | $0.14 | $0.01 | 93% |
| Third+ | $0.14 | $0.01 | 93% |

**Why so efficient?**
- Loads summaries, not full files
- Queries memory backlog (file-based, fast)
- Uses VectorStore learnings (cached)
- Skips irrelevant agent definitions

---

## Constitutional Compliance (Automatic)

I enforce **all 5 articles** automatically:

### Article I: Complete Context
- ✅ Retry on timeout (2x, 3x, 10x)
- ✅ Never proceed with partial data
- ✅ All files read before editing

### Article II: 100% Verification
- ✅ Tests generated FIRST (TDD)
- ✅ All tests must pass (no exceptions)
- ✅ Quality gates enforced

### Article III: Automated Enforcement
- ✅ Quality gates technically enforced
- ✅ No manual overrides
- ✅ Zero bypass authority

### Article IV: Continuous Learning
- ✅ VectorStore queried before planning
- ✅ Learnings applied automatically
- ✅ Patterns stored after success
- ✅ USE_ENHANCED_MEMORY=true (mandatory)

### Article V: Spec-Driven
- ✅ Complex tasks → spec.md → plan.md
- ✅ Simple tasks → plan.md → TodoWrite
- ✅ All implementation traces to plan

**You don't need to check compliance. I enforce it.**

---

## Troubleshooting

### "Plan looks wrong"
```bash
# Stop before execution
/primeccc "task" --plan-only

# Review plan
cat plans/task_*_plan.md

# If wrong, provide more context
/primeccc "task WITH CONSTRAINT: must use existing auth system"
```

### "Taking too long"
```bash
# Check progress (I update TodoWrite in real-time)
# Watch for "Task X/Y: [description]" output

# If stuck >5 min on same task:
# I'll ask for guidance (built-in timeout detection)
```

### "Tests failing"
```bash
# I auto-fix up to 3 attempts
# If still failing, I'll ask:
# "🚫 Task blocked. [R]etry, [S]kip, [A]bort?"

# You decide:
# - R: I try different approach
# - S: Skip task, continue with others
# - A: Stop entire workflow
```

### "Cost concerns"
```bash
# Check cost tracker
/cost-tracker status

# If >$1.00 spent:
# Use --plan-only for review
# Verify plan before expensive execution
```

---

## Best Practices

### ✅ DO

1. **Start with strategic intent**
   ```bash
   /primeccc "Add feature X"  # Good
   ```

2. **Add constraints if needed**
   ```bash
   /primeccc "Add feature X, must be <100ms latency"  # Better
   ```

3. **Use --plan-only for complex tasks**
   ```bash
   /primeccc "Big refactor" --plan-only  # Safe
   ```

4. **Review before approving plan**
   - Read plan summary
   - Check estimated files/tests
   - Press Y only if looks right

5. **Let me run uninterrupted (if plan approved)**
   - Trust the autonomous loop
   - Check progress via TodoWrite updates
   - Interrupt only if clearly wrong

### ❌ DON'T

1. **Don't provide implementation details**
   ```bash
   /primeccc "Edit file X, add function Y at line Z"  # Too tactical
   ```

2. **Don't interrupt mid-execution (if plan was right)**
   - Let me finish task sequence
   - I'll ask if blocked

3. **Don't skip plan review**
   - Always read plan summary
   - Verify complexity assessment
   - Check estimated time

4. **Don't use --auto-pr until comfortable**
   - Review PRs manually at first
   - Switch to --auto-pr when you trust flow

---

## Examples by Task Type

### Bug Fix
```bash
/primeccc "Fix race condition in MessageBus.publish()"
# → Scout finds file
# → Generate regression test
# → Fix code
# → Verify no more race
# Time: ~5-10 min
```

### New Feature
```bash
/primeccc "Add JWT refresh token rotation"
# → Plan: 5 tasks
# → Tests first (TDD)
# → Implement
# → Integration tests
# Time: ~15-20 min
```

### Architectural Change
```bash
/primeccc "Migrate to PostgreSQL from SQLite" --plan-only
# → Chief Architect creates ADR
# → Planner creates 20-task plan
# → Review manually
# → Execute separately
# Time: Plan 5min, Execute 60+ min
```

### Backlog Item
```bash
/primeccc "Fix ExecutorAgent API tests (30 skipped)"
# → Reads backlog
# → Applies docker-compose pattern (learned)
# → Updates tests for new API
# → Marks backlog FIXED
# Time: ~10-15 min
```

### Refactoring
```bash
/primeccc "Optimize memory usage in qwen3-coder KV cache"
# → Auditor analyzes current usage
# → Plan: Switch to Q8_0 quantization
# → Benchmark before/after
# → Update docs
# Time: ~20-30 min
```

---

## Summary: Your Control Points

| Phase | Your Decision | When |
|-------|--------------|------|
| **Intent** | Provide strategic WHAT/WHY | Start |
| **Plan Approval** | Review plan, GO/NOGO | After Phase 2 |
| **Interrupt** | Stop if wrong direction | During Phase 3 (if needed) |
| **Final Review** | Approve code/tests | Before merge |
| **PR Creation** | Manual or --auto-pr | After review |

**You stay strategic. I handle tactical. Simple.**

---

## Next Steps

1. **Try it now:**
   ```bash
   /primeccc "Pick a simple task from backlog"
   ```

2. **Review this guide** when you need advanced patterns

3. **Check memory backlog anytime:**
   ```bash
   cat ~/.agency/memories/agency_backlog/*.md
   ```

4. **Monitor learnings:**
   ```python
   from shared.agent_context import create_agent_context
   context = create_agent_context()
   learnings = context.search_memories(["pattern"], include_session=False)
   print(f"Total patterns: {len(learnings)}")
   ```

---

**Ready to go autonomous? Run `/primeccc "Your strategic intent here"`** 🚀
