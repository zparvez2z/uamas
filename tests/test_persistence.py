from pathlib import Path

import pytest

from reliable_genai.models import (
    ListingInput,
    PredictionResponse,
    ProductAttributes,
    ReliabilityMeta,
    ReviewDecision,
)
from reliable_genai.persistence import SQLiteReviewStore, resolve_db_path


def _prediction() -> PredictionResponse:
    return PredictionResponse(
        category_set=["Shoes"],
        attributes=ProductAttributes(brand="Acme", color="black", material="mesh", size="42"),
        reliability=ReliabilityMeta(
            alpha=0.1,
            coverage_target=0.9,
            set_size=1,
            confidence=0.91,
            abstained=False,
            reason=None,
            policy_action="set_output",
            llm_runtime="MOCK",
            llm_model="mock-model",
            classifier_runtime="ARTIFACT",
            classifier_reason=None,
            classifier_artifact_path="artifacts/classifier.joblib",
            classifier_model_type="embedding",
            coverage_threshold=0.9,
        ),
    )


def test_resolve_db_path_uses_env_override(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "custom.db"
    monkeypatch.setenv("UAMAS_DB_PATH", str(path))

    assert resolve_db_path() == path


def test_store_creates_listing_prediction_and_review_task(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    listing_id = store.create_listing(
        ListingInput(title="ambiguous running shoe", description="could be apparel or sports gear")
    )
    prediction_id = store.create_prediction(listing_id, _prediction())

    task = store.create_review_task(
        listing_id=listing_id,
        prediction_id=prediction_id,
        reason="low_confidence_large_set",
        risk_level="high",
    )

    assert task.id.startswith("rev_")
    assert task.listing_id == listing_id
    assert task.prediction_id == prediction_id
    assert task.status == "pending"
    assert task.reason == "low_confidence_large_set"
    assert task.risk_level == "high"

    fetched = store.get_review_task(task.id)
    assert fetched == task

    pending = store.list_review_tasks(status="pending")
    assert len(pending) == 1
    assert pending[0].title == "ambiguous running shoe"
    assert pending[0].description == "could be apparel or sports gear"


def test_store_records_review_decision(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    listing_id = store.create_listing(ListingInput(title="dress shoe", description="formal leather"))
    task = store.create_review_task(
        listing_id=listing_id,
        prediction_id=None,
        reason="abstained",
    )

    updated = store.record_review_decision(
        task.id,
        ReviewDecision(
            action="correct",
            corrected_category="Shoes",
            corrected_attributes={"material": "leather"},
            notes="Correct category after review.",
        ),
    )

    assert updated.status == "corrected"
    assert updated.corrected_category == "Shoes"
    assert updated.corrected_attributes == {"material": "leather"}
    assert updated.notes == "Correct category after review."
    assert store.list_review_tasks(status="pending") == []
    assert len(store.list_review_tasks(status="corrected")) == 1


def test_store_diagnostics_counts_review_tasks(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    listing_id = store.create_listing(ListingInput(title="item", description="desc"))
    task = store.create_review_task(listing_id=listing_id, prediction_id=None, reason="abstained")

    diagnostics = store.diagnostics()
    assert diagnostics["available"] is True
    assert diagnostics["listing_count"] == 1
    assert diagnostics["review_task_count"] == 1
    assert diagnostics["pending_review_task_count"] == 1

    store.record_review_decision(task.id, ReviewDecision(action="approve"))
    diagnostics = store.diagnostics()
    assert diagnostics["review_task_count"] == 1
    assert diagnostics["pending_review_task_count"] == 0


def test_store_metrics_counts_statuses_reasons_and_rates(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    auto_listing_id = store.create_listing(ListingInput(title="accepted shoe", description="clear shoe"))
    store.create_prediction(auto_listing_id, _prediction())

    pending_listing_id = store.create_listing(ListingInput(title="pending item", description="unclear"))
    pending_prediction_id = store.create_prediction(pending_listing_id, _prediction())
    store.create_review_task(
        listing_id=pending_listing_id,
        prediction_id=pending_prediction_id,
        reason="low_confidence",
    )

    corrected_listing_id = store.create_listing(ListingInput(title="corrected item", description="unclear"))
    corrected_prediction_id = store.create_prediction(corrected_listing_id, _prediction())
    corrected_task = store.create_review_task(
        listing_id=corrected_listing_id,
        prediction_id=corrected_prediction_id,
        reason="low_semantic_consistency",
    )
    store.record_review_decision(corrected_task.id, ReviewDecision(action="correct", corrected_category="Sports"))

    metrics = store.metrics()

    assert metrics["available"] is True
    assert metrics["listing_count"] == 3
    assert metrics["prediction_count"] == 3
    assert metrics["review_task_count"] == 2
    assert metrics["auto_accept_count"] == 1
    assert metrics["needs_human_review_count"] == 2
    assert metrics["pending_review_task_count"] == 1
    assert metrics["corrected_review_task_count"] == 1
    assert metrics["review_status_counts"] == {"corrected": 1, "pending": 1}
    assert metrics["review_reason_counts"] == {"low_confidence": 1, "low_semantic_consistency": 1}
    assert metrics["auto_accept_rate"] == 0.333
    assert metrics["human_review_rate"] == 0.667
    assert metrics["correction_rate"] == 0.5


def test_store_rejects_invalid_limit(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")

    with pytest.raises(ValueError, match="limit must be positive"):
        store.list_review_tasks(limit=0)


def test_store_raises_for_missing_review_task(tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")

    with pytest.raises(KeyError, match="review task not found"):
        store.record_review_decision("rev_missing", ReviewDecision(action="reject"))
