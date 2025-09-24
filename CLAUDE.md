# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start with CLI Helper
```bash
./agency_cli setup    # Complete environment setup
./agency_cli test     # Run comprehensive test suite
./agency_cli demo     # Autonomous healing demonstration
./agency_cli run      # Start the Agency (requires sudo on macOS)
./agency_cli health   # System health and healing status
./agency_cli logs     # View recent logs and activities
```

### Running the Agency
```bash
sudo python agency.py          # Direct terminal demo - requires sudo on macOS for filesystem access
./agency_cli run              # CLI helper (recommended)
python demo_autonomous_healing.py  # Autonomous healing demonstration
```

### Testing
```bash
python run_tests.py                          # Run unit tests only (default)
python run_tests.py --run-integration        # Run integration tests only
python run_tests.py --run-all                # Run all tests (unit + integration)
python run_tests.py test_specific_file.py    # Run specific test file
python tests/run_memory_tests.py             # Run memory system tests
python -m pytest tests/ -v                   # Direct pytest execution
python -m pytest tests/ -v -m "not integration"  # Unit tests only via pytest
python -m pytest tests/test_specific.py::TestClass::test_method  # Run specific test method
python -m pytest tests/ -v --tb=short        # Show short traceback format
python -m pytest tests/ -v -x                # Stop on first failure
python -m pytest tests/ -v --lf              # Run only last failed tests
python -m pytest tests/ -v --co              # Collect tests without running
```

### Testing Quality Patterns
The Agency enforces 100% test success rate via constitutional requirements (ADR-002):

**NECESSARY Pattern Analysis:**
- **N**: No Missing Behaviors - All code paths covered
- **E**: Edge Cases - Boundary conditions tested
- **C**: Comprehensive - Multiple test vectors per function
- **E**: Error Conditions - Exception handling verified
- **S**: State Validation - Object state changes confirmed
- **S**: Side Effects - External impacts tested
- **A**: Async Operations - Concurrent code coverage
- **R**: Regression Prevention - Historical bugs covered
- **Y**: Yielding Confidence - Overall quality assurance

**Quality Score Calculation:**
```python
Q(T) = Π(property_scores) × (|behaviors_covered| / |total_behaviors|)
```

**Test Markers:**
- `@pytest.mark.unit` - Fast unit tests (< 1s each)
- `@pytest.mark.integration` - Slower integration tests
- `@pytest.mark.asyncio` - Async test functions
- `pytest.skip()` - Platform-specific skipping

### Code Quality
```bash
ruff check . --fix          # Fix linting issues and sort imports
ruff format .               # Format code
pre-commit run --all-files  # Run all pre-commit hooks
```

### Initial Setup
```bash
# Recommended: Use CLI helper for complete setup
./agency_cli setup

# Manual setup (if needed)
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# Fix LiteLLM bug with Anthropic reasoning models:
python -m pip install git+https://github.com/openai/openai-agents-python.git@main
```

## 🏥 Autonomous Healing System

### Core Capability
The Agency features **unified self-healing** with a consolidated architecture that reduces 62+ scattered files to 3 core modules.

### Unified Core Architecture (NEW)
**3 Essential Modules** replacing 62+ scattered implementations:

#### core/self_healing.py
```python
class SelfHealingCore:
    def detect_errors(self, path: str) -> List[Finding]
    def fix_error(self, error: Finding) -> bool
    def verify(self) -> bool  # 100% test pass required
```

#### core/telemetry.py
```python
class SimpleTelemetry:
    def log(self, event: str, data: dict, level: str)
    def query(self, event_filter: str, since: datetime, limit: int)
    def get_metrics(self) -> dict  # Health score, error rates
```

#### core/patterns.py
```python
class UnifiedPatternStore:
    def add(self, pattern: Pattern) -> bool
    def find(self, query: str, pattern_type: str, tags: list) -> List[Pattern]
    def learn_from_fix(self, error_type: str, original: str, fixed: str, test_passed: bool)
```

### Migration & Feature Flags
```bash
# Enable unified core (default: false for backward compatibility)
export ENABLE_UNIFIED_CORE=true

# Enable pattern persistence (default: in-memory)
export PERSIST_PATTERNS=true
```

### Key Benefits
- **95% code reduction**: From 62 files to 3 core modules
- **Single telemetry sink**: logs/events/run_*.jsonl with retention
- **Pattern learning**: Automatic learning from successful fixes
- **Feature-flagged migration**: Safe, gradual rollout
- **Clear service boundaries**: Well-defined APIs for autonomous agents

### Safety Mechanisms
- **Test-Driven Verification**: No changes without 100% test success rate
- **Automatic Rollback**: Failed fixes immediately reverted
- **Constitutional Compliance**: All healing actions follow governance principles
- **Telemetry & Audit Trail**: Complete observability via unified sink

### Demonstration
```bash
# Unified demo showcasing consolidated architecture
python demo_unified.py

# Legacy demos archived in demos/archive/
python demos/archive/demo_autonomous_healing.py  # Original demo

# Monitor via CLI
./agency_cli health
./agency_cli logs
```

## Architecture Overview

### Simplified Multi-Agent System (10 Agents)
The Agency implements a **focused, constitutional multi-agent architecture** using the Agency Swarm framework:

**Core Agents:**
- **ChiefArchitectAgent**: Strategic oversight, self-directed task creation, and architectural guidance
- **AgencyCodeAgent**: Primary development agent with comprehensive toolset for implementation
- **PlannerAgent**: Strategic planning using spec-kit methodology for formal specifications
- **AuditorAgent**: Quality analysis using NECESSARY pattern and Q(T) scoring
- **TestGeneratorAgent**: NECESSARY-compliant test generation from audit reports
- **LearningAgent**: Pattern analysis and institutional memory with VectorStore integration
- **MergerAgent**: Integration and pull request management
- **QualityEnforcerAgent** ⭐: **Constitutional compliance and autonomous healing core**
- **ToolsmithAgent**: Tool development and enhancement
- **WorkCompletionSummaryAgent**: Intelligent task summaries and completion reporting

**Key Simplifications:**
- Removed over-engineered agents (BottleneckOptimizer, CostOptimizer, ConstitutionalEnforcement)
- Consolidated responsibilities into focused, single-purpose agents
- Streamlined communication flows from 32 to 18 essential patterns
- Enhanced QualityEnforcerAgent with complete autonomous healing capabilities

**Communication Flow:**
```
ChiefArchitect → Auditor (strategic oversight)
ChiefArchitect → LearningAgent (pattern analysis)
ChiefArchitect → Planner (strategic planning)
Planner ↔ Coder (bidirectional handoff)
Planner → Auditor (quality validation)
Auditor → TestGenerator (quality improvement)
TestGenerator → Coder (test implementation)
Coder → Merger (integration)
```

### Agent Communication Patterns

**Message Handoff System:**
```python
from agency_swarm.tools import SendMessageHandoff

# Standard handoff pattern
handoff_tool = SendMessageHandoff(
    recipient=target_agent_name,
    message="Context-specific instructions",
    context_variables={"key": "value"}
)
```

**Communication Types:**
- **Unidirectional**: ChiefArchitect → Auditor (strategic oversight)
- **Bidirectional**: Planner ↔ Coder (collaborative planning/implementation)
- **Sequential**: Auditor → TestGenerator → Coder (quality improvement pipeline)
- **Context-Aware**: Based on intent routing (e.g., "tts" triggers WorkCompletionSummaryAgent)

**Agent Selection Logic:**
1. **Intent Detection**: Message content analyzed for keywords/patterns
2. **Context Routing**: `context['route_to_agent']` variable controls flow
3. **Capability Matching**: Task requirements matched to agent toolsets
4. **Load Balancing**: Future: distribute work across agent instances

**Handoff Context Variables:**
- `session_id`: Tracks conversation continuity
- `task_priority`: Influences agent response timing
- `tools_needed`: Suggests required tool subset
- `complexity_level`: Affects reasoning effort setting

### Memory System Integration

**Unified Agent Context:**
```python
from shared.agent_context import AgentContext, create_agent_context
from agency_memory import Memory, create_firestore_store

# Shared memory across all agents
memory_store = create_firestore_store() if os.getenv("FRESH_USE_FIRESTORE") else None
shared_memory = Memory(store=memory_store)
shared_context = create_agent_context(memory=shared_memory)
```

**Memory Storage Patterns:**
```python
# Store structured data with tags for efficient retrieval
agent_context.store_memory(
    f"pattern_{session_id}",
    {
        "pattern_type": "error_resolution",
        "context": {...},
        "success_rate": 0.95,
        "timestamp": datetime.now().isoformat()
    },
    ["error_handling", "success_pattern", "learning"]
)

# Retrieve relevant patterns
patterns = agent_context.query_memory(
    tags=["error_handling"],
    limit=5,
    similarity_threshold=0.7
)
```

**VectorStore Learning Integration:**
```python
# Automatic learning consolidation
class LearningMemoryHook:
    def after_successful_operation(self, context, result):
        # Extract patterns from successful operations
        patterns = self.extract_success_patterns(context, result)

        # Store in VectorStore for similarity search
        self.vector_store.add_patterns(patterns)

        # Update agent's learning context
        context.update_learnings(patterns)
```

**Session Transcript Analysis:**
- **Automatic logging**: All interactions saved to `logs/sessions/session_YYYYMMDD_HHMMSS.md`
- **Pattern extraction**: LearningAgent analyzes transcripts for effective patterns
- **Knowledge consolidation**: Successful patterns stored in VectorStore
- **Cross-session learning**: Historical patterns inform current decisions

**Memory Hooks Lifecycle:**
```python
# Composite hook pattern for memory integration
filter_hook = create_message_filter_hook()           # Pre-process messages
memory_hook = create_memory_integration_hook(context) # Store/retrieve memory
combined_hook = create_composite_hook([filter_hook, memory_hook])

# Agent creation with memory integration
agent = Agent(
    name="ExampleAgent",
    hooks=combined_hook,  # Automatic memory lifecycle management
    # ... other configuration
)
```

**Learning Trigger Conditions:**
1. **Task Completion**: Successful multi-step operations
2. **Error Recovery**: Patterns that resolved failures
3. **Performance Milestones**: Operations exceeding efficiency thresholds
4. **Tool Effectiveness**: Successful tool combinations and sequences
5. **Constitutional Compliance**: Patterns maintaining 100% compliance

**Memory Fallback Strategy:**
```python
# Graceful degradation when memory operations fail
try:
    result = memory_store.query(query_params)
except MemoryStoreError:
    logger.warning("Memory store unavailable, proceeding without historical context")
    result = default_behavior()
```

**Context Preservation Across Sessions:**
- **Session continuity**: Key context variables persist between sessions
- **Agent handoffs**: Context automatically transferred between agents
- **State reconstruction**: Ability to resume interrupted workflows
- **Learning application**: Historical patterns automatically applied to new tasks

### Constitutional Governance
The Agency operates under strict constitutional principles (`constitution.md`):
- **Article I**: Complete Context Before Action - No action without full understanding
- **Article II**: 100% Verification - Main branch must maintain 100% test success rate
- **Article III**: Automated Enforcement - Quality standards technically enforced, no manual overrides
- **Article IV**: Continuous Learning - Automatic improvement through experiential learning
- **Article V**: Spec-Driven Development - All features require formal specs in `specs/` and plans in `plans/`

### Tool System
Central tools in `tools/` directory:
- **File operations**: `read.py`, `write.py`, `edit.py`, `multi_edit.py`
- **Search**: `grep.py`, `glob.py`, `ls.py`
- **Version control**: `git.py`
- **System**: `bash.py`, `todo_write.py`, `exit_plan_mode.py`
- **Specialized**: `notebook_edit.py`, `notebook_read.py`, `claude_web_search.py`, `feature_inventory.py`
- **Enterprise Infrastructure**: Extracted from 18K+ line enterprise branch:
  - **Orchestrator System**: `orchestrator/` - Parallel execution, retry policies, telemetry
  - **Telemetry System**: `telemetry/` - JSONL logging, secret sanitization, aggregation
  - **CLI Tools**: `agency_cli/` - Dashboard, tail, navigation utilities
  - **Codegen System**: `codegen/` - Static analysis, test generation, scaffolding
- **Model-specific**: Tools auto-selected based on model type (OpenAI vs Claude vs Grok)

### Enterprise Infrastructure Components

**Orchestrator System** (`tools/orchestrator/`):
```python
from tools.orchestrator.scheduler import run_parallel, OrchestrationPolicy
from tools.orchestrator.api import execute_parallel, execute_graph
from tools.orchestrator.graph import TaskGraph, run_graph

# Parallel task execution with retry policies
policy = OrchestrationPolicy(max_concurrency=4, retry_max=3)
result = await execute_parallel(ctx, tasks, policy)

# DAG-based execution with dependencies
graph = TaskGraph(nodes=task_specs, edges=dependencies)
result = await execute_graph(ctx, graph, policy)
```

**Telemetry System** (`tools/telemetry/`):
```python
from tools.telemetry.sanitize import redact_event
from tools.telemetry.aggregator import aggregate, list_events

# Sanitize sensitive data before logging
safe_event = redact_event(raw_event)

# Get dashboard metrics and filtered events
dashboard = aggregate(since="1h")
events = list_events(since="15m", grep="error")
```

**CLI Tools** (`tools/agency_cli/`):
```python
from tools.agency_cli.dashboard import main as dashboard_main
from tools.agency_cli.tail import main as tail_main
from tools.agency_cli.nav import extract_symbols, find_references

# Live dashboard - use as CLI: python -m tools.agency_cli.dashboard --watch
dashboard_main()

# Telemetry tail - use as CLI: python -m tools.agency_cli.tail --since=1h --grep=error
tail_main()

# Code navigation
symbols = extract_symbols("tools/")  # Extract all Python symbols
refs = find_references(".", "TaskSpec")  # Find all references to TaskSpec
```

**Codegen System** (`tools/codegen/`):
```python
from tools.codegen.analyzer import suggest_refactors
from tools.codegen.test_gen import generate_tests_from_spec
from tools.codegen.scaffold import scaffold_module

# Static analysis with refactoring suggestions
suggestions = suggest_refactors(["path/to/file.py"])

# Generate test skeletons from specification acceptance criteria
tests = generate_tests_from_spec("specs/spec-feature.md", "tests/")

# Scaffold new modules from templates
files = scaffold_module("tool", "my_tool", "tools/my_tool/")
```

**Enterprise Infrastructure Tools:**
- **Orchestrator**: `tools/orchestrator/` - Advanced agent task coordination with parallel execution, retry policies, and telemetry
- **Telemetry**: `tools/telemetry/` - Production-grade event logging, sanitization, and real-time analysis

**Orchestrator Usage:**
```python
from tools.orchestrator.scheduler import run_parallel, OrchestrationPolicy, TaskSpec, RetryPolicy

# Define sophisticated orchestration policy
policy = OrchestrationPolicy(
    max_concurrency=6,                    # Parallel execution limit
    retry=RetryPolicy(
        max_attempts=3,                   # Retry failed tasks up to 3 times
        backoff="exp",                    # Exponential backoff strategy
        base_delay_s=0.5,                # Base delay between retries
        jitter=0.2                       # Add jitter to prevent thundering herd
    ),
    timeout_s=30.0,                      # Task timeout
    fairness="round_robin",              # Fair scheduling
    cancellation="isolated"              # Isolated failure handling
)

# Execute tasks in parallel with full monitoring
result = await run_parallel(context, task_specs, policy)
```

**Telemetry Integration:**
```python
from tools.telemetry.aggregator import aggregate, list_events
from tools.telemetry.sanitize import redact_event

# Get real-time dashboard metrics
dashboard = aggregate(since="1h")
print(f"Active agents: {dashboard['agents_active']}")
print(f"Success rate: {dashboard['recent_results']}")
print(f"Resource utilization: {dashboard['resources']['utilization']}")

# Monitor recent events with filtering
events = list_events(since="15m", grep="error", limit=50)

# Sanitize sensitive data before logging
safe_event = redact_event(raw_event)
```

**Tool Security Patterns:**
- Path validation: All tools use absolute paths
- Permission handling: Graceful degradation for filesystem errors
- Background execution: Support for long-running commands with `run_in_background`
- Error resilience: Comprehensive error handling with fallback mechanisms

### Error Handling & Resilience Patterns

**RetryController Architecture:**
```python
from shared.retry_controller import RetryController, ExponentialBackoffStrategy

# Standard retry pattern
controller = RetryController(
    strategy=ExponentialBackoffStrategy(max_retries=3, base_delay=1.0),
    circuit_breaker_enabled=True
)

@controller.with_retry
def operation_with_resilience():
    # Your operation here
    pass
```

**Circuit Breaker Pattern:**
- **Closed State**: Normal operation, failures tracked
- **Open State**: Fails fast, prevents cascade failures
- **Half-Open State**: Gradual recovery testing
- **Thresholds**: 5 failures trigger open state, 60s timeout

**Snapshot/Undo Mechanism:**
```python
from tools import UndoSnapshot

# Create workspace snapshot before risky operations
snapshot = UndoSnapshot()
snapshot_id = snapshot.create_snapshot("pre_refactor_state")

try:
    # Perform risky operation
    perform_complex_refactoring()
except Exception:
    # Restore on failure
    snapshot.restore_snapshot(snapshot_id)
    raise
```

**Error Recovery Strategies:**
1. **Graceful Degradation**: Fallback to simpler approaches
2. **Automatic Retry**: Exponential backoff with jitter
3. **State Restoration**: Undo mechanisms for failed operations
4. **Context Preservation**: Maintain session state across failures
5. **Learning Integration**: Store failure patterns for future avoidance

**Constitutional Enforcement:**
- **Article I**: Complete context before action (no partial operations)
- **Article II**: 100% test verification (failures block progress)
- **Article III**: Automated quality gates (no manual overrides)
- All operations must pass constitutional validation before execution

### Performance Optimization Patterns

**Parallel Tool Execution:**
```python
# Batch multiple tools in single response for optimal performance
tools.batch_execute([
    Read(file_path="/path/to/file1.py"),
    Read(file_path="/path/to/file2.py"),
    Grep(pattern="function.*", glob="**/*.py")
])
```

**Context Management:**
- **32K token limit**: Auto-truncation for memory operations
- **Context preservation**: Essential information retained across operations
- **Memory optimization**: Efficient storage and retrieval patterns
- **Session boundaries**: Clean context transitions between sessions

**Background Execution Patterns:**
```python
# Long-running commands with background execution
bash_result = Bash(
    command="npm run build",
    run_in_background=True,
    timeout=600000  # 10 minutes
)

# Monitor progress with BashOutput
while not bash_result.completed:
    output = BashOutput(bash_id=bash_result.id)
    # Process incremental output
```

**Tool Selection Optimization:**
- **Model-aware tooling**: Different tools for OpenAI vs Claude vs Grok
- **Capability matching**: Right tool for the task complexity
- **Resource allocation**: Memory vs speed tradeoffs
- **Concurrent operations**: Multiple agents working simultaneously

**Memory System Performance:**
```python
# Efficient memory patterns
agent_context.store_memory(
    key=f"pattern_{session_id}",
    data={"compressed": True, "indexed": True},
    tags=["performance", "optimization"]  # For fast retrieval
)
```

**Agent Reasoning Optimization:**
- **High effort**: Complex planning and architecture decisions
- **Medium effort**: Standard implementation tasks
- **Low effort**: Simple operations and summaries
- **Adaptive effort**: Dynamic adjustment based on task complexity

## Key Patterns

### Agent Creation Pattern
Every agent follows a factory pattern with shared context injection:
```python
create_agent_name(model="gpt-5", reasoning_effort="high", agent_context=shared_context)
```

### File Structure Convention
```
agent_name/
├── __init__.py
├── agent_name.py           # Agent class definition
├── instructions.md         # Claude instructions
├── instructions-gpt-5.md   # GPT-5 specific (if different)
└── tools/                  # Agent-specific tools (optional)
```

### Testing Patterns
- Test files: `test_*.py` in `tests/` directory
- Unit tests: `tests/unit/` with marker `@pytest.mark.unit`
- Integration tests: Marked with `@pytest.mark.integration`
- Async tests: Use `@pytest.mark.asyncio` decorator
- Fixtures: Centralized in `tests/conftest.py` with workspace cleanup
- Quality gates: Tests must pass 100% before any merge (constitutional requirement)

### CodeHealer NECESSARY Pattern
The 9 universal test quality properties:
- **N**: No Missing Behaviors
- **E**: Edge Cases
- **C**: Comprehensive
- **E**: Error Conditions
- **S**: State Validation
- **S**: Side Effects
- **A**: Async Operations
- **R**: Regression Prevention
- **Y**: Yielding Confidence

Quality score: `Q(T) = Π(p_i) × (|B_c| / |B|)`

### Spec-Driven Development Workflow

**Phase 1: Constitutional Analysis**
```bash
# Always start with constitutional review
constitution_check = read_constitution()
validate_against_articles(planned_feature)
```

**Phase 2: Specification Creation**
```markdown
# specs/spec-XXX-feature-name.md
## Goals
- Primary objectives and success criteria

## Non-Goals
- Explicitly excluded scope

## Personas
- Target users and use cases

## Acceptance Criteria
- Verifiable completion requirements
```

**Phase 3: Technical Planning**
```markdown
# plans/plan-XXX-feature-name.md
## Architecture Overview
- System design and component interactions

## Agent Assignments
- Which agents handle which aspects

## Tool Usage Strategy
- Required tools and execution patterns

## Implementation Contracts
- Interfaces and data flow specifications
```

**Phase 4: Task Decomposition**
```python
# TodoWrite integration with spec traceability
TodoWrite(todos=[
    {
        "content": "Implement core feature logic",
        "status": "pending",
        "activeForm": "Implementing core feature logic",
        "spec_reference": "spec-XXX.md#goals",
        "plan_reference": "plan-XXX.md#implementation"
    }
])
```

**Phase 5: Constitutional Implementation**
- All code changes pass ADR-002 (100% test verification)
- Complete context gathering per ADR-001
- Automated enforcement via ADR-003
- Continuous learning integration per ADR-004

**Phase 6: Quality Validation**
```bash
# Constitutional compliance pipeline
python run_tests.py --run-all  # Must achieve 100% pass rate
ruff check . --fix             # Code quality enforcement
pre-commit run --all-files     # Pre-commit hook validation
```

**Workflow Checkpoints:**
1. **Spec Approval**: Stakeholder sign-off on goals and criteria
2. **Plan Review**: Technical architecture validation
3. **Implementation Gates**: Each task verified against acceptance criteria
4. **Constitutional Validation**: Every change passes all articles
5. **Quality Gates**: 100% test success before merge

### Advanced Tool Patterns

**Context Handoff Mechanism:**
```python
from tools import ContextHandoff

# Transfer context between agents
handoff = ContextHandoff()
handoff.create_handoff(
    from_agent="PlannerAgent",
    to_agent="AgencyCodeAgent",
    context={
        "task_id": "implement_feature_x",
        "specifications": {...},
        "constraints": {...}
    },
    priority="high"
)
```

**Workspace Snapshot Management:**
```python
from tools import UndoSnapshot

# Create snapshots for risky operations
snapshot = UndoSnapshot()

# Before major refactoring
snapshot_id = snapshot.create_snapshot("pre_refactor")
perform_complex_refactoring()

# Restore if issues detected
if has_issues():
    snapshot.restore_snapshot(snapshot_id)
```

**Background Process Monitoring:**
```python
# Start long-running process
bash_process = Bash(
    command="npm run build:production",
    run_in_background=True,
    timeout=1800000  # 30 minutes
)

# Monitor with progress filtering
output = BashOutput(
    bash_id=bash_process.id,
    filter=".*error.*|.*warning.*"  # Only show errors/warnings
)
```

**Multi-File Operations:**
```python
# Batch file operations for efficiency
MultiEdit(
    file_path="/path/to/file.py",
    edits=[
        {"old_string": "old_pattern_1", "new_string": "new_pattern_1"},
        {"old_string": "old_pattern_2", "new_string": "new_pattern_2"},
        {"old_string": "class_name", "new_string": "new_class_name", "replace_all": True}
    ]
)
```

**Smart Search Patterns:**
```python
# Efficient codebase exploration
search_results = Grep(
    pattern="def create_.*_agent",
    glob="**/*.py",
    output_mode="files_with_matches",
    head_limit=20
)

# Context-aware file discovery
config_files = Glob(
    pattern="**/config*.{py,json,yaml,yml}",
    path="."
)
```

**Model-Aware Tool Selection:**
```python
# Automatic tool selection based on model capabilities
def select_tools_for_model(model: str) -> list:
    is_openai, is_claude, is_grok = detect_model_type(model)

    if is_openai:
        return [Read, Write, Edit, MultiEdit, Bash, TodoWrite]
    elif is_claude:
        return [Read, Write, Edit, Grep, Glob, Bash, TodoWrite]
    elif is_grok:
        return [Read, Write, Edit, ClaudeWebSearch, Bash, TodoWrite]
```

**Error-Resilient Patterns:**
```python
# Tool execution with automatic retry
@retry_on_failure(max_attempts=3, backoff_factor=2.0)
def resilient_file_operation(file_path: str, content: str):
    try:
        return Write(file_path=file_path, content=content)
    except PermissionError:
        # Fallback to temporary location
        temp_path = f"/tmp/{os.path.basename(file_path)}"
        return Write(file_path=temp_path, content=content)
```

## Core Operating Rules

### Behavioral Standards
- **Minimize token use**: Concise responses, no unnecessary chatter
- **Atomic changes**: Every change must be tested and minimal-intrusive
- **Code over discussion**: Default to repo-style code diffs, not essays
- **Test everything**: Always include unit tests for new code
- **Follow conventions**: Mimic existing code style and patterns

### Hook Integrations
- **RetryController**: Automatic Snapshot/Undo/Retry on validation failures
- **LearningAgent**: Queries VectorStore for patterns, stores institutional memory
- **ChiefArchitect**: Creates `[SELF-DIRECTED TASK]` entries - treat as high priority
- **ToolSmith**: May propose new tools/agents - maintain compatibility

### Task Management
- **TodoWrite usage**: Track all tasks, mark completed immediately
- **Planner handoff**: For complex tasks (5+ steps, multi-component architecture)
- **Constitutional validation**: Every action must comply with `/constitution.md`

### CI/CD Integration & Automation

**GitHub Actions Workflows:**
```yaml
# .github/workflows/ci.yml - Core CI Pipeline
name: CI Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      - name: Run comprehensive test suite
        run: |
          python run_tests.py --run-all  # 100% pass rate required
          ruff check . --fix
          pre-commit run --all-files
```

**Merge Guardian Protection:**
```yaml
# .github/workflows/merge-guardian.yml
# Enforces constitutional Article III (Automated Enforcement)
name: Merge Guardian
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  constitutional-compliance:
    runs-on: ubuntu-latest
    steps:
      - name: Verify 100% test success
        run: |
          if [ $TEST_EXIT_CODE -ne 0 ]; then
            echo "❌ BLOCKED by Constitution Article II"
            echo "100% test success required - no exceptions"
            exit 1
          fi
```

**Pre-commit Hook Enforcement:**
```bash
# .pre-commit-config.yaml integration
repos:
  - repo: local
    hooks:
      - id: constitutional-validation
        name: Constitutional Compliance Check
        entry: python scripts/validate_constitution.py
        language: python
        always_run: true
        pass_filenames: false
```

**Automated Quality Gates:**
- **Code Quality**: Ruff linting and formatting enforced
- **Test Coverage**: 100% test success rate (no negotiation)
- **Constitutional Compliance**: All 5 articles validated
- **Security Scanning**: Dependency vulnerability checks
- **Performance Monitoring**: Test execution time tracking

**Branch Protection Rules:**
```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "CI Pipeline / test (3.12)",
      "CI Pipeline / test (3.13)",
      "Merge Guardian / constitutional-compliance",
      "Claude Code Review / review"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  }
}
```

**Deployment Automation Patterns:**
```bash
# Automated deployment pipeline
deploy_staging() {
    # Deploy to staging environment
    kubectl apply -f k8s/staging/
    run_integration_tests
    if [ $? -eq 0 ]; then
        echo "✅ Staging deployment successful"
    else
        rollback_staging
        exit 1
    fi
}

deploy_production() {
    # Blue-green deployment pattern
    deploy_blue_environment
    run_smoke_tests
    switch_traffic_to_blue
    monitor_health_metrics
}
```

**Monitoring and Observability:**
- **Agent Performance Metrics**: Execution time, success rates, error patterns
- **Memory Usage Tracking**: VectorStore efficiency, context size optimization
- **Constitutional Compliance Monitoring**: Violation detection and alerting
- **Learning Effectiveness**: Pattern application success rates

**Rollback Strategies:**
```bash
# Automatic rollback on constitutional violations
monitor_constitutional_compliance() {
    while true; do
        if detect_constitutional_violation; then
            echo "🚨 Constitutional violation detected"
            trigger_automatic_rollback
            alert_development_team
        fi
        sleep 60
    done
}
```

## Important Notes

- Model selection in `agency.py`: Currently set to `gpt-5` with high reasoning effort
- Reasoning settings: Configurable effort levels (low/medium/high) and summary modes
- Context limit: 32K tokens with auto-truncation for memory operations
- Shared instructions: Referenced via `project-overview.md` in agency initialization
- Environment variables: `OPENAI_API_KEY`, `FRESH_USE_FIRESTORE`, Firebase credentials in `.env`
- Pre-commit hooks: Automatically run ruff checks and formatting on commit
- Subagent creation: Use template in `subagent_example/` or prompt Claude Code to create new agents