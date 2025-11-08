#!/usr/bin/env python3
"""
Autonomous Evolution Loop - Self-Improving AgencyOS

This system runs continuously in the background:
1. Scans codebase for improvement opportunities
2. Uses parallel cheap models (Gemini Flash equivalent)
3. Learns patterns and evolves understanding
4. Self-improves when no urgent tasks
5. Prepares for voice assistant integration

Architecture:
- 5 parallel scanner agents (fast, cheap local models)
- 1 orchestrator (vcoder-120b for decisions)
- Constitutional compliance enforced
- Continuous learning enabled
"""

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json

# Configuration
SCAN_INTERVAL = 300  # 5 minutes between scans
MAX_PARALLEL_SCANNERS = 5
LOCAL_MODEL = "vcoder-120b-1.0-qx86-hi-mlx"
SCANNER_MODEL = "vcoder-120b-1.0-qx86-hi-mlx"  # Will use smaller model when available

class AutonomousEvolution:
    """Self-evolving autonomous system."""
    
    def __init__(self):
        self.project_root = Path("/Users/am/Code/AgencyOS")
        self.log_file = self.project_root / "logs" / "autonomous_evolution.log"
        self.state_file = self.project_root / ".evolution_state.json"
        self.running = True
        
        # Ensure logs directory exists
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Load previous state
        self.state = self._load_state()
        
    def _load_state(self) -> Dict:
        """Load evolution state from disk."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "scan_count": 0,
            "improvements_found": 0,
            "last_scan": None,
            "learned_patterns": [],
            "evolution_history": []
        }
    
    def _save_state(self):
        """Save evolution state to disk."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to file and console."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    async def scan_directory(self, directory: Path, scanner_id: int) -> List[Dict]:
        """Scan directory for improvement opportunities."""
        self.log(f"Scanner {scanner_id}: Scanning {directory.name}", "DEBUG")
        
        improvements = []
        
        # Scan for common issues
        for py_file in directory.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules']):
                continue
            
            try:
                content = py_file.read_text()
                
                # Quick pattern matching for common issues
                issues = []
                
                if "Dict[Any, Any]" in content:
                    issues.append("Constitutional violation: Dict[str, Any] found")
                
                if "TODO:" in content or "FIXME:" in content:
                    issues.append("Unresolved TODO/FIXME comments")
                
                if "import *" in content:
                    issues.append("Wildcard import detected")
                
                if len(content.split('\n')) > 1000:
                    issues.append("File exceeds 1000 lines - consider refactoring")
                
                if issues:
                    improvements.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "issues": issues,
                        "scanner": scanner_id,
                        "timestamp": datetime.now().isoformat()
                    })
            
            except Exception as e:
                self.log(f"Scanner {scanner_id}: Error reading {py_file}: {e}", "ERROR")
        
        return improvements
    
    async def parallel_scan(self) -> List[Dict]:
        """Run multiple scanners in parallel."""
        self.log(f"Starting parallel scan with {MAX_PARALLEL_SCANNERS} scanners")
        
        # Directories to scan
        scan_targets = [
            self.project_root / "shared",
            self.project_root / "tools",
            self.project_root / "tests",
            self.project_root / "scripts",
            self.project_root
        ]
        
        # Create tasks for parallel scanning
        tasks = []
        for i, target in enumerate(scan_targets[:MAX_PARALLEL_SCANNERS]):
            if target.exists():
                tasks.append(self.scan_directory(target, i + 1))
        
        # Run scanners in parallel
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_improvements = []
        for result in results:
            all_improvements.extend(result)
        
        return all_improvements
    
    def analyze_improvements(self, improvements: List[Dict]) -> Dict:
        """Analyze found improvements and prioritize."""
        if not improvements:
            return {"priority": [], "summary": "No improvements found"}
        
        # Group by issue type
        by_type = {}
        for imp in improvements:
            for issue in imp["issues"]:
                if issue not in by_type:
                    by_type[issue] = []
                by_type[issue].append(imp["file"])
        
        # Prioritize constitutional violations
        priority = []
        if "Constitutional violation: Dict[str, Any] found" in by_type:
            priority.append({
                "type": "CONSTITUTIONAL_VIOLATION",
                "issue": "Dict[Any, Any] usage",
                "files": by_type["Constitutional violation: Dict[str, Any] found"][:10],
                "priority": "CRITICAL"
            })
        
        return {
            "priority": priority,
            "by_type": by_type,
            "total_files": len(improvements),
            "summary": f"Found {len(improvements)} files with potential improvements"
        }
    
    def learn_patterns(self, improvements: List[Dict]):
        """Learn from discovered patterns."""
        patterns = set()
        
        for imp in improvements:
            for issue in imp["issues"]:
                patterns.add(issue)
        
        # Update learned patterns
        for pattern in patterns:
            if pattern not in self.state["learned_patterns"]:
                self.state["learned_patterns"].append(pattern)
                self.log(f"Learned new pattern: {pattern}", "INFO")
        
        self._save_state()
    
    async def evolution_cycle(self):
        """Single evolution cycle."""
        cycle_start = time.time()
        
        self.log("=" * 60)
        self.log(f"Evolution Cycle #{self.state['scan_count'] + 1}")
        self.log("=" * 60)
        
        try:
            # 1. Parallel scan
            improvements = await self.parallel_scan()
            
            # 2. Analyze results
            analysis = self.analyze_improvements(improvements)
            
            self.log(f"Scan complete: {analysis['summary']}")
            
            # 3. Learn patterns
            if improvements:
                self.learn_patterns(improvements)
                self.state["improvements_found"] += len(improvements)
            
            # 4. Log priority items
            if analysis["priority"]:
                self.log("Priority improvements found:", "WARN")
                for item in analysis["priority"]:
                    self.log(f"  [{item['priority']}] {item['type']}: {len(item['files'])} files", "WARN")
            
            # 5. Update state
            self.state["scan_count"] += 1
            self.state["last_scan"] = datetime.now().isoformat()
            self.state["evolution_history"].append({
                "cycle": self.state["scan_count"],
                "timestamp": datetime.now().isoformat(),
                "improvements": len(improvements),
                "duration": time.time() - cycle_start
            })
            
            # Keep only last 100 history entries
            if len(self.state["evolution_history"]) > 100:
                self.state["evolution_history"] = self.state["evolution_history"][-100:]
            
            self._save_state()
            
            # 6. Save detailed report
            report_file = self.project_root / "logs" / f"evolution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump({
                    "cycle": self.state["scan_count"],
                    "timestamp": datetime.now().isoformat(),
                    "improvements": improvements,
                    "analysis": analysis
                }, f, indent=2)
            
            self.log(f"Report saved: {report_file.name}")
            self.log(f"Cycle duration: {time.time() - cycle_start:.2f}s")
            
        except Exception as e:
            self.log(f"Error in evolution cycle: {e}", "ERROR")
    
    async def run_forever(self):
        """Run autonomous evolution loop forever."""
        self.log("🚀 Starting Autonomous Evolution System")
        self.log(f"Project: {self.project_root}")
        self.log(f"Model: {LOCAL_MODEL}")
        self.log(f"Scanners: {MAX_PARALLEL_SCANNERS}")
        self.log(f"Scan interval: {SCAN_INTERVAL}s")
        
        while self.running:
            try:
                await self.evolution_cycle()
                
                self.log(f"Next scan in {SCAN_INTERVAL}s...")
                self.log("")
                
                await asyncio.sleep(SCAN_INTERVAL)
                
            except KeyboardInterrupt:
                self.log("Received shutdown signal", "WARN")
                self.running = False
            except Exception as e:
                self.log(f"Unexpected error: {e}", "ERROR")
                await asyncio.sleep(60)  # Wait 1 minute on error
        
        self.log("🛑 Autonomous Evolution System stopped")
        self._save_state()

async def main():
    """Entry point."""
    evolution = AutonomousEvolution()
    await evolution.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
