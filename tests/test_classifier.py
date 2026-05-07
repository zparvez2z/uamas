import json
from pathlib import Path

import pytest

from reliable_genai.classifier import CalibratedTextClassifier
from reliable_genai.models import ClassifierResult, ProductInput
from reliable_genai.pipeline import ReliabilityPipeline


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
    )

    result = classifier.predict(ProductInput(title="lightweight running shoe", description="grippy sole"))

    assert classifier.is_ready
    assert classifier.reason is None
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
    )

    assert not classifier.is_ready
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
