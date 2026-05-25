import json
from pathlib import Path

import joblib
import pytest

from reliable_genai.classifier import CalibratedTextClassifier
from reliable_genai.calibration import calibrate_cumulative_threshold, cumulative_mass_for_label
from reliable_genai.models import ClassifierResult, ProductInput
from reliable_genai.pipeline import ReliabilityPipeline
from reliable_genai.scoring import apply_abstention_policy, build_prediction_set


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(json.dumps(rows), encoding="utf-8")


def test_classifier_trains_calibrates_and_predicts_probabilities(tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    train_rows = [
        {"title": "running shoe trainer", "description": "shoe sneaker sole", "category": "Shoes"},
        {"title": "trail running shoe", "description": "shoe grip", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt fabric apparel", "category": "Clothing"},
        {"title": "denim jacket", "description": "clothing apparel", "category": "Clothing"},
    ]
    calibration_rows = [
        {"title": "blue shoe", "description": "running sole", "category": "Shoes"},
        {"title": "black shirt", "description": "cotton apparel", "category": "Clothing"},
    ]
    write_rows(train_path, train_rows)
    write_rows(calibration_path, calibration_rows)

    classifier = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        prefer_artifact=False,
    )

    result = classifier.predict(ProductInput(title="lightweight running shoe", description="grippy sole"))

    assert classifier.is_ready
    assert classifier.runtime == "TRAINED"
    assert classifier.reason == "model_type=embedding"
    assert 0.0 < classifier.coverage_threshold <= 1.0
    assert set(result.probabilities) == {"Shoes", "Clothing"}
    assert result.sorted_labels[0] == "Shoes"
    assert sum(result.probabilities.values()) == pytest.approx(1.0)


def test_classifier_falls_back_when_dataset_is_missing(tmp_path: Path) -> None:
    classifier = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.2,
        train_path=tmp_path / "missing-train.json",
        calibration_path=tmp_path / "missing-calibration.json",
        prefer_artifact=False,
    )

    assert not classifier.is_ready
    assert classifier.runtime == "FALLBACK"
    assert classifier.coverage_threshold == pytest.approx(0.8)
    assert classifier.reason is not None
    assert "dataset unavailable" in classifier.reason
    with pytest.raises(RuntimeError):
        classifier.predict(ProductInput(title="shoe", description=""))


def test_pipeline_set_builder_uses_calibrated_threshold() -> None:
    pipeline = ReliabilityPipeline.__new__(ReliabilityPipeline)
    pipeline.alpha = 0.3
    pipeline.classifier = type("FakeClassifier", (), {"is_ready": True, "coverage_threshold": 0.75})()
    result = ClassifierResult(
        probabilities={"A": 0.5, "B": 0.3, "C": 0.2},
        sorted_labels=["A", "B", "C"],
    )

    assert pipeline._conformal_set(result) == ["A", "B"]


def test_classifier_artifact_round_trip_preserves_predictions(tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    artifact_path = tmp_path / "classifier.joblib"
    train_rows = [
        {"title": "running shoe trainer", "description": "shoe sneaker sole", "category": "Shoes"},
        {"title": "trail running shoe", "description": "shoe grip", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt fabric apparel", "category": "Clothing"},
        {"title": "denim jacket", "description": "clothing apparel", "category": "Clothing"},
    ]
    calibration_rows = [
        {"title": "blue shoe", "description": "running sole", "category": "Shoes"},
        {"title": "black shirt", "description": "cotton apparel", "category": "Clothing"},
    ]
    write_rows(train_path, train_rows)
    write_rows(calibration_path, calibration_rows)

    trained = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
        save_artifact=True,
        prefer_artifact=False,
    )
    loaded = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
    )
    item = ProductInput(title="lightweight running shoe", description="grippy sole")

    assert artifact_path.exists()
    assert loaded.is_ready
    assert loaded.runtime == "ARTIFACT"
    assert loaded.coverage_threshold == pytest.approx(trained.coverage_threshold)
    assert loaded.predict(item).probabilities == pytest.approx(trained.predict(item).probabilities)


def test_pipeline_loads_classifier_artifact_with_opt_out(monkeypatch, tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    artifact_path = tmp_path / "classifier.joblib"
    rows = [
        {"title": "running shoe", "description": "shoe sole", "category": "Shoes"},
        {"title": "trail shoe", "description": "shoe grip", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt apparel", "category": "Clothing"},
        {"title": "denim jacket", "description": "clothing apparel", "category": "Clothing"},
    ]
    write_rows(train_path, rows)
    write_rows(calibration_path, rows)
    CalibratedTextClassifier(
        labels=ReliabilityPipeline.LABELS,
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
        save_artifact=True,
        prefer_artifact=False,
    )

    monkeypatch.setenv("ALPHA", "0.3")
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    monkeypatch.setenv("CLASSIFIER_ARTIFACT_PATH", str(artifact_path))
    monkeypatch.setenv("STRICT_ARTIFACT_METADATA", "false")

    pipeline = ReliabilityPipeline()

    assert pipeline.classifier.is_ready
    assert pipeline.classifier.runtime == "ARTIFACT"
    assert pipeline.classifier.artifact_path == artifact_path


def test_classifier_diagnostics_report_fallback_reason(tmp_path: Path) -> None:
    classifier = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.2,
        train_path=tmp_path / "missing-train.json",
        calibration_path=tmp_path / "missing-calibration.json",
        prefer_artifact=False,
    )

    diagnostics = classifier.diagnostics()

    assert diagnostics["runtime"] == "FALLBACK"
    assert diagnostics["ready"] is False
    assert diagnostics["reason"] == classifier.reason
    assert diagnostics["coverage_threshold"] == pytest.approx(0.8)



def test_classifier_artifact_metadata_exposed_in_diagnostics(tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    artifact_path = tmp_path / "classifier.joblib"
    rows = [
        {"title": "running shoe", "description": "shoe sole", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt apparel", "category": "Clothing"},
    ]
    write_rows(train_path, rows)
    write_rows(calibration_path, rows)

    CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
        save_artifact=True,
        prefer_artifact=False,
    )

    loaded = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
    )

    diagnostics = loaded.diagnostics()
    metadata = diagnostics["artifact_metadata"]

    assert diagnostics["runtime"] == "ARTIFACT"
    assert isinstance(metadata, dict)
    assert metadata["train_row_count"] == 2
    assert metadata["calibration_row_count"] == 2
    assert metadata["train_data_sha256"]
    assert metadata["calibration_data_sha256"]
    assert metadata["artifact_format_version"] == 1
    assert metadata["classifier_family"] == "logistic_regression_text"
    assert metadata["dataset_fingerprint_sha256"]
    assert metadata["sklearn_version"]



def test_classifier_strict_metadata_validation_detects_mismatch(tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    rows = [
        {"title": "running shoe", "description": "shoe sole", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt apparel", "category": "Clothing"},
    ]
    write_rows(train_path, rows)
    write_rows(calibration_path, rows)

    classifier = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        prefer_artifact=False,
    )

    incompatible_metadata = classifier._build_artifact_metadata(rows + [{"title": "extra", "description": "x", "category": "Shoes"}], rows)
    compatible, reason = classifier._validate_artifact_metadata(incompatible_metadata)

    assert compatible is False
    assert reason is not None
    assert "train" in reason


def test_classifier_strict_metadata_blocks_mismatched_artifact_by_default(tmp_path: Path) -> None:
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
    write_rows(train_path, original_rows)
    write_rows(calibration_path, original_rows)

    CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
        save_artifact=True,
        prefer_artifact=False,
    )

    write_rows(train_path, changed_rows)
    write_rows(calibration_path, changed_rows)
    loaded = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
    )

    assert loaded.runtime == "TRAINED"
    assert loaded.reason == "model_type=embedding"


def test_classifier_strict_metadata_can_be_disabled_for_artifact_compatibility(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
    write_rows(train_path, original_rows)
    write_rows(calibration_path, original_rows)

    CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
        save_artifact=True,
        prefer_artifact=False,
    )

    write_rows(train_path, changed_rows)
    write_rows(calibration_path, changed_rows)
    monkeypatch.setenv("STRICT_ARTIFACT_METADATA", "false")
    loaded = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
    )

    assert loaded.runtime == "ARTIFACT"


def test_classifier_rejects_unsupported_artifact_version(tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    artifact_path = tmp_path / "classifier.joblib"
    rows = [
        {"title": "running shoe", "description": "shoe sole", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt apparel", "category": "Clothing"},
    ]
    write_rows(train_path, rows)
    write_rows(calibration_path, rows)

    CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
        save_artifact=True,
        prefer_artifact=False,
    )
    payload = joblib.load(artifact_path)
    payload["metadata"]["artifact_format_version"] = 999
    joblib.dump(payload, artifact_path)

    loaded = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
    )

    assert loaded.runtime == "TRAINED"
    assert loaded.reason == "model_type=embedding"


def test_classifier_rejects_artifact_with_missing_required_metadata_field(tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    artifact_path = tmp_path / "classifier.joblib"
    rows = [
        {"title": "running shoe", "description": "shoe sole", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt apparel", "category": "Clothing"},
    ]
    write_rows(train_path, rows)
    write_rows(calibration_path, rows)

    CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
        save_artifact=True,
        prefer_artifact=False,
    )
    payload = joblib.load(artifact_path)
    payload["metadata"].pop("sklearn_version", None)
    joblib.dump(payload, artifact_path)

    loaded = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        artifact_path=artifact_path,
    )

    assert loaded.runtime == "TRAINED"
    assert loaded.reason == "model_type=embedding"


def test_calibration_computes_cumulative_threshold() -> None:
    rows = [
        {"title": "a", "category": "A"},
        {"title": "b", "category": "B"},
    ]
    probability_maps = [
        {"A": 0.7, "B": 0.3},
        {"A": 0.6, "B": 0.4},
    ]

    calibration = calibrate_cumulative_threshold(
        rows=rows,
        probability_fn=lambda texts: probability_maps,
        text_fn=lambda row: row["title"],
        alpha=0.5,
    )

    assert cumulative_mass_for_label(probability_maps[1], "B") == pytest.approx(1.0)
    assert calibration.target_coverage == pytest.approx(0.5)
    assert calibration.cumulative_threshold == pytest.approx(1.0)
    assert calibration.sample_count == 2


def test_scoring_helpers_build_sets_and_abstain() -> None:
    result = ClassifierResult(
        probabilities={"A": 0.45, "B": 0.35, "C": 0.2},
        sorted_labels=["A", "B", "C"],
    )

    category_set = build_prediction_set(result, cumulative_threshold=0.75)
    decision = apply_abstention_policy(category_set, max_set_size=1, enable_abstain=True)

    assert category_set == ["A", "B"]
    assert decision.category_set == []
    assert decision.abstained
    assert decision.action == "abstain"


def test_classifier_can_force_tfidf_mode(tmp_path: Path, monkeypatch) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    rows = [
        {"title": "running shoe", "description": "shoe sole", "category": "Shoes"},
        {"title": "trail shoe", "description": "shoe grip", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt apparel", "category": "Clothing"},
        {"title": "denim jacket", "description": "clothing apparel", "category": "Clothing"},
    ]
    write_rows(train_path, rows)
    write_rows(calibration_path, rows)
    monkeypatch.setenv("CLASSIFIER_MODEL_TYPE", "tfidf")

    classifier = CalibratedTextClassifier(
        labels=["Shoes", "Clothing"],
        alpha=0.3,
        train_path=train_path,
        calibration_path=calibration_path,
        prefer_artifact=False,
    )

    assert classifier.is_ready
    assert classifier.reason == "model_type=tfidf"
