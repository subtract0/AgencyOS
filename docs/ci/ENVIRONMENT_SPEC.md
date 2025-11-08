# Environment Specification Integration (Phase 2)

**Status**: ✅ CI Coverage Complete (Phase 2.1 of OpenEnv adoption)
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
│  ├─ 18 CI shards (unit, integration, misc, manual) │
│  │  ├─ Step 1: Reset env (python runner.py reset)  │
│  │  ├─ Step 2: Run tests via scripts/run_in_env.py │
│  │  └─ Step 3: Upload logs (JSON + reset traces)   │
│  └─ Agent scripts (run_tests.py, future tooling)    │
│     └─ Call env runner API directly                 │
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
        set -o pipefail
        mkdir -p test-results
        export AGENCY_ENV_SPEC=${{ github.workspace }}/envs/agency_env_spec.json
        python envs/agency_env_runner.py reset > test-results/runner-reset.log 2>&1
        echo "✅ Environment reset complete"

    # Step 2: Run tests via scripts/run_in_env.py (step API)
    - name: "Run orchestrator tests"
      run: |
        set -o pipefail
        export PYTHONPATH=${{ github.workspace }}
        export USE_ENHANCED_MEMORY=true
        export AGENCY_TEST_TIMEOUT_OVERRIDE=300
        export AGENCY_ENV_SPEC=${{ github.workspace }}/envs/agency_env_spec.json
        mkdir -p test-results
        python scripts/run_in_env.py \
          --timeout 900 \
          --log-file test-results/runner-step.json \
          --env PYTHONMALLOC=malloc \
          -- pytest tests/orchestrator \
            --ignore=tests/test_firestore_learning_persistence.py \
            --ignore=tests/test_firestore_mock_integration.py \
            --ignore=tests/e2e \
            --ignore=tests/benchmarks \
            -m "not slow" --ff --maxfail=1 -q \
            --json-report --json-report-file=test-results/report.json

    # Step 3: Upload logs (runner reset + step JSON + reports)
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

### Shared helper: `envs/openenv_exec.py`

- Provides `run_command()` which prefers the runner but gracefully falls back to `subprocess.run` when shell pipelines/stdin are involved.
- Streams stdout/stderr unless `capture_output=True`, mirroring native subprocess behavior.
- Ensures every automation tool inherits the same logging + timeout semantics with zero duplication.

### `run_tests.py` (local + CI helper)

- Now imports `run_command` from `envs/openenv_exec.py` so it matches every other script.
- When `AGENCY_ENV_SPEC` is set (default when repo is present), commands go through the runner; otherwise it falls back transparently.
- Preserves `capture_output`, `check`, and `TimeoutExpired` semantics automatically.

```python
from envs.agency_env_runner import step as env_step

def run_command(cmd: list[str], **kwargs):
    if not os.getenv("AGENCY_ENV_SPEC"):
        return subprocess.run(cmd, **kwargs)

    action = {"command": cmd, "timeout": kwargs.get("timeout", 600)}
    result = env_step(action)
    if result["status"] == "timeout":
        raise subprocess.TimeoutExpired(cmd, action["timeout"])
    if result.get("exit_code", 0) != 0 and kwargs.get("check"):
        raise subprocess.CalledProcessError(result["exit_code"], cmd)
    return subprocess.CompletedProcess(cmd, result.get("exit_code", 0), result.get("stdout"), result.get("stderr"))
```

### Phase 2.2 Status / Targets

- ✅ `scripts/overnight_worker.py` now routes its git + pytest calls through `envs/openenv_exec.run_command`.
- ✅ `scripts/autonomous_worker.py` commits use the helper (worktree git actions logged via runner).
- ✅ `scripts/worktree_manager.py` wraps add/remove/prune commands via the helper.
- ✅ `scripts/ci_failure_parser.py` runs all `gh` calls through the helper for logging/audit.

Each remaining script should import the helper rather than re-creating subprocess glue; shell-heavy commands will continue to fall back until sandboxing is enforced.

### Sandbox Toggle (macOS sandbox-exec)

**Profile Location**: `envs/sandbox_profile.sb`

The sandbox profile provides a restrictive execution environment for test commands, enforcing:

- **Read-only access**: Repository and Python stdlib (including venv)
- **Limited write access**: Only `/tmp`, `/var/tmp`, `~/Library/Logs/AgencyOS`, `~/Library/Caches/AgencyOS`, and pytest artifacts
- **Loopback networking**: Required for pytest-rerunfailures and test coordination
- **Process isolation**: Prevents unauthorized file system modifications during testing

#### Enabling the Sandbox

Set the environment variable to enable sandboxing for all runner commands:

```bash
export AGENCY_SANDBOX_PROFILE=envs/sandbox_profile.sb
```

The runner automatically wraps commands with `sandbox-exec -f <profile>` when this variable is set.

#### Testing with Sandbox Enabled

Run smoke tests to verify sandbox compatibility:

```bash
# Activate venv first
source venv/bin/activate

# Run smoke tests with sandbox enabled
RUN_TESTS_USE_UV=0 \
AGENCY_SANDBOX_PROFILE=envs/sandbox_profile.sb \
./run_tests.py --fast --pytest-args "-k smoke"
```

Expected behavior:
- Tests should pass with sandbox restrictions in place
- Unauthorized write attempts will fail gracefully
- Loopback network operations (pytest plugins) function normally

#### Customizing the Sandbox Profile

The profile follows Apple sandbox-exec grammar (see `/usr/share/sandbox/` for examples). Key sections:

- `(allow file-read* ...)`: Read-only access rules
- `(allow file-write* ...)`: Write access rules (restricted)
- `(allow network-bind ...)`: Network permissions (loopback only)
- `(allow process-exec ...)`: Executable allowlist

To customize, edit `envs/sandbox_profile.sb` with additional rules as needed.

#### Disabling Sandbox Enforcement (--no-sandbox flag)

For debugging or local development scenarios where sandbox restrictions interfere with normal operation, you can bypass sandbox enforcement using the `--no-sandbox` flag:

```bash
# Run tests without sandbox enforcement (local development)
./run_tests.py --run-all --no-sandbox

# Generate test reports without sandbox restrictions
./run_tests.py --run-all --no-sandbox --json-report --json-report-file=test-results/full-suite.json
```

**When to use `--no-sandbox`:**
- Local development and debugging workflows
- Generating authoritative test artifacts for documentation
- Environments where `AGENCY_SANDBOX_PROFILE` is set but sandbox restrictions are incompatible
- Verifying baseline test behavior without isolation constraints

**Effect:**
- Overrides `AGENCY_SANDBOX_PROFILE` environment variable
- Runner executes commands directly without `sandbox-exec` wrapper
- All other runner functionality (logging, timeout enforcement, JSON output) remains active
- Explicitly sets `sandbox_disabled=True` flag in runner configuration

**Note:** This flag is intended for local use only. CI environments should maintain sandbox enforcement for reproducibility and security.

#### Integration with CI

- `envs/agency_env_spec.json` now includes a `sandbox.profile` entry so the runner can find the profile automatically.
- Set `AGENCY_SANDBOX_PROFILE=envs/sandbox_profile.sb` (or overwrite with your own path) to force all commands through `sandbox-exec -f <profile>`.
- If the profile is missing, the runner prints a warning and falls back to normal execution.
- Future CI integration will enable sandboxing by default for all shards.

### Dockerized Runner (optional)

- `docker/openenv-runner.Dockerfile` builds a Python:3.12-based image with project deps preinstalled.
- `scripts/run_in_docker.sh` builds/runs the image on first use and mounts the current workspace at `/workspace`.
- Usage example:
  ```bash
  ./scripts/run_in_docker.sh pytest tests/test_kanban_smoke.py -q
  ```
- The script sets `AGENCY_ENV_SPEC` automatically so commands still flow through the runner inside the container.

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
3. **Partial wrapping**: `run_tests.py` now routes through runner; other automation scripts still pending (Phase 2.2)
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

### Split Integration Test Suite

**Problem**: The full integration suite (`./run_tests.py --integration-only`) runs 134 tests which can cause macOS to kill the process with signal 9 due to resource exhaustion on long runs.

**Solution**: Split into two balanced parts that can run independently:

```bash
# Part 1: Heavier integration tests (~58 tests)
RUN_TESTS_USE_UV=0 ./run_tests.py --integration-part1

# Part 2: Lighter integration tests (~76 tests)
RUN_TESTS_USE_UV=0 ./run_tests.py --integration-part2
```

**Test Distribution**:

- **Part 1** (58 tests): Larger test files with heavier resource usage
  - `test_non_blocking_cleanup.py` (24 tests)
  - `test_ci_backlog_workflow.py` (18 tests)
  - `test_unit_integration_separation.py` (16 tests)

- **Part 2** (76 tests): Smaller test files with lighter resource usage
  - `test_mock_asyncio_sleep.py` (16 tests)
  - `test_remove_intentional_delays.py` (14 tests)
  - `test_function_timeouts.py` (12 tests)
  - `test_performance_regression.py` (10 tests)
  - `test_ambient_to_witness.py` (7 tests)
  - `test_autonomous_audit_loop.py` (7 tests)
  - `test_epic4_2_complete.py` (6 tests)
  - `test_memory_aware_integration.py` (4 tests)

**Usage in CI**:

```yaml
# CI shard for integration-part1
- name: "Run integration tests part 1"
  run: RUN_TESTS_USE_UV=0 ./run_tests.py --integration-part1

# CI shard for integration-part2
- name: "Run integration tests part 2"
  run: RUN_TESTS_USE_UV=0 ./run_tests.py --integration-part2
```

**Benefits**:
- Prevents macOS signal 9 kills from resource exhaustion
- Enables parallel execution of integration suite
- Maintains full coverage (part1 + part2 = complete integration suite)

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
