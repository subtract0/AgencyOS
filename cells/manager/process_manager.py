
import subprocess
import json
import os
import signal
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

logger = logging.getLogger("ProcessManager")

class ProcessManager:
    """
    Manages the lifecycle of agent subprocesses.
    The 'Hive Queen'.
    """
    
    def __init__(self, manifests_dir: str = "~/.agency/mobile_agents/manifests"):
        self.manifest_dir = Path(manifests_dir).expanduser()
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory registry of active processes
        # { "agent_id": { "proc": Popen, "manifest_path": str, "start_time": float } }
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        
        # Log directory
        self.log_dir = Path("~/.agency/mobile_agents/logs").expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def spawn_agent(self, manifest_data: Dict[str, Any]) -> str:
        """
        Create manifest and spawn process.
        Returns: agent_id
        """
        agent_id = manifest_data.get("id") or manifest_data.get("name").lower().replace(" ", "_")
        manifest_data["id"] = agent_id
        
        # Save manifest
        manifest_path = self.manifest_dir / f"{agent_id}.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
            
        # Start Process
        self._start_process(agent_id, manifest_path)
        return agent_id
        
    def _start_process(self, agent_id: str, manifest_path: Path):
        """Internal launcher."""
        if agent_id in self.active_agents:
            if self.active_agents[agent_id]["proc"].poll() is None:
                logger.warning(f"Agent {agent_id} is already running.")
                return

        # Prepare Command
        # Assumes running from project root
        project_root = Path(os.getcwd())
        runner_script = project_root / "cells" / "manager" / "runner.py"
        
        if not runner_script.exists():
            raise FileNotFoundError(f"Runner script not found: {runner_script}")

        # Logs
        stdout_log = open(self.log_dir / f"{agent_id}.out", "a")
        stderr_log = open(self.log_dir / f"{agent_id}.err", "a")
        
        logger.info(f"Spawning Agent {agent_id}...")
        
        # Spawn
        proc = subprocess.Popen(
            [sys.executable, str(runner_script), "--manifest", str(manifest_path)],
            stdout=stdout_log,
            stderr=stderr_log,
            text=True,
            cwd=str(project_root) # Ensure CWD is root for imports
        )
        
        self.active_agents[agent_id] = {
            "proc": proc,
            "manifest_path": str(manifest_path),
            "start_time": os.path.getmtime(manifest_path) # approximate
        }
        logger.info(f"Agent {agent_id} spawned (PID: {proc.pid})")

    def stop_agent(self, agent_id: str) -> bool:
        """Stop a running agent."""
        if agent_id not in self.active_agents:
            return False
            
        info = self.active_agents[agent_id]
        proc = info["proc"]
        
        if proc.poll() is None:
            logger.info(f"Stopping {agent_id} (PID: {proc.pid})...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                
        del self.active_agents[agent_id]
        return True

    def list_agents(self) -> List[Dict[str, Any]]:
        """Return status of all agents."""
        status_list = []
        
        # Check active memory first
        current_ids = list(self.active_agents.keys())
        
        for aid in current_ids:
            info = self.active_agents[aid]
            proc = info["proc"]
            ret_code = proc.poll()
            
            status = "Running" if ret_code is None else f"Exited ({ret_code})"
            
            # If exited, should we cleanup or restart?
            # For now, just report.
            
            status_list.append({
                "id": aid,
                "status": status,
                "pid": proc.pid
            })
            
        return status_list

    def stop_all(self):
        """Shutdown hook."""
        for aid in list(self.active_agents.keys()):
            self.stop_agent(aid)

# Global Instance?
# For now, this class is instantiated where needed or served by a daemon.
# Since AgencyOS ActionCell is persistent, it can hold an instance?
# Or clearer: The 'spawn_agent' tool instantiates this short-term?
# Better: This should be a persistent singleton or service.
# Ideally, Dashboard holds this? Or Governor?
# Let's make it a singleton in this module for now.

_manager_instance = None

def get_process_manager():
    global _manager_instance
    if not _manager_instance:
        _manager_instance = ProcessManager()
    return _manager_instance
