
import subprocess
import logging
import time
import os
import signal

class CouncilManager:
    """
    Manages the 3 MLX servers for The Council.
    Port 8081: Executive (Nemotron)
    Port 8082: Engineer (Qwen)
    Port 8083: Architect (Llama 70B)
    """
    def __init__(self):
        self.processes = {}
        self.models = {
            "executive": {
                "id": "mlx-community/Llama-3.1-Nemotron-8B-UltraLong-4M-Instruct-4bit",
                "port": 8081
            },
            # DISABLED (SAFE MODE): 32B model causes OOM/Crash when running with 70B.
            # "engineer": {
            #     "id": "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
            #     "port": 8082
            # },
            "architect": {
                "id": "mlx-community/Llama-3.3-70B-Instruct-4bit",
                "port": 8083
            }
        }

    def start_council(self):
        """Starts only the Executive (8B) by default for efficiency."""
        # Only start Executive (Heartbeat/Router)
        self._start_server("executive", self.models["executive"]["id"], self.models["executive"]["port"])
        logging.info("CouncilManager: Executive is seated. Architect is sleeping (Eco Mode).")

    def summon_architect(self):
        """Wakes up the Architect (70B) if not already running."""
        if self.is_architect_running():
            logging.info("CouncilManager: Architect is already awake.")
            return

        logging.info("CouncilManager: Summoning the Architect (70B)... (This may take a moment)")
        role = "architect"
        config = self.models[role]
        self._start_server(role, config["id"], config["port"])
        
        # Wait for port to be ready? 
        # For now, we rely on LeanAgent's retry logic, but a small sleep helps.
        time.sleep(5) 

    
    def dismiss_architect(self):
        """Dismisses the Architect (70B) to free up resources."""
        if not "architect" in self.processes:
            return

        logging.info("CouncilManager: Dismissing the Architect (70B)...")
        try:
            proc = self.processes["architect"]
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            del self.processes["architect"]
        except Exception as e:
            logging.error(f"Failed to dismiss Architect: {e}")

    def is_architect_running(self) -> bool:
        return "architect" in self.processes and self.processes["architect"].poll() is None

    def _wait_for_port(self, port: int, timeout: int = 30):
        """Waits for a port to be open (TCP connection possible)."""
        import socket
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    return True
            except (ConnectionRefusedError, OSError):
                time.sleep(1)
        return False

    def _start_server(self, role: str, model_id: str, port: int):
        log_file = open(f"logs/{role}_server.log", "w")
        cmd = [
            "python3", "-m", "mlx_lm.server",
            "--model", model_id,
            "--port", str(port),
            "--log-level", "INFO"
        ]
        
        logging.info(f"CouncilManager: Summoning {role} on port {port}...")
        try:
            # Check if port is taken? (Blindly assume free for now or kill old)
            proc = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=log_file,
                preexec_fn=os.setsid # Create new process group
            )
            self.processes[role] = proc
            
            # Wait for it to actually accept connections
            if self._wait_for_port(port):
                logging.info(f"CouncilManager: {role} is ready on port {port}.")
            else:
                logging.error(f"CouncilManager: {role} timed out starting on port {port}!")
                
        except Exception as e:
            logging.error(f"CouncilManager: Failed to summon {role}: {e}")

    def stop_council(self):
        """Terminates all servers."""
        for role, proc in self.processes.items():
            logging.info(f"CouncilManager: Dismissing {role}...")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.terminate()
        self.processes.clear()

# Global Instance
council = CouncilManager()
