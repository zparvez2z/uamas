import json
from pathlib import Path

from app import main as app_main
from reliable_genai.classifier import CalibratedTextClassifier
from reliable_genai.review_graph import ReviewGraphRunner


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(json.dumps(rows), encoding="utf-8")


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
    assert "review_graph_gate_strategy" in diagnostics
    assert "review_graph_very_low_confidence_floor" in diagnostics
    assert "review_graph_trigger_rate" in diagnostics
    assert "review_graph_second_pass_rate" in diagnostics
    assert "review_graph_cache_hit_rate" in diagnostics
    assert "review_graph_cached_step_count" in diagnostics


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
