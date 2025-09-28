#!/bin/bash
# Test execution helper script with parallel options

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Agency Test Runner - Parallel Execution Enabled${NC}"
echo "================================================"

# Use virtual environment if available
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
    echo "Using virtual environment Python"
else
    PYTHON="python"
    echo "Using system Python"
fi

# Default to parallel execution
MODE="parallel"
WORKERS="auto"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --serial)
            MODE="serial"
            WORKERS="0"
            shift
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --fast)
            # Run only fast unit tests in parallel
            echo -e "${YELLOW}Running fast unit tests only...${NC}"
            $PYTHON -m pytest tests/ -m "unit" -n auto
            exit $?
            ;;
        --pattern)
            # Run pattern-related tests
            echo -e "${YELLOW}Running pattern intelligence tests...${NC}"
            $PYTHON -m pytest tests/ -k pattern -n auto
            exit $?
            ;;
        --help)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --serial      Run tests in serial (no parallelism)"
            echo "  --workers N   Use N workers (default: auto)"
            echo "  --fast        Run only fast unit tests"
            echo "  --pattern     Run pattern-related tests"
            echo "  --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                 # Run all tests in parallel"
            echo "  ./run_tests.sh --serial         # Run all tests serially"
            echo "  ./run_tests.sh --workers 4      # Run with 4 workers"
            echo "  ./run_tests.sh --fast           # Run only fast tests"
            exit 0
            ;;
        *)
            # Pass through to pytest
            PYTEST_ARGS="$@"
            break
            ;;
    esac
done

# Run tests
if [ "$MODE" = "serial" ]; then
    echo -e "${YELLOW}Running tests in serial mode...${NC}"
    $PYTHON -m pytest -n 0 $PYTEST_ARGS
else
    echo -e "${GREEN}Running tests in parallel with $WORKERS workers...${NC}"
    $PYTHON -m pytest -n $WORKERS $PYTEST_ARGS
fi

# Report exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${YELLOW}✗ Some tests failed (exit code: $EXIT_CODE)${NC}"
fi

exit $EXIT_CODE