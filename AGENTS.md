# Repository Guidelines

## Project Structure & Module Organization
- `agency.py` wires planner and developer agents and loads settings from `.env`.
- `agency_code_agent/` contains the primary agent, prompts, and its `tools/`; extend or reuse logic here.
- `planner_agent/` mirrors the coder setup for planning mode; keep configs aligned when features move between agents.
- `tests/` holds pytest coverage for tools, planner, and integration flows; follow its layout for new scenarios.
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

## Configuration & Secrets
- Store provider keys and model overrides in `.env`; `dotenv` loads them in `agency.py`, so never commit secrets.
- Document new environment variables in `README.md`, and update both agent factories when introducing models or reasoning modes.
