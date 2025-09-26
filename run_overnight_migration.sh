#!/bin/bash
# Run the Agency overnight to complete type safety migration
# Estimated cost: $8-10 for 8 hours of work

echo "=========================================="
echo "AUTONOMOUS TYPE SAFETY MIGRATION"
echo "Constitutional Law #2 Enforcement"
echo "=========================================="
echo ""
echo "This will run the Agency autonomously to:"
echo "- Eliminate remaining ~1,834 Dict[str, Any] violations"
echo "- Create Pydantic models for all data structures"
echo "- Ensure 100% type safety compliance"
echo ""
echo "Estimated duration: 8 hours"
echo "Estimated cost: \$8-10"
echo ""

# Set up environment
export ENABLE_UNIFIED_CORE=true
export PERSIST_PATTERNS=true
export AUTONOMOUS_MODE=true
export OPENAI_MODEL="gpt-4o-mini"  # Use cheaper model for bulk work

# Create mission file for agency
cat > /tmp/type_migration_mission.txt << 'EOF'
You are the Agency system executing Constitutional Law #2: Strict Typing Always.

MISSION: Complete type safety migration by eliminating ALL Dict[str, Any] usage.

CURRENT STATE:
- 93 violations fixed in PR #17
- ~1,834 violations remain across 400+ files

EXECUTION STEPS:
1. For each Python file in the codebase:
   - Find all Dict[str, Any] usage
   - Create appropriate Pydantic models
   - Replace Dict with concrete models
   - Ensure imports are correct

2. Priority order:
   - agency_memory/ (92 violations)
   - tools/ (69 violations)
   - shared/ (35 violations)
   - All remaining files

3. For each migration:
   - Create models in shared/models/
   - Use ConfigDict(extra="forbid")
   - Include proper field types
   - Add docstrings

4. After every 50 files:
   - Run tests to verify
   - Commit progress
   - Continue

5. Final validation:
   - All tests must pass
   - No Dict[str, Any] remaining
   - Create PR with results

Work autonomously for 8 hours. Self-heal any errors. Learn from patterns.
Begin immediately.
EOF

echo "Starting Agency in autonomous mode..."
echo "Logs will be written to: logs/autonomous_migration_$(date +%Y%m%d_%H%M%S).log"
echo ""

# Run the agency with logging (macOS compatible - no timeout command)
# Will run for 8 hours or until completion
python agency.py < /tmp/type_migration_mission.txt 2>&1 | tee "logs/autonomous_migration_$(date +%Y%m%d_%H%M%S).log" &

# Get the PID
AGENCY_PID=$!

echo "Agency launched with PID: $AGENCY_PID"
echo ""
echo "The Agency will now work autonomously overnight."
echo "Check progress with: tail -f logs/autonomous_migration_*.log"
echo "Stop if needed with: kill $AGENCY_PID"
echo ""
echo "Good night! The Agency will complete the migration while you sleep."
echo "=========================================="