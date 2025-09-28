from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import time
import contextlib
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Literal, Optional, cast
from shared.type_definitions.json import JSONValue
from shared.models.orchestrator import ExecutionMetrics

from shared.agent_context import AgentContext  # type: ignore


BackoffType = Literal["fixed", "exp"]
FairnessType = Literal["round_robin", "shortest_first"]
CancellationType = Literal["cascading", "isolated"]


def _telemetry_enabled() -> bool:
    v = str(os.environ.get("AGENCY_TELEMETRY_ENABLED", "1")).strip().lower()
    return v not in {"0", "false", "no"}


def _telemetry_emit(event: Dict[str, JSONValue]) -> None:
    """Append a JSONL telemetry event. Fail-safe and non-blocking best-effort.

    Event schema (subset):
      {"ts": ISO8601Z, "type": "task_started"|"task_finished", "id": str,
       "agent": str, "attempt": int, "status"?: str, "started_at"?: float,
       "finished_at"?: float, "duration_s"?: float, "errors"?: [str]}
    """
    if not _telemetry_enabled():
        return
    try:
        # Compute path logs/telemetry/events-YYYYMMDD.jsonl relative to CWD
        base = os.path.join(os.getcwd(), "logs", "telemetry")
        os.makedirs(base, exist_ok=True)
        ts = datetime.now(timezone.utc)
        fname = os.path.join(base, f"events-{ts:%Y%m%d}.jsonl")
        event = dict(event)
        # Sanitize before writing
        try:
            from tools.telemetry.sanitize import redact_event  # type: ignore
            event = redact_event(event)
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to import telemetry sanitization: {e}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during telemetry sanitization: {e}")
        event["ts"] = ts.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        with open(fname, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except (OSError, IOError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to write telemetry event to {fname}: {e}")
        # Swallow I/O errors per spec but log them
        return
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.critical(f"Unexpected error in telemetry logging: {e}")
        return


@dataclasses.dataclass
class RetryPolicy:
    max_attempts: int = 1
    backoff: BackoffType = "fixed"
    base_delay_s: float = 0.1
    jitter: float = 0.0  # 0..1 proportion


@dataclasses.dataclass
class OrchestrationPolicy:
    max_concurrency: int = 4
    retry: RetryPolicy = dataclasses.field(default_factory=RetryPolicy)
    timeout_s: Optional[float] = None
    cost_budget: Optional[float] = None
    fairness: FairnessType = "round_robin"
    cancellation: CancellationType = "isolated"


@dataclasses.dataclass
class TaskSpec:
    agent_factory: Callable[[AgentContext], Any]
    prompt: str
    params: Optional[Dict[str, JSONValue]] = None
    id: Optional[str] = None


@dataclasses.dataclass
class TaskResult:
    id: str
    agent: str
    status: Literal["success", "failed", "canceled", "timeout"]
    started_at: float
    finished_at: float
    attempts: int
    artifacts: JSONValue | None
    errors: Optional[List[str]]


@dataclasses.dataclass
class OrchestrationResult:
    tasks: List[TaskResult]
    metrics: ExecutionMetrics
    merged: Dict[str, JSONValue]


class _Scheduler:
    def __init__(self, policy: OrchestrationPolicy) -> None:
        self._policy = policy
        self._sem = asyncio.Semaphore(policy.max_concurrency)
        self._run_id: Optional[str] = None

    async def _create_heartbeat_task(self, task_id: str, agent_name: str, started: float, attempts: int) -> tuple[asyncio.Task, asyncio.Event]:
        """Create and start a heartbeat task for telemetry."""
        stop_hb = asyncio.Event()
        hb_interval = float(os.environ.get("AGENCY_HEARTBEAT_INTERVAL_S", "5.0"))

        async def _heartbeat_loop() -> None:
            try:
                while not stop_hb.is_set():
                    _telemetry_emit(
                        {
                            "type": "heartbeat",
                            "run_id": self._run_id,
                            "id": task_id,
                            "agent": agent_name,
                            "attempt": attempts or 0,
                            "pid": os.getpid(),
                            "running_for_s": max(0.0, time.time() - started),
                        }
                    )
                    try:
                        await asyncio.wait_for(stop_hb.wait(), timeout=hb_interval)
                        break  # Stop event was set, exit loop
                    except asyncio.TimeoutError:
                        continue  # Timeout is expected, emit another heartbeat
            except (asyncio.CancelledError, Exception):
                # Handle cancellation and any other errors gracefully
                return

        hb_task = asyncio.create_task(_heartbeat_loop())
        return hb_task, stop_hb

    def _create_agent_safely(self, spec: TaskSpec, ctx: AgentContext, task_id: str, agent_name: str, started: float) -> Any:
        """Create agent with error handling, returning None if creation fails."""
        try:
            return spec.agent_factory(ctx)
        except Exception as e:
            # If agent creation fails, emit telemetry and raise
            finished = time.time()
            _telemetry_emit({
                "type": "task_finished",
                "id": task_id,
                "agent": agent_name,
                "attempt": 1,
                "status": "failed",
                "started_at": started,
                "finished_at": finished,
                "duration_s": max(0.0, finished - started),
                "errors": [f"Agent factory failed: {str(e)}"],
            })
            raise RuntimeError(f"Agent factory failed: {str(e)}") from e

    async def _execute_agent_attempt(self, agent: Any, spec: TaskSpec) -> Dict[str, JSONValue]:
        """Execute a single agent attempt, handling both sync and async agents."""
        import inspect
        params = spec.params or {}
        try:
            call = agent.run(spec.prompt, **params)
        except TypeError:
            call = agent.run(prompt=spec.prompt, **params)  # type: ignore
        if inspect.isawaitable(call):
            return await call  # type: ignore
        # If sync, defer to thread to avoid blocking loop
        return await asyncio.to_thread(lambda: call)

    def _extract_usage_and_model(self, artifacts: Dict[str, JSONValue]) -> tuple[Optional[JSONValue], Optional[str]]:
        """Extract usage and model information from agent artifacts."""
        usage = artifacts.get("usage")
        model = artifacts.get("model")

        # Some agents may nest response under 'response' or 'data'
        response_data = artifacts.get("response")
        if usage is None and isinstance(response_data, dict):
            usage = response_data.get("usage")
            model = response_data.get("model", model)

        data_data = artifacts.get("data")
        if usage is None and isinstance(data_data, dict):
            usage = data_data.get("usage")
            model = data_data.get("model", model)

        return usage, model

    def _emit_success_telemetry(self, task_id: str, agent_name: str, attempts: int, started: float, finished: float, usage: Optional[JSONValue], model: Optional[str]) -> None:
        """Emit telemetry for successful task completion."""
        ev: Dict[str, JSONValue] = {
            "type": "task_finished",
            "id": task_id,
            "agent": agent_name,
            "attempt": attempts,
            "status": "success",
            "started_at": started,
            "finished_at": finished,
            "duration_s": max(0.0, finished - started),
            "errors": None,
        }
        if usage is not None:
            ev["usage"] = usage
        if model is not None:
            ev["model"] = model
        _telemetry_emit(ev)

    def _create_success_result(self, task_id: str, agent_name: str, started: float, finished: float, attempts: int, artifacts: Dict[str, JSONValue]) -> TaskResult:
        """Create a successful TaskResult."""
        return TaskResult(
            id=task_id,
            agent=agent_name,
            status="success",
            started_at=started,
            finished_at=finished,
            attempts=attempts,
            artifacts=artifacts,
            errors=None,
        )

    def _handle_timeout(self, task_id: str, agent_name: str, attempts: int, started: float, errors: List[str]) -> TaskResult:
        """Handle timeout exception and create appropriate result."""
        finished = time.time()
        _telemetry_emit(
            {
                "type": "task_finished",
                "id": task_id,
                "agent": agent_name,
                "attempt": attempts,
                "status": "timeout",
                "started_at": started,
                "finished_at": finished,
                "duration_s": max(0.0, finished - started),
                "errors": ["timeout"],
            }
        )
        return TaskResult(
            id=task_id,
            agent=agent_name,
            status="timeout",
            started_at=started,
            finished_at=finished,
            attempts=attempts,
            artifacts=None,
            errors=errors or ["timeout"],
        )

    def _handle_failure(self, task_id: str, agent_name: str, attempts: int, started: float, errors: List[str]) -> TaskResult:
        """Handle final failure and create appropriate result."""
        finished = time.time()
        _telemetry_emit(
            {
                "type": "task_finished",
                "id": task_id,
                "agent": agent_name,
                "attempt": attempts,
                "status": "failed",
                "started_at": started,
                "finished_at": finished,
                "duration_s": max(0.0, finished - started),
                "errors": cast(JSONValue, errors),
            }
        )
        return TaskResult(
            id=task_id,
            agent=agent_name,
            status="failed",
            started_at=started,
            finished_at=finished,
            attempts=attempts,
            artifacts=None,
            errors=errors,
        )

    def _cleanup_heartbeat(self, hb_task: asyncio.Task, stop_hb: asyncio.Event) -> None:
        """Clean up heartbeat task and suppress exceptions."""
        try:
            stop_hb.set()
            if hb_task:
                hb_task.cancel()
                # Don't await cancelled heartbeat task - just suppress all exceptions
                with contextlib.suppress(Exception):
                    pass
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to cleanup heartbeat task: {e}")

    async def run_task(self, ctx: AgentContext, spec: TaskSpec) -> TaskResult:
        """Execute a task with retry logic, telemetry, and heartbeat monitoring."""
        started = time.time()
        attempts = 0
        errors: List[str] = []
        task_id = spec.id or f"task-{int(started*1000)}"
        agent_name = getattr(spec.agent_factory, "__name__", "agent")

        # Create heartbeat task
        hb_task, stop_hb = await self._create_heartbeat_task(task_id, agent_name, started, attempts)

        # Create agent once per task (not per retry attempt) - with error handling
        try:
            agent = self._create_agent_safely(spec, ctx, task_id, agent_name, started)
        except RuntimeError:
            # Agent creation failed, return appropriate result
            finished = time.time()
            return TaskResult(
                id=task_id,
                agent=agent_name,
                status="failed",
                started_at=started,
                finished_at=finished,
                attempts=1,
                artifacts=None,
                errors=["Agent factory failed"],
            )

        try:
            while True:
                attempts += 1
                attempt_started = time.time()
                _telemetry_emit(
                    {
                        "type": "task_started",
                        "id": task_id,
                        "agent": agent_name,
                        "attempt": attempts,
                        "started_at": attempt_started,
                    }
                )
                try:
                    if self._policy.timeout_s is not None:
                        coro = asyncio.wait_for(self._execute_agent_attempt(agent, spec), timeout=self._policy.timeout_s)
                    else:
                        coro = self._execute_agent_attempt(agent, spec)
                    artifacts = await coro
                    finished = time.time()

                    # Try to extract usage/model for cost accounting if present
                    usage, model = None, None
                    if isinstance(artifacts, dict):
                        usage, model = self._extract_usage_and_model(artifacts)

                    self._emit_success_telemetry(task_id, agent_name, attempts, started, finished, usage, model)
                    return self._create_success_result(task_id, agent_name, started, finished, attempts, artifacts)

                except asyncio.TimeoutError:
                    return self._handle_timeout(task_id, agent_name, attempts, started, errors)
                except Exception as e:  # noqa: BLE001
                    errors.append(str(e))
                    if attempts >= self._policy.retry.max_attempts:
                        return self._handle_failure(task_id, agent_name, attempts, started, errors)
                    delay = self._compute_backoff(attempts)
                    await asyncio.sleep(delay)
        finally:
            self._cleanup_heartbeat(hb_task, stop_hb)

    def _compute_backoff(self, attempt: int) -> float:
        """Compute backoff delay based on retry policy."""
        if self._policy.retry.backoff == "fixed":
            return self._policy.retry.base_delay_s
        # exp backoff
        return self._policy.retry.base_delay_s * (2 ** (attempt - 1))


async def run_parallel(ctx: AgentContext, specs: List[TaskSpec], policy: OrchestrationPolicy) -> OrchestrationResult:
    sched = _Scheduler(policy)
    started = time.time()

    # Emit an orchestration window marker with policy for resource utilization
    _telemetry_emit({
        "type": "orchestrator_started",
        "max_concurrency": policy.max_concurrency,
        "tasks": len(specs),
        "started_at": started,
    })

    async def _wrapped(spec: TaskSpec) -> TaskResult:
        async with sched._sem:
            return await sched.run_task(ctx, spec)

    results = await asyncio.gather(*[_wrapped(s) for s in specs])
    finished = time.time()
    metrics = ExecutionMetrics(
        wall_time=finished - started,
        tasks=len(results),
        additional={},
    )

    _telemetry_emit({
        "type": "orchestrator_finished",
        "finished_at": finished,
        "tasks": len(results),
    })

    return OrchestrationResult(tasks=results, metrics=metrics, merged={"summary": "not_merged_in_mvp"})
