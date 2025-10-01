# ADR-017: Phase 3 Project Execution Architecture for Trinity Life Assistant

## Status
**Accepted**

## Date
2025-10-01

## Context

### Background

Trinity Life Assistant has successfully completed Phases 1 and 2, establishing a robust foundation for ambient intelligence and proactive assistance:

**Phase 1 (Complete)**: Ambient Intelligence
- Local audio capture and Whisper AI transcription
- Pattern detection across 6 categories (recurring topics, projects, frustrations, action items, feature requests, bottlenecks)
- Privacy-first design with 100% on-device processing
- Foundation safety systems (green main verification, budget enforcement, message persistence)

**Phase 2 (Complete)**: Proactive Assistance
- Question engine with low-stakes and high-value question types
- Human-in-the-loop protocol for YES/NO/LATER responses
- Preference learning system (85% accuracy in demo)
- Rate limiting and timing intelligence

### Problem Statement

**Current Gap**: Trinity can listen, understand patterns, and ask thoughtful questions, but cannot execute on user approval. When a user says "YES" to "Want help finishing your book?", the system has no mechanism to:

1. Convert verbal conversation into structured project specification
2. Initialize project state with deliverables, milestones, and daily tasks
3. Execute real-world actions (web research, document generation, calendar management)
4. Coordinate daily check-ins with 1-3 questions to advance the project
5. Track project state across sessions with persistent storage
6. Adapt execution based on user feedback

**User Need**: Professionals (coaches, engineers, healthcare workers) need an assistant that can manage long-running projects (book writing, course creation, system refactoring) with minimal daily time investment (5-10 minutes) while maintaining full user control and constitutional compliance.

**Technical Challenge**: Build a project execution engine that:
- Transforms conversational context into formal specifications
- Manages project lifecycle from initialization to completion
- Integrates real-world tools beyond code (web research, documents, calendar)
- Operates within budget constraints ($30/day hard limit)
- Maintains constitutional compliance (complete context, 100% verification, spec-driven)
- Enables cross-session project continuity via Firestore

### Requirements

**Functional Requirements**:
- Project initialization through conversational Q&A (5-10 questions)
- Automatic spec generation from conversation transcripts
- User approval workflow before project execution begins
- Daily check-in coordination (1-3 questions maximum)
- Micro-task breakdown for daily scope management
- Real-world tool integration (web research, document generation, calendar)
- Project state persistence across Trinity restarts
- Progress tracking and milestone verification

**Non-Functional Requirements**:
- Performance: <30s for spec generation, <5s for daily check-in formulation
- Reliability: 99% project state persistence, graceful degradation on tool failures
- Cost: Project execution within budget enforcer limits ($30/day)
- Privacy: All project data encrypted at rest, user control over deletion
- User Experience: Minimal interruption (max 3 questions/day), clear value articulation

**Constitutional Requirements**:
- Article I: Complete context (read all conversation history before generating spec)
- Article II: 100% verification (all project components tested with NECESSARY pattern)
- Article III: Automated enforcement (budget enforcer blocks excessive tool usage)
- Article IV: Continuous learning (preference data informs question timing and topics)
- Article V: Spec-driven (project initialization creates formal spec.md)

## Decision

We will implement a **Spec-Driven Project Execution Engine** with the following architecture:

### 1. Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 3: Project Execution                    │
│                     (trinity_protocol/)                           │
└─────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
   ┌──────────────────┐ ┌──────────────┐ ┌────────────────┐
   │    Project       │ │   Project    │ │  Daily Checkin │
   │  Initializer     │ │   Executor   │ │  Coordinator   │
   │ (conversation→   │ │ (micro-task  │ │ (1-3 questions │
   │  spec)           │ │  management) │ │  per day)      │
   └──────────────────┘ └──────────────┘ └────────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌────────────────────┐
                    │  Real-World Tools  │
                    │ - Web Research     │
                    │ - Document Gen     │
                    │ - Calendar Mgmt    │
                    └────────────────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │ Firestore Persistence │
                    │ (Project State)    │
                    └────────────────────┘
```

### 2. Key Architectural Decisions

#### Decision 1: Project State Management via Firestore

**Technology**: Firestore for persistent project state storage

**Rationale**:
- Cross-session persistence: Projects survive Trinity restarts and system reboots
- Real-time sync: Multiple devices can access project state
- Structured queries: Find active projects, filter by status, search by topic
- Scalability: Handles hundreds of concurrent projects without performance degradation
- Proven in production: Phases 1-2 validated Firestore reliability (179 documents stored)

**Alternative Considered**: Local SQLite database
- **Pros**: No external dependencies, zero network latency, simpler setup
- **Cons**: No cross-session sync across devices, lost on disk failure, requires manual backup strategy
- **Why Rejected**: Cross-session persistence is critical for life assistant use case (book project spans weeks)

**Implementation Pattern**:
```python
from shared.type_definitions.result import Result, Ok, Err
from trinity_protocol.models.project import ProjectState
from google.cloud import firestore

class ProjectStateStore:
    def __init__(self, firestore_client: firestore.Client):
        self.db = firestore_client
        self.collection = self.db.collection("trinity_projects")

    def store_project(self, project: ProjectState) -> Result[str, str]:
        """Store project state with automatic versioning."""
        try:
            doc_ref = self.collection.document(project.project_id)
            doc_ref.set(project.dict())
            return Ok(project.project_id)
        except Exception as e:
            return Err(f"Failed to store project: {str(e)}")

    def get_active_projects(self) -> Result[list[ProjectState], str]:
        """Retrieve all active projects for daily check-in."""
        try:
            docs = self.collection.where("status", "==", "active").stream()
            projects = [ProjectState(**doc.to_dict()) for doc in docs]
            return Ok(projects)
        except Exception as e:
            return Err(f"Failed to retrieve projects: {str(e)}")
```

#### Decision 2: Conversation → Spec Conversion via LLM

**Technology**: GPT-5 powered Q&A to structured spec generation

**Rationale**:
- Leverages GPT-5 intelligence for context understanding vs brittle rule-based parsing
- Handles ambiguity in conversational input (user says "a book" → spec clarifies "non-fiction coaching book, 150 pages")
- Extracts implicit requirements (user mentions "clients" → infers target audience)
- Validates completeness (detects missing information, asks follow-up questions)

**Alternative Considered**: Rule-based template filling
- **Pros**: Predictable output, faster execution, no LLM cost
- **Cons**: Cannot handle ambiguity, misses implicit context, requires rigid question structure
- **Why Rejected**: User conversations are naturally unstructured; rule-based parser would fail on real input

**Implementation Pattern**:
```python
from shared.type_definitions.result import Result, Ok, Err
from trinity_protocol.models.project import ProjectSpec
from typing import List

class SpecFromConversation:
    def __init__(self, llm_client):
        self.llm = llm_client

    async def generate_spec(
        self,
        conversation_history: List[str],
        pattern_context: str
    ) -> Result[ProjectSpec, str]:
        """Convert conversation to formal specification."""
        prompt = f"""
        User has approved assistance with a project. Generate a formal specification.

        Conversation History:
        {chr(10).join(conversation_history)}

        Pattern Context: {pattern_context}

        Generate a ProjectSpec with:
        - Title and description
        - Goals (3-5 specific outcomes)
        - Deliverables (tangible artifacts)
        - Success criteria (verifiable metrics)
        - Timeline estimate
        - Daily time commitment

        Ensure completeness. Flag missing information.
        """

        response = await self.llm.generate(prompt, response_model=ProjectSpec)

        if response.has_missing_information:
            return Err(f"Missing information: {response.missing_fields}")

        return Ok(response.spec)
```

**Quality Gate**: User approval required before proceeding
- Spec displayed in human-readable format
- User can request modifications
- Execution blocked until explicit approval

#### Decision 3: Daily Check-in Coordination with Preference Learning

**Strategy**: 1-3 questions/day maximum, batch delivery based on preference data

**Rationale**:
- Minimizes interruption: Batching 3 questions together vs 3 separate notifications reduces cognitive load
- Preference-informed timing: Leverages learning system data (85% acceptance in morning) to schedule optimal delivery
- Value-focused: Each question articulates impact ("This unblocks Chapter 2 writing tonight")
- Respects quiet hours: Never interrupt 22:00-08:00 or during focus blocks

**Alternative Considered**: Continuous interruption model (ask whenever needed)
- **Pros**: Faster project velocity, immediate clarification
- **Cons**: Annoys users, breaks flow state, high rejection rate (contradicts preference learning)
- **Why Rejected**: User satisfaction requires thoughtful interruption strategy

**Implementation Pattern**:
```python
from trinity_protocol.preference_learning import PreferenceLearner
from trinity_protocol.models.hitl import QuestionBatch

class DailyCheckinCoordinator:
    def __init__(
        self,
        preference_learner: PreferenceLearner,
        response_handler: ResponseHandler
    ):
        self.preferences = preference_learner
        self.response_handler = response_handler

    async def coordinate_checkin(
        self,
        project: ProjectState
    ) -> Result[QuestionBatch, str]:
        """Formulate and schedule daily check-in questions."""

        # Generate questions based on project state
        questions = self._generate_questions(project)

        # Apply preference learning for timing
        optimal_time = self.preferences.get_optimal_time(
            topic=project.topic,
            question_type="high_value"
        )

        # Batch questions (max 3)
        batch = QuestionBatch(
            questions=questions[:3],
            scheduled_time=optimal_time,
            project_id=project.project_id,
            articulates_value=True
        )

        return Ok(batch)
```

#### Decision 4: Micro-Task Breakdown for Daily Scope

**Strategy**: Decompose projects into daily-sized tasks vs full project plan upfront

**Rationale**:
- Enables adaptation: User feedback on Day 1 informs Day 2 tasks (vs locked-in plan)
- Reduces planning overhead: Focus on next 24 hours, not entire 2-week project
- Aligns with constitutional Article I (complete context): Have full context for today's work before planning tomorrow
- Matches user mental model: "What should I focus on today?" vs "Here's a 50-step plan"

**Alternative Considered**: Waterfall planning (complete project plan upfront)
- **Pros**: Clear roadmap, easier progress tracking, predictable timeline
- **Cons**: Brittle to changes, planning overhead, violates Article I (incomplete future context)
- **Why Rejected**: Real projects require adaptation; waterfall planning fails when requirements evolve

**Implementation Pattern**:
```python
from trinity_protocol.models.project import DailyTask, ProjectState

class ProjectExecutor:
    async def plan_daily_tasks(
        self,
        project: ProjectState,
        yesterday_feedback: Optional[str]
    ) -> Result[List[DailyTask], str]:
        """Plan next 24 hours of work based on current state."""

        # Constitutional Article I: Complete context before planning
        context = await self._gather_complete_context(
            project,
            yesterday_feedback
        )

        # Generate 2-4 daily tasks (each ~2-3 hours max)
        tasks = await self.llm.generate(
            prompt=f"Plan today's tasks for {project.title}. "
                   f"Context: {context}. "
                   f"Limit: 2-4 tasks, each completable in 2-3 hours.",
            response_model=List[DailyTask]
        )

        return Ok(tasks)
```

#### Decision 5: Real-World Tool Integration via MCP Protocol

**Technology**: Model Context Protocol (MCP) for external tool integration

**Rationale**:
- Standard integration pattern: MCP used successfully in Phase 1-2 for firecrawl web research
- Future extensibility: Adding new tools (Notion, Google Calendar, Slack) follows same pattern
- Safety boundaries: Tools wrapped in Result<T,E> pattern with error handling
- Budget enforcement: All tool usage metered by budget enforcer

**Alternative Considered**: Direct API integration per tool
- **Pros**: More control, fewer abstraction layers, potentially faster
- **Cons**: No standardization, each tool requires custom integration, harder to enforce safety
- **Why Rejected**: MCP provides consistent interface for tool safety and budget control

**Implementation Pattern**:
```python
# tools/web_research.py
from shared.type_definitions.result import Result, Ok, Err
from trinity_protocol.budget_enforcer import BudgetEnforcer

class WebResearchTool:
    def __init__(self, mcp_client, budget_enforcer: BudgetEnforcer):
        self.mcp = mcp_client
        self.budget = budget_enforcer

    async def research_topic(
        self,
        topic: str,
        max_results: int = 5
    ) -> Result[List[ResearchResult], str]:
        """Research topic using MCP firecrawl integration."""

        # Budget check before expensive operation
        cost_estimate = 0.50  # $0.50 per research call
        if not self.budget.check_available(cost_estimate):
            return Err("Budget limit reached. Research blocked.")

        try:
            results = await self.mcp.call_tool(
                "firecrawl_search",
                query=topic,
                max_results=max_results
            )

            self.budget.record_usage(cost_estimate)
            return Ok(results)
        except Exception as e:
            return Err(f"Research failed: {str(e)}")
```

**Tool Suite**:
1. **Web Research Tool** (`tools/web_research.py`): MCP firecrawl for content research
2. **Document Generator Tool** (`tools/document_generator.py`): GPT-5 powered writing for book chapters, outlines
3. **Calendar Manager Tool** (`tools/calendar_manager.py`): Schedule focus blocks and deadlines (future enhancement)
4. **Real-World Actions Tool** (`tools/real_world_actions.py`): External integrations (e.g., Amazon KDP publishing)

#### Decision 6: Error Handling with Result<T,E> Pattern

**Strategy**: All project operations return Result<T,E> for explicit error paths

**Rationale**:
- Constitutional requirement (Article II): Functional error handling mandated
- Makes error paths visible in type system (vs hidden try/catch)
- Enables rollback: Failed operations return Err with rollback instructions
- Testability: Easy to test error scenarios without raising exceptions

**Implementation Pattern**:
```python
from shared.type_definitions.result import Result, Ok, Err
from trinity_protocol.models.project import ProjectState

class ProjectInitializer:
    async def initialize_project(
        self,
        pattern: DetectedPattern,
        user_response: str
    ) -> Result[ProjectState, str]:
        """Initialize project from user approval."""

        # Step 1: Generate questions
        questions_result = await self._generate_questions(pattern)
        if questions_result.is_err():
            return Err(f"Question generation failed: {questions_result.error}")

        # Step 2: Collect answers
        answers_result = await self._collect_answers(questions_result.value)
        if answers_result.is_err():
            return Err(f"Answer collection failed: {answers_result.error}")

        # Step 3: Generate spec
        spec_result = await self._generate_spec(
            pattern,
            answers_result.value
        )
        if spec_result.is_err():
            return Err(f"Spec generation failed: {spec_result.error}")

        # Step 4: User approval
        approval_result = await self._request_approval(spec_result.value)
        if approval_result.is_err():
            return Err(f"User rejected spec: {approval_result.error}")

        # Step 5: Create project state
        project = ProjectState(
            project_id=str(uuid.uuid4()),
            spec=spec_result.value,
            status="active",
            created_at=datetime.now()
        )

        # Step 6: Persist to Firestore
        store_result = await self.state_store.store_project(project)
        if store_result.is_err():
            return Err(f"Persistence failed: {store_result.error}")

        return Ok(project)
```

**Rollback Strategy**: Project state snapshots enable recovery
- Before major operations: Snapshot current project state
- On failure: Restore from snapshot
- On success: Clear snapshot
- Firestore document versioning provides automatic history

#### Decision 7: Testing Strategy with NECESSARY Pattern

**Strategy**: 100% pass rate requirement, comprehensive coverage across unit/integration/E2E

**Rationale**:
- Constitutional Article II: 100% test success mandatory (no exceptions)
- NECESSARY pattern ensures quality: Named clearly, Executable in isolation, Comprehensive coverage, Error handling validated, State changes verified, Side effects controlled, Assertions meaningful, Repeatable results, Yield fast execution
- Catches regressions: Project execution complexity requires thorough testing

**Test Structure**:
```
tests/trinity_protocol/
├── test_project_initializer.py       # 30+ tests
│   ├── test_question_generation
│   ├── test_spec_generation
│   ├── test_user_approval_workflow
│   └── test_error_handling
│
├── test_project_executor.py          # 30+ tests
│   ├── test_daily_task_planning
│   ├── test_task_execution
│   ├── test_progress_tracking
│   └── test_milestone_verification
│
├── test_daily_checkin.py             # 20+ tests
│   ├── test_question_batching
│   ├── test_timing_optimization
│   ├── test_preference_integration
│   └── test_quiet_hours_respect
│
└── test_phase3_integration.py        # 25+ tests (E2E)
    ├── test_end_to_end_book_project
    ├── test_multi_session_continuity
    ├── test_budget_enforcement
    └── test_tool_integration

tests/tools/
├── test_web_research.py              # 25+ tests
├── test_document_generator.py        # 25+ tests
├── test_calendar_manager.py          # 20+ tests
└── test_real_world_actions.py        # 20+ tests
```

**Minimum Coverage**: 130+ new tests (plus existing 161 tests = 291+ total)

### 3. Integration Points

#### HITL Protocol Integration

**Connection**: `project_initializer.py` → `human_review_queue.py`

**Flow**:
1. Pattern detected → Question formulated → Asked via HITL
2. User responds YES → Routed to `project_initializer.py`
3. Project initializer asks 5-10 setup questions → Routed via HITL
4. Answers collected → Spec generated → Approval requested via HITL
5. User approves → Project execution begins

**Contract**:
```python
# trinity_protocol/human_review_queue.py
class HumanReviewQueue:
    async def route_response(
        self,
        response: UserResponse
    ) -> Result[None, str]:
        """Route user responses to appropriate handlers."""

        if response.response_type == ResponseType.YES:
            if response.context.is_project_initialization:
                # Route to project initializer
                await self.project_initializer.handle_approval(response)
            else:
                # Standard EXECUTOR routing
                await self.executor.handle_approval(response)

        return Ok(None)
```

#### Preference Learning Integration

**Connection**: `daily_checkin.py` → `preference_learning.py`

**Flow**:
1. Daily check-in coordinator needs to schedule questions
2. Query preference learner for optimal timing
3. Preference learner returns recommendation (e.g., "Ask at 08:30, 85% acceptance rate")
4. Coordinator schedules batch delivery at optimal time

**Contract**:
```python
# trinity_protocol/daily_checkin.py
class DailyCheckinCoordinator:
    def get_optimal_schedule(
        self,
        project: ProjectState
    ) -> Result[datetime, str]:
        """Get optimal time for daily check-in."""

        recommendation = self.preference_learner.get_optimal_time(
            topic=project.topic,
            question_type="high_value",
            respect_quiet_hours=True
        )

        return Ok(recommendation.scheduled_time)
```

#### Response Handler Integration

**Connection**: `project_executor.py` → `response_handler.py`

**Flow**:
1. User responds to daily check-in questions
2. Response handler captures answers
3. Project executor receives answers
4. Project state updated with new information
5. Next day's tasks adjusted based on feedback

**Contract**:
```python
# trinity_protocol/response_handler.py
class ResponseHandler:
    async def handle_project_checkin_response(
        self,
        response: UserResponse
    ) -> Result[None, str]:
        """Handle responses to project check-in questions."""

        # Extract answers
        answers = self._parse_answers(response.content)

        # Route to project executor
        await self.project_executor.process_checkin_answers(
            project_id=response.context.project_id,
            answers=answers
        )

        return Ok(None)
```

#### Real-World Tools Integration

**Connection**: `project_executor.py` → `tools/web_research.py`, `tools/document_generator.py`

**Flow**:
1. Project executor plans daily tasks
2. Task requires external action (e.g., research coaching methodologies)
3. Executor calls web research tool via MCP
4. Tool executes, returns results (or error)
5. Results incorporated into project deliverables

**Contract**:
```python
# trinity_protocol/project_executor.py
class ProjectExecutor:
    async def execute_task(
        self,
        task: DailyTask
    ) -> Result[TaskResult, str]:
        """Execute a single daily task."""

        if task.requires_web_research:
            research_result = await self.web_research_tool.research_topic(
                topic=task.research_topic,
                max_results=5
            )

            if research_result.is_err():
                # Graceful degradation: continue without research
                self._log_tool_failure(research_result.error)
            else:
                task.context.research_data = research_result.value

        # Execute task with available context
        return await self._execute_with_context(task)
```

#### Firestore Persistence Integration

**Connection**: All components → `ProjectStateStore`

**Flow**:
1. Component modifies project state (e.g., executor completes task)
2. Component calls `state_store.store_project(updated_project)`
3. Firestore persists state with automatic versioning
4. On Trinity restart: Load projects via `state_store.get_active_projects()`
5. Execution resumes from last saved state

**Contract**:
```python
# All components use this pattern
async def update_project_state(
    self,
    project: ProjectState,
    update_fn: Callable[[ProjectState], ProjectState]
) -> Result[ProjectState, str]:
    """Update project state with automatic persistence."""

    # Apply update
    updated_project = update_fn(project)

    # Persist to Firestore
    store_result = await self.state_store.store_project(updated_project)

    if store_result.is_err():
        return Err(f"Failed to persist state: {store_result.error}")

    return Ok(updated_project)
```

## Rationale

### Why Spec-Driven Project Initialization?

**Constitutional Mandate**: Article V requires formal specifications for complex features. A book-writing project spanning 2 weeks is complex.

**Benefits**:
- Clear success criteria: User and Trinity agree on outcomes before work begins
- Reduced ambiguity: Spec clarifies vague conversational input ("a book" → "150-page non-fiction coaching book")
- User control: Approval workflow ensures user alignment before execution
- Testability: Spec provides acceptance criteria for validation

**Alternative Considered**: Direct execution from conversation
- **Pros**: Faster start, less overhead
- **Cons**: Misalignment risk (Trinity builds wrong thing), no clear success criteria
- **Why Rejected**: Violates Article V and increases risk of wasted effort

### Why Daily Micro-Tasks vs Full Project Plan?

**Agile Principle**: Adapt based on feedback vs rigid waterfall planning

**Benefits**:
- Flexibility: User feedback on Day 1 informs Day 2 (e.g., "Focus more on tactics, less on mindset")
- Reduced planning overhead: Plan 24 hours, not 2 weeks
- Constitutional alignment (Article I): Have complete context for today before planning tomorrow
- User mental model: "What's next?" vs overwhelming 50-step plan

**Alternative Considered**: Complete project plan upfront
- **Pros**: Predictable timeline, clear roadmap, easier progress tracking
- **Cons**: Brittle to changes, planning overhead, violates Article I
- **Why Rejected**: Real projects require adaptation; upfront planning fails when requirements evolve

### Why Firestore vs Local SQLite?

**Cross-Session Persistence**: Projects span weeks; Trinity restarts must not lose state

**Benefits**:
- Durability: Survives Trinity restarts, system reboots, process crashes
- Real-time sync: Multiple devices can access project state
- Proven reliability: Phase 1-2 validated with 179 documents stored
- Scalability: Handles hundreds of concurrent projects

**Alternative Considered**: Local SQLite database
- **Pros**: Zero network latency, no external dependencies, simpler setup
- **Cons**: Lost on disk failure, no cross-device sync, manual backup complexity
- **Why Rejected**: Durability is critical for life assistant use case

### Why GPT-5 for Spec Generation vs Rule-Based?

**Intelligence Requirement**: Conversational input is unstructured and ambiguous

**Benefits**:
- Handles ambiguity: "A book" → Infers non-fiction coaching book based on pattern context
- Extracts implicit requirements: User mentions "clients" → Infers target audience
- Validates completeness: Detects missing information, asks follow-up questions
- Natural language understanding: No rigid question structure required

**Alternative Considered**: Rule-based template filling
- **Pros**: Predictable output, faster execution, no LLM cost
- **Cons**: Cannot handle ambiguity, misses implicit context, brittle
- **Why Rejected**: Real conversations are unstructured; rule-based parser would fail

### Why MCP Protocol for Tools vs Direct API Integration?

**Standardization**: Consistent interface for all external tools

**Benefits**:
- Safety: All tools wrapped in Result<T,E> with error handling
- Budget enforcement: All tool usage metered by budget enforcer
- Extensibility: Adding new tools (Notion, Slack) follows same pattern
- Proven: Phase 1-2 validated MCP with firecrawl integration

**Alternative Considered**: Direct API integration per tool
- **Pros**: More control, fewer abstraction layers, potentially faster
- **Cons**: No standardization, each tool requires custom integration, harder to enforce safety
- **Why Rejected**: MCP provides consistent interface for tool safety and budget control

## Consequences

### Positive

1. **User Value Delivered**: Trinity transitions from "impressive infrastructure" to "genuinely helpful assistant" that completes real projects (book writing, course creation)

2. **Constitutional Compliance**: Spec-driven initialization (Article V), complete context before planning (Article I), 100% test coverage (Article II), preference learning integration (Article IV), budget enforcement (Article III)

3. **Cross-Session Persistence**: Firestore enables project continuity across weeks, surviving Trinity restarts and system reboots

4. **Minimal User Burden**: 1-3 questions/day (5-10 minutes) vs hours of manual project management

5. **Adaptive Execution**: Daily micro-tasks adjust based on feedback vs rigid waterfall plan

6. **Real-World Capability**: Web research, document generation, calendar management enable non-code actions

7. **User Control Maintained**: Approval workflow at initialization, HITL protocol for daily questions, instant project pause/delete

### Negative

1. **Implementation Complexity**: Project execution engine is substantial (est. 2-3 weeks, 8,000+ lines of code)

2. **Firestore Dependency**: Requires Firebase project setup, credentials management, potential network latency

3. **LLM Cost**: Spec generation and daily task planning consume GPT-5 tokens (~$1-3/project initialization, $0.50/day for active project)

4. **Tool Integration Overhead**: Each real-world tool (web research, calendar) requires MCP integration, error handling, budget enforcement

5. **Testing Burden**: 130+ new tests required for constitutional compliance (Article II)

6. **User Onboarding**: Project initialization workflow (5-10 questions) adds friction vs instant execution

### Risks

#### Risk 1: Firestore Persistence Failure

**Impact**: Project state lost, user loses confidence, work must restart

**Likelihood**: Low (Phase 1-2 validated with 179 documents, zero failures)

**Mitigation**:
- Local cache fallback: Store recent project state in SQLite as backup
- Automatic retry: Failed Firestore writes retry 3x with exponential backoff
- User notification: Alert user if persistence fails, prompt manual export
- Firestore document versioning: Recover from previous snapshot on corruption

#### Risk 2: Spec Generation Misalignment

**Impact**: Trinity builds wrong thing, wastes effort, user frustrated

**Likelihood**: Medium (conversational input inherently ambiguous)

**Mitigation**:
- User approval workflow: Spec displayed for review before execution begins
- Modification support: User can request changes to spec before approval
- Confidence thresholding: Low-confidence specs flag missing information
- Follow-up questions: LLM asks clarifying questions when context incomplete

#### Risk 3: Budget Overrun

**Impact**: Project execution exceeds $30/day limit, auto-shutdown triggered, progress blocked

**Likelihood**: Medium (complex projects may require extensive tool usage)

**Mitigation**:
- Budget enforcer integration: All tool calls checked against daily limit
- Cost estimation: Display estimated daily cost during initialization
- Graceful degradation: Continue execution without expensive tools if budget low
- User notification: Alert user when approaching budget limit, offer options

#### Risk 4: Tool Integration Failures

**Impact**: Web research fails, document generation errors, project blocked

**Likelihood**: Medium (external tools have variable reliability)

**Mitigation**:
- Result<T,E> pattern: All tool calls return explicit error or success
- Graceful degradation: Continue execution without tool results when possible
- Retry logic: Failed tool calls retry 3x before returning error
- User transparency: Log tool failures, inform user of degraded operation

#### Risk 5: Constitutional Violation (Article II)

**Impact**: Test failures block Phase 3 deployment, implementation delayed

**Likelihood**: Low (TDD approach with NECESSARY pattern reduces risk)

**Mitigation**:
- TDD methodology: Write tests before implementation (constitutional mandate)
- Incremental testing: Test each component as built (not all at end)
- QualityEnforcer validation: Autonomous healing for detected violations
- Pre-merge CI: 100% test pass rate enforced before merge

## Alternatives Considered

### Alternative 1: No Formal Spec (Direct Execution from Conversation)

**Description**: Skip spec generation, execute directly from conversational approval

**Pros**:
- ✅ Faster startup (no 5-10 question workflow)
- ✅ Less overhead (no spec generation LLM cost)
- ✅ Lower friction (user says YES, work begins immediately)

**Cons**:
- ❌ **CONSTITUTIONAL VIOLATION**: Article V requires formal spec for complex features
- ❌ High misalignment risk (Trinity builds wrong thing)
- ❌ No clear success criteria (how to verify "book is done"?)
- ❌ User control reduced (no approval checkpoint)

**Why Rejected**: Violates Article V (spec-driven development) and increases risk of wasted effort. Formal spec provides clarity and alignment.

### Alternative 2: Waterfall Project Planning (Full Plan Upfront)

**Description**: Generate complete 2-week project plan with all tasks during initialization

**Pros**:
- ✅ Clear roadmap (user sees full plan upfront)
- ✅ Predictable timeline (all steps defined)
- ✅ Easier progress tracking (% complete calculation)

**Cons**:
- ❌ **BRITTLE TO CHANGES**: User feedback on Day 1 cannot inform Day 2 (plan locked)
- ❌ Planning overhead (requires complete context for 2-week future)
- ❌ Violates Article I (incomplete future context)
- ❌ Fails in practice (real projects require adaptation)

**Why Rejected**: Real projects require adaptation based on feedback. Daily micro-tasks provide flexibility while maintaining progress.

### Alternative 3: Local SQLite for Project State

**Description**: Store project state in local SQLite database instead of Firestore

**Pros**:
- ✅ Zero network latency (local disk access)
- ✅ No external dependencies (simpler setup)
- ✅ No Firebase project required (easier onboarding)

**Cons**:
- ❌ **NO CROSS-SESSION PERSISTENCE**: Lost on disk failure or Trinity reinstall
- ❌ No cross-device sync (project state locked to one machine)
- ❌ Manual backup complexity (user must manage backups)
- ❌ No real-time updates (multiple processes cannot share state)

**Why Rejected**: Cross-session persistence is critical for life assistant use case. Book projects span weeks; Firestore durability required.

### Alternative 4: Rule-Based Spec Generation (No LLM)

**Description**: Use template-based spec generation with predefined question structure

**Pros**:
- ✅ Predictable output (same input → same spec)
- ✅ Faster execution (no LLM latency)
- ✅ Zero LLM cost (no GPT-5 tokens)

**Cons**:
- ❌ **CANNOT HANDLE AMBIGUITY**: Fails on unstructured conversational input
- ❌ Misses implicit context (user mentions "clients" but rule system doesn't infer target audience)
- ❌ Brittle (requires rigid question structure)
- ❌ Poor user experience (feels like form-filling, not conversation)

**Why Rejected**: Conversational input is inherently unstructured. GPT-5 intelligence required for robust spec generation.

### Alternative 5: Synchronous Daily Interruption (Ask Questions Anytime)

**Description**: Ask daily check-in questions whenever needed (no batching, no timing optimization)

**Pros**:
- ✅ Faster project velocity (no waiting for optimal time)
- ✅ Immediate clarification (unblocks work instantly)

**Cons**:
- ❌ **ANNOYS USERS**: Interrupts flow state, breaks concentration
- ❌ High rejection rate (users say NO when interrupted at wrong time)
- ❌ Contradicts preference learning (ignores optimal timing data)
- ❌ Violates thoughtful assistance philosophy (interruption minimization)

**Why Rejected**: User satisfaction requires thoughtful interruption strategy. Batching questions (1-3/day at optimal time) respects user flow state.

## Implementation Notes

### File Structure

```
trinity_protocol/
├── project_initializer.py          # Conversation → spec → project state
├── spec_from_conversation.py       # LLM-powered spec generation
├── project_executor.py             # Daily task planning and execution
├── daily_checkin.py                # Question batching and scheduling
├── models/
│   ├── project.py                  # ProjectState, ProjectSpec, DailyTask
│   └── project_store.py            # Firestore persistence layer

tools/
├── web_research.py                 # MCP firecrawl integration
├── document_generator.py           # GPT-5 powered writing
├── calendar_manager.py             # Focus block scheduling (future)
└── real_world_actions.py           # External integrations (future)

tests/trinity_protocol/
├── test_project_initializer.py     # 30+ tests
├── test_project_executor.py        # 30+ tests
├── test_daily_checkin.py           # 20+ tests
└── test_phase3_integration.py      # 25+ E2E tests

tests/tools/
├── test_web_research.py            # 25+ tests
├── test_document_generator.py      # 25+ tests
├── test_calendar_manager.py        # 20+ tests
└── test_real_world_actions.py      # 20+ tests
```

### Key Implementation Considerations

1. **Firestore Collection Structure**:
```python
# trinity_projects collection
{
    "project_id": "uuid-1234",
    "title": "Coaching Book for Entrepreneurs",
    "status": "active",  # active | paused | completed | cancelled
    "spec": {
        "goals": ["Goal 1", "Goal 2"],
        "deliverables": ["150-page book", "Marketing plan"],
        "success_criteria": ["Published on Amazon KDP", "10 beta reader reviews"]
    },
    "daily_tasks": [
        {"date": "2025-10-02", "task": "Research coaching methodologies", "status": "completed"},
        {"date": "2025-10-03", "task": "Draft chapter 1 outline", "status": "in_progress"}
    ],
    "created_at": "2025-10-01T10:00:00Z",
    "updated_at": "2025-10-03T14:30:00Z",
    "metadata": {
        "topic": "coaching",
        "estimated_completion": "2025-10-14",
        "daily_time_commitment_minutes": 10
    }
}
```

2. **Project Initialization Flow**:
```python
# Detailed initialization sequence
async def initialize_project(
    pattern: DetectedPattern,
    user_approval: str
) -> Result[ProjectState, str]:

    # 1. Generate 5-10 setup questions
    questions = await generate_questions(pattern)
    # Example questions for book project:
    # - What's the book's core message?
    # - Who's the target audience?
    # - How many chapters?
    # - What's already written vs needs writing?
    # - Preferred writing style?

    # 2. Ask questions via HITL protocol
    answers = await ask_questions_via_hitl(questions)

    # 3. Generate formal spec from answers
    spec = await generate_spec(pattern, answers)
    # Spec includes: title, description, goals, deliverables,
    # success criteria, timeline, daily commitment

    # 4. Request user approval of spec
    approval = await request_spec_approval(spec)
    if not approval:
        return Err("User rejected spec")

    # 5. Create project state
    project = ProjectState(
        project_id=str(uuid.uuid4()),
        spec=spec,
        status="active",
        created_at=datetime.now()
    )

    # 6. Persist to Firestore
    await state_store.store_project(project)

    # 7. Schedule first daily check-in
    await daily_checkin.schedule_initial_checkin(project)

    return Ok(project)
```

3. **Daily Check-in Flow**:
```python
# Executed once per day at optimal time
async def daily_checkin(project: ProjectState) -> Result[None, str]:

    # 1. Plan today's tasks based on project state
    tasks = await executor.plan_daily_tasks(
        project,
        yesterday_feedback=project.last_checkin_feedback
    )

    # 2. Formulate 1-3 questions to advance project
    questions = await formulate_checkin_questions(project, tasks)
    # Example questions:
    # - "Should Chapter 2 focus more on mindset or tactics?"
    # - "Any specific case studies to include?"

    # 3. Get optimal delivery time from preference learner
    optimal_time = preference_learner.get_optimal_time(
        topic=project.topic,
        question_type="high_value"
    )

    # 4. Batch questions and schedule delivery
    batch = QuestionBatch(
        questions=questions,
        scheduled_time=optimal_time,
        project_id=project.project_id
    )

    await response_handler.schedule_batch(batch)

    return Ok(None)
```

4. **Budget Enforcement Integration**:
```python
# All tool calls check budget before execution
async def execute_with_budget_check(
    tool_call: Callable,
    estimated_cost: float
) -> Result[Any, str]:

    # Check budget availability
    if not budget_enforcer.check_available(estimated_cost):
        return Err(f"Budget limit reached. Operation blocked. "
                   f"Current usage: ${budget_enforcer.daily_usage:.2f}/$30.00")

    # Execute tool call
    try:
        result = await tool_call()
        budget_enforcer.record_usage(estimated_cost)
        return Ok(result)
    except Exception as e:
        return Err(f"Tool execution failed: {str(e)}")
```

5. **Graceful Degradation Pattern**:
```python
# Continue execution even if tools fail
async def execute_task_with_fallback(
    task: DailyTask
) -> Result[TaskResult, str]:

    # Attempt web research (optional for most tasks)
    if task.benefits_from_research:
        research_result = await web_research_tool.research_topic(
            task.research_topic
        )

        if research_result.is_ok():
            task.context.research_data = research_result.value
        else:
            # Log failure but continue
            logger.warning(f"Research failed: {research_result.error}")
            task.context.research_data = None

    # Execute task with available context
    return await execute_core_task(task)
```

### Dependencies Required

**Python Libraries** (add to `pyproject.toml`):
```toml
[tool.poetry.dependencies]
google-cloud-firestore = "^2.13.0"  # Firestore persistence
pydantic = "^2.4.0"                 # Type-safe models
```

**Environment Variables**:
```bash
# Firestore configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json
FIREBASE_PROJECT_ID=trinity-assistant

# Budget enforcement
TRINITY_DAILY_BUDGET=30.00  # $30/day hard limit
```

### Migration Path

**Week 1**: Project Initialization
- Implement `project_initializer.py` (conversation → spec → project state)
- Implement `spec_from_conversation.py` (LLM-powered spec generation)
- Implement `models/project.py` (Pydantic models)
- Unit tests (30+ tests)

**Week 2**: Project Execution
- Implement `project_executor.py` (daily task planning and execution)
- Implement `daily_checkin.py` (question batching and scheduling)
- Implement `models/project_store.py` (Firestore persistence)
- Unit tests (50+ tests)

**Week 3**: Real-World Tools
- Implement `tools/web_research.py` (MCP firecrawl)
- Implement `tools/document_generator.py` (GPT-5 writing)
- Tool tests (50+ tests)

**Week 4**: Integration & Testing
- E2E integration tests (25+ tests)
- Constitutional compliance validation
- Demo script (`demo_phase3_book_project.py`)
- Full test suite execution (291+ tests, 100% pass required)

### Timeline Estimates

- **Research & Design**: Already complete (this ADR)
- **Core Implementation**: 3 weeks
- **Testing & Validation**: 1 week
- **Documentation & Demos**: 3 days
- **Total**: 4 weeks for production-ready system

## Constitutional Compliance

### Article I: Complete Context Before Action

**Compliance Mechanisms**:
- Project initializer reads full conversation history before generating spec
- Daily executor reviews complete project state before planning tasks
- Spec generation flags missing information, asks follow-up questions
- No execution begins without approved specification

**Validation**:
```python
# Enforced in project_initializer.py
async def generate_spec(
    conversation_history: List[str]
) -> Result[ProjectSpec, str]:

    # Verify complete context
    if len(conversation_history) < 3:
        return Err("Insufficient conversation context. Need 3+ exchanges.")

    # Check for completeness
    spec = await llm.generate_spec(conversation_history)

    if spec.has_missing_information:
        return Err(f"Incomplete context. Missing: {spec.missing_fields}")

    return Ok(spec)
```

### Article II: 100% Verification and Stability

**Compliance Mechanisms**:
- 130+ new tests with NECESSARY pattern (Named, Executable, Comprehensive, Error handling, State changes, Side effects, Assertions, Repeatable, Yield fast)
- TDD approach: Tests written before implementation
- Pre-merge CI enforces 100% pass rate
- QualityEnforcer validates code quality (no Dict[Any], functions <50 lines)

**Validation**:
```bash
# Pre-merge check (run by CI)
python run_tests.py --run-all
# Must show: 291+ tests, 100% pass rate, zero failures

pytest tests/trinity_protocol/test_phase3_integration.py -v
# All E2E tests must pass
```

### Article III: Automated Enforcement

**Compliance Mechanisms**:
- Budget enforcer blocks excessive tool usage (hard $30/day limit)
- Foundation verifier checks green main before execution
- Pre-commit hooks prevent constitutional violations
- No manual override capabilities

**Validation**:
```python
# Enforced in budget_enforcer.py
class BudgetEnforcer:
    DAILY_LIMIT = 30.00  # Hard limit, no override

    def check_available(self, estimated_cost: float) -> bool:
        """Block operation if budget exceeded. No override."""
        if self.daily_usage + estimated_cost > self.DAILY_LIMIT:
            logger.error(f"Budget limit reached: ${self.daily_usage:.2f}")
            return False  # BLOCKED, no exceptions
        return True
```

### Article IV: Continuous Learning and Improvement

**Compliance Mechanisms**:
- Preference learning integration: Daily check-in timing optimized by user response data
- Project success/failure data stored for pattern analysis
- User feedback (YES/NO/LATER) informs future question formulation
- Cross-session learning: Firestore persistence enables pattern recognition across projects

**Validation**:
```python
# Enforced in daily_checkin.py
class DailyCheckinCoordinator:
    def __init__(self, preference_learner: PreferenceLearner):
        self.preferences = preference_learner  # Required dependency

    async def schedule_checkin(self, project: ProjectState):
        # Apply learning: Use preference data for timing
        optimal_time = self.preferences.get_optimal_time(
            topic=project.topic,
            question_type="high_value"
        )
        # Guaranteed to leverage historical learning data
```

### Article V: Spec-Driven Development

**Compliance Mechanisms**:
- Project initialization creates formal spec.md (Goals, Deliverables, Success Criteria)
- User approval workflow before execution begins
- All implementation traces to specification
- Living document: Spec updated during project execution if requirements evolve

**Validation**:
```python
# Enforced in project_initializer.py
async def initialize_project(
    pattern: DetectedPattern
) -> Result[ProjectState, str]:

    # 1. Generate formal spec (Article V requirement)
    spec = await generate_spec(pattern)

    # 2. User approval required before proceeding
    approval = await request_spec_approval(spec)
    if not approval:
        return Err("Execution blocked: No approved spec")

    # 3. All subsequent work references spec
    project = ProjectState(spec=spec, ...)
    return Ok(project)
```

## References

### Technical Documentation

- **Phase 1-2 Progress Report**: `TRINITY_LIFE_ASSISTANT_PROGRESS_REPORT.md`
- **Orchestration Plan**: `PHASE_3_ORCHESTRATION_PLAN.md`
- **Trinity Whitepaper**: `docs/reference/Trinity.pdf`
- **Firestore Python Client**: https://googleapis.dev/python/firestore/latest/
- **Model Context Protocol (MCP)**: https://github.com/anthropics/mcp

### Related ADRs

- **ADR-001**: Complete Context Before Action (context verification before planning)
- **ADR-002**: 100% Verification and Stability (NECESSARY test pattern)
- **ADR-003**: Automated Merge Enforcement (budget enforcer, green main verification)
- **ADR-004**: Continuous Learning and Improvement (preference learning integration)
- **ADR-005**: Per-Agent Model Policy (GPT-5 for spec generation, planning)
- **ADR-007**: Spec-Driven Development (formal spec.md requirement)
- **ADR-010**: Result Pattern for Error Handling (functional error handling)
- **ADR-016**: Ambient Listener Architecture (pattern detection feeds project initialization)

### Related Specifications

- **Spec: Ambient Intelligence System** (`specs/ambient_intelligence_system.md`)
- **Spec: Proactive Question Engine** (`specs/proactive_question_engine.md`)
- **Plan: Ambient Intelligence** (`plans/plan-ambient-intelligence-system.md`)
- **Plan: Question Engine** (`plans/plan-question-engine.md`)

### Integration Guides

- **HITL Implementation Summary**: `trinity_protocol/HITL_IMPLEMENTATION_SUMMARY.md`
- **Preference Learning README**: `trinity_protocol/PREFERENCE_LEARNING_README.md`
- **Ambient Integration Summary**: `trinity_protocol/AMBIENT_INTEGRATION_SUMMARY.md`

### Constitutional Requirements

- **Constitution**: `/Users/am/Code/Agency/constitution.md`
- **ADR Index**: `/Users/am/Code/Agency/docs/adr/ADR-INDEX.md`

---

## Approval

**Proposed by**: ChiefArchitectAgent
**Date**: 2025-10-01
**Status**: Accepted

**Review Checklist**:
- [x] Addresses Phase 3 requirements (project initialization, execution, real-world tools)
- [x] Constitutional compliance (all 5 articles)
- [x] Integration with Phases 1-2 (HITL, preference learning, pattern detection)
- [x] Firestore persistence strategy
- [x] Budget enforcement integration
- [x] Testing strategy (130+ tests, NECESSARY pattern)
- [x] Error handling (Result<T,E> pattern)
- [x] User control mechanisms (approval workflow, daily question limit)
- [x] Clear implementation plan (4-week timeline)

**Next Steps**:
1. Create formal specification: `specs/project_execution_engine.md`
2. Create technical plan: `plans/plan-phase3-execution.md`
3. Implementation begins (TDD approach with NECESSARY pattern)
4. Integration testing with Phases 1-2
5. Constitutional compliance validation
6. Demo creation: `demo_phase3_book_project.py`

---

*"From listening to action: Trinity completes the journey from ambient awareness to real-world execution."*
