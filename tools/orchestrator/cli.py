from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, Dict, List

from shared.agent_context import AgentContext  # type: ignore
from planner_agent.planner_agent import create_planner_agent  # type: ignore
from auditor_agent.auditor_agent import create_auditor_agent  # type: ignore
from learning_agent.learning_agent import create_learning_agent  # type: ignore

from .api import execute_parallel
from .scheduler import OrchestrationPolicy, TaskSpec


_AGENT_MAP = {
    "PlannerAgent": create_planner_agent,
    "AuditorAgent": create_auditor_agent,
    "LearningAgent": create_learning_agent,
}


def _parse_tasks(tasks_json: str) -> List[TaskSpec]:
    payload = json.loads(tasks_json)
    tasks: List[TaskSpec] = []
    for i, t in enumerate(payload):
        agent_name = t["agent"]
        prompt = t["prompt"]
        params: Dict[str, Any] = t.get("params", {})
        factory = _AGENT_MAP.get(agent_name)
        if not factory:
            raise SystemExit(f"Unknown agent: {agent_name}")
        tasks.append(TaskSpec(agent_factory=factory, prompt=prompt, params=params, id=t.get("id", f"task-{i}")))
    return tasks


async def _main_async(args: argparse.Namespace) -> int:
    ctx = AgentContext()
    tasks = _parse_tasks(args.tasks)
    policy = OrchestrationPolicy(max_concurrency=args.max_concurrency, timeout_s=args.timeout)
    res = await execute_parallel(ctx, tasks, policy)
    print(json.dumps({"tasks": [r.__dict__ for r in res.tasks], "metrics": res.metrics, "merged": res.merged}, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="orchestrator", description="Run agent tasks in parallel")
    parser.add_argument("run", nargs="?")
    parser.add_argument("--tasks", type=str, required=True, help="JSON list of task specs")
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=None)
    args = parser.parse_args()
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
