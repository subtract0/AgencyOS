#!/bin/bash
# Run only tests affected by git changes
#
# This script uses smart test selection to run only the tests
# that are affected by your code changes, dramatically reducing
# test execution time during development.
#
# Usage:
#   ./scripts/run_smart_tests.sh [since] [pytest_args...]
#
# Arguments:
#   since       - Git reference to compare against (default: HEAD~1)
#   pytest_args - Additional arguments to pass to pytest
#
# Examples:
#   ./scripts/run_smart_tests.sh                    # Compare to last commit
#   ./scripts/run_smart_tests.sh HEAD~3             # Compare to 3 commits ago
#   ./scripts/run_smart_tests.sh main               # Compare to main branch
#   ./scripts/run_smart_tests.sh HEAD~1 -v --tb=short  # With pytest options

set -e  # Exit on error

# Default values
SINCE="${1:-HEAD~1}"
shift || true  # Remove first argument, keep rest for pytest
PYTEST_ARGS="$@"

OUTPUT_DIR="docs/testing"
SELECTED_TESTS_FILE="/tmp/agency_selected_tests.txt"
REPORT_FILE="${OUTPUT_DIR}/SMART_SELECTION.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎯 Smart Test Selection${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Run smart test selection
echo -e "${CYAN}🔍 Analyzing changes since ${SINCE}...${NC}"
echo ""

python -m tools.smart_test_selection \
  --since "${SINCE}" \
  --output "${SELECTED_TESTS_FILE}" \
  --report "${REPORT_FILE}"

# Check if selection succeeded
if [ $? -ne 0 ]; then
  echo ""
  echo -e "${RED}❌ Smart test selection failed!${NC}"
  exit 1
fi

echo ""

# Check if any tests were selected
if [ ! -f "${SELECTED_TESTS_FILE}" ] || [ ! -s "${SELECTED_TESTS_FILE}" ]; then
  echo -e "${GREEN}✅ No tests affected by changes${NC}"
  echo -e "All changes appear to be in non-code files or comments."
  echo ""
  echo -e "${YELLOW}💡 Tip:${NC} Run full test suite with: ${CYAN}python run_tests.py --run-all${NC}"
  exit 0
fi

# Count selected tests
TEST_COUNT=$(wc -l < "${SELECTED_TESTS_FILE}")

echo -e "${YELLOW}🧪 Running ${TEST_COUNT} affected tests...${NC}"
echo ""

# Build pytest command
PYTEST_CMD="pytest"

# Add test files from selection
while IFS= read -r test_file; do
  PYTEST_CMD="${PYTEST_CMD} \"${test_file}\""
done < "${SELECTED_TESTS_FILE}"

# Add additional pytest arguments
if [ -n "${PYTEST_ARGS}" ]; then
  PYTEST_CMD="${PYTEST_CMD} ${PYTEST_ARGS}"
else
  # Default pytest options
  PYTEST_CMD="${PYTEST_CMD} -v --tb=short --color=yes"
fi

# Display command being run
echo -e "${CYAN}Command:${NC} ${PYTEST_CMD}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Run pytest with selected tests
eval ${PYTEST_CMD}
PYTEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Display results
if [ ${PYTEST_EXIT_CODE} -eq 0 ]; then
  echo -e "${GREEN}✅ All selected tests passed!${NC}"
else
  echo -e "${RED}❌ Some tests failed (exit code: ${PYTEST_EXIT_CODE})${NC}"
fi

echo ""
echo -e "${YELLOW}📊 Summary:${NC}"
echo -e "  Tests run: ${TEST_COUNT}"
echo -e "  Exit code: ${PYTEST_EXIT_CODE}"

# Show time savings estimate from report if available
if [ -f "${REPORT_FILE}" ]; then
  echo -e "  Full report: ${REPORT_FILE}"

  # Try to extract time saved from report
  TIME_SAVED=$(grep -oP "Estimated time saved:\s*\K[\d.]+" "${REPORT_FILE}" 2>/dev/null || echo "N/A")
  SPEEDUP=$(grep -oP "Speedup:\s*\K[\d.]+" "${REPORT_FILE}" 2>/dev/null || echo "N/A")

  if [ "${TIME_SAVED}" != "N/A" ]; then
    echo -e "  Time saved: ~${TIME_SAVED}s"
  fi
  if [ "${SPEEDUP}" != "N/A" ]; then
    echo -e "  Speedup: ${SPEEDUP}x faster"
  fi
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}💡 Tips:${NC}"
echo -e "  • Compare to branch: ${YELLOW}./scripts/run_smart_tests.sh main${NC}"
echo -e "  • Compare to N commits: ${YELLOW}./scripts/run_smart_tests.sh HEAD~5${NC}"
echo -e "  • Run full suite: ${YELLOW}python run_tests.py --run-all${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Clean up temporary file
rm -f "${SELECTED_TESTS_FILE}"

exit ${PYTEST_EXIT_CODE}
