from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from reliable_genai.maintenance import OperationalDataCleaner, RetentionPolicy
from reliable_genai.models import (
    AgentTrace,
    ListingInput,
    PredictionResponse,
    ProductAttributes,
    ReliabilityMeta,
    ReviewDecision,
)
from reliable_genai.persistence import SQLiteReviewStore
from reliable_genai.workflow_history import WorkflowRecorder


NOW = datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc)


def _prediction() -> PredictionResponse:
    return PredictionResponse(
        category_set=["Shoes"],
        attributes=ProductAttributes(
            brand="Acme",
            color="black",
            material="mesh",
            size="42",
        ),
        reliability=ReliabilityMeta(
            alpha=0.1,
            coverage_target=0.9,
            set_size=1,
            confidence=0.9,
            abstained=False,
            policy_action="set_output",
            llm_runtime="MOCK",
            llm_model="mock",
            classifier_runtime="ARTIFACT",
            coverage_threshold=0.9,
        ),
    )


def _age_workflow(
    db_path: Path,
    workflow_run_id: str,
    *,
    days_old: int,
) -> None:
    completed_at = (NOW - timedelta(days=days_old)).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            UPDATE workflow_runs
            SET completed_at = ?, started_at = ?
            WHERE id = ?
            """,
            (completed_at, completed_at, workflow_run_id),
        )


def _completed_workflow(
    store: SQLiteReviewStore,
    *,
    title: str,
    days_old: int,
    review_status: str | None = None,
    fail: bool = False,
) -> str:
    workflow = store.start_workflow_run(
        ListingInput(title=title, description="description"),
        graph_backend="langgraph",
    )
    recorder = WorkflowRecorder(store)
    recorder.run(
        workflow_run_id=workflow.id,
        agent_name="classifier_agent",
        operation=lambda: "ok",
        trace_builder=lambda _: AgentTrace(
            agent="classifier_agent",
            status="ok",
            output={"set_size": 1},
        ),
    )

    if review_status is not None:
        prediction_id = store.create_prediction_for_workflow(
            workflow.id,
            listing_id=workflow.listing_id,
            prediction=_prediction(),
        )
        task = store.create_review_task_for_workflow(
            workflow.id,
            listing_id=workflow.listing_id,
            prediction_id=prediction_id,
            reason="low_confidence",
            risk_level="high",
        )
        if review_status != "pending":
            action = {
                "approved": "approve",
                "corrected": "correct",
                "rejected": "reject",
            }[review_status]
            store.record_review_decision(
                task.id,
                ReviewDecision(action=action),
            )

    if fail:
        store.fail_workflow_run(
            workflow.id,
            error_type="RuntimeError",
            error_message="provider failure",
            duration_ms=2.0,
        )
    else:
        store.complete_workflow_run(
            workflow.id,
            decision=(
                "needs_human_review"
                if review_status is not None
                else "auto_accept"
            ),
            risk_level="high" if review_status is not None else "low",
            duration_ms=2.0,
        )
    _age_workflow(store.db_path, workflow.id, days_old=days_old)
    return workflow.id


def test_retention_policy_defaults_and_feedback_guard() -> None:
    policy = RetentionPolicy.from_env({})

    assert policy.workflow_retention_days == 90
    assert policy.resolved_review_retention_days == 0
    assert policy.batch_size == 500
    assert policy.backup_enabled is True

    with pytest.raises(ValueError, match="feedback exports"):
        RetentionPolicy.from_env({"RESOLVED_REVIEW_RETENTION_DAYS": "365"})


def test_cleanup_dry_run_preserves_all_operational_rows(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    old = _completed_workflow(
        store,
        title="old",
        days_old=120,
    )
    _completed_workflow(
        store,
        title="recent",
        days_old=10,
    )
    pending = _completed_workflow(
        store,
        title="pending",
        days_old=120,
        review_status="pending",
    )
    cleaner = OperationalDataCleaner(
        store,
        RetentionPolicy(
            workflow_retention_days=90,
            backup_enabled=False,
        ),
    )

    result = cleaner.run(dry_run=True, now=NOW)

    assert result.eligible_workflow_runs == 1
    assert result.eligible_agent_runs == 1
    assert result.workflow_runs_pruned == 0
    assert result.agent_runs_deleted == 0
    assert len(store.list_agent_runs(old)) == 1
    assert len(store.list_agent_runs(pending)) == 1
    audit = store.get_maintenance_run(result.maintenance_run_id)
    assert audit is not None
    assert audit["status"] == "completed"
    assert audit["dry_run"] is True


def test_cleanup_apply_backs_up_and_prunes_only_eligible_history(
    tmp_path: Path,
) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    completed = _completed_workflow(
        store,
        title="old completed",
        days_old=120,
    )
    failed = _completed_workflow(
        store,
        title="old failed",
        days_old=120,
        fail=True,
    )
    pending = _completed_workflow(
        store,
        title="old pending",
        days_old=120,
        review_status="pending",
    )
    resolved = _completed_workflow(
        store,
        title="old resolved",
        days_old=120,
        review_status="corrected",
    )
    backup_dir = tmp_path / "backups"
    cleaner = OperationalDataCleaner(
        store,
        RetentionPolicy(
            workflow_retention_days=90,
            batch_size=1,
            backup_enabled=True,
            backup_dir=backup_dir,
        ),
    )

    result = cleaner.run(dry_run=False, now=NOW)

    assert result.eligible_workflow_runs == 3
    assert result.workflow_runs_pruned == 3
    assert result.agent_runs_deleted == 3
    assert result.workflow_errors_cleared == 1
    assert result.preserved_pending_reviews == 1
    assert result.preserved_resolved_reviews == 1
    assert result.backup_path is not None
    assert Path(result.backup_path).exists()
    assert result.maintenance_run_id in Path(result.backup_path).name

    assert store.list_agent_runs(completed) == []
    assert store.list_agent_runs(failed) == []
    assert store.list_agent_runs(resolved) == []
    assert len(store.list_agent_runs(pending)) == 1
    assert store.get_workflow_run(completed).history_pruned_at is not None
    assert store.get_workflow_run(failed).error_message is None
    assert store.get_review_task(
        store.get_workflow_run(pending).review_task_id
    ).status == "pending"
    assert store.get_review_task(
        store.get_workflow_run(resolved).review_task_id
    ).status == "corrected"

    backup_store = SQLiteReviewStore(result.backup_path)
    assert len(backup_store.list_agent_runs(completed)) == 1
    assert backup_store.get_workflow_run(failed).error_message == "provider failure"

    second = cleaner.run(dry_run=False, now=NOW)
    assert second.eligible_workflow_runs == 0
    assert second.workflow_runs_pruned == 0
    assert second.agent_runs_deleted == 0
    assert second.backup_path is None
    assert len(list(backup_dir.glob("*.sqlite3"))) == 1


def test_cleanup_failure_is_audited(monkeypatch, tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    _completed_workflow(
        store,
        title="old",
        days_old=120,
    )
    cleaner = OperationalDataCleaner(
        store,
        RetentionPolicy(
            workflow_retention_days=90,
            backup_enabled=False,
        ),
    )

    def fail_prune(**_kwargs):
        raise RuntimeError("cleanup failed")

    monkeypatch.setattr(store, "prune_workflow_history_batch", fail_prune)
    with pytest.raises(RuntimeError, match="cleanup failed"):
        cleaner.run(dry_run=False, now=NOW)

    with sqlite3.connect(store.db_path) as conn:
        maintenance_id = conn.execute(
            "SELECT id FROM maintenance_runs ORDER BY started_at DESC LIMIT 1"
        ).fetchone()[0]
    audit = store.get_maintenance_run(maintenance_id)
    assert audit is not None
    assert audit["status"] == "failed"
    assert audit["error_message"] == "cleanup failed"
