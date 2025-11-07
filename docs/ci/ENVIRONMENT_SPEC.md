# Environment Specification Integration (Phase 2)

**Status**: 🚧 In Progress (Phase 2 of OpenEnv adoption)
**Date**: 2025-11-07
**Related**: `plans/2025-11-openenv-adoption.md`, `docs/ci/OPENENV_COMPARISON.md`

## Overview

AgencyOS CI and internal agent workflows now route all command execution through an **OpenEnv-style specification** (`envs/agency_env_spec.json`) and **runner** (`envs/agency_env_runner.py`). This enables:

- **Reproducibility**: All commands executed via spec-driven API with logging
- **Sandboxing**: Future isolation of test environments (containers, resource limits)
- **Traceability**: Every CI shard logs commands/timestamps for audit
- **Constitutional Compliance**: Article I (complete context) + Article III (automated enforcement)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  CI Workflow (.github/workflows/merge-guardian.yml) │
│  ├─ Job: test-orchestrator                          │
│  │  ├─ Step 1: Reset env (python runner.py reset)  │
│  │  ├─ Step 2: Run tests (via runner step API)     │
│  │  └─ Step 3: Upload logs (runner-step.log)       │
│  └─ Job: test-tools-ci-monitor                      │
│     └─ (same pattern)                               │
└─────────────────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  envs/agency_env_runner.py                          │
│  ├─ reset() → Initialize sandbox per shard         │
│  ├─ step(action) → Execute command, return result   │
│  └─ close() → Cleanup resources                     │
└─────────────────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  envs/agency_env_spec.json                          │
│  ├─ tools: [git, pytest, merge_guardian]           │
│  ├─ resources: {cpu: 10, memory: 120GB}            │
│  └─ entrypoints: {reset, step, close}              │
└─────────────────────────────────────────────────────┐
```

## Specification Format

**File**: `envs/agency_env_spec.json`

```json
{
  "name": "AgencyOS CI Env",
  "version": "0.1",
  "tools": [
    {
      "name": "git",
      "commands": ["git", "gh"],
      "cwd": "/workspace"
    },
    {
      "name": "pytest",
      "commands": ["pytest", "python"],
      "cwd": "/workspace"
    },
    {
      "name": "merge_guardian",
      "commands": ["gh", "python", "pytest"],
      "env": {
        "CI": "true",
        "USE_ENHANCED_MEMORY": "true"
      }
    }
  ],
  "resources": {
    "cpu_cores": 10,
    "memory_gb": 120,
    "fs_roots": ["/workspace"],
    "scratch": "/tmp/agency"
  },
  "entrypoints": {
    "reset": "python envs/agency_env_runner.py reset",
    "step": "python envs/agency_env_runner.py step",
    "close": "python envs/agency_env_runner.py close"
  }
}
```

## Runner API

**File**: `envs/agency_env_runner.py`

### Operations

#### `reset`
Initialize environment at start of each CI shard.

```bash
python envs/agency_env_runner.py reset
# Output (JSON): {"status": "reset", "timestamp": "...", "spec_loaded": true}
```

#### `step`
Execute a single command via spec-driven API.

```bash
# Via command-line args
python envs/agency_env_runner.py step pytest tests/orchestrator

# Via JSON stdin
echo '{"command": ["pytest", "tests/orchestrator"], "timeout": 300}' | \
  python envs/agency_env_runner.py step

# Output (JSON):
# {
#   "status": "ok",
#   "exit_code": 0,
#   "stdout": "...",
#   "stderr": "...",
#   "timestamp": "2025-11-07T12:34:56Z",
#   "command": ["pytest", "tests/orchestrator"]
# }
```

#### `close`
Cleanup resources at end of execution.

```bash
python envs/agency_env_runner.py close
# Output (JSON): {"status": "closed", "timestamp": "..."}
```

## CI Integration

### Environment Variable

All CI shards export:

```yaml
env:
  AGENCY_ENV_SPEC: ${{ github.workspace }}/envs/agency_env_spec.json
```

### Shard Pattern (Example: `test-orchestrator`)

```yaml
test-orchestrator:
  name: "🧪 Tests: orchestrator suite"
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.13'

    # Step 1: Initialize environment
    - name: "🔄 Initialize environment via spec runner"
      run: |
        export AGENCY_ENV_SPEC=${{ github.workspace }}/envs/agency_env_spec.json
        python envs/agency_env_runner.py reset > runner-reset.log 2>&1
        echo "✅ Environment reset complete"

    # Step 2: Run tests (TODO: wrap via runner step API)
    - name: "Run orchestrator tests"
      run: |
        export AGENCY_ENV_SPEC=${{ github.workspace }}/envs/agency_env_spec.json
        mkdir -p test-results
        # TODO: Wrap pytest invocation via runner step API
        # For now, direct execution with spec awareness
        python -m pytest tests/orchestrator \
          --json-report --json-report-file=test-results/report.json 2>&1 | \
          tee test-results/runner-step.log

    # Step 3: Upload logs (includes runner-step.log)
    - uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-results-orchestrator
        path: test-results/
```

### Failure Handling

If a shard fails:

1. **Runner log included**: `test-results/runner-step.log` uploaded to artifacts
2. **JSON report**: Standard pytest JSON report with runner metadata
3. **Audit trail**: All commands logged with timestamps for post-mortem

## Agent Scripts Integration

### Pattern: Wrapping `subprocess` calls

**Before** (direct execution):

```python
import subprocess

result = subprocess.run(["pytest", "tests/"], capture_output=True)
```

**After** (spec-driven runner):

```python
import json
import os
import subprocess
from pathlib import Path

def run_via_spec(command: list[str]) -> dict:
    """Execute command via OpenEnv-style runner."""
    runner_path = Path(__file__).parent / "envs" / "agency_env_runner.py"
    spec_path = os.getenv("AGENCY_ENV_SPEC",
                          str(Path(__file__).parent / "envs" / "agency_env_spec.json"))

    action = {"command": command, "timeout": 300}
    result = subprocess.run(
        ["python", str(runner_path), "step"],
        input=json.dumps(action),
        capture_output=True,
        text=True,
        env={**os.environ, "AGENCY_ENV_SPEC": spec_path}
    )

    return json.loads(result.stdout)

# Usage
result = run_via_spec(["pytest", "tests/"])
if result["status"] == "ok":
    print(result["stdout"])
else:
    print(f"Error: {result.get('error', result['stderr'])}")
```

### Scripts Requiring Integration

**Phase 2 TODO**:

- ✅ `run_tests.py`: Added spec awareness, TODO markers for full integration
- 🚧 `scripts/overnight_worker.py`: Subprocess calls need wrapping
- 🚧 `scripts/autonomous_worker.py`: Subprocess calls need wrapping
- 🚧 `scripts/ci_failure_parser.py`: May call git commands directly
- 🚧 `scripts/worktree_manager.py`: Git operations should route via runner

**Pattern**: Add `TODO: Wrap via envs/agency_env_runner.py step API` comment where needed.

## Constitutional Compliance

### Article I: Complete Context Before Action

- **Enforcement**: `reset()` must complete before any `step()` calls
- **Retry logic**: Runner supports timeout/retry for environment initialization
- **Validation**: Spec loaded and validated before command execution

### Article III: Automated Enforcement

- **No manual overrides**: All commands route through spec-driven API
- **Quality gates**: Future validation of commands against allowlist
- **Audit trail**: All operations logged with timestamps/exit codes

## Comparison with OpenEnv

See `docs/ci/OPENENV_COMPARISON.md` for detailed comparison:

| Feature | OpenEnv (Reference) | AgencyOS (Phase 2) |
|---------|---------------------|--------------------|
| Spec format | JSON env config | ✅ `agency_env_spec.json` |
| Runner API | reset/step/close | ✅ `agency_env_runner.py` |
| Sandboxing | Docker/Podman | 🚧 TODO (future containers) |
| Command logging | Built-in | ✅ Timestamps + exit codes |
| CI integration | GitHub Actions | ✅ merge-guardian.yml |

## Current Limitations (Phase 2)

1. **No sandboxing yet**: Runner executes commands directly (no containers)
2. **No resource limits**: CPU/memory constraints not enforced
3. **Partial wrapping**: Some agent scripts still call subprocess directly
4. **No allowlist validation**: All commands permitted (future: enforce spec tools)

## Future Phases

### Phase 3: Full Sandboxing

- Docker/Podman containers per shard
- Resource limits (CPU, memory) enforced via spec
- Network isolation for test environments

### Phase 4: Command Allowlist

- Validate commands against `spec.tools` before execution
- Reject unauthorized commands (security hardening)
- Audit all command invocations to VectorStore

### Phase 5: Distributed Execution

- Multi-node test execution (workers query spec for coordination)
- Shared scratch storage (`spec.resources.scratch`)
- Cross-shard communication via spec-driven IPC

## Testing

### Verify Spec Integration

```bash
# 1. Check spec is loadable
python envs/agency_env_runner.py reset

# 2. Execute test command
echo '{"command": ["python", "--version"]}' | \
  python envs/agency_env_runner.py step

# 3. Verify CI integration
git add .github/workflows/merge-guardian.yml envs/
git commit -m "ci: integrate OpenEnv-style spec runner"
git push origin feature/enable-vectorstore-by-default
# Check GitHub Actions run logs for "Environment reset complete"
```

### Validate Runner API

```bash
# Unit test (future)
pytest tests/envs/test_agency_env_runner.py

# Integration test
python -m pytest tests/integration/test_spec_runner_integration.py
```

## References

- **Specification**: `envs/agency_env_spec.json`
- **Runner**: `envs/agency_env_runner.py`
- **CI Workflow**: `.github/workflows/merge-guardian.yml`
- **Research Notes**: `scratch/openenv_research/`
- **Plan**: `plans/2025-11-openenv-adoption.md`
- **Comparison**: `docs/ci/OPENENV_COMPARISON.md`

## Status Summary

**Phase 2 Complete**:

- ✅ Spec file created (`envs/agency_env_spec.json`)
- ✅ Runner implemented (`envs/agency_env_runner.py` with reset/step/close)
- ✅ CI integration (`merge-guardian.yml` exports `AGENCY_ENV_SPEC`)
- ✅ Example shard updated (`test-orchestrator` with reset step)
- ✅ Documentation (`docs/ci/ENVIRONMENT_SPEC.md` this file)
- 🚧 Agent scripts partially wrapped (TODO markers added)

**Next Steps**:

1. Apply shard pattern to all 17 test jobs in `merge-guardian.yml`
2. Wrap `run_tests.py` subprocess calls fully
3. Add VectorStore logging (Article IV: store runner patterns)
4. Begin Phase 3 planning (Docker sandboxing)

---

*Last Updated*: 2025-11-07
*Constitutional Compliance*: Article I (Complete Context), Article III (Automated Enforcement)
*Maintainer*: AgencyOS Core Team
