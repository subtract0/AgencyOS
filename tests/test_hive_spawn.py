
import pytest
import time
import os
from cells.manager.process_manager import get_process_manager
from cells.action.action_cell import spawn_agent

def test_spawn_greeter_agent():
    """
    Test spawning a simple 'Greeter' agent via the ProcessManager.
    """
    manager = get_process_manager()
    
    # Clean up any previous run
    if "greeter_test" in manager.active_agents:
        manager.stop_agent("greeter_test")
    
    # Call the tool function directly (simulating ActionCell)
    result = spawn_agent.function(
        name="Greeter Test",
        instructions="Your job is to log 'Hello Hive' every loop.",
        schedule="loop_5s"
    )
    
    print(f"\nSpawn Result: {result}")
    assert "Successfully spawned" in result
    
    # Verify it exists in manager
    active = manager.list_agents()
    print(f"Active Agents: {active}")
    
    greeter = next((a for a in active if "greeter_test" in a["id"]), None)
    assert greeter is not None
    assert greeter["status"] == "Running"
    
    # Wait for a log file to appear (Check both stdout and stderr)
    out_path = manager.log_dir / "greeter_test.out"
    err_path = manager.log_dir / "greeter_test.err"
    print(f"Watching logs: {out_path}, {err_path}")
    
    timeout = 10
    start = time.time()
    found_log = False
    
    while time.time() - start < timeout:
        content = ""
        if out_path.exists():
            content += out_path.read_text()
        if err_path.exists():
            content += err_path.read_text()
            
        if "Waking up" in content or "Starting loop" in content:
            print("✅ Found activity in log!")
            found_log = True
            break
        time.sleep(1)
        
    if not found_log:
        # Debug: check file content if exists
        if log_path.exists():
            print(f"Log content:\n{log_path.read_text()}")
        else:
            print("Log file never created.")
            
    assert found_log, "Agent did not produce logs within timeout."
    
    # Cleanup
    manager.stop_agent("greeter_test")
    assert "greeter_test" not in manager.active_agents

if __name__ == "__main__":
    test_spawn_greeter_agent()
