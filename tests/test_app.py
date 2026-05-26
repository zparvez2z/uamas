import json
from pathlib import Path

from fastapi import HTTPException
from starlette.requests import Request

from app import main as app_main
from reliable_genai.classifier import CalibratedTextClassifier
from reliable_genai.review_graph import ReviewGraphRunner


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(json.dumps(rows), encoding="utf-8")


def _build_request(path: str) -> Request:
    return Request({"type": "http", "method": "GET", "path": path, "headers": []})


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
