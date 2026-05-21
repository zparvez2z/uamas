import json
from pathlib import Path

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
