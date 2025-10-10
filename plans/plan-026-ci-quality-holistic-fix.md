# Implementation Plan: CI Quality Holistic Fix

**Plan ID**: `plan-026-ci-quality-holistic-fix`
**Spec Reference**: ADR-026 (Holistic CI Quality Cleanup Strategy)
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Implementation Start**: 2025-10-10
**Target Completion**: 2025-10-10 (70 minutes)

---

## Executive Summary

**Mission**: Restore CI/CD pipeline to 100% pass rate across both PR #81 (leap-4-quality-feedback-loop) and main branch using a holistic cleanup strategy.

**Strategy**: Fix PR lint errors → Merge PR → Holistic main branch cleanup (ADR-026)

**Critical Path**: Auto-fix PR lint errors (44 issues) → Merge → Auto-fix main branch (51 issues) → Constitutional verification

**Timeline**: 70 minutes total
- Phase 1: Auto-fix PR lint errors (10 minutes)
- Phase 2: Merge PR to main (5 minutes)
- Phase 3: Holistic main branch cleanup (30 minutes)
- Phase 4: Constitutional verification (10 minutes)
- Phase 5: Documentation and learning (15 minutes)

**Key Insight from ADR-026**: Zero file overlap between PR errors (8 files) and main errors (19 files) enables safe merge-first approach with 22% time savings vs incremental cleanup.

**Constitutional Compliance**:
- **Article I**: Complete context via triple audit (PR, main, overlap analysis)
- **Article II**: Target 100% test pass rate + 0 lint errors
- **Article III**: Automated enforcement maintained (no bypasses)
- **Article IV**: VectorStore learning of holistic cleanup pattern
- **Article V**: Spec-driven (ADR-026 documents decision)

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      CI Quality Fix Flow                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Phase 1:       │───▶│   Phase 2:       │───▶│   Phase 3:       │
│  Fix PR Lint     │    │   Merge PR       │    │  Holistic Main   │
│  (44 errors)     │    │   to Main        │    │  Cleanup (51)    │
└──────────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                        │
        ↓                       ↓                        ↓
  ruff check --fix        gh pr merge            ruff check --fix
  ruff format .          (squash merge)          ruff format .
  39 auto + 5 manual     Fast-forward           Run full test suite
        │                       │                        │
        ↓                       ↓                        ↓
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Verify: PR      │    │  Verify: Main    │    │  Phase 4:        │
│  CI green ✅     │    │  CI green ✅     │    │  Constitutional  │
└──────────────────┘    └──────────────────┘    │  Verification    │
                                                 └──────────────────┘
                                                         │
                                                         ↓
                                                 ┌──────────────────┐
                                                 │  Phase 5:        │
                                                 │  Learning +      │
                                                 │  Documentation   │
                                                 └──────────────────┘
```

### Key Components

#### Component 1: Ruff Linter/Formatter
- **Purpose**: Automated code quality enforcement (Python PEP 8 + constitutional rules)
- **Responsibilities**:
  - Detect style violations (imports, typing, formatting)
  - Auto-fix safe issues (--fix flag)
  - Format code (ruff format)
- **Dependencies**: pyproject.toml configuration
- **Interfaces**: CLI commands, exit codes

#### Component 2: Git/GitHub PR Workflow
- **Purpose**: Version control and CI/CD integration
- **Responsibilities**:
  - Branch management (leap-4 → main)
  - CI trigger and monitoring
  - PR merge with squash
- **Dependencies**: GitHub Actions workflows (.github/workflows/)
- **Interfaces**: gh CLI, git commands

#### Component 3: Test Suite Runner
- **Purpose**: Verification of functional correctness (Article II)
- **Responsibilities**:
  - Run 1,725 tests (100% pass required)
  - Memory-aware parallelism (3 workers with local model)
  - Timeout handling (Article I retry logic)
- **Dependencies**: pytest, run_tests.py, memory_aware_test_runner.py
- **Interfaces**: pytest CLI, exit codes

#### Component 4: Constitutional Audit Tool
- **Purpose**: Validate compliance with Articles I-V
- **Responsibilities**:
  - Check Article I (complete context)
  - Check Article II (100% test pass + quality)
  - Check Article III (automated enforcement)
  - Check Article IV (VectorStore learning)
  - Check Article V (spec-driven process)
- **Dependencies**: Constitutional audit command, VectorStore
- **Interfaces**: /constitutional-audit command

### Data Flow

```
Error Detection → Ruff Analysis → Auto-Fix Generation → Test Verification
     ↓                ↓                   ↓                    ↓
44 PR errors    Error types         39 auto-fixed      Full test suite
51 main errors  (UP035, F401,      5 manual fixes      (1,725 tests)
                 I001, etc.)                                   ↓
                                                        ┌──────────────┐
                                                        │ CI Green ✅  │
                                                        │ or Red ❌    │
                                                        └──────────────┘
                                                               ↓
                                                        ┌──────────────┐
                                                        │  Learning    │
                                                        │  Storage     │
                                                        │ (VectorStore)│
                                                        └──────────────┘
```

---

## Agent Assignments

### Primary Agent: QualityEnforcerAgent
- **Role**: Execute holistic cleanup with constitutional oversight
- **Tasks**:
  - Run ruff auto-fix on PR branch (Phase 1)
  - Verify CI green before merge (Phase 1)
  - Monitor merge process (Phase 2)
  - Run holistic main cleanup (Phase 3)
  - Run constitutional audit (Phase 4)
  - Store learnings in VectorStore (Phase 5)
- **Tools Required**:
  - Bash (ruff, git, gh, pytest)
  - Read (check audit reports)
  - Edit (manual fixes if needed)
  - ConstitutionalAudit
  - VectorStore (memory storage)
- **Deliverables**:
  - PR CI green ✅
  - Main CI green ✅
  - Constitutional compliance report (100%)
  - VectorStore learning entry

### Supporting Agent: AuditorAgent
- **Role**: Provide analysis and verification (already complete)
- **Tasks**:
  - ✅ COMPLETE: Triple audit (PR, main, overlap analysis)
  - ✅ COMPLETE: Zero file overlap discovery
  - ✅ COMPLETE: Quick fix guide generation
  - Verify final quality metrics (Phase 4)
- **Tools Required**:
  - Bash (ruff, mypy, git)
  - Grep (error pattern analysis)
  - Read (code analysis)
- **Deliverables**:
  - ✅ COMPLETE: logs/audits/audit_pr_leap4_20251010.json
  - ✅ COMPLETE: logs/audits/main_branch_audit_20251010.json
  - ✅ COMPLETE: logs/audits/QUICK_FIX_GUIDE.md
  - Final quality report (Phase 4)

### Supporting Agent: LearningAgent
- **Role**: Extract patterns and store in VectorStore (Phase 5)
- **Tasks**:
  - Extract holistic cleanup pattern
  - Store zero-overlap merge strategy
  - Document 22% time savings metric
  - Update institutional memory
- **Tools Required**:
  - VectorStore write
  - Read (audit reports, ADR-026)
- **Deliverables**:
  - VectorStore entry: "holistic_cleanup_pattern_20251010"
  - Pattern tags: ["architecture", "cleanup", "merge_strategy", "zero_overlap"]

### Agent Communication Flow
```
AuditorAgent (complete) → PlannerAgent (this plan) → QualityEnforcerAgent (execution)
                                                              ↓
                                                      LearningAgent (pattern storage)
                                                              ↓
                                                      ChiefArchitect (ADR-026 status update)
```

---

## Tool Requirements

### Core Tools

#### File Operations
- **Read**: Read audit reports (logs/audits/*.json, *.md, ADR-026)
- **Edit**: Manual fixes if auto-fix fails (B904 exception chaining, etc.)
- **Write**: None needed (all fixes via ruff or auto-generated)

#### Code Analysis
- **Grep**: Search for error patterns (e.g., `QualitySignals(` instantiations)
- **Glob**: Find affected files (e.g., `tests/test_*.py`)
- **Bash**: Primary execution tool
  - `ruff check --fix .` (auto-fix lint errors)
  - `ruff format .` (format code)
  - `git status`, `git commit`, `git push`
  - `gh pr merge`, `gh run watch`
  - `pytest`, `python run_tests.py --run-all`

#### Development Support
- **TodoWrite**: NOT NEEDED (simple sequential workflow, no branching)
- **Git Operations**: All via Bash (git, gh commands)

### Specialized Tools

#### Constitutional Tools
- **ConstitutionalAudit**: `/constitutional-audit all suggest`
  - Validates Articles I-V compliance
  - Generates compliance report
  - Suggests fixes for violations

#### Memory Tools
- **VectorStore** (via context.store_memory):
  - Store holistic cleanup pattern
  - Store zero-overlap merge strategy
  - Tag for future retrieval

### Tool Integration Patterns

```python
# Phase 1: Auto-fix PR lint errors
def phase1_fix_pr_lint():
    # 1. Auto-fix safe issues
    bash("ruff check --fix .")  # Fixes 39/44 errors

    # 2. Format all files
    bash("ruff format .")  # Formats 7 uncommitted files

    # 3. Verify clean
    result = bash("ruff check .")
    assert result.returncode == 0, "Ruff check must pass"

    # 4. Commit
    bash('git add -A')
    bash('git commit -m "fix: Auto-fix ruff lint errors in PR #81"')

    # 5. Push and verify CI
    bash('git push origin leap-4-quality-feedback-loop')
    bash('gh run watch')  # Monitor CI until green

# Phase 3: Holistic main cleanup
def phase3_holistic_main_cleanup():
    # 1. Checkout main (post-merge)
    bash('git checkout main && git pull')

    # 2. Auto-fix all errors
    bash('ruff check --fix .')  # Fixes 51 main errors

    # 3. Format all files
    bash('ruff format .')  # Formats 42 files

    # 4. Run full test suite (Article I: complete context)
    bash('python run_tests.py --run-all')  # 1,725 tests must pass

    # 5. Commit holistic cleanup
    bash('git add -A')
    bash('git commit -m "fix: Holistic ruff cleanup (ADR-026)"')

    # 6. Push and verify CI
    bash('git push origin main')
    bash('gh run watch')

# Phase 5: Store learnings
def phase5_store_learnings(context: AgentContext):
    context.store_memory(
        key="holistic_cleanup_pattern_20251010",
        content={
            "pattern": "holistic_cleanup",
            "trigger": "zero_file_overlap_between_branches",
            "decision": "merge_first_fix_together",
            "time_savings": "22% faster than incremental (70min vs 90min)",
            "errors_fixed": 95,  # 44 PR + 51 main
            "files_affected": 27,  # 8 PR + 19 main
            "test_success_rate": 1.0,
            "constitutional_compliance": ["I", "II", "III", "IV", "V"]
        },
        tags=["architecture", "cleanup", "merge_strategy", "zero_overlap"]
    )
```

---

## Contracts & Interfaces

### Internal APIs

#### Ruff CLI Interface
```bash
# Lint checking (read-only)
ruff check .
# Exit code: 0 (pass), 1 (errors found)

# Auto-fix (writes to files)
ruff check --fix .
# Exit code: 0 (all fixed), 1 (unfixable errors remain)

# Formatting (writes to files)
ruff format .
# Exit code: 0 (success)

# Format check (read-only)
ruff format --check .
# Exit code: 0 (pass), 1 (formatting needed)
```

#### Git/GitHub CLI Interface
```bash
# Git status check
git status
# Exit code: 0 (success)

# Commit
git commit -m "message"
# Exit code: 0 (success), 1 (nothing to commit or error)

# Push
git push origin <branch>
# Exit code: 0 (success), 1 (error)

# PR merge
gh pr merge <number> --squash --delete-branch
# Exit code: 0 (success), 1 (error)

# CI monitoring
gh run watch
# Streams CI logs, exit code: 0 (success), 1 (failure)
```

#### Test Runner Interface
```bash
# Full test suite (1,725 tests)
python run_tests.py --run-all
# Exit code: 0 (100% pass), 1 (failures)
# Memory-aware: auto-configures worker count based on local model state
```

### External Integrations

#### GitHub Actions CI
- **Protocol**: HTTP (triggered by git push)
- **Authentication**: GitHub token (gh CLI)
- **Endpoints**:
  - Workflow trigger: `git push`
  - Status check: `gh run watch`, `gh run list`
- **Data Format**: YAML workflow definition (.github/workflows/)

#### VectorStore (Firestore)
- **Protocol**: gRPC (Python SDK)
- **Authentication**: Service account (env var)
- **Endpoints**:
  - Write: `context.store_memory(key, content, tags)`
  - Search: `context.search_memories(tags, include_session=False)`
- **Data Format**: JSON documents

### Data Contracts

#### Ruff Error Format (JSON)
```json
{
  "code": "UP035",
  "message": "`typing.Dict` is deprecated, use `dict` instead",
  "location": {
    "file": "tests/test_leap4_e2e_quality_feedback.py",
    "line": 25,
    "column": 1
  },
  "fix": {
    "fixable": true,
    "applicability": "safe"
  }
}
```

#### VectorStore Learning Entry
```json
{
  "key": "holistic_cleanup_pattern_20251010",
  "content": {
    "pattern": "holistic_cleanup",
    "trigger": "zero_file_overlap_between_branches",
    "decision": "merge_first_fix_together",
    "time_savings": "22% faster than incremental (70min vs 90min)",
    "errors_fixed": 95,
    "files_affected": 27,
    "test_success_rate": 1.0,
    "constitutional_compliance": ["I", "II", "III", "IV", "V"]
  },
  "tags": ["architecture", "cleanup", "merge_strategy", "zero_overlap"],
  "timestamp": "2025-10-10T21:45:00Z",
  "confidence": 0.9
}
```

---

## Implementation Strategy

### Development Phases

#### Phase 1: Fix PR Lint Errors (10 minutes)
**Duration**: 10 minutes
**Agents**: QualityEnforcerAgent
**Deliverables**:
- [ ] 44 PR lint errors fixed (39 auto + 5 manual)
- [ ] 7 uncommitted files formatted
- [ ] PR CI green ✅
- [ ] Git commit pushed to leap-4-quality-feedback-loop

**Tasks**:
1. **TASK-001: Auto-fix safe lint errors** [QualityEnforcerAgent]
   - Command: `ruff check --fix .`
   - Expected: 39/44 errors auto-fixed
   - Error types: UP035 (deprecated typing), F401 (unused imports), I001 (import sorting), UP006, UP041, C416, F541
   - Acceptance: `ruff check .` shows 5 remaining errors (manual fix needed)
   - Estimate: 2 minutes

2. **TASK-002: Format all uncommitted files** [QualityEnforcerAgent]
   - Command: `ruff format .`
   - Expected: 7 files formatted
     - agency_memory/vector_index.py
     - agency_memory/vector_store.py
     - demo_batch_memory_reads.py
     - tests/test_leap4_e2e_quality_feedback.py
     - tools/async_memory_tool.py
     - tools/skill_dashboard.py
     - tools/validate_cost_savings.py
   - Acceptance: `ruff format --check .` returns 0
   - Estimate: 30 seconds

3. **TASK-003: Manual fixes (if needed)** [QualityEnforcerAgent]
   - Expected errors: B904 (exception chaining), B007 (unused loop vars)
   - Fix pattern B904: Add `from e` to exception re-raises
   - Fix pattern B007: Rename unused loop vars to `_`
   - Acceptance: `ruff check .` returns 0
   - Estimate: 3 minutes
   - **NOTE**: May not be needed if ruff --fix handles all errors

4. **TASK-004: Verify clean state** [QualityEnforcerAgent]
   - Command: `ruff check . && ruff format --check .`
   - Acceptance: Exit code 0 (no errors)
   - Estimate: 30 seconds

5. **TASK-005: Commit and push fixes** [QualityEnforcerAgent]
   - Stage: All modified files from TASK-001 to TASK-003
   - Commit message:
     ```
     fix: Auto-fix ruff lint errors in PR #81

     - Auto-fixed 39 lint errors (imports, typing, style)
     - Formatted 7 uncommitted files
     - Manual fixes for B904, B007 (if needed)

     Constitutional compliance:
     - Article II: Strict typing (UP035, UP006)
     - Article III: Automated enforcement (ruff --fix)

     Related: ADR-026 (Holistic CI Quality Cleanup)

     🤖 Generated with [Claude Code](https://claude.com/claude-code)

     Co-Authored-By: Claude <noreply@anthropic.com>
     ```
   - Commands:
     - `git add -A`
     - `git commit -m "$(cat <<'EOF' ... EOF)"`
     - `git push origin leap-4-quality-feedback-loop`
   - Estimate: 1 minute

6. **TASK-006: Monitor CI until green** [QualityEnforcerAgent]
   - Command: `gh run watch`
   - Acceptance: CI status = success (green ✅)
   - Timeout: 5 minutes (typical CI run time)
   - Estimate: 3 minutes

#### Phase 2: Merge PR to Main (5 minutes)
**Duration**: 5 minutes
**Agents**: QualityEnforcerAgent
**Deliverables**:
- [ ] PR #81 merged to main (squash merge)
- [ ] Branch deleted (leap-4-quality-feedback-loop)
- [ ] Main branch updated with PR changes
- [ ] Main branch CI triggered

**Tasks**:
1. **TASK-007: Verify PR CI green** [QualityEnforcerAgent]
   - Command: `gh run list --branch leap-4-quality-feedback-loop --limit 1`
   - Acceptance: Status = completed, Conclusion = success
   - Estimate: 30 seconds

2. **TASK-008: Merge PR to main** [QualityEnforcerAgent]
   - Command: `gh pr merge 81 --squash --delete-branch`
   - Merge strategy: Squash (single commit on main)
   - Acceptance: PR merged, branch deleted, main updated
   - Estimate: 1 minute

3. **TASK-009: Verify main updated** [QualityEnforcerAgent]
   - Command: `git checkout main && git pull`
   - Verify: Latest commit includes PR changes
   - Acceptance: `git log -1` shows PR merge commit
   - Estimate: 30 seconds

4. **TASK-010: Monitor main CI start** [QualityEnforcerAgent]
   - Command: `gh run watch`
   - Expected: CI starts automatically after merge
   - Acceptance: CI workflow running
   - Estimate: 1 minute
   - **NOTE**: CI will show ~51 lint errors (expected, will fix in Phase 3)

#### Phase 3: Holistic Main Branch Cleanup (30 minutes)
**Duration**: 30 minutes
**Agents**: QualityEnforcerAgent
**Deliverables**:
- [ ] 51 main branch lint errors fixed
- [ ] 42 files formatted
- [ ] Full test suite passes (1,725 tests, 100% success)
- [ ] Main branch CI green ✅
- [ ] Holistic cleanup commit pushed

**Tasks**:
1. **TASK-011: Checkout latest main** [QualityEnforcerAgent]
   - Command: `git checkout main && git pull`
   - Verify: On main branch with latest changes
   - Acceptance: `git branch --show-current` returns "main"
   - Estimate: 30 seconds

2. **TASK-012: Auto-fix all main lint errors** [QualityEnforcerAgent]
   - Command: `ruff check --fix .`
   - Expected: 51 main errors fixed (100% auto-fixable per audit)
   - Files: 19 main-specific files (zero overlap with PR)
     - demo_agent_context_checkpoints.py
     - demo_checkpoint_manager.py
     - shared/adaptive_model_router.py
     - shared/agent_context.py
     - shared/checkpoint_manager.py
     - ... (14 more files in shared/session, tests/benchmarks)
   - Acceptance: `ruff check .` returns 0
   - Estimate: 5 minutes

3. **TASK-013: Format all main files** [QualityEnforcerAgent]
   - Command: `ruff format .`
   - Expected: 42 files formatted
   - Acceptance: `ruff format --check .` returns 0
   - Estimate: 1 minute

4. **TASK-014: Run full test suite (Article I: Complete Context)** [QualityEnforcerAgent]
   - Command: `python run_tests.py --run-all`
   - Expected: 1,725 tests pass (100% success rate)
   - Memory-aware: 3 workers with local model (prevents memory exhaustion)
   - Timeout: 10 minutes (Article I retry if needed)
   - Acceptance: Exit code 0, "1725 passed" in output
   - Estimate: 15 minutes
   - **CRITICAL**: Must be 100% pass rate (Article II)

5. **TASK-015: Verify clean state** [QualityEnforcerAgent]
   - Command: `ruff check . && ruff format --check .`
   - Acceptance: Exit code 0 (no errors)
   - Estimate: 30 seconds

6. **TASK-016: Commit holistic cleanup** [QualityEnforcerAgent]
   - Stage: All modified files from TASK-012 to TASK-013
   - Commit message:
     ```
     fix: Holistic ruff lint cleanup across entire codebase (ADR-026)

     Constitutional compliance (Article II: 100% verification):
     - Fixed 51 ruff lint errors on main branch
     - Formatted 42 files
     - All 1,725 tests passing (100% success rate)

     Error types fixed:
     - F401 (unused imports): 10 occurrences
     - I001 (import sorting): 7 occurrences
     - F541 (f-string placeholders): 4 occurrences
     - UP015 (redundant open modes): 3 occurrences
     - UP006 (deprecated typing): 3 occurrences
     - UP035 (deprecated imports): 3 occurrences
     - C416 (unnecessary comprehension): 3 occurrences
     - Others: 18 occurrences

     Zero file overlap with PR #81 (19 main-only files).

     Strategy: Holistic cleanup (ADR-026)
     - 22% time savings vs incremental (70min vs 90min)
     - Single comprehensive pass vs two separate phases
     - Consistent error handling patterns across codebase

     Related: ADR-026 (Holistic CI Quality Cleanup Strategy)

     🤖 Generated with [Claude Code](https://claude.com/claude-code)

     Co-Authored-By: Claude <noreply@anthropic.com>
     ```
   - Commands:
     - `git add -A`
     - `git commit -m "$(cat <<'EOF' ... EOF)"`
     - `git push origin main`
   - Estimate: 2 minutes

7. **TASK-017: Monitor main CI until green** [QualityEnforcerAgent]
   - Command: `gh run watch`
   - Acceptance: CI status = success (green ✅)
   - Timeout: 10 minutes (full test suite + linting)
   - Estimate: 6 minutes

#### Phase 4: Constitutional Verification (10 minutes)
**Duration**: 10 minutes
**Agents**: QualityEnforcerAgent, AuditorAgent
**Deliverables**:
- [ ] Constitutional audit report (Articles I-V)
- [ ] Quality score >90% (baseline: 87.4%)
- [ ] 100% constitutional compliance
- [ ] Final quality metrics documented

**Tasks**:
1. **TASK-018: Run constitutional audit** [QualityEnforcerAgent]
   - Command: `/constitutional-audit all suggest`
   - Verify: All Articles I-V pass
   - Acceptance: 100% compliance across all articles
   - Estimate: 5 minutes

2. **TASK-019: Verify Article I compliance** [QualityEnforcerAgent]
   - Check: Complete context achieved via triple audit
   - Verify: No timeouts, no partial results
   - Acceptance: All tests run to completion (1,725/1,725)
   - Estimate: 1 minute

3. **TASK-020: Verify Article II compliance** [QualityEnforcerAgent]
   - Check: 100% test success rate + 0 lint errors
   - Command: `gh run list --branch main --limit 1`
   - Acceptance: Status = success, conclusion = success
   - Estimate: 1 minute

4. **TASK-021: Verify Article III compliance** [QualityEnforcerAgent]
   - Check: Automated enforcement maintained (no bypasses)
   - Verify: Pre-commit hooks active, CI blocking on errors
   - Acceptance: Zero manual overrides used
   - Estimate: 1 minute

5. **TASK-022: Verify Article IV compliance** [QualityEnforcerAgent]
   - Check: VectorStore learning integration
   - Verify: Holistic cleanup pattern ready for storage
   - Acceptance: Learning entry prepared (Phase 5)
   - Estimate: 1 minute

6. **TASK-023: Generate final quality report** [AuditorAgent]
   - Metrics:
     - Lint errors: 95 → 0 (100% reduction)
     - Test pass rate: Blocked → 100% (1,725/1,725)
     - Quality score: 87.4% → >90%
     - Constitutional compliance: 75% → 100%
     - CI status: ❌ FAILING → ✅ PASSING
   - Acceptance: Report shows all metrics green
   - Estimate: 1 minute

#### Phase 5: Documentation and Learning (15 minutes)
**Duration**: 15 minutes
**Agents**: LearningAgent, QualityEnforcerAgent
**Deliverables**:
- [ ] VectorStore learning entry stored
- [ ] ADR-026 status updated to "Implemented"
- [ ] Success metrics documented
- [ ] Post-mortem insights captured

**Tasks**:
1. **TASK-024: Store holistic cleanup pattern** [LearningAgent]
   - VectorStore entry:
     - Key: "holistic_cleanup_pattern_20251010"
     - Content: Pattern details (see Data Contracts section)
     - Tags: ["architecture", "cleanup", "merge_strategy", "zero_overlap"]
     - Confidence: 0.9 (high confidence in pattern)
   - Acceptance: Entry stored, searchable via tags
   - Estimate: 3 minutes

2. **TASK-025: Store zero-overlap merge strategy** [LearningAgent]
   - VectorStore entry:
     - Key: "zero_overlap_merge_strategy_20251010"
     - Content:
       ```json
       {
         "pattern": "zero_overlap_merge_first",
         "trigger": "pr_errors_and_main_errors_disjoint",
         "decision": "merge_pr_before_main_cleanup",
         "rationale": "Zero merge conflict risk, 22% time savings",
         "success_rate": 1.0,
         "time_savings_percent": 22
       }
       ```
     - Tags: ["architecture", "merge_strategy", "zero_overlap", "optimization"]
     - Confidence: 0.85
   - Acceptance: Entry stored, searchable via tags
   - Estimate: 3 minutes

3. **TASK-026: Update ADR-026 status** [QualityEnforcerAgent]
   - File: docs/adr/ADR-026-ci-quality-holistic-cleanup.md
   - Change: Status "Proposed" → "Implemented"
   - Add implementation notes:
     - Actual time: 70 minutes (as estimated)
     - Errors fixed: 95 (44 PR + 51 main)
     - Test pass rate: 100% (1,725/1,725)
     - Quality score: 87.4% → >90%
     - Success: ✅
   - Acceptance: ADR-026 reflects implementation success
   - Estimate: 5 minutes

4. **TASK-027: Document success metrics** [QualityEnforcerAgent]
   - Create summary in logs/audits/holistic_cleanup_success_20251010.md
   - Include:
     - Timeline (actual vs estimated)
     - Errors fixed (breakdown by type)
     - Test results (1,725/1,725 pass)
     - Constitutional compliance (100%)
     - Learnings stored (VectorStore entries)
     - Time savings (22% vs incremental)
   - Acceptance: Summary complete, ready for review
   - Estimate: 4 minutes

### File Structure Plan

**Modified Files** (No new files created, only editing existing):
```
/Users/am/Code/Agency/
├── agency_memory/
│   ├── vector_index.py          (PR fix: format + lint)
│   └── vector_store.py           (PR fix: format + lint)
├── demo_batch_memory_reads.py    (PR fix: format + lint)
├── tests/
│   └── test_leap4_e2e_quality_feedback.py  (PR fix: format + lint)
├── tools/
│   ├── async_memory_tool.py      (PR fix: format + lint)
│   ├── memory_lock_manager.py    (PR fix: format + lint)
│   ├── skill_dashboard.py        (PR fix: format + lint)
│   └── validate_cost_savings.py  (PR fix: format + lint)
├── [19 main-only files]          (Main fix: format + lint)
│   ├── demo_agent_context_checkpoints.py
│   ├── demo_checkpoint_manager.py
│   ├── shared/adaptive_model_router.py
│   ├── shared/agent_context.py
│   ├── shared/checkpoint_manager.py
│   └── ... (14 more)
├── docs/adr/
│   └── ADR-026-ci-quality-holistic-cleanup.md  (Update status)
└── logs/audits/
    └── holistic_cleanup_success_20251010.md  (New summary)
```

---

## Quality Assurance Strategy

### Testing Framework

#### Unit Testing
- **Framework**: pytest
- **Coverage Target**: 100% (Constitutional requirement - Article II)
- **Test Categories**:
  - All existing tests must pass (1,725 tests)
  - No new tests needed (quality fix only, no functional changes)

#### Integration Testing
- **Framework**: pytest with run_tests.py
- **Test Scenarios**:
  - Full test suite run (--run-all flag)
  - Memory-aware worker configuration (3 workers with local model)
  - Timeout handling (10 minutes, Article I retry logic)

#### End-to-End Testing
- **Framework**: GitHub Actions CI
- **Test Scenarios**:
  - PR CI run (after Phase 1 commit)
  - Main CI run (after Phase 3 commit)
  - Lint + format + test suite (full pipeline)

### Constitutional Compliance Validation

#### Article I: Complete Context Before Action
- **Validation Method**: Full test suite run with retry logic
- **Test Cases**:
  - Run all 1,725 tests to completion (no partial results)
  - Memory-aware worker configuration prevents crashes
  - Timeout retry (2x, 3x, 10x) on failures
- **Acceptance**: 100% test completion rate

#### Article II: 100% Verification and Stability
- **Validation Method**: Test suite execution + lint checks
- **Test Cases**:
  - All 1,725 tests pass (100% success rate)
  - Ruff check passes (0 errors)
  - Ruff format check passes (0 formatting issues)
- **Acceptance**: CI green ✅ on both PR and main

#### Article III: Automated Merge Enforcement
- **Validation Method**: CI blocking verification
- **Test Cases**:
  - CI correctly blocked PR merge before fixes
  - Pre-commit hooks active and enforcing
  - No manual bypasses used (--no-verify, force push)
- **Acceptance**: Zero bypass mechanisms used

#### Article IV: Continuous Learning and Improvement
- **Validation Method**: VectorStore entry verification
- **Test Cases**:
  - Holistic cleanup pattern stored (confidence ≥ 0.6)
  - Zero-overlap merge strategy stored
  - Patterns tagged for future retrieval
- **Acceptance**: 2+ VectorStore entries created

#### Article V: Spec-Driven Development
- **Validation Method**: ADR-026 compliance check
- **Test Cases**:
  - Implementation follows ADR-026 phases
  - Success criteria met (all 5 phases complete)
  - Rollback plan documented (not needed if successful)
- **Acceptance**: ADR-026 status = "Implemented"

### Quality Gates

- [x] **Pre-Flight**: Current branch verified (leap-4-quality-feedback-loop)
- [ ] **Phase 1 Gate**: PR CI green ✅ (44 errors → 0)
- [ ] **Phase 2 Gate**: PR merged to main, branch deleted
- [ ] **Phase 3 Gate**: Main CI green ✅ (51 errors → 0, 1,725 tests pass)
- [ ] **Phase 4 Gate**: Constitutional audit passes (100% compliance)
- [ ] **Phase 5 Gate**: VectorStore learnings stored (2+ entries)

---

## Risk Mitigation

### Technical Risks

#### Risk 1: Auto-fix introduces functional bugs
- **Probability**: Low (ruff auto-fixes are deterministic and safe)
- **Impact**: Medium (tests would fail, easy to detect)
- **Mitigation Strategy**:
  - Full test suite run after auto-fix (TASK-014)
  - Ruff uses "safe" auto-fixes only by default
  - Manual review of auto-fix changes if tests fail
- **Contingency Plan**:
  - Rollback: `git revert HEAD`
  - Manual fix problematic auto-fixes
  - Re-run tests, re-commit

#### Risk 2: Test failures during Phase 3 (main cleanup)
- **Probability**: Low (zero file overlap, no functional changes)
- **Impact**: High (main branch blocked, CI red)
- **Mitigation Strategy**:
  - Full test suite run before commit (TASK-014)
  - Memory-aware test runner prevents crashes
  - Article I retry logic (2x, 3x, 10x timeouts)
- **Contingency Plan**:
  - Rollback: `git revert HEAD`
  - Identify failing tests (pytest output)
  - Fix root cause (likely auto-fix issue)
  - Re-run Phase 3 with fix

#### Risk 3: Manual fixes needed in Phase 1
- **Probability**: Low (ruff handles most error types)
- **Impact**: Low (adds 3 minutes, manageable)
- **Mitigation Strategy**:
  - Quick fix guide (logs/audits/QUICK_FIX_GUIDE.md) documents patterns
  - B904: Add `from e` to exception re-raises
  - B007: Rename unused loop vars to `_`
- **Contingency Plan**:
  - Follow quick fix guide patterns
  - If unfamiliar with error, research ruff docs
  - Worst case: ask user for guidance

### Operational Risks

#### Risk 4: CI timeout during test run
- **Probability**: Low (typical CI run: 6-8 minutes, timeout: 10 minutes)
- **Impact**: Medium (delays merge, no functional issue)
- **Mitigation Strategy**:
  - Memory-aware test runner optimizes worker count
  - Article I retry logic automatically retries on timeout
  - CI timeout set to 10 minutes (sufficient for full suite)
- **Contingency Plan**:
  - Re-trigger CI manually: `gh run rerun <run-id>`
  - If persistent: reduce test parallelism (workers: 3 → 2)
  - If still failing: investigate test suite performance

#### Risk 5: Merge conflicts during PR merge (Phase 2)
- **Probability**: Very Low (zero file overlap between PR and main errors)
- **Impact**: Medium (delays merge, requires conflict resolution)
- **Mitigation Strategy**:
  - ADR-026 analysis confirmed zero file overlap (0% conflict risk)
  - PR branch synced with main recently (commits 6a010d3)
- **Contingency Plan**:
  - Abort merge: `git merge --abort`
  - Re-sync PR with main: `git merge main`
  - Resolve conflicts manually
  - Re-run Phase 1 tests, retry merge

### Constitutional Risks

#### Risk 6: Article IV violation (learning not stored)
- **Article**: Article IV (Continuous Learning and Improvement)
- **Mitigation Strategy**:
  - Phase 5 dedicated to VectorStore learning storage (TASK-024, TASK-025)
  - Pattern storage mandatory before plan completion
  - Constitutional audit verifies learning storage (TASK-022)
- **Monitoring**:
  - VectorStore query after Phase 5: `context.search_memories(["holistic_cleanup"])`
  - Verify 2+ entries exist with confidence ≥ 0.6

#### Risk 7: Article II violation (incomplete test coverage)
- **Article**: Article II (100% Verification and Stability)
- **Mitigation Strategy**:
  - Full test suite run mandatory (TASK-014)
  - 100% pass rate required (no exceptions)
  - CI green required before merge (TASK-006, TASK-017)
- **Monitoring**:
  - CI status check: `gh run list --branch main --limit 1`
  - Test output verification: "1725 passed" in pytest output

---

## Performance Considerations

### Performance Requirements
- **Requirement 1**: Phase 1 completion ≤ 10 minutes (auto-fix + format + CI)
- **Requirement 2**: Phase 3 completion ≤ 30 minutes (main cleanup + full test suite)
- **Requirement 3**: Total execution ≤ 70 minutes (all 5 phases)

### Optimization Strategy
- **Strategy 1**: Use ruff auto-fix instead of manual fixes (39/44 errors auto-fixable)
- **Strategy 2**: Memory-aware test runner (3 workers with local model, prevents crashes)
- **Strategy 3**: Holistic cleanup over incremental (22% time savings: 70min vs 90min)

### Monitoring & Metrics
- **Metric 1**: Phase completion time (actual vs estimated)
- **Metric 2**: Test execution time (target: <15 minutes with 3 workers)
- **Metric 3**: CI run time (target: <8 minutes per run)

---

## Security Considerations

### Security Requirements
- **Authentication**: GitHub token (gh CLI) for PR merge and CI monitoring
- **Authorization**: Git push requires authenticated user (no anonymous commits)
- **Data Protection**: No sensitive data modified (only code quality fixes)
- **Privacy**: No user data involved (codebase-only changes)

### Security Implementation
- **Security Measure 1**: All git operations authenticated via gh CLI
- **Security Measure 2**: Pre-commit hooks enforce quality gates (no bypass)
- **Security Measure 3**: CI pipeline validates all changes before merge

### Threat Model
- **Threat 1**: Malicious code injection via auto-fix
  - **Mitigation**: Ruff is open-source, audited tool (deterministic fixes)
  - **Detection**: Full test suite catches functional regressions
- **Threat 2**: Unauthorized branch deletion
  - **Mitigation**: GitHub branch protection (main branch protected)
  - **Detection**: Audit logs in GitHub UI

---

## Learning Integration

### Learning Opportunities
- **Pattern 1**: Holistic cleanup strategy (zero file overlap enables merge-first)
- **Pattern 2**: Time optimization (22% savings via consolidated approach)
- **Pattern 3**: Constitutional compliance methodology (Articles I-V validation)

### Historical Learning Application
- **Applied Learning 1**: ADR-026 informed by triple audit (Article I: complete context)
- **Applied Learning 2**: Memory-aware test runner from PR #56 (prevents crashes)
- **Applied Learning 3**: Ruff auto-fix patterns from prior quality initiatives

### Learning Extraction Plan
- **Extract 1**: Store holistic cleanup pattern (confidence 0.9)
- **Extract 2**: Store zero-overlap merge strategy (confidence 0.85)
- **Extract 3**: Document time savings metric (22% improvement)

---

## Resource Requirements

### Agent Time Allocation
- **QualityEnforcerAgent**: 60 minutes (Phases 1-4)
- **AuditorAgent**: 5 minutes (Phase 4 quality report)
- **LearningAgent**: 10 minutes (Phase 5 learning storage)
- **ChiefArchitect**: 0 minutes (ADR-026 already complete)

### Infrastructure Requirements
- **Compute Resources**: Local development machine (sufficient for ruff, git, pytest)
- **Storage Requirements**: <1MB (git commits, no large files)
- **Network Requirements**: GitHub API access (gh CLI), VectorStore API (Firestore)

### External Dependencies
- **Service 1**: GitHub Actions CI (automatic, no setup needed)
- **Service 2**: VectorStore (Firestore) - already configured
- **Service 3**: Ruff linter/formatter (installed via pip)

---

## Monitoring & Observability

### Implementation Monitoring
- **Progress Tracking**: TodoWrite NOT USED (simple sequential workflow)
- **Quality Metrics**:
  - Lint errors: 95 → 0 (real-time via ruff check)
  - Test pass rate: Blocked → 100% (real-time via pytest)
  - CI status: ❌ → ✅ (real-time via gh run watch)
- **Performance Metrics**:
  - Phase completion time (actual vs 70min estimate)
  - Test execution time (target <15min)

### Post-Implementation Monitoring
- **Success Metrics**:
  - CI green ✅ on main branch (sustained >24 hours)
  - Zero regression bugs reported
  - VectorStore learnings retrievable (2+ entries)
- **Health Checks**:
  - Daily: `ruff check .` returns 0
  - Daily: `python run_tests.py --run-all` returns 100% pass
- **Alerting**:
  - GitHub Actions failure notifications (email/Slack)
  - Pre-commit hook failures (local developer alerts)

---

## Rollback Strategy

### Rollback Triggers
- **Trigger 1**: Phase 1 fails (PR CI remains red after fixes)
- **Trigger 2**: Phase 3 fails (main tests fail after holistic cleanup)
- **Trigger 3**: Constitutional audit fails (Phase 4)

### Rollback Procedure

#### Rollback 1: Phase 1 Failure (PR CI red)
1. Revert Phase 1 commit: `git revert HEAD`
2. Push revert: `git push origin leap-4-quality-feedback-loop`
3. Investigate CI failure logs: `gh run view <run-id>`
4. Fix root cause (likely manual fix needed for unfixable ruff errors)
5. Re-run Phase 1 with fix

#### Rollback 2: Phase 3 Failure (main tests fail)
1. Revert Phase 3 commit: `git revert HEAD`
2. Push revert: `git push origin main`
3. Identify failing tests: `pytest tests/test_*.py --tb=short`
4. Fix root cause (likely auto-fix introduced bug)
5. Re-run Phase 3 with fix
6. If unfixable: Fall back to incremental cleanup (Alternative 1 in ADR-026)

#### Rollback 3: Phase 4 Failure (constitutional violation)
1. Document violation in ADR-026 (which article failed)
2. No code rollback needed (quality improvements remain)
3. Address violation:
   - Article I: Re-run tests with extended timeout
   - Article II: Investigate test failures, fix and re-run
   - Article III: Verify no bypasses used
   - Article IV: Complete VectorStore learning storage (Phase 5)
   - Article V: Verify ADR-026 compliance
4. Re-run constitutional audit after fix

### Data Recovery
- **Backup Strategy**: Git history preserves all changes (revertible)
- **Recovery Process**:
  - List commits: `git log --oneline`
  - Revert specific commit: `git revert <commit-hash>`
  - Reset to pre-implementation: `git reset --hard 6a010d3` (main branch before PR merge)

### Nuclear Option (Complete Failure)
1. Reset main to pre-merge state: `git reset --hard 6a010d3`
2. Force push: `git push origin main --force` (requires admin override)
3. Recreate PR branch: `git checkout -b leap-4-quality-feedback-loop-v2`
4. Fall back to incremental cleanup (Alternative 1 in ADR-026)
5. Document failure in ADR-026 "Lessons Learned" section
6. Store failure pattern in VectorStore (Article IV)

**Note**: Nuclear option requires admin override (violates Article III), use only if absolutely necessary.

---

## Documentation Plan

### User Documentation
- **Document 1**: ADR-026 implementation notes (update status to "Implemented")
- **Document 2**: Success metrics summary (logs/audits/holistic_cleanup_success_20251010.md)

### Technical Documentation
- **Document 1**: This plan (plan-026-ci-quality-holistic-fix.md)
- **Document 2**: VectorStore learning entries (holistic cleanup pattern, zero-overlap strategy)

### API Documentation
- **Documentation Format**: No API changes (quality fix only)
- **Coverage**: N/A

---

## Review & Approval

### Technical Review Checklist
- [x] **Architecture**: Sound and scalable design (ADR-026 approved)
- [x] **Implementation**: Feasible with available resources (ruff, git, gh, pytest)
- [x] **Quality**: Meets all quality requirements (100% test pass, 0 lint errors)
- [x] **Performance**: Satisfies performance requirements (70 minutes total)
- [x] **Security**: Addresses all security concerns (authenticated git operations)
- [x] **Constitutional**: Complies with all constitutional articles (Articles I-V)

### Approval Status
- [x] **Technical Lead Approval**: PlannerAgent (this plan)
- [x] **Security Review**: No security changes (quality fix only)
- [x] **Architecture Review**: ChiefArchitect (ADR-026 approved)
- [ ] **Constitutional Compliance**: QualityEnforcer (Phase 4 verification)
- [ ] **Final Approval**: User (pending execution)

---

## Appendices

### Appendix A: Ruff Error Types Reference

```python
# UP035: Deprecated typing imports
# Before: from typing import Dict, List, Tuple
# After:  from typing import ... (no import, use dict, list, tuple directly)

# F401: Unused imports
# Before: from datetime import datetime, UTC, timezone  # timezone unused
# After:  from datetime import datetime, UTC

# I001: Import sorting
# Before: import pytest\nimport json\nfrom pathlib import Path
# After:  import json\nfrom pathlib import Path\nimport pytest

# UP006: Deprecated typing generics
# Before: List[str], Dict[str, int]
# After:  list[str], dict[str, int]

# UP041: Deprecated asyncio.TimeoutError
# Before: except asyncio.TimeoutError:
# After:  except TimeoutError:

# C416: Unnecessary comprehension
# Before: list(x for x in items)
# After:  list(items)

# F541: F-string without placeholders
# Before: f"No placeholder here"
# After:  "No placeholder here"

# B904: Exception chaining missing
# Before: except ImportError:\n    raise ImportError("message")
# After:  except ImportError as e:\n    raise ImportError("message") from e

# B007: Unused loop variable
# Before: for item in items:  # item never used
# After:  for _ in items:
```

### Appendix B: Memory-Aware Test Runner Configuration

```python
# tools/memory_aware_test_runner.py
from tools.memory_aware_test_runner import get_safe_worker_count

worker_count = get_safe_worker_count()
# Returns:
# - 1 worker if <10GB available (critical memory)
# - 3 workers if local model ON + <15GB (safe: 38GB model + 9GB tests)
# - 10 workers if local model OFF + >20GB (full parallelism)
# - 6 workers otherwise (moderate parallelism)

# Integration with pytest:
pytest_args = ["-n", str(worker_count), "--dist", "loadgroup"]
```

### Appendix C: Zero File Overlap Analysis

```
PR branch errors (44 errors in 8 files):
  - agency_memory/vector_index.py
  - agency_memory/vector_store.py
  - demo_batch_memory_reads.py
  - tests/test_leap4_e2e_quality_feedback.py
  - tools/async_memory_tool.py
  - tools/memory_lock_manager.py
  - tools/skill_dashboard.py
  - tools/validate_cost_savings.py

Main branch errors (51 errors in 19 files):
  - demo_agent_context_checkpoints.py
  - demo_checkpoint_manager.py
  - shared/adaptive_model_router.py
  - shared/agent_context.py
  - shared/checkpoint_manager.py
  - shared/session/checkpoint_config.py
  - shared/session/checkpoint_error.py
  - shared/session/checkpoint_manager.py
  - shared/session/checkpoint_metadata.py
  - shared/session/checkpoint_policy.py
  - shared/session/checkpoint_strategy.py
  - shared/session/error_recovery.py
  - shared/session/phase_transitions.py
  - shared/session/resource_cleanup.py
  - shared/session/state_machine.py
  - tests/benchmarks/benchmark_checkpoint_overhead.py
  - tests/benchmarks/benchmark_session_state_scalability.py
  - tests/benchmarks/session_benchmarks_dashboard.py
  - tests/test_checkpoint_compression.py

Overlap: 0 files (0% conflict risk)
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-10 | PlannerAgent | Initial implementation plan based on ADR-026 |

---

## Dependencies

**Required Before Implementation**:
- [x] CI failure analysis complete (logs/audits/audit_pr_leap4_20251010.json)
- [x] Main branch audit complete (logs/audits/main_branch_audit_20251010.json)
- [x] Zero file overlap analysis complete
- [x] ADR-026 approved (proposed status, awaiting execution)

**Blocking Issues**:
- None (all audits complete, zero blockers)

**Related ADRs**:
- ADR-001: Complete Context Before Action (Article I compliance)
- ADR-002: 100% Verification and Stability (Article II compliance)
- ADR-003: Automated Merge Enforcement (Article III compliance)
- ADR-004: Continuous Learning and Improvement (Article IV compliance)
- ADR-007: Spec-Driven Development (Article V compliance)
- ADR-026: Holistic CI Quality Cleanup Strategy (PRIMARY REFERENCE)

**Related PRs**:
- PR #81: Leap 4 Quality Feedback Loop (to be merged in Phase 2)

**Constitutional References**:
- constitution.md (Articles I-V)

**Code References**:
- tools/memory_aware_test_runner.py (test execution)
- run_tests.py (full test suite runner)
- .github/workflows/ (CI pipeline)
- pyproject.toml (ruff configuration)

---

## Success Criteria

### Phase 1 Success Criteria
- [x] Current branch: leap-4-quality-feedback-loop
- [ ] Ruff check passes (0 errors)
- [ ] Ruff format check passes (0 formatting issues)
- [ ] PR CI green ✅
- [ ] Commit pushed to PR branch

### Phase 2 Success Criteria
- [ ] PR CI green (verified before merge)
- [ ] PR #81 merged to main (squash merge)
- [ ] Branch deleted (leap-4-quality-feedback-loop)
- [ ] Main branch updated (git log shows merge commit)

### Phase 3 Success Criteria
- [ ] 51 main lint errors fixed
- [ ] 42 files formatted
- [ ] Full test suite passes (1,725 tests, 100% success)
- [ ] Ruff check passes (0 errors)
- [ ] Main CI green ✅

### Phase 4 Success Criteria
- [ ] Constitutional audit passes (Articles I-V, 100% compliance)
- [ ] Quality score >90% (baseline: 87.4%)
- [ ] Test pass rate: 100% (1,725/1,725)
- [ ] CI status: ✅ PASSING (main branch)

### Phase 5 Success Criteria
- [ ] VectorStore entry stored (holistic cleanup pattern)
- [ ] VectorStore entry stored (zero-overlap merge strategy)
- [ ] ADR-026 status updated (Proposed → Implemented)
- [ ] Success metrics documented (logs/audits/holistic_cleanup_success_20251010.md)

### Overall Success Criteria
- [ ] All 5 phases complete
- [ ] Total execution time ≤ 70 minutes
- [ ] 95 lint errors fixed (44 PR + 51 main)
- [ ] 100% test pass rate (1,725/1,725)
- [ ] 100% constitutional compliance (Articles I-V)
- [ ] 2+ VectorStore learning entries stored
- [ ] CI green ✅ on main branch (sustained >24 hours)

---

*"In holistic thinking we find efficiency, in zero overlap we find opportunity, in learning we find growth."*

**Ready for Execution**: Awaiting user approval to begin Phase 1.
