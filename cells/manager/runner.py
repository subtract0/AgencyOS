
import argparse
import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure we can import from root
sys.path.insert(0, str(Path(__file__).parents[2]))

from cells.shared.lean_agent import LeanAgent, AgentConfig
from cells.action.tool_registry import ToolRegistry
from cells.shared.message_bus import MessageBus, async_message_bus
import asyncio

# Custom Handler to push logs to Bus
class BusLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        try:
             # Synchronous publish via ephemeral event loop or just fire-and-forget?
             # Since logging is sync, we have to run async code.
             # This is "expensive" but fine for MVP iteration speed (60s loop).
             
             async def _pub():
                 async with async_message_bus() as bus:
                     await bus.publish("logs", {
                         "source": f"Hive.{record.name}",
                         "message": log_entry,
                         "level": record.levelname
                     }, priority=1)
                     
             asyncio.run(_pub())
        except Exception:
            pass # Don't crash on log failure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentRunner")
logger.addHandler(BusLogHandler())

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    with open(manifest_path, 'r') as f:
        return json.load(f)

def setup_agent(manifest: Dict[str, Any]) -> LeanAgent:
    """Initialize agent based on manifest."""
    name = manifest.get("name", "UnknownAgent")
    instructions = manifest.get("instructions", "You are a helpful assistant.")
    model = manifest.get("model", "gpt-4o")
    requested_tools = manifest.get("tools", [])
    
    logger.info(f"Initializing {name} with model {model}...")
    
    config = AgentConfig(
        name=name,
        instructions=instructions,
        model=model
    )
    
    agent = LeanAgent(config)
    
    # Load Tools
    if requested_tools:
        logger.info(f"Scanning registry for tools: {requested_tools}")
        registry = ToolRegistry()
        all_tools = registry.scan_and_register()
        
        count = 0
        for tool_name in requested_tools:
            # Simple matching logic: precise name or substring
            # Ideal: ToolRegistry should support get_tool(name)
            # For now, we iterate.
            found = False
            for t in all_tools:
                if t.name == tool_name:
                    agent.register_tools(t)
                    count += 1
                    found = True
                    break
            if not found:
                logger.warning(f"Tool '{tool_name}' not found in registry.")
                
        logger.info(f"Registered {count} tools.")
        
    return agent

def run_loop(agent: LeanAgent, manifest: Dict[str, Any]):
    """Main execution loop."""
    schedule = manifest.get("schedule", None) # e.g., "every_5_seconds" or cron (v2)
    
    # Default behavior: If no schedule, run once and exit? 
    # Or 'daemon' mode where it waits for messages?
    # For Class 17 MVP, we support "Loop with Sleep".
    
    loop_interval = manifest.get("loop_interval_seconds", 60)
    
    logger.info(f"Starting loop (Interval: {loop_interval}s)")
    
    try:
        while True:
            # Check for 'task' or 'objective' in manifest?
            # Or does the agent determine its own goals based on instructions?
            # "Monitor the price..." implies active monitoring.
            
            logger.info("⚡ Waking up...")
            
            # We trigger the agent to "do its job"
            # We provide a generic "Wake up" prompt or the core instruction?
            prompt = "Current Status Check. Execute your primary function."
            
            response = agent.run(prompt)
            logger.info(f"🤖 Response: {response[:100]}...")
            
            logger.info(f"💤 Sleeping for {loop_interval}s...")
            time.sleep(loop_interval)
            
    except KeyboardInterrupt:
        logger.info("🛑 Stopping agent (KeyboardInterrupt).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgencyOS Generic Agent Runner")
    parser.add_argument("--manifest", required=True, help="Path to agent manifest JSON")
    args = parser.parse_args()
    
    try:
        if not os.path.exists(args.manifest):
            logger.error(f"Manifest not found: {args.manifest}")
            sys.exit(1)
            
        manifest = load_manifest(args.manifest)
        agent = setup_agent(manifest)
        run_loop(agent, manifest)
        
    except Exception as e:
        logger.critical(f"Agent Crash: {e}", exc_info=True)
        sys.exit(1)
