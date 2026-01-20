#!/bin/bash
# Skill: Test Backend
# Description: Runs the backend test suite using pytest.

echo "Running Backend Tests..."
# Ensure we are in the root
cd "$(dirname "$0")/.." || exit 1

if command -v pytest &> /dev/null; then
    pytest tests/ -v
    EXIT_CODE=$?
else
    echo "Error: pytest not found."
    EXIT_CODE=1
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Tests Passed."
else
    echo "❌ Tests Failed."
fi

exit $EXIT_CODE
