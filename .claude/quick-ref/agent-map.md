# Agent Quick Reference Map

**Fast lookup of agent capabilities and when to use them**

## Core Agents (Production)

### ChiefArchitect
**Purpose**: Strategic oversight, ADR creation, self-directed tasks
**Model**: GPT-5 (high reasoning)
**Use When**: Architecture decisions, strategic planning, ADR needed
**Location**: `chief_architect_agent/`

### Planner
**Purpose**: Spec-kit methodology (Goals/Personas/Criteria), plan.md generation
**Model**: GPT-5 (high reasoning, o3-capable)
**Use When**: Feature planning, spec → plan transformation
**Location**: `planner_agent/`

### AgencyCodeAgent
**Purpose**: Primary development, TDD-first, Result<T,E> pattern
**Model**: GPT-5 (medium reasoning)
**Use When**: Implementation, coding, refactoring
**Location**: `agency_code_agent/`

### QualityEnforcer
**Purpose**: Constitutional compliance, autonomous healing orchestration
**Model**: GPT-5 (high reasoning)
**Use When**: Quality gates, healing needed, compliance checks
**Location**: `quality_enforcer_agent/`

### Auditor
**Purpose**: NECESSARY pattern quality analysis, READ-ONLY mode
**Model**: GPT-5 (high reasoning)
**Use When**: Code quality assessment, violation detection
**Location**: `auditor_agent/`

### TestGenerator
**Purpose**: NECESSARY-compliant test generation, AAA pattern
**Model**: GPT-5 (medium reasoning)
**Use When**: Test creation, coverage improvement
**Location**: `test_generator_agent/`

### LearningAgent
**Purpose**: Session transcript analysis, VectorStore consolidation
**Model**: GPT-5 (high reasoning)
**Use When**: Pattern extraction, learning consolidation
**Location**: `learning_agent/`

### Merger
**Purpose**: Branch → commit → push → PR automation
**Model**: GPT-5 (medium reasoning)
**Use When**: Git operations, PR creation, green main enforcement
**Location**: `merger_agent/`

### Toolsmith
**Purpose**: Tool development, API design, TDD methodology
**Model**: GPT-5 (medium reasoning)
**Use When**: New tool creation, tool enhancement
**Location**: `toolsmith_agent/`

### WorkCompletionSummary
**Purpose**: Task summaries (cost-efficient)
**Model**: GPT-5-mini (low reasoning)
**Use When**: Summarizing completed work
**Location**: `work_completion_summary_agent/`

## Deprecated Agents

### UIDevAgent
**Status**: DEPRECATED
**Location**: `ui_development_agent/`
**Reason**: No longer maintained

---

## Communication Flows

```
ChiefArchitect ──┬→ Auditor
                 ├→ Learning
                 ├→ Planner
                 ├→ Toolsmith
                 └→ QualityEnforcer

Planner ↔ Coder (bidirectional)

Auditor → TestGenerator → Coder

QualityEnforcer ↔ Coder, TestGenerator

Coder/Planner/Merger → Summary
```

---

**Total Agents**: 10 production + 1 deprecated
