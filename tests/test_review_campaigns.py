from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from reliable_genai.models import (
    CatalogQualityDecision,
    ListingInput,
    PredictionResponse,
    ProductAttributes,
    ReliabilityMeta,
    ReviewDecision,
)
from reliable_genai.persistence import SQLiteReviewStore
from reliable_genai.review_campaigns import ReviewCampaignService
from scripts.load_dataset import split_fingerprint


def _prediction(category: str = "Shoes") -> PredictionResponse:
    return PredictionResponse(
        category_set=[category],
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
            semantic_consistency_score=0.8,
            semantic_consistency_status="ok",
            coverage_threshold=0.9,
        ),
    )


class FakeAnalyzer:
    def __init__(self, store: SQLiteReviewStore) -> None:
        self.store = store
        self.calls = 0

    def analyze(self, listing: ListingInput) -> CatalogQualityDecision:
        self.calls += 1
        workflow = self.store.start_workflow_run(
            listing,
            graph_backend="sequential",
        )
        prediction = _prediction("Shoes")
        prediction_id = self.store.create_prediction_for_workflow(
            workflow.id,
            listing_id=workflow.listing_id,
            prediction=prediction,
        )
        needs_review = "policy" in listing.title.lower()
        review_task_id = None
        if needs_review:
            review_task_id = self.store.create_review_task_for_workflow(
                workflow.id,
                listing_id=workflow.listing_id,
                prediction_id=prediction_id,
                reason="low_confidence",
                risk_level="high",
            ).id
        decision = "needs_human_review" if needs_review else "auto_accept"
        self.store.complete_workflow_run(
            workflow.id,
            decision=decision,
            risk_level="high" if needs_review else "low",
            duration_ms=2.0,
        )
        return CatalogQualityDecision(
            listing_id=workflow.listing_id,
            workflow_run_id=workflow.id,
            decision=decision,
            risk_level="high" if needs_review else "low",
            explanation="test decision",
            category_set=prediction.category_set,
            attributes=prediction.attributes,
            reliability=prediction.reliability,
            review_task_id=review_task_id,
        )


def _write_feedback_pool(tmp_path: Path) -> tuple[Path, Path]:
    rows = [
        {
            "ean": "shoe-policy",
            "locale": "en-US",
            "title": "Policy shoe",
            "description": "Needs natural review",
            "category": "Shoes",
        },
        {
            "ean": "shoe-control",
            "locale": "en-US",
            "title": "Control shoe",
            "description": "Control",
            "category": "Shoes",
        },
        {
            "ean": "sports-control",
            "locale": "en-US",
            "title": "Control sports",
            "description": "Control",
            "category": "Sports",
        },
        {
            "ean": "sports-extra",
            "locale": "en-US",
            "title": "Extra sports",
            "description": "Extra",
            "category": "Sports",
        },
    ]
    pool_path = tmp_path / "feedback_pool.json"
    metadata_path = tmp_path / "dataset_metadata.json"
    pool_path.write_text(json.dumps(rows), encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "split_fingerprints_sha256": {
                    "feedback_pool": split_fingerprint(rows)
                }
            }
        ),
        encoding="utf-8",
    )
    return pool_path, metadata_path


def test_campaign_plan_create_run_and_report(tmp_path: Path) -> None:
    pool_path, metadata_path = _write_feedback_pool(tmp_path)
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    analyzer = FakeAnalyzer(store)
    service = ReviewCampaignService(
        store,
        analyzer=analyzer,
        feedback_pool_path=pool_path,
        metadata_path=metadata_path,
        labels=("Shoes", "Sports"),
    )

    first_plan = service.plan(
        name="baseline",
        per_category=1,
        seed=7,
        runtime_mode="MOCK",
    )
    second_plan = service.plan(
        name="baseline",
        per_category=1,
        seed=7,
        runtime_mode="MOCK",
    )
    assert first_plan == second_plan
    assert first_plan["selected_count"] == 2
    assert first_plan["category_counts"] == {"Shoes": 1, "Sports": 1}

    campaign = service.create(
        name="baseline",
        per_category=1,
        seed=7,
        runtime_mode="MOCK",
    )
    repeated = service.create(
        name="baseline",
        per_category=1,
        seed=7,
        runtime_mode="MOCK",
    )
    assert campaign["id"] == repeated["id"]

    first_run = service.run(campaign["id"], limit=1)
    assert first_run["processed_this_run"] == 1
    assert analyzer.calls == 1
    second_run = service.run(campaign["id"], limit=10)
    assert second_run["processed_this_run"] == 1
    assert analyzer.calls == 2
    assert second_run["review_status_counts"] == {"pending": 2}

    tasks = store.list_review_tasks(campaign_id=campaign["id"])
    assert len(tasks) == 2
    assert all(task.campaign_id == campaign["id"] for task in tasks)
    assert all(task.prediction is not None for task in tasks)
    assert "reference_category" not in json.dumps(
        [task.model_dump(mode="json") for task in tasks]
    )

    sports_task = next(task for task in tasks if "sports" in task.title.lower())
    shoe_task = next(task for task in tasks if task.id != sports_task.id)
    store.record_review_decision(
        sports_task.id,
        ReviewDecision(action="correct", corrected_category="Sports"),
    )
    store.record_review_decision(
        shoe_task.id,
        ReviewDecision(action="approve"),
    )

    final_status = service.status(campaign["id"])
    assert final_status["status"] == "completed"
    report = service.report(
        campaign["id"],
        minimum_resolved=2,
        minimum_eligible=2,
        minimum_corrections=1,
        minimum_per_category=1,
    )
    assert report["resolved_count"] == 2
    assert report["training_eligible_count"] == 2
    assert report["final_category_counts"] == {"Shoes": 1, "Sports": 1}
    assert report["model_reviewer_agreement"] == 0.5
    assert report["reviewer_reference_agreement"] == 1.0
    assert report["readiness"]["ready_for_retraining"] is True


def test_campaign_rejects_tampered_feedback_pool(tmp_path: Path) -> None:
    pool_path, metadata_path = _write_feedback_pool(tmp_path)
    rows = json.loads(pool_path.read_text(encoding="utf-8"))
    rows[0]["title"] = "tampered"
    pool_path.write_text(json.dumps(rows), encoding="utf-8")
    service = ReviewCampaignService(
        SQLiteReviewStore(tmp_path / "uamas.db"),
        feedback_pool_path=pool_path,
        metadata_path=metadata_path,
        labels=("Shoes", "Sports"),
    )

    try:
        service.plan(
            name="baseline",
            per_category=1,
            seed=7,
            runtime_mode="MOCK",
        )
        assert False, "expected fingerprint mismatch"
    except ValueError as exc:
        assert "fingerprint" in str(exc)


def test_campaign_plan_cli_does_not_create_database(tmp_path: Path) -> None:
    db_path = tmp_path / "plan.db"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/review_campaign.py",
            "--db-path",
            str(db_path),
            "plan",
            "--name",
            "preview",
            "--per-category",
            "1",
            "--seed",
            "7",
        ],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["selected_count"] == 6
    assert not db_path.exists()
    assert "reference_category" not in (
        Path(__file__).parent.parent / "app" / "templates" / "review.html"
    ).read_text(encoding="utf-8")
