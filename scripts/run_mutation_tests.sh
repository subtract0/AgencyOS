#!/bin/bash
# Mutation Testing Script for Agency OS
# Runs mutation testing on CRITICAL modules to verify test suite effectiveness
#
# Constitutional Compliance:
# - Article II: 100% verification via mutation testing
# - Mars Rover Standard: 95%+ mutation score required
#
# Usage:
#   ./scripts/run_mutation_tests.sh [--quick] [--full] [--file FILE]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/docs/testing"
REPORT_FILE="$REPORT_DIR/MUTATION_REPORT.md"

# Ensure report directory exists
mkdir -p "$REPORT_DIR"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   MUTATION TESTING - MARS ROVER STANDARD${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Parse arguments
MODE="quick"
TARGET_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            MODE="quick"
            shift
            ;;
        --full)
            MODE="full"
            shift
            ;;
        --file)
            TARGET_FILE="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--quick] [--full] [--file FILE]"
            exit 1
            ;;
    esac
done

# Define critical modules to test
CRITICAL_MODULES=(
    "shared/agent_context.py"
    "shared/models/memory.py"
    "agency_cli/commands.py"
    "tools/bash.py"
    "tools/git.py"
)

# Define test commands
TEST_COMMAND="python -m pytest tests/unit -x -v"

# If specific file provided, use it
if [ -n "$TARGET_FILE" ]; then
    CRITICAL_MODULES=("$TARGET_FILE")
fi

# If quick mode, test only first 2 modules
if [ "$MODE" = "quick" ]; then
    CRITICAL_MODULES=("${CRITICAL_MODULES[@]:0:2}")
    echo -e "${YELLOW}Quick Mode: Testing ${#CRITICAL_MODULES[@]} modules${NC}"
else
    echo -e "${YELLOW}Full Mode: Testing ${#CRITICAL_MODULES[@]} modules${NC}"
fi

echo ""

# Run mutation testing via Python
python3 << 'EOF'
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(os.environ.get('PROJECT_ROOT', '.')).resolve()
sys.path.insert(0, str(project_root))

from tools.mutation_testing import (
    MutationConfig,
    MutationTester,
)

# Get configuration from environment
critical_modules = os.environ.get('CRITICAL_MODULES', '').split(':')
test_command = os.environ.get('TEST_COMMAND', 'pytest tests/')
report_file = os.environ.get('REPORT_FILE', 'MUTATION_REPORT.md')

# Filter valid files
target_files = [
    str(project_root / module)
    for module in critical_modules
    if module and (project_root / module).exists()
]

if not target_files:
    print("❌ No valid target files found")
    sys.exit(1)

print(f"🎯 Target files: {len(target_files)}")
for f in target_files:
    print(f"  - {Path(f).relative_to(project_root)}")
print()

# Create mutation config
config = MutationConfig(
    target_files=target_files,
    test_command=test_command,
    mutation_types=["arithmetic", "comparison", "boolean", "constant", "return"],
    timeout_seconds=120,
    parallel=False  # Sequential for better error reporting
)

# Run mutation testing
print("🔬 Running mutation testing...")
print("=" * 80)

tester = MutationTester(config)
result = tester.run()

if result.is_err():
    print(f"❌ Mutation testing failed: {result.unwrap_err()}")
    sys.exit(1)

score = result.unwrap()

# Generate report
report = tester.generate_report(score)
print(report)

# Save report to file
report_path = Path(report_file)
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(report)

print()
print(f"📄 Report saved to: {report_path.relative_to(project_root)}")
print()

# Check Mars Rover standard (95%+)
MARS_ROVER_THRESHOLD = 0.95

if score.mutation_score >= MARS_ROVER_THRESHOLD:
    print("✅ MARS ROVER STANDARD ACHIEVED (95%+)")
    sys.exit(0)
elif score.mutation_score >= 0.80:
    print("⚠️  GOOD but below Mars Rover standard (need 95%+)")
    sys.exit(1)
else:
    print("❌ INSUFFICIENT test coverage (need 95%+)")
    sys.exit(1)

EOF

# Export variables for Python script
export PROJECT_ROOT
export CRITICAL_MODULES="${CRITICAL_MODULES[*]}"
export CRITICAL_MODULES="${CRITICAL_MODULES// /:}"
export TEST_COMMAND
export REPORT_FILE

# Run the embedded Python script
python3 << 'PYTHON_EOF'
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(os.environ.get('PROJECT_ROOT', '.')).resolve()
sys.path.insert(0, str(project_root))

from tools.mutation_testing import (
    MutationConfig,
    MutationTester,
)

# Get configuration from environment
critical_modules = os.environ.get('CRITICAL_MODULES', '').split(':')
test_command = os.environ.get('TEST_COMMAND', 'pytest tests/')
report_file = os.environ.get('REPORT_FILE', 'MUTATION_REPORT.md')

# Filter valid files
target_files = [
    str(project_root / module)
    for module in critical_modules
    if module and (project_root / module).exists()
]

if not target_files:
    print("❌ No valid target files found")
    sys.exit(1)

print(f"🎯 Target files: {len(target_files)}")
for f in target_files:
    print(f"  - {Path(f).relative_to(project_root)}")
print()

# Create mutation config
config = MutationConfig(
    target_files=target_files,
    test_command=test_command,
    mutation_types=["arithmetic", "comparison", "boolean", "constant", "return"],
    timeout_seconds=120,
    parallel=False  # Sequential for better error reporting
)

# Run mutation testing
print("🔬 Running mutation testing...")
print("=" * 80)

tester = MutationTester(config)
result = tester.run()

if result.is_err():
    print(f"❌ Mutation testing failed: {result.unwrap_err()}")
    sys.exit(1)

score = result.unwrap()

# Generate report
report = tester.generate_report(score)
print(report)

# Save report to file
report_path = Path(report_file)
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(report)

print()
print(f"📄 Report saved to: {report_path.relative_to(project_root)}")
print()

# Check Mars Rover standard (95%+)
MARS_ROVER_THRESHOLD = 0.95

if score.mutation_score >= MARS_ROVER_THRESHOLD:
    print("✅ MARS ROVER STANDARD ACHIEVED (95%+)")
    sys.exit(0)
elif score.mutation_score >= 0.80:
    print("⚠️  GOOD but below Mars Rover standard (need 95%+)")
    sys.exit(1)
else:
    print("❌ INSUFFICIENT test coverage (need 95%+)")
    sys.exit(1)

PYTHON_EOF
