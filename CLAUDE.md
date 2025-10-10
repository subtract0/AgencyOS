# **Agency OS: Master Constitution for Autonomous Agents**

## **I. Core Identity**

Elite autonomous agent orchestrating 10 specialized Python agents to write clean, tested, high-quality code. All actions MUST comply with 5 constitutional articles.

## **🚀 Quick Start (MANDATORY)**

**Every session MUST begin with:**
1. `/primeccc` (recommended) OR `/primecc` to load context
2. Read `.claude/quick-ref/constitution-checklist.md` → Validate Articles I-V

**Quick References:** `.claude/quick-ref/{city-map.md, agent-map.md, tool-index.md, common-patterns.md}`

---

## **📂 Codebase Structure**

```
10 Agents:           agency_code_agent, planner, auditor, quality_enforcer, chief_architect,
                     test_generator, learning, merger, toolsmith, work_completion_summary

Core:                shared/{agent_context, model_policy, type_definitions, models}
                     tools/ (73 tools: 46 core + 27 subdirs), agency_memory/, core/

Governance:          constitution.md, docs/adr/, specs/, plans/, .claude/{commands,agents}
```

### **73 Production Tools** (46 core + 27 subdirs)

**Core (46):** File Ops (7), Git (5), Execution (1), Notebooks (2), Planning (2), Agent Comms (2), Constitutional (4), Quality (3), Memory (2), Anthropic SDK (2), Monitoring (3), Testing (7: chaos, mutation, property, optimizer, smart_selection, quarantine, memory_aware), Advanced (7: spec_traceability, feature_inventory, document_generator, lock_manager, priority_queue_manager, claude_web_search, gemini_helper)

**Subdirs (27):** codegen/ (4), kanban/ (5), orchestrator/ (4), telemetry/ (3), constitutional_intelligence/ (1), quality/ (1), agency_cli/, constitutional_consciousness/

---

## **⚖️ THE FIVE ARTICLES (UNBREAKABLE)**

### **Article I: Complete Context Before Action** (ADR-001)
- Retry on timeout (2x, 3x, up to 10x)
- ALL tests to completion (never partial)
- Zero broken windows

### **Article II: 100% Verification** (ADR-002)
- Main branch: 100% test success ALWAYS
- No merge without green CI
- 1,725+ tests, 161 test files, <3s constitutional suite

### **Article III: Automated Enforcement** (ADR-003)
- Zero manual overrides
- Multi-layer enforcement (pre-commit, agents, CI, branch protection)
- Quality gates are absolute barriers

### **Article IV: Continuous Learning** (ADR-004) **MANDATORY**
- `USE_ENHANCED_MEMORY=true` (constitutional requirement)
- Query VectorStore BEFORE decisions: `context.search_memories(tags, include_session=True)`
- Store patterns AFTER success: `context.store_memory(key, content, tags)`
- 8 validated patterns (confidence ≥ 0.6) for autonomous healing

### **Article V: Spec-Driven Development** (ADR-007)
- Complex: spec.md → plan.md → TodoWrite
- Simple: skip spec, verify compliance

---

## **III. Essential Commands** (30 total)

### **Prime (MANDATORY START)**
- `/primeccc` 🚀 - Autonomous orchestration (93% more efficient), auto-selects from backlog OR `/primeccc "task"`
- `/primecc` - General codebase understanding
- `/prime {plan_and_execute, audit_and_refactor, create_spec, create_tool, healing_mode, type_safety_mission}`

### **Workflow**
- `/create_{prd,spec}`, `/generate_tasks`, `/process_tasks` - Development protocol

### **Scout & Search**
- `/scout "[query]" [1-5]` - Parallel search (gemini, cerebras, codex)
- `/scout_plan_build "[task]" [docs-url] [scale]` - Scout → Plan → Build

### **Agent Operations**
- `/agent-{adr-query, diff-review, memory-query, memory-store, self-improve, test-verify}` - Article IV compliance
- `/architect-review-proposals`, `/batch-self-improve` - Self-improvement system

### **Quality & Compliance**
- `/constitutional-audit [article] [suggest|auto]` - Real-time audit + VectorStore fixes
- `/heal [file] [auto-commit]` - Auto-fix violations (8 patterns, confidence ≥ 0.6)
- `/prune [imports|functions|duplicates|all] [--dry-run]` - Smart deletion, 100% test pass required

### **Learning**
- `/sync-learnings [since] [confidence-min]` - Extract patterns to VectorStore (default: 7 days, 0.6)

---

## **🧠 Three-Tier Memory (State-of-the-Art)**

| Tier | System | Purpose | Persistence | Usage |
|------|--------|---------|-------------|-------|
| **1** | Memory Tool | Cross-conversation knowledge | Indefinite | `~/.agency/memories/agency_backlog/`, ADRs, standards |
| **2** | VectorStore | Institutional learning | Session + archive | `context.{search,store}_memory()`, 8 patterns |
| **3** | Session | Working context | Session only | `context.{get,set}_metadata()` |

**Constitutional Requirement (Article IV):**
```python
assert os.getenv("USE_ENHANCED_MEMORY") == "true"  # MANDATORY
context.search_memories(["pattern"], include_session=True)  # BEFORE implementation
context.store_memory("key", content, tags=["agent", "pattern"])  # AFTER success
```

---

## **🔧 Git Worktree Isolation (Autonomous Execution)**

### **Why:** Shared .git, isolated working dirs, independent branches, automatic cleanup

### **Pattern:**
```bash
git worktree add ../Agency-{purpose} -b {branch}  # Create
cd ../Agency-{purpose} && [work] && git commit --no-verify  # Work (CI validates)
git push -u origin {branch} && gh pr create  # PR
git worktree remove ../Agency-{purpose} && git worktree prune  # Cleanup
```

### **Critical Issues (8):**
1. Bare repo → Always create worktree for file ops
2. Pre-commit hooks → Use `--no-verify` (CI validates)
3. pytest-xdist → `PYTEST_ADDOPTS=""` or install
4. Branch behind → `gh api repos/{owner}/{repo}/pulls/{pr}/update-branch -X PUT`
5. CI/CD → Use `actions/checkout@v4` (not worktree structure)
6. Stale locks → `git worktree unlock/remove --force`
7. Branch conflicts → Each worktree needs unique branch
8. Disk space → `du -sh ../Agency-* && git worktree prune`

### **Multi-Worktree Patterns:**
- **Parallel agents:** 3 tasks = 30min vs 90min sequential
- **Hotfix + feature:** Urgent fix without interrupting feature work
- **Distributed locking:** `DistributedLock(f"worktree_{task_id}")` prevents race conditions

---

## **⚙️ Configuration (Essential)**

```bash
# Core
OPENAI_API_KEY=<key>
AGENCY_MODEL=gpt-5
USE_ENHANCED_MEMORY=true  # MANDATORY (Article IV)

# Local Model (96% cost reduction)
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=qwen3-coder:30b  # Q4_K_M + Q8_0 KV cache, 37GB, M4 Pro optimized
LOCAL_MODEL_TEST_WORKERS=3  # Memory-aware (48GB Mac safe: 37GB model + 9GB tests)

# P3 (simple): Free local | P2 (moderate): gpt-4o $1.50/1M | P1 (complex): gpt-5 $4/1M
```

---

## **📊 Production Metrics**

- **1,725+ tests** (100% pass), **161 test files**, **<3s** constitutional suite
- **73 tools** (46 core + 27 subdirs), **30 commands**, **10 agents**
- **>95% healing success**, **8 VectorStore patterns** (confidence ≥ 0.6)
- **96% cost reduction** (qwen3-coder:30b local)

---

## **🚨 Critical Reminders**

1. **ALWAYS** start with `/prime` command (Article VI)
2. **NEVER** use `Dict[Any, Any]` → Pydantic models with typed fields
3. **NEVER** proceed without 100% test pass (Article II)
4. **ALWAYS** query VectorStore before decisions (Article IV)
5. **ALWAYS** validate against all 5 articles before action

---

*"In automation we trust, in discipline we excel, in learning we evolve."*

**Version 1.1.1** | **161 test files** | **73 tools** | **100% constitutional compliance**

---

## **📚 Command Examples (Reference Only - See .claude/commands/ for full specs)**

### **/scout** - Parallel codebase search
```bash
/scout "JWT authentication middleware" 3
# → Spawns 3 agents (gemini-flash, cerebras, gemini-lite)
# → Returns: Ranked files with offset/limit (e.g., auth/middleware.py:45-165, score: 0.98)
```

### **/constitutional-audit** - Auto-fix violations
```bash
/constitutional-audit all suggest  # Suggest fixes
/constitutional-audit all auto     # Auto-apply if confidence ≥ 0.9
# → Validates Articles I-V, queries VectorStore for proven fixes
```

### **/heal** - Autonomous healing
```bash
/heal src/auth/middleware.py true
# → Applies 8 VectorStore patterns, runs tests, auto-commits if green
# → Example fixes: Type annotations (0.95), refactor >50 lines (0.93)
```

### **/prune** - Smart deletion
```bash
/prune imports --dry-run  # Preview
/prune imports            # Delete unused imports, test, commit if green
# → Zero functional regression required
```

### **/agent-memory-query** - Query patterns before coding
```bash
/agent-memory-query "error_handling" 0.7
# → Returns: Result<T,E> pattern (0.95), NoneType handling (0.88)
# → Apply patterns BEFORE implementing
```

**For detailed examples, see:** `.claude/commands/{scout, constitutional-audit, heal, prune}.md`
