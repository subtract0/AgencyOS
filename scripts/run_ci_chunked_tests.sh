#!/usr/bin/env bash

# Run the AgencyOS test suite in memory-friendly chunks suitable for low-memory CI runners.
# Mirrors the filters used in merge-guardian but executes smaller batches sequentially to avoid OOM (exit 137).

set -euo pipefail
shopt -s nullglob

PYTEST_BIN=${PYTEST_BIN:-"python -m pytest"}
read -r -a PYTEST_CMD <<< "${PYTEST_BIN}"
DEFAULT_DATA_DIR=${AGENCY_DATA_DIR:-"$PWD/.ci_agency_data"}
mkdir -p "$DEFAULT_DATA_DIR"
export AGENCY_DATA_DIR="$DEFAULT_DATA_DIR"
COMMON_ARGS=(
  "--ignore=tests/test_firestore_learning_persistence.py"
  "--ignore=tests/test_firestore_mock_integration.py"
  "--ignore=tests/e2e"
  "--ignore=tests/benchmark"
  "--ignore=tests/benchmarks"
  "-m" "not slow"
  "--ff"
  "--maxfail=1"
)

run_chunk() {
  local label="$1"
  shift
  local targets=("$@")
  local filter=${CI_CHUNK_FILTER:-}
  if [[ -n "$filter" ]]; then
    local label_lc
    local filter_lc
    label_lc=$(printf '%s' "$label" | tr '[:upper:]' '[:lower:]')
    filter_lc=$(printf '%s' "$filter" | tr '[:upper:]' '[:lower:]')
    if [[ $label_lc != *"$filter_lc"* ]]; then
      echo "::group::pytest ${label}"
      echo "Skipping ${label} due to CI_CHUNK_FILTER='${filter}'."
      echo "::endgroup::"
      return
    fi
  fi

  echo "::group::pytest ${label}"
  if [[ ${#targets[@]} -eq 0 ]]; then
    echo "Skipping ${label} (no tests found)."
    echo "::endgroup::"
    return
  fi

  echo "Running ${PYTEST_BIN} ${targets[*]}"
  env PYTHONMALLOC=malloc "${PYTEST_CMD[@]}" "${targets[@]}" "${COMMON_ARGS[@]}"
  echo "::endgroup::"
}

# High-load suites executed individually
run_chunk "orchestrator suite" tests/orchestrator
# Split tools/ to prevent OOM (exit 137) - tools has many memory-heavy tests
run_chunk "tools/ci_monitor suite" tests/tools/ci_monitor
run_chunk "tools/orchestrator suite" tests/tools/orchestrator
run_chunk "tools core suite" tests/tools/test_*.py
run_chunk "integration suite" tests/integration
run_chunk "unit suite" tests/unit

# Medium-size collections grouped together
run_chunk "domain suites" \
  tests/adr \
  tests/agents \
  tests/chaos \
  tests/commands \
  tests/docs \
  tests/foundation_automation \
  tests/meta_learning \
  tests/necessary \
  tests/property \
  tests/shared \
  tests/stress \
  tests/trinity_protocol

# Top-level tests that live directly under tests/
TOP_LEVEL_TESTS=(tests/test_*.py)
run_chunk "top-level tests" "${TOP_LEVEL_TESTS[@]}"
