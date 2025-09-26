#!/usr/bin/env python3
"""
Launch the Agency in autonomous mode to complete type safety migration.
This will run overnight and complete the Constitutional Law #2 enforcement.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    """Launch autonomous type safety migration."""

    print("=" * 60)
    print("AGENCY AUTONOMOUS TYPE SAFETY MIGRATION")
    print("Constitutional Law #2 Enforcement Protocol")
    print("=" * 60)
    print()

    # Import the Agency
    try:
        from agency import agency
        from agency_code_agent.agency_code_agent import AgencyCodeAgent
    except ImportError as e:
        print(f"Failed to import Agency: {e}")
        print("Ensure you're in the Agency directory and dependencies are installed")
        return 1

    print("✅ Agency imported successfully")
    print()

    # Read the mission prompt
    mission_file = Path("autonomous_type_safety_mission.md")
    if not mission_file.exists():
        print("❌ Mission file not found: autonomous_type_safety_mission.md")
        return 1

    with open(mission_file, "r") as f:
        mission_prompt = f.read()

    print("📋 Mission loaded:")
    print("-" * 40)
    print(mission_prompt[:500] + "...")
    print("-" * 40)
    print()

    # Configure for autonomous operation
    os.environ["ENABLE_UNIFIED_CORE"] = "true"
    os.environ["PERSIST_PATTERNS"] = "true"
    os.environ["AUTONOMOUS_MODE"] = "true"
    os.environ["MAX_ITERATIONS"] = "10000"  # Allow many iterations
    os.environ["SELF_HEALING_ENABLED"] = "true"

    print("🔧 Environment configured for autonomous operation")
    print()

    # Initialize the Agency
    print("🚀 Initializing Agency system...")

    try:
        # Get the main code agent
        ceo = agency.ceo  # ChiefArchitectAgent
        code_agent = None

        # Find the AgencyCodeAgent
        for agent in agency.agents:
            if isinstance(agent, AgencyCodeAgent):
                code_agent = agent
                break

        if not code_agent:
            print("❌ Could not find AgencyCodeAgent")
            return 1

        print("✅ Agency initialized with agents:")
        for agent in agency.agents:
            print(f"  - {agent.__class__.__name__}")
        print()

        # Create the migration task
        print("📝 Creating migration task...")

        migration_task = f"""
        {mission_prompt}

        ADDITIONAL CONTEXT:
        - Work autonomously without human intervention
        - Use all available agents and tools
        - Commit progress regularly
        - Self-heal any errors
        - Learn from successful patterns
        - Target completion in 8 hours

        Start immediately and work continuously until complete.
        """

        print("🏁 Starting autonomous migration...")
        print("This will run for approximately 8 hours")
        print("Progress will be logged to: logs/autonomous_type_migration.log")
        print()
        print("=" * 60)
        print("AUTONOMOUS EXECUTION BEGINNING NOW")
        print("=" * 60)
        print()

        # Run the Agency autonomously
        result = agency.run(migration_task)

        print()
        print("=" * 60)
        print("MISSION COMPLETE")
        print("=" * 60)
        print()
        print("Result:", result)

        return 0

    except Exception as e:
        print(f"❌ Error during autonomous execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Run with asyncio if needed
    exit_code = asyncio.run(main())
    sys.exit(exit_code)