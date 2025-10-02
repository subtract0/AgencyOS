# Agency User Manual - Comprehensive Plan

**Date**: 2025-10-01
**Planner**: Planner Agent
**Target Audience**: New Users, Developers, Operators, Architects
**Estimated Length**: 5,000-8,000 lines
**Format**: Single markdown file with deep linking

---

## Executive Summary

This plan outlines a comprehensive user manual for the Agency autonomous software engineering platform. The manual will serve as the single authoritative reference for all users, from first-time setup to advanced production operations.

### Design Principles
1. **Progressive Disclosure**: Start simple, add complexity gradually
2. **Learn by Example**: Every concept illustrated with runnable code
3. **User Story Driven**: Real-world scenarios throughout
4. **Quick Reference Ready**: Scannable structure with clear headings
5. **Maintenance First**: Easy to update, version-controlled

### Deliverables
1. **USER_MANUAL.md** - Complete user manual (~5,000 lines)
2. **QUICK_START.md** - 5-minute getting started guide (~200 lines)
3. **API_REFERENCE.md** - Complete API documentation (~3,000 lines)
4. **TROUBLESHOOTING.md** - Common issues and solutions (~1,000 lines)
5. **EXAMPLES.md** - Runnable code examples (~800 lines)

---

## Table of Contents (3-Level Deep)

### Chapter 1: Quick Start Guide
**Estimated Length**: 500 lines
**Priority**: P0 (Write First)
**User Stories**: 2

#### 1.1 Prerequisites and System Requirements
- 1.1.1 Operating System Requirements
- 1.1.2 Python Version Requirements (3.12 or 3.13)
- 1.1.3 API Key Setup
- 1.1.4 Hardware Recommendations

#### 1.2 Five-Minute Installation
- 1.2.1 Clone and Setup
  - Example: `git clone` command
  - Example: `./agency setup` command
- 1.2.2 Environment Configuration
  - Example: .env file template
  - Example: Required vs optional variables
- 1.2.3 Verification Steps
  - Example: `python run_tests.py --run-all`
  - Expected output screenshots

#### 1.3 Your First Autonomous Task
- 1.3.1 Understanding Prime Commands
- 1.3.2 Running a Simple Code Analysis
  - Example: `/prime audit_and_refactor`
  - Expected output walkthrough
- 1.3.3 Reading the Output
  - How to interpret agent responses
  - Understanding file modifications

#### 1.4 Understanding What Just Happened
- 1.4.1 Agent Orchestration Overview
- 1.4.2 Constitutional Compliance in Action
- 1.4.3 Log File Locations

#### 1.5 Next Steps
- Quick links to deeper dives
- Suggested learning path

**User Story 1: "Getting Started in 5 Minutes"**
```
As a new developer,
I want to install and run my first autonomous task in 5 minutes,
So that I can see the value immediately without reading extensive documentation.

Acceptance Criteria:
- Complete installation in < 5 minutes
- Run first task successfully
- Understand basic output
```

**User Story 2: "Validating Installation"**
```
As a new user,
I want to verify my installation is working correctly,
So that I can trust the system before using it for real work.

Acceptance Criteria:
- Run full test suite
- See 100% pass rate
- Understand system health indicators
```

---

### Chapter 2: Core Concepts
**Estimated Length**: 800 lines
**Priority**: P0 (Write First)
**User Stories**: 3

#### 2.1 Constitutional Governance
- 2.1.1 Article I: Complete Context Before Action
  - What it means
  - Why it matters
  - Example: Timeout handling in practice
- 2.1.2 Article II: 100% Verification and Stability
  - Test success requirements
  - Example: Pre-commit hook in action
- 2.1.3 Article III: Automated Enforcement
  - Multi-layer enforcement
  - Example: Blocked commit scenario
- 2.1.4 Article IV: Continuous Learning
  - How the system learns
  - Example: Pattern recognition
- 2.1.5 Article V: Spec-Driven Development
  - When to use specs
  - Example: Complex feature workflow

#### 2.2 Agent Architecture
- 2.2.1 The 11 Specialized Agents
  - Role summary table
  - Communication patterns
- 2.2.2 Agent Orchestration
  - How agents coordinate
  - Example: Development workflow diagram
- 2.2.3 Constitutional Compliance Validation
  - The @constitutional_compliance decorator
  - Example: How validation prevents errors

#### 2.3 Memory and Learning Systems
- 2.3.1 AgentContext API
  - store_memory() usage
  - search_memories() usage
  - Example: Storing and retrieving patterns
- 2.3.2 VectorStore Integration
  - Semantic search capabilities
  - Example: Pattern matching
- 2.3.3 Cross-Session Learning
  - How knowledge persists
  - Example: Learning from past sessions

#### 2.4 Tool Infrastructure
- 2.4.1 The 45+ Tools Overview
  - Tool categories
  - Common vs specialized tools
- 2.4.2 Tool Execution Model
  - How tools are invoked
  - Error handling
- 2.4.3 Constitutional Compliance in Tools
  - Security validation
  - Type safety

#### 2.5 Quality Enforcement
- 2.5.1 Type Safety Requirements
  - No Dict[Any, Any] rule
  - Pydantic model usage
  - Example: Converting to typed models
- 2.5.2 TDD Requirements
  - Test-first development
  - NECESSARY pattern
  - Example: Writing a compliant test
- 2.5.3 Code Quality Standards
  - Function length limits
  - Complexity limits
  - Example: Refactoring a long function

**User Story 3: "Understanding How Agency Maintains Quality"**
```
As a developer,
I want to understand how Agency ensures code quality,
So that I can trust the autonomous changes it makes to my codebase.

Acceptance Criteria:
- Understand the 5 constitutional articles
- See quality enforcement in action
- Know how to check compliance status
```

**User Story 4: "Learning the Agent Model"**
```
As a technical user,
I want to understand how the 11 agents work together,
So that I can predict and guide their behavior.

Acceptance Criteria:
- Identify each agent's role
- Understand communication flows
- Predict which agent handles which task
```

**User Story 5: "Understanding Memory Systems"**
```
As a power user,
I want to understand how Agency learns and remembers,
So that I can leverage cross-session knowledge.

Acceptance Criteria:
- Store custom memories
- Search historical patterns
- Understand learning triggers
```

---

### Chapter 3: Prime Commands Reference
**Estimated Length**: 1,200 lines
**Priority**: P0 (Write First)
**User Stories**: 8 (one per command)

#### 3.1 Command Overview
- 3.1.1 The Prime-First Mandate
- 3.1.2 When to Use Which Command
- 3.1.3 Command Execution Model

#### 3.2 /prime_cc - Codebase Understanding
- 3.2.1 Purpose and Use Cases
- 3.2.2 Required Context
- 3.2.3 Step-by-Step Workflow
- 3.2.4 Example Output
- 3.2.5 Troubleshooting
- 3.2.6 Best Practices

**Example Walkthrough**:
```bash
# User executes
/prime_cc

# Agency reads and analyzes
- README.md
- CLAUDE.md
- constitution.md
- All agent definitions
- All prime commands

# Output format
[Detailed summary showing understanding]
```

**User Story 6: "Understanding My Codebase"**
```
As a new user on an existing project,
I want Agency to analyze and explain the codebase to me,
So that I can get up to speed quickly.

Acceptance Criteria:
- Run /prime_cc command
- Receive clear architecture summary
- Identify key components and patterns
```

#### 3.3 /prime plan_and_execute - Full Development Cycle
- 3.3.1 Purpose and Use Cases
- 3.3.2 Required Inputs (specification file)
- 3.3.3 Step-by-Step Workflow
  - Planner agent creates plan
  - ChiefArchitect makes ADRs
  - CodeAgent implements
  - TestGenerator creates tests
- 3.3.4 Example: Adding a New Feature
- 3.3.5 Troubleshooting
- 3.3.6 Best Practices

**Example Walkthrough**:
```bash
# User provides spec
/prime plan_and_execute
Spec file: specs/spec-new-feature.md

# Agency workflow
1. Planner reads spec → creates plan.md
2. ChiefArchitect → creates ADR if needed
3. CodeAgent → implements code
4. TestGenerator → creates tests
5. All tests pass → completion report

# Artifacts created
- plans/plan-new-feature.md
- docs/adr/ADR-XXX.md (if needed)
- Modified source files
- New test files
```

**User Story 7: "Building a Feature from Spec"**
```
As a developer,
I want to provide a specification and have Agency implement it,
So that I can focus on design while Agency handles implementation.

Acceptance Criteria:
- Create formal spec
- Run /prime plan_and_execute
- Receive working, tested code
- All tests pass
```

#### 3.4 /prime audit_and_refactor - Code Quality Improvement
- Purpose, workflow, examples, user story

#### 3.5 /prime create_tool - Tool Development
- Purpose, workflow, examples, user story

#### 3.6 /prime healing_mode - Autonomous Healing
- Purpose, workflow, examples, user story

#### 3.7 /prime web_research - Research and Analysis
- Purpose, workflow, examples, user story

#### 3.8 /create_prd - Product Requirements
- Purpose, workflow, examples, user story

#### 3.9 /generate_tasks - Task Breakdown
- Purpose, workflow, examples, user story

#### 3.10 /process_tasks - Task Execution
- Purpose, workflow, examples, user story

#### 3.11 Command Comparison Matrix
Table showing when to use each command

---

### Chapter 4: Development Workflows
**Estimated Length**: 1,000 lines
**Priority**: P1 (Write Second)
**User Stories**: 5

#### 4.1 Spec-Driven Development
- 4.1.1 When to Use Specs
  - Complex vs simple tasks
  - Decision tree
- 4.1.2 Creating a Specification
  - Template walkthrough
  - Goals, Non-Goals, Personas, Acceptance Criteria
  - Example: Complete spec
- 4.1.3 Creating an Implementation Plan
  - Template walkthrough
  - Architecture, Tasks, Testing Strategy
  - Example: Complete plan
- 4.1.4 Executing from Plan
  - TodoWrite integration
  - Task breakdown
  - Progress tracking

**User Story 8: "Spec-Driven Feature Development"**
```
As a product owner,
I want to define a feature formally and have it implemented correctly,
So that requirements are met and quality is maintained.

Acceptance Criteria:
- Create spec using template
- Generate implementation plan
- Execute with full test coverage
- Verify against acceptance criteria
```

#### 4.2 TDD Workflow
- 4.2.1 Test-First Development
  - Why tests first
  - Example: Red-Green-Refactor cycle
- 4.2.2 NECESSARY Pattern Explained
  - Each letter explained with example
  - Quality metrics (Q(T) score)
- 4.2.3 Writing Compliant Tests
  - AAA pattern (Arrange-Act-Assert)
  - Example: Complete test suite for a feature
- 4.2.4 Test Execution and Validation
  - Running tests locally
  - CI/CD integration
  - Example: Pre-commit validation

**User Story 9: "Test-First Development"**
```
As a developer,
I want to write tests before implementation,
So that my code is designed for testability and meets requirements.

Acceptance Criteria:
- Write tests first using NECESSARY pattern
- See tests fail (red)
- Implement to make tests pass (green)
- Refactor while maintaining green tests
```

#### 4.3 Code Review Process
- 4.3.1 Automated Pre-Review
- 4.3.2 Constitutional Compliance Checks
- 4.3.3 Quality Metrics Review
- 4.3.4 Example: Full review workflow

**User Story 10: "Automated Code Review"**
```
As a reviewer,
I want automated quality checks before manual review,
So that I can focus on logic and design rather than style.

Acceptance Criteria:
- All constitutional checks pass
- Type safety verified
- Test coverage adequate
- Code quality metrics green
```

#### 4.4 Autonomous Healing
- 4.4.1 What Gets Auto-Fixed
  - NoneType errors
  - Type annotations
  - Import cleanup
  - Formatting issues
- 4.4.2 Healing Workflow Deep Dive
  - Detection mechanisms
  - LLM-powered fix generation
  - Safety validation
  - Automatic rollback
- 4.4.3 Monitoring Healing Operations
  - Log locations
  - Success metrics
  - Manual intervention cases
- 4.4.4 Example: Complete Healing Cycle

**User Story 11: "Automatic Error Fixing"**
```
As a developer,
I want Agency to detect and fix common errors automatically,
So that I can focus on complex problems.

Acceptance Criteria:
- NoneType errors detected
- Fixes generated and applied
- Tests validate fixes
- Audit trail maintained
```

#### 4.5 Integration and Deployment
- 4.5.1 GitWorkflowTool Usage
  - Branch creation
  - Commit automation
  - PR generation
  - Example: Complete workflow
- 4.5.2 CI/CD Integration
- 4.5.3 Green Main Enforcement
- 4.5.4 Example: Feature to Production

**User Story 12: "Automated Git Workflow"**
```
As a developer,
I want automated branch, commit, and PR creation,
So that I can focus on code rather than Git commands.

Acceptance Criteria:
- Create feature branch
- Atomic commits with clear messages
- PR created with full context
- All checks pass before merge
```

---

### Chapter 5: Agent Deep Dive
**Estimated Length**: 1,500 lines
**Priority**: P1 (Write Second)
**User Stories**: 11 (one per agent)

#### 5.1 Agent Architecture Overview
- 5.1.1 Multi-Agent Coordination
- 5.1.2 Communication Patterns
- 5.1.3 Shared Context Model

#### 5.2 ChiefArchitectAgent
- 5.2.1 Role and Responsibilities
  - Strategic oversight
  - ADR creation
  - Self-directed task generation
- 5.2.2 Tools Available
  - List and explain each tool
- 5.2.3 Communication Patterns
  - When ChiefArchitect is invoked
  - How it coordinates other agents
- 5.2.4 Configuration Options
  - Model selection
  - Custom instructions
- 5.2.5 Example Interactions
  - Creating an ADR
  - System improvement task
- 5.2.6 Troubleshooting

**User Story 13: "Strategic Architecture Decisions"**
```
As an architect,
I want the ChiefArchitectAgent to provide strategic guidance,
So that the system evolves with good architectural decisions.

Acceptance Criteria:
- Identify architectural decisions needed
- Create formal ADRs
- Track architectural evolution
```

#### 5.3 PlannerAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.4 AgencyCodeAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.5 AuditorAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.6 TestGeneratorAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.7 QualityEnforcerAgent
- Role, tools, patterns, configuration, examples, troubleshooting
- Special focus on autonomous healing

#### 5.8 LearningAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.9 MergerAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.10 ToolsmithAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.11 WorkCompletionSummaryAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.12 SpecGeneratorAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.13 UIDeploymentAgent
- Role, tools, patterns, configuration, examples, troubleshooting

#### 5.14 Agent Selection Guide
- Which agent for which task
- Decision tree
- Common patterns

---

### Chapter 6: Tool Reference
**Estimated Length**: 1,800 lines
**Priority**: P2 (Write Third)

#### 6.1 Tool Categories
- 6.1.1 File Operations (read, write, edit, multi_edit)
- 6.1.2 Search and Navigation (grep, glob, find)
- 6.1.3 Version Control (git, git_workflow)
- 6.1.4 Code Execution (bash, python)
- 6.1.5 Analysis Tools (constitution_check, analyze_type_patterns)
- 6.1.6 Healing Tools (auto_fix_nonetype, apply_and_verify_patch)
- 6.1.7 Memory and Context (context_handoff, agent_context)
- 6.1.8 Specialized Tools (learning_dashboard, document_generator)

#### 6.2 File Operation Tools

**6.2.1 Read Tool**
```python
# Function signature
def read(file_path: str, offset: int = 0, limit: int = 2000) -> str

# Purpose
Read file contents with optional pagination

# Parameters
- file_path: Absolute path to file
- offset: Line number to start from (0-indexed)
- limit: Maximum lines to read

# Returns
String containing file contents with line numbers

# Example: Basic usage
result = read("/Users/am/Code/Agency/README.md")

# Example: Pagination
result = read("/Users/am/Code/Agency/README.md", offset=100, limit=50)

# Security considerations
- Path validation performed
- Constitutional compliance enforced
- Safe error handling

# Common errors and solutions
- FileNotFoundError: Check path is absolute
- PermissionError: Check file permissions
```

**6.2.2 Write Tool**
[Similar detailed format]

**6.2.3 Edit Tool**
[Similar detailed format]

**6.2.4 MultiEdit Tool**
[Similar detailed format]

[Continue for all 45+ tools with same detail level]

#### 6.3 Version Control Tools

**6.3.1 Git Tool**
[Detailed documentation]

**6.3.2 GitWorkflowTool**
```python
# Function signature
def git_workflow(
    branch_name: str,
    files_to_add: list[str],
    commit_message: str,
    push: bool = True,
    create_pr: bool = False,
    pr_title: str = "",
    pr_body: str = ""
) -> dict

# Purpose
Complete Git workflow automation: branch → commit → push → PR

# Example: Feature development workflow
result = git_workflow(
    branch_name="feature/new-authentication",
    files_to_add=["src/auth.py", "tests/test_auth.py"],
    commit_message="feat: Add JWT authentication",
    push=True,
    create_pr=True,
    pr_title="Add JWT Authentication",
    pr_body="Implements JWT-based authentication with refresh tokens"
)

# Constitutional compliance
- Green main enforcement
- Test validation before commit
- Atomic commit structure
```

[Continue for all Git tools]

#### 6.4 Security and Validation
- Input sanitization
- Path traversal prevention
- Command injection prevention
- Constitutional compliance

---

### Chapter 7: Constitutional Compliance Guide
**Estimated Length**: 900 lines
**Priority**: P1 (Write Second)

#### 7.1 Article I: Complete Context Before Action
- 7.1.1 What It Means
- 7.1.2 Why It Matters
- 7.1.3 Compliant Code Examples
  ```python
  # ✅ COMPLIANT: Proper context gathering
  def ensure_complete_context(operation_func, max_retries=3):
      timeout = 120000
      for attempt in range(max_retries):
          result = operation_func(timeout=timeout)
          if result.timed_out:
              timeout *= 2  # Exponential backoff
              continue
          if result.incomplete:
              continue
          if result.has_failures():
              raise Exception("STOP: Fix failures before proceeding")
          return result
      raise Exception("Unable to obtain complete context")
  ```
- 7.1.4 Non-Compliant Examples
  ```python
  # ❌ NON-COMPLIANT: Proceeding with partial data
  result = operation_func(timeout=10000)
  if result.timed_out:
      # BAD: Using partial results
      return partial_process(result.partial_data)
  ```
- 7.1.5 Validation and Testing
- 7.1.6 Common Violations and Fixes

#### 7.2 Article II: 100% Verification and Stability
[Similar detailed format]

#### 7.3 Article III: Automated Enforcement
[Similar detailed format]

#### 7.4 Article IV: Continuous Learning
[Similar detailed format]

#### 7.5 Article V: Spec-Driven Development
[Similar detailed format]

#### 7.6 Compliance Validation
- 7.6.1 Using @constitutional_compliance Decorator
- 7.6.2 Running Compliance Checks
- 7.6.3 Interpreting Compliance Reports

#### 7.7 Violation Remediation
- 7.7.1 Common Violations
- 7.7.2 Remediation Steps
- 7.7.3 Prevention Strategies

#### 7.8 User Story: "Ensuring Constitutional Compliance"
```
As a developer,
I want to validate my code against constitutional requirements,
So that I maintain quality standards.

Acceptance Criteria:
- Run constitutional compliance check
- Understand violations
- Apply fixes
- Verify compliance
```

---

### Chapter 8: Production Operations
**Estimated Length**: 700 lines
**Priority**: P2 (Write Third)

#### 8.1 Environment Setup
- 8.1.1 Development Environment
- 8.1.2 Staging Environment
- 8.1.3 Production Environment
- 8.1.4 Environment Variable Reference

#### 8.2 Monitoring and Observability
- 8.2.1 Log Structure
  - `logs/sessions/` - Session transcripts
  - `logs/autonomous_healing/` - Healing audit trails
  - `logs/telemetry/` - Metrics and events
- 8.2.2 Key Metrics
  - Test success rate (must be 100%)
  - Healing success rate (target >95%)
  - Agent execution time
  - Memory usage
- 8.2.3 Alerting
- 8.2.4 Example: Setting Up Monitoring

#### 8.3 Cost Tracking
- 8.3.1 Model Usage by Agent
- 8.3.2 Cost Optimization Strategies
- 8.3.3 Example: Monthly Cost Report

#### 8.4 Performance Tuning
- 8.4.1 Model Selection Optimization
- 8.4.2 Parallel Execution
- 8.4.3 Cache Configuration
- 8.4.4 Example: Reducing Execution Time

#### 8.5 Troubleshooting Guide
- 8.5.1 Common Issues
  - API rate limits
  - Memory exhaustion
  - Test timeouts
  - Git conflicts
- 8.5.2 Debug Mode
- 8.5.3 Health Checks
- 8.5.4 Recovery Procedures

#### 8.6 Backup and Recovery
- 8.6.1 Memory Backup
- 8.6.2 Configuration Backup
- 8.6.3 Disaster Recovery

#### 8.7 User Story: "Running Agency 24/7"
```
As an operator,
I want to run Agency in production continuously,
So that it can autonomously maintain our codebase.

Acceptance Criteria:
- Set up monitoring
- Configure alerting
- Handle failures gracefully
- Maintain audit trails
```

---

### Chapter 9: Advanced Topics
**Estimated Length**: 1,000 lines
**Priority**: P3 (Write Last)

#### 9.1 Learning and Memory Architecture
- 9.1.1 VectorStore Deep Dive
- 9.1.2 Semantic Search Implementation
- 9.1.3 Cross-Session Persistence
- 9.1.4 Firestore Backend Setup
- 9.1.5 Example: Custom Learning Patterns

#### 9.2 DSPy Integration
- 9.2.1 DSPy vs Traditional Agents
- 9.2.2 When to Use DSPy Agents
- 9.2.3 Chain-of-Thought Reasoning
- 9.2.4 A/B Testing Framework
- 9.2.5 Example: DSPy Agent Usage

#### 9.3 Trinity Protocol
- 9.3.1 Overview and Status
- 9.3.2 Ambient Intelligence System
- 9.3.3 Pattern Detection
- 9.3.4 Project Execution Engine
- 9.3.5 Example: Trinity Workflow

#### 9.4 Custom Tool Development
- 9.4.1 Tool Architecture
- 9.4.2 Creating a New Tool
- 9.4.3 Constitutional Compliance for Tools
- 9.4.4 Testing Tools
- 9.4.5 Example: Complete Tool Implementation

#### 9.5 Custom Agent Development
- 9.5.1 Agent Architecture
- 9.5.2 Creating a New Agent
- 9.5.3 Agent Communication Patterns
- 9.5.4 Testing Agents
- 9.5.5 Example: Complete Agent Implementation

#### 9.6 Model Policy Customization
- 9.6.1 Model Selection Strategy
- 9.6.2 Cost vs Quality Tradeoffs
- 9.6.3 Custom Model Configuration
- 9.6.4 Example: Custom Model Policy

#### 9.7 Extension Points
- 9.7.1 Plugin System
- 9.7.2 Custom Workflows
- 9.7.3 Integration APIs
- 9.7.4 Example: Custom Workflow

---

### Chapter 10: API Reference
**Estimated Length**: 1,500 lines
**Priority**: P2 (Write Third)

#### 10.1 Agent Functions

**ChiefArchitectAgent API**
```python
class ChiefArchitectAgent:
    """
    Strategic oversight and self-directed task creation

    Attributes:
        model: LLM model name
        agent_context: Shared context for memory and coordination
    """

    def __init__(
        self,
        model: str = "gpt-5",
        agent_context: AgentContext | None = None
    ):
        """
        Initialize ChiefArchitectAgent

        Args:
            model: LLM model to use (default: gpt-5)
            agent_context: Shared context (created if not provided)

        Raises:
            ConstitutionalViolation: If compliance checks fail

        Example:
            >>> from chief_architect_agent import create_chief_architect
            >>> agent = create_chief_architect(model="gpt-5")
            >>> result = agent.create_adr(topic="New API Design")
        """
```

[Continue for all agents]

#### 10.2 Tool Functions
[Complete API docs for all 45+ tools]

#### 10.3 Pydantic Models
```python
class LearningPattern(BaseModel):
    """
    Represents a learned pattern from system experience

    Attributes:
        pattern_id: Unique identifier
        description: Human-readable description
        confidence: Confidence score (0.0 to 1.0)
        evidence_count: Number of occurrences observed
        tags: Categorization tags
        created_at: Creation timestamp

    Example:
        >>> pattern = LearningPattern(
        ...     pattern_id="error-handling-retry",
        ...     description="Retry with exponential backoff",
        ...     confidence=0.87,
        ...     evidence_count=15,
        ...     tags=["error-handling", "resilience"]
        ... )
    """
```

[Continue for all models]

#### 10.4 Type Definitions
```python
# JSONValue type
JSONValue = Union[
    str, int, float, bool, None,
    Dict[str, 'JSONValue'],
    List['JSONValue']
]

# Result pattern
class Ok(Generic[T]):
    """Success result containing value"""
    def __init__(self, value: T):
        self.value = value

class Err(Generic[E]):
    """Error result containing error"""
    def __init__(self, error: E):
        self.error = error

Result = Union[Ok[T], Err[E]]
```

[Continue for all types]

---

## Appendices

### Appendix A: Glossary
**Estimated Length**: 200 lines

- **ADR**: Architecture Decision Record
- **NECESSARY Pattern**: Quality pattern for tests (N-E-C-E-S-S-A-R-Y)
- **Q(T) Score**: Test quality metric
- **Spec-Kit**: Specification methodology (Goals, Personas, Criteria)
- **Constitutional Compliance**: Adherence to 5 articles
- **VectorStore**: Semantic search database for learning
- **Agent Context**: Shared memory and coordination system
- [Continue for all terms]

### Appendix B: Configuration Reference
**Estimated Length**: 300 lines

Complete list of all environment variables with descriptions and examples.

### Appendix C: File Structure Reference
**Estimated Length**: 200 lines

Complete directory structure with descriptions.

### Appendix D: Command Line Reference
**Estimated Length**: 100 lines

All CLI commands and options.

### Appendix E: Keyboard Shortcuts
**Estimated Length**: 50 lines

If applicable.

### Appendix F: Migration Guides
**Estimated Length**: 200 lines

- Migrating from version X to Y
- Breaking changes
- Deprecation notices

### Appendix G: Contributing Guide
**Estimated Length**: 300 lines

How to contribute to Agency.

---

## Companion Documents

### QUICK_START.md (200 lines)
Extracted from Chapter 1, optimized for immediate success.

Structure:
1. Prerequisites (1 minute)
2. Install (2 minutes)
3. Run first task (2 minutes)
4. Next steps (links to manual)

### API_REFERENCE.md (3,000 lines)
Extracted from Chapter 10, comprehensive API documentation.

Structure:
1. Agent APIs
2. Tool APIs
3. Model APIs
4. Type Definitions
5. Examples

### TROUBLESHOOTING.md (1,000 lines)
Extracted from Chapter 8, focused on problem-solving.

Structure:
1. Common Issues
2. Error Messages Explained
3. Debug Procedures
4. Recovery Steps
5. Getting Help

### EXAMPLES.md (800 lines)
Runnable code examples from all chapters.

Structure:
1. Basic Examples
2. Workflow Examples
3. Advanced Examples
4. Integration Examples
5. Custom Development Examples

---

## Writing Priorities

### Phase 1: Foundation (Week 1)
**Target**: Get users productive quickly
1. QUICK_START.md
2. Chapter 1: Quick Start Guide
3. Chapter 2: Core Concepts
4. Chapter 3: Prime Commands Reference

### Phase 2: Core Usage (Week 2)
**Target**: Enable all common workflows
5. Chapter 4: Development Workflows
6. Chapter 5: Agent Deep Dive
7. TROUBLESHOOTING.md

### Phase 3: Deep Reference (Week 3)
**Target**: Complete technical reference
8. Chapter 6: Tool Reference
9. Chapter 7: Constitutional Compliance Guide
10. Chapter 10: API Reference
11. API_REFERENCE.md

### Phase 4: Advanced & Production (Week 4)
**Target**: Enable production deployment
12. Chapter 8: Production Operations
13. Chapter 9: Advanced Topics
14. EXAMPLES.md
15. All Appendices

---

## Quality Standards

### For Each Section
- [ ] Clear heading structure (H1 → H2 → H3)
- [ ] At least one runnable example
- [ ] Cross-references to related sections
- [ ] User story included where applicable
- [ ] Code examples validated
- [ ] No outdated information
- [ ] Consistent terminology
- [ ] Proper markdown formatting

### For Code Examples
- [ ] Syntactically correct
- [ ] Includes comments
- [ ] Shows expected output
- [ ] Handles errors
- [ ] Follows constitutional guidelines

### For User Stories
- [ ] "As a [role]" format
- [ ] Clear goal ("I want to...")
- [ ] Clear benefit ("So that...")
- [ ] Specific acceptance criteria
- [ ] Realistic scenario

---

## Maintenance Plan

### Version Control
- Manual stored in git
- Version number in header
- Changelog section
- Last updated date

### Review Schedule
- **Weekly**: New PRs update relevant sections
- **Monthly**: Complete review for accuracy
- **Quarterly**: Major updates and restructuring
- **Annually**: Complete rewrite if needed

### Metrics to Track
- User feedback (confusion points)
- Most visited sections
- Search queries (what users look for)
- Outdated sections (last updated > 3 months)

### Automation
- Link checker (detect broken cross-references)
- Code validator (test all examples)
- Markdown linter (consistent formatting)
- Spell checker

---

## Success Criteria

### Completion Criteria
- [ ] All 10 chapters written
- [ ] All 4 companion documents created
- [ ] All appendices complete
- [ ] 100+ runnable examples
- [ ] 25+ user stories
- [ ] All cross-references valid
- [ ] All code examples tested

### Quality Criteria
- [ ] New user can complete first task in 5 minutes
- [ ] Developer can understand agent model in 15 minutes
- [ ] Operator can set up monitoring in 30 minutes
- [ ] Architect can understand full system in 1 hour
- [ ] Zero broken links or references
- [ ] Zero untested code examples

### User Feedback Goals
- "Clear and easy to follow" - 90%+
- "Found what I needed" - 85%+
- "Examples worked first try" - 95%+
- "Confident using Agency" - 80%+

---

## Estimated Effort

### Total Estimated Lines
- USER_MANUAL.md: ~5,000 lines
- QUICK_START.md: ~200 lines
- API_REFERENCE.md: ~3,000 lines
- TROUBLESHOOTING.md: ~1,000 lines
- EXAMPLES.md: ~800 lines
- **Total**: ~10,000 lines

### Writing Time Estimates
- Phase 1 (Foundation): 20 hours
- Phase 2 (Core Usage): 25 hours
- Phase 3 (Deep Reference): 30 hours
- Phase 4 (Advanced): 20 hours
- Editing and validation: 15 hours
- **Total**: ~110 hours (~3 weeks full-time)

### Resources Needed
- 1 technical writer (lead)
- 1 developer (code examples validation)
- 1 reviewer (accuracy check)
- CI/CD integration (automation)

---

## Next Steps

### Immediate Actions
1. Review and approve this plan
2. Set up documentation infrastructure
3. Create document templates
4. Begin Phase 1 writing

### Before Writing Begins
1. Resolve all high-priority audit findings
2. Verify actual test/tool/agent counts
3. Create examples directory structure
4. Set up CI/CD for docs

### During Writing
1. Write one chapter at a time
2. Validate all code examples immediately
3. Get user feedback on drafts
4. Iterate based on feedback

### After Completion
1. Launch user manual
2. Gather feedback
3. Iterate based on usage
4. Maintain continuously

---

**Plan Status**: DRAFT
**Next Review**: After audit findings addressed
**Owner**: Documentation Team
**Last Updated**: 2025-10-01
