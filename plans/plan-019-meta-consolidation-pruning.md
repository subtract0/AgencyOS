# Implementation Plan: Meta-Level Consolidation & Elegant Pruning

**Plan ID**: `plan-019-meta-consolidation-pruning`
**Status**: `In Progress`
**Related Spec**: `spec-019-meta-consolidation-pruning.md`
**Author**: ChiefArchitectAgent + AuditorAgent
**Created**: 2025-10-02
**Estimated Duration**: 16 weeks (4 months)

---

## Overview

Execute SpaceX-level aggressive pruning through 6 phases over 16 weeks, achieving 40% code reduction, 60% token savings, and 3x speed improvement while maintaining 100% functional completeness.

---

## Phase 1: Git Tool Unification (Weeks 1-2) ⚡ **QUICK WIN**

### Current State Analysis

**3 Git Tools Identified:**
1. **`tools/git.py`** (153 lines):
   - Read-only operations: `status`, `diff`, `log`, `show`
   - Uses dulwich library (Python-native git)
   - Security: Command whitelisting, injection prevention
   - **Scope**: Basic git inspection only

2. **`tools/git_workflow.py`** (883 lines):
   - Full git workflow: branch, commit, push, PR creation
   - Uses subprocess + GitHub CLI (gh)
   - Classes: `GitWorkflowTool` (low-level), `GitWorkflowProtocol` (high-level)
   - Security: Pydantic validation, Result<T,E> pattern
   - **Scope**: Complete git workflow management

3. **`tools/git_workflow_tool.py`** (331 lines):
   - Agency Swarm wrapper around `git_workflow.py`
   - Thin adapter layer for BaseTool interface
   - Forwards operations to `GitWorkflowTool` and `GitWorkflowProtocol`
   - **Scope**: Agency integration only

**Overlap Analysis:**
- **100% overlap**: `git_workflow_tool.py` is pure wrapper (all functionality in `git_workflow.py`)
- **70% overlap**: `git.py` read operations duplicated in `git_workflow.py`'s status/diff methods
- **Result**: 70% of 1,367 lines = 967 lines redundant

### Feature Inventory

| Feature | git.py | git_workflow.py | git_workflow_tool.py | Unified API |
|---------|--------|-----------------|---------------------|-------------|
| **Read Operations** |
| git status | ✅ (dulwich) | ✅ (subprocess) | ✅ (wrapper) | `git.status()` |
| git diff | ✅ (dulwich) | ✅ (subprocess) | ✅ (wrapper) | `git.diff()` |
| git log | ✅ (dulwich) | ✅ (subprocess) | - | `git.log()` |
| git show | ✅ (dulwich) | - | - | `git.show()` |
| **Write Operations** |
| create branch | - | ✅ | ✅ (wrapper) | `git.create_branch()` |
| switch branch | - | ✅ | ✅ (wrapper) | `git.switch_branch()` |
| delete branch | - | ✅ | ✅ (wrapper) | `git.delete_branch()` |
| stage files | - | ✅ | ✅ (wrapper) | `git.stage()` |
| commit | - | ✅ | ✅ (wrapper) | `git.commit()` |
| push | - | ✅ | ✅ (wrapper) | `git.push()` |
| create PR | - | ✅ | ✅ (wrapper) | `git.create_pr()` |
| **High-Level Workflows** |
| start feature | - | ✅ | ✅ (wrapper) | `git.start_feature()` |
| cleanup after merge | - | ✅ | ✅ (wrapper) | `git.cleanup()` |

**Conclusion**: All functionality can be unified into single tool with clear API.

### Unified Git Tool Design

**File**: `tools/git_unified.py` (estimated 400 lines)

**Architecture - 3 Layers:**

```python
# Layer 1: Deterministic Core (90% of operations)
class GitCore:
    """Direct subprocess calls - no LLM needed."""

    def status(self) -> Result[str, GitError]:
        """git status - deterministic subprocess"""

    def diff(self, ref: str = "HEAD") -> Result[str, GitError]:
        """git diff - deterministic subprocess"""

    def create_branch(self, name: str) -> Result[BranchInfo, GitError]:
        """git checkout -b - deterministic"""

    def commit(self, message: str) -> Result[CommitInfo, GitError]:
        """git commit - deterministic"""

    def push(self, branch: str) -> Result[PushInfo, GitError]:
        """git push - deterministic"""

# Layer 2: Validated Operations (Pydantic models)
class GitUnified(BaseTool):
    """Agency Swarm integration with validation."""

    operation: GitOperation  # Enum: status, diff, create_branch, commit, etc.
    # ... operation-specific parameters

    def run(self) -> str:
        core = GitCore()
        result = core.execute(self.operation, **params)
        return self._format_result(result)

# Layer 3: LLM-Assisted Workflows (complex only)
class GitWorkflowAssisted:
    """LLM assistance for complex workflows only."""

    def resolve_conflicts(self, files: list[str]) -> Result[str, GitError]:
        """LLM helps resolve merge conflicts"""

    def optimize_commit_message(self, message: str) -> Result[str, GitError]:
        """LLM suggests improved commit message"""
```

**Migration Strategy:**

1. **Extract Core** (Day 1-2):
   - Create `GitCore` with all deterministic operations
   - Use subprocess (not dulwich) for compatibility
   - Pydantic models: `BranchInfo`, `CommitInfo`, `PushInfo`, `GitError`

2. **Build Unified Tool** (Day 3-5):
   - Create `GitUnified(BaseTool)` with all operations
   - Enum: `GitOperation` for operation types
   - Parameter validation via Pydantic

3. **Test Coverage** (Day 6-7):
   - Unit tests for all operations (30+ tests)
   - Integration tests for workflows
   - Edge cases: merge conflicts, detached HEAD, etc.

4. **Migrate Agent References** (Day 8-9):
   - Find all `from tools import Git` or `git_workflow`
   - Replace with `from tools import GitUnified`
   - Update invocations: `GitUnified(operation="status").run()`

5. **Add Deprecation** (Day 10):
   - Old tools redirect to `GitUnified` with warnings
   - 30-day deprecation period before removal

### Implementation Checklist

- [ ] Create `tools/git_unified.py` with GitCore, GitUnified, GitWorkflowAssisted
- [ ] Port all 15 operations from old tools with Result<T,E> pattern
- [ ] Add security validation (prevent injection, whitelist operations)
- [ ] Create Pydantic models: BranchInfo, CommitInfo, PushInfo, PRInfo, GitError
- [ ] Write 30+ unit tests covering all operations and edge cases
- [ ] Update all agent references (estimated 35 locations)
- [ ] Add deprecation warnings to git.py, git_workflow.py, git_workflow_tool.py
- [ ] Run full test suite (1,568 tests) - must pass 100%
- [ ] Measure speed improvement (expect 10x for deterministic ops)
- [ ] Document unified API in tools/README.md

### Success Criteria

- ✅ All 15 git operations functional in GitUnified
- ✅ 967 lines removed (70% reduction from 1,367 → 400)
- ✅ All 1,568 tests pass (zero regression)
- ✅ 10x speed improvement for simple ops (status, diff, branch)
- ✅ 80% token savings (no LLM calls for deterministic ops)
- ✅ Zero feature loss (validated by feature inventory)

---

## Phase 2: Agent Instruction Compression (Weeks 3-4) ⚡ **HIGHEST TOKEN SAVINGS**

### Current State Analysis

**Agent Instructions Inventory:**
```
.claude/agents/
├── auditor.md (200 lines)
├── chief_architect.md (300 lines)
├── code_agent.md (231 lines)
├── learning_agent.md (397 lines)
├── merger.md (373 lines)
├── planner.md (154 lines)
├── quality_enforcer.md (303 lines)
├── test_generator.md (252 lines)
├── toolsmith.md (378 lines)
└── work_completion_summary.md (150 lines)

TOTAL: ~2,738 lines

Agent directories (instructions.md):
agency_code_agent/instructions.md
planner_agent/instructions.md
... (duplicates of .claude/agents/)

ESTIMATED TOTAL: 3,000+ lines
```

**Redundancy Analysis:**

Common sections across ALL agents (60% redundancy):
1. **Constitutional Compliance** (identical in all 10 agents):
   - Article I: Complete Context Before Action
   - Article II: 100% Verification and Stability
   - Article III: Automated Merge Enforcement
   - Article IV: Continuous Learning and Improvement
   - Article V: Spec-Driven Development

2. **Quality Standards** (identical in all 10 agents):
   - TDD is Mandatory
   - Strict Typing Always
   - Validate All Inputs
   - Repository Pattern
   - Functional Error Handling
   - Focused Functions (<50 lines)
   - Document Public APIs

3. **Interaction Protocol** (similar in all 10 agents):
   - Receive task
   - Analyze requirements
   - Execute with quality checks
   - Verify results
   - Report completion

4. **Anti-patterns to Avoid** (mostly identical):
   - Using any or Dict[Any, Any]
   - Missing type annotations
   - Functions over 50 lines
   - etc.

**Unique Content Per Agent** (40%):
- Role description (unique)
- Core competencies (unique)
- Agent-specific responsibilities (unique)
- Specialized tools (unique)
- Domain-specific patterns (unique)

### Unified Instruction Design

**Core Template** (`shared/AGENT_INSTRUCTION_CORE.md` - 100 lines):

```markdown
# {{AGENT_NAME}} Agent

## Role
{{AGENT_ROLE}}

## Core Competencies
{{AGENT_COMPETENCIES}}

## Responsibilities
{{AGENT_RESPONSIBILITIES}}

## Constitutional Compliance (SHARED)

### Article I: Complete Context Before Action
[Standard text - identical for all agents]

### Article II: 100% Verification and Stability
[Standard text - identical for all agents]

### Article III: Automated Merge Enforcement
[Standard text - identical for all agents]

### Article IV: Continuous Learning and Improvement
[Standard text - identical for all agents]

### Article V: Spec-Driven Development
[Standard text - identical for all agents]

## Quality Standards (SHARED)
[Standard checklist - identical for all agents]

## Interaction Protocol (SHARED)
[Standard workflow - identical for all agents]

## Anti-patterns to Avoid (SHARED)
[Standard list - identical for all agents]

## Agent-Specific Details
{{AGENT_SPECIFIC_CONTENT}}
```

**Agent Delta Example** (`.claude/agents/planner-delta.md` - 50 lines):

```markdown
# Planner Agent Delta (unique content only)

## Role
Expert software architect transforming specs into detailed implementation plans.

## Core Competencies
- System architecture design
- Task decomposition and breakdown
- Dependency analysis
- Risk assessment

## Responsibilities
1. Plan Generation: Analyze specs, break down into tasks, identify dependencies
2. Architecture Design: Define components, interfaces, data models
3. Risk Management: Identify blockers, propose mitigations

## Agent-Specific Tools
- TodoWrite: Task breakdown
- Read: Spec analysis
- Write: Plan creation

## Plan Structure
[Specific to Planner only - not shared]
```

**Instruction Loader** (`shared/instruction_loader.py`):

```python
from pathlib import Path
from typing import Dict

def load_agent_instruction(agent_name: str) -> str:
    """
    Load agent instruction by composing core template + agent delta.

    Args:
        agent_name: Agent name (e.g., "planner", "coder", "auditor")

    Returns:
        Complete instruction text with variables substituted
    """
    # Load core template
    core_path = Path("shared/AGENT_INSTRUCTION_CORE.md")
    core_template = core_path.read_text()

    # Load agent delta
    delta_path = Path(f".claude/agents/{agent_name}-delta.md")
    delta = delta_path.read_text()

    # Parse delta for variable values
    variables = parse_delta_variables(delta)

    # Substitute variables in core template
    instruction = core_template
    for key, value in variables.items():
        instruction = instruction.replace(f"{{{{{'{'}{key}}}}}}}", value)

    # Append agent-specific content
    instruction += "\n\n" + delta.get("agent_specific_content", "")

    return instruction
```

### Migration Strategy

1. **Extract Common Patterns** (Day 1-2):
   - Analyze all 10 agent instructions
   - Identify 100% identical sections (constitutional, quality, anti-patterns)
   - Extract to `shared/AGENT_INSTRUCTION_CORE.md`

2. **Create Core Template** (Day 3):
   - Build template with {{VARIABLE}} placeholders
   - Add standard sections (constitutional, quality, interaction)
   - Validate template structure

3. **Compress Each Agent** (Day 4-8):
   - **One agent per day**: Extract unique delta content
   - Create `.claude/agents/{agent}-delta.md` files
   - Validate compressed instruction produces identical output
   - A/B test: original vs. compressed (must be behaviorally identical)

4. **Implement Loader** (Day 9):
   - Create `shared/instruction_loader.py`
   - Add variable substitution logic
   - Cache loaded instructions (avoid re-parsing)

5. **Update Agent Initialization** (Day 10):
   - Modify agent creation to use `load_agent_instruction()`
   - Test each agent with compressed instructions
   - Validate zero behavioral change

### Implementation Checklist

- [ ] Analyze all 10 agent instructions, create redundancy map
- [ ] Extract common sections to `shared/AGENT_INSTRUCTION_CORE.md` (100 lines)
- [ ] Create 10 agent delta files (50 lines each = 500 lines total)
- [ ] Implement `shared/instruction_loader.py` with caching
- [ ] A/B test each agent: original vs. compressed (must be identical)
- [ ] Update agent initialization to use loader
- [ ] Run full test suite (1,568 tests) - must pass 100%
- [ ] Measure token savings per agent invocation
- [ ] Document compression approach in docs/

### Success Criteria

- ✅ 2,000 lines removed (66% reduction from 3,000 → 1,000)
- ✅ 60% token savings per agent invocation (load delta not full)
- ✅ All agents maintain identical behavior (A/B tested)
- ✅ All 1,568 tests pass (zero regression)
- ✅ Single edit to core propagates to all agents
- ✅ Agent differences highlighted in deltas (improved clarity)

---

## Phase 3: Trinity Protocol Production-ization (Weeks 5-8) 🔥 **BIGGEST CODE REDUCTION**

### Current State Analysis

**Trinity Protocol Files** (47 files, 18,914 lines):

**Production-Ready Modules** (keep, optimize):
- `executor_agent.py` (execution coordinator)
- `architect_agent.py` (project architect)
- `witness_agent.py` (ambient monitoring)
- `cost_tracker.py` (budget tracking)
- `cost_dashboard.py` (cost visualization)
- `foundation_verifier.py` (CI/tests validation)
- `hitl.py` (human-in-the-loop protocol)
- `preference_learning.py` (user preference adaptation)
- `pattern_detector.py` (behavioral pattern recognition)

**Experimental/Prototype** (move to `/experimental/`):
- `audio_capture.py` (microphone capture - not production-critical)
- `ambient_listener_service.py` (always-on listening - privacy concerns)
- `whisper_transcriber.py` (transcription - requires whisper.cpp)
- `witness_ambient_mode.py` (ambient witness - experimental)

**Demo Files** (consolidate to `/demos/`):
- `demo_integration.py`
- `demo_complete_trinity.py`
- `demo_hitl.py`
- `demo_architect.py`
- `demo_preference_learning.py`
- `test_architect_simple.py`
- `run_8h_ui_test.py`
- `run_24h_test.py`
- `verify_cost_tracking.py`

**Reusable Components** (extract to `/shared/`):
- Cost tracking system (used across multiple agents)
- HITL protocol (generic pattern, not Trinity-specific)
- Preference learning (generic user adaptation)
- Pattern detection (generic behavioral analysis)

### Consolidation Strategy

**New Structure:**

```
trinity_protocol/
├── core/                      # Production modules (~5,000 lines)
│   ├── __init__.py
│   ├── executor.py           # Production executor
│   ├── architect.py          # Production architect
│   ├── witness.py            # Production witness (patterns only)
│   ├── orchestrator.py       # Trinity orchestration
│   └── models/               # Data models
│       ├── project.py
│       ├── patterns.py
│       └── preferences.py
├── experimental/             # Prototype modules (~3,500 lines)
│   ├── __init__.py
│   ├── audio_capture.py     # Audio capture (experimental)
│   ├── ambient_listener.py  # Ambient listening (experimental)
│   ├── whisper_transcriber.py
│   └── witness_ambient.py
├── demos/                    # Consolidated demos (~1,000 lines)
│   ├── demo_complete.py     # Main demo (consolidates 5 demos)
│   ├── demo_hitl.py         # HITL demo
│   └── demo_preferences.py  # Preference demo
└── README.md                # Production vs. experimental guide

shared/                       # Extracted reusable (~2,000 lines)
├── cost_tracker.py          # Generic cost tracking
├── hitl_protocol.py         # Generic HITL pattern
├── preference_learning.py   # Generic preference engine
└── pattern_detector.py      # Generic pattern detection
```

**Before**: 18,914 lines
**After**: 5,000 (core) + 3,500 (experimental) + 1,000 (demos) + 2,000 (shared) = **11,500 lines**
**Reduction**: 7,414 lines (39%) + clarity of separation

### Implementation Strategy

**Week 5: Audit & Mapping**
- [ ] Audit all 47 Trinity files
- [ ] Map dependencies (which files depend on which)
- [ ] Categorize: production / experimental / demo / reusable
- [ ] Create extraction plan for reusable components

**Week 6: Extract Reusable Components**
- [ ] Extract `shared/cost_tracker.py` with clean API
- [ ] Extract `shared/hitl_protocol.py` with generic interface
- [ ] Extract `shared/preference_learning.py` with pluggable backend
- [ ] Extract `shared/pattern_detector.py` with configurable patterns
- [ ] Update Trinity modules to import from shared/
- [ ] Run tests - ensure zero regression

**Week 7: Reorganize Production vs. Experimental**
- [ ] Create `trinity_protocol/core/` directory
- [ ] Move production modules with optimization:
  - `executor_agent.py` → `core/executor.py` (optimize, reduce size)
  - `architect_agent.py` → `core/architect.py` (optimize, reduce size)
  - `witness_agent.py` → `core/witness.py` (patterns only, remove ambient)
- [ ] Create `trinity_protocol/experimental/` directory
- [ ] Move experimental modules as-is (rapid iteration, less optimization)
- [ ] Update imports across codebase
- [ ] Run tests - ensure zero regression

**Week 8: Consolidate Demos & Documentation**
- [ ] Consolidate 10 demo files into 3:
  - `demos/demo_complete.py` (main Trinity demo)
  - `demos/demo_hitl.py` (HITL workflow demo)
  - `demos/demo_preferences.py` (preference learning demo)
- [ ] Create `trinity_protocol/README.md`:
  - Production modules (tested, stable, documented)
  - Experimental modules (rapid iteration, may change)
  - Upgrade path: experimental → production checklist
- [ ] Remove redundant test files (`test_architect_simple.py`, etc.)
- [ ] Update documentation to reflect new structure
- [ ] Run full test suite - ensure zero regression

### Implementation Checklist

- [ ] Complete dependency mapping for all 47 Trinity files
- [ ] Extract 4 reusable components to shared/ with tests
- [ ] Reorganize to core/ (5,000 lines) + experimental/ (3,500 lines)
- [ ] Consolidate 10 demos into 3 (remove duplication)
- [ ] Update all imports across codebase (search for "trinity_protocol")
- [ ] Create Trinity README with production/experimental guide
- [ ] Run full test suite (1,568 tests) - must pass 100%
- [ ] Measure code reduction and clarity improvement

### Success Criteria

- ✅ 7,414 lines removed (39% reduction from 18,914 → 11,500)
- ✅ Clear separation: production (core/) vs. experimental vs. demos
- ✅ 4 reusable components benefit all agents (cost, HITL, preference, pattern)
- ✅ All 1,568 tests pass (zero regression)
- ✅ Production modules: 100% test coverage, type-safe, documented
- ✅ Experimental modules: documented as experimental, upgrade path defined

---

## Phase 4: Tool Smart Caching & Determinism (Weeks 9-12) 🚀 **HIGHEST SPEED & TOKEN SAVINGS**

### Current State Analysis

**Tools Categorized by LLM Usage:**

**Pure Deterministic** (should NEVER call LLM):
- File ops: `read.py`, `write.py`, `edit.py`, `multi_edit.py`, `glob.py`, `grep.py`
- Git ops: `git_unified.py` (post Phase 1)
- Utility: `ls.py`, `notebook_read.py`, `notebook_edit.py`
- **Current**: Some may call LLM unnecessarily
- **Target**: 100% deterministic, <100ms execution

**Hybrid** (deterministic path + LLM fallback):
- Type checking: Run mypy deterministically, LLM only for fix generation
- Code analysis: AST parsing deterministic, LLM for complex insights
- Pattern analysis: Pattern matching deterministic, LLM for novel patterns
- **Current**: Call LLM for everything
- **Target**: 90% deterministic path, 10% LLM fallback

**LLM-Required** (complex, can't be deterministic):
- Code generation: `document_generator.py`
- Analysis: Deep code understanding, ADR creation
- Planning: Spec/plan generation
- **Current**: LLM every time (correct)
- **Target**: Add caching, optimize prompts

### Deterministic Optimization Strategy

**Week 9-10: Implement Deterministic Paths**

1. **Type Checking Tool** (currently hybrid):
   ```python
   # BEFORE: Calls LLM for every type check
   def check_types(file_path: str) -> Result[TypeIssues, Error]:
       # LLM analyzes file and reports type issues
       issues = call_llm(f"Check types in {file_path}")
       return Ok(issues)

   # AFTER: Run mypy deterministically, LLM only for fixes
   def check_types(file_path: str) -> Result[TypeIssues, Error]:
       # Run mypy directly (deterministic, <1 second)
       result = subprocess.run(["mypy", file_path], capture_output=True)
       issues = parse_mypy_output(result.stdout)  # Deterministic parsing

       if issues.count == 0:
           return Ok(TypeIssues(issues=[], count=0))

       # LLM only for fix generation (if requested)
       return Ok(TypeIssues(issues=issues, count=len(issues)))
   ```

2. **Git Status Parsing** (currently may use LLM):
   ```python
   # BEFORE: May call LLM to interpret git status
   def git_status() -> Result[GitStatus, Error]:
       status_text = call_llm("Run git status and parse")
       return Ok(parse_status(status_text))

   # AFTER: Direct subprocess + deterministic parsing
   def git_status() -> Result[GitStatus, Error]:
       result = subprocess.run(["git", "status", "--porcelain"], capture_output=True)
       status = parse_porcelain_status(result.stdout)  # Deterministic
       return Ok(status)
   ```

3. **File Validation** (should be deterministic):
   ```python
   # BEFORE: May call LLM to validate file
   def validate_file(file_path: str) -> Result[bool, Error]:
       validation = call_llm(f"Validate {file_path} exists and is readable")
       return Ok(validation.is_valid)

   # AFTER: Direct filesystem check
   def validate_file(file_path: str) -> Result[bool, Error]:
       path = Path(file_path)
       is_valid = path.exists() and path.is_file() and os.access(path, os.R_OK)
       return Ok(is_valid)
   ```

**Week 11: Implement Smart Caching**

**Cache Architecture:**

```python
# shared/tool_cache.py

from typing import Any, Optional, Callable
from functools import wraps
import hashlib
import time

class ToolCache:
    """Smart LRU cache for tool operations with invalidation."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.cache: dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def get_cache_key(self, operation: str, **params) -> str:
        """Generate cache key from operation + parameters."""
        param_str = str(sorted(params.items()))
        key_str = f"{operation}:{param_str}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get cached result if fresh."""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if time.time() - entry.timestamp > self.ttl_seconds:
            del self.cache[key]  # Expired
            return None

        return entry.result

    def set(self, key: str, result: Any):
        """Cache result with LRU eviction."""
        if len(self.cache) >= self.max_size:
            # Evict oldest entry (simple LRU)
            oldest_key = min(self.cache, key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest_key]

        self.cache[key] = CacheEntry(result=result, timestamp=time.time())

    def invalidate_file(self, file_path: str):
        """Invalidate cache entries for specific file."""
        keys_to_delete = [k for k in self.cache if file_path in str(k)]
        for key in keys_to_delete:
            del self.cache[key]

# Global cache instance
_cache = ToolCache()

def with_cache(ttl_seconds: int = 300):
    """Decorator for caching tool operations."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _cache.get_cache_key(func.__name__, args=args, kwargs=kwargs)

            # Check cache
            cached = _cache.get(cache_key)
            if cached is not None:
                return cached  # Cache hit!

            # Cache miss - execute function
            result = func(*args, **kwargs)

            # Cache result
            _cache.set(cache_key, result)

            return result
        return wrapper
    return decorator

# Usage example:
@with_cache(ttl_seconds=5)  # Cache git status for 5 seconds
def git_status() -> Result[GitStatus, Error]:
    # Expensive operation (only executed on cache miss)
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True)
    return Ok(parse_porcelain_status(result.stdout))
```

**Cache Invalidation Strategy:**
- **File modification**: Invalidate on file write/edit (monitor mtime)
- **Git commit**: Invalidate all git caches on commit (SHA changed)
- **TTL**: Short TTLs (5-300 seconds) for safety
- **Explicit clear**: `cache.clear()` command for agents

**Week 12: Measure & Optimize Hot Paths**

1. **Instrument All Tool Calls:**
   ```python
   # shared/telemetry.py

   def instrument_tool(tool_name: str, operation: str):
       """Decorator to measure tool execution time."""
       def decorator(func):
           @wraps(func)
           def wrapper(*args, **kwargs):
               start = time.time()
               result = func(*args, **kwargs)
               duration = time.time() - start

               # Log to telemetry
               log_tool_execution(
                   tool=tool_name,
                   operation=operation,
                   duration_ms=duration * 1000,
                   cached=kwargs.get("_from_cache", False)
               )

               return result
           return wrapper
       return decorator
   ```

2. **Identify Top 10 Hot Paths:**
   - Run telemetry for 1 week
   - Analyze: which tools called most frequently?
   - Prioritize optimization: optimize top 80% of calls

3. **Optimize Top 10:**
   - Add deterministic paths
   - Add caching where appropriate
   - Reduce unnecessary file I/O
   - Batch operations where possible

### Implementation Checklist

- [ ] Categorize all 46 tools: pure deterministic / hybrid / LLM-required
- [ ] Implement deterministic paths for hybrid tools (type checking, git parsing, file validation)
- [ ] Create `shared/tool_cache.py` with LRU cache + invalidation
- [ ] Add `@with_cache` decorator to frequently-called tools
- [ ] Implement cache invalidation (file mtime, git SHA monitoring)
- [ ] Add telemetry instrumentation to all tool calls
- [ ] Run telemetry for 1 week, identify top 10 hot paths
- [ ] Optimize top 10 tools for speed and caching
- [ ] Run full test suite (1,568 tests) - must pass 100%
- [ ] Measure speed improvement and token savings

### Success Criteria

- ✅ 90% of tool operations deterministic (no LLM calls)
- ✅ 10x speed improvement for deterministic ops (2-5s → 200ms)
- ✅ 80%+ cache hit rate for repeated operations (measured over 1 week)
- ✅ 70% token savings (90% of operations no longer call LLM)
- ✅ 70% cost reduction (measured over 1 month)
- ✅ All 1,568 tests pass (zero regression)

---

## Phase 5: Test Reorganization (Weeks 13-14) 📊 **DEVELOPER EXPERIENCE**

### Current State Analysis

**Test Files: 2,069 total**
- **139 test files** in root `tests/` directory
- No clear categorization (unit vs. integration vs. e2e)
- Test fixtures duplicated across files
- Slow: 2+ minutes to run all tests

**Example of Current Chaos:**
```
tests/
├── test_agency_code_agent.py
├── test_auditor_agent.py
├── test_chief_architect_agent.py
├── test_constitutional_compliance.py
├── test_git.py
├── test_git_workflow.py
├── test_learning_agent.py
├── test_memory.py
├── test_planner_agent.py
├── test_quality_enforcer_agent.py
├── test_self_healing.py
├── test_tools.py
├── test_vectorstore.py
├── ... (126 more files)
```

### Target Structure

```
tests/
├── unit/                     # Fast, isolated tests (<30 seconds)
│   ├── agents/
│   │   ├── test_planner.py
│   │   ├── test_coder.py
│   │   └── ...
│   ├── tools/
│   │   ├── test_git_unified.py
│   │   ├── test_file_ops.py
│   │   └── ...
│   └── shared/
│       ├── test_memory.py
│       ├── test_result.py
│       └── ...
├── integration/              # Cross-component tests (1-2 minutes)
│   ├── test_agent_workflows.py
│   ├── test_git_workflow.py
│   ├── test_healing_workflow.py
│   └── ...
├── e2e/                      # Full workflows (2-5 minutes)
│   ├── test_spec_to_deploy.py
│   ├── test_autonomous_healing.py
│   └── ...
├── benchmark/                # Performance tests (optional)
│   ├── test_vectorstore_perf.py
│   ├── test_cache_perf.py
│   └── ...
├── fixtures/                 # Shared test data
│   ├── conftest.py          # Pytest fixtures
│   ├── sample_files/
│   ├── mock_agents/
│   └── test_data/
└── README.md                # Test organization guide
```

### Reorganization Strategy

**Week 13: Categorize & Move**

1. **Analyze Each Test File** (Day 1-2):
   - Identify test type: unit, integration, e2e, or benchmark
   - Mark for categorization
   - Identify shared fixtures

2. **Extract Shared Fixtures** (Day 3):
   - Create `tests/fixtures/conftest.py`
   - Move common fixtures:
     ```python
     # tests/fixtures/conftest.py

     import pytest
     from pathlib import Path

     @pytest.fixture
     def sample_file(tmp_path):
         """Create temporary sample file for testing."""
         file_path = tmp_path / "sample.py"
         file_path.write_text("def hello(): return 'world'")
         return file_path

     @pytest.fixture
     def mock_agent_context():
         """Mock AgentContext for testing."""
         from shared.agent_context import AgentContext
         from agency_memory import Memory
         return AgentContext(memory=Memory(), session_id="test_session")
     ```
   - Remove duplicate fixtures from individual test files

3. **Reorganize Files** (Day 4-5):
   - Create category directories: `unit/`, `integration/`, `e2e/`, `benchmark/`
   - Move test files to appropriate categories
   - Update imports (absolute imports: `from tests.fixtures import ...`)
   - Add pytest markers:
     ```python
     @pytest.mark.unit
     def test_git_status():
         ...

     @pytest.mark.integration
     def test_git_workflow():
         ...
     ```

**Week 14: Optimize & Document**

4. **Consolidate Related Tests** (Day 6-7):
   - Combine small related test files:
     - `test_git.py` + `test_git_workflow.py` → `test_git_unified.py`
     - Multiple agent test files → `tests/unit/agents/test_agents.py` (grouped by domain)
   - Maintain clear test organization (grouped by class or domain)

5. **Add Selective Execution** (Day 8-9):
   - Update pytest configuration:
     ```ini
     # pytest.ini

     [pytest]
     markers =
         unit: Fast unit tests (< 30 seconds)
         integration: Integration tests (1-2 minutes)
         e2e: End-to-end tests (2-5 minutes)
         benchmark: Performance benchmark tests (optional)

     # Default: run only unit tests
     addopts = -m "unit" --tb=short
     ```
   - Add test execution commands to `README.md`:
     ```bash
     # Fast feedback (unit tests only)
     pytest tests/unit  # <30 seconds

     # Comprehensive (unit + integration)
     pytest tests/unit tests/integration  # ~2 minutes

     # Full validation (all tests)
     pytest tests/  # ~5 minutes

     # Specific category
     pytest -m unit         # Unit tests only
     pytest -m integration  # Integration tests only
     pytest -m e2e          # E2E tests only
     ```

6. **Parallel Execution** (Day 10):
   - Enable pytest-xdist for parallel test execution:
     ```bash
     # Install
     pip install pytest-xdist

     # Run tests in parallel (4 workers)
     pytest -n 4 tests/unit  # 4x faster for independent tests
     ```

### Implementation Checklist

- [ ] Analyze all 2,069 test files, categorize: unit / integration / e2e / benchmark
- [ ] Create directory structure: tests/{unit,integration,e2e,benchmark,fixtures}/
- [ ] Extract shared fixtures to tests/fixtures/conftest.py (eliminate duplication)
- [ ] Move test files to appropriate categories (preserve all 1,568 tests)
- [ ] Add pytest markers (@pytest.mark.unit, etc.)
- [ ] Consolidate related test files (139 → ~100 files)
- [ ] Update pytest.ini for selective execution (default: unit tests only)
- [ ] Enable pytest-xdist for parallel execution
- [ ] Create tests/README.md with organization guide and execution commands
- [ ] Run all tests in all categories - ensure 1,568 tests still pass
- [ ] Measure unit test execution time (target: <30 seconds)

### Success Criteria

- ✅ Clear categorization: unit (<30s) / integration (~2min) / e2e (~5min)
- ✅ 30% reduction in fixture duplication (extracted to conftest.py)
- ✅ Unit tests run in <30 seconds (4x improvement)
- ✅ Parallel execution: 4x faster for unit tests (pytest-xdist)
- ✅ All 1,568 tests remain passing (zero loss)
- ✅ Developers can run fast unit tests for quick feedback

---

## Phase 6: LLM Call Optimization via Prompt Compression (Weeks 15-16) 💰 **FINAL TOKEN SQUEEZE**

### Current State Analysis

**Average Agent Prompt Structure:**
```
[System Prompt]               ~2,000 tokens
├── Agent role                ~200 tokens
├── Constitutional articles   ~800 tokens  (REDUNDANT - same for all agents)
├── Quality standards         ~400 tokens  (REDUNDANT - same for all agents)
├── Interaction protocol      ~300 tokens  (REDUNDANT - same for all agents)
└── Anti-patterns             ~300 tokens  (REDUNDANT - same for all agents)

[Task Context]                ~3,000 tokens
├── User request              ~500 tokens
├── File contents             ~2,000 tokens
└── Previous context          ~500 tokens

[Examples]                    ~3,000 tokens  (REDUNDANT - can be cached)
├── Code examples             ~1,500 tokens
├── Workflow examples         ~1,000 tokens
└── Error examples            ~500 tokens

TOTAL: ~8,000 tokens per invocation
```

**Redundancy Analysis:**
- **60% redundant across calls**: Constitutional, quality, anti-patterns repeated every time
- **Examples re-transmitted**: Same examples sent in every request
- **No prompt caching**: Anthropic supports caching, but not used

### Prompt Compression Strategy

**Week 15: Implement Compressed Prompts**

**1. System Prompt Externalization:**
```python
# shared/prompt_templates.py

SYSTEM_PROMPT_CORE = """
You are {{AGENT_NAME}}, an expert {{AGENT_ROLE}}.

Your core mission: {{AGENT_MISSION}}

## Constitutional Framework (Cached - loads once)
[Constitutional articles - ~800 tokens]

## Quality Standards (Cached - loads once)
[Quality standards - ~400 tokens]

## Interaction Protocol (Cached - loads once)
[Standard workflow - ~300 tokens]

## Anti-patterns (Cached - loads once)
[Anti-patterns list - ~300 tokens]

Total: ~2,000 tokens (cached via Anthropic caching)
"""

TASK_PROMPT_TEMPLATE = """
## Task
{{USER_REQUEST}}

## Context
{{RELEVANT_CONTEXT}}

Total: ~1,500 tokens (task-specific, not cached)
"""
```

**2. Anthropic Prompt Caching Integration:**
```python
# shared/llm_client.py

from anthropic import Anthropic

client = Anthropic()

def call_with_caching(agent_name: str, task: str, context: dict):
    """
    Call LLM with prompt caching to reduce token costs.

    System prompt + examples cached for 5 minutes.
    Only task-specific content transmitted each call.
    """
    # Load cached system prompt (transmitted once, then cached)
    system_prompt = load_system_prompt(agent_name)  # ~2,000 tokens (cached)

    # Load cached examples (transmitted once, then cached)
    examples = load_examples(agent_name)  # ~3,000 tokens (cached)

    # Compose task prompt (transmitted every call)
    task_prompt = TASK_PROMPT_TEMPLATE.format(
        USER_REQUEST=task,
        RELEVANT_CONTEXT=context
    )  # ~1,500 tokens (not cached)

    # Call with caching
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}  # Cache for 5 minutes
            },
            {
                "type": "text",
                "text": examples,
                "cache_control": {"type": "ephemeral"}  # Cache for 5 minutes
            }
        ],
        messages=[
            {"role": "user", "content": task_prompt}
        ]
    )

    return response.content[0].text

# Token usage:
# First call: 2,000 (system) + 3,000 (examples) + 1,500 (task) = 6,500 tokens
# Subsequent calls (within 5 min): 1,500 tokens (60% savings!)
```

**3. Example Externalization:**
```python
# shared/prompt_examples/
# ├── planner_examples.md      (~1,500 tokens)
# ├── coder_examples.md        (~1,500 tokens)
# ├── auditor_examples.md      (~1,500 tokens)
# └── ...

# Load on-demand and cache
def load_examples(agent_name: str) -> str:
    path = Path(f"shared/prompt_examples/{agent_name}_examples.md")
    return path.read_text()
```

**Week 16: A/B Testing & Validation**

**4. A/B Test Compressed vs. Original:**
```python
# tests/integration/test_prompt_compression.py

def test_compressed_prompts_identical_output():
    """Validate compressed prompts produce identical output to originals."""

    test_tasks = [
        "Create a plan for implementing user authentication",
        "Analyze this code for type safety issues",
        "Generate tests for this function"
    ]

    for task in test_tasks:
        # Original prompt (8,000 tokens)
        original_response = call_with_original_prompt(task)

        # Compressed prompt (3,200 tokens on first call, 1,500 on subsequent)
        compressed_response = call_with_compressed_prompt(task)

        # Validate identical output (semantic similarity > 95%)
        similarity = calculate_similarity(original_response, compressed_response)
        assert similarity > 0.95, f"Compressed prompt altered output (similarity: {similarity})"

def test_prompt_caching_works():
    """Validate Anthropic caching reduces token usage."""

    # First call (cache miss)
    metrics1 = call_with_caching("planner", "Create a plan")
    assert metrics1.input_tokens == 6500  # Full prompt

    # Second call within 5 min (cache hit)
    metrics2 = call_with_caching("planner", "Create another plan")
    assert metrics2.input_tokens == 1500  # Only task prompt
    assert metrics2.cache_hit == True

    # Token savings: (6500 - 1500) / 6500 = 77% savings!
```

**5. Measure Cost Savings:**
```python
# Instrument all LLM calls with cost tracking

def track_llm_cost(agent: str, input_tokens: int, output_tokens: int, cached: bool):
    # Cost per 1M tokens (Sonnet 4.5)
    input_cost = 3.00 / 1_000_000  # $3 per 1M input tokens
    output_cost = 15.00 / 1_000_000  # $15 per 1M output tokens
    cache_write_cost = 3.75 / 1_000_000  # $3.75 per 1M cache write
    cache_read_cost = 0.30 / 1_000_000  # $0.30 per 1M cache read (90% discount!)

    if cached:
        # Cache hit: only pay cache read + output
        cost = (input_tokens * cache_read_cost) + (output_tokens * output_cost)
    else:
        # Cache miss: pay full input + cache write + output
        cost = (input_tokens * input_cost) + (input_tokens * cache_write_cost) + (output_tokens * output_cost)

    log_cost(agent, cost, input_tokens, output_tokens, cached)
    return cost

# Expected savings:
# - Before compression: 8,000 input tokens × $3/1M = $0.024 per call
# - After compression (cache hit): 1,500 input tokens × $0.30/1M = $0.0005 per call
# - Savings: 98% reduction in input token costs!
```

### Implementation Checklist

- [ ] Extract system prompts to `shared/prompt_templates.py` (2,000 tokens cached)
- [ ] Extract examples to `shared/prompt_examples/` (3,000 tokens cached)
- [ ] Implement `call_with_caching()` using Anthropic prompt caching API
- [ ] Update all agent invocations to use compressed prompts
- [ ] A/B test compressed vs. original prompts (must be >95% similar output)
- [ ] Instrument all LLM calls with cost tracking
- [ ] Run for 1 week, measure token savings and cost reduction
- [ ] Validate: compressed prompts maintain quality (agent tests pass)
- [ ] Document prompt compression approach in docs/

### Success Criteria

- ✅ 60% token reduction per agent invocation (8,000 → 3,200 first call, 1,500 subsequent)
- ✅ 98% cost reduction for cached calls (input tokens)
- ✅ 40% faster response time (less context to process)
- ✅ Identical output quality (>95% similarity in A/B testing)
- ✅ All 1,568 tests pass with compressed prompts
- ✅ Cost savings measured over 1 month (target: 60%+ reduction)

---

## Final Metrics & Validation

### Pre-Consolidation Baseline
| Metric | Value |
|--------|-------|
| Total Code Lines | 33,000+ |
| Git Tools | 3 (1,367 lines) |
| Agent Instructions | 3,000 lines |
| Trinity Protocol | 18,914 lines |
| Documentation | 9,932 files |
| Test Files | 2,069 |
| Avg LLM Tokens/Call | 8,000 tokens |
| Avg Tool Execution | 2-5 seconds |
| Monthly LLM Cost | $Baseline |

### Post-Consolidation Targets
| Metric | Target | Improvement |
|--------|--------|-------------|
| Total Code Lines | <20,000 | **40% reduction** |
| Git Tools | 1 (400 lines) | **70% reduction** |
| Agent Instructions | 1,000 lines | **66% reduction** |
| Trinity Protocol | 11,500 lines | **39% reduction** |
| Documentation | ~4,000 files | **60% reduction** |
| Test Files | ~100 (organized) | Clarity |
| Avg LLM Tokens/Call | 3,200 (first), 1,500 (cached) | **60-80% reduction** |
| Avg Tool Execution | 200ms (deterministic) | **10x faster** |
| Monthly LLM Cost | 70% reduction | **70% savings** |

### Validation Checklist

After each phase:
- [ ] All 1,568 tests pass (100% pass rate)
- [ ] Feature inventory: zero feature loss
- [ ] A/B testing: compressed == original (>95% similarity)
- [ ] Performance metrics: speed/token/cost improvements measured
- [ ] Documentation updated
- [ ] Code reviewed by ChiefArchitectAgent
- [ ] Constitutional compliance verified

---

## Risk Mitigation

### Rollback Plan
Each phase has isolated git branch:
- `consolidation/phase1-git-unification`
- `consolidation/phase2-instruction-compression`
- `consolidation/phase3-trinity-production`
- `consolidation/phase4-tool-determinism`
- `consolidation/phase5-test-reorganization`
- `consolidation/phase6-prompt-compression`

If any phase fails validation:
1. Rollback git branch
2. Analyze failure root cause
3. Refine approach
4. Retry with fixes

### Quality Gates
Each phase must pass:
1. **Test Gate**: All 1,568 tests pass
2. **Feature Gate**: Feature inventory shows zero loss
3. **Performance Gate**: Speed/token/cost metrics meet targets
4. **Review Gate**: Technical review by ChiefArchitectAgent

No phase proceeds without passing all 4 gates.

---

## Timeline

| Week | Phase | Deliverable | Validation |
|------|-------|-------------|------------|
| 1-2 | Phase 1 | Git Tool Unification (400 lines) | Tests pass, 10x speed |
| 3-4 | Phase 2 | Agent Instruction Compression (1,000 lines) | Tests pass, 60% tokens saved |
| 5-8 | Phase 3 | Trinity Production-ization (11,500 lines) | Tests pass, clear separation |
| 9-12 | Phase 4 | Tool Determinism & Caching | Tests pass, 10x speed, 70% tokens saved |
| 13-14 | Phase 5 | Test Reorganization (~100 files) | Tests pass, <30s unit tests |
| 15-16 | Phase 6 | Prompt Compression (3,200→1,500 tokens) | Tests pass, 60% tokens saved |

**Total Duration**: 16 weeks (4 months)
**Total Effort**: ~320 hours (20 hours/week)

---

*"Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away." — Antoine de Saint-Exupéry*

**Let's execute! Starting with Phase 1: Git Tool Unification.** 🚀
