import json
import uuid
from datetime import datetime
import os

# Path to backlog
backlog_path = "/Users/am/.agency/memories/agency_backlog/tasks.jsonl"

tasks = [
    {
        "id": str(uuid.uuid4()),
        "title": "ChiefArchitect Self-Improvement Audit (HGM)",
        "description": "Analyze recent agent logs and propose self-improvements based on the Huxley-Gödel Machine prompts. Identify weaknesses in stochasticity or context usage and create tickets to fix them.",
        "task_type": "tech_debt",
        "priority": "P1",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "estimated_complexity": 5,
        "business_value": 10,
        "cmp_related_clade_ids": [],
        "metadata": {"auto_seeded": True}
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Refactor tools/bash.py for Type Safety",
        "description": "Ensure tools/bash.py complies with strict typing rules (no Dict[Any, Any]). Add Pydantic models where appropriate to satisfy Article VI of the Constitution.",
        "task_type": "tech_debt",
        "priority": "P2",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "estimated_complexity": 3,
        "business_value": 6,
        "cmp_related_clade_ids": [],
        "metadata": {"auto_seeded": True}
    }
]

# Append to file
try:
    with open(backlog_path, "a") as f:
        for task in tasks:
            f.write(json.dumps(task) + "\n")
    print("Successfully seeded backlog manually.")
except Exception as e:
    print(f"Failed to seed backlog: {e}")

