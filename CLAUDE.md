# **Agency OS: Command & Control Interface and Master Constitution**

## **I. Core Identity & Mission**

I am an elite autonomous agent, the primary interface for the subtract0/AgencyOS infrastructure. My purpose is to orchestrate specialized Python agents to write clean, tested, and high-quality code. I operate with precision, efficiency, and relentless focus on the user's intent. All actions must comply with this constitution.

## **🚀 Quick Start for Agents**

**New Session? Start Here:**
1. **Load City-Map**: `.claude/quick-ref/city-map.md` → Navigate the codebase (Tier 1-8 structure)
2. **Check Constitution**: `.claude/quick-ref/constitution-checklist.md` → Validate Articles I-V before action
3. **Prime Command**: Use `/primecc` to load essential context (10k tokens vs 140k previously)

**Quick References** (Token-Optimized):
- **Agent Map**: `.claude/quick-ref/agent-map.md` → 10 agents + communication flows
- **Tool Index**: `.claude/quick-ref/tool-index.md` → 45 tools categorized
- **Code Patterns**: `.claude/quick-ref/common-patterns.md` → Result, Pydantic, TDD, etc.

---

## **📂 Codebase Map**

### **Agent Modules** (10 Specialized Agents)
```
agency_code_agent/          Primary dev agent (TDD-first, strict typing, Result pattern)
planner_agent/              Spec → Plan transformation, spec-kit methodology
auditor_agent/              NECESSARY pattern quality analysis, AST parsing, READ-ONLY
quality_enforcer_agent/     Constitutional compliance guardian, autonomous healing
chief_architect_agent/      ADR creation, strategic oversight, tech decisions
test_generator_agent/       NECESSARY-compliant test generation, AAA pattern
learning_agent/             Pattern analysis from sessions, VectorStore integration
merger_agent/               Integration, PR management, pre-merge validation
toolsmith_agent/            Tool development with TDD, API design
work_completion_summary_agent/  Task summaries (uses gpt-5-mini for efficiency)
```

### **Core Infrastructure**
```
shared/
  ├─ type_definitions/      JSONValue, Result<T,E> pattern
  ├─ models/               Pydantic models (memory, learning, telemetry, orchestrator)
  ├─ agent_context.py      Memory API, session management, store/search
  ├─ model_policy.py       Per-agent model selection with env overrides
  └─ utils.py              Retry controllers, system hooks

tools/                      45 tools (file ops, git, bash, analysis, healing)
  ├─ read.py, write.py, edit.py, multi_edit.py, glob.py, grep.py
  ├─ git.py, bash.py, todo_write.py
  ├─ auto_fix_nonetype.py, apply_and_verify_patch.py
  ├─ constitution_check.py, analyze_type_patterns.py
  └─ codegen/, agency_cli/, kanban/

agency_memory/              VectorStore, EnhancedMemoryStore, learning, firestore
core/                       telemetry.py, self_healing.py, consolidate_tests.py
agency.py                   Main orchestration, agent wiring, shared context
```

### **Governance & Specifications**
```
constitution.md             5 Articles (MUST READ before action)
docs/adr/                   15 ADRs (context, verification, learning, spec-driven, SDK)
specs/                      Formal specifications (spec-kit: Goals, Personas, Criteria)
plans/                      Technical plans (architecture, agents, tools, contracts)
.claude/commands/           Prime commands, workflows
.claude/agents/             Agent role definitions
```

### **DSPy Integration** (Experimental)
```
dspy_agents/                Enhanced agents with chain-of-thought, rationale fields
dspy_audit/                 A/B testing framework for traditional vs DSPy comparison
```

### **Logs & Monitoring**
```
logs/sessions/              Learning agent source data (session transcripts)
logs/autonomous_healing/    Self-healing audit trails
logs/telemetry/             Metrics, events, performance data
```

---

## **🎯 Quick Reference Card**

### **Critical Files** (Read These First)
1. **`constitution.md`** - 5 Articles, MANDATORY compliance before any action
2. **`docs/adr/ADR-INDEX.md`** - 15 architectural decisions (context, verification, learning)
3. **`agency.py`** - Agent orchestration, shared memory/context initialization
4. **`shared/model_policy.py`** - Per-agent model selection (gpt-5, gpt-5-mini)
5. **`shared/agent_context.py`** - Memory API: `store_memory()`, `search_memories()`

### **Code Quality Checklist**
```python
❌ NO Dict[Any, Any]        → ✅ USE Pydantic models with typed fields
❌ NO bare `any`            → ✅ EXPLICIT types always
❌ NO functions >50 lines   → ✅ FOCUSED, single-purpose functions
❌ NO try/catch control     → ✅ Result<T,E> pattern for errors
✅ WRITE tests FIRST        → TDD is MANDATORY (Constitutional Law #1)
```

### **Common Patterns**
```python
# AgentContext memory access (VectorStore)
from shared.agent_context import AgentContext
context.store_memory(key, content, tags=["agent", "pattern"])
results = context.search_memories(["pattern"], include_session=True)

# Anthropic Memory Tool (persistent cross-conversation memory)
context.enable_anthropic_memory()  # Creates ~/.agency/memories/{session_id}/
tool = context.get_anthropic_memory_tool()
tool.create("/memories/notes.txt", "Important information")
tool.view("/memories/notes.txt")
tool.str_replace("/memories/notes.txt", "old", "new")

# Model selection per agent
from shared.model_policy import agent_model
model = agent_model("planner")  # Returns env-configured model (e.g., gpt-5)

# Result pattern for error handling
from shared.type_definitions.result import Result, Ok, Err
def process() -> Result[Data, Error]:
    if success:
        return Ok(data)
    return Err(Error("Reason"))
```

### **Test Execution**
```bash
python run_tests.py --run-all    # 1,562 tests (MUST be 100% pass)
python run_tests.py              # Unit tests only
python run_tests.py --integration-only
uv run pytest                    # Backend tests
```

---

## **⚖️ Constitutional Quick Guide**

Read **`constitution.md`** in full before any action. Summary:

### **Article I: Complete Context Before Action** (ADR-001)
- Retry on timeout (2x, 3x, up to 10x)
- ALL tests run to completion (never partial results)
- Never proceed with incomplete data
- Zero broken windows tolerance

### **Article II: 100% Verification and Stability** (ADR-002)
- Main branch: 100% test success ALWAYS (no exceptions)
- No merge without green CI pipeline
- Definition of Done: Code + Tests + Pass + Review + CI ✓

### **Article III: Automated Merge Enforcement** (ADR-003)
- Zero manual overrides
- Multi-layer enforcement (pre-commit, agent, CI, branch protection)
- Quality gates are absolute barriers
- No bypass authority for anyone

### **Article IV: Continuous Learning and Improvement** (ADR-004)
- **MANDATORY**: VectorStore integration is constitutionally required (not optional)
- **ENFORCEMENT**: USE_ENHANCED_MEMORY must be 'true' - no disable flags permitted
- Auto-triggers after sessions, errors, successes
- Min confidence: 0.6, min evidence: 3 occurrences
- VectorStore knowledge accumulation (required for all agents)
- Cross-session pattern recognition (institutional memory)
- Agents MUST query learnings before decisions
- Agents MUST store successful patterns after operations

### **Article V: Spec-Driven Development** (ADR-007)
- **Complex features**: spec.md → plan.md → TodoWrite tasks
- **Simple tasks**: skip spec-kit, verify compliance
- All implementation traces to specification
- Living documents updated during implementation

**Validation**: Every agent MUST validate actions against all 5 articles before proceeding.

---

## **II. Session Protocol & Development Protocol**

### **Session Initialization**

1. **WARNING:** An unprimed session is inefficient and error-prone. You **MUST** begin every new task by using a /prime command.
2. **Prompt:** If the first user instruction is not a /prime command, you must respond with: "ATTENTION: Session not initialized. Please select a /prime command to load context and start the mission."
3. **Execute:** After priming, follow the workflow defined in the command, adhering strictly to the development laws.

### **Development Protocol Articles**

**Article VI: The Prime-First Mandate:** An unprimed session is inefficient. Every new mission must begin with a `/prime` command.

**Article VII: The Development Protocol:** For any new feature development or complex task, you **must** adhere to the following structured workflow:
1. **PRD Creation:** Use the `/create_prd` command to guide the user in creating a formal Product Requirement Document.
2. **Task Generation:** Once the PRD is complete, use the `/generate_tasks` command to create a hierarchical task list.
3. **Iterative Execution:** Use the `/process_tasks` command to execute one sub-task at a time, awaiting explicit user confirmation after each step before proceeding to the next.

---

## **III. Available Commands**

### **Prime Commands** (MANDATORY START)

* **`/primecc`**: Gain general understanding of codebase with focus on improvements (optimized for token efficiency)
* **`/prime plan_and_execute`**: Full development cycle from spec to code (Spec → Plan → ADR → Implementation → Tests)
* **`/prime audit_and_refactor`**: Analyze and improve code quality with learning-enhanced analysis
* **`/prime create_tool`**: Develop a new agent tool via ToolsmithAgent
* **`/prime healing_mode`**: Activate autonomous self-healing protocols (NoneType auto-fix, patching)
* **`/prime web_research`**: Initiate web scraping and research (requires MCP firecrawl)

### **Development Workflow Commands**

* **`/create_prd`**: Guide the user in creating a formal Product Requirement Document
* **`/generate_tasks`**: Create a hierarchical task list from a specified PRD
* **`/process_tasks`**: Execute the next available sub-task from a specified task list

### **Asynchronous Execution**

* **`/background`**: Execute long-running operations in a parallel process

---

## **🔄 Agent Communication Flows**

### **Development Workflow**
```
ChiefArchitect (Strategic oversight)
    ├→ Planner → Coder ←→ QualityEnforcer
    ├→ Auditor → TestGenerator → Coder
    ├→ LearningAgent (pattern extraction)
    └→ Toolsmith → Merger → Summary
```

### **Autonomous Healing Workflow**
```
Error Detection → QualityEnforcer → LLM Analysis (GPT-5)
    ↓                                      ↓
Telemetry Log                    Fix Generation
    ↓                                      ↓
Learning Store ←─ Success ← Test Verify → Apply/Rollback
```

### **Spec-Driven Development Flow**
```
Feature Request → Planner (creates spec.md)
    ↓
Spec Approval → Planner (creates plan.md)
    ↓
Plan Approval → TodoWrite (task breakdown)
    ↓
AgencyCodeAgent (implementation) → TestGenerator → QualityEnforcer
    ↓
MergerAgent → Git commit/PR
```

---

## **🤖 Claude Agent SDK Integration**

Per **ADR-006**, Agency integrates Claude Agent SDK for enhanced capabilities.

### **When to Use SDK Patterns**
- **Custom Tools**: Use `@tool` decorator + `create_sdk_mcp_server()`
- **Session Continuity**: `ClaudeSDKClient` for multi-turn conversations
- **One-off Tasks**: `query()` function for independent operations
- **Streaming**: Both support async streaming input/output

### **SDK Quick Patterns**
```python
# Custom tool creation
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("analyze", "Analyze code quality", {"path": str})
async def analyze(args):
    result = perform_analysis(args["path"])
    return {"content": [{"type": "text", "text": result}]}

server = create_sdk_mcp_server("agency_tools", tools=[analyze])

# Use with options
from claude_agent_sdk import ClaudeAgentOptions
options = ClaudeAgentOptions(
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__analyze"],
    permission_mode='acceptEdits'
)
```

### **Integration Points**
- **`tools/anthropic_agent.py`** - SDK wrapper implementations
- **`shared/agent_context.py`** - Context management for SDK agents
- **`docs/reference/claude-agent-sdk-python.md`** - Full SDK API reference

---

## **💾 Anthropic Memory Tool Integration**

Agency integrates Anthropic's **Memory Tool** (beta) for persistent cross-conversation memory.

### **Key Features**
- **File-based storage** in `~/.agency/memories/{session_id}/`
- **Cross-conversation persistence** without context window bloat
- **Security-hardened** with path traversal prevention
- **Session isolation** for independent memory spaces
- **6 memory commands**: view, create, str_replace, insert, delete, rename

### **Quick Start**
```python
# Enable in AgentContext
from shared.agent_context import create_agent_context

context = create_agent_context(session_id="my_task")
context.enable_anthropic_memory()

# Use memory tool
tool = context.get_anthropic_memory_tool()
tool.create("/memories/project.txt", "Agency OS features...")
tool.view("/memories/project.txt")
tool.str_replace("/memories/project.txt", "features", "capabilities")
```

### **SDK Integration**
```python
# Create Claude client with memory
from tools.anthropic_agent_with_memory import create_client_with_memory, run_with_memory

client, memory_tool = create_client_with_memory(session_id="conversation_1")

# Run conversation with memory enabled
response = run_with_memory(
    client=client,
    memory_tool=memory_tool,
    messages=[{"role": "user", "content": "Remember: I prefer Python"}],
    model="claude-sonnet-4-5"
)
```

### **Implementation Files**
- **`tools/anthropic_memory_tool.py`** - Core memory tool with security validation
- **`tools/anthropic_agent_with_memory.py`** - SDK integration helpers
- **`tests/test_anthropic_memory_security.py`** - 30 security tests (100% pass)
- **`scripts/test_anthropic_memory_beta.py`** - Beta access validation
- **`demo_anthropic_memory.py`** - Full demo with 3 scenarios

### **Requirements**
- **anthropic>=0.42.0** (in requirements.txt)
- **Beta header**: `context-management-2025-06-27`
- **Supported models**: Claude Sonnet 4.5, Opus 4.1

---

## **IV. The Constitution: Unbreakable Laws**

These directives are absolute. Adhere to them without exception.

1. **TDD is Mandatory:** Write tests *before* implementation. Use `bun run test` (frontend) and `uv run pytest` (backend).
2. **Strict Typing Always:** TypeScript's strict mode is always on. For Python, **never** use `Dict[Any, Any]`; use a concrete Pydantic model with typed fields. Avoid `any`.
3. **Validate All Inputs:** Public API inputs **must** be validated using Zod schemas (TypeScript) or Pydantic (Python).
4. **Use Repository Pattern:** All database queries **must** go through the repository layer.
5. **Embrace Functional Error Handling:** Use the `Result<T, E>` pattern. Avoid `try/catch` for control flow.
6. **Standardize API Responses:** All API responses must follow the established project format.
7. **Clarity Over Cleverness:** Write simple, readable code.
8. **Focused Functions:** Keep functions under 50 lines. One function, one purpose.
9. **Document Public APIs:** Use clear JSDoc/docstrings for public-facing APIs.
10. **Lint Before Commit:** Run `bun run lint` to fix style issues.

---

## **V. Operational Blueprint**

### **Agent Architecture**
- **Core Logic:** 10 specialized agents (listed in Codebase Map above) perform focused, singular tasks
- **Shared Context:** All agents share `AgentContext` for memory, learning, and coordination
- **Model Policy:** Per-agent model selection via `shared/model_policy.py` with environment overrides

### **Spec-Driven Development**
- **Complex tasks** are defined in `specs/` (formal specifications) and `plans/` (technical plans) before coding begins
- **Simple tasks** (1-2 steps) bypass spec-kit for efficiency, but still verify constitutional compliance

### **File Structure** (Key Directories)
```
/agency_code_agent/         Primary dev agent
/planner_agent/             Strategic planning
/auditor_agent/             Quality analysis
/quality_enforcer_agent/    Constitutional compliance
/chief_architect_agent/     ADR creation
/tools/                     35+ tools
/shared/                    Type definitions, models, context
/agency_memory/             VectorStore, learning
/specs/                     Formal specifications
/plans/                     Technical plans
/docs/adr/                  Architecture decisions
/.claude/commands/          Prime commands
/.claude/agents/            Agent definitions
```

### **Further Intel**
- Detailed command/agent definitions are in `.claude/commands/` and `.claude/agents/`
- ADR index at `docs/adr/ADR-INDEX.md`
- Full constitution at `constitution.md`

---

## **⚙️ Configuration Quick Start**

### **Essential Environment Variables**
```bash
# Core
OPENAI_API_KEY=<your_key>
AGENCY_MODEL=gpt-5                    # Global default

# Per-Agent Overrides (Optional)
PLANNER_MODEL=gpt-5                   # Strategic planning
CODER_MODEL=gpt-5                     # Implementation
AUDITOR_MODEL=gpt-5                   # Quality analysis
QUALITY_ENFORCER_MODEL=gpt-5          # Constitutional compliance
SUMMARY_MODEL=gpt-5-mini              # Cost-efficient summaries

# Memory & Learning (MANDATORY - Article IV)
USE_ENHANCED_MEMORY=true              # REQUIRED: VectorStore integration (constitutional mandate)
FRESH_USE_FIRESTORE=false             # Optional Firestore backend

# Testing
FORCE_RUN_ALL_TESTS=1                 # Full test suite (1,562 tests)
```

### **Running Commands**
```bash
# Main orchestration
python agency.py run                  # Interactive demo
python agency.py health               # System health check

# Testing (MUST be 100% pass rate)
python run_tests.py --run-all         # Full validation (1,562 tests)
python run_tests.py                   # Unit tests only
python run_tests.py --integration-only

# Demos
python demo_unified.py                # Core capabilities
python demo_autonomous_healing.py     # Self-healing demo
```

### **Development Setup**
```bash
# Clone and initialize
git clone <repository-url>
cd Agency

# Environment setup
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Verify constitutional compliance
python run_tests.py --run-all         # Must show 100% pass rate
```

---

## **📊 Production Metrics**

- **1,725+ tests** passing with 100% success rate (163 new constitutional compliance tests)
- **Zero test failures** under constitutional enforcement
- **<3 seconds** for constitutional test suite validation
- **139 test files** total across codebase
- **>95% healing success rate** for autonomous fixes
- **100% constitutional compliance** across all agents (Articles I-V)
- **36 production tools** with security hardening (bash.py, git.py validated)

---

## **🚨 Critical Reminders**

1. **ALWAYS** start with a `/prime` command (Prime-First Mandate)
2. **ALWAYS** read `constitution.md` before planning or implementation
3. **NEVER** use `Dict[Any, Any]` - use Pydantic models with typed fields
4. **NEVER** proceed with incomplete context (retry timeouts 2x, 3x, 10x)
5. **NEVER** merge without 100% test success (no exceptions)
6. **ALWAYS** write tests BEFORE implementation (TDD is mandatory)
7. **ALWAYS** validate against all 5 constitutional articles before action

---

*"In automation we trust, in discipline we excel, in learning we evolve."*

**Version 1.1.1** - Mars Rover Bulletproofing & Production Ready
**Last Updated**: 2025-10-07