# Repository Guidelines

## CodeHealer Agents

### AuditorAgent
- **Purpose**: Analyzes codebases for test quality using NECESSARY pattern
- **Location**: `auditor_agent/`
- **Q(T) Score**: Calculates test quality metric: `Q(T) = Π(p_i) × (|B_c| / |B|)`
- **NECESSARY Properties**: Evaluates 9 universal test quality properties (N-E-C-E-S-S-A-R-Y)
- **Memory Integration**: Stores audit reports and violation patterns for learning
- **Output**: Structured JSON reports with violations and recommendations

### TestGeneratorAgent
- **Purpose**: Generates NECESSARY-compliant tests based on audit reports
- **Location**: `test_generator_agent/`
- **Strategy**: Property-specific test generation templates for each violation type
- **Prioritization**: Focuses on high-impact violations first
- **Memory Integration**: Learns from generated test patterns and success rates
- **Output**: Test files that maximize Q(T) score improvements

### ToolSmithAgent
- **Purpose**: Meta-agent craftsman that scaffolds, implements, tests, and hands off new tools
- **Location**: `toolsmith_agent/`
- **Capabilities**: Parses tool directives, scaffolds BaseTool + Pydantic patterns, generates tests
- **Integration**: Updates `tools/__init__.py` exports additively and idempotently
- **Quality Gates**: Runs pytest and aborts on failures (Constitutional Article II compliance)
- **Handoff Pattern**: Delivers green artifacts to MergerAgent for verification and integration
- **Learning**: Stores successful/failed scaffolding patterns in memory for improvement
- **Communication Flow**: ChiefArchitectAgent → ToolSmithAgent → MergerAgent

## Project Structure & Module Organization
- `agency.py` wires all 8 agents (planner, developer, auditor, test generator, toolsmith, etc.) and loads settings from `.env`.
- `agency_code_agent/` contains the primary agent, prompts, and its `tools/`; extend or reuse logic here.
- `planner_agent/` mirrors the coder setup for planning mode; keep configs aligned when features move between agents.
- `auditor_agent/` analyzes codebases using NECESSARY pattern and calculates Q(T) scores for test quality.
- `test_generator_agent/` generates NECESSARY-compliant tests based on audit reports to improve quality.
- `toolsmith_agent/` meta-agent for dynamic tool creation, scaffolding, and integration into the agency.
- `chief_architect_agent/` strategic oversight agent with self-directed task creation and system optimization.
- `learning_agent/` analyzes session transcripts and consolidates patterns into institutional memory.
- `merger_agent/` handles integration, pull request management, and final verification of changes.
- `work_completion_summary_agent/` provides concise audio summaries and suggests next steps.
- `tests/` holds pytest coverage for tools, agents, and integration flows; follow its layout for new scenarios.
- `subagent_template/` scaffolds new agents, while shared adapters sit in `tools/` and `agents/` for reuse.

## Build, Test, and Development Commands
- `python3.13 -m venv .venv && source .venv/bin/activate` prepares the supported runtime.
- `python -m pip install -r requirements.txt` installs Agency Swarm plus test dependencies.
- `sudo python agency.py` launches the interactive terminal demo (sudo required on macOS for filesystem access).
- `python run_tests.py` bootstraps dependencies if missing and runs the full pytest suite with project defaults.
- `pytest tests/test_tool_integration.py -k handoff` narrows execution when iterating on a flow.
- `pre-commit run --all-files` invokes Ruff import sorting and formatting before commits.

## Coding Style & Naming Conventions
- Use 4-space indentation, targeted type hints, and docstrings on public agent or tool factories.
- Files remain snake_case, classes PascalCase, and instruction templates stay under `agency_code_agent/`.
- Ruff owns linting and formatting (`ruff check . --fix`, `ruff format .`); expose `create_*` factories for new agents, hooks, or tools.

## Testing Guidelines
- Pytest with `pytest-asyncio` powers the suite; new files follow `test_<area>.py` and mark async cases with `@pytest.mark.asyncio`.
- Reuse fixtures from `tests/conftest.py`, and extend `tests/test_tool_integration.py` for orchestration coverage.
- Exercise both success and failure paths for any tool or planner change, and add regression tests when fixing bugs.

## Commit & Pull Request Guidelines
- Keep commit titles short and descriptive (e.g., `Enable reasoning effort for anthropic models`), using the imperative mood where possible.
- Group related edits, call out instruction or template updates in the PR description, and list the verification commands you ran.
- Reference issues or tasks and include terminal output or screenshots when UX or agent behaviour changes.

## Memory Integration & Agent Context
- Agents now share a unified memory system through `shared.agent_context` that enables cross-session learning.
- Memory flows through the complete agent lifecycle: initialization → tool execution → response generation → memory consolidation.
- The `create_agent_context(memory=shared_memory)` pattern injects memory capabilities into both planner and developer agents.
- Memory operations use a verbose fallback policy: warnings are logged but execution continues if memory storage fails.
- Session transcripts are automatically generated and stored in `logs/sessions/` for learning analysis and debugging.
- Memory stores support tagging and search functionality for efficient retrieval of relevant context.

## Configuration & Secrets
- Store provider keys and model overrides in `.env`; `dotenv` loads them in `agency.py`, so never commit secrets.
- Memory configuration: Set `FRESH_USE_FIRESTORE=true` for persistent Firestore backend or leave unset for in-memory default.
- For local development with Firestore emulator, set `FIRESTORE_EMULATOR_HOST=localhost:8080`.
- Document new environment variables in `README.md`, and update both agent factories when introducing models or reasoning modes.
