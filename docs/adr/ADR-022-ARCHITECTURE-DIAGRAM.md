# ADR-022: Autonomous Auditor - Architecture Diagrams

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS AUDITOR SYSTEM                         │
│                   (From 5/5 Stars → 6/5 Stars)                      │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Continuous      │
│  Auditor         │  ← Phase 4 (5/5 stars)
│  (M4 Pro Local)  │
└────────┬─────────┘
         │
         │ Scans codebase
         │ AST analysis
         │ Pattern detection
         ↓
┌────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDATION PIPELINE                          │
│                      (NEW: ADR-022)                                │
└────────────────────────────────────────────────────────────────────┘

   ┌────────────────────┐
   │  Issue Detection   │
   │  (AST + LLM)       │
   └─────────┬──────────┘
             │
             │ Issue object
             ↓
   ┌─────────────────────────────┐
   │  Auto-Fixability            │
   │  Classifier                 │
   │  • Trivial/Simple/Moderate  │
   │  • Confidence scoring       │
   │  • Learning query           │
   └──────────┬──────────────────┘
              │
              │ Classification metadata
              ↓
   ┌─────────────────────────────┐
   │  Fix Code Generator         │
   │  (qwen2.5-coder:32b)        │
   │  • LLM prompt               │
   │  • Patch generation         │
   │  • Validation code          │
   └──────────┬──────────────────┘
              │
              │ Generated fix
              ↓
   ┌─────────────────────────────┐
   │  Dependency Analyzer        │
   │  (AST import graph)         │
   │  • Inter-file deps          │
   │  • Fix ordering             │
   └──────────┬──────────────────┘
              │
              │ Dependency info
              ↓
   ┌─────────────────────────────┐
   │  Risk Scorer                │
   │  • Quantified risk (0.0-1.0)│
   │  • Risk factors             │
   │  • Rollback difficulty      │
   └──────────┬──────────────────┘
              │
              │ Risk assessment
              ↓
   ┌─────────────────────────────┐
   │  Enhanced Recommendation    │
   │  (Pydantic model)           │
   │  • auto_fixable: bool       │
   │  • fix_confidence: 0.85     │
   │  • risk_score: 0.12         │
   │  • generated_fix: patch     │
   │  • validation_plan          │
   │  • learning_metadata        │
   └──────────┬──────────────────┘
              │
              │ Write to markdown + JSON
              ↓
   ┌─────────────────────────────┐
   │  .output/recommendations/   │
   │  localM4_recommends_042.md  │
   │  + recommendation_042.json  │
   └──────────┬──────────────────┘
              │
              │
              ↓
┌────────────────────────────────────────────────────────────────────┐
│                  AUTONOMOUS FIXER SYSTEM                            │
│                      (Enhanced)                                     │
└────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────┐
   │  Recommendation Loader      │
   │  • Read markdown + JSON     │
   │  • Parse metadata           │
   │  • Priority sorting         │
   └──────────┬──────────────────┘
              │
              │ Sorted recommendations
              ↓
   ┌─────────────────────────────┐
   │  Autonomous Decision        │
   │  Engine                     │
   │                             │
   │  IF auto_fixable == True    │
   │  AND confidence >= 0.80     │
   │  AND risk_score < 0.30      │
   │  AND no violations          │
   │  THEN apply_autonomously()  │
   │  ELSE create_github_issue() │
   └──────────┬──────────────────┘
              │
              │ Decision: AUTO or MANUAL
              ↓
   ┌─────────────────────────────┐
   │  Autonomous Fix Applicator  │
   │  (AgencyOSAgent)          │
   │  • Read generated_fix.patch │
   │  • Apply patch              │
   │  • Run validation tests     │
   │  • Commit or rollback       │
   └──────────┬──────────────────┘
              │
              │ Fix result
              ↓
   ┌─────────────────────────────┐
   │  Validation & Rollback      │
   │  • Execute test_commands    │
   │  • Check success_criteria   │
   │  • Rollback on failure      │
   │  • Log telemetry            │
   └──────────┬──────────────────┘
              │
              │ Success/Failure
              ↓
   ┌─────────────────────────────┐
   │  Learning Storage           │
   │  (VectorStore)              │
   │  • Store success pattern    │
   │  • Update success_rate      │
   │  • Feed future confidence   │
   └─────────────────────────────┘
```

---

## Classification Flow

```
┌──────────────────────────────────────────────────────────────┐
│              AUTO-FIXABILITY CLASSIFICATION                   │
└──────────────────────────────────────────────────────────────┘

  Recommendation Input
         │
         ↓
  ┌──────────────────┐
  │  Analyze Scope   │
  │  • Lines changed │
  │  • Files affected│
  │  • Fix type      │
  └────────┬─────────┘
           │
           ↓
  ┌──────────────────────────────────────────────────────────┐
  │                    CLASSIFICATION RULES                   │
  └──────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────┐
  │  TRIVIAL (auto=True, confidence=0.95)                   │
  │  • Pure deletion (commented code, unused imports)       │
  │  • <5 lines affected                                    │
  │  • Single file                                          │
  │  • Zero behavior change                                 │
  │  Validation: Syntax-only                                │
  └──────────────────┬──────────────────────────────────────┘
                     │
                     ↓ (if not trivial)
  ┌─────────────────────────────────────────────────────────┐
  │  SIMPLE (auto=True, confidence=0.85)                    │
  │  • Single function edit                                 │
  │  • Extract 2-3 line helper                              │
  │  • Rename operation                                     │
  │  • 5-20 lines affected                                  │
  │  • Single file                                          │
  │  Validation: Unit tests                                 │
  └──────────────────┬──────────────────────────────────────┘
                     │
                     ↓ (if not simple)
  ┌─────────────────────────────────────────────────────────┐
  │  MODERATE (auto=False, confidence=0.65)                 │
  │  • Multi-function changes                               │
  │  • Split 80+ line function                              │
  │  • Refactor duplicates                                  │
  │  • 20-100 lines affected                                │
  │  • Single or multiple files                             │
  │  Validation: Integration tests                          │
  └──────────────────┬──────────────────────────────────────┘
                     │
                     ↓ (if not moderate)
  ┌─────────────────────────────────────────────────────────┐
  │  COMPLEX (auto=False, confidence=0.40)                  │
  │  • Architectural changes                                │
  │  • Multi-file refactors                                 │
  │  • Public API modifications                             │
  │  • >100 lines affected                                  │
  │  • Multiple files                                       │
  │  Validation: Full test suite                            │
  └──────────────────┬──────────────────────────────────────┘
                     │
                     ↓
  ┌─────────────────────────────────────────────────────────┐
  │  LEARNING BOOST                                         │
  │  Query VectorStore for similar fixes                    │
  │  If success_rate > 0.80:                                │
  │      confidence += 0.10                                 │
  └──────────────────┬──────────────────────────────────────┘
                     │
                     ↓
  ┌─────────────────────────────────────────────────────────┐
  │  OUTPUT: Enhanced Recommendation                        │
  │  • auto_fixable: bool                                   │
  │  • fix_confidence: 0.0-1.0                              │
  │  • fix_difficulty: enum                                 │
  │  • requires_review: bool                                │
  └─────────────────────────────────────────────────────────┘
```

---

## Risk Scoring Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    RISK SCORE CALCULATION                     │
└──────────────────────────────────────────────────────────────┘

  Recommendation Input
         │
         ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Boolean Risk Factors (checked via AST/heuristics)        │
  └───────────────────────────────────────────────────────────┘

  ┌────────────────────────┬─────────┐
  │  modifies_public_api   │  +0.25  │  ← Signature changes, API breaks
  ├────────────────────────┼─────────┤
  │  no_test_coverage      │  +0.20  │  ← No test file found
  ├────────────────────────┼─────────┤
  │  changes_core_logic    │  +0.15  │  ← Algorithm/validation changes
  ├────────────────────────┼─────────┤
  │  multi_file_impact     │  +0.15  │  ← >1 file affected
  ├────────────────────────┼─────────┤
  │  external_dependencies │  +0.10  │  ← Uses requests/openai/etc
  ├────────────────────────┼─────────┤
  │  database_changes      │  +0.10  │  ← Schema/migration keywords
  ├────────────────────────┼─────────┤
  │  affects_critical_path │  +0.05  │  ← agency.py, constitution.md
  └────────────────────────┴─────────┘

         │
         │ Sum risk factors
         ↓
  ┌───────────────────────────────────────────────────────────┐
  │  risk_score = min(1.0, sum(factors))                      │
  └───────────────┬───────────────────────────────────────────┘
                  │
                  ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Categorical Risk Level                                   │
  └───────────────────────────────────────────────────────────┘

  risk_score < 0.1  → ZERO     → Rollback: EASY
  risk_score < 0.3  → LOW      → Rollback: EASY
  risk_score < 0.6  → MEDIUM   → Rollback: MEDIUM
  risk_score < 0.8  → HIGH     → Rollback: MEDIUM
  risk_score >= 0.8 → CRITICAL → Rollback: HARD

         │
         ↓
  ┌───────────────────────────────────────────────────────────┐
  │  OUTPUT: RiskFactors                                      │
  │  • risk_score: 0.25 (example)                             │
  │  • risk_level: LOW                                        │
  │  • rollback_difficulty: EASY                              │
  │  • All boolean factors                                    │
  └───────────────────────────────────────────────────────────┘
```

---

## Autonomous Decision Flow

```
┌──────────────────────────────────────────────────────────────┐
│             AUTONOMOUS FIX DECISION ENGINE                    │
└──────────────────────────────────────────────────────────────┘

  Enhanced Recommendation
         │
         ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Safety Gate #1: Auto-Fixable?                            │
  │  recommendation.auto_fixable == True                      │
  └────────┬──────────────────────────────────────────────────┘
           │ YES
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Safety Gate #2: Sufficient Confidence?                   │
  │  recommendation.fix_confidence >= 0.80                    │
  └────────┬──────────────────────────────────────────────────┘
           │ YES
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Safety Gate #3: Acceptable Risk?                         │
  │  recommendation.risk_score < 0.30                         │
  └────────┬──────────────────────────────────────────────────┘
           │ YES
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Safety Gate #4: Constitutional Compliance?               │
  │  len(blocking_violations) == 0                            │
  └────────┬──────────────────────────────────────────────────┘
           │ YES
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Safety Gate #5: Validation Defined?                      │
  │  validation_strategy != MANUAL_REVIEW                     │
  └────────┬──────────────────────────────────────────────────┘
           │ YES
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  ✓ APPROVED FOR AUTONOMOUS FIX                            │
  └────────┬──────────────────────────────────────────────────┘
           │
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Apply Fix Autonomously                                   │
  │  1. Read generated_fix.patch                              │
  │  2. Apply to file(s)                                      │
  │  3. Run validation tests                                  │
  │  4. If tests pass: commit                                 │
  │  5. If tests fail: rollback                               │
  │  6. Store result in VectorStore                           │
  └───────────────────────────────────────────────────────────┘


  ANY GATE FAILS (NO) → ↓

  ┌───────────────────────────────────────────────────────────┐
  │  ✗ REJECTED FOR AUTONOMOUS FIX                            │
  └────────┬──────────────────────────────────────────────────┘
           │
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Create GitHub Issue                                      │
  │  • Title: recommendation.title                            │
  │  • Labels: priority, category                             │
  │  • Body: details + steps + generated_fix                  │
  │  • Assignee: human reviewer                               │
  └───────────────────────────────────────────────────────────┘
```

---

## LLM Fix Generation Flow

```
┌──────────────────────────────────────────────────────────────┐
│               FIX CODE GENERATION (qwen2.5-coder:32b)        │
└──────────────────────────────────────────────────────────────┘

  Enhanced Recommendation
         │
         ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Read Current Code                                        │
  │  • Extract lines from file_path                           │
  │  • Use line_start/line_end from location                  │
  └────────┬──────────────────────────────────────────────────┘
           │
           │ current_code: str
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Build LLM Prompt                                         │
  │                                                           │
  │  You are a code quality expert.                           │
  │  Generate ONLY the fixed code.                            │
  │                                                           │
  │  ISSUE: {title}                                           │
  │  CATEGORY: {category}                                     │
  │  SUMMARY: {summary}                                       │
  │  DETAILS: {details}                                       │
  │                                                           │
  │  CURRENT CODE:                                            │
  │  ```python                                                │
  │  {current_code}                                           │
  │  ```                                                      │
  │                                                           │
  │  STEPS TO FIX:                                            │
  │  1. {step1}                                               │
  │  2. {step2}                                               │
  │  ...                                                      │
  │                                                           │
  │  CONSTITUTIONAL REQUIREMENTS:                             │
  │  - Article I: Preserve complete context                   │
  │  - Article II: Maintain 100% test compatibility           │
  │  - Article V: Follow spec (this recommendation)           │
  │                                                           │
  │  Generate ONLY the fixed code:                            │
  └────────┬──────────────────────────────────────────────────┘
           │
           │ Send to qwen2.5-coder:32b
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  LLM Response                                             │
  │  • Parse code from response                               │
  │  • Remove markdown fences if present                      │
  │  • Extract pure code                                      │
  └────────┬──────────────────────────────────────────────────┘
           │
           │ fixed_code: str
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Generate Unified Diff Patch                              │
  │  • difflib.unified_diff()                                 │
  │  • Format: a/file vs b/file                               │
  │  • 3 lines context                                        │
  └────────┬──────────────────────────────────────────────────┘
           │
           │ patch: str
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  Generate Validation Code                                 │
  │                                                           │
  │  TRIVIAL: syntax check only                               │
  │  ```python                                                │
  │  compile(fixed_code, '<string>', 'exec')                  │
  │  ```                                                      │
  │                                                           │
  │  SIMPLE: unit test execution                              │
  │  ```python                                                │
  │  subprocess.run(['pytest', 'tests/test_foo.py'])          │
  │  ```                                                      │
  └────────┬──────────────────────────────────────────────────┘
           │
           │ validation_code: str
           ↓
  ┌───────────────────────────────────────────────────────────┐
  │  OUTPUT: GeneratedFix                                     │
  │  • fix_type: "deletion" | "replacement" | "refactor"      │
  │  • original_code: str                                     │
  │  • fixed_code: str                                        │
  │  • patch_format: str (unified diff)                       │
  │  • validation_code: str                                   │
  │  • generation_confidence: 0.85                            │
  │  • llm_model: "qwen2.5-coder:32b"                         │
  └───────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA FLOW OVERVIEW                            │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Codebase   │
│   (Python)   │
└──────┬───────┘
       │
       │ AST parsing
       ↓
┌──────────────────┐
│  Issue Detection │     ┌─────────────────┐
│  (AST + LLM)     │────→│  Issue object   │
└──────────────────┘     └────────┬────────┘
                                  │
                                  ↓
                         ┌────────────────────┐
                         │  AutoFixability    │
                         │  Classifier        │
                         └─────────┬──────────┘
                                   │
                                   │ Query learnings
                                   ↓
                         ┌─────────────────┐
                         │  VectorStore    │◄─────┐
                         │  (learning DB)  │      │
                         └─────────────────┘      │
                                   │              │
                                   │ Similar fixes│
                                   ↓              │
                         ┌────────────────────┐   │
                         │  Confidence boost  │   │
                         └─────────┬──────────┘   │
                                   │              │
                                   ↓              │
                         ┌────────────────────┐   │
                         │  Fix Generator     │   │
                         │  (LLM)             │   │
                         └─────────┬──────────┘   │
                                   │              │
                                   │ Generated fix│
                                   ↓              │
                         ┌────────────────────┐   │
                         │  Dependency        │   │
                         │  Analyzer          │   │
                         └─────────┬──────────┘   │
                                   │              │
                                   │ Dependencies │
                                   ↓              │
                         ┌────────────────────┐   │
                         │  Risk Scorer       │   │
                         └─────────┬──────────┘   │
                                   │              │
                                   │ Risk score   │
                                   ↓              │
                         ┌────────────────────┐   │
                         │  Enhanced          │   │
                         │  Recommendation    │   │
                         │  (Pydantic)        │   │
                         └─────────┬──────────┘   │
                                   │              │
                                   │ Write        │
                                   ↓              │
                         ┌────────────────────┐   │
                         │  Markdown + JSON   │   │
                         │  Files             │   │
                         └─────────┬──────────┘   │
                                   │              │
                                   │ Read         │
                                   ↓              │
                         ┌────────────────────┐   │
                         │  Autonomous        │   │
                         │  Decision Engine   │   │
                         └─────────┬──────────┘   │
                                   │              │
                    ┌──────────────┴──────────┐   │
                    │ AUTO      │   MANUAL    │   │
                    ↓           ↓             ↓   │
          ┌──────────────┐  ┌────────────┐       │
          │  Apply Fix   │  │  GitHub    │       │
          │  (patch)     │  │  Issue     │       │
          └──────┬───────┘  └────────────┘       │
                 │                                │
                 │ Test validation                │
                 ↓                                │
          ┌──────────────┐                        │
          │  Tests Pass? │                        │
          └──────┬───────┘                        │
                 │                                │
          ┌──────┴──────┐                         │
          │ YES    │ NO │                         │
          ↓        ↓    ↓                         │
    ┌─────────┐  ┌────────────┐                  │
    │ Commit  │  │  Rollback  │                  │
    └────┬────┘  └────────────┘                  │
         │                                        │
         │ Store success pattern                 │
         └────────────────────────────────────────┘
```

---

## Component Interaction Matrix

```
┌───────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│  Component    │ Reads    │ Writes   │ Queries  │ Calls    │ Stores   │
├───────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Classifier    │ Issue    │ Metadata │ Vector   │ Risk     │ -        │
│               │          │          │ Store    │ Scorer   │          │
├───────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Fix Generator │ Issue    │ Generated│ -        │ LLM      │ -        │
│               │ Code     │ Fix      │          │ API      │          │
├───────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Dependency    │ Files    │ Dep      │ -        │ AST      │ Import   │
│ Analyzer      │ (AST)    │ Info     │          │ Parser   │ Graph    │
├───────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Risk Scorer   │ Issue    │ Risk     │ -        │ AST      │ -        │
│               │ Files    │ Factors  │          │ Parser   │          │
├───────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Decision      │ Enhanced │ Decision │ -        │ Safety   │ -        │
│ Engine        │ Rec      │          │          │ Gates    │          │
├───────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Fix Applicator│ Patch    │ Modified │ -        │ Git      │ Vector   │
│               │ Tests    │ Files    │          │ Pytest   │ Store    │
└───────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## File Structure

```
Agency/
├── auditor_agent/
│   ├── auditor_agent.py (existing - AST analysis)
│   ├── ast_analyzer.py (existing)
│   ├── classifiers.py (NEW - auto-fixability)
│   ├── fix_generator.py (NEW - LLM fix generation)
│   ├── dependency_analyzer.py (NEW - AST import graph)
│   └── risk_scorer.py (NEW - risk quantification)
│
├── shared/
│   └── models/
│       └── auditor.py (NEW - EnhancedRecommendation + sub-models)
│
├── scripts/
│   ├── continuous_audit_m4pro.py (MODIFIED - integrate enhanced models)
│   └── autonomous_recommendation_fixer.py (MODIFIED - use metadata)
│
├── .output/
│   └── audit_recommendations/
│       ├── localM4_recommends_042.md (enhanced markdown)
│       └── recommendation_042.json (NEW - structured metadata)
│
└── docs/
    └── adr/
        ├── ADR-022-autonomous-auditor-architecture.md
        ├── ADR-022-EXECUTIVE-SUMMARY.md
        └── ADR-022-ARCHITECTURE-DIAGRAM.md (this file)
```

---

**Document Version**: 1.0
**Author**: ChiefArchitect (via Claude Code)
**Date**: 2025-10-07
