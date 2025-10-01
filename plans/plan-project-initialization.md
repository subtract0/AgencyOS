# Technical Plan: Trinity Project Initialization Flow

**Plan ID**: `plan-018-project-initialization`
**Spec Reference**: `spec-018-project-initialization-flow.md`
**Status**: Draft
**Author**: Planner Agent
**Created**: 2025-10-01
**Last Updated**: 2025-10-01
**Implementation Start**: TBD
**Target Completion**: 2 weeks from start

---

## Executive Summary

This plan implements Trinity Life Assistant Phase 3: Project Initialization Flow. The architecture consists of five core components working together to transform YES responses into completed projects. The ProjectInitializer conducts structured Q&A sessions, SpecFromConversation generates formal specifications, ProjectExecutor manages daily micro-tasks, DailyCheckin coordinates 1-3 questions per day, and ProjectStateManager ensures persistence across restarts. The implementation follows strict constitutional requirements (100% test coverage, strict typing, Result pattern) and integrates seamlessly with existing Phase 1-2 systems (ambient listener, preference learning, WITNESS/ARCHITECT agents).

**Key Innovation**: The system maintains sustained project momentum with minimal user time investment (~5 minutes per day) by intelligently breaking work into micro-tasks, asking focused questions, and executing background work between check-ins.

---

## Architecture Overview

### High-Level Design
```
┌──────────────────────────────────────────────────────────────────────┐
│                     Phase 3: Project Execution                        │
│                                                                        │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐         │
│  │   WITNESS   │───▶│  ARCHITECT   │───▶│ Human Review    │         │
│  │  (Phase 1)  │    │   (Phase 2)  │    │ Queue (Phase 2) │         │
│  └─────────────┘    └──────────────┘    └─────────────────┘         │
│                                                    │                   │
│                                                    │ YES response      │
│                                                    ▼                   │
│                          ┌──────────────────────────────────┐         │
│                          │   Project Initializer            │         │
│                          │  (project_initializer.py)        │         │
│                          │  - Trigger Q&A phase             │         │
│                          │  - Generate 5-10 questions       │         │
│                          │  - Capture answers               │         │
│                          │  - Validate completeness         │         │
│                          └──────────────────────────────────┘         │
│                                     │                                  │
│                                     │ Q&A transcript                   │
│                                     ▼                                  │
│                          ┌──────────────────────────────────┐         │
│                          │   Spec From Conversation         │         │
│                          │  (spec_from_conversation.py)     │         │
│                          │  - Extract requirements          │         │
│                          │  - Generate formal spec.md       │         │
│                          │  - Request user approval         │         │
│                          └──────────────────────────────────┘         │
│                                     │                                  │
│                                     │ Approved spec                    │
│                                     ▼                                  │
│                          ┌──────────────────────────────────┐         │
│                          │   Plan Generator                 │         │
│                          │  (plan_generator.py)             │         │
│                          │  - Break into micro-tasks        │         │
│                          │  - Define dependencies           │         │
│                          │  - Estimate timeline             │         │
│                          │  - Create plan.md                │         │
│                          └──────────────────────────────────┘         │
│                                     │                                  │
│                                     │ Implementation plan              │
│                                     ▼                                  │
│     ┌────────────────────────────────────────────────────────┐        │
│     │                  Project Executor                       │        │
│     │                (project_executor.py)                    │        │
│     │                                                          │        │
│     │  ┌──────────────────────────────────────────────┐      │        │
│     │  │      Daily Check-in Coordinator              │      │        │
│     │  │       (daily_checkin.py)                     │      │        │
│     │  │  - Generate 1-3 questions/day                │      │        │
│     │  │  - Capture responses                         │      │        │
│     │  │  - Update project state                      │      │        │
│     │  └──────────────────────────────────────────────┘      │        │
│     │                      │                                  │        │
│     │                      ▼                                  │        │
│     │  ┌──────────────────────────────────────────────┐      │        │
│     │  │      Background Task Executor                │      │        │
│     │  │   - Draft chapters (book project)            │      │        │
│     │  │   - Conduct research (MCP tools)             │      │        │
│     │  │   - Generate documents                       │      │        │
│     │  │   - Prepare next check-in                    │      │        │
│     │  └──────────────────────────────────────────────┘      │        │
│     │                      │                                  │        │
│     │                      ▼                                  │        │
│     │  ┌──────────────────────────────────────────────┐      │        │
│     │  │      Completion Detector                     │      │        │
│     │  │   - Detect all tasks complete                │      │        │
│     │  │   - Generate final deliverable               │      │        │
│     │  │   - Request user review                      │      │        │
│     │  │   - Mark project complete                    │      │        │
│     │  └──────────────────────────────────────────────┘      │        │
│     └────────────────────────────────────────────────────────┘        │
│                                                                        │
│                            Storage Layer                               │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                        Firestore                              │    │
│  │  Collections: trinity_projects, trinity_qa_sessions,          │    │
│  │               trinity_project_specs, trinity_project_plans,   │    │
│  │               trinity_daily_checkins, trinity_project_tasks   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

### Key Components

#### Component 1: ProjectInitializer
- **Purpose**: Orchestrates project initialization from YES response to approved plan
- **Responsibilities**:
  - Detect YES response from human_review_queue
  - Generate contextual Q&A questions based on pattern type
  - Conduct Q&A session with user (5-10 questions)
  - Validate answer completeness
  - Trigger spec generation
- **Dependencies**: HumanReviewQueue, PatternDetector, AgentContext, Firestore
- **Interfaces**: `initialize_project(pattern: DetectedPattern) -> Result[ProjectSession, Error]`

#### Component 2: SpecFromConversation
- **Purpose**: Transform Q&A transcript into formal specification document
- **Responsibilities**:
  - Extract requirements from conversation
  - Generate Goals, Non-Goals, User Personas sections
  - Create Acceptance Criteria from requirements
  - Format as spec.md following template
  - Store in Firestore and present for approval
- **Dependencies**: ProjectSession, GPT-5 (model_policy), Firestore, spec template
- **Interfaces**: `generate_spec(qa_session: QASession) -> Result[ProjectSpec, Error]`

#### Component 3: PlanGenerator
- **Purpose**: Create implementation plan from approved specification
- **Responsibilities**:
  - Break project into daily micro-tasks (<30 min each)
  - Define task dependencies and ordering
  - Estimate timeline (based on 1-3 questions/day model)
  - Create plan.md following template
  - Store plan in Firestore
- **Dependencies**: ProjectSpec, task_breakdown_templates, Firestore
- **Interfaces**: `generate_plan(spec: ProjectSpec) -> Result[ProjectPlan, Error]`

#### Component 4: ProjectExecutor
- **Purpose**: Manage project execution from start to completion
- **Responsibilities**:
  - Track project state (current phase, completed tasks)
  - Coordinate daily check-ins
  - Execute background tasks between check-ins
  - Detect blockers and adapt plan
  - Generate final deliverable
- **Dependencies**: ProjectPlan, DailyCheckin, BackgroundTaskExecutor, Firestore
- **Interfaces**: `execute_project(project: Project) -> Result[ProjectOutcome, Error]`

#### Component 5: DailyCheckin
- **Purpose**: Coordinate daily user interactions (1-3 questions)
- **Responsibilities**:
  - Generate check-in questions based on current phase
  - Time questions appropriately (respect quiet hours, flow state)
  - Capture responses with context
  - Update project state from responses
  - Communicate next steps clearly
- **Dependencies**: Project state, PreferenceLearning, HumanReviewQueue, Firestore
- **Interfaces**: `conduct_checkin(project: Project) -> Result[CheckinResponse, Error]`

### Data Flow
```
1. YES Response Detection
   User: "YES!" → HumanReviewQueue → ProjectInitializer triggers

2. Q&A Phase (5-10 minutes)
   ProjectInitializer → Generate questions → HumanReviewQueue → User answers
   Loop until all required questions answered → QASession complete

3. Spec Generation (<30 seconds)
   QASession → SpecFromConversation → Extract requirements → Generate spec.md
   → Store Firestore → Present to user for approval

4. User Reviews Spec (2-3 minutes)
   User reads spec → Approves/Rejects/Modifies → If approved, continue

5. Plan Generation (<60 seconds)
   ProjectSpec → PlanGenerator → Break into tasks → Estimate timeline
   → Generate plan.md → Store Firestore → Notify user

6. Daily Execution Loop (2-4 weeks typical)
   Day 1-N:
     Morning: DailyCheckin → Generate 1-3 questions → User responds (5 min)
     Background: BackgroundTaskExecutor → Execute tasks → Prepare next check-in
     Evening: Progress update (optional) → "Chapter 2 draft ready"

7. Completion Detection
   All tasks complete → CompletionDetector → Generate deliverable
   → User review → Final iteration → Mark complete

8. Learning Extraction
   ProjectOutcome → LearningAgent → Extract patterns → Store Firestore
   → Improve future Q&A templates and task breakdowns
```

---

## Data Models (Pydantic)

### Core Data Structures

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from shared.type_definitions.result import Result

class QAQuestion(BaseModel):
    """Single question in Q&A session."""
    question_id: str
    question_text: str
    question_number: int  # 1-10
    required: bool
    context: Optional[str]  # Why we're asking this

class QAAnswer(BaseModel):
    """User's answer to Q&A question."""
    question_id: str
    answer_text: str
    answered_at: datetime
    confidence: Literal["certain", "uncertain", "not_sure"]

class QASession(BaseModel):
    """Complete Q&A session."""
    session_id: str
    project_id: str
    pattern_id: str
    pattern_type: str  # "book_project", "workflow_improvement", etc.
    questions: List[QAQuestion]
    answers: List[QAAnswer]
    started_at: datetime
    completed_at: Optional[datetime]
    status: Literal["in_progress", "completed", "abandoned"]
    total_time_minutes: Optional[int]

class ProjectSpec(BaseModel):
    """Formal project specification."""
    spec_id: str
    project_id: str
    qa_session_id: str
    title: str
    goals: List[str]
    non_goals: List[str]
    user_personas: List[str]
    acceptance_criteria: List[str]
    constraints: List[str]
    spec_markdown: str  # Full spec.md content
    created_at: datetime
    approved_at: Optional[datetime]
    approval_status: Literal["pending", "approved", "rejected", "modified"]

class ProjectTask(BaseModel):
    """Single micro-task in project plan."""
    task_id: str
    project_id: str
    title: str
    description: str
    estimated_minutes: int  # <30 typical
    dependencies: List[str]  # task_ids that must complete first
    acceptance_criteria: List[str]
    assigned_to: Literal["user", "system"]  # User answers questions, system does work
    status: Literal["pending", "in_progress", "completed", "blocked"]
    completed_at: Optional[datetime]

class ProjectPlan(BaseModel):
    """Implementation plan with task breakdown."""
    plan_id: str
    project_id: str
    spec_id: str
    tasks: List[ProjectTask]
    total_estimated_days: int
    daily_questions_avg: int  # 1-3 typical
    timeline_start: datetime
    timeline_end_estimate: datetime
    plan_markdown: str  # Full plan.md content
    created_at: datetime

class CheckinQuestion(BaseModel):
    """Question asked during daily check-in."""
    question_id: str
    checkin_id: str
    project_id: str
    task_id: Optional[str]  # Related task if applicable
    question_text: str
    question_type: Literal["clarification", "decision", "feedback", "progress"]
    asked_at: datetime

class CheckinResponse(BaseModel):
    """User's response to check-in question."""
    response_id: str
    question_id: str
    response_text: str
    responded_at: datetime
    sentiment: Literal["positive", "neutral", "negative"]
    action_needed: bool  # Does this require system action?

class DailyCheckin(BaseModel):
    """Complete daily check-in interaction."""
    checkin_id: str
    project_id: str
    checkin_date: datetime
    questions: List[CheckinQuestion]
    responses: List[CheckinResponse]
    total_time_minutes: int
    next_steps: str  # What system will do next
    status: Literal["pending", "completed", "skipped"]

class ProjectState(BaseModel):
    """Current state of project execution."""
    project_id: str
    current_phase: str  # "initialization", "execution", "review", "completed"
    current_task_id: Optional[str]
    completed_task_ids: List[str]
    blocked_task_ids: List[str]
    total_tasks: int
    completed_tasks: int
    progress_percentage: int
    last_checkin_at: Optional[datetime]
    next_checkin_at: Optional[datetime]
    blockers: List[str]  # Descriptions of current blockers

class Project(BaseModel):
    """Complete project entity."""
    project_id: str
    pattern_id: str
    user_id: str
    title: str
    project_type: str  # "book", "workflow", "decision", etc.
    qa_session: QASession
    spec: ProjectSpec
    plan: ProjectPlan
    state: ProjectState
    checkins: List[DailyCheckin]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: Literal["initializing", "active", "paused", "completed", "abandoned"]

class ProjectOutcome(BaseModel):
    """Final project outcome for learning."""
    project_id: str
    completed: bool
    completion_rate: float  # 0.0-1.0
    total_time_minutes: int
    total_checkins: int
    user_satisfaction: Optional[int]  # 1-5 rating
    deliverable_quality: Optional[int]  # 1-5 rating
    blockers_encountered: List[str]
    learnings: List[str]
    would_recommend: Optional[bool]
```

---

## Agent Assignments

### Primary Agent: AgencyCodeAgent
- **Role**: Implement all Phase 3 components (primary developer)
- **Tasks**:
  - Create all data models (models/project.py, models/qa_session.py, etc.)
  - Implement ProjectInitializer with Q&A generation logic
  - Implement SpecFromConversation with LLM integration
  - Implement PlanGenerator with task breakdown logic
  - Implement ProjectExecutor orchestration
  - Implement DailyCheckin coordinator
  - Integrate with existing Phase 1-2 systems
  - Ensure 100% type safety (zero Dict[Any])
  - Follow Result<T,E> pattern for all error handling
- **Tools Required**: Read, Write, Edit, MultiEdit, Bash (tests), Grep, Glob
- **Deliverables**:
  - `trinity_protocol/project_initializer.py` (~400 lines)
  - `trinity_protocol/spec_from_conversation.py` (~350 lines)
  - `trinity_protocol/plan_generator.py` (~300 lines)
  - `trinity_protocol/project_executor.py` (~450 lines)
  - `trinity_protocol/daily_checkin.py` (~300 lines)
  - `trinity_protocol/models/project.py` (~400 lines)
  - `trinity_protocol/models/qa_session.py` (~200 lines)

### Supporting Agent: TestGeneratorAgent
- **Role**: Generate comprehensive test suite for Phase 3
- **Tasks**:
  - Create unit tests for each component (60+ tests)
  - Create integration tests for end-to-end flows (40+ tests)
  - Create E2E tests for complete project lifecycle (10+ tests)
  - Create constitutional compliance tests (20+ tests)
  - Mock Firestore for deterministic testing
  - Mock LLM responses for reproducibility
- **Tools Required**: Write, Bash (pytest execution), TodoWrite (track coverage)
- **Deliverables**:
  - `tests/trinity_protocol/test_project_initializer.py` (~30 tests)
  - `tests/trinity_protocol/test_spec_from_conversation.py` (~20 tests)
  - `tests/trinity_protocol/test_plan_generator.py` (~20 tests)
  - `tests/trinity_protocol/test_project_executor.py` (~30 tests)
  - `tests/trinity_protocol/test_daily_checkin.py` (~25 tests)
  - `tests/trinity_protocol/test_project_integration.py` (~40 tests)
  - `tests/trinity_protocol/test_phase3_e2e.py` (~10 tests)

### Supporting Agent: ToolsmithAgent
- **Role**: Implement real-world tools for background task execution
- **Tasks**:
  - Create MCP web research tool integration
  - Create document generation tool (book chapters, outlines)
  - Create calendar management tool (focus blocks scheduling)
  - Ensure TDD approach (tests before implementation)
  - Follow tool API design patterns
- **Tools Required**: Read, Write, Bash, TodoWrite
- **Deliverables**:
  - `tools/web_research.py` (~250 lines)
  - `tools/document_generator.py` (~300 lines)
  - `tools/calendar_manager.py` (~200 lines)
  - `tests/tools/test_web_research.py` (~25 tests)
  - `tests/tools/test_document_generator.py` (~25 tests)
  - `tests/tools/test_calendar_manager.py` (~20 tests)

### Supporting Agent: QualityEnforcerAgent
- **Role**: Validate constitutional compliance throughout implementation
- **Tasks**:
  - Run constitution checks on all new code
  - Verify zero Dict[Any] violations
  - Validate all functions <50 lines
  - Ensure Result<T,E> pattern usage
  - Trigger autonomous healing if violations detected
- **Tools Required**: AnalyzeTypePatterns, ConstitutionCheck, Bash, AutoFixNoneType
- **Deliverables**: Constitutional compliance report, any auto-fixes applied

### Supporting Agent: ChiefArchitectAgent
- **Role**: Provide architectural guidance and create ADR
- **Tasks**:
  - Review initial architecture design
  - Create ADR-017 for Phase 3 architectural decisions
  - Validate integration points with Phase 1-2
  - Approve final architecture before implementation
- **Tools Required**: Write, Read
- **Deliverables**: `docs/adr/ADR-017-phase3-project-execution.md`

### Agent Communication Flow
```
1. ChiefArchitect → Create ADR → AgencyCodeAgent (architecture approved)
2. AgencyCodeAgent → Implement core components → TestGeneratorAgent (code ready)
3. TestGeneratorAgent → Generate tests → AgencyCodeAgent (tests available)
4. ToolsmithAgent → Implement tools (parallel) → AgencyCodeAgent (tools ready)
5. QualityEnforcer → Validate compliance → AgencyCodeAgent (fixes if needed)
6. AgencyCodeAgent → Final integration → All agents (complete)
```

---

## Implementation Strategy

### Development Phases

#### Phase 3.1: Foundation & Data Models (Days 1-2)
**Duration**: 2 days
**Agents**: ChiefArchitect, AgencyCodeAgent
**Deliverables**:
- [ ] ADR-017 created and approved
- [ ] All Pydantic models implemented (models/project.py, models/qa_session.py)
- [ ] Firestore schema designed and documented
- [ ] ProjectStateManager for persistence implemented
- [ ] Unit tests for data models (20 tests minimum)

**Tasks**:
1. TASK-3.1.1: ChiefArchitect creates ADR-017 (Phase 3 architecture) - 4 hours
2. TASK-3.1.2: AgencyCodeAgent implements Project Pydantic models - 3 hours
3. TASK-3.1.3: AgencyCodeAgent implements QASession models - 2 hours
4. TASK-3.1.4: AgencyCodeAgent implements ProjectState manager with Firestore - 4 hours
5. TASK-3.1.5: TestGeneratorAgent creates model unit tests - 3 hours

#### Phase 3.2: Project Initialization (Days 3-5)
**Duration**: 3 days
**Agents**: AgencyCodeAgent, TestGeneratorAgent
**Deliverables**:
- [ ] ProjectInitializer implemented (Q&A orchestration)
- [ ] SpecFromConversation implemented (spec generation)
- [ ] PlanGenerator implemented (task breakdown)
- [ ] Integration with HumanReviewQueue
- [ ] Unit tests (40 tests) and integration tests (15 tests)

**Tasks**:
1. TASK-3.2.1: AgencyCodeAgent implements ProjectInitializer core - 6 hours
2. TASK-3.2.2: AgencyCodeAgent implements Q&A generation logic - 4 hours
3. TASK-3.2.3: AgencyCodeAgent implements SpecFromConversation - 5 hours
4. TASK-3.2.4: AgencyCodeAgent implements PlanGenerator - 5 hours
5. TASK-3.2.5: AgencyCodeAgent integrates with HumanReviewQueue - 3 hours
6. TASK-3.2.6: TestGeneratorAgent creates initialization tests - 6 hours

#### Phase 3.3: Daily Check-in System (Days 6-8)
**Duration**: 3 days
**Agents**: AgencyCodeAgent, TestGeneratorAgent
**Deliverables**:
- [ ] DailyCheckin coordinator implemented
- [ ] Question generation based on project phase
- [ ] Timing intelligence (quiet hours, flow state respect)
- [ ] Response handling and state updates
- [ ] Unit tests (25 tests) and integration tests (15 tests)

**Tasks**:
1. TASK-3.3.1: AgencyCodeAgent implements DailyCheckin coordinator - 5 hours
2. TASK-3.3.2: AgencyCodeAgent implements check-in question generation - 4 hours
3. TASK-3.3.3: AgencyCodeAgent integrates timing intelligence from Phase 2 - 3 hours
4. TASK-3.3.4: AgencyCodeAgent implements response handling - 3 hours
5. TASK-3.3.5: AgencyCodeAgent implements state updates from responses - 3 hours
6. TASK-3.3.6: TestGeneratorAgent creates check-in tests - 5 hours

#### Phase 3.4: Project Executor (Days 9-11)
**Duration**: 3 days
**Agents**: AgencyCodeAgent, ToolsmithAgent, TestGeneratorAgent
**Deliverables**:
- [ ] ProjectExecutor orchestration implemented
- [ ] Background task execution framework
- [ ] Completion detection logic
- [ ] Real-world tools (web research, document generation)
- [ ] Unit tests (30 tests) and E2E tests (10 tests)

**Tasks**:
1. TASK-3.4.1: AgencyCodeAgent implements ProjectExecutor core - 6 hours
2. TASK-3.4.2: AgencyCodeAgent implements background task framework - 5 hours
3. TASK-3.4.3: AgencyCodeAgent implements completion detection - 3 hours
4. TASK-3.4.4: ToolsmithAgent implements web research tool - 4 hours
5. TASK-3.4.5: ToolsmithAgent implements document generator - 5 hours
6. TASK-3.4.6: TestGeneratorAgent creates executor and E2E tests - 8 hours

#### Phase 3.5: Integration & Validation (Days 12-14)
**Duration**: 3 days
**Agents**: AgencyCodeAgent, QualityEnforcer, TestGeneratorAgent
**Deliverables**:
- [ ] End-to-end integration with Phase 1-2 systems
- [ ] Full regression testing (Phase 1-2 tests still pass)
- [ ] Constitutional compliance validation (all 5 articles)
- [ ] Demo scripts (demo_project_initialization.py)
- [ ] Documentation (PHASE_3_IMPLEMENTATION_SUMMARY.md)

**Tasks**:
1. TASK-3.5.1: AgencyCodeAgent integrates with WITNESS/ARCHITECT - 4 hours
2. TASK-3.5.2: AgencyCodeAgent creates demo script - 3 hours
3. TASK-3.5.3: TestGeneratorAgent runs full regression tests - 2 hours
4. TASK-3.5.4: QualityEnforcer validates constitutional compliance - 2 hours
5. TASK-3.5.5: AgencyCodeAgent creates implementation summary - 3 hours
6. TASK-3.5.6: AgencyCodeAgent fixes any issues found - 4 hours

### File Structure Plan
```
trinity_protocol/
├── project_initializer.py          # Orchestrates YES → spec → plan
├── spec_from_conversation.py       # Q&A → formal spec.md
├── plan_generator.py               # Spec → task breakdown → plan.md
├── project_executor.py             # Manages project execution lifecycle
├── daily_checkin.py                # Coordinates 1-3 questions/day
├── project_state_manager.py        # Firestore persistence for projects
├── models/
│   ├── project.py                  # Project, ProjectState, ProjectOutcome
│   ├── qa_session.py               # QASession, QAQuestion, QAAnswer
│   ├── project_spec.py             # ProjectSpec model
│   ├── project_plan.py             # ProjectPlan, ProjectTask models
│   └── daily_checkin.py            # DailyCheckin, CheckinQuestion/Response
├── templates/
│   ├── qa_templates/
│   │   ├── book_project.json       # Book project Q&A template
│   │   ├── workflow.json           # Workflow improvement template
│   │   └── decision.json           # Decision framework template
│   ├── spec_template.md            # Spec generation template
│   └── plan_template.md            # Plan generation template
└── PHASE_3_IMPLEMENTATION_SUMMARY.md

tests/trinity_protocol/
├── test_project_initializer.py     # 30 tests
├── test_spec_from_conversation.py  # 20 tests
├── test_plan_generator.py          # 20 tests
├── test_project_executor.py        # 30 tests
├── test_daily_checkin.py           # 25 tests
├── test_project_state_manager.py   # 15 tests
├── test_project_integration.py     # 40 integration tests
├── test_phase3_e2e.py              # 10 E2E tests (full project lifecycle)
└── fixtures/
    ├── mock_qa_sessions.json       # Mock Q&A data
    ├── mock_projects.json          # Mock project states
    └── mock_llm_responses.json     # Deterministic LLM outputs

tools/
├── web_research.py                 # MCP firecrawl integration
├── document_generator.py           # Book chapters, outlines
├── calendar_manager.py             # Focus blocks scheduling
└── real_world_actions.py           # Generic external actions

tests/tools/
├── test_web_research.py            # 25 tests
├── test_document_generator.py      # 25 tests
└── test_calendar_manager.py        # 20 tests

docs/adr/
└── ADR-017-phase3-project-execution.md
```

---

## Quality Assurance Strategy

### Testing Framework

#### Unit Testing (80+ tests)
- **Framework**: pytest (existing Trinity test infrastructure)
- **Coverage Target**: 100% (Constitutional requirement)
- **Test Categories**:
  - **Data Models** (20 tests): Pydantic validation, field constraints, serialization
  - **ProjectInitializer** (30 tests): Q&A generation, answer validation, session management
  - **SpecFromConversation** (20 tests): Requirement extraction, spec formatting, template rendering
  - **PlanGenerator** (20 tests): Task breakdown, dependency resolution, timeline estimation
  - **DailyCheckin** (25 tests): Question generation, timing logic, response handling
  - **ProjectExecutor** (30 tests): State management, background tasks, completion detection

#### Integration Testing (40 tests)
- **Framework**: pytest with Firestore emulator
- **Test Scenarios**:
  - **Initialization Flow** (15 tests): YES → Q&A → spec → plan end-to-end
  - **Execution Flow** (15 tests): Daily check-ins → state updates → completion
  - **Phase 1-2 Integration** (10 tests): WITNESS → ARCHITECT → ProjectInitializer

#### End-to-End Testing (10 tests)
- **Framework**: pytest with full Trinity stack
- **Test Scenarios**:
  - **Complete Book Project** (3 tests): Full lifecycle from pattern detection to book delivery
  - **Project Abandonment** (2 tests): User stops responding, graceful handling
  - **Plan Modification** (2 tests): User requests changes mid-project
  - **Multiple Projects** (3 tests): Sequential projects, state isolation

#### Constitutional Compliance Testing (20 tests)
- **Article I**: Complete context before action (5 tests)
  - No partial Q&A transcripts used for spec generation
  - All timeout handling with retry
  - Complete answers required before proceeding

- **Article II**: 100% verification and stability (5 tests)
  - All Phase 3 tests pass
  - Integration with Phase 1-2 maintains existing pass rate
  - No test deactivation or weakening

- **Article IV**: Continuous learning (5 tests)
  - Project outcomes logged to Firestore
  - Learnings extracted and stored
  - Q&A templates improve over time

- **Article V**: Spec-driven development (5 tests)
  - Implementation matches this specification
  - Requirements traceability validated

### Quality Gates
- [ ] **Code Review**: Manual review by QualityEnforcer
- [ ] **Test Coverage**: 100% coverage achieved (130+ tests passing)
- [ ] **Performance**: All operations meet latency requirements
- [ ] **Constitutional**: Zero violations detected (no Dict[Any], all functions <50 lines)
- [ ] **Integration**: Phase 1-2 tests still pass (no regression)

---

## Contracts & Interfaces

### Core Interfaces

#### ProjectInitializer Interface
```python
class ProjectInitializer:
    """Orchestrates project initialization from YES response."""

    async def initialize_project(
        self,
        pattern: DetectedPattern,
        user_response: UserResponse
    ) -> Result[ProjectSession, InitializationError]:
        """
        Start project initialization from YES response.

        Returns: ProjectSession with Q&A in progress or Error
        """

    async def generate_questions(
        self,
        pattern: DetectedPattern,
        session: ProjectSession
    ) -> Result[List[QAQuestion], QuestionGenerationError]:
        """
        Generate 5-10 contextual questions for project type.

        Returns: List of questions or Error
        """

    async def conduct_qa_session(
        self,
        session: ProjectSession
    ) -> Result[QASession, SessionError]:
        """
        Conduct Q&A session with user until complete.

        Returns: Completed QASession or Error
        """

    async def validate_qa_completeness(
        self,
        session: QASession
    ) -> Result[bool, ValidationError]:
        """
        Validate all required questions answered.

        Returns: True if complete, False if missing answers, or Error
        """
```

#### SpecFromConversation Interface
```python
class SpecFromConversation:
    """Generate formal specification from Q&A transcript."""

    async def generate_spec(
        self,
        qa_session: QASession
    ) -> Result[ProjectSpec, SpecGenerationError]:
        """
        Create formal spec.md from conversation.

        Returns: ProjectSpec ready for approval or Error
        """

    async def extract_requirements(
        self,
        qa_session: QASession
    ) -> Result[Requirements, ExtractionError]:
        """
        Extract Goals, Non-Goals, Acceptance Criteria from answers.

        Returns: Structured requirements or Error
        """

    async def request_spec_approval(
        self,
        spec: ProjectSpec
    ) -> Result[ApprovalResponse, ApprovalError]:
        """
        Present spec to user for approval.

        Returns: Approved/Rejected/Modified response or Error
        """
```

#### PlanGenerator Interface
```python
class PlanGenerator:
    """Create implementation plan from specification."""

    async def generate_plan(
        self,
        spec: ProjectSpec
    ) -> Result[ProjectPlan, PlanGenerationError]:
        """
        Break spec into daily micro-tasks with dependencies.

        Returns: ProjectPlan with task breakdown or Error
        """

    async def break_into_tasks(
        self,
        spec: ProjectSpec
    ) -> Result[List[ProjectTask], TaskBreakdownError]:
        """
        Decompose project into <30 minute micro-tasks.

        Returns: List of tasks with dependencies or Error
        """

    async def estimate_timeline(
        self,
        tasks: List[ProjectTask]
    ) -> Result[TimelineEstimate, EstimationError]:
        """
        Estimate completion timeline (1-3 questions/day model).

        Returns: Timeline with start/end dates or Error
        """
```

#### DailyCheckin Interface
```python
class DailyCheckin:
    """Coordinate daily user interactions."""

    async def conduct_checkin(
        self,
        project: Project
    ) -> Result[CheckinResponse, CheckinError]:
        """
        Execute daily check-in (1-3 questions).

        Returns: User responses with next steps or Error
        """

    async def generate_checkin_questions(
        self,
        project: Project
    ) -> Result[List[CheckinQuestion], QuestionGenerationError]:
        """
        Generate 1-3 questions for current project phase.

        Returns: List of questions or Error
        """

    async def time_checkin_appropriately(
        self,
        project: Project
    ) -> Result[datetime, TimingError]:
        """
        Determine best time for check-in (respect preferences).

        Returns: Optimal check-in time or Error
        """

    async def update_project_from_responses(
        self,
        project: Project,
        responses: List[CheckinResponse]
    ) -> Result[ProjectState, UpdateError]:
        """
        Update project state based on user responses.

        Returns: Updated project state or Error
        """
```

#### ProjectExecutor Interface
```python
class ProjectExecutor:
    """Manage complete project execution lifecycle."""

    async def execute_project(
        self,
        project: Project
    ) -> Result[ProjectOutcome, ExecutionError]:
        """
        Execute project from start to completion.

        Returns: ProjectOutcome with metrics or Error
        """

    async def execute_background_tasks(
        self,
        project: Project,
        tasks: List[ProjectTask]
    ) -> Result[List[TaskResult], TaskExecutionError]:
        """
        Execute background work between check-ins.

        Returns: Task results or Error
        """

    async def detect_completion(
        self,
        project: Project
    ) -> Result[bool, DetectionError]:
        """
        Detect when all tasks complete.

        Returns: True if complete, False if in progress, or Error
        """

    async def generate_deliverable(
        self,
        project: Project
    ) -> Result[Deliverable, DeliverableError]:
        """
        Generate final project deliverable (book, report, etc.).

        Returns: Deliverable ready for user review or Error
        """
```

---

## Risk Mitigation

### Technical Risks

#### Risk 1: Q&A takes >10 minutes (user abandons)
- **Probability**: Medium
- **Impact**: High (feature unusable if setup too long)
- **Mitigation Strategy**:
  - Hard limit 10 questions maximum
  - Show progress indicator ("Question 3 of 7")
  - Show time estimate upfront ("~5 minutes")
  - Allow "skip" or "not sure" answers for optional questions
  - Adaptive questioning (stop early if enough info gathered)
- **Contingency Plan**: If >10 minutes in testing, reduce to 5 questions and make spec generation more robust with less info

#### Risk 2: Generated specs too generic (not personalized)
- **Probability**: Medium
- **Impact**: High (user rejects spec, loses trust)
- **Mitigation Strategy**:
  - Use user's exact phrasing from answers
  - Reference specific examples they provided
  - Include direct quotes from conversation
  - Validation step shows spec to user before proceeding
- **Contingency Plan**: Allow user to modify spec before approval, learn from modifications

#### Risk 3: Firestore latency impacts UX (>1s delays)
- **Probability**: Low
- **Impact**: Medium (user perceives as slow)
- **Mitigation Strategy**:
  - Local caching for project state
  - SQLite fallback if Firestore unavailable
  - Async operations with loading indicators
  - Batch Firestore operations where possible
- **Contingency Plan**: Implement aggressive local caching, sync to Firestore in background

#### Risk 4: LLM hallucination in spec/plan generation
- **Probability**: Medium
- **Impact**: High (wrong specs lead to wrong outcomes)
- **Mitigation Strategy**:
  - Use structured output from LLM (Pydantic validation)
  - Ground generation in Q&A transcript (no external knowledge)
  - User approval required before proceeding
  - Validation checks for consistency (goals match acceptance criteria)
- **Contingency Plan**: Add human-in-loop validation step, allow spec editing

### Operational Risks

#### Risk 5: Daily check-ins feel annoying
- **Probability**: Medium
- **Impact**: High (user stops responding, project stalls)
- **Mitigation Strategy**:
  - Apply Phase 2 learnings (timing, acceptance rates)
  - Strict 1-3 questions/day limit
  - Respect quiet hours from preference learning
  - Batch questions together (not separate interruptions)
  - User can snooze or skip check-ins
- **Contingency Plan**: Reduce to 1 question/day, increase to 2-3 only if user engagement high

#### Risk 6: Projects stall halfway through
- **Probability**: Medium
- **Impact**: Medium (incomplete projects, wasted effort)
- **Mitigation Strategy**:
  - Detect stagnation (no responses for 3 days)
  - Offer to adjust plan or pause project
  - Ask if project still relevant (priorities change)
  - Graceful pause/resume capability
- **Contingency Plan**: Auto-pause after 7 days no response, easy resume when user returns

### Constitutional Risks

#### Risk 7: Partial Q&A used for spec (Article I violation)
- **Probability**: Low
- **Impact**: Critical (constitutional violation)
- **Mitigation Strategy**:
  - State machine ensures all required questions answered
  - Explicit validation before spec generation
  - No "skip ahead" functionality
  - Tests verify completeness requirement enforced
- **Monitoring**: Constitutional compliance tests fail if violation detected

#### Risk 8: Test failures ignored to meet timeline (Article II violation)
- **Probability**: Low
- **Impact**: Critical (constitutional violation)
- **Mitigation Strategy**:
  - QualityEnforcer blocks merge if tests fail
  - Autonomous healing for common failures
  - Timeline includes buffer for fixes
  - Definition of Done includes "all tests pass"
- **Monitoring**: CI pipeline enforces 100% pass rate

---

## Performance Considerations

### Performance Requirements
- **Q&A Question Generation**: <2 seconds per question (user waiting)
- **Spec Generation**: <30 seconds (acceptable wait with loading indicator)
- **Plan Generation**: <60 seconds (acceptable wait)
- **Daily Check-in Questions**: <5 seconds (user waiting)
- **Firestore Operations**: <500ms average (reads/writes)
- **Background Task Execution**: No time limit (happens while user offline)

### Optimization Strategy
- **LLM Caching**: Cache similar Q&A templates to avoid repeated generation
- **Firestore Batching**: Batch reads/writes to reduce round-trips
- **Async Operations**: Use asyncio for all I/O operations
- **Lazy Loading**: Load project history only when needed
- **Pre-generation**: Generate next check-in questions in background

### Monitoring & Metrics
- **Latency Metrics**: p50, p95, p99 for all operations
- **Success Rates**: % of projects that complete
- **User Time**: Average time per Q&A, per check-in
- **Engagement**: Response rate to check-ins
- **Quality**: User satisfaction ratings

---

## Learning Integration

### Learning Opportunities
- **Pattern 1**: Which question types yield most useful answers (optimize Q&A)
- **Pattern 2**: Which project types complete most often (success indicators)
- **Pattern 3**: At what point do projects typically stall (intervention triggers)
- **Pattern 4**: Which daily question types get best responses (question quality)

### Historical Learning Application
- **Applied Learning 1**: Phase 2 acceptance rate data informs check-in timing
- **Applied Learning 2**: Preference learning data determines quiet hours
- **Applied Learning 3**: Pattern detection thresholds inform project opportunity detection

### Learning Extraction Plan
- **Extract 1**: After each completed project, analyze what made it successful
- **Extract 2**: After abandoned projects, analyze stall points and user feedback
- **Extract 3**: Quarterly analysis of question quality vs user satisfaction

---

## Monitoring & Observability

### Implementation Monitoring
- **Progress Tracking**: TodoWrite tool for task breakdown and completion
- **Quality Metrics**: Test pass rate, constitutional compliance checks
- **Performance Metrics**: Test execution time, latency measurements

### Post-Implementation Monitoring
- **Success Metrics**: Project completion rate, user satisfaction, time investment
- **Health Checks**: Daily cron checks project state consistency
- **Alerting**: Notify if >3 days no check-in responses (stalled project)

---

## Documentation Plan

### User Documentation
- **Phase 3 User Guide**: How to use project initialization, what to expect
- **FAQ**: Common questions about project setup, check-ins, completion

### Technical Documentation
- **Architecture Doc**: `docs/adr/ADR-017-phase3-project-execution.md`
- **Integration Guide**: `trinity_protocol/PHASE_3_IMPLEMENTATION_SUMMARY.md`
- **API Reference**: Docstrings for all public interfaces

---

## Review & Approval

### Technical Review Checklist
- [x] **Architecture**: Sound design with clear component boundaries
- [x] **Implementation**: Feasible with 2-week timeline and available agents
- [x] **Quality**: 100% test coverage planned, constitutional compliance validated
- [x] **Performance**: Latency requirements realistic (<2s questions, <30s specs)
- [x] **Integration**: Clear integration points with Phase 1-2 systems
- [x] **Constitutional**: All 5 articles addressed in design and testing

### Approval Status
- [ ] **Technical Lead Approval**: Pending Alex review
- [ ] **Architecture Review**: Pending ChiefArchitect review
- [ ] **Constitutional Compliance**: Pending QualityEnforcer review
- [ ] **Final Approval**: Pending after all reviews complete

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-01 | Planner Agent | Initial technical plan for Phase 3 |

---

*"The best plans are detailed enough to execute autonomously, flexible enough to adapt when reality intervenes."*
