#!/usr/bin/env python3
"""
Launch the Agency autonomously to complete type safety migration.
Runs for up to 8 hours or until completion.
"""

import os
import sys
import signal
import time
from datetime import datetime, timedelta
from pathlib import Path

def main():
    """Launch the autonomous type safety migration."""

    print("=" * 60)
    print("AGENCY AUTONOMOUS TYPE SAFETY MIGRATION")
    print("Constitutional Law #2 Enforcement Protocol")
    print("=" * 60)
    print()

    # Set environment for autonomous operation
    os.environ["ENABLE_UNIFIED_CORE"] = "true"
    os.environ["PERSIST_PATTERNS"] = "true"
    os.environ["AUTONOMOUS_MODE"] = "true"
    os.environ["OPENAI_MODEL"] = "gpt-4o-mini"  # Cost-efficient for bulk work

    print("✅ Environment configured")
    print("   - Using gpt-4o-mini for cost efficiency")
    print("   - Autonomous mode enabled")
    print("   - Pattern persistence enabled")
    print()

    # Create mission prompt
    mission = """You are the Agency executing Constitutional Law #2: Strict Typing Always.

MISSION: Eliminate ALL Dict[str, Any] usage (~1,834 violations remaining).

SYSTEMATIC APPROACH:
1. Process each Python file sequentially
2. Create Pydantic models in shared/models/
3. Replace all Dict[str, Any] with concrete models
4. Verify syntax and imports
5. Commit every 50 files

PRIORITY ORDER:
- agency_memory/ (92 violations)
- tools/ (69 violations)
- shared/ (35 violations)
- learning_loop/ (22 violations)
- All remaining files

REQUIREMENTS:
- Use ConfigDict(extra="forbid") on all models
- Include field types and docstrings
- Reuse existing models where applicable
- Self-heal any errors encountered
- Learn from successful patterns

Work autonomously. Begin immediately."""

    print("📋 Mission prepared:")
    print("-" * 40)
    print(mission[:300] + "...")
    print("-" * 40)
    print()

    # Set up timeout (8 hours)
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=8)

    print(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create log file
    log_file = f"logs/autonomous_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    print(f"📝 Logging to: {log_file}")
    print()

    print("🚀 Launching Agency...")
    print("=" * 60)

    # Import and run the agency
    try:
        import subprocess

        # Write mission to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(mission)
            mission_file = f.name

        # Launch agency as subprocess
        process = subprocess.Popen(
            [sys.executable, 'agency.py'],
            stdin=open(mission_file, 'r'),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        print(f"✅ Agency launched with PID: {process.pid}")
        print()
        print("The Agency is now working autonomously.")
        print("It will:")
        print("  1. Scan all files for Dict[str, Any]")
        print("  2. Create appropriate Pydantic models")
        print("  3. Migrate each file systematically")
        print("  4. Test and commit regularly")
        print("  5. Create final PR when complete")
        print()
        print("Monitor progress with: tail -f " + log_file)
        print(f"Stop if needed with: kill {process.pid}")
        print()
        print("=" * 60)
        print("AUTONOMOUS EXECUTION IN PROGRESS...")
        print("=" * 60)
        print()

        # Write output to log file and console
        with open(log_file, 'w') as log:
            log.write(f"Agency Autonomous Migration Started: {start_time}\n")
            log.write(f"Mission:\n{mission}\n")
            log.write("=" * 60 + "\n")

            while True:
                # Check if timeout reached
                if datetime.now() > end_time:
                    print("\n⏰ 8-hour timeout reached. Stopping Agency...")
                    process.terminate()
                    time.sleep(5)
                    if process.poll() is None:
                        process.kill()
                    break

                # Read output
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                if line:
                    print(line.rstrip())
                    log.write(line)
                    log.flush()

        # Clean up temp file
        os.unlink(mission_file)

        print()
        print("=" * 60)
        print("MISSION COMPLETE")
        print("=" * 60)
        print()
        print(f"Duration: {datetime.now() - start_time}")
        print(f"Log saved to: {log_file}")
        print()
        print("Next steps:")
        print("  1. Review the changes: git diff")
        print("  2. Run tests: python run_tests.py")
        print("  3. Create PR if successful")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())