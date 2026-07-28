from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .persistence import SQLiteReviewStore
from .pipeline import ReliabilityPipeline


FEEDBACK_SCHEMA_VERSION = "1.0"
DEFAULT_FEEDBACK_OUTPUT_DIR = Path("data/feedback")
STATUS_ACTIONS = {
    "approved": "approve",
    "corrected": "correct",
    "rejected": "reject",
}


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _round_rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 3) if denominator else 0.0


@dataclass(frozen=True)
class FeedbackExportResult:
    applied: bool
    batch_id: str | None
    source_fingerprint: str | None
    output_directory: str | None
    selected_count: int
    training_eligible_count: int
    excluded_count: int
    summary: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class FeedbackExporter:
    def __init__(
        self,
        store: SQLiteReviewStore,
        *,
        output_root: str | Path = DEFAULT_FEEDBACK_OUTPUT_DIR,
        labels: Sequence[str] = tuple(ReliabilityPipeline.LABELS),
    ) -> None:
        self.store = store
        self.output_root = Path(output_root)
        self.labels = tuple(labels)
        self.label_set = frozenset(labels)

    def run(self, *, apply: bool = False) -> FeedbackExportResult:
        candidates = self.store.list_feedback_export_candidates()
        if not candidates:
            return FeedbackExportResult(
                applied=apply,
                batch_id=None,
                source_fingerprint=None,
                output_directory=None,
                selected_count=0,
                training_eligible_count=0,
                excluded_count=0,
                summary=self._empty_summary(),
            )

        evidence = [self._build_evidence(row) for row in candidates]
        fingerprint_payload = {
            "schema_version": FEEDBACK_SCHEMA_VERSION,
            "evidence": evidence,
        }
        source_fingerprint = _sha256_bytes(
            _canonical_json(fingerprint_payload).encode("utf-8")
        )
        batch_id = f"fb_{source_fingerprint[:16]}"
        output_directory = self.output_root / batch_id
        training_examples = [
            self._training_example(record)
            for record in evidence
            if record["validation"]["training_eligible"]
        ]
        excluded_records = [
            record
            for record in evidence
            if not record["validation"]["training_eligible"]
        ]
        summary = self._build_summary(
            batch_id=batch_id,
            evidence=evidence,
        )

        if apply:
            manifest_sha256 = self._write_artifacts(
                output_directory=output_directory,
                batch_id=batch_id,
                source_fingerprint=source_fingerprint,
                evidence=evidence,
                training_examples=training_examples,
                excluded_records=excluded_records,
                summary=summary,
            )
            self.store.record_feedback_export_batch(
                batch_id=batch_id,
                schema_version=FEEDBACK_SCHEMA_VERSION,
                source_fingerprint=source_fingerprint,
                output_directory=str(output_directory),
                selected_count=len(evidence),
                training_eligible_count=len(training_examples),
                excluded_count=len(excluded_records),
                manifest_sha256=manifest_sha256,
                review_items=[
                    (
                        str(record["review"]["task_id"]),
                        str(record["review"]["decided_at"]),
                    )
                    for record in evidence
                ],
            )

        return FeedbackExportResult(
            applied=apply,
            batch_id=batch_id,
            source_fingerprint=source_fingerprint,
            output_directory=str(output_directory),
            selected_count=len(evidence),
            training_eligible_count=len(training_examples),
            excluded_count=len(excluded_records),
            summary=summary,
        )

    def _build_evidence(
        self,
        row: dict[str, object],
    ) -> dict[str, object]:
        validation_errors: list[str] = []
        category_set = self._parse_json(
            row.get("category_set_json"),
            field="category_set",
            expected_type=list,
            errors=validation_errors,
        )
        attributes = self._parse_json(
            row.get("attributes_json"),
            field="attributes",
            expected_type=dict,
            errors=validation_errors,
        )
        reliability = self._parse_json(
            row.get("reliability_json"),
            field="reliability",
            expected_type=dict,
            errors=validation_errors,
        )
        corrected_attributes = self._parse_json(
            row.get("corrected_attributes_json"),
            field="corrected_attributes",
            expected_type=dict,
            errors=validation_errors,
        )

        prediction_id = row.get("prediction_id")
        workflow_run_id = row.get("workflow_run_id")
        if not prediction_id:
            validation_errors.append("missing_prediction")
        if not workflow_run_id:
            validation_errors.append("missing_workflow")

        valid_category_set: list[str] = []
        if isinstance(category_set, list):
            if not all(isinstance(label, str) for label in category_set):
                validation_errors.append("invalid_category_set")
            else:
                valid_category_set = list(category_set)
                if any(label not in self.label_set for label in valid_category_set):
                    validation_errors.append("unknown_predicted_category")

        review_status = str(row["review_status"])
        action = STATUS_ACTIONS[review_status]
        corrected_category = row.get("corrected_category")
        exclusion_reason: str | None = None
        effective_category: str | None = None

        if review_status == "corrected":
            if not corrected_category:
                validation_errors.append("missing_corrected_category")
            elif corrected_category not in self.label_set:
                validation_errors.append("unknown_corrected_category")
            else:
                effective_category = str(corrected_category)
        elif review_status == "approved":
            if len(valid_category_set) == 1:
                effective_category = valid_category_set[0]
            else:
                exclusion_reason = "ambiguous_approved_prediction_set"
        else:
            exclusion_reason = "review_rejected"

        if validation_errors:
            exclusion_reason = validation_errors[0]

        training_eligible = (
            not validation_errors
            and exclusion_reason is None
            and effective_category is not None
        )
        original_attributes = attributes if isinstance(attributes, dict) else {}
        correction_attributes = (
            corrected_attributes
            if isinstance(corrected_attributes, dict)
            else {}
        )
        effective_attributes = dict(original_attributes)
        if review_status == "corrected":
            effective_attributes.update(correction_attributes)

        original_category = valid_category_set[0] if valid_category_set else None
        category_corrected = (
            review_status == "corrected"
            and effective_category is not None
            and original_category != effective_category
        )

        return {
            "schema_version": FEEDBACK_SCHEMA_VERSION,
            "listing": {
                "id": row["listing_id"],
                "external_id": row.get("external_id"),
                "title": row["title"],
                "description": row["description"],
                "created_at": row["listing_created_at"],
            },
            "prediction": {
                "id": prediction_id,
                "category_set": valid_category_set,
                "attributes": original_attributes,
                "reliability": reliability if isinstance(reliability, dict) else {},
                "created_at": row.get("prediction_created_at"),
            },
            "review": {
                "task_id": row["review_task_id"],
                "action": action,
                "status": review_status,
                "reason": row["review_reason"],
                "risk_level": row["review_risk_level"],
                "corrected_category": corrected_category,
                "corrected_attributes": correction_attributes,
                "created_at": row["review_created_at"],
                "decided_at": row["review_updated_at"],
            },
            "workflow": {
                "run_id": workflow_run_id,
                "status": row.get("workflow_status"),
                "decision": row.get("workflow_decision"),
                "risk_level": row.get("workflow_risk_level"),
                "graph_backend": row.get("graph_backend"),
                "started_at": row.get("workflow_started_at"),
                "completed_at": row.get("workflow_completed_at"),
                "history_pruned_at": row.get("history_pruned_at"),
            },
            "derived": {
                "original_category": original_category,
                "effective_category": effective_category,
                "effective_attributes": effective_attributes,
                "category_corrected": category_corrected,
            },
            "validation": {
                "status": "valid" if not validation_errors else "invalid",
                "errors": validation_errors,
                "training_eligible": training_eligible,
                "exclusion_reason": exclusion_reason,
            },
        }

    @staticmethod
    def _parse_json(
        raw_value: object,
        *,
        field: str,
        expected_type: type,
        errors: list[str],
    ) -> object:
        if raw_value is None:
            errors.append(f"missing_{field}")
            return expected_type()
        try:
            parsed = json.loads(str(raw_value))
        except (TypeError, json.JSONDecodeError):
            errors.append(f"malformed_{field}")
            return expected_type()
        if not isinstance(parsed, expected_type):
            errors.append(f"invalid_{field}")
            return expected_type()
        return parsed

    @staticmethod
    def _training_example(record: dict[str, Any]) -> dict[str, object]:
        return {
            "schema_version": FEEDBACK_SCHEMA_VERSION,
            "example_id": record["review"]["task_id"],
            "title": record["listing"]["title"],
            "description": record["listing"]["description"],
            "category": record["derived"]["effective_category"],
            "attributes": record["derived"]["effective_attributes"],
            "source": {
                "listing_id": record["listing"]["id"],
                "external_id": record["listing"]["external_id"],
                "prediction_id": record["prediction"]["id"],
                "workflow_run_id": record["workflow"]["run_id"],
                "review_task_id": record["review"]["task_id"],
                "review_action": record["review"]["action"],
                "review_reason": record["review"]["reason"],
                "decided_at": record["review"]["decided_at"],
                "original_category_set": record["prediction"]["category_set"],
            },
        }

    def _build_summary(
        self,
        *,
        batch_id: str,
        evidence: list[dict[str, Any]],
    ) -> dict[str, object]:
        action_counts = Counter(
            str(record["review"]["action"]) for record in evidence
        )
        reason_counts = Counter(
            str(record["review"]["reason"]) for record in evidence
        )
        exclusion_counts = Counter(
            str(record["validation"]["exclusion_reason"])
            for record in evidence
            if record["validation"]["exclusion_reason"]
        )
        category_actions: dict[str, Counter[str]] = defaultdict(Counter)
        reason_actions: dict[str, Counter[str]] = defaultdict(Counter)
        transitions: Counter[str] = Counter()

        for record in evidence:
            action = str(record["review"]["action"])
            reason = str(record["review"]["reason"])
            original_category = (
                record["derived"]["original_category"] or "unknown"
            )
            category_actions[str(original_category)][action] += 1
            reason_actions[reason][action] += 1
            if action == "correct" and record["derived"]["effective_category"]:
                transition = (
                    f"{original_category}->"
                    f"{record['derived']['effective_category']}"
                )
                transitions[transition] += 1

        decided_count = action_counts["approve"] + action_counts["correct"]
        training_eligible_count = sum(
            bool(record["validation"]["training_eligible"])
            for record in evidence
        )
        return {
            "schema_version": FEEDBACK_SCHEMA_VERSION,
            "batch_id": batch_id,
            "selected_count": len(evidence),
            "training_eligible_count": training_eligible_count,
            "excluded_count": len(evidence) - training_eligible_count,
            "action_counts": dict(sorted(action_counts.items())),
            "review_reason_counts": dict(sorted(reason_counts.items())),
            "exclusion_reason_counts": dict(sorted(exclusion_counts.items())),
            "correction_count": action_counts["correct"],
            "correction_rate": _round_rate(
                action_counts["correct"],
                decided_count,
            ),
            "rejection_rate": _round_rate(
                action_counts["reject"],
                len(evidence),
            ),
            "category_metrics": self._rate_breakdown(category_actions),
            "review_reason_metrics": self._rate_breakdown(reason_actions),
            "category_transitions": dict(sorted(transitions.items())),
        }

    @staticmethod
    def _rate_breakdown(
        groups: dict[str, Counter[str]],
    ) -> dict[str, dict[str, int | float]]:
        result: dict[str, dict[str, int | float]] = {}
        for key, actions in sorted(groups.items()):
            decided_count = actions["approve"] + actions["correct"]
            result[key] = {
                "approved_count": actions["approve"],
                "corrected_count": actions["correct"],
                "rejected_count": actions["reject"],
                "correction_rate": _round_rate(
                    actions["correct"],
                    decided_count,
                ),
            }
        return result

    def _write_artifacts(
        self,
        *,
        output_directory: Path,
        batch_id: str,
        source_fingerprint: str,
        evidence: list[dict[str, object]],
        training_examples: list[dict[str, object]],
        excluded_records: list[dict[str, object]],
        summary: dict[str, object],
    ) -> str:
        output_directory.mkdir(parents=True, exist_ok=True)
        self._set_private_permissions(self.output_root, directory=True)
        self._set_private_permissions(output_directory, directory=True)
        files: dict[str, tuple[bytes, int]] = {
            "review_evidence.jsonl": (
                self._jsonl_bytes(evidence),
                len(evidence),
            ),
            "training_examples.jsonl": (
                self._jsonl_bytes(training_examples),
                len(training_examples),
            ),
            "excluded_records.jsonl": (
                self._jsonl_bytes(excluded_records),
                len(excluded_records),
            ),
            "summary.json": (
                (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode(
                    "utf-8"
                ),
                1,
            ),
        }
        manifest_files: dict[str, dict[str, object]] = {}
        for filename, (content, record_count) in files.items():
            self._atomic_write(output_directory / filename, content)
            manifest_files[filename] = {
                "record_count": record_count,
                "sha256": _sha256_bytes(content),
                "size_bytes": len(content),
            }

        evidence_cutoff_at = max(
            str(record["review"]["decided_at"]) for record in evidence
        )
        manifest = {
            "schema_version": FEEDBACK_SCHEMA_VERSION,
            "batch_id": batch_id,
            "source_fingerprint": source_fingerprint,
            "evidence_cutoff_at": evidence_cutoff_at,
            "taxonomy": list(self.labels),
            "source_database": str(self.store.db_path),
            "files": manifest_files,
            "counts": {
                "selected": len(evidence),
                "training_eligible": len(training_examples),
                "excluded": len(excluded_records),
            },
        }
        manifest_bytes = (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        self._atomic_write(output_directory / "manifest.json", manifest_bytes)
        return _sha256_bytes(manifest_bytes)

    @staticmethod
    def _jsonl_bytes(records: Iterable[dict[str, object]]) -> bytes:
        lines = [_canonical_json(record) for record in records]
        return (("\n".join(lines) + "\n") if lines else "").encode("utf-8")

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        temporary_path = path.with_name(f".{path.name}.tmp")
        with temporary_path.open("wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        FeedbackExporter._set_private_permissions(temporary_path)
        os.replace(temporary_path, path)

    @staticmethod
    def _set_private_permissions(
        path: Path,
        *,
        directory: bool = False,
    ) -> None:
        try:
            path.chmod(0o700 if directory else 0o600)
        except OSError:
            pass

    @staticmethod
    def _empty_summary() -> dict[str, object]:
        return {
            "schema_version": FEEDBACK_SCHEMA_VERSION,
            "batch_id": None,
            "selected_count": 0,
            "training_eligible_count": 0,
            "excluded_count": 0,
            "action_counts": {},
            "review_reason_counts": {},
            "exclusion_reason_counts": {},
            "correction_count": 0,
            "correction_rate": 0.0,
            "rejection_rate": 0.0,
            "category_metrics": {},
            "review_reason_metrics": {},
            "category_transitions": {},
        }
