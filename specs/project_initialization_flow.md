# Specification: Trinity Project Initialization Flow

**Spec ID**: `spec-018-project-initialization-flow`
**Status**: Draft
**Author**: Planner Agent
**Created**: 2025-10-01
**Last Updated**: 2025-10-01
**Related Plan**: `plan-018-project-initialization.md`

---

## Executive Summary

Trinity Life Assistant Phase 3 transforms YES responses into structured, manageable projects through an intelligent initialization flow. When a user accepts a proactive question, Trinity conducts a focused 5-10 question conversation to gather requirements, generates a formal specification, obtains approval, and creates an implementation plan. The system then manages project execution with 1-3 daily check-ins, minimizing user time investment while maximizing output quality. This enables Trinity to help complete long-term projects (like writing a book) through sustained, low-friction collaboration.

---

## Goals

### Primary Goals

- [ ] **Goal 1**: Transform YES responses into formal project specifications through structured Q&A (5-10 questions, 5-10 minutes)
- [ ] **Goal 2**: Generate implementation plans that break projects into daily micro-tasks with clear acceptance criteria
- [ ] **Goal 3**: Execute projects with 1-3 questions per day maximum, achieving completion with minimal user time investment
- [ ] **Goal 4**: Maintain constitutional compliance (100% test pass rate, strict typing, Result pattern) throughout Phase 3
- [ ] **Goal 5**: Enable Alex to complete his coaching book project in 2 weeks with ~70-140 minutes total time investment

### Success Metrics

- **User Time Efficiency**: <10 minutes for project initialization, <5 minutes per daily check-in
- **Project Completion Rate**: >80% of initialized projects reach completion
- **Question Quality**: <3 questions per day average, >70% acceptance rate for proposed actions
- **Constitutional Compliance**: 100% test pass rate, zero Dict[Any] violations, all functions <50 lines
- **User Satisfaction**: Alex rates system >4/5 for helpfulness after completing book project

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Multi-user project collaboration (Phase 3 is single-user focused)
- **Non-Goal 2**: Real-time chat interface (terminal-based Q&A sufficient for MVP)
- **Non-Goal 3**: Project portfolio management UI (focus on execution, not visualization)
- **Non-Goal 4**: Advanced scheduling algorithms (simple daily check-in timing adequate)
- **Non-Goal 5**: External project tracking integration (Jira, Asana) - keep self-contained

### Future Considerations

- **Future Enhancement 1**: Visual project dashboard showing progress, milestones, and dependencies
- **Future Enhancement 2**: Multi-stakeholder approval workflows (when Trinity supports teams)
- **Future Enhancement 3**: Voice-based project initialization (speak answers instead of typing)
- **Future Enhancement 4**: Project template library (common project types pre-configured)
- **Future Enhancement 5**: Automated progress reporting (weekly summaries sent to user)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Alex (Busy Professional - Coach, Author, Podcaster)
- **Description**: Runs a coaching business, records podcasts, writes books. Values efficiency and hates busywork. Deep work blocks are sacred. Has strong preferences about timing and interruptions.
- **Goals**: Complete coaching book in 2 weeks, improve podcast workflow, reduce administrative overhead
- **Pain Points**: Projects stall due to overwhelm (too many steps), lack of accountability (no external structure), time fragmentation (can't dedicate full days), unclear next steps
- **Technical Proficiency**: Advanced (uses terminal, understands code, comfortable with automation)

#### Persona 2: Trinity System (Proactive Life Assistant)
- **Description**: Ambient intelligence system that observes patterns, detects opportunities, and offers assistance through thoughtful questions. Has learned Alex's preferences through Phase 2.
- **Goals**: Help Alex complete high-value projects with minimal time investment, maintain trust by never being annoying, continuously improve through learning
- **Pain Points**: Uncertain how much detail to gather for project setup, balancing thoroughness vs user time, knowing when to ask follow-up questions vs proceeding
- **Technical Proficiency**: Autonomous agent with access to GPT-5, Firestore, VectorStore, and Trinity Protocol tools

### User Journeys

#### Journey 1: Book Project Initialization (Primary Use Case)
```
1. User starts with: Alex mentions "coaching book" 5 times in ambient conversations
2. Pattern detected: WITNESS detects recurring topic, ARCHITECT formulates high-value question
3. Trinity asks: "You've mentioned your coaching book 5 times. I can help finish it in 2 weeks with 1-3 questions per day. Want to hear the plan?"
4. User responds: "YES!"
5. Trinity initiates: Project initialization flow begins
6. Q&A Phase (5-10 minutes):
   - Q1: "What's the book's core message or main topic?"
   - A1: "Helping coaches scale from 1-on-1 to leveraged programs"
   - Q2: "Who's the target audience?"
   - A2: "New coaches who are stuck doing only 1-on-1 sessions"
   - Q3: "How many chapters are you envisioning?"
   - A3: "8-10 chapters, around 30,000 words total"
   - Q4: "What's already written vs needs writing?"
   - A4: "Have outlines for 3 chapters, rest needs full writing"
   - Q5: "Any specific structure or writing style preference?"
   - A5: "Practical with case studies, conversational tone"
   - Q6: "What's your ideal daily time commitment?"
   - A6: "10-15 minutes max per day for questions"
   - Q7: "Any deadlines or target completion date?"
   - A7: "Would love to finish in 2-3 weeks"
7. Spec Generation: Trinity creates formal specification document
8. Review: "Here's the project spec I created. Review and approve?"
9. User reviews: Alex reads spec (2-3 minutes), says "Looks good!"
10. Plan Creation: Trinity generates implementation plan with daily tasks
11. Kickoff: "Great! I'll work on chapter outlines tonight and check in tomorrow with 2-3 questions."
12. User achieves: Project initialized, clear path forward, minimal time invested (~10 minutes)
```

#### Journey 2: Daily Check-in (Recurring Interaction)
```
1. User starts with: Alex finishes morning coffee, Trinity detects natural break
2. Trinity initiates: "Morning! Quick check-in on your book project (2 questions, 5 min)"
3. Trinity asks:
   - Q1: "For Chapter 2 (Leveraged Coaching Models), should I focus more on group programs or digital products?"
   - Q2: "You mentioned case studies - any specific client success stories to include?"
4. User responds: (Types answers, 3-4 minutes)
   - A1: "Group programs first, digital products as sidebar"
   - A2: "Use Sarah's story (1-on-1 to $20K/month group program)"
5. Trinity confirms: "Got it! I'll draft Chapter 2 with that focus and have it ready this evening."
6. User achieves: Project advances with minimal time investment, clear next steps
7. Background work: Trinity generates chapter draft, prepares next check-in
8. Next day: Repeat with new questions
```

#### Journey 3: Project Completion
```
1. User starts with: 14 days of daily check-ins completed
2. Trinity delivers: "Your coaching book is complete! Here's the full draft (30,000 words, 9 chapters)"
3. User reviews: Alex reads draft, provides feedback (30-60 minutes)
4. Final iteration: Trinity incorporates feedback, generates final version
5. Delivery: "Final version ready! Formatted for Amazon KDP. Want me to help with publishing next?"
6. User achieves: Complete book in 2 weeks with ~2 hours total time investment (vs months/years of solo effort)
```

---

## Acceptance Criteria

### Functional Requirements

#### FC-1: Project Initialization Q&A
- [ ] **AC-1.1**: System generates 5-10 contextual questions based on pattern type (book project, workflow improvement, decision framework)
- [ ] **AC-1.2**: Questions are specific and build on previous answers (adaptive questioning)
- [ ] **AC-1.3**: User can provide answers via terminal input (text-based Q&A)
- [ ] **AC-1.4**: System validates answers for completeness and requests clarification if needed
- [ ] **AC-1.5**: Entire Q&A phase completes in <10 minutes (measured via timestamps)

#### FC-2: Specification Generation
- [ ] **AC-2.1**: System generates formal spec.md following Agency spec-kit template
- [ ] **AC-2.2**: Spec includes Goals, Non-Goals, User Personas, Acceptance Criteria sections
- [ ] **AC-2.3**: Spec references user's specific answers (not generic placeholder text)
- [ ] **AC-2.4**: Spec is saved to Firestore with project_id correlation
- [ ] **AC-2.5**: User receives spec for review with option to approve/reject/modify

#### FC-3: Implementation Plan Creation
- [ ] **AC-3.1**: Upon spec approval, system generates plan.md with task breakdown
- [ ] **AC-3.2**: Plan breaks project into daily micro-tasks (<30 min each estimated)
- [ ] **AC-3.3**: Tasks have clear acceptance criteria and dependencies
- [ ] **AC-3.4**: Plan includes timeline estimate (based on 1-3 questions/day model)
- [ ] **AC-3.5**: Plan is stored in Firestore linked to spec and project

#### FC-4: Daily Check-in System
- [ ] **AC-4.1**: System generates 1-3 questions per day based on current project phase
- [ ] **AC-4.2**: Questions are timed appropriately (respects quiet hours, flow state)
- [ ] **AC-4.3**: User responses are captured and stored with context (timestamp, sentiment)
- [ ] **AC-4.4**: System confirms understanding and communicates next steps clearly
- [ ] **AC-4.5**: Check-ins complete in <5 minutes average (measured)

#### FC-5: Project Execution Engine
- [ ] **AC-5.1**: System tracks project state (current phase, completed tasks, blockers)
- [ ] **AC-5.2**: Background work executes between check-ins (chapter drafts, research)
- [ ] **AC-5.3**: System adapts plan based on user feedback (re-prioritizes if needed)
- [ ] **AC-5.4**: Progress is visible (user can query "How's the book project?")
- [ ] **AC-5.5**: System detects and handles blockers (asks for clarification, suggests alternatives)

#### FC-6: Project Completion
- [ ] **AC-6.1**: System detects when all tasks complete and notifies user
- [ ] **AC-6.2**: Final deliverable is generated (book draft, workflow automation, etc.)
- [ ] **AC-6.3**: User reviews and provides final feedback
- [ ] **AC-6.4**: System incorporates feedback and delivers final version
- [ ] **AC-6.5**: Project is marked complete in Firestore with final metrics

### Non-Functional Requirements

#### Performance
- [ ] **AC-P.1**: Q&A question generation <2 seconds per question
- [ ] **AC-P.2**: Spec generation from conversation <30 seconds
- [ ] **AC-P.3**: Plan generation from spec <60 seconds
- [ ] **AC-P.4**: Daily check-in question generation <5 seconds
- [ ] **AC-P.5**: Firestore read/write operations <500ms average

#### Quality
- [ ] **AC-Q.1**: All Pydantic models strictly typed (zero Dict[Any])
- [ ] **AC-Q.2**: All functions under 50 lines (constitutional requirement)
- [ ] **AC-Q.3**: Result<T,E> pattern for all error handling (no exceptions for control flow)
- [ ] **AC-Q.4**: 100% test coverage for all Phase 3 components
- [ ] **AC-Q.5**: Integration with Phase 1-2 systems maintains existing test pass rate

#### Reliability
- [ ] **AC-R.1**: Project state persists across Trinity restarts (Firestore storage)
- [ ] **AC-R.2**: Graceful degradation if Firestore unavailable (local SQLite fallback)
- [ ] **AC-R.3**: Q&A conversation can be paused and resumed (state machine)
- [ ] **AC-R.4**: No data loss if user responds late or skips check-in
- [ ] **AC-R.5**: System recovers from API failures with retry logic (Article I compliance)

#### Usability
- [ ] **AC-U.1**: Clear progress indicators during Q&A ("Question 3 of 7")
- [ ] **AC-U.2**: Estimated time shown for each interaction ("~5 minutes")
- [ ] **AC-U.3**: User can skip questions or provide "not sure" responses
- [ ] **AC-U.4**: Confirmation messages after each major step (spec created, plan approved)
- [ ] **AC-U.5**: Help text available if user uncertain how to respond

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [ ] **AC-CI.1**: Q&A does not proceed until all required questions answered
- [ ] **AC-CI.2**: Spec generation waits for complete Q&A transcript
- [ ] **AC-CI.3**: Timeouts handled with retry (never proceed with partial data)
- [ ] **AC-CI.4**: No broken windows introduced (all code passes quality checks)

#### Article II: 100% Verification and Stability
- [ ] **AC-CII.1**: All Phase 3 tests pass (130+ new tests minimum)
- [ ] **AC-CII.2**: Integration tests verify end-to-end project initialization flow
- [ ] **AC-CII.3**: No test deactivation or weakening to force passage
- [ ] **AC-CII.4**: Definition of Done includes code + tests + pass + review

#### Article III: Automated Merge Enforcement
- [ ] **AC-CIII.1**: Pre-commit hooks validate Phase 3 code quality
- [ ] **AC-CIII.2**: CI pipeline enforces 100% test pass before merge
- [ ] **AC-CIII.3**: No manual overrides required or implemented

#### Article IV: Continuous Learning and Improvement
- [ ] **AC-CIV.1**: All Q&A interactions logged for pattern analysis
- [ ] **AC-CIV.2**: Project success/failure tracked (completion rate, user satisfaction)
- [ ] **AC-CIV.3**: Learnings stored in Firestore for cross-session intelligence
- [ ] **AC-CIV.4**: System adapts questioning based on past project types

#### Article V: Spec-Driven Development
- [ ] **AC-CV.1**: Implementation follows this specification exactly
- [ ] **AC-CV.2**: All changes documented and approved via spec updates
- [ ] **AC-CV.3**: Requirements traceability maintained (spec → plan → code)
- [ ] **AC-CV.4**: Living documents updated during implementation

---

## Dependencies & Constraints

### System Dependencies
- **Trinity Protocol**: WITNESS (pattern detection), ARCHITECT (strategy generation), message bus
- **Phase 1-2 Systems**: Ambient listener, preference learning, human review queue
- **Firestore**: Project state storage, Q&A transcripts, specs, plans, progress tracking
- **VectorStore**: Semantic search for similar past projects, question templates
- **AgentContext**: Memory API for storing/retrieving project context

### External Dependencies
- **OpenAI GPT-5**: LLM for Q&A generation, spec creation, plan generation (via model policy)
- **MCP Integration**: Web research tool (for book content), document generation
- **Whisper AI**: Ambient transcription feeding pattern detection (already in Phase 1)

### Technical Constraints
- **Terminal-based UI**: MVP uses terminal for Q&A (no web UI required)
- **Sequential Q&A**: Questions asked one at a time (not parallel form)
- **English-only**: Phase 3 initially supports English only (multi-language future)
- **Single-project focus**: User can have one active project at a time (multi-project future)
- **Text-based interaction**: No voice input/output for Phase 3 MVP (future enhancement)

### Business Constraints
- **Time investment**: Total initialization must be <10 minutes (user acceptance threshold)
- **Daily interruption**: Maximum 3 questions per day (never more)
- **Completion timeline**: Projects should complete in 2-4 weeks typical (not months)
- **Quality bar**: Generated content (book chapters, etc.) must be >80% usable without major rewrites

---

## Risk Assessment

### High Risk Items
- **Risk 1**: Q&A phase takes >10 minutes, user abandons project - *Mitigation*: Strict 5-10 question limit, progress indicator, time estimates shown upfront
- **Risk 2**: Generated specs too generic/not personalized - *Mitigation*: Use user's exact phrasing from answers, reference specific examples they gave, validation before approval

### Medium Risk Items
- **Risk 3**: Daily check-ins feel annoying instead of helpful - *Mitigation*: Learn from Phase 2 acceptance rates, respect quiet hours, batch questions together
- **Risk 4**: Projects stall halfway through (low completion rate) - *Mitigation*: Detect stagnation, offer to adjust plan, ask if project still relevant, pause instead of abandon

### Low Risk Items
- **Risk 5**: Firestore latency impacts user experience - *Mitigation*: Local caching, SQLite fallback, async operations, show loading indicators
- **Risk 6**: User responses ambiguous/unclear - *Mitigation*: Clarifying questions, "not sure" option, smart defaults based on project type

### Constitutional Risks
- **Constitutional Risk 1**: Partial Q&A transcript used for spec generation (Article I violation) - *Mitigation*: State machine ensures all required questions answered, explicit validation before generation
- **Constitutional Risk 2**: Test failures ignored to meet timeline (Article II violation) - *Mitigation*: Autonomous healing, QualityEnforcer validation, no merge without green tests

---

## Integration Points

### Agent Integration
- **WITNESS Agent**: Provides detected patterns that trigger project opportunities
- **ARCHITECT Agent**: Receives YES responses, hands off to ProjectInitializer
- **EXECUTOR Agent**: Executes background work (chapter drafts, research) between check-ins
- **LearningAgent**: Analyzes project outcomes, improves Q&A templates, adjusts timing
- **QualityEnforcer**: Validates constitutional compliance of Phase 3 implementation

### System Integration
- **Message Bus**: `project_initialization_queue` for YES responses, `daily_checkin_queue` for scheduled questions
- **Human Review Queue**: Integration point for asking questions and capturing responses
- **Firestore Collections**: `trinity_projects`, `trinity_qa_sessions`, `trinity_project_specs`, `trinity_project_plans`
- **VectorStore**: Semantic search for similar projects, template retrieval, context augmentation

### External Integration
- **MCP Tools**: Web research (firecrawl), document generation, calendar management (future)
- **Whisper AI**: Ambient transcription continues feeding pattern detection during projects
- **File System**: Specs and plans saved locally for user access and version control

---

## Testing Strategy

### Test Categories
- **Unit Tests**: 60+ tests covering Q&A generation, spec creation, plan generation, state management
- **Integration Tests**: 40+ tests covering end-to-end flows (YES → spec → plan → execution)
- **End-to-End Tests**: 10+ tests simulating complete project lifecycle (book example)
- **Constitutional Compliance Tests**: 20+ tests validating all 5 articles

### Test Data Requirements
- **Mock Projects**: 5 project types (book, workflow, decision, research, automation)
- **Mock Q&A Transcripts**: 10 complete Q&A sessions with varying answer quality
- **Mock User Responses**: 100+ check-in responses (YES, NO, clarifications, ambiguous)
- **Edge Cases**: Incomplete answers, contradictory responses, changed requirements

### Test Environment Requirements
- **Local Firestore Emulator**: For integration tests without hitting production Firestore
- **Mock LLM Responses**: Deterministic GPT-5 responses for reproducible tests
- **Time Mocking**: Control clock for timing-sensitive tests (quiet hours, daily check-ins)

---

## Implementation Phases

### Phase 3.1: Project Initialization Core
- **Scope**: Q&A engine, spec generation, plan creation, basic state management
- **Deliverables**: `project_initializer.py`, `spec_from_conversation.py`, `models/project.py`
- **Success Criteria**: Complete book project Q&A → spec → plan flow works end-to-end

### Phase 3.2: Daily Check-in System
- **Scope**: Question generation, timing intelligence, response handling, progress tracking
- **Deliverables**: `daily_checkin.py`, `project_executor.py`, integration with preference learning
- **Success Criteria**: Daily check-ins work, 1-3 questions/day respected, state persists

### Phase 3.3: Background Execution & Real-World Tools
- **Scope**: EXECUTOR integration, MCP tools (web research, document generation), deliverable creation
- **Deliverables**: Tool integrations, background task orchestration, completion detection
- **Success Criteria**: Complete book project from YES to final draft delivered

---

## Review & Approval

### Stakeholders
- **Primary Stakeholder**: Alex (user, coach, author)
- **Technical Reviewers**: ChiefArchitect Agent, QualityEnforcer Agent
- **Constitutional Compliance**: AuditorAgent

### Review Criteria
- [x] **Completeness**: All sections filled with appropriate detail
- [x] **Clarity**: Requirements are unambiguous and testable
- [x] **Feasibility**: Technical implementation realistic with Phase 1-2 foundation
- [x] **Constitutional Compliance**: Aligns with all 5 constitutional articles
- [x] **Quality Standards**: Meets Agency quality requirements (strict typing, Result pattern, functions <50 lines)

### Approval Status
- [ ] **Stakeholder Approval**: Pending Alex review
- [ ] **Technical Approval**: Pending ChiefArchitect review
- [ ] **Constitutional Compliance**: Pending AuditorAgent review
- [ ] **Final Approval**: Pending after all reviews complete

---

## Appendices

### Appendix A: Glossary
- **Project Initialization**: The process of converting a YES response into a structured project with spec and plan
- **Q&A Phase**: 5-10 question conversation to gather requirements (5-10 minutes duration)
- **Daily Check-in**: 1-3 questions per day to gather input and advance project
- **Background Work**: Tasks EXECUTOR performs between check-ins (drafts, research, generation)
- **Micro-task**: Single task that takes <30 minutes, clear acceptance criteria
- **Project State**: Current phase, completed tasks, blockers, next actions

### Appendix B: References
- **Trinity Whitepaper**: `docs/reference/Trinity.pdf`
- **WITNESS Agent**: `trinity_protocol/witness_ambient_mode.py`
- **ARCHITECT Agent**: Receives patterns, formulates questions
- **Preference Learning**: `trinity_protocol/preference_learning.py`
- **Human Review Queue**: `trinity_protocol/human_review_queue.py`

### Appendix C: Related Documents
- **ADR-016**: Ambient Listener Architecture (Phase 1 foundation)
- **Spec-017**: Proactive Question Engine (Phase 2, question formulation)
- **Plan-017**: Ambient Intelligence System Implementation
- **Plan-018**: Project Initialization Implementation (this spec's plan)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-01 | Planner Agent | Initial specification for Phase 3 |

---

*"A well-initialized project is halfway complete. Clear requirements and daily momentum complete the rest."*
