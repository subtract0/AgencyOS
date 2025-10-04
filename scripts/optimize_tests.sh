#!/bin/bash
# Analyze test suite for optimization opportunities
#
# This script analyzes the test suite to identify:
# - Parallelizable tests
# - Expensive fixtures
# - Mocking opportunities
# - Redundant test coverage
#
# Usage:
#   ./scripts/optimize_tests.sh [test_dir]
#
# Arguments:
#   test_dir - Directory containing tests (default: tests/)
#
# Output:
#   - docs/testing/TEST_OPTIMIZATION.md

set -e  # Exit on error

# Default values
TEST_DIR="${1:-tests/}"
OUTPUT_DIR="docs/testing"
OUTPUT_FILE="${OUTPUT_DIR}/TEST_OPTIMIZATION.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 Test Suite Optimization Analyzer${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Run optimization analysis
echo -e "${CYAN}🔍 Analyzing test suite for optimization opportunities...${NC}"
echo -e "Test directory: ${TEST_DIR}"
echo ""

python -m tools.test_optimizer \
  --test-dir "${TEST_DIR}" \
  --output "${OUTPUT_FILE}"

# Check if analysis succeeded
if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✅ Optimization analysis complete!${NC}"
  echo ""

  # Display key findings if report exists
  if [ -f "${OUTPUT_FILE}" ]; then
    echo -e "${YELLOW}📊 Key Findings:${NC}"
    echo ""

    # Extract parallelizable tests count
    PARALLEL_COUNT=$(grep -oP "Found \K\d+(?= tests safe for parallel)" "${OUTPUT_FILE}" 2>/dev/null || echo "0")
    echo -e "  ${GREEN}✓${NC} Parallelizable tests: ${PARALLEL_COUNT}"

    # Extract expensive fixtures count
    EXPENSIVE_COUNT=$(grep -c "| .* | .* | .* |" "${OUTPUT_FILE}" 2>/dev/null || echo "0")
    # Subtract header rows
    EXPENSIVE_COUNT=$((EXPENSIVE_COUNT > 2 ? EXPENSIVE_COUNT - 2 : 0))
    echo -e "  ${YELLOW}⚠${NC} Expensive fixtures: ${EXPENSIVE_COUNT}"

    # Extract mocking opportunities count
    MOCK_COUNT=$(grep -oP "Found \K\d+(?= tests that should use mocks)" "${OUTPUT_FILE}" 2>/dev/null || echo "0")
    echo -e "  ${CYAN}💡${NC} Mocking opportunities: ${MOCK_COUNT}"

    # Extract estimated savings
    SAVINGS=$(grep -oP "Total estimated savings: \K[\d.]+(?= seconds)" "${OUTPUT_FILE}" 2>/dev/null || echo "0")
    echo -e "  ${GREEN}💰${NC} Estimated savings: ${SAVINGS}s"

    echo ""
    echo -e "${YELLOW}📁 Full report:${NC} ${OUTPUT_FILE}"

    # Display optimization priorities
    echo ""
    echo -e "${YELLOW}🎯 Implementation Priority:${NC}"
    echo ""

    # Extract priority sections
    if grep -q "Quick Wins" "${OUTPUT_FILE}"; then
      echo -e "${GREEN}1. Quick Wins (1 day):${NC}"
      grep -A 3 "Quick Wins" "${OUTPUT_FILE}" | tail -n 2 | sed 's/^/  /' | sed 's/   -/  •/'
      echo ""
    fi

    if grep -q "Medium Effort" "${OUTPUT_FILE}"; then
      echo -e "${YELLOW}2. Medium Effort (2-3 days):${NC}"
      grep -A 3 "Medium Effort" "${OUTPUT_FILE}" | tail -n 2 | sed 's/^/  /' | sed 's/   -/  •/'
      echo ""
    fi

    if grep -q "Long Term" "${OUTPUT_FILE}"; then
      echo -e "${CYAN}3. Long Term (1 week):${NC}"
      grep -A 3 "Long Term" "${OUTPUT_FILE}" | tail -n 2 | sed 's/^/  /' | sed 's/   -/  •/'
      echo ""
    fi
  fi

  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN}Next steps:${NC}"
  echo -e "  1. Review optimization plan in ${OUTPUT_FILE}"
  echo -e "  2. Start with Quick Wins for immediate impact"
  echo -e "  3. Install pytest-xdist: ${YELLOW}pip install pytest-xdist${NC}"
  echo -e "  4. Run tests in parallel: ${YELLOW}pytest -n auto${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

  exit 0
else
  echo ""
  echo -e "${RED}❌ Optimization analysis failed!${NC}"
  echo -e "Check the output above for errors."
  exit 1
fi
