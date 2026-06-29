import json
from pathlib import Path

from fastapi import HTTPException
from starlette.requests import Request

from app import main as app_main
from reliable_genai.classifier import CalibratedTextClassifier
from reliable_genai.models import ListingInput, PredictionResponse, ProductAttributes, ReliabilityMeta, ReviewDecision
from reliable_genai.persistence import SQLiteReviewStore
from reliable_genai.review_graph import ReviewGraphRunner


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(json.dumps(rows), encoding="utf-8")


def _build_request(path: str) -> Request:
    return Request({"type": "http", "method": "GET", "path": path, "headers": []})


def _prediction(
    *,
    category_set: list[str] | None = None,
    confidence: float = 0.9,
    abstained: bool = False,
    semantic_score: float | None = 0.8,
    semantic_status: str = "ok",
) -> PredictionResponse:
    category_set = [] if category_set is None and abstained else category_set or ["Shoes"]
    return PredictionResponse(
        category_set=category_set,
        attributes=ProductAttributes(brand="Acme", color="black", material="mesh", size="42"),
        reliability=ReliabilityMeta(
            alpha=0.1,
            coverage_target=0.9,
            set_size=len(category_set),
            confidence=confidence,
            abstained=abstained,
            reason="abstained" if abstained else None,
            policy_action="abstain" if abstained else "set_output",
            llm_runtime="MOCK",
            llm_model="mock-model",
            classifier_runtime="ARTIFACT",
            classifier_reason=None,
            classifier_artifact_path="artifacts/classifier.joblib",
            classifier_model_type="embedding",
            semantic_consistency_score=semantic_score,
            semantic_consistency_status=semantic_status,
            semantic_consistency_reason=None,
            coverage_threshold=0.9,
        ),
    )


class StubReviewGraph:
    def __init__(self, prediction: PredictionResponse) -> None:
        self.prediction = prediction

    def predict(self, payload):
        return self.prediction

    @staticmethod
    def diagnostics() -> dict:
        return {"semantic_threshold": 0.4}


def test_diagnostics_include_classifier_runtime_metadata() -> None:
    diagnostics = app_main.build_diagnostics()

    assert "llm_last_error" in diagnostics
    assert diagnostics["classifier_runtime"] in {"ARTIFACT", "TRAINED", "FALLBACK"}
    assert "classifier_ready" in diagnostics
    assert "classifier_reason" in diagnostics
    assert "classifier_artifact_path" in diagnostics
    assert "classifier_model_type" in diagnostics
    assert isinstance(diagnostics["coverage_threshold"], float)
    assert "classifier_artifact_metadata" in diagnostics
    assert "classifier_artifact_format_version" in diagnostics
    assert "classifier_dataset_fingerprint" in diagnostics
    assert "classifier_artifact_load_attempted" in diagnostics
    assert "classifier_artifact_load_status" in diagnostics
    assert "classifier_artifact_rejection_reason" in diagnostics
    assert "classifier_artifact_rebuild_attempted" in diagnostics
    assert "classifier_artifact_rebuild_status" in diagnostics
    assert "classifier_artifact_rebuild_reason" in diagnostics
    assert "review_graph_enabled" in diagnostics
    assert "review_graph_available" in diagnostics
    assert "review_graph_backend" in diagnostics
    assert "review_graph_reason" in diagnostics
    assert "review_graph_confidence_threshold" in diagnostics
    assert "review_graph_set_size_trigger" in diagnostics
    assert "review_graph_semantic_threshold" in diagnostics
    assert "review_graph_gate_strategy" in diagnostics
    assert "review_graph_very_low_confidence_floor" in diagnostics
    assert "review_graph_trigger_rate" in diagnostics
    assert "review_graph_second_pass_rate" in diagnostics
    assert "review_graph_semantic_trigger_rate" in diagnostics
    assert "review_graph_cache_hit_rate" in diagnostics
    assert "review_graph_cached_step_count" in diagnostics
    assert "semantic_scorer_enabled" in diagnostics
    assert "semantic_scorer_client_available" in diagnostics
    assert "semantic_scorer_threshold" in diagnostics
    assert "semantic_scorer_model" in diagnostics
    assert "semantic_scorer_degraded_rate" in diagnostics
    assert "semantic_scorer_degraded_requests" in diagnostics
    assert "persistence_available" in diagnostics
    assert "persistence_db_path" in diagnostics
    assert "persistence_error" in diagnostics
    assert "listing_count" in diagnostics
    assert "review_task_count" in diagnostics
    assert "pending_review_task_count" in diagnostics


def test_diagnostics_report_auto_rebuild_for_mismatched_artifact(monkeypatch, tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    artifact_path = tmp_path / "classifier.joblib"
    original_rows = [
        {"title": "running shoe", "description": "shoe sole", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt apparel", "category": "Clothing"},
    ]
    changed_rows = [
        {"title": "running shoe", "description": "shoe sole", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt apparel", "category": "Clothing"},
        {"title": "tennis shoe", "description": "shoe court", "category": "Shoes"},
    ]
    _write_rows(train_path, original_rows)
    _write_rows(calibration_path, original_rows)
    CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
        save_artifact=True,
        prefer_artifact=False,
    )
    _write_rows(train_path, changed_rows)
    _write_rows(calibration_path, changed_rows)

    rebuilt_classifier = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
        artifact_mismatch_policy="auto_rebuild",
    )
    assert rebuilt_classifier.runtime == "ARTIFACT"
    assert rebuilt_classifier.is_ready is True
    assert rebuilt_classifier.artifact_rebuild_status == "rebuilt"

    fake_pipeline = type(
        "FakePipeline",
        (),
        {
            "classifier": rebuilt_classifier,
            "llm": type(
                "FakeLLM",
                (),
                {
                    "use_mock": True,
                    "model": "mock-model",
                    "endpoint": "mock-endpoint",
                    "last_runtime": "MOCK",
                    "last_error": None,
                },
            )(),
            "max_set_size": 3,
            "enable_abstain": True,
        },
    )()
    monkeypatch.setattr(app_main, "pipeline", fake_pipeline)
    monkeypatch.setattr(app_main, "review_graph", ReviewGraphRunner(fake_pipeline, enabled=False))

    diagnostics = app_main.build_diagnostics()

    assert diagnostics["classifier_runtime"] == "ARTIFACT"
    assert diagnostics["classifier_ready"] is True
    assert diagnostics["classifier_artifact_rebuild_attempted"] is True
    assert diagnostics["classifier_artifact_rebuild_status"] == "rebuilt"
    assert diagnostics["classifier_artifact_rebuild_reason"] is None


def test_load_results_artifact_handles_missing_file(tmp_path: Path) -> None:
    artifact, error = app_main.load_results_artifact(tmp_path / "missing.json")
    assert artifact is None
    assert error is not None


def test_load_results_artifact_reads_valid_json(tmp_path: Path) -> None:
    artifact_path = tmp_path / "results.json"
    artifact_path.write_text('{"metrics":{"empirical_coverage":0.9}}', encoding="utf-8")
    artifact, error = app_main.load_results_artifact(artifact_path)
    assert error is None
    assert artifact is not None
    assert artifact["metrics"]["empirical_coverage"] == 0.9


def test_dashboard_renders_with_artifact(monkeypatch) -> None:
    artifact = {
        "timestamp": "deterministic",
        "total_products": 10,
        "classifier_runtime": "ARTIFACT",
        "llm_runtime_mode": "MOCK",
        "metrics": {"empirical_coverage": 0.9, "abstention_rate": 0.1},
        "semantic_score_availability_rate": 1.0,
        "semantic_degraded_rate": 0.0,
        "review_graph_trigger_reason_counts": {"abstained": 1, "low_semantic_consistency": 2},
    }
    monkeypatch.setattr(app_main, "load_results_artifact", lambda path=app_main.RESULTS_JSON_PATH: (artifact, None))
    response = app_main.dashboard(_build_request("/dashboard"))

    assert response.status_code == 200
    html = response.body.decode("utf-8")
    assert "Reliability Dashboard" in html
    assert "Review Queue Storage" in html
    assert "Trigger Reason Distribution" in html
    assert "Latest Results (JSON)" in html


def test_dashboard_renders_with_missing_artifact(monkeypatch) -> None:
    monkeypatch.setattr(
        app_main,
        "load_results_artifact",
        lambda path=app_main.RESULTS_JSON_PATH: (None, "reports/results.json not found"),
    )
    response = app_main.dashboard(_build_request("/dashboard"))

    assert response.status_code == 200
    assert "reports/results.json not found" in response.body.decode("utf-8")


def test_artifact_routes_return_404_when_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(app_main, "RESULTS_JSON_PATH", tmp_path / "missing_results.json")
    monkeypatch.setattr(app_main, "RESULTS_MD_PATH", tmp_path / "missing_results.md")
    try:
        app_main.artifact_results_json()
        assert False, "expected HTTPException for missing JSON artifact"
    except HTTPException as exc:
        assert exc.status_code == 404

    try:
        app_main.artifact_results_md()
        assert False, "expected HTTPException for missing Markdown artifact"
    except HTTPException as exc:
        assert exc.status_code == 404


def test_analyze_listing_auto_accepts_and_persists_without_review_task(monkeypatch, tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    monkeypatch.setattr(app_main, "review_store", store)
    monkeypatch.setattr(app_main, "review_graph", StubReviewGraph(_prediction(confidence=0.92)))

    decision = app_main.analyze_listing(
        ListingInput(title="Lightweight running shoe", description="Black mesh upper size 42")
    )

    assert decision.listing_id.startswith("lst_")
    assert decision.decision == "auto_accept"
    assert decision.risk_level == "low"
    assert decision.review_task_id is None
    assert decision.category_set == ["Shoes"]
    assert [trace.agent for trace in decision.agent_trace] == [
        "classifier_agent",
        "attribute_extraction_agent",
        "semantic_critic_agent",
        "policy_agent",
        "human_review_agent",
    ]

    diagnostics = store.diagnostics()
    assert diagnostics["listing_count"] == 1
    assert diagnostics["review_task_count"] == 0


def test_analyze_listing_creates_review_task_for_low_confidence(monkeypatch, tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    monkeypatch.setattr(app_main, "review_store", store)
    monkeypatch.setattr(app_main, "review_graph", StubReviewGraph(_prediction(confidence=0.2)))

    decision = app_main.analyze_listing(
        ListingInput(title="Ambiguous item", description="Could fit multiple marketplace categories")
    )

    assert decision.decision == "needs_human_review"
    assert decision.risk_level == "high"
    assert decision.review_task_id is not None
    assert decision.review_task_id.startswith("rev_")
    assert decision.agent_trace[-1].status == "created"
    assert decision.agent_trace[-1].reason == "low_confidence"

    queue = app_main.list_review_queue()
    assert len(queue) == 1
    assert queue[0].id == decision.review_task_id
    assert queue[0].status == "pending"
    assert queue[0].reason == "low_confidence"
    assert queue[0].title == "Ambiguous item"


def test_analyze_listing_creates_review_task_for_low_semantic_consistency(monkeypatch, tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    monkeypatch.setattr(app_main, "review_store", store)
    monkeypatch.setattr(
        app_main,
        "review_graph",
        StubReviewGraph(_prediction(confidence=0.9, semantic_score=0.1, semantic_status="ok")),
    )

    decision = app_main.analyze_listing(
        ListingInput(title="Formal shoe", description="Description appears unrelated to selected category")
    )

    assert decision.decision == "needs_human_review"
    assert decision.review_task_id is not None
    assert store.get_review_task(decision.review_task_id).reason == "low_semantic_consistency"


def test_review_queue_decision_endpoint_updates_task(monkeypatch, tmp_path: Path) -> None:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    monkeypatch.setattr(app_main, "review_store", store)
    monkeypatch.setattr(app_main, "review_graph", StubReviewGraph(_prediction(confidence=0.2)))
    decision = app_main.analyze_listing(ListingInput(title="Ambiguous item", description="Needs reviewer"))
    task_id = decision.review_task_id

    updated = app_main.record_review_task_decision(
        task_id,
        ReviewDecision(
            action="correct",
            corrected_category="Sports",
            corrected_attributes={"material": "rubber"},
            notes="Reviewer corrected the category.",
        ),
    )

    assert updated.id == task_id
    assert updated.status == "corrected"
    assert updated.corrected_category == "Sports"
    assert updated.corrected_attributes == {"material": "rubber"}
    assert updated.notes == "Reviewer corrected the category."

    assert app_main.list_review_queue() == []


def test_review_queue_missing_task_returns_404(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(app_main, "review_store", SQLiteReviewStore(tmp_path / "uamas.db"))

    try:
        app_main.get_review_task("rev_missing")
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 404

    try:
        app_main.record_review_task_decision("rev_missing", ReviewDecision(action="reject"))
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 404
