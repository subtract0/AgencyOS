# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Agency
```bash
sudo python agency.py  # Terminal demo - requires sudo on macOS for filesystem access
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
```

### Code Quality
```bash
ruff check . --fix          # Fix linting issues and sort imports
ruff format .               # Format code
pre-commit run --all-files  # Run all pre-commit hooks
```

### Initial Setup
```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# Fix LiteLLM bug with Anthropic reasoning models:
python -m pip install git+https://github.com/openai/openai-agents-python.git@main
```

## Architecture Overview

### Multi-Agent System (7 Agents)
The Agency implements a sophisticated multi-agent architecture using the Agency Swarm framework:

**Core Agents:**
- **ChiefArchitectAgent** (`chief_architect_agent/`): Strategic oversight, reviews audits and VectorStore knowledge, creates self-directed tasks
- **AgencyCodeAgent** (`agency_code_agent/`): Primary developer agent with 16 tools for file operations, search, and system commands
- **PlannerAgent** (`planner_agent/`): Strategic planning using spec-kit methodology for formal specifications and plans
- **AuditorAgent** (`auditor_agent/`): CodeHealer integration analyzing test quality using NECESSARY pattern
- **TestGeneratorAgent** (`test_generator_agent/`): Creates NECESSARY-compliant tests from audit reports
- **LearningAgent** (`learning_agent/`): Analyzes session transcripts and consolidates patterns into institutional memory
- **MergerAgent** (`merger_agent/`): Handles integration and pull request management

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

### Memory System
All agents share a unified memory system via `AgentContext`:
- **In-memory store** (default): Session-based memory
- **Firestore backend** (optional): Set `FRESH_USE_FIRESTORE=true` for persistence
- **VectorStore**: Learning consolidation and similarity search for institutional knowledge
- **Session tracking**: Automatic transcript generation in `logs/sessions/`
- **Composite hooks**: MemoryIntegrationHook, SystemReminderHook, MessageFilterHook for lifecycle management
- **Learning triggers**: After successful sessions, error resolution, effective patterns, performance milestones

### Constitutional Governance
The Agency operates under strict constitutional principles (`constitution.md`):
- **Article I**: Complete Context Before Action - No action without full understanding
- **Article II**: 100% Verification - Main branch must maintain 100% test success rate
- **Article III**: Automated Enforcement - Quality standards technically enforced, no manual overrides
- **Article IV**: Continuous Learning - Automatic improvement through experiential learning
- **Article V**: Spec-Driven Development - All features require formal specs in `specs/` and plans in `plans/`

### Tool System
Central tools in `tools/` directory:
- File operations: `read.py`, `write.py`, `edit.py`, `multi_edit.py`
- Search: `grep.py`, `glob.py`, `ls.py`
- Version control: `git.py`
- System: `bash.py`, `todo_write.py`, `exit_plan_mode.py`
- Specialized: `notebook_edit.py`, `notebook_read.py`, `claude_web_search.py`, `feature_inventory.py`
- Model-specific: Tools auto-selected based on model type (OpenAI vs Claude vs Grok)

**Tool Security Patterns:**
- Path validation: All tools use absolute paths
- Permission handling: Graceful degradation for filesystem errors
- Background execution: Support for long-running commands with `run_in_background`
- Error resilience: Comprehensive error handling with fallback mechanisms

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

### Spec-Driven Development Process
1. Constitutional compliance check via `/constitution.md`
2. Formal specification generation in `/specs/` directory
3. Technical planning in `/plans/` directory
4. Task breakdown using TodoWrite tool with traceability
5. Implementation with continuous constitutional validation

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

## Important Notes

- Model selection in `agency.py`: Currently set to `gpt-5` with high reasoning effort
- Reasoning settings: Configurable effort levels (low/medium/high) and summary modes
- Context limit: 32K tokens with auto-truncation for memory operations
- Shared instructions: Referenced via `project-overview.md` in agency initialization
- Environment variables: `OPENAI_API_KEY`, `FRESH_USE_FIRESTORE`, Firebase credentials in `.env`
- Pre-commit hooks: Automatically run ruff checks and formatting on commit
- Subagent creation: Use template in `subagent_example/` or prompt Claude Code to create new agents