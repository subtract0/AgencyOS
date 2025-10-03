#!/bin/bash
# Quick Health Check for Agency OS
# Validates constitutional compliance and system status

set -e

echo "🏥 Agency OS Health Check"
echo "========================="
echo ""

# Check Python environment
echo "🐍 Python Environment:"
python_version=$(python --version 2>&1)
echo "   $python_version"
echo ""

# Constitutional validation
echo "⚖️  Constitutional Compliance:"
python -c "
from shared.constitutional_validator import *
try:
    validate_article_i()
    print('   ✅ Article I: Complete Context Before Action')
except Exception as e:
    print(f'   ❌ Article I: {e}')

try:
    validate_article_ii()
    print('   ✅ Article II: 100% Verification and Stability')
except Exception as e:
    print(f'   ❌ Article II: {e}')

try:
    validate_article_iii()
    print('   ✅ Article III: Automated Merge Enforcement')
except Exception as e:
    print(f'   ❌ Article III: {e}')

try:
    validate_article_iv()
    print('   ✅ Article IV: Continuous Learning')
except Exception as e:
    print(f'   ❌ Article IV: {e}')

try:
    validate_article_v()
    print('   ✅ Article V: Spec-Driven Development')
except Exception as e:
    print(f'   ❌ Article V: {e}')
" 2>&1 | grep -E "✅|❌"
echo ""

# Git status
echo "📦 Git Status:"
if git rev-parse --git-dir > /dev/null 2>&1; then
    current_branch=$(git branch --show-current)
    echo "   Branch: $current_branch"

    if [ -z "$(git status --porcelain)" ]; then
        echo "   ✅ Working tree clean"
    else
        modified=$(git status --porcelain | wc -l | tr -d ' ')
        echo "   ⚠️  $modified uncommitted changes"
    fi
else
    echo "   ❌ Not a git repository"
fi
echo ""

# Log health
echo "📊 Log Health:"
if [ -d logs/sessions ]; then
    session_size=$(du -sh logs/sessions 2>/dev/null | awk '{print $1}')
    session_count=$(ls -1 logs/sessions/*.md 2>/dev/null | wc -l | tr -d ' ')
    echo "   Sessions: $session_size ($session_count files)"
fi

if [ -d logs/telemetry ]; then
    telemetry_size=$(du -sh logs/telemetry 2>/dev/null | awk '{print $1}')
    echo "   Telemetry: $telemetry_size"
fi

if [ -d logs/autonomous_healing ]; then
    healing_size=$(du -sh logs/autonomous_healing 2>/dev/null | awk '{print $1}')
    echo "   Autonomous Healing: $healing_size"
fi
echo ""

# Technical debt
echo "🔧 Technical Debt:"
debt_count=$(grep -r "TODO\|FIXME\|XXX\|HACK" --include="*.py" . 2>/dev/null | wc -l | tr -d ' ')
echo "   $debt_count markers found"
echo ""

# Test infrastructure
echo "🧪 Test Infrastructure:"
test_files=$(find tests -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
echo "   $test_files test files"
echo ""

echo "✅ Health check complete!"
echo ""
echo "For detailed report, see: SYSTEM_HEALTH_REPORT.md"
