from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, List, Optional

from .models import ClassifierResult, ProductInput


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "train.json"
DEFAULT_CALIBRATION_PATH = PROJECT_ROOT / "data" / "processed" / "calibration.json"


class CalibratedTextClassifier:
    """TF-IDF classifier with a conformal cumulative-mass threshold."""

    def __init__(
        self,
        labels: Iterable[str],
        alpha: float,
        train_path: Path = DEFAULT_TRAIN_PATH,
        calibration_path: Path = DEFAULT_CALIBRATION_PATH,
    ) -> None:
        self.labels = list(labels)
        self.alpha = alpha
        self.train_path = train_path
        self.calibration_path = calibration_path
        self.coverage_threshold = 1.0 - alpha
        self.is_ready = False
        self.reason: Optional[str] = None
        self._model = None

        self._fit()

    def predict(self, item: ProductInput) -> ClassifierResult:
        if not self.is_ready or self._model is None:
            raise RuntimeError(self.reason or "classifier is not ready")

        probabilities = self._predict_probability_map([self._text_from_item(item)])[0]
        sorted_labels = sorted(probabilities, key=lambda label: probabilities[label], reverse=True)
        return ClassifierResult(probabilities=probabilities, sorted_labels=sorted_labels)

    def _fit(self) -> None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import Pipeline as SklearnPipeline
        except ImportError as exc:
            self.reason = f"sklearn unavailable: {exc}"
            return

        try:
            train_rows = self._load_rows(self.train_path)
            calibration_rows = self._load_rows(self.calibration_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.reason = f"dataset unavailable: {exc}"
            return

        if not train_rows or not calibration_rows:
            self.reason = "train or calibration split is empty"
            return

        self._model = SklearnPipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, min_df=1)),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=1000,
                        random_state=42,
                    ),
                ),
            ]
        )
        self._model.fit(
            [self._text_from_row(row) for row in train_rows],
            [row["category"] for row in train_rows],
        )
        self.coverage_threshold = self._calibrate(calibration_rows)
        self.is_ready = True
        self.reason = None

    def _calibrate(self, rows: list[dict[str, str]]) -> float:
        probabilities = self._predict_probability_map([self._text_from_row(row) for row in rows])
        scores: List[float] = []

        for row, probability_map in zip(rows, probabilities):
            true_label = row["category"]
            cumulative = 0.0
            for label in sorted(probability_map, key=lambda key: probability_map[key], reverse=True):
                cumulative += probability_map[label]
                if label == true_label:
                    scores.append(cumulative)
                    break

        if not scores:
            return 1.0 - self.alpha

        scores.sort()
        rank = min(math.ceil((len(scores) + 1) * (1.0 - self.alpha)), len(scores)) - 1
        return scores[max(rank, 0)]

    def _predict_probability_map(self, texts: list[str]) -> list[dict[str, float]]:
        if self._model is None:
            raise RuntimeError("classifier is not fitted")

        predicted = self._model.predict_proba(texts)
        model_labels = list(self._model.named_steps["classifier"].classes_)
        results = []

        for row in predicted:
            probability_map = {label: 0.0 for label in self.labels}
            probability_map.update({label: float(probability) for label, probability in zip(model_labels, row)})
            total = sum(probability_map.values())
            if total:
                probability_map = {label: value / total for label, value in probability_map.items()}
            results.append(probability_map)

        return results

    @staticmethod
    def _load_rows(path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8") as handle:
            rows = json.load(handle)
        if not isinstance(rows, list):
            raise ValueError(f"{path} must contain a JSON list")
        return rows

    @staticmethod
    def _text_from_item(item: ProductInput) -> str:
        return f"{item.title} {item.description}".strip()

    @staticmethod
    def _text_from_row(row: dict[str, str]) -> str:
        return f"{row.get('title', '')} {row.get('description', '')}".strip()
