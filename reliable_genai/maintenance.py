from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping

from .persistence import SQLiteReviewStore


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


@dataclass(frozen=True)
class RetentionPolicy:
    workflow_retention_days: int = 90
    resolved_review_retention_days: int = 0
    batch_size: int = 500
    backup_enabled: bool = True
    backup_dir: Path = Path("data/backups")

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> RetentionPolicy:
        values = os.environ if environ is None else environ
        policy = cls(
            workflow_retention_days=int(
                values.get("WORKFLOW_RETENTION_DAYS", "90")
            ),
            resolved_review_retention_days=int(
                values.get("RESOLVED_REVIEW_RETENTION_DAYS", "0")
            ),
            batch_size=int(values.get("CLEANUP_BATCH_SIZE", "500")),
            backup_enabled=_parse_bool(
                values.get("CLEANUP_BACKUP_ENABLED"),
                default=True,
            ),
            backup_dir=Path(values.get("CLEANUP_BACKUP_DIR", "data/backups")),
        )
        policy.validate()
        return policy

    def validate(self) -> None:
        if self.workflow_retention_days <= 0:
            raise ValueError("WORKFLOW_RETENTION_DAYS must be positive")
        if self.resolved_review_retention_days != 0:
            raise ValueError(
                "resolved-review deletion is disabled until feedback exports "
                "can prove evidence was preserved; set "
                "RESOLVED_REVIEW_RETENTION_DAYS=0"
            )
        if self.batch_size <= 0:
            raise ValueError("CLEANUP_BATCH_SIZE must be positive")

    def cutoff(self, *, now: datetime) -> datetime:
        return now - timedelta(days=self.workflow_retention_days)


@dataclass(frozen=True)
class CleanupResult:
    maintenance_run_id: str
    dry_run: bool
    cutoff_at: str
    eligible_workflow_runs: int
    eligible_agent_runs: int
    workflow_runs_pruned: int
    agent_runs_deleted: int
    workflow_errors_cleared: int
    preserved_pending_reviews: int
    preserved_resolved_reviews: int
    backup_path: str | None
    vacuumed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class OperationalDataCleaner:
    def __init__(
        self,
        store: SQLiteReviewStore,
        policy: RetentionPolicy,
    ) -> None:
        self.store = store
        self.policy = policy

    def run(
        self,
        *,
        dry_run: bool = True,
        vacuum: bool = False,
        now: datetime | None = None,
    ) -> CleanupResult:
        effective_now = now or datetime.now(timezone.utc)
        if effective_now.tzinfo is None:
            raise ValueError("cleanup time must be timezone-aware")
        cutoff_at = self.policy.cutoff(now=effective_now).astimezone(
            timezone.utc
        ).isoformat()
        maintenance_id = self.store.start_maintenance_run(
            operation="workflow_history_cleanup",
            dry_run=dry_run,
            cutoff_at=cutoff_at,
        )
        details: dict[str, object] = {
            "eligible_workflow_runs": 0,
            "eligible_agent_runs": 0,
            "workflow_runs_pruned": 0,
            "agent_runs_deleted": 0,
            "workflow_errors_cleared": 0,
            "backup_path": None,
            "vacuumed": False,
        }
        try:
            preview = self.store.preview_workflow_history_cleanup(
                cutoff_at=cutoff_at
            )
            details.update(
                {
                    "eligible_workflow_runs": preview[
                        "eligible_workflow_runs"
                    ],
                    "eligible_agent_runs": preview["eligible_agent_runs"],
                    "preserved_pending_reviews": preview[
                        "preserved_pending_reviews"
                    ],
                    "preserved_resolved_reviews": preview[
                        "preserved_resolved_reviews"
                    ],
                }
            )
            if not dry_run:
                if (
                    self.policy.backup_enabled
                    and int(details["eligible_workflow_runs"]) > 0
                ):
                    backup_path = self._backup_path(
                        effective_now,
                        maintenance_id=maintenance_id,
                    )
                    self.store.backup_to(backup_path)
                    details["backup_path"] = str(backup_path)

                while True:
                    batch = self.store.prune_workflow_history_batch(
                        cutoff_at=cutoff_at,
                        batch_size=self.policy.batch_size,
                    )
                    details["workflow_runs_pruned"] = int(
                        details["workflow_runs_pruned"]
                    ) + batch["workflow_runs_pruned"]
                    details["agent_runs_deleted"] = int(
                        details["agent_runs_deleted"]
                    ) + batch["agent_runs_deleted"]
                    details["workflow_errors_cleared"] = int(
                        details["workflow_errors_cleared"]
                    ) + batch["workflow_errors_cleared"]
                    if batch["workflow_runs_pruned"] == 0:
                        break

                if vacuum:
                    self.store.vacuum()
                    details["vacuumed"] = True

            result = CleanupResult(
                maintenance_run_id=maintenance_id,
                dry_run=dry_run,
                cutoff_at=cutoff_at,
                eligible_workflow_runs=int(
                    details["eligible_workflow_runs"]
                ),
                eligible_agent_runs=int(details["eligible_agent_runs"]),
                workflow_runs_pruned=int(details["workflow_runs_pruned"]),
                agent_runs_deleted=int(details["agent_runs_deleted"]),
                workflow_errors_cleared=int(
                    details["workflow_errors_cleared"]
                ),
                preserved_pending_reviews=int(
                    details["preserved_pending_reviews"]
                ),
                preserved_resolved_reviews=int(
                    details["preserved_resolved_reviews"]
                ),
                backup_path=(
                    str(details["backup_path"])
                    if details["backup_path"] is not None
                    else None
                ),
                vacuumed=bool(details["vacuumed"]),
            )
            self.store.finish_maintenance_run(
                maintenance_id,
                status="completed",
                details=result.to_dict(),
            )
            return result
        except Exception as exc:
            try:
                self.store.finish_maintenance_run(
                    maintenance_id,
                    status="failed",
                    details=details,
                    error_message=str(exc),
                )
            except Exception:
                pass
            raise

    def _backup_path(self, now: datetime, *, maintenance_id: str) -> Path:
        timestamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return self.policy.backup_dir / (
            f"uamas-{timestamp}-{maintenance_id}.sqlite3"
        )
