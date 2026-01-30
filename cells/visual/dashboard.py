
import os
import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
import asyncio
from typing import List
from pathlib import Path
import time

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2])) # /Users/am/Code/AgencyOS

app = FastAPI()

# Mount static for CSS/JS
app.mount("/static", StaticFiles(directory="cells/visual/static"), name="static")
templates = Jinja2Templates(directory="cells/visual/templates")

# State (In-Memory for now, later Redis/File)
SYSTEM_STATE = {
    "hand_status": "Idle",
    "eye_status": "Idle",
    "last_screenshot": None,
    "current_plan": [],
    "logs": []
}

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": SYSTEM_STATE})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive client commands
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "command":
                    query = msg.get("query")
                    # Push log that we heard them
                    SYSTEM_STATE["logs"].append(f"🧠 User: {query}")
                    await manager.broadcast({"type": "update", "data": SYSTEM_STATE})
                    
                    # Execute (Async)
                    asyncio.create_task(execute_command(query))
            except Exception as e:
                print(f"WS Error: {e}")

    except Exception:
        manager.disconnect(websocket)

async def execute_command(query: str):
    """Bridge to The Hand"""
    # For now, we spawn a subprocess calling action_cell.py
    # Ideally, this would use a message queue, but this is MVP Class 7.
    import subprocess
    SYSTEM_STATE["hand_status"] = "Thinking"
    await manager.broadcast({"type": "update", "data": SYSTEM_STATE})
    
    try:
        # We fire and forget, effectively.
        # But we want the output? ActionCell will push its own logs.
        cmd = ["python3", "cells/action/action_cell.py", query]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        # We don't wait for it to finish here to avoid blocking WS loop,
        # but ActionCell pushes updates via HTTP API.
    except Exception as e:
        SYSTEM_STATE["logs"].append(f"❌ Error starting Hand: {e}")
        await manager.broadcast({"type": "update", "data": SYSTEM_STATE})

# API Updates (Cells call this)
@app.post("/api/status/hand")
async def update_hand(status: dict):
    SYSTEM_STATE["hand_status"] = status.get("state", "Unknown")
    if "log" in status:
        SYSTEM_STATE["logs"].append(f"✋ {status['log']}")
    await manager.broadcast({"type": "update", "data": SYSTEM_STATE})
    return {"status": "ok"}

@app.post("/api/status/eye")
async def update_eye(status: dict):
    SYSTEM_STATE["eye_status"] = status.get("state", "Unknown")
    if "image_url" in status:
        SYSTEM_STATE["last_screenshot"] = status["image_url"] 
    await manager.broadcast({"type": "update", "data": SYSTEM_STATE})
    return {"status": "ok"}


# Compassion Engine (The Heart)
class CompassionEngine:
    def __init__(self):
        # Priority: Satechi Drive -> Local Logs
        self.sources = [
            Path("/Volumes/Satechi4TB/pain_points/raw"),
            Path("logs/knowledge_ingest/exports")
        ]
        self.check_interval = 10  # Seconds

    async def run(self):
        """Background loop to poll for compassion data."""
        while True:
            try:
                self._update_metrics()
            except Exception as e:
                print(f"Compassion Engine Error: {e}")
                SYSTEM_STATE["compassion_status"] = f"Error: {str(e)[:20]}"
            
            await asyncio.sleep(self.check_interval)

    def _update_metrics(self):
        # 1. Find valid source directory
        data_dir = None
        for source in self.sources:
            if source.exists():
                data_dir = source
                break
        
        if not data_dir:
            SYSTEM_STATE["compassion_status"] = "No Source"
            return
            
        # 2. Find latest export (goldminer_*.json OR pain_points_*.json)
        files = list(data_dir.glob("goldminer_*.json")) + list(data_dir.glob("pain_points_*.json"))
        if not files:
            SYSTEM_STATE["compassion_status"] = "No Data"
            return
            
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        
        # 3. Read Data (Handle large files gracefully?)
        # For MVP dashboard, we just load it. 
        # CAUTION: If file is 5MB+, this is fine. If 100MB+, might be slow.
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return # Skip if read fails (active write)
            
        if not isinstance(data, list):
            return

        # 4. Calculate Metrics
        enriched_items = [d for d in data if "llm_analysis" in d]
        if not enriched_items:
            SYSTEM_STATE["compassion_status"] = f"Scanning {len(data)} items..."
            # Still show total raw count?
            return

        total_suffering = sum(d["llm_analysis"].get("suffering_score", 0) for d in enriched_items)
        avg_suffering = total_suffering / len(enriched_items) if enriched_items else 0
        
        # 4. Find Distress Signals (Score >= 8)
        high_distress = [
            {
                "title": d.get("title", d.get("content", "")[:30] + "..."),
                "score": d["llm_analysis"].get("suffering_score", 0),
                "pain": d["llm_analysis"].get("primary_pain", "unknown")
            }
            for d in enriched_items 
            if d["llm_analysis"].get("suffering_score", 0) >= 8
        ]
        
        # Sort by score desc, take top 5
        high_distress.sort(key=lambda x: x["score"], reverse=True)
        
        # 5. Update State
        SYSTEM_STATE["compassion"] = {
            "avg_suffering": round(avg_suffering, 1),
            "total_analyzed": len(enriched_items),
            "distress_signals": high_distress[:5],
            "last_updated": time.strftime("%H:%M:%S")
        }
        SYSTEM_STATE["compassion_status"] = "Active"
        
        # Push update immediately
        asyncio.create_task(manager.broadcast({"type": "update", "data": SYSTEM_STATE}))

compassion_engine = CompassionEngine()

# Memory Monitor
class MemoryMonitor:
    def __init__(self):
        self.check_interval = 10
        # Lazy import to avoid circular dependency issues if any
        # But here we just need to read stats from the class interface if possible
        # Or more safely, just instantiate PatternMemory briefly or depend on file system
        
    async def run(self):
        while True:
            try:
                self._update_stats()
            except Exception as e:
                print(f"Memory Monitor Error: {e}")
            await asyncio.sleep(self.check_interval)

    def _update_stats(self):
        # We need to import here to ensure paths are set up
        import sys
        sys.path.append(os.getcwd())
        from agency_memory.pattern_memory import get_pattern_memory
        
        mem = get_pattern_memory()
        stats = mem.stats()
        
        SYSTEM_STATE["memory"] = {
            "total_patterns": stats["total_patterns"],
            "avg_confidence": f"{stats['avg_confidence']:.2f}",
            "top_tags": [f"{t[0]} ({t[1]})" for t in stats["top_tags"][:5]],
            "graph_nodes": stats.get("graph_nodes", 0),
            "graph_edges": stats.get("graph_edges", 0)
        }
        asyncio.create_task(manager.broadcast({"type": "update", "data": SYSTEM_STATE}))

memory_monitor = MemoryMonitor()

class HiveMonitor:
    def __init__(self):
        self.check_interval = 5
        
    async def run(self):
        while True:
            try:
                self._update_stats()
            except Exception as e:
                print(f"Hive Monitor Error: {e}")
            await asyncio.sleep(self.check_interval)
            
    def _update_stats(self):
        from cells.manager.process_manager import get_process_manager
        mgr = get_process_manager()
        agents = mgr.list_agents()
        
        SYSTEM_STATE["hive"] = {
            "active_count": len(agents),
            "agents": agents
        }
        asyncio.create_task(manager.broadcast({"type": "update", "data": SYSTEM_STATE}))

from cells.visual.bus_bridge import BusBridge

hive_monitor = HiveMonitor()
bus_bridge = BusBridge() # broadcast_func set later to avoid circular/init issues? 
# Actually we can pass manager.broadcast directly if manager is defined above.
# manager is defined on line 45.

# Maintenance Scheduler (The Immune System)
class MaintenanceScheduler:
    def __init__(self):
        # Run every 60 minutes in production, but for now let's say 30 mins
        self.interval = 1800 
        self.supervisor = None

    async def run(self):
        """Background loop to trigger maintenance."""
        print("🛡️ Maintenance Scheduler Online.")
        while True:
            await asyncio.sleep(60) # Initial delay
            try:
                # Lazy load to avoid startup circular imports or heavy blocking
                if not self.supervisor:
                    from cells.maintenance.supervisor import MaintenanceSupervisor
                    self.supervisor = MaintenanceSupervisor()
                
                # Run the cycle in a thread to not block the event loop
                SYSTEM_STATE["logs"].append("🛡️ Auto-Maintenance Started...")
                await manager.broadcast({"type": "update", "data": SYSTEM_STATE})
                
                report = await asyncio.to_thread(self.supervisor.run_cycle)
                
                # Log log LOG!
                SYSTEM_STATE["logs"].append(f"🛡️ Maintenance Report:\n{report}")
                SYSTEM_STATE["last_maintenance"] = time.strftime("%H:%M:%S")
                await manager.broadcast({"type": "update", "data": SYSTEM_STATE})
                
            except Exception as e:
                print(f"Maintenance Scheduler Error: {e}")
                SYSTEM_STATE["logs"].append(f"❌ Maintenance Error: {e}")
            
            await asyncio.sleep(self.interval)

maintenance_scheduler = MaintenanceScheduler()

@app.on_event("startup")
async def startup_event():
    # Link bridge to manager
    bus_bridge.broadcast_func = manager.broadcast
    
    asyncio.create_task(compassion_engine.run())
    asyncio.create_task(memory_monitor.run())
    asyncio.create_task(maintenance_scheduler.run())
    asyncio.create_task(hive_monitor.run())
    asyncio.create_task(bus_bridge.run())

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
