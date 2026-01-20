#!/bin/bash
# skills/audit.sh
# Purpose: Provide a high-level overview of the codebase state for the Agent.

echo "=== 🔍 CODEBASE AUDIT REPORT ==="
echo "Date: $(date)"
echo "Directory: $(pwd)"
echo ""

echo "--- 1. STRUCTURE (Top 2 Levels) ---"
if command -v tree &> /dev/null; then
    tree -L 2 -I '__pycache__|node_modules|.git|.venv'
else
    find . -maxdepth 2 -not -path '*/.*'
fi
echo ""

echo "--- 2. SIZE ---"
echo "Python Files: $(find . -name "*.py" | wc -l)"
echo "Markdown Files: $(find . -name "*.md" | wc -l)"
echo "Total Lines (approx): $(find . -name "*.py" -o -name "*.md" | xargs wc -l | tail -n 1)"
echo ""

echo "--- 3. TODOs & FIXMEs ---"
grep -r "TODO" . --include="*.py" --include="*.md" | head -n 5
echo "(...and more)"
grep -r "FIXME" . --include="*.py" --include="*.md" | head -n 5
echo ""

echo "--- 4. RECENT ACTIVITY (Last 5 Commits) ---"
git log -n 5 --oneline 2>/dev/null || echo "Not a git repo or no commits."

echo ""
echo "=== END REPORT ==="
