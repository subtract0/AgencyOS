# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Agency
```bash
sudo python agency.py  # Terminal demo - requires sudo on macOS for filesystem access
```

### Testing
```bash
python run_tests.py                          # Run all tests with installation
python -m pytest tests/ -v                   # Direct pytest execution
python run_tests.py test_specific_file.py    # Run specific test file
python tests/run_memory_tests.py            # Run memory system tests
```

### Code Quality
```bash
ruff check . --fix      # Fix linting issues and sort imports
ruff format .           # Format code
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

### Multi-Agent System
The Agency implements a sophisticated multi-agent architecture using the Agency Swarm framework:

**Core Agents:**
- **AgencyCodeAgent** (`agency_code_agent/`): Primary developer agent with 14 Claude Code tools for file operations, search, and system commands
- **PlannerAgent** (`planner_agent/`): Strategic planning specialist that breaks down complex tasks
- **AuditorAgent** (`auditor_agent/`): CodeHealer integration analyzing test quality using NECESSARY pattern
- **TestGeneratorAgent** (`test_generator_agent/`): Creates NECESSARY-compliant tests from audit reports

**Communication Flow:**
```
Coder ↔ Planner (bidirectional handoff)
Planner → Auditor (task delegation)
Auditor → TestGenerator (quality improvement)
TestGenerator → Coder (implementation)
```

### Memory System
All agents share a unified memory system via `AgentContext`:
- **In-memory store** (default): Session-based memory
- **Firestore backend** (optional): Set `FRESH_USE_FIRESTORE=true` for persistence
- **Session tracking**: Automatic transcript generation in `logs/sessions/`
- **Learning consolidation**: Pattern analysis from memory usage

### Tool System
Central tools in `tools/` directory:
- File operations: `read.py`, `write.py`, `edit.py`, `multi_edit.py`
- Search: `grep.py`, `glob.py`, `ls.py`
- Version control: `git.py`
- System: `bash.py`, `todo_write.py`
- Specialized: `notebook_edit.py`, `notebook_read.py`, `claude_web_search.py`

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
├── agent_name.py        # Agent class definition
├── instructions.md      # Claude instructions
├── instructions-gpt-5.md # GPT-5 specific (if different)
└── tools/              # Agent-specific tools (optional)
```

### Testing Patterns
- Test files: `test_*.py` in `tests/` directory
- Async tests: Use `@pytest.mark.asyncio` decorator
- Fixtures: Centralized in `tests/conftest.py`
- Integration tests: `test_tool_integration.py` for workflow testing

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

## Important Notes

- Model selection in `agency.py`: Currently set to `gpt-5` with high reasoning effort
- Shared instructions: Referenced via `project-overview.md` in agency initialization
- Environment variables: API keys in `.env` file
- Pre-commit hooks: Automatically run ruff checks on commit
- Subagent creation: Use template in `subagent_example/` or prompt Claude Code to create new agents