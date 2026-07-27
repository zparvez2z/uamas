from __future__ import annotations

from time import perf_counter
from typing import Callable, TypeVar

from .models import AgentTrace
from .persistence import SQLiteReviewStore


T = TypeVar("T")


class WorkflowRecorder:
    """Persists bounded agent execution summaries around domain operations."""

    def __init__(self, store: SQLiteReviewStore) -> None:
        self.store = store

    def run(
        self,
        *,
        workflow_run_id: str,
        agent_name: str,
        operation: Callable[[], T],
        trace_builder: Callable[[T], AgentTrace],
        input_summary: dict[str, object] | None = None,
    ) -> tuple[T, AgentTrace]:
        started = perf_counter()
        agent_run = self.store.start_agent_run(
            workflow_run_id,
            agent_name=agent_name,
            input_summary=input_summary,
        )
        try:
            result = operation()
            trace = trace_builder(result)
            self.store.complete_agent_run(
                agent_run.id,
                status=self._durable_status(trace.status),
                output=trace.output,
                reason=trace.reason,
                duration_ms=(perf_counter() - started) * 1000,
            )
            return result, trace
        except Exception as exc:
            try:
                self.store.fail_agent_run(
                    agent_run.id,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    duration_ms=(perf_counter() - started) * 1000,
                )
            except Exception:
                pass
            raise

    def record_trace(
        self,
        *,
        workflow_run_id: str,
        trace: AgentTrace,
        input_summary: dict[str, object] | None = None,
    ) -> None:
        agent_run = self.store.start_agent_run(
            workflow_run_id,
            agent_name=trace.agent,
            input_summary=input_summary,
        )
        self.store.complete_agent_run(
            agent_run.id,
            status=self._durable_status(trace.status),
            output=trace.output,
            reason=trace.reason,
            duration_ms=0.0,
        )

    @staticmethod
    def _durable_status(trace_status: str) -> str:
        if trace_status == "degraded":
            return "degraded"
        if trace_status in {"disabled", "skipped"}:
            return "skipped"
        return "completed"
