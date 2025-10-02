# Specification: Workflow State Persistence & Parallel Execution

**Spec ID**: `spec-015-workflow-state-persistence`
**Status**: `Draft`
**Author**: ChiefArchitectAgent
**Created**: 2025-10-02
**Last Updated**: 2025-10-02
**Related Plan**: `plan-015-workflow-state-persistence.md`

---

## Executive Summary

Implement a workflow state machine with checkpoint persistence, resumability after interruption, parallel execution orchestration for multi-agent workflows, and Human-in-the-Loop (HITL) approval gates with configurable thresholds. This will improve workflow orchestration from 72/100 to 84/100, enabling production-grade autonomous operations with fault tolerance and human oversight.

---

## Goals

### Primary Goals
- [ ] **Goal 1**: Build workflow state machine with SQLite/Firestore persistence for checkpoint storage
- [ ] **Goal 2**: Implement resumability allowing workflows to continue after interruption or failure
- [ ] **Goal 3**: Add parallel execution orchestrator enabling concurrent multi-agent operations
- [ ] **Goal 4**: Define Human-in-the-Loop (HITL) approval gates with configurable risk thresholds
- [ ] **Goal 5**: Integrate workflow state with telemetry for observability and debugging

### Success Metrics
- **Resumability**: 100% of interrupted workflows resume from last checkpoint without data loss
- **Parallel Efficiency**: 50%+ reduction in workflow execution time for parallelizable tasks
- **HITL Integration**: 95%+ user satisfaction with approval gate placement and UX
- **Fault Tolerance**: 99%+ workflow success rate after implementing retry and rollback
- **State Persistence**: <100ms checkpoint write latency, zero data corruption
- **Observability**: 100% workflow steps tracked in telemetry with state transitions

---

## Non-Goals

### Explicit Exclusions
- **Distributed Orchestration**: Not implementing distributed workflow engine (Airflow/Temporal) - using lightweight local orchestrator
- **Complex Scheduling**: Not implementing cron-like scheduling or time-based triggers
- **Workflow Marketplace**: Not building shareable workflow templates or community exchange
- **Visual Workflow Designer**: Not implementing graphical workflow builder (defer to future)

### Future Considerations
- **Workflow Templates**: Pre-built workflow templates for common tasks (spec-to-deployment, audit-to-fix)
- **Distributed Execution**: Scaling workflows across multiple machines or cloud workers
- **Workflow Analytics**: Historical execution analysis, bottleneck detection, optimization recommendations
- **Interactive Debugging**: Step-through execution mode for workflow development

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Development Lead (@am - Autonomous Operations)
- **Description**: Project owner running long-running autonomous workflows (spec → plan → implement → test → merge)
- **Goals**: Uninterrupted execution despite network issues, ability to pause/resume, parallel agent execution
- **Pain Points**: Network timeouts kill entire workflow, sequential execution too slow, no recovery from failures
- **Technical Proficiency**: Expert in software architecture, expects production-grade reliability

#### Persona 2: PlannerAgent (Workflow Orchestrator)
- **Description**: Agent responsible for coordinating multi-agent workflows like plan_and_execute
- **Goals**: Reliable state management, automatic recovery, clear progress tracking, HITL integration points
- **Pain Points**: No state persistence, can't resume after crash, sequential bottlenecks, unclear when to ask human
- **Technical Proficiency**: Expert in agent coordination, requires simple state management API

#### Persona 3: QualityEnforcerAgent (Parallel Executor)
- **Description**: Agent running parallel autonomous healing operations across multiple files
- **Goals**: Concurrent execution of independent fixes, efficient resource utilization, failure isolation
- **Pain Points**: Must execute fixes sequentially, one failure blocks all others, no parallelism
- **Technical Proficiency**: Expert in autonomous operations, requires parallel execution primitives

### User Journeys

#### Journey 1: Long-Running Workflow Interrupted (Current - Data Loss)
```
1. User starts: /prime plan_and_execute on large feature
2. Workflow runs: Planner creates spec (5 min), creates plan (8 min), starts implementation
3. Network interruption: API timeout at minute 18
4. Workflow fails: All progress lost, no checkpoint
5. User must restart: From beginning, repeating 18 minutes of work
6. Frustration: Multiple retries needed, unpredictable completion time
```

#### Journey 2: Long-Running Workflow Interrupted (Future - Resumable)
```
1. User starts: /prime plan_and_execute on large feature
2. Workflow runs: State checkpointed after each major step (spec, plan, code)
3. Network interruption: API timeout at minute 18
4. Workflow auto-resumes: Detects checkpoint, skips completed steps
5. Execution continues: From last checkpoint (implementation), not from beginning
6. User achieves: Completion in 25 minutes (18 + 7 resume) vs. 36 minutes (18 × 2 retries)
```

#### Journey 3: Parallel Healing Operations (Current - Sequential Bottleneck)
```
1. QualityEnforcer starts: Autonomous healing on 10 files with NoneType errors
2. Files are independent: No shared state or dependencies
3. Sequential execution: Fix file 1 (2 min), file 2 (2 min), ... file 10 (2 min) = 20 minutes total
4. Resource waste: CPU idle during LLM API calls, no parallelism
5. Slow completion: 20 minutes for work that could be 4 minutes
```

#### Journey 4: Parallel Healing Operations (Future - Concurrent Execution)
```
1. QualityEnforcer starts: Autonomous healing on 10 files with NoneType errors
2. Orchestrator detects: Independent tasks, eligible for parallel execution
3. Parallel execution: 5 concurrent workers, each handling 2 files
4. Completion time: 4 minutes (10 files ÷ 5 workers × 2 min/file)
5. 80% time savings: 20 minutes → 4 minutes for identical work
```

#### Journey 5: HITL Approval Gate (Future - Risk-Based Oversight)
```
1. Workflow executes: plan_and_execute on security-critical feature
2. Risk threshold: Security changes require human approval (HITL gate)
3. Checkpoint created: Before implementing security-sensitive code changes
4. User notified: "Approve implementation of authentication system? [Y/n/details]"
5. User reviews: Specification and plan, approves proceed
6. Workflow continues: Implementation phase begins with user confidence
```

---

## Acceptance Criteria

### Functional Requirements

#### State Machine Implementation
- [ ] **AC-1.1**: Workflow state machine defined with states: PENDING, RUNNING, PAUSED, CHECKPOINTED, COMPLETED, FAILED
- [ ] **AC-1.2**: State transitions validated: only legal transitions permitted (e.g., PENDING → RUNNING, RUNNING → CHECKPOINTED)
- [ ] **AC-1.3**: State machine persisted to SQLite (local) or Firestore (production) after each transition
- [ ] **AC-1.4**: Workflow state includes: workflow_id, current_step, completed_steps, pending_steps, metadata, timestamps
- [ ] **AC-1.5**: Atomic state updates: checkpoint writes are transactional to prevent corruption

#### Checkpoint Persistence
- [ ] **AC-2.1**: Checkpoint created after each major workflow step (e.g., spec created, plan generated, code implemented)
- [ ] **AC-2.2**: Checkpoint includes: step name, outputs, agent context, tool results, timestamps
- [ ] **AC-2.3**: Checkpoint write latency <100ms to SQLite, <500ms to Firestore
- [ ] **AC-2.4**: Checkpoint storage uses compressed JSON or MessagePack for efficiency
- [ ] **AC-2.5**: Checkpoint retention policy: keep last 10 checkpoints per workflow, auto-cleanup old checkpoints

#### Resumability
- [ ] **AC-3.1**: Workflow resume detection: on startup, check for checkpointed workflows
- [ ] **AC-3.2**: Resume prompt: "Resume workflow 'plan_and_execute' from step 'implementation'? [Y/n]"
- [ ] **AC-3.3**: Resume execution: skip completed steps, restore agent context, continue from checkpoint
- [ ] **AC-3.4**: Resume validation: verify checkpoint integrity before resuming (checksum validation)
- [ ] **AC-3.5**: Failed resume handling: fallback to restart from beginning if checkpoint corrupted

#### Parallel Execution Orchestrator
- [ ] **AC-4.1**: Task dependency graph: workflows declare dependencies between steps
- [ ] **AC-4.2**: Parallel execution: independent tasks run concurrently with configurable max concurrency (default: 5)
- [ ] **AC-4.3**: Failure isolation: one task failure doesn't abort all parallel tasks (continue others, aggregate results)
- [ ] **AC-4.4**: Resource management: respect OpenAI API rate limits, avoid concurrent request spikes
- [ ] **AC-4.5**: Progress tracking: real-time updates on parallel task completion (e.g., "3/10 files healed")

#### HITL Approval Gates
- [ ] **AC-5.1**: Approval gate definition: workflows declare HITL gates at specific steps
- [ ] **AC-5.2**: Risk thresholds: configurable via environment variables (e.g., HITL_SECURITY_CHANGES=true)
- [ ] **AC-5.3**: Approval prompt: clear context provided (step name, inputs/outputs, risks)
- [ ] **AC-5.4**: Approval options: Yes (proceed), No (abort), Details (show more info), Skip (proceed without approval this time)
- [ ] **AC-5.5**: Approval timeout: if no response in 5 minutes, workflow pauses and waits

#### Telemetry Integration
- [ ] **AC-6.1**: All workflow state transitions logged to telemetry system
- [ ] **AC-6.2**: Workflow execution metrics: start time, end time, duration, steps completed, failures
- [ ] **AC-6.3**: Checkpoint events: logged with checkpoint_id, workflow_id, step_name, timestamp
- [ ] **AC-6.4**: Parallel execution metrics: concurrency level, task durations, resource utilization
- [ ] **AC-6.5**: HITL approval metrics: gate location, user response, response time

### Non-Functional Requirements

#### Performance
- [ ] **AC-P.1**: Checkpoint write latency: <100ms to SQLite, <500ms to Firestore
- [ ] **AC-P.2**: Workflow resume time: <2 seconds to restore state and continue
- [ ] **AC-P.3**: Parallel execution efficiency: >50% reduction in total execution time for parallelizable workflows
- [ ] **AC-P.4**: State machine overhead: <5% additional latency per workflow step

#### Reliability
- [ ] **AC-R.1**: Checkpoint data integrity: 100% of checkpoints recoverable without corruption
- [ ] **AC-R.2**: Workflow fault tolerance: 99%+ success rate after retry/resume implementation
- [ ] **AC-R.3**: Atomic operations: all state updates are transactional (all-or-nothing)
- [ ] **AC-R.4**: Crash recovery: workflows resume automatically on system restart (if auto-resume enabled)

#### Usability
- [ ] **AC-U.1**: Clear workflow progress: user sees "Step 3/7: Implementing code changes"
- [ ] **AC-U.2**: Checkpoint transparency: user informed when checkpoints created
- [ ] **AC-U.3**: HITL approval UX: clear prompts with context, no confusion about what's being approved
- [ ] **AC-U.4**: Error messages: actionable guidance if workflow fails or checkpoint corrupted

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [ ] **AC-CI.1**: Workflow state machine gathers complete step context before execution
- [ ] **AC-CI.2**: Checkpoints include full context to enable informed resume decisions
- [ ] **AC-CI.3**: HITL approval gates provide complete context for user decision-making

#### Article II: 100% Verification and Stability
- [ ] **AC-CII.1**: 100% test coverage for state machine, checkpoint persistence, resume logic
- [ ] **AC-CII.2**: All workflow steps verify completion before proceeding to next step
- [ ] **AC-CII.3**: Parallel execution includes verification that all tasks completed successfully

#### Article III: Automated Merge Enforcement
- [ ] **AC-CIII.1**: Workflow state persistence works within existing automated enforcement (no bypasses)
- [ ] **AC-CIII.2**: HITL approval gates respect constitutional quality standards (e.g., can't approve failing tests)

#### Article IV: Continuous Learning and Improvement
- [ ] **AC-CIV.1**: Workflow execution patterns stored in VectorStore for learning
- [ ] **AC-CIV.2**: Historical checkpoint data informs optimal checkpoint placement
- [ ] **AC-CIV.3**: Parallel execution efficiency metrics drive future optimization

#### Article V: Spec-Driven Development
- [ ] **AC-CV.1**: This specification drives all workflow state persistence implementation
- [ ] **AC-CV.2**: Workflow structure follows spec-kit patterns (formal definitions, validation)

---

## Dependencies & Constraints

### System Dependencies
- **SQLite**: Local checkpoint persistence (development and fast access)
- **Firestore**: Production checkpoint persistence (cross-session, cross-device)
- **Telemetry System**: State transition logging and metrics
- **AgentContext**: Workflow state tied to agent context for continuity

### External Dependencies
- **asyncio (Python)**: For parallel execution orchestration
- **aiosqlite**: Async SQLite access for non-blocking checkpoint writes
- **google-cloud-firestore**: Optional production persistence backend

### Technical Constraints
- **Checkpoint Size**: Must keep checkpoints <1MB to avoid storage bloat
- **Concurrency Limits**: Respect OpenAI API rate limits (5 concurrent requests max by default)
- **State Serialization**: Workflow state must be JSON-serializable for persistence
- **Backward Compatibility**: Workflows must remain backward-compatible across Agency versions

### Business Constraints
- **No Manual State Management**: Users should not manually edit workflow state (corruption risk)
- **Graceful Degradation**: If Firestore unavailable, fall back to SQLite with warning
- **Cost Control**: Firestore usage must stay within budget (estimate: <$5/month)

---

## Risk Assessment

### High Risk Items
- **Risk 1**: Checkpoint corruption leads to unrecoverable workflow state - *Mitigation*: Checksum validation, keep last 10 checkpoints, atomic writes
- **Risk 2**: Parallel execution exhausts API rate limits or causes quota errors - *Mitigation*: Configurable concurrency limits, rate limit detection, exponential backoff

### Medium Risk Items
- **Risk 3**: HITL approval gates interrupt workflows at inconvenient times - *Mitigation*: Smart gate placement (batch approvals), timeout with pause-and-wait
- **Risk 4**: State machine complexity increases maintenance burden - *Mitigation*: Comprehensive testing, clear state transition diagram, extensive documentation

### Constitutional Risks
- **Constitutional Risk 1**: Article I violation if checkpoints lack complete context - *Mitigation*: Checkpoint validation ensures all required context captured
- **Constitutional Risk 2**: Article II violation if parallel execution bypasses test verification - *Mitigation*: Each parallel task includes verification step

---

## Integration Points

### Agent Integration
- **PlannerAgent**: Uses workflow state machine for plan_and_execute and audit_and_refactor workflows
- **QualityEnforcerAgent**: Uses parallel executor for concurrent healing operations
- **AgencyCodeAgent**: Checkpoints after code generation, resume from checkpoint on interruption
- **All Agents**: Workflow state accessible via shared AgentContext

### System Integration
- **Telemetry System**: All state transitions logged with workflow_id, step_name, timestamp
- **Memory System**: Workflow metadata stored in VectorStore for learning extraction
- **Cost Tracker**: Workflow execution costs tracked per workflow_id for budget monitoring
- **CLI**: New commands: `agency workflow resume`, `agency workflow status`, `agency workflow list`

### External Integration
- **SQLite**: Local database at `trinity_workflows.db` for checkpoint storage
- **Firestore**: Optional cloud persistence at `agency-workflows` collection
- **GitHub Actions**: Workflow state could trigger CI events (future enhancement)

---

## Testing Strategy

### Test Categories
- **Unit Tests**: State machine transitions, checkpoint serialization, resume logic
- **Integration Tests**: End-to-end workflow execution with checkpoints and resume
- **Concurrency Tests**: Parallel execution with various concurrency levels and failure modes
- **Fault Injection Tests**: Simulated network failures, corrupt checkpoints, API rate limits
- **Constitutional Compliance Tests**: Verify all 5 articles respected in workflow execution

### Test Data Requirements
- **Sample Workflows**: Simple (3 steps), complex (10 steps), parallel (5 concurrent tasks)
- **Checkpoint Fixtures**: Valid checkpoints, corrupted checkpoints, partial checkpoints
- **Failure Scenarios**: Network timeout, API error, agent crash, user abort

### Test Environment Requirements
- **Local SQLite**: Test checkpoint persistence and resume locally
- **Firestore Emulator**: Test production persistence without cloud costs
- **Mock LLM Calls**: Simulate long-running operations without actual API usage

---

## Implementation Phases

### Phase 1: State Machine Core (Week 1)
- **Scope**: Implement workflow state machine with SQLite persistence
- **Deliverables**:
  - `shared/workflow_state_machine.py` with state definitions and transitions
  - SQLite schema for checkpoint storage
  - Basic checkpoint create/read/resume API
- **Success Criteria**: Workflows can checkpoint and resume from SQLite storage

### Phase 2: Resumability Integration (Week 2)
- **Scope**: Integrate resume capability into existing workflows (plan_and_execute, audit_and_refactor)
- **Deliverables**:
  - Updated PlannerAgent to use checkpoint API
  - Resume detection on workflow startup
  - User prompts for resume confirmation
- **Success Criteria**: Interrupted workflows resume successfully from last checkpoint

### Phase 3: Parallel Execution Orchestrator (Week 3)
- **Scope**: Build async parallel executor for concurrent agent operations
- **Deliverables**:
  - `shared/parallel_executor.py` with dependency graph and concurrency control
  - QualityEnforcerAgent integration for parallel healing
  - Rate limit handling and failure isolation
- **Success Criteria**: Parallel workflows execute 50%+ faster than sequential

### Phase 4: HITL Approval Gates (Week 4)
- **Scope**: Implement approval gate system with risk-based thresholds
- **Deliverables**:
  - HITL approval prompt system
  - Configurable risk thresholds via environment variables
  - Approval logging to telemetry
- **Success Criteria**: Users can approve/reject workflow steps at defined gates

### Phase 5: Firestore Production Persistence (Week 5)
- **Scope**: Add optional Firestore backend for cross-session workflow state
- **Deliverables**:
  - Firestore adapter for checkpoint storage
  - Fallback logic: Firestore → SQLite if unavailable
  - Migration path from SQLite to Firestore
- **Success Criteria**: Workflows persist to Firestore with graceful degradation

---

## Review & Approval

### Stakeholders
- **Primary Stakeholder**: @am (Project Owner)
- **Secondary Stakeholders**: All Agency agents (workflow participants)
- **Technical Reviewers**: ChiefArchitectAgent (architecture validation), QualityEnforcerAgent (reliability verification)

### Review Criteria
- [ ] **Completeness**: All workflow orchestration gaps addressed
- [ ] **Clarity**: State machine and API design clear and implementable
- [ ] **Feasibility**: Parallel execution and persistence technically viable
- [ ] **Constitutional Compliance**: All 5 articles supported by implementation
- [ ] **Quality Standards**: Meets Agency's testing and reliability requirements

### Approval Status
- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending agent validation
- [ ] **Constitutional Compliance**: Pending article verification
- [ ] **Final Approval**: Pending all above approvals

---

## Appendices

### Appendix A: Glossary
- **Checkpoint**: Persistent snapshot of workflow state enabling resumability
- **State Machine**: Finite state machine managing workflow lifecycle and transitions
- **Parallel Execution**: Concurrent execution of independent workflow steps
- **HITL (Human-in-the-Loop)**: Approval gates requiring human decision-making
- **Resumability**: Capability to continue interrupted workflows from last checkpoint

### Appendix B: References
- **ADR-001**: Complete Context Before Action (drives checkpoint completeness)
- **ADR-002**: 100% Verification and Stability (drives fault tolerance requirements)
- **ADR-004**: Continuous Learning and Improvement (drives workflow pattern learning)
- **Article I**: Complete context required in checkpoints for informed resume

### Appendix C: Related Documents
- **spec-016-expanded-autonomous-healing.md**: Parallel healing as primary use case
- **shared/agent_context.py**: AgentContext integration for workflow state
- **core/telemetry.py**: Telemetry integration for workflow observability

### Appendix D: State Machine Diagram
```
PENDING → RUNNING → CHECKPOINTED → RUNNING → COMPLETED
            ↓            ↓              ↓
          PAUSED ←──── PAUSED        FAILED
            ↓
         RUNNING (resume)
```

**State Definitions:**
- **PENDING**: Workflow created, not yet started
- **RUNNING**: Workflow actively executing current step
- **CHECKPOINTED**: State saved, ready to resume
- **PAUSED**: User-initiated pause (waiting for HITL approval or manual resume)
- **COMPLETED**: All steps finished successfully
- **FAILED**: Terminal failure, manual intervention required

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-02 | ChiefArchitectAgent | Initial specification for workflow state persistence and parallel execution |

---

*"A specification is a contract between intention and implementation."*
