from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import (
    AgentRun,
    ListingInput,
    PredictionResponse,
    ReviewDecision,
    ReviewQueueItem,
    ReviewTask,
    WorkflowRun,
    WorkflowRunDetail,
)


DEFAULT_DB_PATH = Path("data/uamas.db")
REVIEW_DECISION_STATUS = {
    "approve": "approved",
    "correct": "corrected",
    "reject": "rejected",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_db_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    return Path(os.getenv("UAMAS_DB_PATH", str(DEFAULT_DB_PATH)))


class SQLiteReviewStore:
    """SQLite persistence for listings, predictions, and human review tasks."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = resolve_db_path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.RLock()
        self.initialize()

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS listings (
                    id TEXT PRIMARY KEY,
                    external_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS predictions (
                    id TEXT PRIMARY KEY,
                    listing_id TEXT NOT NULL,
                    category_set_json TEXT NOT NULL,
                    attributes_json TEXT NOT NULL,
                    reliability_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(listing_id) REFERENCES listings(id)
                );

                CREATE TABLE IF NOT EXISTS review_tasks (
                    id TEXT PRIMARY KEY,
                    listing_id TEXT NOT NULL,
                    prediction_id TEXT,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    corrected_category TEXT,
                    corrected_attributes_json TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(listing_id) REFERENCES listings(id),
                    FOREIGN KEY(prediction_id) REFERENCES predictions(id)
                );

                CREATE INDEX IF NOT EXISTS idx_review_tasks_status
                    ON review_tasks(status, updated_at);

                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY,
                    listing_id TEXT NOT NULL,
                    prediction_id TEXT,
                    review_task_id TEXT,
                    status TEXT NOT NULL,
                    decision TEXT,
                    risk_level TEXT,
                    graph_backend TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_ms REAL,
                    error_type TEXT,
                    error_message TEXT,
                    history_pruned_at TEXT,
                    FOREIGN KEY(listing_id) REFERENCES listings(id),
                    FOREIGN KEY(prediction_id) REFERENCES predictions(id),
                    FOREIGN KEY(review_task_id) REFERENCES review_tasks(id)
                );

                CREATE TABLE IF NOT EXISTS agent_runs (
                    id TEXT PRIMARY KEY,
                    workflow_run_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    attempt INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_ms REAL,
                    input_summary_json TEXT NOT NULL DEFAULT '{}',
                    output_json TEXT NOT NULL DEFAULT '{}',
                    reason TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id),
                    UNIQUE(workflow_run_id, agent_name, attempt)
                );

                CREATE INDEX IF NOT EXISTS idx_workflow_runs_status_started
                    ON workflow_runs(status, started_at DESC);
                CREATE INDEX IF NOT EXISTS idx_agent_runs_workflow_started
                    ON agent_runs(workflow_run_id, started_at);
                CREATE INDEX IF NOT EXISTS idx_agent_runs_name_status
                    ON agent_runs(agent_name, status);

                CREATE TABLE IF NOT EXISTS maintenance_runs (
                    id TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    dry_run INTEGER NOT NULL,
                    cutoff_at TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    error_message TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_maintenance_runs_started
                    ON maintenance_runs(started_at DESC);

                CREATE TABLE IF NOT EXISTS feedback_export_batches (
                    id TEXT PRIMARY KEY,
                    schema_version TEXT NOT NULL,
                    source_fingerprint TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    output_directory TEXT NOT NULL,
                    selected_count INTEGER NOT NULL,
                    training_eligible_count INTEGER NOT NULL,
                    excluded_count INTEGER NOT NULL,
                    manifest_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS feedback_export_items (
                    review_task_id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL,
                    decision_updated_at TEXT NOT NULL,
                    FOREIGN KEY(review_task_id) REFERENCES review_tasks(id),
                    FOREIGN KEY(batch_id) REFERENCES feedback_export_batches(id)
                );

                CREATE INDEX IF NOT EXISTS idx_feedback_export_batches_completed
                    ON feedback_export_batches(completed_at DESC);
                """
            )
            workflow_columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(workflow_runs)").fetchall()
            }
            if "history_pruned_at" not in workflow_columns:
                conn.execute(
                    "ALTER TABLE workflow_runs ADD COLUMN history_pruned_at TEXT"
                )
        self._set_private_file_permissions(self.db_path)

    def create_listing(self, listing: ListingInput) -> str:
        listing_id = self._new_id("lst")
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO listings (id, external_id, title, description, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (listing_id, listing.external_id, listing.title, listing.description, now),
                )
        return listing_id

    def start_workflow_run(
        self,
        listing: ListingInput,
        *,
        graph_backend: str,
    ) -> WorkflowRun:
        listing_id = self._new_id("lst")
        workflow_run_id = self._new_id("run")
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO listings (id, external_id, title, description, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (listing_id, listing.external_id, listing.title, listing.description, now),
                )
                conn.execute(
                    """
                    INSERT INTO workflow_runs (
                        id,
                        listing_id,
                        status,
                        graph_backend,
                        started_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (workflow_run_id, listing_id, "running", graph_backend, now),
                )
        run = self.get_workflow_run(workflow_run_id)
        if run is None:
            raise RuntimeError(f"failed to create workflow run {workflow_run_id}")
        return run

    def start_agent_run(
        self,
        workflow_run_id: str,
        *,
        agent_name: str,
        input_summary: dict[str, object] | None = None,
        attempt: int = 1,
    ) -> AgentRun:
        agent_run_id = self._new_id("agt")
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_runs (
                        id,
                        workflow_run_id,
                        agent_name,
                        attempt,
                        status,
                        started_at,
                        input_summary_json,
                        output_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        agent_run_id,
                        workflow_run_id,
                        agent_name,
                        attempt,
                        "running",
                        now,
                        json.dumps(input_summary or {}),
                        "{}",
                    ),
                )
        run = self.get_agent_run(agent_run_id)
        if run is None:
            raise RuntimeError(f"failed to create agent run {agent_run_id}")
        return run

    def complete_agent_run(
        self,
        agent_run_id: str,
        *,
        status: str,
        output: dict[str, object] | None,
        reason: str | None,
        duration_ms: float,
    ) -> AgentRun:
        if status not in {"completed", "degraded", "skipped"}:
            raise ValueError(f"invalid completed agent status: {status}")
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    UPDATE agent_runs
                    SET
                        status = ?,
                        completed_at = ?,
                        duration_ms = ?,
                        output_json = ?,
                        reason = ?,
                        error_type = NULL,
                        error_message = NULL
                    WHERE id = ?
                    """,
                    (
                        status,
                        now,
                        round(max(duration_ms, 0.0), 3),
                        json.dumps(output or {}),
                        self._bounded_error(reason) if reason else None,
                        agent_run_id,
                    ),
                )
        if cursor.rowcount == 0:
            raise KeyError(f"agent run not found: {agent_run_id}")
        run = self.get_agent_run(agent_run_id)
        if run is None:
            raise KeyError(f"agent run not found: {agent_run_id}")
        return run

    def fail_agent_run(
        self,
        agent_run_id: str,
        *,
        error_type: str,
        error_message: str,
        duration_ms: float,
    ) -> AgentRun:
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    UPDATE agent_runs
                    SET
                        status = 'failed',
                        completed_at = ?,
                        duration_ms = ?,
                        error_type = ?,
                        error_message = ?
                    WHERE id = ?
                    """,
                    (
                        now,
                        round(max(duration_ms, 0.0), 3),
                        error_type,
                        self._bounded_error(error_message),
                        agent_run_id,
                    ),
                )
        if cursor.rowcount == 0:
            raise KeyError(f"agent run not found: {agent_run_id}")
        run = self.get_agent_run(agent_run_id)
        if run is None:
            raise KeyError(f"agent run not found: {agent_run_id}")
        return run

    def get_agent_run(self, agent_run_id: str) -> AgentRun | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM agent_runs WHERE id = ?",
                (agent_run_id,),
            ).fetchone()
        return self._agent_run_from_row(row) if row else None

    def list_agent_runs(self, workflow_run_id: str) -> list[AgentRun]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM agent_runs
                WHERE workflow_run_id = ?
                ORDER BY started_at, rowid
                """,
                (workflow_run_id,),
            ).fetchall()
        return [self._agent_run_from_row(row) for row in rows]

    def create_prediction(self, listing_id: str, prediction: PredictionResponse) -> str:
        prediction_id = self._new_id("pred")
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                self._insert_prediction(
                    conn,
                    prediction_id=prediction_id,
                    listing_id=listing_id,
                    prediction=prediction,
                    created_at=now,
                )
        return prediction_id

    def create_prediction_for_workflow(
        self,
        workflow_run_id: str,
        *,
        listing_id: str,
        prediction: PredictionResponse,
    ) -> str:
        prediction_id = self._new_id("pred")
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                self._insert_prediction(
                    conn,
                    prediction_id=prediction_id,
                    listing_id=listing_id,
                    prediction=prediction,
                    created_at=now,
                )
                cursor = conn.execute(
                    """
                    UPDATE workflow_runs
                    SET prediction_id = ?
                    WHERE id = ? AND listing_id = ?
                    """,
                    (prediction_id, workflow_run_id, listing_id),
                )
                if cursor.rowcount == 0:
                    raise KeyError(f"workflow run not found: {workflow_run_id}")
        return prediction_id

    def create_review_task(
        self,
        *,
        listing_id: str,
        prediction_id: str | None,
        reason: str,
        risk_level: str = "high",
    ) -> ReviewTask:
        task_id = self._new_id("rev")
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                self._insert_review_task(
                    conn,
                    task_id=task_id,
                    listing_id=listing_id,
                    prediction_id=prediction_id,
                    reason=reason,
                    risk_level=risk_level,
                    now=now,
                )
        task = self.get_review_task(task_id)
        if task is None:
            raise RuntimeError(f"failed to create review task {task_id}")
        return task

    def create_review_task_for_workflow(
        self,
        workflow_run_id: str,
        *,
        listing_id: str,
        prediction_id: str,
        reason: str,
        risk_level: str,
    ) -> ReviewTask:
        task_id = self._new_id("rev")
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                self._insert_review_task(
                    conn,
                    task_id=task_id,
                    listing_id=listing_id,
                    prediction_id=prediction_id,
                    reason=reason,
                    risk_level=risk_level,
                    now=now,
                )
                cursor = conn.execute(
                    """
                    UPDATE workflow_runs
                    SET review_task_id = ?
                    WHERE id = ? AND listing_id = ? AND prediction_id = ?
                    """,
                    (task_id, workflow_run_id, listing_id, prediction_id),
                )
                if cursor.rowcount == 0:
                    raise KeyError(f"workflow run not found: {workflow_run_id}")
        task = self.get_review_task(task_id)
        if task is None:
            raise RuntimeError(f"failed to create review task {task_id}")
        return task

    def get_review_task(self, task_id: str) -> ReviewTask | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM review_tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return self._task_from_row(row) if row else None

    def list_review_tasks(self, *, status: str | None = None, limit: int = 100) -> list[ReviewQueueItem]:
        if limit <= 0:
            raise ValueError("limit must be positive")

        query = """
            SELECT
                review_tasks.*,
                listings.title AS title,
                listings.description AS description
            FROM review_tasks
            JOIN listings ON listings.id = review_tasks.listing_id
        """
        params: tuple[Any, ...]
        if status is None:
            query += " ORDER BY review_tasks.updated_at DESC LIMIT ?"
            params = (limit,)
        else:
            query += " WHERE review_tasks.status = ? ORDER BY review_tasks.updated_at DESC LIMIT ?"
            params = (status, limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._queue_item_from_row(row) for row in rows]

    def complete_workflow_run(
        self,
        workflow_run_id: str,
        *,
        decision: str,
        risk_level: str,
        duration_ms: float,
    ) -> WorkflowRun:
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    UPDATE workflow_runs
                    SET
                        status = 'completed',
                        decision = ?,
                        risk_level = ?,
                        completed_at = ?,
                        duration_ms = ?,
                        error_type = NULL,
                        error_message = NULL
                    WHERE id = ?
                    """,
                    (
                        decision,
                        risk_level,
                        now,
                        round(max(duration_ms, 0.0), 3),
                        workflow_run_id,
                    ),
                )
        if cursor.rowcount == 0:
            raise KeyError(f"workflow run not found: {workflow_run_id}")
        run = self.get_workflow_run(workflow_run_id)
        if run is None:
            raise KeyError(f"workflow run not found: {workflow_run_id}")
        return run

    def fail_workflow_run(
        self,
        workflow_run_id: str,
        *,
        error_type: str,
        error_message: str,
        duration_ms: float,
    ) -> WorkflowRun:
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    UPDATE workflow_runs
                    SET
                        status = 'failed',
                        completed_at = ?,
                        duration_ms = ?,
                        error_type = ?,
                        error_message = ?
                    WHERE id = ?
                    """,
                    (
                        now,
                        round(max(duration_ms, 0.0), 3),
                        error_type,
                        self._bounded_error(error_message),
                        workflow_run_id,
                    ),
                )
        if cursor.rowcount == 0:
            raise KeyError(f"workflow run not found: {workflow_run_id}")
        run = self.get_workflow_run(workflow_run_id)
        if run is None:
            raise KeyError(f"workflow run not found: {workflow_run_id}")
        return run

    def get_workflow_run(self, workflow_run_id: str) -> WorkflowRun | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM workflow_runs WHERE id = ?",
                (workflow_run_id,),
            ).fetchone()
        return self._workflow_run_from_row(row) if row else None

    def get_workflow_run_detail(self, workflow_run_id: str) -> WorkflowRunDetail | None:
        run = self.get_workflow_run(workflow_run_id)
        if run is None:
            return None
        return WorkflowRunDetail(
            **run.model_dump(),
            agent_runs=self.list_agent_runs(workflow_run_id),
        )

    def list_workflow_runs(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[WorkflowRun]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if status is not None and status not in {"running", "completed", "failed"}:
            raise ValueError(f"invalid workflow status: {status}")

        query = "SELECT * FROM workflow_runs"
        params: tuple[Any, ...]
        if status is None:
            query += " ORDER BY started_at DESC LIMIT ?"
            params = (limit,)
        else:
            query += " WHERE status = ? ORDER BY started_at DESC LIMIT ?"
            params = (status, limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._workflow_run_from_row(row) for row in rows]

    def record_review_decision(self, task_id: str, decision: ReviewDecision) -> ReviewTask:
        status = REVIEW_DECISION_STATUS[decision.action]
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    UPDATE review_tasks
                    SET
                        status = ?,
                        corrected_category = ?,
                        corrected_attributes_json = ?,
                        notes = ?,
                        updated_at = ?
                    WHERE id = ? AND status = 'pending'
                    """,
                    (
                        status,
                        decision.corrected_category,
                        json.dumps(decision.corrected_attributes),
                        decision.notes,
                        now,
                        task_id,
                    ),
                )
                if cursor.rowcount == 0:
                    existing = conn.execute(
                        "SELECT status FROM review_tasks WHERE id = ?",
                        (task_id,),
                    ).fetchone()
                    if existing is None:
                        raise KeyError(f"review task not found: {task_id}")
                    raise ValueError(
                        f"review task is already resolved: {task_id} "
                        f"({existing['status']})"
                    )
        task = self.get_review_task(task_id)
        if task is None:
            raise KeyError(f"review task not found: {task_id}")
        return task

    def list_feedback_export_candidates(self) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    review_tasks.id AS review_task_id,
                    review_tasks.listing_id,
                    review_tasks.prediction_id,
                    review_tasks.status AS review_status,
                    review_tasks.reason AS review_reason,
                    review_tasks.risk_level AS review_risk_level,
                    review_tasks.corrected_category,
                    review_tasks.corrected_attributes_json,
                    review_tasks.created_at AS review_created_at,
                    review_tasks.updated_at AS review_updated_at,
                    listings.external_id,
                    listings.title,
                    listings.description,
                    listings.created_at AS listing_created_at,
                    predictions.category_set_json,
                    predictions.attributes_json,
                    predictions.reliability_json,
                    predictions.created_at AS prediction_created_at,
                    workflow_runs.id AS workflow_run_id,
                    workflow_runs.status AS workflow_status,
                    workflow_runs.decision AS workflow_decision,
                    workflow_runs.risk_level AS workflow_risk_level,
                    workflow_runs.graph_backend,
                    workflow_runs.started_at AS workflow_started_at,
                    workflow_runs.completed_at AS workflow_completed_at,
                    workflow_runs.history_pruned_at
                FROM review_tasks
                JOIN listings
                    ON listings.id = review_tasks.listing_id
                LEFT JOIN predictions
                    ON predictions.id = review_tasks.prediction_id
                LEFT JOIN workflow_runs
                    ON workflow_runs.id = (
                        SELECT candidate_workflow.id
                        FROM workflow_runs AS candidate_workflow
                        WHERE candidate_workflow.review_task_id = review_tasks.id
                        ORDER BY candidate_workflow.started_at DESC
                        LIMIT 1
                    )
                WHERE review_tasks.status IN (
                    'approved',
                    'corrected',
                    'rejected'
                )
                  AND NOT EXISTS (
                    SELECT 1
                    FROM feedback_export_items
                    WHERE feedback_export_items.review_task_id = review_tasks.id
                  )
                ORDER BY review_tasks.updated_at, review_tasks.id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def record_feedback_export_batch(
        self,
        *,
        batch_id: str,
        schema_version: str,
        source_fingerprint: str,
        output_directory: str,
        selected_count: int,
        training_eligible_count: int,
        excluded_count: int,
        manifest_sha256: str,
        review_items: list[tuple[str, str]],
    ) -> None:
        now = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO feedback_export_batches (
                        id,
                        schema_version,
                        source_fingerprint,
                        status,
                        output_directory,
                        selected_count,
                        training_eligible_count,
                        excluded_count,
                        manifest_sha256,
                        created_at,
                        completed_at
                    )
                    VALUES (?, ?, ?, 'completed', ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch_id,
                        schema_version,
                        source_fingerprint,
                        output_directory,
                        selected_count,
                        training_eligible_count,
                        excluded_count,
                        manifest_sha256,
                        now,
                        now,
                    ),
                )
                conn.executemany(
                    """
                    INSERT INTO feedback_export_items (
                        review_task_id,
                        batch_id,
                        decision_updated_at
                    )
                    VALUES (?, ?, ?)
                    """,
                    [
                        (review_task_id, batch_id, decision_updated_at)
                        for review_task_id, decision_updated_at in review_items
                    ],
                )

    def get_feedback_export_batch(
        self,
        batch_id: str,
    ) -> dict[str, object] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM feedback_export_batches WHERE id = ?",
                (batch_id,),
            ).fetchone()
        return dict(row) if row else None

    def start_maintenance_run(
        self,
        *,
        operation: str,
        dry_run: bool,
        cutoff_at: str,
    ) -> str:
        maintenance_id = self._new_id("mnt")
        with self._write_lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO maintenance_runs (
                        id,
                        operation,
                        status,
                        dry_run,
                        cutoff_at,
                        started_at,
                        details_json
                    )
                    VALUES (?, ?, 'running', ?, ?, ?, '{}')
                    """,
                    (
                        maintenance_id,
                        operation,
                        int(dry_run),
                        cutoff_at,
                        utc_now(),
                    ),
                )
        return maintenance_id

    def finish_maintenance_run(
        self,
        maintenance_id: str,
        *,
        status: str,
        details: dict[str, object],
        error_message: str | None = None,
    ) -> None:
        if status not in {"completed", "failed"}:
            raise ValueError(f"invalid maintenance status: {status}")
        with self._write_lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    UPDATE maintenance_runs
                    SET
                        status = ?,
                        completed_at = ?,
                        details_json = ?,
                        error_message = ?
                    WHERE id = ?
                    """,
                    (
                        status,
                        utc_now(),
                        json.dumps(details, sort_keys=True),
                        self._bounded_error(error_message) if error_message else None,
                        maintenance_id,
                    ),
                )
        if cursor.rowcount == 0:
            raise KeyError(f"maintenance run not found: {maintenance_id}")

    def get_maintenance_run(self, maintenance_id: str) -> dict[str, object] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM maintenance_runs WHERE id = ?",
                (maintenance_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "operation": row["operation"],
            "status": row["status"],
            "dry_run": bool(row["dry_run"]),
            "cutoff_at": row["cutoff_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "details": json.loads(row["details_json"]),
            "error_message": row["error_message"],
        }

    def preview_workflow_history_cleanup(self, *, cutoff_at: str) -> dict[str, int]:
        eligible_query = """
            FROM workflow_runs
            LEFT JOIN review_tasks
                ON review_tasks.id = workflow_runs.review_task_id
            WHERE workflow_runs.status IN ('completed', 'failed')
              AND workflow_runs.completed_at IS NOT NULL
              AND workflow_runs.completed_at < ?
              AND workflow_runs.history_pruned_at IS NULL
              AND (
                    review_tasks.id IS NULL
                    OR review_tasks.status != 'pending'
              )
        """
        with self._connect() as conn:
            workflow_count = int(
                conn.execute(
                    f"SELECT COUNT(*) {eligible_query}",
                    (cutoff_at,),
                ).fetchone()[0]
            )
            agent_count = int(
                conn.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM agent_runs
                    WHERE workflow_run_id IN (
                        SELECT workflow_runs.id
                        {eligible_query}
                    )
                    """,
                    (cutoff_at,),
                ).fetchone()[0]
            )
            pending_review_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM review_tasks WHERE status = 'pending'"
                ).fetchone()[0]
            )
            resolved_review_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM review_tasks WHERE status != 'pending'"
                ).fetchone()[0]
            )
        return {
            "eligible_workflow_runs": workflow_count,
            "eligible_agent_runs": agent_count,
            "preserved_pending_reviews": pending_review_count,
            "preserved_resolved_reviews": resolved_review_count,
        }

    def prune_workflow_history_batch(
        self,
        *,
        cutoff_at: str,
        batch_size: int,
    ) -> dict[str, int]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        pruned_at = utc_now()
        with self._write_lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT workflow_runs.id
                    FROM workflow_runs
                    LEFT JOIN review_tasks
                        ON review_tasks.id = workflow_runs.review_task_id
                    WHERE workflow_runs.status IN ('completed', 'failed')
                      AND workflow_runs.completed_at IS NOT NULL
                      AND workflow_runs.completed_at < ?
                      AND workflow_runs.history_pruned_at IS NULL
                      AND (
                            review_tasks.id IS NULL
                            OR review_tasks.status != 'pending'
                      )
                    ORDER BY workflow_runs.completed_at
                    LIMIT ?
                    """,
                    (cutoff_at, batch_size),
                ).fetchall()
                workflow_ids = [row["id"] for row in rows]
                if not workflow_ids:
                    return {
                        "workflow_runs_pruned": 0,
                        "agent_runs_deleted": 0,
                        "workflow_errors_cleared": 0,
                    }

                placeholders = ",".join("?" for _ in workflow_ids)
                agent_cursor = conn.execute(
                    f"""
                    DELETE FROM agent_runs
                    WHERE workflow_run_id IN ({placeholders})
                    """,
                    workflow_ids,
                )
                error_count = int(
                    conn.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM workflow_runs
                        WHERE id IN ({placeholders})
                          AND error_message IS NOT NULL
                        """,
                        workflow_ids,
                    ).fetchone()[0]
                )
                workflow_cursor = conn.execute(
                    f"""
                    UPDATE workflow_runs
                    SET history_pruned_at = ?, error_message = NULL
                    WHERE id IN ({placeholders})
                    """,
                    (pruned_at, *workflow_ids),
                )
        return {
            "workflow_runs_pruned": int(workflow_cursor.rowcount),
            "agent_runs_deleted": int(agent_cursor.rowcount),
            "workflow_errors_cleared": error_count,
        }

    def backup_to(self, destination: str | Path) -> Path:
        backup_path = Path(destination)
        if backup_path.resolve() == self.db_path.resolve():
            raise ValueError("backup destination must differ from the active database")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        with self._write_lock:
            source = self._connect()
            destination_conn = sqlite3.connect(backup_path)
            try:
                source.backup(destination_conn)
            finally:
                destination_conn.close()
                source.close()
        self._set_private_file_permissions(backup_path)
        return backup_path

    def vacuum(self) -> None:
        with self._write_lock:
            with self._connect() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.execute("VACUUM")

    def metrics(self) -> dict[str, object]:
        try:
            with self._connect() as conn:
                listing_count = int(conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0])
                prediction_count = int(conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0])
                review_task_count = int(conn.execute("SELECT COUNT(*) FROM review_tasks").fetchone()[0])
                status_rows = conn.execute(
                    "SELECT status, COUNT(*) AS count FROM review_tasks GROUP BY status"
                ).fetchall()
                reason_rows = conn.execute(
                    "SELECT reason, COUNT(*) AS count FROM review_tasks GROUP BY reason"
                ).fetchall()
                workflow_status_rows = conn.execute(
                    "SELECT status, COUNT(*) AS count FROM workflow_runs GROUP BY status"
                ).fetchall()
                workflow_decision_rows = conn.execute(
                    """
                    SELECT decision, COUNT(*) AS count
                    FROM workflow_runs
                    WHERE status = 'completed' AND decision IS NOT NULL
                    GROUP BY decision
                    """
                ).fetchall()
                workflow_duration_rows = conn.execute(
                    """
                    SELECT duration_ms
                    FROM workflow_runs
                    WHERE status = 'completed' AND duration_ms IS NOT NULL
                    ORDER BY duration_ms
                    """
                ).fetchall()
                agent_status_rows = conn.execute(
                    "SELECT status, COUNT(*) AS count FROM agent_runs GROUP BY status"
                ).fetchall()
                agent_duration_rows = conn.execute(
                    """
                    SELECT agent_name, AVG(duration_ms) AS average_duration_ms
                    FROM agent_runs
                    WHERE duration_ms IS NOT NULL
                    GROUP BY agent_name
                    """
                ).fetchall()
                legacy_listing_count = int(
                    conn.execute(
                        """
                        SELECT COUNT(*)
                        FROM listings
                        WHERE id NOT IN (SELECT listing_id FROM workflow_runs)
                        """
                    ).fetchone()[0]
                )
                legacy_review_count = int(
                    conn.execute(
                        """
                        SELECT COUNT(*)
                        FROM review_tasks
                        WHERE listing_id NOT IN (SELECT listing_id FROM workflow_runs)
                        """
                    ).fetchone()[0]
                )

            status_counts = {row["status"]: int(row["count"]) for row in status_rows}
            reason_counts = {row["reason"]: int(row["count"]) for row in reason_rows}
            workflow_status_counts = {
                row["status"]: int(row["count"]) for row in workflow_status_rows
            }
            workflow_decision_counts = {
                row["decision"]: int(row["count"]) for row in workflow_decision_rows
            }
            agent_status_counts = {
                row["status"]: int(row["count"]) for row in agent_status_rows
            }
            workflow_run_count = sum(workflow_status_counts.values())
            completed_workflow_count = workflow_status_counts.get("completed", 0)
            durations = [float(row["duration_ms"]) for row in workflow_duration_rows]
            average_workflow_duration = (
                round(sum(durations) / len(durations), 3) if durations else 0.0
            )
            p95_index = max(math.ceil(0.95 * len(durations)) - 1, 0)
            p95_workflow_duration = round(durations[p95_index], 3) if durations else 0.0
            average_agent_duration = {
                row["agent_name"]: round(float(row["average_duration_ms"]), 3)
                for row in agent_duration_rows
            }
            auto_accept_count = workflow_decision_counts.get("auto_accept", 0) + max(
                legacy_listing_count - legacy_review_count,
                0,
            )
            needs_human_review_count = workflow_decision_counts.get(
                "needs_human_review",
                0,
            ) + legacy_review_count
            decided_count = auto_accept_count + needs_human_review_count
            corrected_count = status_counts.get("corrected", 0)
            return {
                "available": True,
                "db_path": str(self.db_path),
                "error": None,
                "listing_count": listing_count,
                "prediction_count": prediction_count,
                "review_task_count": review_task_count,
                "review_status_counts": status_counts,
                "review_reason_counts": reason_counts,
                "pending_review_task_count": status_counts.get("pending", 0),
                "approved_review_task_count": status_counts.get("approved", 0),
                "corrected_review_task_count": corrected_count,
                "rejected_review_task_count": status_counts.get("rejected", 0),
                "auto_accept_count": auto_accept_count,
                "needs_human_review_count": needs_human_review_count,
                "auto_accept_rate": round(auto_accept_count / decided_count, 3) if decided_count else 0.0,
                "human_review_rate": (
                    round(needs_human_review_count / decided_count, 3) if decided_count else 0.0
                ),
                "correction_rate": round(corrected_count / review_task_count, 3) if review_task_count else 0.0,
                "workflow_run_count": workflow_run_count,
                "completed_workflow_run_count": completed_workflow_count,
                "failed_workflow_run_count": workflow_status_counts.get("failed", 0),
                "running_workflow_run_count": workflow_status_counts.get("running", 0),
                "workflow_success_rate": (
                    round(completed_workflow_count / workflow_run_count, 3)
                    if workflow_run_count
                    else 0.0
                ),
                "average_workflow_duration_ms": average_workflow_duration,
                "p95_workflow_duration_ms": p95_workflow_duration,
                "degraded_agent_run_count": agent_status_counts.get("degraded", 0),
                "failed_agent_run_count": agent_status_counts.get("failed", 0),
                "average_agent_duration_ms": average_agent_duration,
            }
        except Exception as exc:
            return {
                "available": False,
                "db_path": str(self.db_path),
                "error": str(exc),
                "listing_count": 0,
                "prediction_count": 0,
                "review_task_count": 0,
                "review_status_counts": {},
                "review_reason_counts": {},
                "pending_review_task_count": 0,
                "approved_review_task_count": 0,
                "corrected_review_task_count": 0,
                "rejected_review_task_count": 0,
                "auto_accept_count": 0,
                "needs_human_review_count": 0,
                "auto_accept_rate": 0.0,
                "human_review_rate": 0.0,
                "correction_rate": 0.0,
                "workflow_run_count": 0,
                "completed_workflow_run_count": 0,
                "failed_workflow_run_count": 0,
                "running_workflow_run_count": 0,
                "workflow_success_rate": 0.0,
                "average_workflow_duration_ms": 0.0,
                "p95_workflow_duration_ms": 0.0,
                "degraded_agent_run_count": 0,
                "failed_agent_run_count": 0,
                "average_agent_duration_ms": {},
            }

    def diagnostics(self) -> dict[str, object]:
        try:
            metrics = self.metrics()
            return {
                "available": metrics["available"],
                "db_path": metrics["db_path"],
                "listing_count": metrics["listing_count"],
                "review_task_count": metrics["review_task_count"],
                "pending_review_task_count": metrics["pending_review_task_count"],
                "workflow_run_count": metrics["workflow_run_count"],
                "failed_workflow_run_count": metrics["failed_workflow_run_count"],
                "error": metrics["error"],
            }
        except Exception as exc:
            return {
                "available": False,
                "db_path": str(self.db_path),
                "listing_count": 0,
                "review_task_count": 0,
                "pending_review_task_count": 0,
                "workflow_run_count": 0,
                "failed_workflow_run_count": 0,
                "error": str(exc),
            }

    @staticmethod
    def _insert_prediction(
        conn: sqlite3.Connection,
        *,
        prediction_id: str,
        listing_id: str,
        prediction: PredictionResponse,
        created_at: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO predictions (
                id,
                listing_id,
                category_set_json,
                attributes_json,
                reliability_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                prediction_id,
                listing_id,
                json.dumps(prediction.category_set),
                prediction.attributes.model_dump_json(),
                prediction.reliability.model_dump_json(),
                created_at,
            ),
        )

    @staticmethod
    def _insert_review_task(
        conn: sqlite3.Connection,
        *,
        task_id: str,
        listing_id: str,
        prediction_id: str | None,
        reason: str,
        risk_level: str,
        now: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO review_tasks (
                id,
                listing_id,
                prediction_id,
                status,
                reason,
                risk_level,
                corrected_category,
                corrected_attributes_json,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                listing_id,
                prediction_id,
                "pending",
                reason,
                risk_level,
                None,
                "{}",
                None,
                now,
                now,
            ),
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

    @staticmethod
    def _bounded_error(message: str, limit: int = 1000) -> str:
        sanitized = message
        for env_name in (
            "GITHUB_TOKEN",
            "GITHUB_MODELS_API_KEY",
            "UAMAS_ADMIN_TOKEN",
            "UAMAS_API_TOKEN",
            "UAMAS_SESSION_SECRET",
        ):
            secret = os.getenv(env_name, "")
            if secret:
                sanitized = sanitized.replace(secret, "[REDACTED]")
        return sanitized[:limit]

    @staticmethod
    def _set_private_file_permissions(path: Path) -> None:
        try:
            path.chmod(0o600)
        except OSError:
            pass

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> ReviewTask:
        return ReviewTask(
            id=row["id"],
            listing_id=row["listing_id"],
            prediction_id=row["prediction_id"],
            status=row["status"],
            reason=row["reason"],
            risk_level=row["risk_level"],
            corrected_category=row["corrected_category"],
            corrected_attributes=json.loads(row["corrected_attributes_json"]),
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _workflow_run_from_row(row: sqlite3.Row) -> WorkflowRun:
        return WorkflowRun(
            id=row["id"],
            listing_id=row["listing_id"],
            prediction_id=row["prediction_id"],
            review_task_id=row["review_task_id"],
            status=row["status"],
            decision=row["decision"],
            risk_level=row["risk_level"],
            graph_backend=row["graph_backend"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            duration_ms=row["duration_ms"],
            error_type=row["error_type"],
            error_message=row["error_message"],
            history_pruned_at=row["history_pruned_at"],
        )

    @staticmethod
    def _agent_run_from_row(row: sqlite3.Row) -> AgentRun:
        return AgentRun(
            id=row["id"],
            workflow_run_id=row["workflow_run_id"],
            agent_name=row["agent_name"],
            attempt=row["attempt"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            duration_ms=row["duration_ms"],
            input_summary=json.loads(row["input_summary_json"]),
            output=json.loads(row["output_json"]),
            reason=row["reason"],
            error_type=row["error_type"],
            error_message=row["error_message"],
        )

    @classmethod
    def _queue_item_from_row(cls, row: sqlite3.Row) -> ReviewQueueItem:
        task = cls._task_from_row(row)
        return ReviewQueueItem(
            **task.model_dump(),
            title=row["title"],
            description=row["description"],
        )
