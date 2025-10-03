#!/bin/bash
# Profile test suite performance and identify bottlenecks
#
# This script runs comprehensive performance profiling on the test suite
# to identify optimization opportunities.
#
# Usage:
#   ./scripts/profile_tests.sh [test_path] [threshold]
#
# Arguments:
#   test_path  - Path to tests (default: tests/)
#   threshold  - Slow test threshold in seconds (default: 1.0)
#
# Output:
#   - docs/testing/PERFORMANCE_PROFILE.md (markdown report)
#   - docs/testing/PERFORMANCE_PROFILE.json (JSON data)

set -e  # Exit on error

# Default values
TEST_PATH="${1:-tests/}"
THRESHOLD="${2:-1.0}"
OUTPUT_DIR="docs/testing"
OUTPUT_FILE="${OUTPUT_DIR}/PERFORMANCE_PROFILE.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 Test Suite Performance Profiler${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Run performance profiling
echo -e "${YELLOW}Running performance profiling...${NC}"
echo -e "Test path: ${TEST_PATH}"
echo -e "Slow test threshold: ${THRESHOLD}s"
echo ""

python -m tools.performance_profiling \
  --test-path "${TEST_PATH}" \
  --output "${OUTPUT_FILE}" \
  --threshold "${THRESHOLD}"

# Check if profiling succeeded
if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✅ Performance profiling complete!${NC}"
  echo ""

  # Display slowest tests if report exists
  if [ -f "${OUTPUT_FILE}" ]; then
    echo -e "${YELLOW}📊 Slowest tests:${NC}"
    echo ""

    # Extract and display top 10 slowest tests from markdown table
    grep -A 11 "## Slowest Tests" "${OUTPUT_FILE}" | tail -n +4 | head -n 10 | \
      awk -F'|' '{if (NF > 1) print "  " $2 " →" $3}'

    echo ""
    echo -e "${YELLOW}📁 Full report:${NC} ${OUTPUT_FILE}"
    echo -e "${YELLOW}📁 JSON data:${NC} ${OUTPUT_DIR}/PERFORMANCE_PROFILE.json"

    # Display key metrics
    if [ -f "${OUTPUT_DIR}/PERFORMANCE_PROFILE.json" ]; then
      echo ""
      echo -e "${YELLOW}📈 Key Metrics:${NC}"

      TOTAL_DURATION=$(python -c "import json; print(json.load(open('${OUTPUT_DIR}/PERFORMANCE_PROFILE.json'))['total_duration'])")
      TEST_COUNT=$(python -c "import json; print(json.load(open('${OUTPUT_DIR}/PERFORMANCE_PROFILE.json'))['test_count'])")

      echo -e "  Total duration: ${TOTAL_DURATION}s"
      echo -e "  Test count: ${TEST_COUNT}"
      echo -e "  Average per test: $(python -c "print(round(${TOTAL_DURATION} / max(${TEST_COUNT}, 1), 3))")s"
    fi
  fi

  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN}Next steps:${NC}"
  echo -e "  1. Review bottlenecks in ${OUTPUT_FILE}"
  echo -e "  2. Run optimization analysis: ${YELLOW}./scripts/optimize_tests.sh${NC}"
  echo -e "  3. Implement recommendations from the reports"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

  exit 0
else
  echo ""
  echo -e "${RED}❌ Performance profiling failed!${NC}"
  echo -e "Check the output above for errors."
  exit 1
fi
