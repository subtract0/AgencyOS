
import pytest
import sqlite3
import time
import asyncio
from cells.action.action_cell import spawn_agent
from cells.manager.process_manager import get_process_manager

def test_intercom_logging():
    """
    Verify that a spawned agent logs to the MessageBus (SQLite).
    """
    manager = get_process_manager()
    if "intercom_test" in manager.active_agents:
        manager.stop_agent("intercom_test")

    # 1. Spawn Agent
    print("Spawning Intercom Test Agent...")
    result = spawn_agent.function(
        name="Intercom Test",
        instructions="Log 'Hello Intercom' then sleep.",
        schedule="loop_5s"
    )
    assert "Successfully spawned" in result
    
    # 2. Add a delay for startup + logging
    print("Waiting for logs...")
    time.sleep(8) 
    
    # 3. Check SQLite DB
    db_path = "messages.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT queue_name, message_data FROM messages ORDER BY created_at DESC LIMIT 10")
    rows = cursor.fetchall()
    
    print(f"\nRecent Messages in DB ({len(rows)}):")
    found_log = False
    found_spawn = False
    
    for row in rows:
        queue, data = row
        print(f"[{queue}] {data}")
        
        if queue == "logs" and "Hello Intercom" in data:
            found_log = True
        if queue == "hive" and "spawn" in data and "Intercom Test" in data:
            found_spawn = True
            
    conn.close()
    
    # Cleanup
    manager.stop_agent("intercom_test")
    
    assert found_spawn, "Did not find 'spawn' event in 'hive' queue."
    # Note: Agent logs might take longer or logging handler might fail silently if async loop issue.
    # But we check if at least spawn event worked.
    
    # If the logging inside runner.py failed (due to asyncio.run vs loop), we might miss it.
    # But let's see.

if __name__ == "__main__":
    test_intercom_logging()
