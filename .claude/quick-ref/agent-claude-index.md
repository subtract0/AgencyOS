# Agent-Specific CLAUDE.md Index

Quick reference to all agent-specific CLAUDE.md files for fast navigation.

## Purpose

Each agent has its own CLAUDE.md file located in its directory with:
- Role & identity (purpose, model tier, complexity focus)
- When to use decision trees
- Tools & capabilities (allowed/prohibited)
- Dependencies & communication flows
- Constitutional requirements
- Common patterns with code examples
- Quick start examples (3-5 scenarios)
- Cross-references to ADRs and root CLAUDE.md
- Success metrics

## Agent CLAUDE.md Files

### Core Development Agents

1. **[AgencyCodeAgent](../../agency_code_agent/CLAUDE.md)**
   - **Role**: TDD-first implementation, Result patterns, type safety
   - **Model**: GPT-5 (medium reasoning)
   - **Complexity**: P2/P3 (implementation, refactoring, bug fixes)
   - **Key Features**: Tests before code, memory-aware execution, VectorStore integration

2. **[Planner](../../planner_agent/CLAUDE.md)**
   - **Role**: Spec-kit methodology, implementation plans, task breakdown
   - **Model**: GPT-5 (high reasoning, o3-capable)
   - **Complexity**: P1 (strategic planning)
   - **Key Features**: Goals/Non-Goals/Personas/Criteria, TodoWrite integration

3. **[Auditor](../../auditor_agent/CLAUDE.md)**
   - **Role**: NECESSARY pattern analysis, constitutional compliance, READ-ONLY
   - **Model**: GPT-5 (high reasoning)
   - **Complexity**: P1 (analysis)
   - **Key Features**: 9-category audit, JSON reports, pattern discovery

### Quality & Compliance Agents

4. **[QualityEnforcer](../../quality_enforcer_agent/CLAUDE.md)**
   - **Role**: Constitutional guardian, autonomous healing, quality gates
   - **Model**: GPT-5 (high reasoning)
   - **Complexity**: P1 (strategic oversight)
   - **Key Features**: All 5 articles + 10 laws enforcement, healing workflows, safety protocols

5. **[TestGenerator](../../test_generator_agent/CLAUDE.md)**
   - **Role**: NECESSARY-compliant test generation, AAA pattern
   - **Model**: GPT-5 (medium reasoning)
   - **Complexity**: P2 (test generation)
   - **Key Features**: TDD red phase verification, comprehensive test suites

### Architecture & Integration Agents

6. **[ChiefArchitect](../../chief_architect_agent/CLAUDE.md)**
   - **Role**: ADR creation, strategic oversight, technical governance
   - **Model**: GPT-5 (highest reasoning)
   - **Complexity**: P1 (architecture)
   - **Key Features**: Self-directed tasks, ADR management, long-term planning

7. **[Merger](../../merger_agent/CLAUDE.md)**
   - **Role**: Git workflow automation, PR creation, green main enforcement
   - **Model**: GPT-5 (medium reasoning)
   - **Complexity**: P2 (git operations)
   - **Key Features**: Branch → commit → push → PR, 100% test pass enforcement

### Support & Tooling Agents

8. **[LearningAgent](../../learning_agent/CLAUDE.md)**
   - **Role**: Session analysis, pattern extraction, VectorStore consolidation
   - **Model**: GPT-5 (high reasoning)
   - **Complexity**: P1 (pattern analysis)
   - **Key Features**: Article IV enforcement, cross-session learning

9. **[Toolsmith](../../toolsmith_agent/CLAUDE.md)**
   - **Role**: Tool development with TDD, API design
   - **Model**: GPT-5 (medium reasoning)
   - **Complexity**: P2 (tool development)
   - **Key Features**: Tests-first tool creation, strict typing

10. **[WorkCompletionSummary](../../work_completion_summary_agent/CLAUDE.md)**
    - **Role**: Cost-efficient task summaries
    - **Model**: GPT-5-mini (low reasoning)
    - **Complexity**: P3 (simple summarization)
    - **Key Features**: 3-5 sentence summaries, git log analysis

---

## Module & Infrastructure CLAUDE.md Files ⭐ NEW

### Core Infrastructure Modules

11. **[Trinity Protocol](../../trinity_protocol/CLAUDE.md)**
    - **Role**: Constitutional execution framework, adaptive routing, quality feedback
    - **Key Components**: HybridExecutor, AdaptiveModelRouter, QualityFeedbackCollector
    - **Innovations**: Leap 3/4/6/8 (96% cost reduction, 40-60% churn reduction)
    - **When to Use**: Building orchestrators, constitutional execution, quality learning

12. **[Orchestrator Tools](../../tools/orchestrator/CLAUDE.md)**
    - **Role**: PrimeA production hardening (slop immunity, budget guard, TDD validation)
    - **Key Components**: SlopGuardian, BudgetGuard, NECESSARYValidator, PRCreator, CompletionValidator
    - **Innovations**: Leap 6/7 (quality gates, test-driven autonomy, completion validation)
    - **When to Use**: Custom orchestrators, CI/CD quality gates, autonomous workflows

13. **[Shared Infrastructure](../../shared/CLAUDE.md)**
    - **Role**: Universal infrastructure (AgentContext, memory API, cost tracking, validation)
    - **Key Components**: AgentContext, AdaptiveModelRouter, CostTracker, ConstitutionalValidator, CheckpointManager
    - **Mandatory**: All agents depend on this module (AgentContext required)
    - **When to Use**: Building new agents, memory integration, cost tracking, compliance validation

14. **[Agency Memory](../../agency_memory/CLAUDE.md)**
    - **Role**: Three-tier memory architecture (Memory Tool, VectorStore, Session)
    - **Key Components**: VectorStore, EnhancedMemoryStore, Learning, MemoryCache, SwarmMemory
    - **Constitutional**: Article IV implementation (VectorStore integration mandatory)
    - **When to Use**: Pattern storage, cross-session learning, institutional memory

### Orchestrator Commands

15. **[PrimeA Orchestrator](../../.claude/agents/primea_orchestrator.md)**
    - **Command**: `/primeA [intent] [flags]`
    - **Role**: AGI-class autonomous development orchestrator (intent → production code)
    - **Key Features**: Two-stage workflow, TDD autonomy, completion validation, TRM-7M validation
    - **Flags**: `--two-stage`, `--graph`, `--plan-only`, `--visualize`, `--auto-pr`, `--no-pr`, `--force`
    - **When to Use**: Complex features (multi-agent), autonomous end-to-end workflow, spec approval workflow

---

## Quick Selection Guide

### I need to...

**Implement a feature:**
- Has spec/plan? → [AgencyCodeAgent](../../agency_code_agent/CLAUDE.md)
- No spec? → [Planner](../../planner_agent/CLAUDE.md) first

**Analyze code quality:**
- Read-only analysis? → [Auditor](../../auditor_agent/CLAUDE.md)
- Need automated fixes? → [QualityEnforcer](../../quality_enforcer_agent/CLAUDE.md)

**Work with tests:**
- Generate tests? → [TestGenerator](../../test_generator_agent/CLAUDE.md)
- Write tests manually (TDD)? → [AgencyCodeAgent](../../agency_code_agent/CLAUDE.md)

**Make architectural decisions:**
- Create ADR? → [ChiefArchitect](../../chief_architect_agent/CLAUDE.md)
- Create technical plan? → [Planner](../../planner_agent/CLAUDE.md)

**Integrate changes:**
- Create PR, git workflow? → [Merger](../../merger_agent/CLAUDE.md)
- Summary for stakeholders? → [WorkCompletionSummary](../../work_completion_summary_agent/CLAUDE.md)

**Create tools:**
- New tool development? → [Toolsmith](../../toolsmith_agent/CLAUDE.md)

**Extract learnings:**
- Post-session analysis? → [LearningAgent](../../learning_agent/CLAUDE.md)

## File Structure

### Agent CLAUDE.md Files (10 agents)
```
Agency/
├── agency_code_agent/CLAUDE.md          (395 lines, 12KB)
├── planner_agent/CLAUDE.md              (453 lines, 13KB)
├── auditor_agent/CLAUDE.md              (512 lines, 15KB)
├── quality_enforcer_agent/CLAUDE.md     (551 lines, 17KB)
├── chief_architect_agent/CLAUDE.md      (140 lines, 4KB)
├── test_generator_agent/CLAUDE.md       (213 lines, 6KB)
├── learning_agent/CLAUDE.md             (86 lines, 3KB)
├── merger_agent/CLAUDE.md               (112 lines, 3KB)
├── toolsmith_agent/CLAUDE.md            (115 lines, 3KB)
└── work_completion_summary_agent/CLAUDE.md (100 lines, 3KB)
```

### Module & Infrastructure CLAUDE.md Files ⭐ NEW (5 modules)
```
Agency/
├── trinity_protocol/CLAUDE.md           (12KB, ~3100 tokens)
├── tools/orchestrator/CLAUDE.md         (18KB, ~4500 tokens)
├── shared/CLAUDE.md                     (18KB, ~4600 tokens)
├── agency_memory/CLAUDE.md              (18KB, ~4500 tokens)
└── .claude/agents/primea_orchestrator.md (17KB, ~4300 tokens)
```

## Common Patterns Across All Agents

### 1. VectorStore Integration (Article IV)
All agents follow this pattern:
```python
# BEFORE action - Query learnings
patterns = context.search_memories(
    tags=["agent_type", "pattern", "success"],
    include_session=False
)

# AFTER success - Store learnings
context.store_memory(
    key=f"success_{task}_{uuid.uuid4()}",
    content={"pattern": pattern, "confidence": 0.9},
    tags=["agent_name", "success", "pattern"]
)
```

### 2. Result Pattern (ADR-010)
All agents use Result<T,E> for error handling:
```python
from shared.type_definitions.result import Result, Ok, Err

def operation(input: Input) -> Result[Output, Error]:
    if not valid(input):
        return Err(Error.INVALID_INPUT)
    return Ok(output)
```

### 3. Constitutional Compliance
All agents validate against:
- Article I: Complete context (no timeouts)
- Article II: 100% verification (tests pass)
- Article III: Automated enforcement (no overrides)
- Article IV: Continuous learning (VectorStore)
- Article V: Spec-driven development

## Success Metrics (Aggregate)

| Metric | Target | Actual |
|--------|--------|--------|
| **Agents Documented** | 10 | 10 ✅ |
| **Modules Documented** ⭐ NEW | 5 | 5 ✅ |
| **Total CLAUDE.md Files** | 15 | 15 ✅ |
| Template Compliance | 100% | 100% ✅ |
| Constitutional Compliance | 100% | 100% ✅ |
| Cross-References Complete | 100% | 100% ✅ |
| Token Budget Compliance | 100% | 100% ✅ |
| Documentation Scan Status | PASS | ✅ PASS (0 missing) |

**Documentation Coverage**:
- Agent CLAUDE.md: 10/10 (100%)
- Module CLAUDE.md: 5/5 (100%) ⭐ NEW
- Critical Directories: 15/15 (100%)
- Missing CLAUDE.md Issues: 0 (resolved)

---

**Last Updated**: 2025-10-15
**Version**: 2.0.0 (Module CLAUDE.md expansion)
**Maintained By**: Agency OS Core Team
