#!/bin/bash
# Install AgencyOS git hooks

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Installing AgencyOS git hooks..."

# Create hooks directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/.git/hooks"

# Install pre-commit hook
cp "$SCRIPT_DIR/pre-commit-heal" "$PROJECT_ROOT/.git/hooks/pre-commit"
chmod +x "$PROJECT_ROOT/.git/hooks/pre-commit"

echo "✅ Installed pre-commit hook"
echo ""
echo "The hook will now run before each commit to check for:"
echo "  - Dict[Any, Any] violations (Constitutional Article IV)"
echo "  - Bare except statements"
echo "  - Other code quality issues"
echo ""
echo "To bypass: git commit --no-verify"
