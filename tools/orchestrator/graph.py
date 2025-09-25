from __future__ import annotations

import dataclasses
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

from shared.agent_context import AgentContext  # type: ignore

from .scheduler import OrchestrationPolicy, OrchestrationResult, TaskResult, TaskSpec
from .scheduler import run_parallel as _run_parallel


@dataclasses.dataclass
class TaskGraph:
    nodes: Dict[str, TaskSpec]
    edges: List[Tuple[str, str]]  # (upstream, downstream)

    def topo_order(self) -> List[str]:
        indeg: Dict[str, int] = defaultdict(int)
        for u, v in self.edges:
            indeg[v] += 1
            indeg.setdefault(u, 0)
        q = deque([n for n in self.nodes if indeg.get(n, 0) == 0])
        order: List[str] = []
        while q:
            u = q.popleft()
            order.append(u)
            for a, b in self.edges:
                if a == u:
                    indeg[b] -= 1
                    if indeg[b] == 0:
                        q.append(b)
        if len(order) != len(self.nodes):
            raise ValueError("Cycle detected in TaskGraph")
        return order


async def run_graph(ctx: AgentContext, graph: TaskGraph, policy: OrchestrationPolicy) -> OrchestrationResult:
    # Level-by-level execution based on indegree (simple backpressure)
    levels: List[List[str]] = _levels(graph)
    all_results: Dict[str, TaskResult] = {}
    for level in levels:
        specs = [graph.nodes[n] for n in level]
        res = await _run_parallel(ctx, specs, policy)
        for r in res.tasks:
            all_results[r.id] = r
        # Basic failure isolation: if any upstream failed, downstream can be skipped later
        # (MVP does not auto-skip; policy can extend this)
    # Aggregate metrics (MVP: wall_time approximated by sum of levels)
    # In practice, _run_parallel returns times; a richer aggregator can be added later.
    merged = {"summary": "dag_executed", "levels": len(levels)}
    return OrchestrationResult(tasks=list(all_results.values()), metrics={}, merged=merged)


def _levels(graph: TaskGraph) -> List[List[str]]:
    indeg: Dict[str, int] = defaultdict(int)
    adj: Dict[str, List[str]] = defaultdict(list)
    for u, v in graph.edges:
        adj[u].append(v)
        indeg[v] += 1
        indeg.setdefault(u, 0)
    level0 = [n for n in graph.nodes if indeg.get(n, 0) == 0]
    levels: List[List[str]] = []
    frontier = level0
    seen: Set[str] = set()
    while frontier:
        levels.append(frontier)
        seen.update(frontier)
        next_frontier: List[str] = []
        for u in frontier:
            for v in adj.get(u, []):
                indeg[v] -= 1
                if indeg[v] == 0:
                    next_frontier.append(v)
        frontier = next_frontier
    if len(seen) != len(graph.nodes):
        raise ValueError("Cycle detected in TaskGraph")
    return levels