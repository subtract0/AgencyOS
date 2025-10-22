# Agency OS User Manual

> **The Complete Guide to Autonomous Multi-Agent Development**

**Version**: 1.0
**Last Updated**: 2025-10-01
**Status**: Production Ready
**Test Coverage**: 1,711 tests passing (100% success rate)

---

## Table of Contents

1. [Introduction & Quick Start](#1-introduction--quick-start)
2. [Constitutional Governance](#2-constitutional-governance)
3. [Prime Commands Guide](#3-prime-commands-guide)
4. [Agent Architecture](#4-agent-architecture)
5. [Tool Reference](#5-tool-reference)
6. [Development Workflows](#6-development-workflows)
7. [Memory & Learning Systems](#7-memory--learning-systems)
8. [Testing & Quality](#8-testing--quality)
9. [Production Operations](#9-production-operations)
10. [Advanced Topics](#10-advanced-topics)

---

## 1. Introduction & Quick Start

### What is Agency OS?

Agency OS is an autonomous multi-agent development system that orchestrates specialized AI agents to write, test, and maintain high-quality code. Built on constitutional principles, Agency OS enforces strict quality standards while enabling rapid, autonomous development.

**Key Features:**

- 🤖 **11 Specialized Agents** - Each with focused expertise (planning, coding, testing, quality enforcement)
- ⚖️ **Constitutional Governance** - 5 unbreakable articles enforcing quality, context, and learning
- 🧠 **VectorStore Learning** - Cross-session pattern recognition and institutional memory
- 🔧 **35+ Tools** - File operations, git workflow, autonomous healing, analysis
- 🛡️ **100% Quality Standard** - Zero test failures, automated enforcement, no bypasses
- 📊 **1,711 Tests** - Comprehensive coverage with 100% pass rate
- 🔄 **Self-Healing** - Autonomous error detection and fixing

**Why Agency OS?**

Traditional development requires constant context switching, manual testing, and vigilant code review. Agency OS handles the entire development lifecycle autonomously:

- **Write specifications** → Planner creates formal specs
- **Generate code** → CodingAgent implements with TDD
- **Run tests** → TestGenerator ensures coverage
- **Enforce quality** → QualityEnforcer validates constitutional compliance
- **Learn from experience** → LearningAgent extracts patterns
- **Merge to production** → MergerAgent handles integration

### 5-Minute Setup Guide

**Prerequisites:**

- Python 3.11+
- OpenAI API key (for GPT-5 access)
- Git repository (recommended)

**Installation:**

```bash
# Clone the repository
git clone https://github.com/yourusername/Agency.git
cd Agency

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

**Essential Environment Variables:**

Create `.env` file:

```bash
# Core configuration
OPENAI_API_KEY=sk-your-api-key-here
AGENCY_MODEL=gpt-5  # Global default model

# Optional: Per-agent model overrides
PLANNER_MODEL=gpt-5
CODER_MODEL=gpt-5
QUALITY_ENFORCER_MODEL=gpt-5
SUMMARY_MODEL=gpt-5-mini  # Cost-efficient for summaries

# Memory & Learning
USE_ENHANCED_MEMORY=true  # Enable VectorStore
FRESH_USE_FIRESTORE=false  # Use in-memory (dev) or Firestore (prod)

# Testing
FORCE_RUN_ALL_TESTS=1  # Run full test suite
```

**Verify Installation:**

```bash
# Run health check
python agency.py health

# Run full test suite (should show 100% pass rate)
python run_tests.py --run-all

# Expected output:
# ✅ 1,711 tests passed
# ✅ 0 tests failed
# ✅ Test success rate: 100.0%
```

### Your First Autonomous Task

Let's use Agency OS to implement a simple feature autonomously.

**Step 1: Start a Prime Session**

Every Agency OS session MUST begin with a prime command to load context:

```bash
# Launch Agency OS
python agency.py run
```

**Step 2: Initialize with /prime_cc**

In the Agency OS interface:

```
You: /prime_cc
```

This command:
- Loads the codebase map
- Reads constitutional requirements
- Initializes agent context
- Prepares shared memory

**Step 3: Request a Feature**

```
You: Create a utility function that validates email addresses using regex.
     Include comprehensive tests following the NECESSARY pattern.
```

**Step 4: Watch Agency Work**

Agency OS autonomously:

1. **PlannerAgent** analyzes the request and creates a task plan
2. **TestGeneratorAgent** writes tests FIRST (TDD mandate)
3. **CodingAgent** implements the email validator
4. **QualityEnforcer** validates constitutional compliance
5. **MergerAgent** commits the changes to git

**Step 5: Review the Output**

Agency OS shows you:

```
✅ Tests written: test_email_validator.py (8 tests)
✅ Implementation: shared/validators/email.py (42 lines)
✅ Constitutional compliance: PASSED
✅ Test results: 8/8 passed (100%)
✅ Git commit: feat: Add email validator with comprehensive tests

📊 Files created:
  - /Users/you/Agency/shared/validators/email.py
  - /Users/you/Agency/tests/unit/shared/validators/test_email_validator.py
```

### Understanding the Output

Agency OS provides structured output for every operation:

**Success Output:**

```
✅ [Agent Name] - [Action Completed]
📊 [Metrics/Statistics]
📁 [Files Modified]
🔍 [Validation Results]
```

**Error Output:**

```
❌ [Error Type]: [Description]
🔧 [Autonomous Fix Attempted]
✅ [Fix Result]
```

**Learning Output:**

```
🧠 Pattern learned: [Pattern description]
📈 Confidence: 0.85 (3 occurrences)
💾 Stored in VectorStore for future sessions
```

### User Story: Sarah's First Day - Deploying a Feature Without Writing Code

**Persona**: Sarah, Senior Product Manager (non-technical)

**Situation**: Sarah needs to add a "forgot password" feature to her company's web application. Traditionally, she'd write a requirements doc, schedule meetings with engineers, wait for implementation, then test and iterate. This process takes 2-3 weeks.

**Solution**: Sarah uses Agency OS

```
Sarah: /prime plan_and_execute

Sarah: I need a forgot password feature that:
       - Sends password reset emails
       - Expires reset links after 1 hour
       - Logs all reset attempts
       - Works with our existing user database

Agency OS:
✅ PlannerAgent: Created formal specification (specs/forgot-password.md)
✅ ChiefArchitect: Created ADR-018 for security decisions
✅ PlannerAgent: Generated implementation plan (plans/forgot-password-plan.md)
✅ CodingAgent: Implemented password reset service (TDD)
✅ TestGenerator: Created 23 comprehensive tests
✅ QualityEnforcer: Validated constitutional compliance
✅ All tests passed (23/23)
✅ MergerAgent: Created PR #142

⏱️  Total time: 8 minutes
📊 Files created: 5 (2 implementation, 3 test files)
🧪 Test coverage: 100%
🔒 Security review: PASSED
```

**Outcome**: Sarah deployed a production-ready feature in 8 minutes without writing a single line of code. The implementation includes comprehensive tests, security best practices, and full documentation.

**Key Takeaway**: Agency OS democratizes software development. Non-technical stakeholders can ship production code autonomously by describing requirements in plain English.

---

## 2. Constitutional Governance

### Why Constitutional Governance Matters

Traditional development teams rely on code review, manual testing, and developer discipline. Agency OS replaces these human processes with **machine-enforceable constitutional law**.

**The Problem with Human Governance:**

- ❌ Code review is subjective and inconsistent
- ❌ Manual testing is skipped under deadlines
- ❌ "Just this once" exceptions accumulate into technical debt
- ❌ Quality standards degrade over time

**The Solution: Constitutional Enforcement:**

- ✅ Quality rules are absolute and automated
- ✅ Zero manual overrides or emergency bypasses
- ✅ Multi-layer enforcement (pre-commit, agent, CI, branch protection)
- ✅ Self-healing capabilities fix violations autonomously

### The 5 Articles Explained

Agency OS is governed by 5 constitutional articles. Every agent MUST validate actions against all articles before proceeding.

---

#### Article I: Complete Context Before Action

**Principle**: No action shall be taken without complete contextual understanding.

**Why It Matters**: Incomplete context leads to wasted work. Agency OS waits for full information rather than proceeding with assumptions.

**Enforcement Rules:**

```python
# Required pattern for all agents
def ensure_complete_context(operation_func, max_retries=3):
    timeout = 120000  # Start with 2 minutes

    for attempt in range(max_retries):
        result = operation_func(timeout=timeout)

        if result.timed_out:
            timeout *= 2  # Double timeout for retry
            continue

        if result.incomplete:
            continue  # Retry with same timeout

        if result.has_failures():
            raise Exception("STOP: Fix failures before proceeding")

        return result

    raise Exception("Unable to obtain complete context")
```

**Real-World Example:**

```
❌ BAD (Incomplete Context):
CodingAgent: "Test suite timed out after 2 minutes. I'll assume tests pass."

✅ GOOD (Article I Compliance):
CodingAgent: "Test suite timed out. Retrying with 4-minute timeout..."
[Wait for completion]
CodingAgent: "All 1,711 tests passed (100%). Context complete."
```

**Violation Examples and Remediation:**

```python
# VIOLATION: Proceeding with partial test results
def bad_approach():
    result = run_tests(timeout=60)
    if result.timed_out:
        return "Tests probably fine"  # ❌ VIOLATION

# CORRECT: Retry with extended timeout
def article_i_compliant():
    result = run_tests(timeout=60)
    if result.timed_out:
        result = run_tests(timeout=120)  # 2x timeout
    if result.timed_out:
        result = run_tests(timeout=240)  # 4x timeout
    if result.timed_out:
        raise Exception("Unable to complete tests - blocking action")
    return result  # ✅ COMPLIANT
```

---

#### Article II: 100% Verification and Stability

**Principle**: A task is complete ONLY when 100% verified and stable.

**Why It Matters**: "95% passing tests" is indistinguishable from broken. Agency OS enforces absolute quality.

**Non-Negotiable Standards:**

1. **Test Success Rate**: Main branch MUST maintain 100% test success
2. **No Merge Without Green CI**: Failing tests block ALL other activities
3. **Tests Must Verify Real Functionality**: No deactivation or skip markers
4. **When Tests Fail**: Code is wrong, not the test

**"Delete the Fire First" Priority:**

Before ANY new feature, ALL tests must be green:

```bash
# Required pre-commit pattern
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "❌ BLOCKED by Constitution Article II"
    echo "100% test success required - no exceptions"
    exit 1
fi
```

**Definition of Done:**

```
1. Code written ✓
2. Tests written ✓
3. All tests pass ✓
4. Code review ✓
5. CI pipeline green ✓
────────────────────
= COMPLETE (not before)
```

**Real-World Example:**

```
Developer: "Can I merge this PR? Only 3 tests failing."

❌ Human Review: "Looks mostly good. Merge and fix later."

✅ Agency OS: "❌ BLOCKED by Constitution Article II.
              100% test success required - no exceptions.
              Fix 3 failing tests before merge."
```

**Violation Examples and Remediation:**

```python
# VIOLATION: Commenting out failing assertions
def test_user_creation():
    user = create_user("test@example.com")
    assert user.email == "test@example.com"
    # assert user.verified == False  # ❌ VIOLATION: Commented to pass

# CORRECT: Fix the code to pass the test
def test_user_creation():
    user = create_user("test@example.com")
    assert user.email == "test@example.com"
    assert user.verified == False  # ✅ Code fixed to set verified=False
```

---

#### Article III: Automated Merge Enforcement

**Principle**: Quality standards SHALL be technically enforced, not manually governed.

**Why It Matters**: Humans make exceptions. Machines don't. Automated enforcement eliminates "emergency" bypasses that accumulate into technical debt.

**Zero-Tolerance Policy:**

- ❌ No manual override capabilities
- ❌ No "emergency bypass" mechanisms
- ❌ No "merge now, fix later" authority
- ✅ Quality gates are absolute barriers

**Multi-Layer Enforcement:**

```
1. Pre-commit Hook
   ├─ Local enforcement
   ├─ Runs tests before commit
   └─ Blocks commit if tests fail

2. Agent Validation
   ├─ QualityEnforcer validates all changes
   ├─ Constitutional compliance check
   └─ Autonomous fix attempts

3. CI/CD Pipeline
   ├─ Remote verification
   ├─ Full test suite execution
   └─ Build and integration tests

4. Branch Protection
   ├─ Repository-level safeguards
   ├─ Require PR approval
   └─ No force pushes to main
```

**Agent Implementation:**

```python
# All agents must implement enforcement checking
def validate_constitutional_compliance(operation):
    if not passes_article_i_verification(operation):
        raise ConstitutionalViolation("Article I: Incomplete context")
    if not passes_article_ii_verification(operation):
        raise ConstitutionalViolation("Article II: Quality standards not met")
    if not passes_article_iii_verification(operation):
        raise ConstitutionalViolation("Article III: Enforcement bypassed")
    return True
```

**Real-World Example:**

```
CEO: "Production is down! Override the tests and merge the hotfix NOW!"

❌ Traditional Team: "OK, merging..." [Technical debt increases]

✅ Agency OS: "❌ BLOCKED by Constitution Article III.
              No bypass authority exists.
              Autonomous healing detected issue.
              Fix generated and verified in 47 seconds.
              ✅ Hotfix ready with 100% test success."
```

---

#### Article IV: Continuous Learning and Improvement

**Principle**: The Agency SHALL continuously improve through experiential learning.

**Why It Matters**: Static systems stagnate. Agency OS learns from every session, error, and success to become more effective over time.

**Automatic Learning Triggers:**

- ✅ After successful session completion
- ✅ After error resolution sequences
- ✅ After effective tool usage patterns
- ✅ When performance milestones achieved

**Learning Quality Standards:**

```python
# Required learning integration pattern
class ConstitutionalAgent:
    def __init__(self, agent_context):
        self.learning_store = agent_context.vector_store
        self.constitutional_compliance = True

    def before_action(self, context):
        # Check constitutional compliance
        self.validate_constitutional_adherence()
        # Apply relevant learnings
        self.apply_historical_learnings(context)

    def after_action(self, result):
        # Extract learnings from experience
        self.extract_and_store_learnings(result)
```

**Learning Parameters:**

- **Minimum Confidence**: 0.6 (60% certainty required)
- **Minimum Evidence**: 3 occurrences (pattern must repeat)
- **Storage**: VectorStore for semantic search
- **Scope**: Cross-session (institutional memory)

**Real-World Example:**

```
Session 1: CodingAgent fixes NoneType error in user service
          🧠 Pattern learned: "Check None before accessing attributes"
          📈 Confidence: 0.4 (1 occurrence) - NOT STORED

Session 2: CodingAgent fixes similar error in auth service
          🧠 Pattern updated: Confidence: 0.65 (2 occurrences) - NOT STORED

Session 3: CodingAgent fixes similar error in payment service
          🧠 Pattern confirmed: Confidence: 0.82 (3 occurrences)
          ✅ STORED in VectorStore

Session 4: CodingAgent encounters similar code pattern
          🧠 VectorStore search: Found matching pattern (confidence 0.82)
          ✅ Proactively applies None-check pattern
          ✅ Error prevented before it occurs
```

---

#### Article V: Spec-Driven Development

**Principle**: All development SHALL follow formal specification and planning processes.

**Why It Matters**: Implementation without specification leads to rework. Formal specs ensure alignment before code is written.

**Mandatory Workflows:**

```
Feature Request
    ↓
Formal Specification (spec.md)
    ├─ Goals and Non-Goals
    ├─ User Personas
    ├─ Acceptance Criteria
    └─ Success Metrics
    ↓
Technical Plan (plan.md)
    ├─ Architecture Decisions
    ├─ Agent Assignments
    ├─ Tool Usage Strategy
    └─ Integration Contracts
    ↓
Task Breakdown (TodoWrite)
    ├─ Granular, verifiable tasks
    ├─ References to spec sections
    └─ Progress tracking
    ↓
Implementation
    ├─ TDD (tests first)
    ├─ Constitutional compliance
    └─ Continuous validation
```

**Agent Compliance Pattern:**

```python
# Required pattern for all planning agents
def constitutional_planning_process(feature_request):
    # 1. Read constitution for compliance requirements
    constitution = read_constitution()

    # 2. Generate specification following Article V requirements
    spec = generate_specification(feature_request, constitution)

    # 3. Create implementation plan with constitutional validation
    plan = create_implementation_plan(spec, constitution)

    # 4. Break down into constitutional-compliant tasks
    tasks = create_granular_tasks(plan, constitution)

    return spec, plan, tasks
```

**When to Skip Spec-Kit (Simple Tasks):**

For trivial 1-2 step tasks, spec-kit can be bypassed, but constitutional compliance MUST still be validated:

```python
# Simple task: Add a helper function
if is_simple_task(request):
    # Skip formal spec creation
    validate_constitutional_compliance(request)
    proceed_with_implementation()
else:
    # Complex task: Follow Article V
    create_specification()
    create_technical_plan()
    break_into_tasks()
    implement_with_validation()
```

**Real-World Example:**

```
Request: "Add dark mode to the application"

❌ Without Article V:
   - Developer starts coding immediately
   - Realizes dark mode breaks existing themes
   - Refactors color system (3 days wasted)
   - Discovers accessibility issues
   - Total time: 2 weeks

✅ With Article V (Agency OS):
   - PlannerAgent creates spec (5 minutes)
   - Identifies: color system refactor needed FIRST
   - ChiefArchitect creates ADR for color architecture
   - Plan includes: theme system, color tokens, accessibility
   - Implementation follows validated plan
   - Total time: 2 days (7x faster, zero rework)
```

---

### Constitutional Compliance Validator

Every agent must validate actions before execution:

```python
from shared.constitutional_validator import constitutional_compliance

@constitutional_compliance
def create_planner_agent(model: str = "gpt-5", agent_context=None):
    """Factory decorated with constitutional validator.

    The @constitutional_compliance decorator ensures:
    - Article I: Complete context loaded
    - Article II: Quality standards enforced
    - Article III: Automated checks enabled
    - Article IV: Learning integration active
    - Article V: Spec-driven process followed
    """
    # Agent creation logic...
    return agent
```

### User Story: How Agency Maintains 100% Quality Standards

**Persona**: Alex, DevOps Engineer at a Fintech Startup

**Situation**: Alex's team struggles with flaky tests and inconsistent code quality. Their main branch fails 5-10% of the time. "Hotfix" branches regularly bypass code review. Tech debt is accumulating faster than they can address it.

**Solution**: Alex deploys Agency OS with constitutional governance

**Week 1: Transition**

```bash
# Enable constitutional enforcement
git config core.hooksPath .agency/hooks
python agency.py enforce-constitution --strict

Result:
- 47 pre-existing test failures discovered
- QualityEnforcer blocked 12 attempted merges
- Developers frustrated: "We can't ship anything!"
```

**Week 2: Healing**

```bash
# Activate autonomous healing
python agency.py healing-mode --auto-fix

Result:
- 47 test failures fixed autonomously (95% success rate)
- Remaining 3 failures required human intervention
- Main branch: 100% test success (first time in 2 years)
```

**Week 3: Enforcement**

```
Developers adapt to Article II:
- "Fix tests first, then add features"
- No more "I'll fix it later" promises
- Quality gates become routine

Attempted bypasses: 8
Successful bypasses: 0 (Article III enforcement)
Developer satisfaction: Initially low, rising
```

**Month 2: Results**

```
Metrics Before Agency OS:
- Test success rate: 90-95%
- Hotfix frequency: 3-4 per week
- Production incidents: 2-3 per month
- Time debugging flaky tests: 8 hours/week

Metrics After Agency OS:
- Test success rate: 100% (enforced)
- Hotfix frequency: 0.5 per week (60% reduction)
- Production incidents: 0.3 per month (85% reduction)
- Time debugging: 0 hours (autonomous healing)

Developer satisfaction: High
Reason: "I don't worry about code quality anymore. Agency handles it."
```

**Key Takeaway**: Constitutional governance transforms quality from a human responsibility into an automated guarantee. Initial friction gives way to unprecedented reliability.

---

## 3. Prime Commands Guide

Every Agency OS session MUST begin with a prime command. Prime commands load context, initialize agents, and set up the operational environment.

**Available Prime Commands:**

1. `/prime_cc` - General codebase understanding
2. `/prime plan_and_execute` - Full development cycle
3. `/prime audit_and_refactor` - Quality analysis and improvement
4. `/prime create_tool` - New tool development
5. `/prime healing_mode` - Autonomous error fixing
6. `/prime web_research` - Web scraping and research

---

### /prime_cc - Codebase Understanding

**Purpose**: Gain general understanding of codebase with focus on improvements.

**When to Use:**

- Starting a new session
- Onboarding to existing codebase
- General exploration and analysis
- Before making architectural decisions

**Prerequisites:**

- Valid git repository
- `.env` file configured with `OPENAI_API_KEY`

**Step-by-Step Execution:**

```bash
# 1. Start Agency OS
python agency.py run

# 2. Execute prime command
You: /prime_cc

# 3. Agency OS responds
✅ Loading codebase map...
✅ Reading constitution.md...
✅ Analyzing ADR index...
✅ Initializing agent context...
✅ Loading VectorStore memories...

📊 Codebase Summary:
   - 11 agents configured
   - 35+ tools available
   - 1,711 tests (100% passing)
   - 15 ADRs documented
   - 5 constitutional articles active

🎯 Ready for task assignment
```

**Expected Output:**

```
🗺️  CODEBASE MAP LOADED

Agents:
  ✅ ChiefArchitect - Strategic oversight
  ✅ Planner - Spec → Plan transformation
  ✅ CodingAgent - TDD implementation
  ✅ QualityEnforcer - Constitutional compliance
  ✅ Auditor - Quality analysis
  ✅ TestGenerator - Test creation
  ✅ LearningAgent - Pattern extraction
  ✅ Merger - Integration and PR management
  ✅ Toolsmith - Tool development
  ✅ Summary - Task summaries

Tools Available:
  📁 File Operations: read, write, edit, multi_edit, glob, grep
  🔧 Git: status, diff, log, show
  ⚙️  Execution: bash (validated)
  🔍 Analysis: analyze_type_patterns, constitution_check
  🛠️  Healing: auto_fix_nonetype, apply_and_verify_patch

Constitutional Status:
  ✅ Article I: Context verification active
  ✅ Article II: 100% test success enforced
  ✅ Article III: Automated enforcement enabled
  ✅ Article IV: Learning integration active
  ✅ Article V: Spec-driven process ready

🧠 VectorStore: 47 patterns learned (confidence ≥ 0.6)

Ready for instructions.
```

**Troubleshooting:**

```
❌ Error: "Constitution not found"
Fix: Ensure constitution.md exists in repository root

❌ Error: "AgentContext initialization failed"
Fix: Check .env file has OPENAI_API_KEY configured

❌ Error: "VectorStore unavailable"
Fix: Set USE_ENHANCED_MEMORY=true in .env
```

**User Story: Jake's Codebase Exploration**

**Persona**: Jake, Senior Engineer joining an existing team

**Challenge**: Jake needs to understand a 50,000-line codebase before making changes.

```bash
Jake: /prime_cc

Agency OS:
✅ Analyzed codebase structure
✅ Identified 11 core modules
✅ Mapped dependencies
✅ Found 3 architectural decision records

Jake: What's the authentication flow?

ChiefArchitect:
📖 Authentication Architecture (ADR-012):
   - JWT tokens with 1-hour expiration
   - Refresh tokens stored in Redis
   - OAuth2 for social login

🔍 Relevant files:
   - auth/jwt_handler.py (lines 45-89)
   - auth/oauth_provider.py (lines 12-67)
   - middleware/auth_middleware.py (lines 23-45)

Jake: Are there any known issues?

Auditor:
⚠️  3 potential issues found:
   1. auth/jwt_handler.py: Token expiration not validated (line 67)
   2. middleware/auth_middleware.py: Missing rate limiting
   3. oauth_provider.py: Refresh token rotation not implemented

💡 Recommended: Review ADR-012 and security best practices

Result: Jake understands the auth system in 5 minutes vs. 2 days
```

---

### /prime plan_and_execute - Full Development Cycle

**Purpose**: Complete development workflow from specification to implementation.

**When to Use:**

- Building new features
- Complex refactoring projects
- Multi-component changes
- When full spec-driven development is required

**Prerequisites:**

- Clear feature requirements
- Acceptance criteria defined
- `/prime_cc` executed (recommended)

**Workflow:**

```
/prime plan_and_execute
    ↓
1. PlannerAgent creates formal specification
    ↓
2. ChiefArchitect reviews architecture implications
    ↓
3. PlannerAgent generates technical plan
    ↓
4. Task breakdown with TodoWrite
    ↓
5. CodingAgent implements (TDD)
    ↓
6. TestGenerator ensures coverage
    ↓
7. QualityEnforcer validates compliance
    ↓
8. MergerAgent creates PR
```

**Step-by-Step Execution:**

```bash
# 1. Start Agency OS
python agency.py run

# 2. Execute prime command
You: /prime plan_and_execute

# 3. Agency OS initiates planning workflow
✅ Prime mode: Plan and Execute
✅ Activating: Planner, ChiefArchitect, Coder, TestGenerator, QualityEnforcer, Merger
✅ Spec-driven development (Article V) enforced

# 4. Describe your feature
You: Create a user notification system that:
     - Sends email and SMS notifications
     - Supports templates with variables
     - Tracks delivery status
     - Integrates with existing user database

# 5. Watch the autonomous workflow
[Planner creates specification]
✅ Specification created: specs/user-notification-system.md
   Goals:
   - Multi-channel notification delivery
   - Template-based messaging
   - Delivery tracking and analytics

   Non-Goals:
   - Push notifications (future phase)
   - In-app messaging (separate system)

[ChiefArchitect reviews]
✅ ADR-019 created: Notification System Architecture
   Decisions:
   - Use Twilio for SMS
   - Use SendGrid for email
   - PostgreSQL for delivery tracking
   - Redis for rate limiting

[Planner generates plan]
✅ Technical plan: plans/user-notification-system-plan.md
   Components:
   1. Notification service layer
   2. Template engine
   3. Delivery tracking system
   4. Integration adapters (Twilio, SendGrid)

   Agent assignments:
   - CodingAgent: Core implementation
   - TestGenerator: Comprehensive test suite
   - QualityEnforcer: Constitutional validation

[Task breakdown]
✅ TodoWrite: 12 tasks created
   1. Create notification service interface
   2. Implement template engine
   3. Add Twilio integration
   4. Add SendGrid integration
   5. Create delivery tracking models
   6. Implement rate limiting
   ... [remaining tasks]

[Implementation with TDD]
✅ Task 1/12: Create notification service interface
   - Tests written first (4 tests)
   - Interface implemented
   - Tests passing (4/4)

✅ Task 2/12: Implement template engine
   - Tests written first (7 tests)
   - Template engine implemented
   - Tests passing (7/7)

[Continue for all 12 tasks...]

✅ All tasks complete (12/12)
✅ Total tests: 47 (47 passing, 0 failing)
✅ Constitutional compliance: PASSED
✅ Integration tests: 8/8 passing

[Merge preparation]
✅ MergerAgent: Created PR #156
   Title: feat: Add user notification system
   Files changed: 8
   Tests added: 47
   Coverage: 100%

🎉 Feature complete and ready for merge
```

**Expected Output:**

```
📊 DEVELOPMENT CYCLE SUMMARY

Specification: specs/user-notification-system.md
Plan: plans/user-notification-system-plan.md
ADR: docs/adr/ADR-019-notification-architecture.md
Pull Request: #156

Files Created:
  notifications/
    ├── service.py (142 lines)
    ├── template_engine.py (98 lines)
    ├── integrations/
    │   ├── twilio_adapter.py (76 lines)
    │   └── sendgrid_adapter.py (81 lines)
    └── tracking.py (54 lines)

  tests/notifications/
    ├── test_service.py (189 lines, 12 tests)
    ├── test_template_engine.py (134 lines, 7 tests)
    ├── test_integrations.py (156 lines, 20 tests)
    └── test_tracking.py (87 lines, 8 tests)

Metrics:
  ⏱️  Total time: 14 minutes
  📝 Lines of code: 451 (implementation) + 566 (tests)
  🧪 Tests: 47 (100% passing)
  📊 Coverage: 100%
  ✅ Constitutional compliance: PASSED

Ready to merge: git merge pr/156
```

**Troubleshooting:**

```
❌ Error: "Specification validation failed"
Reason: Requirements too vague
Fix: Provide clear acceptance criteria and constraints

❌ Error: "Tests failing (3/47)"
Reason: Article II enforcement blocking merge
Fix: QualityEnforcer will attempt autonomous fixes
      If unsuccessful, review test failures and fix code

❌ Error: "ADR creation failed"
Reason: Architecture decision already documented
Fix: ChiefArchitect will reference existing ADR instead
```

**User Story: Building a Payment Gateway Integration**

**Persona**: Maria, Founder of an E-commerce Startup

**Challenge**: Maria needs to integrate Stripe payments but has no backend experience.

```bash
Maria: /prime plan_and_execute

Maria: Add Stripe payment integration with:
       - Checkout flow
       - Webhook handling
       - Refund support
       - Payment history

Agency OS Workflow:

[Minute 1-2: Planning]
✅ Planner: Created formal spec
✅ ChiefArchitect: ADR-020 (security decisions)
✅ Planner: Technical plan ready

[Minute 3-10: Implementation]
✅ CodingAgent: Implemented Stripe service
✅ TestGenerator: 34 tests created
✅ QualityEnforcer: Security validation passed

[Minute 11-12: Integration]
✅ MergerAgent: PR #87 created
✅ All tests passing (34/34)

Maria's Result:
- Production-ready Stripe integration: 12 minutes
- Zero security vulnerabilities
- Comprehensive test coverage
- Full webhook handling
- Refund workflow implemented

Traditional Approach:
- Hire backend developer: 2 weeks recruiting
- Implementation: 1 week
- Testing: 3 days
- Security review: 2 days
- Total: 3-4 weeks

Agency OS: 12 minutes (2,520x faster)
```

---

### /prime audit_and_refactor - Quality Analysis

**Purpose**: Analyze codebase quality and implement improvements autonomously.

**When to Use:**

- Periodic code quality checks
- Before major releases
- After rapid development sprints
- When tech debt accumulates

**Prerequisites:**

- Existing codebase to analyze
- Tests in place (for validation)

**Step-by-Step Execution:**

```bash
# 1. Start Agency OS
python agency.py run

# 2. Execute audit prime
You: /prime audit_and_refactor

# 3. Specify scope (optional)
You: Focus on authentication module

# 4. Watch audit process
✅ AuditorAgent: Analyzing codebase...
   Scanning: auth/*.py (12 files)

🔍 Quality Analysis Results:

NECESSARY Pattern Compliance:
  ✅ Named clearly: 47/47 tests
  ✅ Executable in isolation: 45/47 tests
  ⚠️  Comprehensive coverage: 89% (target: 100%)
  ✅ Error handling validated: 47/47 tests
  ✅ State changes verified: 47/47 tests
  ✅ Side effects controlled: 47/47 tests
  ✅ Assertions meaningful: 47/47 tests
  ✅ Repeatable results: 47/47 tests
  ✅ Yield fast execution: Avg 23ms/test

Code Quality Issues:
  ⚠️  3 functions exceed 50-line limit
  ⚠️  2 files use Dict[str, Any] (should use Pydantic)
  ⚠️  1 module missing type hints
  ✅ No use of try/except for control flow
  ✅ Result<T,E> pattern used consistently

Security Issues:
  ⚠️  JWT expiration not validated (auth/jwt.py:67)
  ⚠️  Password hashing uses MD5 (auth/password.py:23)
  ✅ No hardcoded secrets detected
  ✅ Input validation in place

[QualityEnforcer activates autonomous fixes]

✅ Refactoring 3 long functions...
   - auth/login.py:login_user() split into 3 functions
   - auth/register.py:create_account() refactored
   - auth/session.py:validate_session() simplified

✅ Replacing Dict[str, Any] with Pydantic models...
   - Created UserModel (auth/models.py)
   - Created SessionModel (auth/models.py)
   - Updated 8 function signatures

✅ Adding type hints...
   - auth/utils.py: 12 functions annotated

✅ Fixing security issues...
   - JWT expiration validation added
   - Password hashing upgraded to bcrypt
   - Added security tests (6 new tests)

📊 Refactoring Complete
   Files modified: 8
   Functions refactored: 3
   Models created: 2
   Security fixes: 2
   Tests added: 6

🧪 Validation
   Running all tests...
   ✅ 53/53 tests passing (100%)

✅ All changes committed
   Commit: refactor: Improve auth module quality and security
```

**Expected Output:**

```
📋 AUDIT REPORT

Scope: authentication module (12 files, 1,847 lines)

Quality Score: 87/100 (Good)
  Code Quality: 92/100
  Test Quality: 95/100
  Security: 78/100 (IMPROVED to 95/100 after fixes)
  Type Safety: 85/100 (IMPROVED to 100/100 after fixes)

Issues Found: 8
Issues Fixed Autonomously: 6
Issues Requiring Human Review: 2

Autonomous Fixes Applied:
  ✅ Refactored 3 functions exceeding 50 lines
  ✅ Replaced Dict[str, Any] with Pydantic models (2 instances)
  ✅ Added type hints to auth/utils.py (12 functions)
  ✅ Fixed JWT expiration validation
  ✅ Upgraded password hashing (MD5 → bcrypt)
  ✅ Added security tests (6 tests)

Remaining Issues (Human Review Required):
  ⚠️  auth/oauth.py:45 - OAuth token refresh logic complex
      Recommendation: Consider extracting to separate service

  ⚠️  auth/permissions.py:89 - Cyclic dependency detected
      Recommendation: Refactor permission checking to avoid circular imports

Learning Patterns Extracted:
  🧠 Pattern: "JWT validation requires expiration check"
      Confidence: 0.87 (5 occurrences)
      Stored in VectorStore

  🧠 Pattern: "Pydantic models preferred over Dict[str, Any]"
      Confidence: 0.91 (8 occurrences)
      Stored in VectorStore

Next Steps:
  1. Review remaining 2 issues
  2. Run full test suite: python run_tests.py --run-all
  3. Merge changes: git merge audit-fixes
```

**Troubleshooting:**

```
❌ Error: "AST parsing failed"
Reason: Syntax error in code
Fix: Run python -m py_compile <file> to identify syntax errors

❌ Error: "Cannot refactor - tests failing"
Reason: Article II enforcement (100% test success required)
Fix: Fix failing tests before requesting audit

❌ Error: "Insufficient context for refactoring"
Reason: Missing type information or unclear code intent
Fix: Add type hints and docstrings for better analysis
```

**User Story: Preparing for Security Audit**

**Persona**: David, CTO preparing for SOC 2 compliance

**Situation**: David's company needs SOC 2 certification. Security auditors require evidence of code quality practices.

```bash
David: /prime audit_and_refactor

David: Full security and quality audit across entire codebase

Agency OS:
✅ Scanning 127 files (18,432 lines)...

[5 minutes later]

📊 COMPREHENSIVE AUDIT REPORT

Security Score: 68/100 (Needs Improvement)
Quality Score: 82/100 (Good)

Critical Security Issues: 4
  ❌ SQL injection risk (database/queries.py:156)
  ❌ Hardcoded API key (services/payment.py:23)
  ❌ Unvalidated user input (api/endpoints.py:89)
  ❌ Missing rate limiting (api/auth.py:45)

[Autonomous Healing Activates]

✅ Fixed SQL injection - parameterized queries
✅ Moved API key to environment variable
✅ Added input validation with Zod schema
✅ Implemented rate limiting (100 req/min)

[Final Validation]

✅ Security Score: 95/100 (Excellent)
✅ All critical issues resolved
✅ 1,847 tests passing (100%)

📄 Generated compliance report:
   - docs/audit/security-audit-2025-10-01.md
   - Evidence of automated quality enforcement
   - Test coverage metrics
   - Security fix audit trail

David's Result:
- SOC 2 audit preparation: 15 minutes
- Critical vulnerabilities: 4 found, 4 fixed
- Compliance documentation: Auto-generated
- Auditor satisfaction: High
```

---

### /prime create_tool - Tool Development

**Purpose**: Develop new agent tools with TDD and API design.

**When to Use:**

- Creating custom tools for specific workflows
- Extending Agency OS capabilities
- Building domain-specific integrations

**Prerequisites:**

- Clear tool requirements
- Understanding of Agency OS tool architecture
- Familiarity with `agency_swarm.tools.BaseTool`

**Step-by-Step Execution:**

```bash
# 1. Start Agency OS
python agency.py run

# 2. Execute tool creation prime
You: /prime create_tool

# 3. Describe the tool
You: Create a tool that analyzes Python code complexity:
     - Calculate cyclomatic complexity
     - Identify functions exceeding complexity threshold
     - Generate refactoring suggestions
     - Output JSON report

# 4. Toolsmith agent workflow
✅ ToolsmithAgent activated
✅ Analyzing tool requirements...
✅ Designing tool API...

📋 Tool Design:
   Name: AnalyzeComplexity
   Input: file_path (str), threshold (int, default=10)
   Output: ComplexityReport (Pydantic model)

[TDD Phase: Tests First]

✅ Writing tests...
   tests/tools/test_analyze_complexity.py

   - test_simple_function_low_complexity()
   - test_nested_loops_high_complexity()
   - test_multiple_files()
   - test_threshold_filtering()
   - test_refactoring_suggestions()
   - test_invalid_file_path()
   - test_json_report_format()

✅ Tests written: 7 tests
✅ Running tests: 0/7 passing (expected - no implementation yet)

[Implementation Phase]

✅ Implementing AnalyzeComplexity tool...
   tools/analyze_complexity.py

   - AST traversal logic
   - Cyclomatic complexity calculation
   - Refactoring suggestion engine
   - JSON report generation

✅ Implementation complete
✅ Running tests: 7/7 passing (100%)

[Validation Phase]

✅ QualityEnforcer validation...
   - Type safety: PASSED
   - Function complexity: PASSED (all <50 lines)
   - Error handling: PASSED (Result<T,E> pattern)
   - Documentation: PASSED (JSDoc complete)

✅ Integration test...
   - Tool integrates with agency_swarm: PASSED
   - Pydantic model validation: PASSED
   - JSON serialization: PASSED

[Registration]

✅ Tool registered in tools/__init__.py
✅ Added to ToolsmithAgent tool list
✅ Documentation generated: docs/tools/analyze_complexity.md

🎉 Tool creation complete!
   Tool: AnalyzeComplexity
   Location: tools/analyze_complexity.py
   Tests: tests/tools/test_analyze_complexity.py
   Docs: docs/tools/analyze_complexity.md
```

**Example Tool Usage:**

```python
from tools.analyze_complexity import AnalyzeComplexity

# Create tool instance
tool = AnalyzeComplexity(
    file_path="auth/login.py",
    threshold=10
)

# Run analysis
result = tool.run()

# Handle result
if result.is_ok():
    report = result.unwrap()
    print(f"Total functions: {report.total_functions}")
    print(f"Complex functions: {len(report.complex_functions)}")

    for func in report.complex_functions:
        print(f"  {func.name}: complexity {func.complexity}")
        print(f"  Suggestion: {func.refactoring_suggestion}")
else:
    print(f"Error: {result.unwrap_err()}")
```

**Output:**

```json
{
  "total_functions": 12,
  "complex_functions": [
    {
      "name": "login_user",
      "line": 45,
      "complexity": 15,
      "refactoring_suggestion": "Extract validation logic to separate function"
    },
    {
      "name": "validate_session",
      "line": 89,
      "complexity": 12,
      "refactoring_suggestion": "Use early returns to reduce nesting"
    }
  ],
  "average_complexity": 6.8,
  "max_complexity": 15
}
```

**User Story: Building a Custom Database Migration Tool**

**Persona**: Lisa, Senior Database Engineer

**Challenge**: Lisa needs a custom tool to analyze database migrations for potential issues before applying them.

```bash
Lisa: /prime create_tool

Lisa: Create a tool to validate database migrations:
      - Check for breaking changes
      - Verify rollback scripts exist
      - Detect missing indexes
      - Estimate migration time

ToolsmithAgent:
✅ Tests written: 11 tests
✅ Implementation: tools/validate_migration.py
✅ All tests passing (11/11)

Lisa uses the tool:

from tools.validate_migration import ValidateMigration

tool = ValidateMigration(migration_file="migrations/0042_add_indexes.sql")
result = tool.run()

Output:
{
  "breaking_changes": [],
  "rollback_available": true,
  "missing_indexes": ["users.email", "orders.created_at"],
  "estimated_time": "12 minutes",
  "risk_level": "low"
}

Lisa's Result:
- Custom tool created: 8 minutes
- Production-ready with tests
- Integrated into CI pipeline
- Prevented 3 production incidents in first month
```

---

### /prime healing_mode - Autonomous Error Fixing

**Purpose**: Activate autonomous self-healing protocols for error detection and fixing.

**When to Use:**

- After test failures
- When NoneType errors occur
- For systematic error remediation
- During refactoring to catch issues early

**Prerequisites:**

- Test suite in place
- Error logs available
- `/prime_cc` executed (recommended)

**Step-by-Step Execution:**

```bash
# 1. Start Agency OS
python agency.py run

# 2. Activate healing mode
You: /prime healing_mode

✅ Healing mode activated
✅ QualityEnforcer monitoring enabled
✅ Auto-fix enabled for: NoneType, AttributeError, TypeError

# 3. Run tests to discover errors
✅ Running test suite...
   Tests: 1,711
   Passing: 1,683
   Failing: 28

❌ 28 test failures detected

# 4. Autonomous healing activates

[Error Analysis]
🔍 Analyzing failures...
   - NoneType errors: 18
   - AttributeError: 7
   - Type mismatches: 3

[Fix Generation]
🔧 Generating fixes...

Error 1/28: test_user_profile (NoneType)
  File: services/user.py:45
  Issue: user.profile accessed without None check

  ✅ Fix generated:
     + if user.profile is None:
     +     return Err("User profile not found")
     return Ok(user.profile.data)

  ✅ Tests passing: 1,684/1,711
  ✅ Fix verified and applied

Error 2/28: test_order_total (AttributeError)
  File: services/order.py:67
  Issue: 'NoneType' object has no attribute 'price'

  ✅ Fix generated:
     + if item.price is None:
     +     logger.warning(f"Item {item.id} has no price")
     +     continue
     total += item.price

  ✅ Tests passing: 1,685/1,711
  ✅ Fix verified and applied

[Continue for all 28 errors...]

✅ Healing complete
   Errors fixed: 26/28 (93% success rate)
   Errors requiring human intervention: 2

📊 Healing Summary:
   Total errors: 28
   Auto-fixed: 26
   Manual review needed: 2
   Tests passing: 1,709/1,711 (99.9%)
   Time: 3 minutes 47 seconds

Remaining Issues:
  ⚠️  test_payment_processing - Complex logic requiring domain knowledge
      File: services/payment.py:123
      Recommendation: Review payment flow logic

  ⚠️  test_email_validation - Regex pattern needs update
      File: utils/validators.py:34
      Recommendation: Update email regex to RFC 5322 standard
```

**Expected Output:**

```
🛠️  AUTONOMOUS HEALING REPORT

Session: 2025-10-01_14_23_45
Duration: 3 minutes 47 seconds
Success Rate: 93% (26/28 fixes applied)

Fixes Applied:
  ✅ NoneType errors: 18/18 fixed
     Pattern: Added None checks before attribute access

  ✅ AttributeError: 6/7 fixed
     Pattern: Validated object state before method calls

  ✅ Type mismatches: 2/3 fixed
     Pattern: Added type conversion with validation

Fix Examples:

1. services/user.py:45
   Before:
     return user.profile.data

   After:
     if user.profile is None:
         return Err("User profile not found")
     return Ok(user.profile.data)

   Tests fixed: test_user_profile, test_user_data

2. services/order.py:67
   Before:
     total += item.price

   After:
     if item.price is None:
         logger.warning(f"Item {item.id} has no price")
         continue
     total += item.price

   Tests fixed: test_order_total, test_cart_calculation

Learning Patterns Extracted:
  🧠 "None check before attribute access" (confidence: 0.92, 18 occurrences)
  🧠 "Validate object state in multi-step operations" (confidence: 0.85, 6 occurrences)

Commits Created:
  - fix: Add None checks in user service (18 fixes)
  - fix: Validate item state in order service (6 fixes)
  - fix: Add type conversion in payment service (2 fixes)

Next Steps:
  1. Review 2 remaining failures requiring human intervention
  2. Validate fixes in production-like environment
  3. Run full integration test suite
```

**User Story: Fixing a Broken Test Suite**

**Persona**: Carlos, Junior Developer inheriting legacy code

**Situation**: Carlos inherits a codebase with 147 failing tests. Previous developers left no documentation. Deadline: 1 week.

```bash
Day 1 - Monday:
Carlos: /prime healing_mode

Agency OS:
✅ 147 test failures detected
🔧 Autonomous healing activated...

[3 hours later]
✅ 134/147 errors fixed autonomously (91% success rate)
✅ 13 errors require human review

Carlos reviews 13 remaining errors:
- 8 errors: Business logic changes needed
- 5 errors: Tests incorrectly written

Day 2 - Tuesday:
Carlos fixes 8 business logic issues (with Agency OS assistance)
Carlos corrects 5 incorrect tests

Result:
✅ All 147 tests now passing (100%)
✅ Learning patterns extracted: 23 patterns
✅ Future similar errors prevented automatically

Traditional approach: 2-3 weeks debugging
Agency OS approach: 1.5 days (10x faster)

Carlos: "I would have quit on day 3 without autonomous healing."
```

---

### /prime web_research - Web Scraping and Research

**Purpose**: Initiate web scraping and research operations.

**When to Use:**

- Gathering external documentation
- Researching API specifications
- Collecting competitive intelligence
- Building knowledge bases

**Prerequisites:**

- MCP firecrawl tool installed and configured
- Valid API credentials for data sources
- Clear research objectives

**Step-by-Step Execution:**

```bash
# 1. Ensure MCP firecrawl is available
You: /prime web_research

✅ Checking MCP firecrawl availability...
✅ MCP firecrawl detected and ready

# 2. Define research objective
You: Research best practices for implementing OAuth2 in Python.
     Focus on security and user experience.

# 3. Watch research process
✅ Generating search queries...
   - "OAuth2 Python best practices security"
   - "OAuth2 implementation patterns Python"
   - "OAuth2 user experience guidelines"

✅ Scraping sources...
   - https://oauth.net/2/
   - https://www.rfc-editor.org/rfc/rfc6749
   - https://realpython.com/oauth2-implementation/
   - https://auth0.com/docs/get-started/authentication-and-authorization

✅ Extracting key information...

📚 Research Summary:

Security Best Practices:
  1. Always use HTTPS for redirect URIs
  2. Implement PKCE for public clients
  3. Validate redirect URIs strictly
  4. Use state parameter to prevent CSRF
  5. Rotate refresh tokens on use

Implementation Patterns:
  1. Use established libraries (authlib, oauthlib)
  2. Separate authorization and resource servers
  3. Implement token introspection endpoint
  4. Store tokens encrypted at rest
  5. Use short-lived access tokens (15-60 min)

User Experience:
  1. Clear consent screens
  2. Minimal scope requests
  3. Remember device for trusted users
  4. Provide revocation capabilities
  5. Transparent privacy policies

Code Examples Found:
  - 12 implementation examples
  - 5 security patterns
  - 3 common pitfalls to avoid

✅ Synthesizing into actionable plan...

📋 Recommended Implementation:

1. Use authlib for OAuth2 (most comprehensive)
2. Implement PKCE flow for mobile/SPA clients
3. Set access token expiry: 30 minutes
4. Set refresh token expiry: 30 days (rotating)
5. Implement token introspection for resource servers

🧠 Learning stored in VectorStore for future reference
```

**User Story: Researching Database Sharding Strategies**

**Persona**: Kevin, Database Architect planning for scale

**Challenge**: Kevin's database is approaching capacity. He needs to research sharding strategies before implementing.

```bash
Kevin: /prime web_research

Kevin: Research database sharding strategies for PostgreSQL.
       Our app has 50M users, growing 20% monthly.
       Focus on: horizontal sharding, partition keys, rebalancing.

Agency OS:
✅ Researching sharding strategies...
✅ Sources analyzed: 23 articles, 5 technical papers, 8 case studies

📊 Research Report:

Recommended Strategy: Range-based sharding with consistent hashing

Rationale:
  - User distribution: Predictable (by user_id)
  - Growth pattern: Linear (20% monthly)
  - Query patterns: 80% single-user queries
  - Cross-shard queries: Minimize with denormalization

Partition Key: user_id % num_shards

Shard Count: Start with 16 shards
  - Allows growth to 800M users before resharding
  - Balanced load distribution
  - Manageable operational complexity

Rebalancing Strategy:
  - Use logical shards (64) mapped to physical shards (16)
  - Rebalance by moving logical shards
  - Zero downtime with dual-write pattern

Tools Recommended:
  - pg_partman for partition management
  - pgBouncer for connection pooling
  - Citus for distributed queries (if needed)

Case Studies:
  - Instagram: User ID sharding (same approach)
  - Discord: Message ID sharding (similar scale)
  - Notion: Workspace sharding (different model)

Implementation Plan Generated:
  ✅ specs/database-sharding-strategy.md
  ✅ plans/sharding-implementation-plan.md
  ✅ Referenced: ADR-021-database-sharding.md

Kevin's Result:
- Research completed: 12 minutes
- Implementation plan: Ready
- Risk assessment: Documented
- Case studies: 8 relevant examples
- Confidence: High

Traditional approach: 2 weeks reading + 1 week planning
Agency OS: 12 minutes (2,520x faster)
```

---

## 4. Agent Architecture

Agency OS consists of 11 specialized agents, each with focused expertise and clear responsibilities. Agents communicate through shared context and coordinate autonomously.

### Agent Communication Model

```
┌─────────────────────────────────────────────────────────────┐
│                      Shared Context                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AgentContext (Memory + VectorStore + Learning)      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
    │  Chief  │       │ Planner │      │ Quality │
    │Architect│◄─────►│         │◄────►│Enforcer │
    └────┬────┘       └────┬────┘      └────┬────┘
         │                 │                 │
         │           ┌─────┴─────┐          │
         │           │           │          │
    ┌────▼────┐ ┌───▼────┐ ┌────▼────┐ ┌──▼─────┐
    │ Auditor │ │ Coder  │ │  Test   │ │Learning│
    │         │ │        │ │Generator│ │        │
    └─────────┘ └───┬────┘ └─────────┘ └────────┘
                    │
              ┌─────┴─────┐
              │           │
         ┌────▼────┐ ┌────▼────┐
         │ Merger  │ │ Summary │
         └─────────┘ └─────────┘
```

---

### ChiefArchitect Agent

**Role**: Strategic oversight, ADR creation, architectural decision-making

**Responsibilities:**

1. Create Architecture Decision Records (ADRs)
2. Evaluate technical trade-offs
3. Ensure architectural consistency
4. Guide long-term technical direction
5. Validate designs against constitutional principles

**Available Tools:**

- `read`, `write`, `edit` - Document manipulation
- `glob`, `grep` - Code analysis
- `git` - Version control inspection
- `constitution_check` - Validate compliance
- `document_generator` - ADR creation

**Configuration:**

```python
from chief_architect_agent import create_chief_architect_agent
from shared.agent_context import create_agent_context

# Create agent with custom model
context = create_agent_context()
architect = create_chief_architect_agent(
    model="gpt-5",  # or override with CHIEF_ARCHITECT_MODEL env var
    agent_context=context
)
```

**Communication Patterns:**

```
Inputs from:
  - PlannerAgent: Feature specifications requiring architectural decisions
  - QualityEnforcer: Architectural violations detected
  - User: Direct architectural questions

Outputs to:
  - PlannerAgent: ADR references for implementation plans
  - CodingAgent: Architectural guidance
  - All agents: ADR documentation for future reference
```

**Example Interaction:**

```python
from agency_swarm import Agency
from chief_architect_agent import create_chief_architect_agent
from planner_agent import create_planner_agent
from shared.agent_context import create_agent_context

# Create shared context
context = create_agent_context()

# Create agents
architect = create_chief_architect_agent(agent_context=context)
planner = create_planner_agent(agent_context=context)

# Create agency with communication flow
agency = Agency(
    [
        [architect, planner],  # Architect advises Planner
    ],
    shared_instructions="Follow constitutional principles"
)

# Run agency
result = agency.run(
    "Design caching strategy for API responses",
    recipient_agent=architect
)

print(result)
# Output:
# ✅ ADR-022 created: API Response Caching Strategy
# Decision: Use Redis for caching with 5-minute TTL
# Rationale: Balance freshness vs. database load
# Alternatives considered: In-memory cache, CDN, database query cache
# Consequences: 80% reduction in database queries, 200ms avg response time
```

**User Story: A Day in the Life of ChiefArchitect**

**Morning: Architectural Review**

```
08:00 - PlannerAgent requests guidance
Message: "User wants to add real-time notifications. WebSockets or SSE?"

ChiefArchitect analysis:
✅ Analyzed current architecture
✅ Reviewed connection pool capacity
✅ Evaluated scaling requirements

Decision: Server-Sent Events (SSE)
Rationale:
  - Simpler than WebSockets
  - Unidirectional (fits use case)
  - Better browser support
  - Easier load balancing

✅ ADR-023 created: Real-Time Notification Strategy
✅ Shared with PlannerAgent for implementation plan
```

**Midday: Code Quality Escalation**

```
12:30 - QualityEnforcer escalates architectural violation
Issue: Circular dependency between auth and user modules

ChiefArchitect investigation:
🔍 Analyzed dependency graph
🔍 Identified coupling points
🔍 Proposed refactoring strategy

Solution: Extract shared interfaces to separate module
✅ ADR-024 created: Dependency Management Strategy
✅ Refactoring plan sent to CodingAgent
```

**Afternoon: Long-term Planning**

```
15:00 - User asks about microservices migration
Question: "Should we split our monolith into microservices?"

ChiefArchitect analysis:
📊 Current system: 50K lines, 20 devs, 10K requests/min
📊 Pain points: Deployment coupling, scaling constraints
📊 Benefits: Independent scaling, team autonomy
📊 Costs: Operational complexity, distributed transactions

Decision: Gradual extraction, not big-bang rewrite
Strategy:
  1. Start with high-traffic modules (auth, payments)
  2. Use strangler fig pattern
  3. Shared database initially (avoid distributed transactions)
  4. Event-driven communication (not direct API calls)

✅ ADR-025 created: Microservices Migration Strategy
✅ 6-month roadmap generated
✅ Risk assessment documented
```

**Key Takeaway**: ChiefArchitect prevents costly architectural mistakes by providing strategic guidance before implementation begins.

---

### Planner Agent

**Role**: Specification to plan transformation, task orchestration

**Responsibilities:**

1. Create formal specifications (spec.md)
2. Generate technical plans (plan.md)
3. Break down complex features into tasks
4. Coordinate agent workflows
5. Ensure spec-driven development (Article V)

**Available Tools:**

- `read`, `write`, `edit` - Specification creation
- `todo_write` - Task breakdown
- `glob`, `grep` - Codebase analysis
- `git` - Version control
- `context_handoff` - Agent coordination
- `learning_dashboard` - Historical pattern access

**Configuration:**

```python
from planner_agent import create_planner_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
planner = create_planner_agent(
    model="gpt-5",  # Enhanced reasoning for strategic planning
    reasoning_effort="high",  # Maximum reasoning depth
    agent_context=context
)
```

**Communication Patterns:**

```
Inputs from:
  - User: Feature requests and requirements
  - ChiefArchitect: Architectural constraints and decisions
  - LearningAgent: Historical patterns and best practices

Outputs to:
  - CodingAgent: Implementation tasks and specifications
  - TestGenerator: Test strategy and acceptance criteria
  - QualityEnforcer: Quality requirements
  - All agents: Formal specifications and plans
```

**Spec-Kit Methodology:**

Planner follows the spec-kit template for all specifications:

```markdown
# Feature Name

## Goals
- Primary objective 1
- Primary objective 2
- Primary objective 3

## Non-Goals
- Out-of-scope item 1
- Out-of-scope item 2

## Personas
### User Type 1
- Needs: [specific needs]
- Pain points: [current problems]

### User Type 2
- Needs: [specific needs]
- Pain points: [current problems]

## Acceptance Criteria
1. Criterion 1 (testable and specific)
2. Criterion 2 (testable and specific)
3. Criterion 3 (testable and specific)

## Success Metrics
- Metric 1: [measurement method]
- Metric 2: [measurement method]

## Technical Constraints
- Constraint 1
- Constraint 2

## Dependencies
- Internal dependency 1
- External dependency 2
```

**Example Interaction:**

```python
from planner_agent import create_planner_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
planner = create_planner_agent(agent_context=context)

# Request feature planning
result = planner.run(
    """
    Create a rate limiting system:
    - Prevent API abuse
    - Allow 100 requests/minute per user
    - Return 429 status when exceeded
    - Provide headers showing limit/remaining
    """
)

# Planner outputs:
# 1. specs/rate-limiting-system.md (formal specification)
# 2. plans/rate-limiting-implementation.md (technical plan)
# 3. TodoWrite tasks (12 granular implementation steps)
```

**Generated Specification (specs/rate-limiting-system.md):**

```markdown
# Rate Limiting System

## Goals
- Prevent API abuse through request throttling
- Provide clear feedback to API consumers
- Minimize performance impact on legitimate users

## Non-Goals
- DDoS protection (handled at infrastructure layer)
- Per-endpoint custom limits (future enhancement)
- Billing integration (separate system)

## Personas
### API Consumer (Developer)
- Needs: Clear rate limit information to avoid errors
- Pain points: Unpredictable 429 errors without context

### Platform Operator
- Needs: Control over abuse without blocking legitimate traffic
- Pain points: Manual intervention required for rate limit adjustments

## Acceptance Criteria
1. Users limited to 100 requests/minute per API key
2. 429 status returned when limit exceeded
3. Response headers include: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
4. Rate limit counters reset every 60 seconds
5. Different limits for authenticated vs. unauthenticated users
6. Redis-based storage for distributed rate limiting

## Success Metrics
- API abuse incidents: 90% reduction
- False positive rate: <1% (legitimate users blocked)
- Latency overhead: <5ms per request
- Rate limit header accuracy: 100%

## Technical Constraints
- Must work in distributed environment (multiple servers)
- Redis required for state sharing
- No in-memory state (server restarts must not reset limits)

## Dependencies
- Redis 6.0+ (required for atomic operations)
- Existing authentication middleware (user identification)
```

**Generated Plan (plans/rate-limiting-implementation.md):**

```markdown
# Rate Limiting System Implementation Plan

## Architecture

### Components
1. **RateLimitMiddleware**: Flask/FastAPI middleware for request interception
2. **RateLimiter**: Core logic for limit checking and enforcement
3. **RedisStore**: Redis interface for distributed counters
4. **ConfigManager**: Rate limit configuration management

### Data Flow
```
Request → Auth → RateLimitMiddleware → RateLimiter → RedisStore
                       ↓                     ↓
                   Add Headers          Check/Increment
                       ↓                     ↓
                   200 OK              429 if exceeded
```

## Agent Assignments

### CodingAgent
- Implement RateLimitMiddleware
- Implement RateLimiter core logic
- Implement RedisStore interface
- Implement ConfigManager

### TestGenerator
- Unit tests for RateLimiter (8 tests minimum)
- Integration tests with Redis (5 tests minimum)
- Middleware integration tests (6 tests minimum)
- Load testing for performance validation

### QualityEnforcer
- Validate constitutional compliance
- Verify Result<T,E> pattern usage
- Ensure type safety (no Dict[Any, Any])
- Check function complexity (<50 lines)

## Tool Usage Strategy

- `read`: Analyze existing middleware patterns
- `write`: Create new rate limiting modules
- `edit`: Integrate with existing request pipeline
- `bash`: Run Redis locally for development
- `git`: Track changes and create PR

## Implementation Tasks

1. Create RateLimiter class with Redis backend
2. Implement sliding window counter algorithm
3. Add response header generation
4. Create Flask middleware integration
5. Implement configuration management
6. Write unit tests (NECESSARY pattern)
7. Write integration tests with Redis
8. Add performance benchmarks
9. Update API documentation
10. Create monitoring dashboard

## Validation Criteria

- All tests passing (100%)
- Performance: <5ms overhead per request
- Redis connection pooling working
- Distributed environment tested
- Configuration validated
- Documentation complete
```

**User Story: Planning a Complex Migration**

**Persona**: Emma, Engineering Manager

**Challenge**: Emma needs to migrate from MongoDB to PostgreSQL without downtime.

```python
Emma: (to PlannerAgent)
      Plan a zero-downtime migration from MongoDB to PostgreSQL.
      We have 50M records, 24/7 uptime requirement.

PlannerAgent:
✅ Analyzing migration requirements...
✅ Consulting LearningAgent for historical patterns...
   Found: 3 similar migrations in knowledge base
✅ Consulting ChiefArchitect for strategic guidance...
   ADR-026: Database Migration Strategy

✅ Specification created: specs/mongodb-to-postgres-migration.md
✅ Technical plan: plans/migration-implementation.md

Key Strategy: Dual-write pattern with gradual cutover

Phases:
  1. Setup: PostgreSQL schema creation (1 week)
  2. Dual-write: Write to both databases (2 weeks)
  3. Backfill: Migrate existing data (1 week)
  4. Validation: Compare data consistency (3 days)
  5. Cutover: Read from PostgreSQL (gradual, 1 week)
  6. Cleanup: Remove MongoDB (after 1 month validation)

Risk Mitigation:
  - Feature flags for rollback capability
  - Data consistency checks (automated)
  - Performance monitoring at each phase
  - Gradual traffic shifting (10%, 25%, 50%, 100%)

✅ 47 tasks created with TodoWrite
✅ Timeline: 6-7 weeks total
✅ Risk assessment: Medium (well-documented pattern)

Emma's Result:
- Migration plan: 15 minutes
- Risk-free execution roadmap
- Historical learnings applied
- Architect approval obtained
- Team confidence: High
```

**Key Takeaway**: Planner transforms vague requirements into actionable, validated plans before any code is written.

---

### CodingAgent

**Role**: Primary development agent with TDD-first implementation

**Responsibilities:**

1. Write production code following TDD principles
2. Implement features from specifications
3. Maintain strict type safety (no `Dict[Any, Any]`)
4. Use Result<T,E> pattern for error handling
5. Keep functions under 50 lines
6. Ensure constitutional compliance

**Available Tools:**

- `read`, `write`, `edit`, `multi_edit` - Code manipulation
- `glob`, `grep` - Code search
- `bash` - Test execution and validation
- `git` - Version control
- `analyze_type_patterns` - Type safety validation
- `constitution_check` - Compliance verification
- `auto_fix_nonetype` - Autonomous error fixing

**Configuration:**

```python
from coding_agent import create_coding_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
coder = create_coding_agent(
    model="gpt-5",  # Quality-critical agent
    agent_context=context
)
```

**TDD Workflow:**

```
1. Read specification → Understand requirements
2. Write tests FIRST → Define expected behavior
3. Run tests → Verify they fail (red)
4. Implement code → Minimal code to pass tests
5. Run tests → Verify they pass (green)
6. Refactor → Improve code quality
7. Run tests → Verify still passing
8. Repeat → Until all acceptance criteria met
```

**Example Interaction:**

```python
from coding_agent import create_coding_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
coder = create_coding_agent(agent_context=context)

# Request implementation
task = """
Implement email validation function following spec:
- Accepts string input
- Returns Result<bool, str>
- Validates against RFC 5322 standard
- Includes comprehensive tests
"""

result = coder.run(task)
```

**TDD Process Output:**

```
[Step 1: Write Tests First]

✅ Created: tests/unit/validators/test_email.py

from shared.validators.email import validate_email
from shared.type_definitions.result import Ok, Err

def test_valid_email_returns_ok():
    result = validate_email("user@example.com")
    assert result.is_ok()
    assert result.unwrap() == True

def test_invalid_email_missing_at_returns_err():
    result = validate_email("userexample.com")
    assert result.is_err()
    assert "Invalid email" in result.unwrap_err()

def test_invalid_email_missing_domain_returns_err():
    result = validate_email("user@")
    assert result.is_err()

def test_email_with_plus_addressing_is_valid():
    result = validate_email("user+tag@example.com")
    assert result.is_ok()

def test_email_with_subdomain_is_valid():
    result = validate_email("user@mail.example.com")
    assert result.is_ok()

def test_empty_email_returns_err():
    result = validate_email("")
    assert result.is_err()

def test_email_with_spaces_returns_err():
    result = validate_email("user @example.com")
    assert result.is_err()

def test_email_max_length_validation():
    long_email = "a" * 250 + "@example.com"
    result = validate_email(long_email)
    assert result.is_err()

[Step 2: Run Tests - Verify Failure]

✅ Running: pytest tests/unit/validators/test_email.py

❌ 8 tests failed (expected - no implementation yet)
   ModuleNotFoundError: No module named 'shared.validators.email'

[Step 3: Implement Minimal Code]

✅ Created: shared/validators/email.py

import re
from shared.type_definitions.result import Result, Ok, Err

def validate_email(email: str) -> Result[bool, str]:
    """Validate email address against RFC 5322 standard.

    Args:
        email: Email address to validate

    Returns:
        Ok(True) if valid, Err(message) if invalid
    """
    # Check empty
    if not email or not email.strip():
        return Err("Email cannot be empty")

    # Check length (RFC 5321: 254 char limit)
    if len(email) > 254:
        return Err("Email exceeds maximum length (254 characters)")

    # RFC 5322 compliant regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(pattern, email):
        return Ok(True)
    else:
        return Err(f"Invalid email format: {email}")

[Step 4: Run Tests - Verify Success]

✅ Running: pytest tests/unit/validators/test_email.py

✅ 8/8 tests passed (100%)
✅ Coverage: 100% (all lines executed)

[Step 5: Refactor]

No refactoring needed - function is 23 lines, single purpose

[Step 6: Constitutional Compliance Check]

✅ Type safety: PASSED (explicit return type Result[bool, str])
✅ No Dict[Any, Any]: PASSED
✅ Function complexity: PASSED (23 lines < 50)
✅ Error handling: PASSED (Result<T,E> pattern)
✅ Tests written first: PASSED (TDD followed)

[Complete]

📊 Implementation Summary:
   Files created: 2
   - shared/validators/email.py (23 lines)
   - tests/unit/validators/test_email.py (67 lines)

   Tests: 8/8 passing (100%)
   Constitutional compliance: PASSED
   Ready for code review
```

**Type Safety Enforcement:**

```python
# ❌ VIOLATION: Dict[Any, Any] usage
def bad_function(data: Dict[Any, Any]) -> Dict[Any, Any]:
    return {"result": data.get("value")}

# ✅ CORRECT: Pydantic model with typed fields
from pydantic import BaseModel

class InputData(BaseModel):
    value: str
    count: int

class OutputData(BaseModel):
    result: str

def good_function(data: InputData) -> OutputData:
    return OutputData(result=data.value)
```

**Result Pattern Usage:**

```python
from shared.type_definitions.result import Result, Ok, Err

def divide(a: float, b: float) -> Result[float, str]:
    """Divide two numbers safely.

    Args:
        a: Numerator
        b: Denominator

    Returns:
        Ok(result) if successful, Err(message) if division by zero
    """
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)

# Usage
result = divide(10, 2)
if result.is_ok():
    print(f"Result: {result.unwrap()}")  # Output: Result: 5.0
else:
    print(f"Error: {result.unwrap_err()}")

# Chain operations
result = divide(10, 2).and_then(lambda x: divide(x, 2))
# Result: Ok(2.5)

# Provide defaults
value = divide(10, 0).unwrap_or(0.0)
# Value: 0.0 (default since division failed)
```

**User Story: Implementing a Feature Without Manual Coding**

**Persona**: Nathan, Product Manager with basic Python knowledge

**Challenge**: Nathan needs to add a "recently viewed" feature but doesn't have time to write code.

```python
Nathan: (to CodingAgent)
        Implement "recently viewed items" feature:
        - Track last 10 items user viewed
        - Store in Redis with 7-day expiration
        - Provide API endpoint to retrieve
        - Include comprehensive tests

CodingAgent (TDD Workflow):

[Minute 1-2: Write Tests]
✅ tests/test_recently_viewed.py (12 tests)
   - test_add_item_to_recent()
   - test_retrieve_recent_items()
   - test_max_10_items_enforced()
   - test_redis_expiration_set()
   - test_duplicate_items_moved_to_top()
   ... [7 more tests]

[Minute 3-5: Implementation]
✅ services/recently_viewed.py (87 lines)
   - RecentlyViewedService class
   - Redis integration
   - 7-day TTL configuration
   - Item deduplication logic

✅ api/endpoints/recently_viewed.py (34 lines)
   - GET /api/recently-viewed endpoint
   - POST /api/recently-viewed endpoint
   - Pydantic request/response models

[Minute 6: Validation]
✅ Running tests: 12/12 passed
✅ Constitutional compliance: PASSED
✅ Integration test with Redis: PASSED

[Minute 7: Documentation]
✅ Updated API docs
✅ Added usage examples

Nathan's Result:
- Feature implemented: 7 minutes
- Code quality: Production-ready
- Test coverage: 100%
- Zero bugs in production
- Manual coding required: 0 lines
```

**Key Takeaway**: CodingAgent writes production code faster and more reliably than manual coding through strict TDD and constitutional compliance.

---

### QualityEnforcer Agent

**Role**: Constitutional compliance guardian and autonomous code healing

**Responsibilities:**

1. Validate all changes against 5 constitutional articles
2. Detect code quality violations
3. Autonomous error fixing and healing
4. Enforce testing standards (NECESSARY pattern)
5. Block non-compliant merges

**Available Tools:**

- `constitution_check` - Validate compliance
- `analyze_type_patterns` - Type safety verification
- `auto_fix_nonetype` - NoneType error fixing
- `apply_and_verify_patch` - Safe code patching
- `bash` - Test execution
- `read`, `edit`, `multi_edit` - Code inspection and fixing

**Configuration:**

```python
from quality_enforcer_agent import create_quality_enforcer_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
enforcer = create_quality_enforcer_agent(
    model="gpt-5",  # Quality-critical agent
    agent_context=context
)
```

**Validation Workflow:**

```
1. Receive code changes
2. Run constitutional compliance check
3. Detect violations
4. Attempt autonomous fixes
5. Verify fixes with tests
6. Report results
7. Block merge if unfixable
```

**Example Interaction:**

```python
from quality_enforcer_agent import create_quality_enforcer_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
enforcer = create_quality_enforcer_agent(agent_context=context)

# Submit code for validation
result = enforcer.run("Validate changes in PR #142")
```

**Constitutional Validation Output:**

```
🔍 CONSTITUTIONAL COMPLIANCE VALIDATION

Pull Request: #142
Files changed: 5
Lines added: 234
Lines removed: 67

[Article I: Complete Context]
✅ All tests run to completion
✅ No timeouts during validation
✅ Full context verified

[Article II: 100% Verification]
✅ Test success rate: 100% (1,719/1,719)
✅ No skipped or deactivated tests
✅ All assertions meaningful

[Article III: Automated Enforcement]
✅ Pre-commit hooks active
✅ CI pipeline configured
✅ Branch protection enabled

[Article IV: Learning Integration]
✅ Historical patterns consulted
✅ Similar implementations reviewed
✅ Best practices applied

[Article V: Spec-Driven Development]
✅ Changes trace to spec: specs/user-profile.md
✅ Implementation matches plan: plans/profile-implementation.md
✅ All acceptance criteria met

CODE QUALITY VALIDATION:

Type Safety:
✅ No Dict[Any, Any] usage
✅ All function signatures typed
✅ Pydantic models used correctly

Function Complexity:
✅ All functions <50 lines
   Longest: 42 lines (format_user_data)

Error Handling:
✅ Result<T,E> pattern used
✅ No try/except for control flow
✅ All error paths tested

Test Quality (NECESSARY Pattern):
✅ Named clearly: 8/8 tests
✅ Executable in isolation: 8/8 tests
✅ Comprehensive coverage: 100%
✅ Error handling validated: 8/8 tests
✅ State changes verified: 8/8 tests
✅ Side effects controlled: 8/8 tests
✅ Assertions meaningful: 8/8 tests
✅ Repeatable results: 8/8 tests
✅ Yield fast execution: Avg 18ms/test

SECURITY VALIDATION:

✅ No hardcoded secrets
✅ Input validation present
✅ SQL injection prevention (parameterized queries)
✅ XSS prevention (output escaping)
✅ Authentication required on endpoints

🎉 VALIDATION RESULT: PASSED

All constitutional requirements met.
Code quality: Excellent (98/100)
Ready for merge approval.
```

**Autonomous Healing Example:**

```
🛠️  AUTONOMOUS HEALING ACTIVATED

Issue detected: NoneType error in user_service.py:45

[Analysis]
Error: 'NoneType' object has no attribute 'email'
Location: services/user_service.py:45
Code: return user.email

[Root Cause]
Function get_user() can return None when user not found
No None-check before accessing .email attribute

[Fix Generation]
✅ Generated fix:
   Before:
     def get_user_email(user_id: str) -> str:
         user = get_user(user_id)
         return user.email  # ❌ Crashes if user is None

   After:
     def get_user_email(user_id: str) -> Result[str, str]:
         user = get_user(user_id)
         if user is None:
             return Err(f"User {user_id} not found")
         return Ok(user.email)  # ✅ Safe access

[Validation]
✅ Applied fix to user_service.py
✅ Running tests...
   Before: 1,718/1,719 passing (1 failure)
   After: 1,719/1,719 passing (100%)
✅ Fix verified

[Learning]
🧠 Pattern learned: "Check None before attribute access"
📈 Confidence: 0.88 (4th occurrence)
💾 Stored in VectorStore

[Commit]
✅ Committed: fix: Add None check in get_user_email
✅ PR #142 updated

Healing success: 100%
Time: 47 seconds
```

**User Story: Preventing a Production Incident**

**Persona**: Rachel, Site Reliability Engineer

**Situation**: A developer attempts to merge code with subtle bugs.

```
Friday 4:45 PM:
Developer: "Merging hotfix before weekend!"

QualityEnforcer: ❌ BLOCKED
Reason: 3 test failures detected

Developer: "They're just flaky tests. I'll fix Monday."

QualityEnforcer: ❌ BLOCKED by Constitution Article II
"100% test success required - no exceptions"

[Autonomous Healing Activates]

QualityEnforcer:
✅ Analyzing failures...
✅ 2/3 failures: NoneType errors (auto-fixable)
✅ 1/3 failures: Logic error (requires review)

✅ Fixing NoneType errors... (32 seconds)
✅ Tests passing: 1,718/1,719

⚠️  Remaining failure: test_payment_refund
    Issue: Refund logic assumes payment always successful
    Recommendation: Add payment status check before refund

Developer: "Oh! That would have caused refund failures in production."
[Developer fixes logic error - 5 minutes]

✅ All tests passing: 1,719/1,719
✅ Merge approved

Rachel's Reflection:
"Without QualityEnforcer, we would have had a production incident.
 The 'flaky tests' were real bugs. Article II saved us."

Incident prevented: 1
Developer education: 1
Weekend saved: Rachel's
```

**Key Takeaway**: QualityEnforcer acts as an automated quality gatekeeper that cannot be bypassed, preventing technical debt and production incidents.

---

### Auditor Agent

**Role**: Code quality analysis and pattern detection (READ-ONLY)

**Responsibilities:**

1. Analyze codebase for quality issues
2. Detect anti-patterns and violations
3. Perform AST-based code analysis
4. Generate quality reports
5. Recommend refactoring opportunities
6. Validate NECESSARY test pattern compliance

**Available Tools:**

- `read`, `glob`, `grep` - Code inspection
- `analyze_type_patterns` - Type safety analysis
- `bash` - Test execution for metrics
- AST analyzer (built-in) - Abstract Syntax Tree parsing

**Important**: Auditor is READ-ONLY. It identifies issues but does not modify code.

**Configuration:**

```python
from auditor_agent import create_auditor_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
auditor = create_auditor_agent(
    model="gpt-5",
    agent_context=context
)
```

**Analysis Workflow:**

```
1. Scan codebase (glob patterns)
2. Parse AST for each file
3. Detect patterns and anti-patterns
4. Calculate quality metrics
5. Generate recommendations
6. Output structured report
```

**Example Interaction:**

```python
from auditor_agent import create_auditor_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
auditor = create_auditor_agent(agent_context=context)

# Request audit
result = auditor.run("Audit authentication module for quality issues")
```

**Audit Report Output:**

```
📋 AUDIT REPORT: Authentication Module

Scope: auth/*.py (12 files, 1,847 lines)
Duration: 2 minutes 34 seconds

QUALITY SCORE: 87/100 (Good)
├─ Code Quality: 92/100
├─ Test Quality: 95/100
├─ Security: 78/100
└─ Type Safety: 85/100

═══════════════════════════════════════════════════

CODE QUALITY ISSUES (8 found):

⚠️  HIGH PRIORITY (3):

1. Function Complexity Exceeded
   File: auth/login.py:45
   Function: login_user()
   Lines: 67 (exceeds 50-line limit)
   Cyclomatic Complexity: 12 (threshold: 10)

   Recommendation:
   - Extract validation logic to validate_credentials()
   - Extract session creation to create_user_session()
   - Extract logging to log_login_attempt()

2. Dict[str, Any] Usage
   File: auth/session.py:23
   Function: create_session(user_data: Dict[str, Any])

   Recommendation:
   - Create SessionData Pydantic model
   - Replace Dict[str, Any] with SessionData type

3. Missing Type Hints
   File: auth/utils.py
   Functions: 12 functions missing return type annotations

   Recommendation:
   - Add explicit return types to all functions
   - Enable mypy strict mode for validation

⚠️  MEDIUM PRIORITY (3):

4. Potential NoneType Error
   File: auth/password.py:67
   Code: user.email.lower()
   Issue: No None-check before attribute access

   Recommendation:
   - Add None-check: if user.email is None: return Err(...)
   - Or use Optional type with proper handling

5. Try/Except for Control Flow
   File: auth/jwt.py:89
   Issue: Using exception for expected flow

   Recommendation:
   - Replace with Result<T,E> pattern
   - Use explicit validation instead of try/except

6. Hardcoded Configuration
   File: auth/config.py:12
   Value: JWT_SECRET = "dev-secret-key"

   Recommendation:
   - Move to environment variable
   - Use secrets management system

⚠️  LOW PRIORITY (2):

7. Inconsistent Naming
   Files: auth/login.py, auth/auth_handler.py
   Issue: Mixed snake_case and camelCase

   Recommendation:
   - Standardize on snake_case (Python convention)

8. Duplicate Code
   Files: auth/login.py:45-67, auth/register.py:78-95
   Similarity: 89%

   Recommendation:
   - Extract common logic to shared function

═══════════════════════════════════════════════════

TEST QUALITY (NECESSARY Pattern Compliance):

✅ PASSING (95/100):
├─ Named clearly: 47/47 tests
├─ Executable in isolation: 45/47 tests (2 with dependencies)
├─ Comprehensive coverage: 42/47 tests (89% avg coverage)
├─ Error handling validated: 47/47 tests
├─ State changes verified: 47/47 tests
├─ Side effects controlled: 47/47 tests
├─ Assertions meaningful: 47/47 tests
├─ Repeatable results: 47/47 tests
└─ Yield fast execution: 46/47 tests (<50ms avg)

⚠️  TEST ISSUES (2):

1. Tests with Dependencies
   - test_login_integration (depends on database state)
   - test_session_persistence (depends on Redis)

   Recommendation: Use mocking for true isolation

2. Coverage Gaps
   Files with <100% coverage:
   - auth/oauth.py: 78% (error paths not tested)
   - auth/permissions.py: 82% (edge cases missing)

═══════════════════════════════════════════════════

SECURITY ANALYSIS:

⚠️  CRITICAL (1):
- JWT expiration not validated (auth/jwt.py:67)

⚠️  HIGH (2):
- Password hashing uses MD5 (auth/password.py:23)
- No rate limiting on login endpoint

⚠️  MEDIUM (3):
- Session tokens not rotated
- CORS configuration too permissive
- No brute-force protection

✅ GOOD:
- No hardcoded secrets detected
- Input validation present
- SQL injection prevention (parameterized queries)

═══════════════════════════════════════════════════

TYPE SAFETY ANALYSIS:

⚠️  TYPE ISSUES (3):
- Dict[str, Any] usage: 2 instances
- Missing type hints: 12 functions
- Loose Optional usage: 5 instances (should use Result<T,E>)

✅ TYPE STRENGTHS:
- Pydantic models: Well-structured
- Return types: 89% annotated
- No bare 'any' type usage

═══════════════════════════════════════════════════

RECOMMENDATIONS (Priority Order):

1. IMMEDIATE (Security):
   - Fix JWT expiration validation
   - Upgrade password hashing (MD5 → bcrypt)
   - Add login rate limiting

2. HIGH (Quality):
   - Refactor login_user() function (too complex)
   - Replace Dict[str, Any] with Pydantic models
   - Add type hints to auth/utils.py

3. MEDIUM (Maintainability):
   - Extract duplicate code
   - Fix NoneType risks
   - Improve test isolation

4. LOW (Polish):
   - Standardize naming conventions
   - Improve test coverage to 100%

═══════════════════════════════════════════════════

LEARNING PATTERNS DETECTED:

🧠 Pattern: "JWT validation frequently missed"
   Occurrences: 3 codebases analyzed
   Confidence: 0.91
   Status: Stored in VectorStore

🧠 Pattern: "Dict[str, Any] correlates with runtime errors"
   Occurrences: 5 codebases analyzed
   Confidence: 0.87
   Status: Stored in VectorStore

═══════════════════════════════════════════════════

NEXT STEPS:

1. Address critical security issues (Est: 2 hours)
2. Refactor complex functions (Est: 4 hours)
3. Improve type safety (Est: 3 hours)
4. Enhance test coverage (Est: 2 hours)

Estimated effort: 11 hours
Recommended: Activate QualityEnforcer for autonomous fixes
```

**User Story: Preparing for Technical Interview**

**Persona**: Miguel, Engineering Candidate

**Situation**: Miguel is interviewing at a company. They ask him to review their codebase and provide feedback.

```bash
Miguel: /prime audit_and_refactor

Miguel: (to AuditorAgent)
        Analyze the entire codebase for quality issues.
        I need to provide detailed feedback in 30 minutes.

AuditorAgent:
✅ Scanning codebase... (127 files, 18,432 lines)
✅ Running AST analysis...
✅ Calculating quality metrics...
✅ Generating report...

[5 minutes later]

📊 COMPREHENSIVE AUDIT REPORT

Overall Score: 72/100 (Needs Improvement)

Top 10 Issues:
1. 47% of functions exceed 50-line limit
2. Security: 12 SQL injection risks
3. No input validation on API endpoints
4. Test coverage: 58% (should be 100%)
5. 23 instances of Dict[str, Any]
6. No error handling in critical paths
7. Hardcoded secrets in 8 files
8. 0% type hint coverage
9. No logging in production code
10. Circular dependencies in 3 modules

Strengths:
+ Clean git history
+ Good README documentation
+ Consistent file structure

Miguel's Feedback (to interviewers):
"I audited your codebase and found several areas for improvement:

Priority 1: Security (SQL injection, hardcoded secrets)
Priority 2: Quality (function complexity, test coverage)
Priority 3: Maintainability (type hints, error handling)

I'd recommend:
1. Implement Agency OS constitutional governance
2. Enable autonomous healing for NoneType errors
3. Enforce TDD for all new features
4. Add pre-commit hooks for quality enforcement

With these changes, you'd go from 72/100 to 95/100 in 2-3 weeks."

Interviewer Response:
"That's exactly what we needed. You're hired as Tech Lead."

Miguel's Result:
- Audit completed: 5 minutes
- Detailed feedback: Comprehensive
- Job offer: Received
- Starting salary: +$40K (based on technical insight)
```

**Key Takeaway**: Auditor provides deep code insights without modifying code, making it ideal for analysis, reporting, and strategic planning.

---

### TestGenerator Agent

**Role**: NECESSARY-compliant test generation and strategy

**Responsibilities:**

1. Generate comprehensive tests following NECESSARY pattern
2. Create unit, integration, and end-to-end tests
3. Ensure edge case coverage
4. Validate test quality and isolation
5. Calculate and improve coverage metrics

**Available Tools:**

- `read`, `write`, `edit` - Test file creation
- `bash` - Test execution and coverage analysis
- `glob`, `grep` - Test discovery and analysis
- `todo_write` - Test task breakdown

**Configuration:**

```python
from test_generator_agent import create_test_generator_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
test_gen = create_test_generator_agent(
    model="gpt-5",
    agent_context=context
)
```

**NECESSARY Pattern:**

Every test MUST follow the NECESSARY pattern:

- **N**amed clearly with test purpose
- **E**xecutable in isolation
- **C**omprehensive coverage
- **E**rror handling validated
- **S**tate changes verified
- **S**ide effects controlled
- **A**ssertions meaningful
- **R**epeatable results
- **Y**ield fast execution

**Test Generation Workflow:**

```
1. Analyze implementation code
2. Identify test scenarios (happy path, edge cases, errors)
3. Generate test cases following NECESSARY pattern
4. Create test fixtures and mocks
5. Validate test isolation
6. Calculate coverage
7. Iterate until 100% coverage
```

**Example Interaction:**

```python
from test_generator_agent import create_test_generator_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
test_gen = create_test_generator_agent(agent_context=context)

# Request test generation
result = test_gen.run("""
Generate comprehensive tests for:
shared/validators/email.py:validate_email()

Requirements:
- Follow NECESSARY pattern
- 100% coverage
- Include edge cases
""")
```

**Generated Tests:**

```python
"""
Comprehensive tests for email validator.

NECESSARY Pattern Compliance:
- Named clearly: Test names describe exact scenario
- Executable in isolation: No dependencies between tests
- Comprehensive coverage: 100% line and branch coverage
- Error handling validated: All error paths tested
- State changes verified: Pure function (no state changes)
- Side effects controlled: No side effects in validator
- Assertions meaningful: Explicit success/failure checks
- Repeatable results: Deterministic (no randomness)
- Yield fast execution: <10ms per test
"""

import pytest
from shared.validators.email import validate_email
from shared.type_definitions.result import Ok, Err


# HAPPY PATH TESTS (Named clearly - NECESSARY)
def test_valid_simple_email_returns_ok():
    """Valid email with simple format passes validation."""
    result = validate_email("user@example.com")
    assert result.is_ok()
    assert result.unwrap() == True


def test_valid_email_with_subdomain_returns_ok():
    """Valid email with subdomain passes validation."""
    result = validate_email("user@mail.example.com")
    assert result.is_ok()


def test_valid_email_with_plus_addressing_returns_ok():
    """Valid email with plus addressing passes validation."""
    result = validate_email("user+tag@example.com")
    assert result.is_ok()


def test_valid_email_with_dash_in_domain_returns_ok():
    """Valid email with dash in domain passes validation."""
    result = validate_email("user@my-domain.com")
    assert result.is_ok()


# EDGE CASE TESTS (Comprehensive coverage - NECESSARY)
def test_email_at_minimum_length_is_valid():
    """Email at minimum valid length (a@b.co) passes validation."""
    result = validate_email("a@b.co")
    assert result.is_ok()


def test_email_at_maximum_length_is_valid():
    """Email at maximum length (254 chars) passes validation."""
    # 254 char email: 64 char local + @ + 189 char domain
    local = "a" * 64
    domain = "b" * 185 + ".com"
    email = f"{local}@{domain}"
    assert len(email) == 254
    result = validate_email(email)
    assert result.is_ok()


def test_email_with_multiple_dots_in_local_part_is_valid():
    """Email with multiple dots in local part passes validation."""
    result = validate_email("first.last.name@example.com")
    assert result.is_ok()


# ERROR PATH TESTS (Error handling validated - NECESSARY)
def test_empty_email_returns_err():
    """Empty string returns error with descriptive message."""
    result = validate_email("")
    assert result.is_err()
    assert "cannot be empty" in result.unwrap_err().lower()


def test_whitespace_only_email_returns_err():
    """Whitespace-only string returns error."""
    result = validate_email("   ")
    assert result.is_err()
    assert "cannot be empty" in result.unwrap_err().lower()


def test_email_missing_at_symbol_returns_err():
    """Email without @ symbol returns error."""
    result = validate_email("userexample.com")
    assert result.is_err()
    assert "invalid" in result.unwrap_err().lower()


def test_email_missing_domain_returns_err():
    """Email without domain returns error."""
    result = validate_email("user@")
    assert result.is_err()


def test_email_missing_local_part_returns_err():
    """Email without local part returns error."""
    result = validate_email("@example.com")
    assert result.is_err()


def test_email_with_spaces_returns_err():
    """Email with spaces returns error."""
    result = validate_email("user @example.com")
    assert result.is_err()


def test_email_exceeding_max_length_returns_err():
    """Email exceeding 254 characters returns error."""
    long_email = "a" * 250 + "@example.com"
    result = validate_email(long_email)
    assert result.is_err()
    assert "exceeds maximum length" in result.unwrap_err().lower()


def test_email_with_invalid_characters_returns_err():
    """Email with invalid characters returns error."""
    result = validate_email("user#invalid@example.com")
    assert result.is_err()


def test_email_with_double_at_symbol_returns_err():
    """Email with multiple @ symbols returns error."""
    result = validate_email("user@@example.com")
    assert result.is_err()


# PROPERTY-BASED TESTS (Repeatable results - NECESSARY)
@pytest.mark.parametrize("valid_email", [
    "simple@example.com",
    "user.name@example.com",
    "user+tag@example.com",
    "user@subdomain.example.com",
    "user123@example.co.uk",
    "first_last@example.com",
])
def test_various_valid_formats_return_ok(valid_email):
    """Various valid email formats pass validation."""
    result = validate_email(valid_email)
    assert result.is_ok(), f"Expected {valid_email} to be valid"


@pytest.mark.parametrize("invalid_email", [
    "user",
    "user@",
    "@example.com",
    "user @example.com",
    "user@example",
    "user@@example.com",
    "",
    "   ",
])
def test_various_invalid_formats_return_err(invalid_email):
    """Various invalid email formats return errors."""
    result = validate_email(invalid_email)
    assert result.is_err(), f"Expected {invalid_email} to be invalid"


# PERFORMANCE TEST (Yield fast execution - NECESSARY)
def test_email_validation_executes_quickly(benchmark):
    """Email validation completes in <10ms."""
    # pytest-benchmark fixture
    result = benchmark(validate_email, "user@example.com")
    assert result.is_ok()
    # benchmark automatically verifies execution time


# ISOLATION TEST (Executable in isolation - NECESSARY)
def test_validation_has_no_side_effects():
    """Validation function has no side effects (pure function)."""
    email = "user@example.com"

    # Call multiple times
    result1 = validate_email(email)
    result2 = validate_email(email)

    # Results should be identical
    assert result1.is_ok() == result2.is_ok()

    # Function should not modify input
    assert email == "user@example.com"  # Unchanged
```

**Coverage Report:**

```bash
$ pytest tests/unit/validators/test_email.py --cov=shared/validators/email

==================== test session starts ====================
collected 20 items

tests/unit/validators/test_email.py::test_valid_simple_email_returns_ok PASSED
tests/unit/validators/test_email.py::test_valid_email_with_subdomain_returns_ok PASSED
tests/unit/validators/test_email.py::test_valid_email_with_plus_addressing_returns_ok PASSED
[... 17 more tests PASSED]

----------- coverage: platform darwin, python 3.11.5 -----------
Name                               Stmts   Miss  Cover
------------------------------------------------------
shared/validators/email.py            23      0   100%
------------------------------------------------------
TOTAL                                 23      0   100%

==================== 20 passed in 0.18s ====================
```

**Test Quality Report:**

```
📊 TEST QUALITY ANALYSIS

File: tests/unit/validators/test_email.py
Tests: 20
Coverage: 100%
NECESSARY Compliance: 100%

NECESSARY Pattern Breakdown:

✅ Named clearly: 20/20 (100%)
   - All test names describe exact scenario
   - Format: test_[condition]_[expected_result]

✅ Executable in isolation: 20/20 (100%)
   - No shared state between tests
   - No test dependencies
   - Each test can run independently

✅ Comprehensive coverage: 100%
   - All lines executed
   - All branches tested
   - Happy path + edge cases + error paths

✅ Error handling validated: 9/20 tests (45%)
   - All error paths have dedicated tests
   - Error messages validated

✅ State changes verified: N/A
   - Pure function (no state changes)

✅ Side effects controlled: 20/20 (100%)
   - No database calls
   - No file I/O
   - No network requests
   - No global state modification

✅ Assertions meaningful: 20/20 (100%)
   - Explicit assertions on Result type
   - Error message content validated
   - Success conditions clearly defined

✅ Repeatable results: 20/20 (100%)
   - Deterministic (no randomness)
   - No time-dependent logic
   - Parametrized tests for consistency

✅ Yield fast execution: 20/20 (100%)
   - Average: 9ms per test
   - Total suite: 180ms
   - All tests <50ms

Test Quality Score: 100/100 (Excellent)
```

**User Story: Achieving 100% Test Coverage**

**Persona**: Olivia, QA Engineer tasked with improving test coverage

**Challenge**: Current test coverage is 63%. Management wants 100% before Q4 release.

```bash
Olivia: /prime plan_and_execute

Olivia: (to TestGenerator)
        Generate comprehensive tests for all modules with <100% coverage.
        Follow NECESSARY pattern.

TestGeneratorAgent:
✅ Analyzing codebase coverage...
   Current: 63% (8,473 / 13,421 lines)
   Missing: 4,948 lines

✅ Identifying modules with coverage gaps:
   1. auth/ - 78% coverage (1,234 lines uncovered)
   2. api/ - 82% coverage (892 lines uncovered)
   3. services/ - 71% coverage (1,567 lines uncovered)
   4. utils/ - 54% coverage (1,255 lines uncovered)

✅ Generating tests...

[30 minutes later - Agency OS works autonomously]

✅ Test generation complete:
   - auth/: 47 new tests (100% coverage)
   - api/: 38 new tests (100% coverage)
   - services/: 67 new tests (100% coverage)
   - utils/: 52 new tests (100% coverage)

📊 Results:
   Total new tests: 204
   Coverage before: 63%
   Coverage after: 100%
   All tests passing: 1,919/1,919
   NECESSARY compliance: 100%

Olivia's Result:
- Coverage goal achieved: 100%
- Time spent: 30 minutes (Agency OS worked autonomously)
- Manual test writing: 0 tests
- QA approval: Immediate
- Q4 release: On track

Traditional approach: 2-3 weeks of manual test writing
Agency OS: 30 minutes (672x faster)
```

**Key Takeaway**: TestGenerator ensures comprehensive, high-quality tests following NECESSARY pattern, achieving 100% coverage autonomously.

---

### LearningAgent

**Role**: Pattern analysis from sessions and VectorStore integration

**Responsibilities:**

1. Extract patterns from successful sessions
2. Analyze errors and resolutions
3. Store learnings in VectorStore
4. Provide historical insights to other agents
5. Improve system performance over time
6. Maintain institutional memory

**Available Tools:**

- VectorStore (built-in) - Semantic search and storage
- `read` - Session log analysis
- `grep`, `glob` - Pattern discovery
- `learning_dashboard` - Visualization and reporting

**Configuration:**

```python
from learning_agent import create_learning_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
learning = create_learning_agent(
    model="gpt-5",
    agent_context=context
)
```

**Learning Workflow:**

```
1. Monitor session events
2. Detect successful patterns
3. Analyze error resolutions
4. Extract actionable learnings
5. Validate confidence (≥0.6) and evidence (≥3 occurrences)
6. Store in VectorStore
7. Make available for future sessions
```

**Pattern Types:**

1. **Code Patterns**: Recurring implementation solutions
2. **Error Patterns**: Common errors and fixes
3. **Tool Usage**: Effective tool combinations
4. **Architectural Patterns**: Design decisions
5. **Test Patterns**: Testing strategies

**Example Interaction:**

```python
from learning_agent import create_learning_agent
from shared.agent_context import create_agent_context

context = create_agent_context()
learning = create_learning_agent(agent_context=context)

# Trigger learning extraction
result = learning.run("Extract patterns from last 10 sessions")
```

**Learning Extraction Output:**

```
🧠 LEARNING EXTRACTION REPORT

Sessions Analyzed: 10 (last 7 days)
Patterns Detected: 23
Patterns Stored: 8 (confidence ≥0.6, evidence ≥3)
Patterns Rejected: 15 (insufficient evidence)

═══════════════════════════════════════════════════

STORED PATTERNS:

1. Code Pattern: "NoneType Prevention"
   Confidence: 0.92 (8 occurrences)
   Evidence: Sessions #142, #145, #147, #151, #153, #158, #160, #162

   Pattern:
   ```python
   # Always check None before attribute access
   if obj is None:
       return Err("Object not found")
   return Ok(obj.attribute)
   ```

   Context:
   - Triggered by: NoneType AttributeError
   - Fixed by: Adding None-check before access
   - Success rate: 100% (8/8 fixes successful)

   Applied to modules: auth, user, order, payment
   Time saved: ~15 minutes per occurrence

2. Tool Pattern: "Bash + Read + Edit Workflow"
   Confidence: 0.88 (6 occurrences)
   Evidence: Sessions #143, #148, #152, #154, #157, #161

   Workflow:
   1. Use bash to run tests and identify failures
   2. Use read to inspect failing code
   3. Use edit to apply fix
   4. Use bash to verify fix

   Context:
   - Most effective for: Test-driven bug fixes
   - Success rate: 95% (57/60 fixes successful)
   - Avg time: 2.3 minutes per fix

3. Architectural Pattern: "Result<T,E> for Error Handling"
   Confidence: 0.94 (12 occurrences)
   Evidence: All sessions

   Pattern:
   ```python
   def risky_operation() -> Result[Data, Error]:
       if validation_failed:
           return Err(ValidationError("..."))
       return Ok(result)
   ```

   Benefits observed:
   - 0 unhandled exceptions in production
   - Explicit error handling
   - Type-safe error propagation

   Success rate: 100% (0 runtime errors)

4. Test Pattern: "NECESSARY Compliance Checklist"
   Confidence: 0.91 (7 occurrences)
   Evidence: Sessions #144, #146, #149, #155, #156, #159, #163

   Checklist applied before test approval:
   - [x] Named clearly
   - [x] Executable in isolation
   - [x] Comprehensive coverage
   - [x] Error handling validated
   - [x] State changes verified
   - [x] Side effects controlled
   - [x] Assertions meaningful
   - [x] Repeatable results
   - [x] Yield fast execution

   Result: 100% test success rate when checklist followed

5. Error Pattern: "Missing Type Hints Lead to Runtime Errors"
   Confidence: 0.87 (5 occurrences)
   Evidence: Sessions #143, #150, #154, #157, #162

   Correlation:
   - Functions without type hints: 3.2x more likely to have runtime errors
   - Functions with type hints: 0.1% error rate

   Recommendation: Enforce type hints via mypy strict mode

6. Code Pattern: "Pydantic Models Over Dict[str, Any]"
   Confidence: 0.89 (9 occurrences)
   Evidence: Sessions #142, #145, #147, #149, #151, #153, #156, #159, #161

   Before (problematic):
   ```python
   def process(data: Dict[str, Any]) -> Dict[str, Any]:
       return {"result": data.get("value")}
   ```

   After (reliable):
   ```python
   class InputData(BaseModel):
       value: str

   class OutputData(BaseModel):
       result: str

   def process(data: InputData) -> OutputData:
       return OutputData(result=data.value)
   ```

   Impact:
   - Runtime errors: -87%
   - Type safety: 100%
   - Code maintainability: +45% (subjective estimate)

7. Tool Pattern: "Git Diff Before Commit"
   Confidence: 0.85 (5 occurrences)
   Evidence: Sessions #148, #152, #155, #158, #163

   Workflow:
   1. git diff (review changes)
   2. Validate against spec
   3. Run tests
   4. git commit (if all checks pass)

   Prevented issues:
   - Accidental file commits: 7 incidents
   - Incomplete implementations: 3 incidents
   - Test failures: 2 incidents

8. Architectural Pattern: "Redis for Distributed State"
   Confidence: 0.83 (4 occurrences)
   Evidence: Sessions #150, #154, #159, #162

   Use cases:
   - Rate limiting
   - Session storage
   - Cache
   - Distributed locks

   Success factors:
   - TTL for automatic cleanup
   - Atomic operations for consistency
   - Connection pooling for performance

═══════════════════════════════════════════════════

REJECTED PATTERNS (Insufficient Evidence):

- "FastAPI over Flask" (2 occurrences - need 3)
- "MongoDB for user data" (1 occurrence - need 3)
- "Docker for local development" (2 occurrences - need 3)
- [... 12 more]

═══════════════════════════════════════════════════

LEARNING IMPACT METRICS:

Time Saved: ~4.2 hours (estimated across 10 sessions)
Errors Prevented: 23 (proactive pattern application)
Code Quality: +18% (based on Auditor scores)

Historical Comparison:
- Sessions 1-50: Avg 47 minutes per task
- Sessions 51-100: Avg 38 minutes per task (-19%)
- Sessions 101-163: Avg 31 minutes per task (-34% vs. baseline)

Learning Curve: Improving 2.1% per 10 sessions

═══════════════════════════════════════════════════

NEXT STEPS:

1. Apply "NoneType Prevention" pattern proactively in new code
2. Enforce "Pydantic Models" pattern via QualityEnforcer
3. Integrate "NECESSARY Checklist" into TestGenerator
4. Monitor for new patterns (sessions #164-173)
```

**VectorStore Query Example:**

```python
from shared.agent_context import create_agent_context

context = create_agent_context()

# Search for relevant patterns
patterns = context.search_memories(
    ["NoneType", "error handling"],
    include_session=False  # Search all sessions
)

# Apply learned pattern
if patterns:
    best_pattern = patterns[0]  # Highest confidence first
    print(f"Pattern: {best_pattern['content']}")
    print(f"Confidence: {best_pattern['confidence']}")
    print(f"Evidence: {best_pattern['evidence_count']} occurrences")

    # Apply pattern to current code
    apply_pattern(best_pattern)
```

**User Story: How Agency Learns from Experience**

**Persona**: System Administrator observing Agency OS over 6 months

**Observations:**

**Month 1: Baseline Performance**

```
Average task completion: 52 minutes
Errors encountered: 18 per week
Autonomous fix success rate: 78%
Patterns learned: 0 (insufficient evidence)
```

**Month 2: Pattern Emergence**

```
Average task completion: 47 minutes (-10%)
Errors encountered: 15 per week
Autonomous fix success rate: 82%
Patterns learned: 3 (confidence ≥0.6)

Notable pattern:
- "None-check before attribute access" (confidence 0.84)
- Applied proactively in 12 new implementations
- Prevented 12 potential NoneType errors
```

**Month 3: Knowledge Accumulation**

```
Average task completion: 41 minutes (-21% vs. Month 1)
Errors encountered: 11 per week
Autonomous fix success rate: 89%
Patterns learned: 12 cumulative

New patterns:
- "Result<T,E> for error handling" (confidence 0.91)
- "Pydantic models over Dict[str, Any]" (confidence 0.87)
- "NECESSARY pattern for tests" (confidence 0.93)

Impact:
- Proactive pattern application: 34 instances
- Errors prevented: 28 (vs. 6 actual errors)
```

**Month 4: Cross-Session Learning**

```
Average task completion: 36 minutes (-31% vs. Month 1)
Errors encountered: 7 per week
Autonomous fix success rate: 94%
Patterns learned: 23 cumulative

Breakthrough:
- LearningAgent queries VectorStore before implementation
- Historical patterns applied automatically
- "I've seen this before" behavior emerges

Example:
User: "Add email validation"
LearningAgent: "Found 3 similar implementations. Applying best practices..."
✅ Implementation uses learned patterns (regex, RFC 5322, Result<T,E>)
✅ Zero errors, 100% test coverage
✅ Completion time: 8 minutes (vs. 25 minutes in Month 1)
```

**Month 6: Institutional Memory**

```
Average task completion: 29 minutes (-44% vs. Month 1)
Errors encountered: 3 per week
Autonomous fix success rate: 97%
Patterns learned: 47 cumulative

Advanced behaviors observed:
- Predicts likely errors before they occur
- Suggests architectural improvements proactively
- Optimizes tool usage based on historical success
- Self-improves without human intervention

ROI:
- Developer productivity: +78%
- Error rate: -83%
- Code quality (Auditor score): 72 → 94
- Time to production: -56%
```

**Admin's Conclusion:**

"Agency OS learns like a human developer but never forgets. After 6 months, it has institutional knowledge that would take a new hire 2+ years to acquire. The learning curve is exponential, not linear."

**Key Takeaway**: LearningAgent enables Agency OS to improve continuously, accumulating institutional knowledge that makes every session faster and more reliable than the last.

---

[CONTINUED IN NEXT RESPONSE DUE TO LENGTH...]

Would you like me to continue with the remaining agent documentation (Merger, Toolsmith, WorkCompletionSummary, UIDevelopment) and the Tool Reference section (Section 5)?