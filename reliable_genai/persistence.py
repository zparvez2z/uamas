from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ListingInput, PredictionResponse, ReviewDecision, ReviewQueueItem, ReviewTask


DEFAULT_DB_PATH = Path("data/uamas.db")
REVIEW_DECISION_STATUS = {
    "approve": "approved",
    "correct": "corrected",
    "reject": "rejected",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_db_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    return Path(os.getenv("UAMAS_DB_PATH", str(DEFAULT_DB_PATH)))


class SQLiteReviewStore:
    """SQLite persistence for listings, predictions, and human review tasks."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = resolve_db_path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with self._connect() as conn:
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
                """
            )

    def create_listing(self, listing: ListingInput) -> str:
        listing_id = self._new_id("lst")
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO listings (id, external_id, title, description, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (listing_id, listing.external_id, listing.title, listing.description, now),
            )
        return listing_id

    def create_prediction(self, listing_id: str, prediction: PredictionResponse) -> str:
        prediction_id = self._new_id("pred")
        now = utc_now()
        with self._connect() as conn:
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
                    now,
                ),
            )
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
        with self._connect() as conn:
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

    def record_review_decision(self, task_id: str, decision: ReviewDecision) -> ReviewTask:
        status = REVIEW_DECISION_STATUS[decision.action]
        now = utc_now()
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
                WHERE id = ?
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
            raise KeyError(f"review task not found: {task_id}")
        task = self.get_review_task(task_id)
        if task is None:
            raise KeyError(f"review task not found: {task_id}")
        return task

    def diagnostics(self) -> dict[str, object]:
        try:
            with self._connect() as conn:
                listing_count = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
                review_task_count = conn.execute("SELECT COUNT(*) FROM review_tasks").fetchone()[0]
                pending_review_task_count = conn.execute(
                    "SELECT COUNT(*) FROM review_tasks WHERE status = 'pending'"
                ).fetchone()[0]
            return {
                "available": True,
                "db_path": str(self.db_path),
                "listing_count": int(listing_count),
                "review_task_count": int(review_task_count),
                "pending_review_task_count": int(pending_review_task_count),
                "error": None,
            }
        except Exception as exc:
            return {
                "available": False,
                "db_path": str(self.db_path),
                "listing_count": 0,
                "review_task_count": 0,
                "pending_review_task_count": 0,
                "error": str(exc),
            }

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

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

    @classmethod
    def _queue_item_from_row(cls, row: sqlite3.Row) -> ReviewQueueItem:
        task = cls._task_from_row(row)
        return ReviewQueueItem(
            **task.model_dump(),
            title=row["title"],
            description=row["description"],
        )
