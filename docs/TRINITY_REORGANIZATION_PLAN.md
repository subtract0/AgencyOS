# Trinity Protocol Reorganization Implementation Plan

**Plan Status**: Ready for Execution
**Related ADR**: ADR-020-trinity-protocol-production-ization.md
**Phase**: Phase 2 of spec-019-meta-consolidation-pruning.md
**Duration**: 4 weeks (1 month)
**Code Reduction**: 18,914 → 11,500 lines (39% reduction)

---

## Executive Summary

This plan executes the reorganization of Trinity Protocol from a 47-file, 18,914-line monolith into a clean, maintainable structure with clear production/experimental boundaries. The reorganization achieves:

- **39% code reduction** (7,414 lines removed)
- **Clear boundaries** (production vs. experimental vs. demos)
- **Reusable components** (4 shared modules extracted)
- **Production readiness** (100% test coverage for core modules)

---

## Week 1: Audit & Categorization

### Day 1-2: File Audit & Categorization

**Objective**: Categorize all 47 Trinity files into production/experimental/demo/reusable.

**Tasks**:
1. **Analyze Each File**:
   - Review code quality (typing, tests, documentation)
   - Assess production-readiness (constitutional compliance, error handling)
   - Identify dependencies (imports, coupling)
   - Determine category (production/experimental/demo/reusable)

2. **Create Categorization Matrix** (CSV format):
   ```csv
   File,Lines,Category,Rationale,Dependencies,Test Coverage,Typing Quality
   executor_agent.py,774,Production,"Core execution coordinator, well-tested","cost_tracker, foundation_verifier",85%,Good
   architect_agent.py,729,Production,"Core architecture planner, well-tested","models/project, cost_tracker",90%,Excellent
   audio_capture.py,?,Experimental,"Microphone capture, not production-critical","pyaudio (external)",0%,Fair
   ...
   ```

3. **Document Categorization Criteria**:
   - **Production**: Tests ≥80%, strict typing, constitutional compliance, stable API
   - **Experimental**: Tests <80% or missing, rapid iteration, documented risks
   - **Demo**: Demonstration code, duplicates setup/fixtures, not used in production
   - **Reusable**: Generic functionality, no Trinity-specific coupling, API-ready

**Deliverables**:
- [ ] `TRINITY_MODULE_CATEGORIZATION.csv` (all 47 files categorized)
- [ ] Categorization criteria documented
- [ ] Initial assessment complete

**Validation Criteria**:
- ✅ All 47 files categorized with rationale
- ✅ Category criteria documented and applied consistently
- ✅ No files left uncategorized or ambiguous

---

### Day 3-4: Dependency Mapping

**Objective**: Map all dependencies between Trinity modules to identify extraction candidates and migration order.

**Tasks**:
1. **Generate Dependency Graph**:
   ```bash
   # Use pydeps or manual analysis
   pydeps trinity_protocol --max-bacon 2 --cluster --rankdir TB -o trinity_deps.svg
   ```

2. **Analyze Dependency Patterns**:
   - Identify circular dependencies (must be broken)
   - Find tightly coupled modules (candidates for consolidation)
   - Discover shared utilities (candidates for extraction)
   - Map import chains (determine safe migration order)

3. **Create Extraction Plan**:
   ```markdown
   ## Reusable Components (extract to shared/)

   ### 1. Cost Tracking System
   - **Files**: cost_tracker.py (473 lines), cost_dashboard.py (626 lines), cost_alerts.py (612 lines)
   - **Dependencies**: SQLite, telemetry
   - **Importers**: executor_agent.py, architect_agent.py, witness_agent.py
   - **API Surface**: CostTracker.track(), get_summary(), get_budget_status()

   ### 2. HITL Protocol
   - **Files**: human_review_queue.py (375 lines), question_delivery.py
   - **Dependencies**: models/hitl.py
   - **Importers**: executor_agent.py, architect_agent.py
   - **API Surface**: HITLProtocol.ask(), wait_approval(), get_queue_status()

   ### 3. Preference Learning
   - **Files**: preference_learning.py, preference_store.py (397 lines), alex_preference_learner.py (609 lines)
   - **Dependencies**: models/preferences.py (485 lines)
   - **Importers**: architect_agent.py, witness_agent.py
   - **API Surface**: PreferenceLearner.observe(), recommend(), get_preferences()

   ### 4. Pattern Detection
   - **Files**: pattern_detector.py, models/patterns.py
   - **Dependencies**: telemetry, message_bus.py
   - **Importers**: witness_agent.py, executor_agent.py
   - **API Surface**: PatternDetector.detect(), get_patterns(), register_pattern()
   ```

**Deliverables**:
- [ ] `trinity_deps.svg` (dependency graph visualization)
- [ ] Dependency analysis document (circular deps, coupling, extraction candidates)
- [ ] Extraction plan for 4 reusable components

**Validation Criteria**:
- ✅ Dependency graph shows all 47 files and their relationships
- ✅ No circular dependencies in extraction plan
- ✅ 4 reusable components identified with clear API boundaries
- ✅ Migration order determined (safe sequence to avoid breaking changes)

---

### Day 5: Migration Strategy & Rollback Plan

**Objective**: Define detailed migration strategy and rollback procedures.

**Tasks**:
1. **Create Migration Sequence**:
   ```markdown
   ## Week 2: Extract Reusable Components
   1. Extract shared/cost_tracker.py (lowest coupling)
   2. Extract shared/hitl_protocol.py
   3. Extract shared/preference_learning.py
   4. Extract shared/pattern_detector.py
   5. Update Trinity imports to use shared/

   ## Week 3: Reorganize Core & Experimental
   1. Create core/ directory, migrate production modules
   2. Create experimental/ directory, migrate prototypes
   3. Update imports across codebase

   ## Week 4: Consolidate Demos & Documentation
   1. Consolidate 10 demos → 3 demos
   2. Create Trinity README
   3. Create upgrade checklist
   ```

2. **Define Rollback Triggers**:
   - Test suite failure (any test fails)
   - Feature loss detected (inventory mismatch)
   - Performance regression (>10% slowdown)
   - Blocking bugs introduced

3. **Create Rollback Procedure**:
   ```bash
   # Rollback script
   #!/bin/bash

   echo "Rolling back Trinity reorganization..."
   git checkout pre-trinity-reorg  # Tag created before migration
   python run_tests.py --run-all   # Validate baseline tests pass
   echo "Rollback complete. Analyze failure and retry."
   ```

**Deliverables**:
- [ ] Migration sequence document (week-by-week, day-by-day)
- [ ] Rollback triggers documented
- [ ] Rollback script created (`scripts/rollback_trinity_reorg.sh`)

**Validation Criteria**:
- ✅ Migration sequence addresses all 47 files
- ✅ Rollback triggers clearly defined
- ✅ Rollback script tested (dry-run successful)

---

## Week 2: Extract Reusable Components

### Day 1-2: Extract shared/cost_tracker.py

**Objective**: Extract cost tracking system to shared/ with generic API.

**Tasks**:
1. **Create Generic Cost Tracker**:
   ```python
   # shared/cost_tracker.py

   from typing import Optional, Dict, List
   from datetime import datetime
   from pydantic import BaseModel
   from shared.type_definitions.result import Result, Ok, Err

   class CostEntry(BaseModel):
       """Single cost tracking entry."""
       operation: str
       cost: float
       tokens_input: int
       tokens_output: int
       model: str
       timestamp: datetime
       metadata: Dict[str, str] = {}

   class CostSummary(BaseModel):
       """Cost summary with aggregations."""
       total_cost: float
       total_operations: int
       total_tokens: int
       cost_by_model: Dict[str, float]
       cost_by_operation: Dict[str, float]

   class CostTracker:
       """Generic cost tracking for any agent or operation."""

       def __init__(self, storage_backend: str = "sqlite"):
           """Initialize with pluggable storage backend."""
           self.backend = self._init_backend(storage_backend)

       def track(self, operation: str, cost: float, tokens_input: int,
                 tokens_output: int, model: str, **metadata) -> Result[None, str]:
           """Track a cost entry."""
           entry = CostEntry(
               operation=operation,
               cost=cost,
               tokens_input=tokens_input,
               tokens_output=tokens_output,
               model=model,
               timestamp=datetime.now(),
               metadata=metadata
           )
           return self.backend.store(entry)

       def get_summary(self, start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> Result[CostSummary, str]:
           """Get cost summary for date range."""
           entries = self.backend.query(start_date, end_date)
           return Ok(self._calculate_summary(entries))
   ```

2. **Extract from Trinity**:
   - Copy `trinity_protocol/cost_tracker.py` → `shared/cost_tracker.py`
   - Remove Trinity-specific coupling (hardcoded paths, Trinity models)
   - Add generic API (pluggable backends: SQLite, memory, custom)
   - Add 100% test coverage

3. **Update Trinity Imports**:
   ```python
   # Before
   from trinity_protocol.cost_tracker import CostTracker

   # After
   from shared.cost_tracker import CostTracker
   ```

**Deliverables**:
- [ ] `shared/cost_tracker.py` with generic API
- [ ] 100% test coverage (`tests/unit/shared/test_cost_tracker.py`)
- [ ] Trinity imports updated (executor, architect, witness)
- [ ] All tests pass (zero regression)

**Validation Criteria**:
- ✅ Generic API with no Trinity-specific coupling
- ✅ 100% test coverage (all paths tested)
- ✅ Trinity modules successfully use `shared/cost_tracker`
- ✅ All 1,568+ tests pass (baseline maintained)

---

### Day 3: Extract shared/hitl_protocol.py

**Objective**: Extract human-in-the-loop protocol to shared/.

**Tasks**:
1. **Create Generic HITL Protocol**:
   ```python
   # shared/hitl_protocol.py

   from typing import Optional, List, Callable
   from pydantic import BaseModel
   from shared.type_definitions.result import Result, Ok, Err

   class HITLQuestion(BaseModel):
       """Human-in-the-loop question."""
       id: str
       question: str
       context: Dict[str, str]
       options: List[str] = []
       default: Optional[str] = None

   class HITLResponse(BaseModel):
       """Human response to HITL question."""
       question_id: str
       answer: str
       timestamp: datetime

   class HITLProtocol:
       """Generic human-in-the-loop protocol."""

       def __init__(self, delivery_method: str = "cli"):
           """Initialize with pluggable delivery method (cli, web, slack)."""
           self.delivery = self._init_delivery(delivery_method)
           self.queue: List[HITLQuestion] = []

       def ask(self, question: str, context: Dict[str, str] = {},
              options: List[str] = []) -> Result[str, str]:
           """Ask human for input."""
           q = HITLQuestion(
               id=generate_id(),
               question=question,
               context=context,
               options=options
           )
           self.queue.append(q)
           return self.delivery.deliver_and_wait(q)

       def wait_approval(self, action: str, details: Dict[str, str]) -> Result[bool, str]:
           """Wait for human approval of action."""
           response = self.ask(
               f"Approve action: {action}?",
               context=details,
               options=["approve", "reject", "modify"]
           )
           return Ok(response.is_ok() and response.unwrap() == "approve")
   ```

2. **Extract from Trinity**:
   - Copy `trinity_protocol/human_review_queue.py`, `question_delivery.py` → `shared/hitl_protocol.py`
   - Remove Trinity-specific coupling
   - Add pluggable delivery methods (CLI, web, Slack)
   - Add 100% test coverage

3. **Update Trinity Imports**:
   ```python
   # Before
   from trinity_protocol.human_review_queue import HumanReviewQueue

   # After
   from shared.hitl_protocol import HITLProtocol
   ```

**Deliverables**:
- [ ] `shared/hitl_protocol.py` with generic API
- [ ] 100% test coverage (`tests/unit/shared/test_hitl_protocol.py`)
- [ ] Trinity imports updated (executor, architect)
- [ ] All tests pass (zero regression)

**Validation Criteria**:
- ✅ Generic HITL protocol with pluggable delivery
- ✅ 100% test coverage
- ✅ Trinity modules use `shared/hitl_protocol`
- ✅ All tests pass

---

### Day 4: Extract shared/preference_learning.py

**Objective**: Extract preference learning engine to shared/.

**Tasks**:
1. **Create Generic Preference Learner**:
   ```python
   # shared/preference_learning.py

   from typing import Dict, List, Any
   from pydantic import BaseModel
   from shared.type_definitions.result import Result, Ok, Err

   class UserPreference(BaseModel):
       """Single user preference."""
       category: str
       key: str
       value: Any
       confidence: float
       evidence_count: int

   class PreferenceLearner:
       """Generic preference learning engine."""

       def __init__(self, storage_backend: str = "memory"):
           """Initialize with pluggable storage."""
           self.backend = self._init_backend(storage_backend)
           self.preferences: Dict[str, UserPreference] = {}

       def observe(self, action: str, outcome: str, context: Dict[str, Any]) -> Result[None, str]:
           """Observe user action and outcome to learn preferences."""
           preference = self._extract_preference(action, outcome, context)
           return self._update_preference(preference)

       def recommend(self, context: Dict[str, Any]) -> Result[str, str]:
           """Recommend action based on learned preferences."""
           relevant_prefs = self._filter_preferences(context)
           return Ok(self._generate_recommendation(relevant_prefs))

       def get_preferences(self, category: Optional[str] = None) -> List[UserPreference]:
           """Get all learned preferences."""
           if category:
               return [p for p in self.preferences.values() if p.category == category]
           return list(self.preferences.values())
   ```

2. **Extract from Trinity**:
   - Copy `preference_learning.py`, `preference_store.py`, `alex_preference_learner.py` → `shared/preference_learning.py`
   - Consolidate 3 files into single generic implementation
   - Remove Alex-specific hardcoding
   - Add 100% test coverage

3. **Update Trinity Imports**:
   ```python
   # Before
   from trinity_protocol.alex_preference_learner import AlexPreferenceLearner

   # After
   from shared.preference_learning import PreferenceLearner
   ```

**Deliverables**:
- [ ] `shared/preference_learning.py` with generic API
- [ ] 100% test coverage (`tests/unit/shared/test_preference_learning.py`)
- [ ] Trinity imports updated (architect, witness)
- [ ] All tests pass (zero regression)

**Validation Criteria**:
- ✅ Generic preference learner with pluggable backend
- ✅ 100% test coverage
- ✅ Trinity modules use `shared/preference_learning`
- ✅ All tests pass

---

### Day 5: Extract shared/pattern_detector.py

**Objective**: Extract pattern detection system to shared/.

**Tasks**:
1. **Create Generic Pattern Detector**:
   ```python
   # shared/pattern_detector.py

   from typing import List, Dict, Callable
   from pydantic import BaseModel
   from shared.type_definitions.result import Result, Ok, Err

   class Pattern(BaseModel):
       """Detected behavioral pattern."""
       pattern_id: str
       pattern_type: str
       description: str
       frequency: int
       confidence: float
       examples: List[Dict[str, Any]]

   class PatternDetector:
       """Generic pattern detection engine."""

       def __init__(self):
           """Initialize pattern detector."""
           self.patterns: Dict[str, Pattern] = {}
           self.detectors: List[Callable] = []

       def register_pattern(self, pattern_type: str,
                          detector_func: Callable) -> Result[None, str]:
           """Register a new pattern detector."""
           self.detectors.append((pattern_type, detector_func))
           return Ok(None)

       def detect(self, events: List[Dict[str, Any]]) -> Result[List[Pattern], str]:
           """Detect patterns in event stream."""
           detected = []
           for pattern_type, detector in self.detectors:
               patterns = detector(events)
               detected.extend(patterns)
           return Ok(detected)

       def get_patterns(self, pattern_type: Optional[str] = None,
                       min_confidence: float = 0.0) -> List[Pattern]:
           """Get detected patterns."""
           patterns = self.patterns.values()
           if pattern_type:
               patterns = [p for p in patterns if p.pattern_type == pattern_type]
           return [p for p in patterns if p.confidence >= min_confidence]
   ```

2. **Extract from Trinity**:
   - Copy `pattern_detector.py`, `models/patterns.py` → `shared/pattern_detector.py`
   - Remove Trinity-specific patterns (make pluggable)
   - Add generic pattern registration API
   - Add 100% test coverage

3. **Update Trinity Imports**:
   ```python
   # Before
   from trinity_protocol.pattern_detector import PatternDetector

   # After
   from shared.pattern_detector import PatternDetector
   ```

**Deliverables**:
- [ ] `shared/pattern_detector.py` with generic API
- [ ] 100% test coverage (`tests/unit/shared/test_pattern_detector.py`)
- [ ] Trinity imports updated (witness, executor)
- [ ] All tests pass (zero regression)

**Validation Criteria**:
- ✅ Generic pattern detector with pluggable detectors
- ✅ 100% test coverage
- ✅ Trinity modules use `shared/pattern_detector`
- ✅ All tests pass

---

## Week 3: Reorganize Core & Experimental

### Day 1-2: Create Directory Structure & Migrate Core

**Objective**: Create `core/` directory and migrate production-ready modules.

**Tasks**:
1. **Create Directory Structure**:
   ```bash
   mkdir -p trinity_protocol/core
   mkdir -p trinity_protocol/core/models
   mkdir -p trinity_protocol/experimental
   mkdir -p trinity_protocol/demos
   ```

2. **Migrate Production Modules to core/**:

   **executor_agent.py → core/executor.py** (optimize):
   - Extract core executor logic (remove Trinity-specific coupling)
   - Reduce from 774 → ~400 lines (consolidate, simplify)
   - Add strict typing (Result<T,E> pattern throughout)
   - Ensure 100% test coverage

   **architect_agent.py → core/architect.py** (optimize):
   - Extract core architect logic
   - Reduce from 729 → ~400 lines
   - Add strict typing
   - Ensure 100% test coverage

   **witness_agent.py → core/witness.py** (patterns only):
   - Keep pattern detection only (remove ambient monitoring)
   - Reduce to ~300 lines (focused on patterns)
   - Ambient features moved to experimental/

   **orchestrator.py → core/orchestrator.py** (as-is):
   - Move orchestrator to core/
   - Minimal changes (already production-ready)

3. **Migrate Models to core/models/**:
   ```bash
   mv trinity_protocol/models/project.py trinity_protocol/core/models/project.py
   mv trinity_protocol/models/patterns.py trinity_protocol/core/models/patterns.py
   mv trinity_protocol/models/preferences.py trinity_protocol/core/models/preferences.py
   mv trinity_protocol/models/hitl.py trinity_protocol/core/models/hitl.py
   ```

4. **Update core/__init__.py**:
   ```python
   # trinity_protocol/core/__init__.py

   """Trinity Protocol Core - Production-Ready Modules

   All modules in this directory meet production criteria:
   - 100% test coverage
   - Strict Pydantic typing (no Dict[Any, Any])
   - Constitutional compliance (all 5 articles)
   - Result<T,E> error handling
   - Functions <50 lines
   - Comprehensive documentation
   """

   from .executor import TrinityExecutor
   from .architect import TrinityArchitect
   from .witness import TrinityWitness
   from .orchestrator import TrinityOrchestrator

   __all__ = [
       "TrinityExecutor",
       "TrinityArchitect",
       "TrinityWitness",
       "TrinityOrchestrator"
   ]
   ```

**Deliverables**:
- [ ] `trinity_protocol/core/` directory created with 4 production modules
- [ ] `trinity_protocol/core/models/` with 4 model files
- [ ] Production modules optimized (5,000 total lines)
- [ ] 100% test coverage for all core modules

**Validation Criteria**:
- ✅ All core modules have 100% test coverage
- ✅ Strict typing enforced (mypy --strict passes)
- ✅ Constitutional compliance verified (all 5 articles)
- ✅ All tests pass (zero regression)

---

### Day 3: Migrate Experimental Modules

**Objective**: Move experimental/prototype modules to `experimental/`.

**Tasks**:
1. **Migrate to experimental/**:
   ```bash
   # Audio/transcription (experimental - not production-critical)
   mv trinity_protocol/audio_capture.py trinity_protocol/experimental/audio_capture.py
   mv trinity_protocol/whisper_transcriber.py trinity_protocol/experimental/whisper_transcriber.py
   mv trinity_protocol/transcription_service.py trinity_protocol/experimental/transcription_service.py

   # Ambient listening (experimental - privacy concerns)
   mv trinity_protocol/ambient_listener_service.py trinity_protocol/experimental/ambient_listener.py
   mv trinity_protocol/witness_ambient_mode.py trinity_protocol/experimental/witness_ambient.py

   # Response handling (experimental)
   mv trinity_protocol/response_handler.py trinity_protocol/experimental/response_handler.py
   ```

2. **Mark as Experimental** (add docstring warnings):
   ```python
   # trinity_protocol/experimental/audio_capture.py

   """Audio Capture - EXPERIMENTAL

   **Status**: Experimental / Prototype
   **Privacy Concerns**: Microphone access, user consent required
   **Dependencies**: pyaudio (external), platform-specific
   **Production Readiness**: Not ready (lacks tests, error handling)

   To upgrade to production, complete:
   - [ ] 100% test coverage (currently 0%)
   - [ ] Privacy consent flow (user approval)
   - [ ] Cross-platform compatibility (Windows, macOS, Linux)
   - [ ] Error handling (Result<T,E> pattern)
   - [ ] Constitutional compliance (Articles I-V)

   See: docs/TRINITY_UPGRADE_CHECKLIST.md
   """
   ```

3. **Update experimental/__init__.py**:
   ```python
   # trinity_protocol/experimental/__init__.py

   """Trinity Protocol Experimental - Prototypes & Research

   **WARNING**: Modules in this directory are EXPERIMENTAL.

   Experimental modules:
   - May have incomplete tests or no tests
   - May have privacy/security concerns
   - May require external dependencies
   - May change rapidly without notice

   Do NOT use experimental modules in production.
   Upgrade path: See docs/TRINITY_UPGRADE_CHECKLIST.md
   """

   # Import experimental modules (marked as experimental)
   from .audio_capture import AudioCapture
   from .ambient_listener import AmbientListener
   from .whisper_transcriber import WhisperTranscriber
   from .witness_ambient import WitnessAmbient

   __all__ = [
       "AudioCapture",
       "AmbientListener",
       "WhisperTranscriber",
       "WitnessAmbient"
   ]
   ```

**Deliverables**:
- [ ] `trinity_protocol/experimental/` directory with 6 experimental modules
- [ ] All experimental files marked with "EXPERIMENTAL" warnings
- [ ] `experimental/__init__.py` with clear warnings
- [ ] Documentation of privacy/security concerns

**Validation Criteria**:
- ✅ All experimental modules moved to `experimental/`
- ✅ Clear "EXPERIMENTAL" warnings in all docstrings
- ✅ Privacy/security concerns documented
- ✅ Upgrade checklist referenced

---

### Day 4-5: Update Imports Across Codebase

**Objective**: Update all imports to use new `core/` and `experimental/` structure.

**Tasks**:
1. **Find All Trinity Imports**:
   ```bash
   # Search for Trinity imports
   grep -r "from trinity_protocol import" --include="*.py"
   grep -r "from trinity_protocol." --include="*.py"
   grep -r "import trinity_protocol" --include="*.py"
   ```

2. **Update to core/ Imports**:
   ```python
   # Before
   from trinity_protocol.executor_agent import ExecutorAgent
   from trinity_protocol.architect_agent import ArchitectAgent
   from trinity_protocol.witness_agent import WitnessAgent
   from trinity_protocol.orchestrator import Orchestrator

   # After
   from trinity_protocol.core import TrinityExecutor
   from trinity_protocol.core import TrinityArchitect
   from trinity_protocol.core import TrinityWitness
   from trinity_protocol.core import TrinityOrchestrator
   ```

3. **Update to experimental/ Imports** (if needed):
   ```python
   # Before
   from trinity_protocol.audio_capture import AudioCapture
   from trinity_protocol.ambient_listener_service import AmbientListener

   # After
   from trinity_protocol.experimental import AudioCapture
   from trinity_protocol.experimental import AmbientListener
   ```

4. **Add Backward Compatibility** (30-day deprecation):
   ```python
   # trinity_protocol/__init__.py

   import warnings

   # Deprecated imports (remove after 30 days)
   def __getattr__(name):
       deprecated_map = {
           "executor_agent": "trinity_protocol.core.executor",
           "architect_agent": "trinity_protocol.core.architect",
           "witness_agent": "trinity_protocol.core.witness",
           "audio_capture": "trinity_protocol.experimental.audio_capture"
       }

       if name in deprecated_map:
           warnings.warn(
               f"{name} is deprecated. Use {deprecated_map[name]} instead.",
               DeprecationWarning,
               stacklevel=2
           )
           # Still import (backward compatible during transition)
           module = __import__(deprecated_map[name], fromlist=[name])
           return getattr(module, name)

       raise AttributeError(f"module 'trinity_protocol' has no attribute '{name}'")
   ```

5. **Validate All Imports**:
   ```bash
   # Run tests to validate imports work
   python run_tests.py --run-all

   # Check for import errors
   python -c "from trinity_protocol.core import TrinityExecutor; print('OK')"
   python -c "from trinity_protocol.experimental import AudioCapture; print('OK')"
   ```

**Deliverables**:
- [ ] All imports updated to use `core/` and `experimental/`
- [ ] Backward compatibility layer added (30-day deprecation)
- [ ] Import validation complete (all imports work)
- [ ] All tests pass (zero regression)

**Validation Criteria**:
- ✅ All imports updated successfully (no broken references)
- ✅ Backward compatibility works (old imports still function with warnings)
- ✅ All 1,568+ tests pass (zero regression)
- ✅ No import errors (validated via test suite)

---

## Week 4: Consolidate Demos & Documentation

### Day 1-2: Consolidate Demos

**Objective**: Consolidate 10 demo files into 3 focused demos.

**Tasks**:
1. **Consolidate Main Demo** (`demos/demo_complete.py`):
   - Merge: `demo_integration.py`, `demo_complete_trinity.py`, `test_dashboard_demo.py`
   - Structure:
     ```python
     # trinity_protocol/demos/demo_complete.py

     """Trinity Protocol Complete Demo

     Demonstrates full Trinity capabilities:
     - Project architecture (Architect)
     - Project execution (Executor)
     - Pattern detection (Witness)
     - Cost tracking
     - Foundation verification
     """

     def demo_architecture():
         """Demo: Architect agent creates project plan."""
         ...

     def demo_execution():
         """Demo: Executor agent executes project."""
         ...

     def demo_witness():
         """Demo: Witness agent detects patterns."""
         ...

     def demo_cost_tracking():
         """Demo: Cost tracking and budgets."""
         ...

     if __name__ == "__main__":
         print("Trinity Protocol Complete Demo")
         demo_architecture()
         demo_execution()
         demo_witness()
         demo_cost_tracking()
     ```

2. **Keep HITL Demo** (`demos/demo_hitl.py`):
   - Keep as-is (already focused on HITL workflow)
   - Minor updates to use `shared/hitl_protocol`

3. **Keep Preference Demo** (`demos/demo_preferences.py`):
   - Keep as-is (already focused on preferences)
   - Minor updates to use `shared/preference_learning`

4. **Remove Redundant Demos**:
   ```bash
   # Verify no unique functionality, then remove
   git rm trinity_protocol/demo_integration.py
   git rm trinity_protocol/demo_complete_trinity.py
   git rm trinity_protocol/demo_architect.py
   git rm trinity_protocol/test_dashboard_demo.py
   git rm trinity_protocol/run_8h_ui_test.py
   git rm trinity_protocol/run_24h_test.py
   git rm trinity_protocol/verify_cost_tracking.py
   git rm trinity_protocol/generate_24h_report.py
   ```

**Deliverables**:
- [ ] `trinity_protocol/demos/demo_complete.py` (main demo, ~400 lines)
- [ ] `trinity_protocol/demos/demo_hitl.py` (HITL demo, ~300 lines)
- [ ] `trinity_protocol/demos/demo_preferences.py` (preferences demo, ~300 lines)
- [ ] 7 redundant demos removed (verified no unique functionality lost)

**Validation Criteria**:
- ✅ 3 focused demos created (complete, HITL, preferences)
- ✅ All demos run successfully (no errors)
- ✅ Redundant demos removed (verified via feature inventory)
- ✅ Total demo code: ~1,000 lines (75% reduction from 4,000)

---

### Day 3: Create Trinity README

**Objective**: Create comprehensive Trinity README with production/experimental guide.

**Tasks**:
1. **Create trinity_protocol/README.md**:
   ```markdown
   # Trinity Protocol

   **Status**: Production-Ready Core + Experimental Extensions
   **Code Size**: 11,500 lines (39% reduction from 18,914)
   **Test Coverage**: 100% (core modules)

   ---

   ## Overview

   Trinity Protocol provides intelligent project execution with three core agents:
   - **Architect**: Creates project plans from specifications
   - **Executor**: Executes projects with quality gates and HITL
   - **Witness**: Detects patterns and learns user preferences

   ---

   ## Production Modules (trinity_protocol/core/)

   ### Core Agents
   - `executor.py`: Production execution coordinator (400 lines, 100% tests)
   - `architect.py`: Production architecture planner (400 lines, 100% tests)
   - `witness.py`: Production pattern witness (300 lines, 100% tests)
   - `orchestrator.py`: Trinity orchestration (200 lines, 100% tests)

   ### Models
   - `models/project.py`: Project data models
   - `models/patterns.py`: Pattern detection models
   - `models/preferences.py`: User preference models
   - `models/hitl.py`: Human-in-the-loop models

   **Production Criteria**:
   - ✅ 100% test coverage
   - ✅ Strict Pydantic typing
   - ✅ Constitutional compliance
   - ✅ Result<T,E> error handling
   - ✅ Functions <50 lines
   - ✅ Comprehensive documentation

   ---

   ## Experimental Modules (trinity_protocol/experimental/)

   **WARNING**: Experimental modules are NOT production-ready.

   - `audio_capture.py`: Microphone capture (privacy concerns)
   - `ambient_listener.py`: Always-on listening (privacy concerns)
   - `whisper_transcriber.py`: Transcription (requires whisper.cpp)
   - `witness_ambient.py`: Ambient witness prototype

   **Experimental Characteristics**:
   - ℹ️ Tests incomplete or missing
   - ℹ️ Privacy/security concerns documented
   - ℹ️ Rapid iteration permitted
   - ℹ️ May require external dependencies
   - ℹ️ May change without notice

   ---

   ## Reusable Components (shared/)

   Trinity uses generic components from `shared/`:
   - `shared/cost_tracker.py`: Generic cost tracking
   - `shared/hitl_protocol.py`: Generic HITL pattern
   - `shared/preference_learning.py`: Generic preference engine
   - `shared/pattern_detector.py`: Generic pattern detection

   ---

   ## Usage

   ### Production Usage
   ```python
   from trinity_protocol.core import TrinityExecutor, TrinityArchitect, TrinityWitness

   # Create project plan
   architect = TrinityArchitect()
   plan = architect.create_plan(spec)

   # Execute project
   executor = TrinityExecutor()
   result = executor.execute_project(plan)

   # Detect patterns
   witness = TrinityWitness()
   patterns = witness.detect_patterns(events)
   ```

   ### Experimental Usage (Use at Your Own Risk)
   ```python
   from trinity_protocol.experimental import AudioCapture, AmbientListener

   # EXPERIMENTAL: Audio capture (privacy concerns)
   audio = AudioCapture()
   audio.start_capture()  # Requires user consent!
   ```

   ---

   ## Demos

   - `demos/demo_complete.py`: Full Trinity capabilities
   - `demos/demo_hitl.py`: Human-in-the-loop workflow
   - `demos/demo_preferences.py`: Preference learning

   ---

   ## Upgrade Path: Experimental → Production

   See: `docs/TRINITY_UPGRADE_CHECKLIST.md` for detailed checklist.

   Summary:
   1. Achieve 100% test coverage
   2. Convert to strict typing (Pydantic models)
   3. Validate constitutional compliance
   4. Add comprehensive documentation
   5. Code review by ChiefArchitectAgent
   6. Move to `trinity_protocol/core/`
   ```

**Deliverables**:
- [ ] `trinity_protocol/README.md` (comprehensive guide)
- [ ] Clear production vs. experimental documentation
- [ ] Usage examples for both production and experimental
- [ ] Upgrade path referenced

**Validation Criteria**:
- ✅ README covers all modules (core, experimental, demos)
- ✅ Production criteria clearly documented
- ✅ Experimental warnings prominent
- ✅ Usage examples provided

---

### Day 4: Create Upgrade Checklist

**Objective**: Create comprehensive experimental-to-production upgrade checklist.

**Tasks**:
1. **Create docs/TRINITY_UPGRADE_CHECKLIST.md** (already included in ADR-020)
   - Copy from ADR-020 "Production Module Upgrade Checklist" section
   - Expand with detailed instructions for each step
   - Add validation scripts and automation where possible

**Deliverables**:
- [ ] `docs/TRINITY_UPGRADE_CHECKLIST.md` (detailed checklist)
- [ ] Validation scripts for automated checking

**Validation Criteria**:
- ✅ Checklist covers all 6 upgrade steps
- ✅ Each step has clear validation criteria
- ✅ Automation provided where possible

---

### Day 5: Final Validation & Documentation

**Objective**: Final validation and documentation updates.

**Tasks**:
1. **Run Full Test Suite**:
   ```bash
   python run_tests.py --run-all
   # Expected: 1,568+ tests pass (100% pass rate)
   ```

2. **Validate Code Reduction**:
   ```bash
   # Count lines before/after
   find trinity_protocol -name "*.py" -exec wc -l {} + | tail -1
   # Expected: ~11,500 lines (39% reduction from 18,914)
   ```

3. **Update Documentation**:
   - Update main README.md (Trinity references)
   - Update constitution.md (if Trinity-specific references)
   - Update ADR-016 (Ambient Listener) with new paths
   - Update ADR-017 (Phase 3 Project Execution) with new imports

4. **Create Migration Summary**:
   ```markdown
   # Trinity Reorganization Summary

   ## Metrics
   - **Code Reduction**: 18,914 → 11,500 lines (39% reduction)
   - **File Reduction**: 47 → 25 files (47% reduction)
   - **Test Coverage**: 100% (core modules)
   - **Reusable Components**: 4 (cost, HITL, preferences, patterns)

   ## Structure
   - `core/`: 4 production modules (5,000 lines, 100% tests)
   - `experimental/`: 6 experimental modules (3,500 lines)
   - `demos/`: 3 consolidated demos (1,000 lines)
   - `shared/`: 4 reusable components (2,000 lines)

   ## Impact
   - Clarity: 100% module categorization (no ambiguity)
   - Reusability: 4 shared components benefit all agents
   - Maintainability: 37% → 23% of total codebase
   - Quality: Production core has 100% test coverage
   ```

**Deliverables**:
- [ ] All tests pass (1,568+ tests, 100% pass rate)
- [ ] Code reduction validated (39% reduction achieved)
- [ ] Documentation updated (README, ADRs, constitution)
- [ ] Migration summary document created

**Validation Criteria**:
- ✅ All 1,568+ tests pass (zero regression)
- ✅ Code reduction: 7,414 lines removed (39%)
- ✅ Documentation complete and accurate
- ✅ Migration summary shows success metrics

---

## Final Validation Checklist

### Quantitative Validation

- [ ] **Code Volume**: Reduced from 18,914 → 11,500 lines (39% reduction)
- [ ] **File Count**: Reduced from 47 → 25 files (47% reduction)
- [ ] **Test Coverage**: 100% for all core modules
- [ ] **Reusable Components**: 4 components extracted to shared/
- [ ] **Test Pass Rate**: 100% (all 1,568+ tests pass)

### Qualitative Validation

- [ ] **Clarity**: 100% module categorization (production/experimental/demos)
- [ ] **Documentation**: README complete, upgrade checklist created
- [ ] **Reusability**: Other agents can use cost tracking, HITL, preferences, patterns
- [ ] **Maintainability**: Clear boundaries, appropriate standards for each category

### Constitutional Compliance

- [ ] **Article I**: Complete context (timeout wrapper, retry logic) - core modules
- [ ] **Article II**: 100% verification (all tests pass) - core modules
- [ ] **Article III**: Automated enforcement (quality gates) - core modules
- [ ] **Article IV**: Continuous learning (telemetry, pattern detection) - all modules
- [ ] **Article V**: Spec-driven (traced to spec-019 Phase 2) - reorganization

---

## Success Declaration

**Trinity Reorganization Complete When**:
- ✅ All 5 quantitative metrics met (code reduction, file reduction, tests, components, pass rate)
- ✅ All 4 qualitative metrics met (clarity, docs, reusability, maintainability)
- ✅ All 5 constitutional articles validated (core modules)
- ✅ Zero test failures (100% pass rate maintained)
- ✅ Zero feature loss (inventory validated)

**Celebration Message**:
```
🎉 Trinity Protocol Reorganization Complete!

📊 Metrics:
- 39% code reduction (18,914 → 11,500 lines)
- 47% file reduction (47 → 25 files)
- 100% test coverage (core modules)
- 4 reusable components extracted

🎯 Outcomes:
- Clear production/experimental boundaries
- Reusable components benefit all agents
- 37% → 23% of total codebase
- Production-ready core with strict quality gates

🚀 Ready for Phase 3: Tool Smart Caching & Determinism
```

---

## Appendix: Quick Reference

### Directory Structure
```
trinity_protocol/
├── core/                    # Production (5,000 lines, 100% tests)
│   ├── executor.py
│   ├── architect.py
│   ├── witness.py
│   ├── orchestrator.py
│   └── models/
├── experimental/            # Experimental (3,500 lines)
│   ├── audio_capture.py
│   ├── ambient_listener.py
│   ├── whisper_transcriber.py
│   └── witness_ambient.py
├── demos/                   # Demos (1,000 lines)
│   ├── demo_complete.py
│   ├── demo_hitl.py
│   └── demo_preferences.py
└── README.md

shared/                      # Reusable (2,000 lines)
├── cost_tracker.py
├── hitl_protocol.py
├── preference_learning.py
└── pattern_detector.py
```

### Import Patterns
```python
# Production modules
from trinity_protocol.core import TrinityExecutor, TrinityArchitect, TrinityWitness

# Experimental modules (use at your own risk)
from trinity_protocol.experimental import AudioCapture, AmbientListener

# Reusable components
from shared.cost_tracker import CostTracker
from shared.hitl_protocol import HITLProtocol
from shared.preference_learning import PreferenceLearner
from shared.pattern_detector import PatternDetector
```

### Key Commands
```bash
# Run full test suite
python run_tests.py --run-all

# Validate code reduction
find trinity_protocol -name "*.py" -exec wc -l {} + | tail -1

# Run demos
python trinity_protocol/demos/demo_complete.py
python trinity_protocol/demos/demo_hitl.py
python trinity_protocol/demos/demo_preferences.py

# Check imports
python -c "from trinity_protocol.core import TrinityExecutor; print('✅ OK')"
```

---

*"Simplicity is the ultimate sophistication." — Leonardo da Vinci*

**Let's execute! Week 1 starts now.** 🚀
