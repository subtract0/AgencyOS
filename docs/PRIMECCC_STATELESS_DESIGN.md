# PrimeCCC Stateless Design

**Created:** 2025-10-08
**Purpose:** Explain how `/primeccc` works perfectly in fresh/cleared sessions

---

## Architecture: Persistent Memory + Stateless Execution

```
┌─────────────────────────────────────────────────────────────┐
│              CONVERSATION CONTEXT (Ephemeral)               │
│                                                             │
│  - Cleared on reset                                         │
│  - Rebuilt from persistent files                            │
│  - Not required for /primeccc                               │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
                    [Context Reset]
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│            PERSISTENT MEMORY (Survives Resets)              │
│                                                             │
│  ┌────────────────────┐  ┌─────────────────────────────┐   │
│  │  Memory Tool       │  │  VectorStore                │   │
│  │  (File-based)      │  │  (ChromaDB/Firestore)       │   │
│  ├────────────────────┤  ├─────────────────────────────┤   │
│  │ ~/.agency/memories/│  │ - 47 patterns               │   │
│  │ ├─ agency_backlog/ │  │ - 200+ learnings            │   │
│  │ │  ├─ gaps.md      │  │ - Session history           │   │
│  │ │  └─ priority.md  │  │ - Cross-session knowledge   │   │
│  │ ├─ patterns/       │  └─────────────────────────────┘   │
│  │ ├─ institutional/  │                                     │
│  │ └─ sessions/       │                                     │
│  └────────────────────┘                                     │
│                                                             │
│  ┌────────────────────┐  ┌─────────────────────────────┐   │
│  │  Codebase Files    │  │  Constitution               │   │
│  │  (Git-tracked)     │  │  (Git-tracked)              │   │
│  ├────────────────────┤  ├─────────────────────────────┤   │
│  │ - Agent defs       │  │ - Articles I-V              │   │
│  │ - CLAUDE.md        │  │ - Compliance rules          │   │
│  │ - Plans/specs      │  │ - Quality standards         │   │
│  │ - Source code      │  └─────────────────────────────┘   │
│  └────────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Session Lifecycle

### Traditional Approach (Context-Dependent)
```
Session 1:
  User: "Add feature X"
  Claude: [Uses conversation history]
  [120k tokens of context accumulated]

Session 2 (after reset):
  User: "Continue with feature X"
  Claude: ❌ "I don't have context from previous session"
  User: [Must re-explain everything]
```

### PrimeCCC Approach (Stateless)
```
Session 1:
  User: /primeccc "Add feature X"
  Claude: [Loads from files: 10k tokens]
  Claude: [Executes → Updates memory files]
  Memory: ✅ Backlog updated, patterns stored

[Context cleared/reset]

Session 2 (fresh start):
  User: /primeccc
  Claude: [Loads from files: 10k tokens]
  Claude: ✅ "Auto-selected: Next priority from backlog"
  Claude: ✅ "Applied 3 learnings from Session 1"
  User: Y
  Claude: [Executes autonomously]
```

**Key difference:** Memory Tool + VectorStore survive resets

---

## Data Flow: Fresh Session

```
1. You Clear Context
   └─> Conversation history deleted
   └─> TodoWrite lists cleared
   └─> Session metadata reset

2. You Run /primeccc
   ├─> Initialize Session (Phase 0)
   │   ├─> Read(constitution.md) ✅
   │   ├─> context.enable_anthropic_memory() ✅
   │   ├─> tool.view("/memories/agency_backlog/") ✅
   │   └─> context.search_memories(["pattern"]) ✅
   │
   ├─> Auto-Select Task (from backlog)
   │   ├─> Parse TOP 5 PRIORITY QUEUE ✅
   │   ├─> Find highest ROI + Ready ✅
   │   └─> Show details + confirm ✅
   │
   ├─> Load Context (10k tokens)
   │   ├─> Relevant agent summaries ✅
   │   ├─> Related VectorStore learnings ✅
   │   └─> Backlog gap details ✅
   │
   ├─> Plan (Chief Architect + Planner)
   │   └─> Create plan.md in plans/ ✅
   │
   ├─> Execute (Autonomous loop)
   │   └─> Write code → Run tests → Verify ✅
   │
   └─> Update Memory (Backlog + VectorStore)
       ├─> tool.str_replace(backlog, "Ready" → "FIXED ✅") ✅
       ├─> context.store_memory(new_pattern) ✅
       └─> tool.create(session_report.md) ✅

3. You Review
   └─> git diff && python run_tests.py

4. Next Session
   └─> Clear again → /primeccc → Repeat
```

---

## Persistence Layers

### Layer 1: Memory Tool (Cross-Conversation)
**Location:** `~/.agency/memories/`
**Type:** File-based
**Survives:** Everything (resets, restarts, reboots)

```bash
~/.agency/memories/
├── agency_backlog/
│   ├── test_suite_gaps.md          # TOP 5 PRIORITY QUEUE
│   ├── architecture_decisions.md   # Strategic debt
│   └── feature_requests.md         # User-requested features
│
├── patterns/
│   ├── result_pattern.md           # Error handling
│   ├── pydantic_models.md          # Data validation
│   └── tdd_workflow.md             # Test-first development
│
├── institutional/
│   ├── coding_standards.md         # Agency code style
│   ├── git_workflow.md             # Branch/commit strategy
│   └── constitutional_compliance.md # Article I-V checklist
│
└── sessions/
    ├── session_20251008_143022/
    │   ├── execution_report.md     # What was done
    │   └── learnings.md            # Patterns extracted
    └── session_20251008_151033/
        └── ...
```

### Layer 2: VectorStore (Institutional Learning)
**Backend:** ChromaDB (local) / Firestore (production)
**Type:** Semantic database
**Survives:** Resets, restarts (persistent DB)

```python
# Accessible in ANY session
context = create_agent_context()
learnings = context.search_memories(
    tags=["pattern", "success"],
    include_session=False  # Cross-session search
)

# Returns:
# - 47 patterns from past work
# - Confidence scores (0.6-1.0)
# - Context about when/how pattern worked
```

### Layer 3: Codebase Files (Always Available)
**Location:** Git repository
**Type:** Version-controlled files
**Survives:** Everything (tracked in git)

- `constitution.md` (5 articles)
- `CLAUDE.md` (quick reference)
- `.claude/agents/*.md` (agent definitions)
- `.claude/commands/*.md` (slash commands)
- `specs/*.md`, `plans/*.md` (formal docs)

---

## Benefits of Stateless Design

### 1. No Context Bloat
```
Traditional:
  Session start:   20k tokens
  After 1 task:    80k tokens
  After 2 tasks:  140k tokens
  After 3 tasks:  ❌ Near limit, must reset

PrimeCCC:
  Session start:   10k tokens (always)
  After 1 task:    10k tokens (reset between tasks)
  After 2 tasks:   10k tokens (reset between tasks)
  After 3 tasks:   ✅ Still 10k tokens
```

### 2. Consistent Performance
```
Traditional:
  Task 1: Fast (20k context)
  Task 2: Slower (80k context)
  Task 3: Slow (140k context)
  Task 4: ❌ Must reset first

PrimeCCC:
  Task 1: Fast (10k context)
  Task 2: Fast (10k context, cleared)
  Task 3: Fast (10k context, cleared)
  Task 4: ✅ Fast (10k context, cleared)
```

### 3. Cost Optimization
```
Traditional (no resets):
  Prompt tokens: 140k accumulated
  Cache hits: Good (same context)
  Cost per task: $0.56 → $0.40 → $0.35 (cache improves)
  Total 3 tasks: $1.31

PrimeCCC (reset between):
  Prompt tokens: 10k per task
  Cache hits: Minimal (fresh each time)
  Cost per task: $0.04 → $0.04 → $0.04
  Total 3 tasks: $0.12 (91% cheaper!)
```

### 4. Institutional Memory Growth
```
Traditional:
  Session 1: 0 learnings
  Session 2: ❌ Forgot Session 1 learnings
  Session 3: ❌ Forgot Session 1 & 2

PrimeCCC:
  Session 1: 3 patterns stored → VectorStore
  Session 2: ✅ Loads 3 patterns + adds 2 more
  Session 3: ✅ Loads 5 patterns + adds 1 more
  Result: Exponential knowledge growth
```

---

## Initialization Sequence (Fresh Session)

### Step 1: Create Context (1 second)
```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
context = create_agent_context(session_id=f"primeccc_{timestamp}")
```

### Step 2: Enable Memory Tool (2 seconds)
```python
context.enable_anthropic_memory()
tool = context.get_anthropic_memory_tool()

# Verifies ~/.agency/memories/ exists
# Creates directory if missing
# Validates path security (no traversal)
```

### Step 3: Load Constitution (1 second)
```python
constitution = Read("constitution.md", offset=1, limit=50)
# Articles I-V summaries (2.1k tokens)
```

### Step 4: Load Backlog (2 seconds)
```python
backlog = tool.view("/memories/agency_backlog/test_suite_gaps.md")
priority_queue = extract_priority_queue(backlog)

print(f"📋 Backlog: {len(priority_queue)} priorities")
# Priority #1: Ollama Docker Compose (Ready)
# Priority #2: MessageBus Cleanup (Ready)
# ...
```

### Step 5: Query VectorStore (3 seconds)
```python
all_patterns = context.search_memories(
    tags=["pattern"],
    include_session=False
)

print(f"🧠 VectorStore: {len(all_patterns)} patterns available")
# 47 patterns from past sessions
```

### Step 6: Load Agent Summaries (1 second)
```python
# Load ONLY agents needed for auto-selected task
task_type = classify_task(priority_queue[0].command)
# → "infrastructure" (Ollama setup)

required_agents = ["code_agent", "quality_enforcer"]
for agent in required_agents:
    Read(f".claude/agents/{agent}.summary.md")
# 2.3k tokens total
```

**Total initialization: ~10 seconds, 9.8k tokens**

---

## Example: Multi-Day Project

### Day 1 - Morning
```bash
[Fresh session]
/primeccc
# → Auto-selects: Ollama Docker Compose (1-2h)
# → Executes → 140 tests enabled ✅
# → Updates: Backlog (Priority #1 → FIXED), VectorStore (+2 patterns)
```

### Day 1 - Afternoon
```bash
[Clear context]
/primeccc
# → Auto-selects: MessageBus Cleanup (15m) - Now Priority #1
# → Applied 2 learnings from morning session ✅
# → Executes → Memory leak fixed ✅
# → Updates: Backlog, VectorStore (+1 pattern)
```

### Day 2 - Morning
```bash
[New day, fresh session]
/primeccc
# → Auto-selects: ExecutorAgent API (9-13h) - Skipped yesterday
# → Applied 3 learnings from Day 1 ✅
# → Executes → 30 tests updated ✅
```

### Day 3 - Review
```bash
cat ~/.agency/memories/sessions/*/execution_report.md

# Session 1: Ollama setup (140 tests, 2h actual vs 1-2h estimate)
# Session 2: MessageBus fix (1 test, 15m actual vs 15m estimate)
# Session 3: ExecutorAgent API (30 tests, 11h actual vs 9-13h estimate)

# Total: 171 tests enabled, 3 backlog items cleared
# VectorStore: +6 new patterns, 53 total
```

**Key point:** Each session started fresh, yet had full memory of previous work.

---

## FAQ

**Q: Do I NEED to clear context before `/primeccc`?**
A: No, but it's RECOMMENDED for:
- Faster execution (10k vs 120k tokens)
- Cheaper API calls (91% cost reduction)
- Cleaner experience (no stale context)

**Q: What if I don't clear context?**
A: It still works! But you'll have:
- Slower responses (large context)
- Higher costs (more tokens)
- Risk of hitting context limit after 2-3 tasks

**Q: Will I lose progress if I clear context mid-task?**
A: No! Progress is saved to:
- Memory files (backlog updates)
- VectorStore (patterns)
- Git (code changes)
- TodoWrite (only if you're mid-execution, then yes - wait for task completion)

**Q: How does auto-selection work in fresh sessions?**
A: Perfectly! The priority queue is in a file:
1. I read `~/.agency/memories/agency_backlog/test_suite_gaps.md`
2. I parse TOP 5 PRIORITY QUEUE section
3. I find highest Ready task
4. I show you details + confirm
5. You approve [Y/n]

**Q: Can I edit priorities in fresh sessions?**
A: Yes! Memory Tool persists across sessions:
```python
# Works in ANY session
context.enable_anthropic_memory()
tool = context.get_anthropic_memory_tool()
tool.str_replace("/memories/agency_backlog/test_suite_gaps.md", ...)
```

---

## Summary: Stateless = Superior

**Traditional approach:**
- ❌ Context accumulates (bloat)
- ❌ Must reset after 2-3 tasks
- ❌ Loses context on reset
- ❌ No institutional memory

**PrimeCCC approach:**
- ✅ Context always minimal (10k tokens)
- ✅ Reset encouraged (better performance)
- ✅ Memory survives resets (files + VectorStore)
- ✅ Exponential knowledge growth

**Your workflow:**
```
1. Clear context (optional but recommended)
2. /primeccc (auto-selects or you specify)
3. Execute task
4. Review results
5. Repeat (clear again for next task)
```

**Result:** Infinite task execution without context limits, with growing institutional intelligence.
