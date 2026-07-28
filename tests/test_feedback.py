from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from reliable_genai.feedback import FEEDBACK_SCHEMA_VERSION, FeedbackExporter
from reliable_genai.models import (
    ListingInput,
    PredictionResponse,
    ProductAttributes,
    ReliabilityMeta,
    ReviewDecision,
)
from reliable_genai.persistence import SQLiteReviewStore


def _prediction(category_set: list[str]) -> PredictionResponse:
    return PredictionResponse(
        category_set=category_set,
        attributes=ProductAttributes(
            brand="Acme",
            color="black",
            material="mesh",
            size="42",
        ),
        reliability=ReliabilityMeta(
            alpha=0.1,
            coverage_target=0.9,
            set_size=len(category_set),
            confidence=0.8,
            abstained=False,
            policy_action="set_output",
            llm_runtime="MOCK",
            llm_model="mock",
            classifier_runtime="ARTIFACT",
            coverage_threshold=0.9,
        ),
    )


def _resolved_workflow_review(
    store: SQLiteReviewStore,
    *,
    title: str,
    category_set: list[str],
    decision: ReviewDecision,
    reason: str = "low_confidence_large_set",
) -> str:
    workflow = store.start_workflow_run(
        ListingInput(title=title, description=f"{title} description"),
        graph_backend="langgraph",
    )
    prediction_id = store.create_prediction_for_workflow(
        workflow.id,
        listing_id=workflow.listing_id,
        prediction=_prediction(category_set),
    )
    task = store.create_review_task_for_workflow(
        workflow.id,
        listing_id=workflow.listing_id,
        prediction_id=prediction_id,
        reason=reason,
        risk_level="high",
    )
    store.complete_workflow_run(
        workflow.id,
        decision="needs_human_review",
        risk_level="high",
        duration_ms=5.0,
    )
    store.record_review_decision(task.id, decision)
    return task.id


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def test_feedback_export_dry_run_does_not_write_or_register(
    tmp_path: Path,
) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    _resolved_workflow_review(
        store,
        title="Trail shoes",
        category_set=["Sports", "Shoes"],
        decision=ReviewDecision(
            action="correct",
            corrected_category="Shoes",
        ),
    )
    output_root = tmp_path / "feedback"
    exporter = FeedbackExporter(store, output_root=output_root)

    first = exporter.run()
    second = exporter.run()

    assert first.applied is False
    assert first.selected_count == 1
    assert first.training_eligible_count == 1
    assert first.batch_id == second.batch_id
    assert first.source_fingerprint == second.source_fingerprint
    assert not output_root.exists()
    assert store.get_feedback_export_batch(str(first.batch_id)) is None


def test_feedback_export_separates_training_and_excluded_records(
    tmp_path: Path,
) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    approved_id = _resolved_workflow_review(
        store,
        title="Clear shoes",
        category_set=["Shoes"],
        decision=ReviewDecision(action="approve", notes="private note"),
        reason="abstained",
    )
    corrected_id = _resolved_workflow_review(
        store,
        title="Trail equipment",
        category_set=["Sports", "Shoes"],
        decision=ReviewDecision(
            action="correct",
            corrected_category="Shoes",
            corrected_attributes={"material": "rubber"},
        ),
    )
    ambiguous_id = _resolved_workflow_review(
        store,
        title="Ambiguous item",
        category_set=["Home", "Electronics"],
        decision=ReviewDecision(action="approve"),
    )
    rejected_id = _resolved_workflow_review(
        store,
        title="Rejected item",
        category_set=["Beauty"],
        decision=ReviewDecision(action="reject"),
    )
    invalid_correction_id = _resolved_workflow_review(
        store,
        title="Unknown category",
        category_set=["Home"],
        decision=ReviewDecision(
            action="correct",
            corrected_category="Unsupported",
        ),
    )

    listing_id = store.create_listing(
        ListingInput(title="Legacy item", description="No workflow")
    )
    legacy_prediction_id = store.create_prediction(
        listing_id,
        _prediction(["Clothing"]),
    )
    legacy_task = store.create_review_task(
        listing_id=listing_id,
        prediction_id=legacy_prediction_id,
        reason="legacy_review",
    )
    store.record_review_decision(
        legacy_task.id,
        ReviewDecision(action="approve"),
    )

    pending_workflow = store.start_workflow_run(
        ListingInput(title="Pending item", description="Not decided"),
        graph_backend="sequential",
    )
    pending_prediction_id = store.create_prediction_for_workflow(
        pending_workflow.id,
        listing_id=pending_workflow.listing_id,
        prediction=_prediction(["Sports"]),
    )
    store.create_review_task_for_workflow(
        pending_workflow.id,
        listing_id=pending_workflow.listing_id,
        prediction_id=pending_prediction_id,
        reason="pending",
        risk_level="high",
    )

    exporter = FeedbackExporter(
        store,
        output_root=tmp_path / "feedback",
    )
    result = exporter.run(apply=True)

    assert result.applied is True
    assert result.selected_count == 6
    assert result.training_eligible_count == 2
    assert result.excluded_count == 4
    assert result.summary["correction_rate"] == 0.4
    assert result.summary["rejection_rate"] == 0.167
    assert result.summary["category_transitions"] == {
        "Sports->Shoes": 1
    }

    output_directory = Path(str(result.output_directory))
    evidence = _read_jsonl(output_directory / "review_evidence.jsonl")
    training = _read_jsonl(output_directory / "training_examples.jsonl")
    excluded = _read_jsonl(output_directory / "excluded_records.jsonl")
    manifest = json.loads(
        (output_directory / "manifest.json").read_text(encoding="utf-8")
    )

    assert len(evidence) == 6
    assert {row["example_id"] for row in training} == {
        approved_id,
        corrected_id,
    }
    assert {
        row["review"]["task_id"]: row["validation"]["exclusion_reason"]
        for row in excluded
    } == {
        ambiguous_id: "ambiguous_approved_prediction_set",
        rejected_id: "review_rejected",
        invalid_correction_id: "unknown_corrected_category",
        legacy_task.id: "missing_workflow",
    }
    corrected_training = next(
        row for row in training if row["example_id"] == corrected_id
    )
    assert corrected_training["category"] == "Shoes"
    assert corrected_training["attributes"]["material"] == "rubber"
    assert "private note" not in (
        output_directory / "review_evidence.jsonl"
    ).read_text(encoding="utf-8")

    assert manifest["schema_version"] == FEEDBACK_SCHEMA_VERSION
    assert manifest["counts"] == {
        "excluded": 4,
        "selected": 6,
        "training_eligible": 2,
    }
    assert set(manifest["files"]) == {
        "excluded_records.jsonl",
        "review_evidence.jsonl",
        "summary.json",
        "training_examples.jsonl",
    }
    batch = store.get_feedback_export_batch(str(result.batch_id))
    assert batch is not None
    assert batch["status"] == "completed"
    assert batch["manifest_sha256"]

    repeated = exporter.run(apply=True)
    assert repeated.selected_count == 0
    assert repeated.batch_id is None


def test_feedback_cli_defaults_to_dry_run(tmp_path: Path) -> None:
    db_path = tmp_path / "uamas.db"
    SQLiteReviewStore(db_path)
    output_root = tmp_path / "feedback"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/export_review_feedback.py",
            "--db-path",
            str(db_path),
            "--output-dir",
            str(output_root),
        ],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["applied"] is False
    assert payload["selected_count"] == 0
    assert not output_root.exists()
