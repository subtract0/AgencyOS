# Agency Code

Agency Code is a local, testable coding agent built with Agency Swarm that behaves like a focused “Claude Code”-style developer inside your repo. It provides a set of tools (LS, Read, Grep, Glob, Edit, MultiEdit, Write, NotebookRead/Edit, Bash, TodoWrite, etc.) and an agent orchestration layer so you can iterate on code with safety and strong tests.

## What it does

- Answers and executes developer tasks inside your repository using first-class tools instead of brittle shell parsing.
- Enforces a disciplined workflow: read → change → test → commit. Tests live in `tests/` and cover tools and agent behaviors.
- Runs entirely on your machine; no remote writes unless you explicitly push.

## Key features

- Agency Swarm agents: a primary “Developer” and an optional “Planner” for complex tasks.
- Comprehensive toolbelt:
  - Files: `LS`, `Read`, `Write`, `Edit`, `MultiEdit`, `Glob`, `Grep`.
  - Notebooks: `NotebookRead`, `NotebookEdit`.
  - Process: `Bash` (macOS sandboxed writes to CWD and /tmp), `TodoWrite`/`TodoComplete`.
- Tests-first workflow with `pytest` and a convenience runner `python run_tests.py`.

## Quick start

1) Install deps:

```
python -m pip install -r requirements.txt
```

2) Run tests:

```
pytest -q
```

3) Try the agency (terminal demo):

```
python agency.py
```

## Development conventions

- Prefer editing existing files; avoid generating docs unless requested.
- Use absolute paths with tools; don’t shell out to `cat`/`grep`/`find` when `Read`/`Grep`/`Glob` exist.
- Keep changes minimal; run tests and pre-commit before committing:

```
pre-commit run --all-files
pytest -q
```

## Security & sandboxing

- On macOS, `Bash` executes under `sandbox-exec` with file writes allowed only in the current working directory and `/tmp` (`/private/tmp`).
- The agent does not push to remotes unless you ask it to.

## Structure

```
agency.py                         # agency entrypoint
agency_code_agent/                # developer agent and tools
planner_agent/                    # optional planner agent
tests/                            # tool and agent tests
run_tests.py                      # convenience test runner
```

## Inspired by Claude Code

This project mirrors the “code-first, tool-driven” agent pattern popularized by Claude Code: fast, local feedback loops; structured tools instead of free-form shell; and strong test coverage to keep edits safe and incremental.
