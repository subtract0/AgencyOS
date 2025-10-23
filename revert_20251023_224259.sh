#!/bin/bash
# Revert script for test deletion PR
# Generated: 20251023_224259
# Backup: backup.zip

set -e  # Exit on error

echo "⚠️  Reverting test deletions from 20251023_224259..."
echo ""

# Check if backup exists
if [ ! -f "backup.zip" ]; then
    echo "❌ Backup file not found: backup.zip"
    exit 1
fi

# Unzip backup (restore all test files)
echo "📦 Restoring 0 test files from backup..."
unzip -o "backup.zip" -d .

echo ""
echo "✅ Test files restored successfully!"
echo ""
echo "🧪 Running tests to verify restoration..."
python run_tests.py --run-all

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests pass! Restoration successful."
    echo ""
    echo "Next steps:"
    echo "1. git add tests/"
    echo "2. git commit -m 'revert: Restore deleted tests (rollback 20251023_224259)'"
    echo "3. git push"
else
    echo ""
    echo "❌ Some tests failed after restoration. Manual review needed."
    exit 1
fi
