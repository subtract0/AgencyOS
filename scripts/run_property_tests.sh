#!/bin/bash
#
# Property-Based Testing Runner for Agency OS
#
# Runs Hypothesis-powered property tests with statistics and shrinking reports.
# Auto-generates 1000s of test cases to validate invariants.
#
# Usage:
#   ./scripts/run_property_tests.sh              # Run all property tests
#   ./scripts/run_property_tests.sh --fast       # Quick run (fewer examples)
#   ./scripts/run_property_tests.sh --extensive  # Extensive run (more examples)
#   ./scripts/run_property_tests.sh --verbose    # Show detailed statistics

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
HYPOTHESIS_PROFILE="default"
VERBOSITY="normal"
SHOW_STATS="--hypothesis-show-statistics"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            HYPOTHESIS_PROFILE="fast"
            shift
            ;;
        --extensive)
            HYPOTHESIS_PROFILE="extensive"
            shift
            ;;
        --verbose)
            VERBOSITY="verbose"
            shift
            ;;
        --quiet)
            VERBOSITY="quiet"
            SHOW_STATS=""
            shift
            ;;
        --no-stats)
            SHOW_STATS=""
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --fast        Run with fewer examples (faster, less thorough)"
            echo "  --extensive   Run with more examples (slower, more thorough)"
            echo "  --verbose     Show detailed Hypothesis statistics"
            echo "  --quiet       Minimal output"
            echo "  --no-stats    Don't show Hypothesis statistics"
            echo "  --help        Show this help message"
            echo ""
            echo "Hypothesis Profiles:"
            echo "  default    - 100 examples per test (balanced)"
            echo "  fast       - 20 examples per test (quick validation)"
            echo "  extensive  - 1000 examples per test (thorough validation)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Set Hypothesis profile
export HYPOTHESIS_PROFILE="$HYPOTHESIS_PROFILE"

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Property-Based Testing Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Profile: ${YELLOW}$HYPOTHESIS_PROFILE${NC}"
echo -e "Verbosity: ${YELLOW}$VERBOSITY${NC}"
echo ""

# Configure pytest arguments based on verbosity
PYTEST_ARGS=""
case $VERBOSITY in
    verbose)
        PYTEST_ARGS="-vv"
        ;;
    normal)
        PYTEST_ARGS="-v"
        ;;
    quiet)
        PYTEST_ARGS="-q"
        ;;
esac

# Add statistics flag if enabled
if [ -n "$SHOW_STATS" ]; then
    PYTEST_ARGS="$PYTEST_ARGS $SHOW_STATS"
fi

# Print test plan
echo -e "${BLUE}Test Plan:${NC}"
echo "  • Result pattern properties"
echo "  • JSONValue serialization properties"
echo "  • VectorStore state properties"
echo "  • RetryController behavior properties"
echo "  • Memory consolidation properties"
echo "  • Stateful tests (random operation sequences)"
echo ""

# Run property tests
echo -e "${BLUE}Running Property Tests...${NC}"
echo ""

# Track start time
START_TIME=$(date +%s)

# Run pytest with property tests
if uv run pytest tests/property/ $PYTEST_ARGS; then
    EXIT_CODE=0
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All Property Tests Passed${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    EXIT_CODE=1
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Property Tests Failed${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Hypothesis automatically shrinks failing cases to minimal examples.${NC}"
    echo -e "${YELLOW}Check the output above for the minimal failing input.${NC}"
fi

# Calculate elapsed time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo -e "Elapsed time: ${BLUE}${ELAPSED}s${NC}"

# Print hypothesis database info
if [ -d ".hypothesis" ]; then
    echo ""
    echo -e "${BLUE}Hypothesis Database:${NC}"
    echo "  Location: .hypothesis/"
    echo "  Contains: Cached failing examples for faster reproduction"
    echo ""
    echo -e "${YELLOW}Tip: Run tests again to reproduce failures instantly${NC}"
fi

# Print profile recommendations
if [ "$HYPOTHESIS_PROFILE" = "fast" ] && [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${YELLOW}Recommendation:${NC} Run with --extensive before commit"
fi

# Exit with test result code
exit $EXIT_CODE
