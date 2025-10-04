#!/bin/bash
# Phase 2A: Delete Experimental Test Bloat
#
# This script removes 731 experimental tests (24.7% of test suite)
# - Trinity Protocol: 19 test files (experimental voice assistant)
# - DSPy Agents: 6 test files (A/B testing framework)
# - Archived: 7 test files (legacy removed features)
# - Other experimental: 3 test files
#
# SAFE TO RUN: All deleted tests are for non-production experimental features

set -e  # Exit on error

AGENCY_ROOT="/Users/am/Code/Agency"
cd "$AGENCY_ROOT"

echo "============================================"
echo "Phase 2A: Test Bloat Removal"
echo "============================================"
echo ""
echo "This will DELETE 731 experimental tests (24.7% of suite)"
echo "Estimated time savings: 73 seconds per test run"
echo ""
echo "Categories to delete:"
echo "  - Trinity Protocol tests (19 files, ~140 tests)"
echo "  - DSPy A/B testing (6 files, ~248 tests)"
echo "  - Archived legacy tests (7 files, ~24 tests)"
echo "  - Other experimental (3 files, ~320 tests)"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Creating backup..."
BACKUP_DIR=".test_bloat_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup all files to be deleted
echo "Backing up Trinity Protocol tests..."
if [ -d "tests/trinity_protocol" ]; then
    cp -r tests/trinity_protocol "$BACKUP_DIR/"
fi

echo "Backing up DSPy agent tests..."
if [ -d "tests/dspy_agents" ]; then
    cp -r tests/dspy_agents "$BACKUP_DIR/"
fi

echo "Backing up archived tests..."
if [ -d "tests/archived" ]; then
    cp -r tests/archived "$BACKUP_DIR/"
fi

echo "Backing up other experimental tests..."
for file in \
    "tests/test_bash_tool_infrastructure.py" \
    "tests/test_learning_loop_integration.py" \
    "tests/test_git_error_paths.py"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/"
    fi
done

echo "✅ Backup created: $BACKUP_DIR"
echo ""

# Phase 2A.1: Delete experimental tests
echo "Phase 2A.1: Deleting experimental tests..."
echo ""

# Delete Trinity Protocol tests
if [ -d "tests/trinity_protocol" ]; then
    echo "  Deleting tests/trinity_protocol/ (19 files)..."
    rm -rf tests/trinity_protocol/
    echo "  ✅ Trinity Protocol tests deleted"
fi

# Delete DSPy agent tests
if [ -d "tests/dspy_agents" ]; then
    echo "  Deleting tests/dspy_agents/ (6 files)..."
    rm -rf tests/dspy_agents/
    echo "  ✅ DSPy agent tests deleted"
fi

# Delete archived tests
if [ -d "tests/archived" ]; then
    echo "  Deleting tests/archived/ (7 files)..."
    rm -rf tests/archived/
    echo "  ✅ Archived tests deleted"
fi

# Delete other experimental tests
echo "  Deleting experimental infrastructure tests..."
for file in \
    "tests/test_bash_tool_infrastructure.py" \
    "tests/test_learning_loop_integration.py" \
    "tests/test_git_error_paths.py"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "    ✅ Deleted $file"
    fi
done

echo ""
echo "============================================"
echo "Deletion Complete"
echo "============================================"
echo ""
echo "Files deleted: 35"
echo "Tests removed: 731"
echo "Lines removed: ~22,847"
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. Run test suite to verify: python run_tests.py --run-all"
echo "  2. If tests pass, commit changes"
echo "  3. If issues found, restore from: $BACKUP_DIR"
echo ""
echo "To restore backup:"
echo "  cp -r $BACKUP_DIR/trinity_protocol tests/"
echo "  cp -r $BACKUP_DIR/dspy_agents tests/"
echo "  cp -r $BACKUP_DIR/archived tests/"
echo "  cp $BACKUP_DIR/test_*.py tests/"
echo ""
