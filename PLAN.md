# Agency OS: Master Plan & Current State

**Last Updated:** 2025-10-02  
**Current Branch:** `main` (green, 100% tests passing)  
**Commit:** 06581b8 - Constitutional Compliance 100/100  
**Constitutional Status:** Articles II-V: 100/100 | Article I: 90/100  

---

## 🎯 Quick Context (Read This First)

**What Agency Is:** Constitutional multi-agent system with 10 specialized Python agents enforcing quality, learning, and spec-driven development through 5 mandatory articles.

**Critical Principle (Est. 2025-10-02):**  
> **"Mocks ≠ Green"** - Article II Amendment  
> Mocked functions SHALL NOT merge to main. Only fully-implemented, tested functionality may merge.

---

## 📊 Current State (commit 06581b8)

### What's Production-Ready ✅
- 1,725+ tests passing (100% success rate, <3s for constitutional suite)
- Constitutional validator on all 11 agents (`@constitutional_compliance`)
- Security: bash.py + git.py with Pydantic validation (+83 tests)
- VectorStore: MANDATORY (Article IV, cannot be disabled)
- Spec traceability: tools/spec_traceability.py + pre-commit hook
- Self-healing: core/self_healing.py (all functions <50 lines)
- Article II Amendment: "No Mocks in Production" in constitution.md

### What's Partially Implemented ⚠️
- **ADR-018 Timeout Wrapper** - Core exists (shared/timeout_wrapper.py), only 2/35 tools using it
- Production Trinity Protocol - autonomous.py exists, needs integration
- ADR-016 Ambient Listener - Full implementation in trinity_protocol/
- ADR-017 Phase 3 - Extensive implementation in trinity_protocol/

---

## ⚖️ Constitutional Status

**Article I:** 90/100 ⚠️ - Timeout wrapper not implemented (only 2/36 tools have retry)  
**Article II:** 100/100 ✅ - 1,725+ tests, "No Mocks" amendment added  
**Article III:** 100/100 ✅ - Zero bypass, multi-layer enforcement  
**Article IV:** 100/100 ✅ - VectorStore mandatory, cannot disable  
**Article V:** 100/100 ✅ - Spec traceability validated  

---

## 🚀 Priority Roadmap

### **NEW: Elite Tier Upgrade (6 Specs Created)** 🎯 **HIGHEST LEVERAGE**
**Goal:** Advance 78.9/100 → 84.9/100 | **Timeline:** 16 weeks

**Created Specifications:**
- [ ] **spec-014**: Documentation Consolidation (+7 pts → Doc 78→85)
- [ ] **spec-015**: Workflow State Persistence (+12 pts → Workflow 72→84)
- [ ] **spec-016**: Expanded Autonomous Healing (+10 pts → Healing 79→89)
- [ ] **spec-017**: Pattern Library & Learning Dashboard (+12 pts → Learning 76→88)
- [ ] **spec-018**: Unified Command Interface (+15 pts → Commands 69→84)
- [ ] **spec-019**: Meta-Level Consolidation & Pruning (40% code, 60% tokens, 3x speed)

**Current Focus: spec-019 (Meta-Consolidation)**
- [x] Phase 1.1 Audit: Git tools analyzed (3 tools, 1,367 lines → unify to 1 tool, 400 lines)
- [ ] Phase 1.1: Design unified git API with deterministic + LLM layers
- [ ] Phase 1.1: Implement git_unified.py with 100% test coverage
- [ ] Phase 1.1: Migrate all agent references
- [ ] Phase 1.2: Agent instruction compression (3,000 lines → 1,000 lines, 60% tokens saved)
- [ ] Phase 2: Trinity production-ization (18,914 lines → 11,500 lines, 60% reduction)
- [ ] Phase 3: Tool determinism & caching (90% ops deterministic, 10x speed)
- [ ] Phase 4: Test reorganization (unit <30s, clear categorization)
- [ ] Phase 5: LLM prompt compression (8,000 → 1,500 tokens, 60% savings)

**See:** `plans/plan-019-meta-consolidation-pruning.md` for full details

---

### **Phase 2: ADR-018 Timeout Wrapper** (HIGH PRIORITY)
**Goal:** Article I: 90→100/100 | **ROI:** 2.5x | **Effort:** 4-6 hours

**Files:**
1. `shared/timeout_wrapper.py` - `@with_constitutional_timeout` decorator, Result<T,E> pattern, 1x/2x/3x/5x/10x multipliers
2. `tests/test_timeout_wrapper.py` - Comprehensive timeout/error handling tests
3. Migrate 2 pilots (bash.py, read.py) - Zero regression

**Success:** All 36 tools have retry, Article I: 100/100

### **Phase 3: Production Trinity** (MEDIUM PRIORITY)
**Effort:** 12-16 hours | **Note:** Will be addressed in spec-019 Phase 2

**Current Problem:**
Trinity v2.0 (`/tmp/trinity_v2_*.py`) is simulation only - print statements, hardcoded ROI, mock quality gates.

**What's Needed:**
1. **ARCHITECT:** Real codebase analysis, actual ADR creation
2. **EXECUTE:** Spawn real Agency agents via agency_swarm
3. **WITNESS:** Run real checks (tools/constitution_check.py)
4. **Location:** `trinity_protocol/` package (not /tmp)
5. **Storage:** Firestore (not `/tmp/*.jsonl`)

---

## 📍 Key Files

- **constitution.md** - 5 articles (MUST READ before action)
- **agency.py** - Main orchestration (line 132: use_enhanced_memory = True)
- **shared/constitutional_validator.py** - Decorator
- **docs/adr/ADR-018-constitutional-timeout-wrapper.md** - Next target

---

## 🚨 Critical Reminders

1. Read `constitution.md` before planning
2. NO `Dict[Any, Any]` - use Pydantic models
3. NEVER merge mocks/simulations (Article II Amendment)
4. ALWAYS write tests FIRST (TDD mandatory)
5. Functions <50 lines, Result<T,E> for errors

---

## 🎯 Next Action (After /clear /prime_cc)

**IMMEDIATE:** Implement ADR-018 Timeout Wrapper  
**Why:** Article I completion (90→100/100), highest ROI  
**Approach:** TDD-first, Result<T,E>, <50 lines per function  

---

*"In automation we trust, in discipline we excel, in learning we evolve."*
