# Specification: Parallel Development Rails System

**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft
**Author**: Claude Sonnet 4.5 (Autonomous)

---

## Executive Summary

Build a "success rails" system that makes parallel development **so easy it's irresistible**, while maintaining **user as ultimate authority** for all decisions.

**Core Principle**: "System suggests, user decides, system executes."

---

## Goals

### Primary Goals
1. **Zero-Conflict Parallel Development**: Enable 5-10 agents working simultaneously
2. **Foolproof Workflow**: Make correct path easier than incorrect path
3. **User Authority Preserved**: All destructive actions require approval
4. **Learning System**: VectorStore learns what works, prevents known conflicts

### Non-Goals
- ❌ Automatic merging without approval
- ❌ Overriding user decisions
- ❌ Hiding complexity entirely (transparency > magic)
- ❌ Removing constitutional enforcement

---

## Personas

### Persona 1: "Orchestrating User" (Primary)
**Who**: Developer managing multiple autonomous agents
**Needs**:
- Quick status of all parallel work
- Confidence that agents won't conflict
- Ability to override any decision
- Visibility into what agents are doing

**Pain Points**:
- Merge conflicts from parallel work
- Lost work due to worktree confusion
- Unclear what's safe to merge
- Too many decisions to make

### Persona 2: "Autonomous Agent" (Secondary)
**Who**: Claude Code agent working on task
**Needs**:
- Know if safe to proceed in parallel
- Automatic worktree setup
- Constitutional compliance
- Clear approval gates

**Pain Points**:
- Don't know about other agents' work
- Worktree setup is manual
- Pre-commit failures in worktrees
- Merge conflicts discovered too late

---

## User Stories

### Story 1: Starting Parallel Work
```
AS a user with Agent1 already working on tests
WHEN I want to start work on a new feature
THEN system should:
  1. Detect Agent1's parallel work automatically
  2. Analyze conflict probability
  3. Recommend worktree protocol
  4. Set up worktree with ONE approval
  5. Track both workstreams
```

### Story 2: Preventing Conflicts
```
AS a user starting work on database changes
WHEN another agent is also modifying database
THEN system should:
  1. Detect high conflict probability
  2. Show which files overlap
  3. Suggest coordination or alternative approach
  4. Store conflict pattern in VectorStore
  5. Prevent similar issues in future
```

### Story 3: Merge Orchestration
```
AS a user with 3 PRs ready to merge
WHEN all CI checks are green
THEN system should:
  1. Analyze merge order dependencies
  2. Show optimal merge sequence
  3. Estimate time to complete
  4. Execute ONLY after approval
  5. Provide rollback option if issues occur
```

### Story 4: Constitutional Override
```
AS a user with emergency production hotfix
WHEN I need to commit directly to main
THEN system should:
  1. Block per Article III (as expected)
  2. Offer override option with reason prompt
  3. Log override for learning
  4. Execute after I provide reason
  5. Notify merge-guardian for coordination
```

---

## Acceptance Criteria

### Must Have (v1.0)
- ✅ `/parallel-dev [intent]` command creates worktree with conflict analysis
- ✅ Pre-commit hook detects parallel work and suggests worktree protocol
- ✅ `/merge-status` shows all active work across worktrees
- ✅ Merge-guardian-lite analyzes merge safety before execution
- ✅ All destructive operations require explicit approval
- ✅ User can override any decision with reason (logged for learning)
- ✅ Dry-run mode for all risky operations
- ✅ Automatic backups before worktree deletion
- ✅ VectorStore integration for conflict pattern learning

### Should Have (v1.1)
- ⏳ `/agency-status` dashboard with all agent activity
- ⏳ Conflict probability prediction using ML ensemble
- ⏳ Automatic coordination suggestions based on VectorStore
- ⏳ `/undo-last` universal rollback command
- ⏳ Merge plan visualization (dependency graph)

### Could Have (v2.0)
- ⏳ Real-time agent activity notifications
- ⏳ Automatic PR creation after worktree completion
- ⏳ Multi-agent chat for coordination
- ⏳ Predictive conflict detection using file history

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  /parallel-dev | /merge-status | /constitutional-check      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                   Detection Layer                            │
│  - Parallel work detector (pre-commit hook)                  │
│  - Conflict analyzer (file overlap, VectorStore patterns)   │
│  - Worktree scanner (active branches, uncommitted changes)  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                  Orchestration Layer                         │
│  - Worktree manager (create, delete, backup)                │
│  - Merge-guardian-lite (merge order, safety checks)         │
│  - Approval gate manager (user prompts, logging)            │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Learning Layer                            │
│  - VectorStore (conflict patterns, successful workflows)    │
│  - ML ensemble (conflict probability prediction)            │
│  - Pattern extractor (learn from user overrides)            │
└─────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. Parallel Work Detector
**File**: `tools/parallel_dev/parallel_work_detector.py`

```python
class ParallelWorkDetector:
    """Detect parallel work across all worktrees."""

    def scan_worktrees(self) -> List[WorktreeInfo]:
        """Scan all git worktrees for uncommitted changes."""

    def analyze_conflicts(self, new_files: List[str]) -> ConflictAnalysis:
        """Analyze conflict probability with parallel work."""

    def get_recommendations(self, analysis: ConflictAnalysis) -> List[str]:
        """Get recommendations based on conflict analysis."""
```

**Inputs**:
- Files user intends to modify
- Current git state

**Outputs**:
- List of active worktrees
- Conflict probability (0.0-1.0)
- Recommendations (worktree, coordinate, proceed)

**Algorithm**:
1. Get all worktrees: `git worktree list`
2. For each worktree: check `git status --porcelain`
3. Extract modified files
4. Calculate overlap: `len(set(user_files) & set(parallel_files)) / len(user_files)`
5. Query VectorStore for similar past conflicts
6. Return weighted probability

#### 2. Worktree Manager
**File**: `tools/parallel_dev/worktree_manager.py`

```python
class WorktreeManager:
    """Manage worktree lifecycle with safety guarantees."""

    def create_worktree(self, intent: str, auto_branch: bool = True) -> WorktreeInfo:
        """Create new worktree with automatic branch naming."""

    def delete_worktree(self, path: str, backup: bool = True) -> None:
        """Delete worktree with automatic backup."""

    def list_worktrees(self) -> List[WorktreeInfo]:
        """List all worktrees with status."""
```

**Safety Features**:
- Automatic backup before deletion
- Uncommitted changes check
- Prune after cleanup
- Git reflog preservation

#### 3. Merge-Guardian-Lite
**File**: `tools/parallel_dev/merge_guardian_lite.py`

```python
class MergeGuardianLite:
    """Lightweight merge orchestrator with approval gates."""

    def analyze_merge_plan(self, prs: List[int]) -> MergePlan:
        """Analyze optimal merge order and conflicts."""

    def execute_merge_plan(self, plan: MergePlan, dry_run: bool = False) -> Result:
        """Execute merge plan with user approval gates."""

    def rollback_merge(self, merge_id: str) -> None:
        """Rollback failed merge."""
```

**Approval Gates**:
- Before starting merge sequence
- After each PR merge (optional)
- On any conflict detected
- Before pushing to remote

#### 4. VectorStore Learning Integration
**File**: `tools/parallel_dev/conflict_learner.py`

```python
class ConflictLearner:
    """Learn conflict patterns from historical data."""

    def store_conflict_pattern(self, pattern: ConflictPattern) -> None:
        """Store successful/failed parallel work pattern."""

    def query_similar_patterns(self, files: List[str]) -> List[Pattern]:
        """Query VectorStore for similar past work."""

    def predict_conflict_probability(self, context: WorkContext) -> float:
        """Predict conflict probability using patterns + ML."""
```

**Learning Signals**:
- Successful parallel work (confidence += 0.1)
- Merge conflicts occurred (confidence -= 0.2)
- User overrides (store reason for context)
- Time to merge (performance metric)

---

## Command Specifications

### `/parallel-dev [intent]`

**Purpose**: Intelligent parallel development orchestrator

**Arguments**:
- `intent` (required): Description of work to do
- `--auto-approve` (optional): Skip approval prompts (not recommended)
- `--force` (optional): Override conflict warnings

**Workflow**:
1. Scan all worktrees for parallel work
2. Analyze conflict probability
3. Show status + recommendations
4. Create worktree if approved
5. Track in VectorStore

**Example**:
```bash
$ /parallel-dev "Add JWT authentication to user service"

🔍 Analyzing parallel work...
✅ Safe to proceed
   Agent1: test_suite_improvements (orthogonal)
   Conflict probability: 5% (LOW)

📋 Proposed workflow:
1. Worktree: Agency-jwt-auth
2. Branch: feat/jwt-auth-user-service
3. Isolated development

Execute? [Y/n]: Y
✅ Worktree created
```

### `/merge-status`

**Purpose**: Show all parallel work and merge readiness

**Arguments**: None

**Output**:
```bash
$ /merge-status

🤖 ACTIVE WORKTREES (4):
────────────────────────────────────────
Agency-main               [main]        ✅ Clean
Agency-ml-v1.1           [PR #101]     ✅ CI Green
Agency-distributed-locks [PR #99]      🔄 CI Running
Agency-parallel-dev-rails [Local]      📝 In Progress

📊 MERGE READINESS:
────────────────────────────────────────
Ready: PR #101 (ML model v1.1)
Waiting: PR #99 (CI must complete)
Not ready: parallel-dev-rails (local only)

⚡ Suggested merge order:
1. #101 (ML model) - Safe, zero conflicts
2. #99 (Distributed locks) - Wait for CI
```

### `/constitutional-check [action]`

**Purpose**: Preview what would be blocked by constitution

**Arguments**:
- `action` (required): Action to check (e.g., "commit to main")

**Example**:
```bash
$ /constitutional-check "commit directly to main"

🔍 Checking: "commit directly to main"

🚫 WOULD BE BLOCKED:
────────────────────────────────────────
Constitution: Article III (Automated Merge Enforcement)
Reason: Direct commits to main not allowed

Override available: YES (with reason)
Alternatives:
  1. Create feature branch
  2. Use /parallel-dev workflow
  3. Override with emergency reason

No action taken (preview only)
```

---

## Implementation Plan

### Phase 1: Foundation (Days 1-2)
**Goal**: Basic parallel work detection and worktree management

**Tasks**:
1. Create `tools/parallel_dev/` directory
2. Implement `ParallelWorkDetector`
3. Implement `WorktreeManager`
4. Create `/parallel-dev` command
5. Write unit tests (20+ tests)

**Deliverables**:
- Working parallel work detection
- Automatic worktree creation
- Basic conflict analysis

### Phase 2: Intelligence (Days 3-4)
**Goal**: VectorStore learning and merge orchestration

**Tasks**:
1. Implement `ConflictLearner`
2. Implement `MergeGuardianLite`
3. Create `/merge-status` command
4. Create `/constitutional-check` command
5. Integration tests (10+ tests)

**Deliverables**:
- VectorStore conflict pattern learning
- Merge plan generation
- Constitutional preview

### Phase 3: Safety & Polish (Day 5)
**Goal**: Guardrails, documentation, rollback

**Tasks**:
1. Implement automatic backups
2. Implement dry-run mode
3. Write comprehensive documentation
4. Create user guide with examples
5. E2E tests (5+ scenarios)

**Deliverables**:
- `docs/PARALLEL_DEV_GUIDE.md`
- `docs/adr/ADR-029-parallel-development-rails.md`
- Complete test coverage (95%+)

---

## Success Metrics

### Quantitative
- **Parallel work conflicts**: <5% (baseline: ~20%)
- **Setup time**: <30 seconds (baseline: 5+ minutes manual)
- **User decisions required**: 1-2 per workflow (baseline: 10+)
- **Merge time**: <2 minutes for 2 PRs (baseline: 10+ minutes)

### Qualitative
- **"Foolproof" rating**: User cannot accidentally cause conflicts
- **"Rails" feeling**: Correct workflow is default, wrong is hard
- **Authority preserved**: User can override ANY decision
- **Learning observed**: System gets smarter over time

---

## Constitutional Compliance

### Article I: Complete Context Before Action
- ✅ Scan ALL worktrees before recommending workflow
- ✅ Query VectorStore for historical patterns
- ✅ Retry on git operation failures

### Article II: 100% Verification and Stability
- ✅ All risky operations have dry-run mode
- ✅ Backups before deletion
- ✅ Git reflog preserved
- ✅ Rollback available

### Article III: Automated Merge Enforcement
- ✅ Merge-guardian validates all merges
- ✅ Constitutional blocks with override option
- ✅ Approval gates for destructive operations

### Article IV: Continuous Learning and Improvement
- ✅ VectorStore stores conflict patterns
- ✅ ML ensemble predicts conflicts
- ✅ System learns from user overrides
- ✅ Patterns shared across agents

### Article V: Spec-Driven Development
- ✅ This specification defines all behavior
- ✅ Implementation traces to acceptance criteria
- ✅ Tests validate spec compliance

---

## Risk Assessment

### High Risk
- **User frustration with too many prompts**
  - Mitigation: Learn user preferences, reduce prompts over time
  - Metric: <2 approvals per workflow

- **False positive conflict warnings**
  - Mitigation: Conservative thresholds, VectorStore learning
  - Metric: <10% false positives

### Medium Risk
- **Complex merge scenarios not handled**
  - Mitigation: Fall back to manual merge with guidance
  - Escalation: Show error, suggest manual intervention

### Low Risk
- **Worktree confusion**
  - Mitigation: Clear naming, status commands
  - Documentation: Comprehensive guide

---

## Appendix A: File Structure

```
tools/parallel_dev/
├── __init__.py
├── parallel_work_detector.py    # Detect parallel work
├── worktree_manager.py           # Manage worktree lifecycle
├── conflict_analyzer.py          # Analyze conflict probability
├── merge_guardian_lite.py        # Merge orchestration
├── conflict_learner.py           # VectorStore learning
├── approval_gate.py              # User approval management
└── README.md                     # API documentation

.claude/commands/
├── parallel-dev.md               # /parallel-dev command
├── merge-status.md               # /merge-status command
└── constitutional-check.md       # /constitutional-check command

tests/tools/parallel_dev/
├── test_parallel_work_detector.py
├── test_worktree_manager.py
├── test_conflict_analyzer.py
├── test_merge_guardian_lite.py
├── test_conflict_learner.py
└── test_e2e_parallel_workflow.py

docs/
├── PARALLEL_DEV_GUIDE.md         # User guide
└── adr/ADR-029-parallel-development-rails.md
```

---

## Appendix B: Authority Hierarchy

```python
AUTHORITY_HIERARCHY = {
    1: "User explicit command with override flag",
    2: "User approval in interactive prompt",
    3: "Constitutional mandate (Articles I-V)",
    4: "VectorStore learned pattern (high confidence)",
    5: "Agent recommendation",
    6: "Default behavior",
}

# Rule: Lower number ALWAYS wins
# Example: User override (1) beats Constitution (3)
```

---

**Status**: Ready for implementation
**Next Steps**: Begin Phase 1 (Foundation)
