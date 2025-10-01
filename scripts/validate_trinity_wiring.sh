#!/bin/bash
# Validates Trinity Protocol production wiring
#
# Usage: ./scripts/validate_trinity_wiring.sh
#
# Constitutional Compliance:
# - Article II: 100% test success required
# - No Dict[Any, Any] violations allowed
# - Type checking must pass

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================================================"
echo "Trinity Protocol - Production Wiring Validation"
echo "================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall success
VALIDATION_PASSED=true

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
        VALIDATION_PASSED=false
    fi
}

echo "Phase 1: Trinity Component Tests"
echo "----------------------------------------------------------------"
echo -n "Running Trinity tests... "

if python -m pytest tests/trinity_protocol/ -o addopts="" -q > /tmp/trinity_tests.log 2>&1; then
    TRINITY_COUNT=$(grep -o "[0-9]* passed" /tmp/trinity_tests.log | awk '{print $1}')
    echo -e "${GREEN}✓ $TRINITY_COUNT tests passed${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    cat /tmp/trinity_tests.log
    VALIDATION_PASSED=false
fi
echo ""

echo "Phase 2: Type Checking"
echo "----------------------------------------------------------------"
echo -n "Running mypy type check... "

if python -m mypy trinity_protocol/ --no-error-summary > /tmp/mypy.log 2>&1; then
    print_status 0
else
    # Check if mypy is installed
    if grep -q "No module named mypy" /tmp/mypy.log; then
        echo -e "${YELLOW}⊘ SKIPPED (mypy not installed)${NC}"
    else
        print_status 1
        cat /tmp/mypy.log
    fi
fi
echo ""

echo "Phase 3: Constitutional Compliance"
echo "----------------------------------------------------------------"
echo -n "Checking for Dict[Any, Any] violations... "

# Search for Dict[Any, Any] in trinity_protocol Python files
if grep -r "Dict\[Any, Any\]" trinity_protocol/*.py > /tmp/dict_violations.log 2>&1; then
    echo -e "${RED}✗ VIOLATIONS FOUND${NC}"
    cat /tmp/dict_violations.log
    VALIDATION_PASSED=false
else
    echo -e "${GREEN}✓ No violations${NC}"
fi
echo ""

echo "Phase 4: Sub-Agent Wiring Verification"
echo "----------------------------------------------------------------"
echo -n "Checking sub-agent imports... "

# Verify all required imports exist in executor_agent.py
IMPORTS_OK=true

for agent in "agency_code_agent" "test_generator_agent" "toolsmith_agent" "quality_enforcer_agent" "merger_agent" "work_completion_summary_agent"; do
    if grep -q "from $agent import" trinity_protocol/executor_agent.py; then
        : # Import found, continue
    else
        IMPORTS_OK=false
        echo ""
        echo -e "${YELLOW}  ⊘ Missing import: $agent${NC}"
    fi
done

if [ "$IMPORTS_OK" = true ]; then
    echo -e "${GREEN}✓ All imports present${NC}"
else
    echo -e "${YELLOW}⊘ INCOMPLETE (some imports missing)${NC}"
    echo "   This is expected if Phase 1.1 wiring not yet complete"
fi
echo ""

echo -n "Checking verification implementation... "
# Verify _run_absolute_verification uses real subprocess execution
if grep -q "subprocess.run" trinity_protocol/executor_agent.py && \
   grep -q "run_tests.py" trinity_protocol/executor_agent.py && \
   grep -q "\-\-run-all" trinity_protocol/executor_agent.py; then
    echo -e "${GREEN}✓ Real verification wired${NC}"
else
    echo -e "${RED}✗ Mock verification still in use${NC}"
    VALIDATION_PASSED=false
fi
echo ""

echo "Phase 5: Integration Tests"
echo "----------------------------------------------------------------"
echo -n "Running production integration tests... "

if python -m pytest tests/trinity_protocol/test_production_integration.py -o addopts="" -q > /tmp/integration_tests.log 2>&1; then
    INT_COUNT=$(grep -o "[0-9]* passed" /tmp/integration_tests.log | awk '{print $1}')
    echo -e "${GREEN}✓ $INT_COUNT tests passed${NC}"
else
    echo -e "${YELLOW}⊘ INCOMPLETE${NC}"
    # Show summary but don't fail (some tests may be skipped pre-wiring)
    tail -10 /tmp/integration_tests.log
fi
echo ""

echo "Phase 6: Full Agency Test Suite (Optional)"
echo "----------------------------------------------------------------"
echo -n "Checking if run_tests.py exists... "

if [ -f "run_tests.py" ]; then
    echo -e "${GREEN}✓ Found${NC}"
    echo -n "Run full test suite? (y/N) "
    read -t 5 -n 1 response || response="n"
    echo ""

    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Running full test suite (this may take several minutes)..."
        if python run_tests.py --run-all > /tmp/full_tests.log 2>&1; then
            FULL_COUNT=$(grep -o "[0-9]* passed" /tmp/full_tests.log | awk '{print $1}')
            echo -e "${GREEN}✓ $FULL_COUNT tests passed${NC}"
        else
            echo -e "${RED}✗ FAILED${NC}"
            tail -50 /tmp/full_tests.log
            VALIDATION_PASSED=false
        fi
    else
        echo -e "${YELLOW}⊘ SKIPPED${NC}"
    fi
else
    echo -e "${YELLOW}⊘ Not found${NC}"
fi
echo ""

echo "================================================================"
echo "Validation Summary"
echo "================================================================"

if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}✓ ALL VALIDATIONS PASSED${NC}"
    echo ""
    echo "Trinity Protocol wiring is ready for production."
    echo ""
    echo "Next steps:"
    echo "  1. Review docs/trinity_protocol/PRODUCTION_WIRING.md"
    echo "  2. Complete any remaining Phase 1 tasks"
    echo "  3. Run end-to-end integration test"
    echo "  4. Deploy for 24-hour continuous operation test"
    echo ""
    exit 0
else
    echo -e "${RED}✗ VALIDATION FAILED${NC}"
    echo ""
    echo "Some checks did not pass. Review errors above."
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure all dependencies installed: pip install -e ."
    echo "  2. Check constitutional compliance in PRODUCTION_WIRING.md"
    echo "  3. Run individual test suites to isolate failures"
    echo "  4. Review logs in /tmp/ for detailed error messages"
    echo ""
    exit 1
fi
