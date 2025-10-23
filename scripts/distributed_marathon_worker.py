#!/usr/bin/env python3
"""
DISTRIBUTED MARATHON WORKER - Multi-Machine Test Analyzer

Worker process that claims tasks from shared queue and analyzes tests
using local model (Qwen3-Coder-30b on MBP, GPT-OSS-20b on MBA).

Usage:
    # On MacBook Pro:
    python scripts/distributed_marathon_worker.py --machine mbp --model qwen3-coder:30b

    # On MacBook Air:
    python scripts/distributed_marathon_worker.py --machine mba --model gpt-oss:20b

Features:
- Atomic task claiming (no conflicts)
- Local model execution ($0 cost)
- Automatic retry on failures
- Graceful shutdown (Ctrl+C)
"""

import argparse
import json
import requests
import signal
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from meta_learning.task_queue import TaskQueue

# Distributed audit config
DISTRIBUTED_DIR = Path.home() / ".agency" / "marathon_distributed"
RESULTS_DIR = DISTRIBUTED_DIR / "results"
QUEUE_FILE = DISTRIBUTED_DIR / "task_queue.json"

# NECESSARY categories
NECESSARY_CATEGORIES = [
    "Normal", "Edge", "Cascading", "Essential",
    "Security", "Spec", "Accessibility", "Resilience", "Year-round"
]

class DistributedWorker:
    """Worker that processes test analysis tasks from distributed queue."""

    def __init__(self, machine: str, model: str, ollama_api: str = "http://localhost:11434/api/generate"):
        self.machine = machine
        self.model = model
        self.ollama_api = ollama_api
        self.queue = TaskQueue(queue_file=str(QUEUE_FILE))
        self.running = True
        self.agent_id = f"{machine}-worker-{int(time.time())}"
        self.tasks_completed = 0

        # Setup shutdown handler
        signal.signal(signal.SIGINT, self._handle_shutdown)

        # Ensure results directory exists
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        print(f"\n\n⚠️  Shutdown signal received. Finishing current task...")
        self.running = False

    def call_local_model(self, prompt: str, max_tokens: int = 1024) -> str:
        """Call local model with retry logic."""
        for attempt in range(3):
            try:
                response = requests.post(
                    self.ollama_api,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "num_predict": max_tokens,
                        }
                    },
                    timeout=180
                )

                if response.status_code == 200:
                    return response.json().get('response', '')

            except Exception as e:
                if attempt == 2:
                    return f"ERROR: {str(e)}"
                time.sleep(5 * (attempt + 1))

        return "ERROR: Max retries exceeded"

    def analyze_test(self, task_metadata: Dict) -> Dict:
        """Analyze a single test function."""
        test_file = Path(task_metadata["test_file"])
        test_name = task_metadata["test_name"]
        start_line = task_metadata["start_line"]
        end_line = task_metadata["end_line"]

        # Read test code
        try:
            lines = test_file.read_text().split('\n')
            test_code = '\n'.join(lines[start_line-1:end_line])
            lines_of_code = len([line for line in test_code.split('\n') if line.strip() and not line.strip().startswith('#')])
        except Exception as e:
            return {
                "error": str(e),
                "file": str(test_file),
                "name": test_name,
                "line_start": start_line,
                "line_end": end_line
            }

        # Call local model for analysis
        prompt = f"""Analyze this test function for NECESSARY pattern compliance.

Test: {test_name} (lines {start_line}-{end_line})
File: {test_file}

Code:
```python
{test_code}
```

NECESSARY Categories (9 total):
1. Normal: Standard usage paths
2. Edge: Boundary conditions
3. Cascading: Error propagation
4. Essential: Critical business logic
5. Security: Auth, injection, XSS
6. Spec: Acceptance criteria
7. Accessibility: Inclusive design
8. Resilience: Error recovery
9. Year-round: Time-based logic

Respond in this EXACT format:
COVERED: [comma-separated categories covered]
GAPS: [comma-separated categories missing]
ISSUES: [bullet list of quality issues]
PRIORITY: P0/P1/P2/P3
"""

        response = self.call_local_model(prompt, max_tokens=1024)

        # Parse response
        covered = self._parse_field(response, "COVERED:")
        gaps = self._parse_field(response, "GAPS:")
        issues = self._parse_field(response, "ISSUES:")
        priority_list = self._parse_field(response, "PRIORITY:")
        priority = priority_list[0] if priority_list else "P2"

        # Calculate complexity
        complexity = min(1.0, lines_of_code / 50.0)

        return {
            "file": str(test_file),
            "name": test_name,
            "line_start": start_line,
            "line_end": end_line,
            "lines_of_code": lines_of_code,
            "complexity_score": complexity,
            "necessary_coverage": covered,
            "necessary_gaps": gaps,
            "quality_issues": issues,
            "healing_priority": priority,
            "analysis_timestamp": datetime.now().isoformat(),
            "machine": self.machine,
            "model": self.model
        }

    def _parse_field(self, response: str, field_name: str) -> List[str]:
        """Parse field from model response (handles multi-line values)."""
        try:
            lines = response.split('\n')
            collecting = False
            results = []

            for line in lines:
                if line.strip().startswith(field_name):
                    value = line.replace(field_name, '').strip()
                    if value:
                        if ',' in value:
                            return [item.strip() for item in value.split(',') if item.strip()]
                        return [value] if value else []
                    else:
                        collecting = True
                        continue

                if collecting:
                    if line.strip().startswith(('COVERED:', 'GAPS:', 'ISSUES:', 'PRIORITY:', 'REASONING:')):
                        break
                    if line.strip():
                        clean_line = line.strip().lstrip('- ').lstrip('• ').lstrip('* ')
                        if clean_line:
                            results.append(clean_line)

            return results if results else []
        except:
            return []

    def run(self):
        """Main worker loop."""
        print("="*80)
        print(f"🤖 DISTRIBUTED MARATHON WORKER")
        print("="*80)
        print(f"Machine: {self.machine}")
        print(f"Model: {self.model}")
        print(f"Agent ID: {self.agent_id}")
        print(f"Queue: {QUEUE_FILE}")
        print()
        print("Waiting for tasks...")
        print("(Press Ctrl+C to stop gracefully)")
        print("="*80)
        print()

        while self.running:
            # Claim a task
            task = self.queue.claim_task(agent_id=self.agent_id, machine=self.machine)

            if task is None:
                # No tasks available
                status = self.queue.get_status()
                if status['pending'] == 0 and status['in_progress'] == 0:
                    # Queue is empty and nothing in progress
                    print("\n✅ All tasks complete! Exiting.")
                    break
                else:
                    # Wait for tasks to become available
                    time.sleep(5)
                    continue

            # Process task
            print(f"[{self.tasks_completed:4d}] Analyzing {task.metadata['test_name'][:50]:50s}", end='  ')

            try:
                # Analyze test
                result = self.analyze_test(task.metadata)

                # Save result
                result_file = RESULTS_DIR / f"{task.task_id}.json"
                with open(result_file, 'w') as f:
                    json.dump(result, f, indent=2)

                # Mark task complete
                self.queue.complete_task(task.task_id, success=True)

                self.tasks_completed += 1
                print("✅")

                # Rate limit (1 second between analyses)
                time.sleep(1)

            except Exception as e:
                print(f"❌ Error: {e}")
                # Mark task failed
                self.queue.fail_task(task.task_id, error=str(e))

        print()
        print("="*80)
        print(f"✅ WORKER COMPLETE")
        print("="*80)
        print(f"Machine: {self.machine}")
        print(f"Tasks Completed: {self.tasks_completed}")
        print(f"Results: {RESULTS_DIR}")
        print()
        print("Next step: Merge results on coordinator")
        print("  python scripts/distributed_marathon_coordinator.py --merge-results")
        print("="*80)

def main():
    parser = argparse.ArgumentParser(description="Distributed Marathon Worker")
    parser.add_argument("--machine", required=True, help="Machine identifier (mbp, mba, etc)")
    parser.add_argument("--model", required=True, help="Local model name (qwen3-coder:30b, gpt-oss:20b, etc)")
    parser.add_argument("--ollama-api", default="http://localhost:11434/api/generate", help="Ollama API endpoint")

    args = parser.parse_args()

    worker = DistributedWorker(
        machine=args.machine,
        model=args.model,
        ollama_api=args.ollama_api
    )

    worker.run()

if __name__ == "__main__":
    main()
