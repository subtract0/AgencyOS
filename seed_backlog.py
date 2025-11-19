import uuid
import sys
import os

# Ensure we can import tools
sys.path.append(os.getcwd())

from tools.backlog_agent import BacklogStorage
from shared.models.backlog import Task, TaskType, TaskPriority, TaskStatus

storage = BacklogStorage()

tasks = [
    Task(
        id=str(uuid.uuid4()),
        title="ChiefArchitect Self-Improvement Audit (HGM)",
        description="Analyze recent agent logs and propose self-improvements based on the Huxley-Gödel Machine prompts. Identify weaknesses in stochasticity or context usage and create tickets to fix them.",
        task_type=TaskType.TECH_DEBT,
        priority=TaskPriority.P1,
        estimated_complexity=5,
        business_value=10
    ),
    Task(
         id=str(uuid.uuid4()),
         title="Refactor tools/bash.py for Type Safety",
         description="Ensure tools/bash.py complies with strict typing rules (no Dict[Any, Any]). Add Pydantic models where appropriate to satisfy Article VI of the Constitution.",
         task_type=TaskType.TECH_DEBT,
         priority=TaskPriority.P2,
         estimated_complexity=3,
         business_value=6
    )
]

print("Seeding backlog with tasks...")
for t in tasks:
    res = storage.add_task(t)
    if res.is_ok():
        print(f"✅ Added: {t.title}")
    else:
        print(f"❌ Failed: {t.title} - {res.unwrap_err()}")

