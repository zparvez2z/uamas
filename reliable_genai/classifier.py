from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Optional

import joblib

from .calibration import calibrate_cumulative_threshold
from .models import ClassifierResult, ProductInput


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "train.json"
DEFAULT_CALIBRATION_PATH = PROJECT_ROOT / "data" / "processed" / "calibration.json"
DEFAULT_ARTIFACT_PATH = PROJECT_ROOT / "artifacts" / "classifier.joblib"


class CalibratedTextClassifier:
    """TF-IDF classifier with a conformal cumulative-mass threshold."""

    def __init__(
        self,
        labels: Iterable[str],
        alpha: float,
        train_path: Path = DEFAULT_TRAIN_PATH,
        calibration_path: Path = DEFAULT_CALIBRATION_PATH,
        artifact_path: Optional[Path] = None,
        save_artifact: bool = False,
        prefer_artifact: bool = True,
    ) -> None:
        self.labels = list(labels)
        self.alpha = alpha
        self.train_path = train_path
        self.calibration_path = calibration_path
        self.artifact_path = artifact_path if artifact_path is not None else self._default_artifact_path()
        self.save_artifact = save_artifact
        self.coverage_threshold = 1.0 - alpha
        self.is_ready = False
        self.reason: Optional[str] = None
        self._model = None

        if prefer_artifact and self.artifact_path and self.artifact_path.exists() and self._load_artifact():
            return

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
        calibration = calibrate_cumulative_threshold(
            rows=calibration_rows,
            probability_fn=self._predict_probability_map,
            text_fn=self._text_from_row,
            alpha=self.alpha,
        )
        self.coverage_threshold = calibration.cumulative_threshold
        self.is_ready = True
        self.reason = None
        if self.save_artifact and self.artifact_path:
            self._save_artifact()

    def _load_artifact(self) -> bool:
        if self.artifact_path is None:
            return False

        try:
            payload = joblib.load(self.artifact_path)
        except (OSError, ValueError, TypeError) as exc:
            self.reason = f"classifier artifact unavailable: {exc}"
            return False

        if not isinstance(payload, dict):
            self.reason = "classifier artifact is malformed"
            return False

        artifact_labels = payload.get("labels")
        artifact_alpha = payload.get("alpha")
        artifact_model = payload.get("model")
        artifact_threshold = payload.get("coverage_threshold")
        if artifact_labels != self.labels or artifact_model is None or artifact_threshold is None:
            self.reason = "classifier artifact is incompatible"
            return False
        if artifact_alpha is not None and abs(float(artifact_alpha) - self.alpha) > 1e-12:
            self.reason = "classifier artifact alpha does not match runtime alpha"
            return False

        self._model = artifact_model
        self.coverage_threshold = float(artifact_threshold)
        self.is_ready = True
        self.reason = None
        return True

    def _save_artifact(self) -> None:
        if self.artifact_path is None or self._model is None:
            return

        self.artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "labels": self.labels,
                "alpha": self.alpha,
                "coverage_threshold": self.coverage_threshold,
                "model": self._model,
            },
            self.artifact_path,
        )

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

    @staticmethod
    def _default_artifact_path() -> Optional[Path]:
        configured = os.getenv("CLASSIFIER_ARTIFACT_PATH")
        if configured:
            return Path(configured)
        if os.getenv("DISABLE_CLASSIFIER_ARTIFACT", "false").lower() == "true":
            return None
        return DEFAULT_ARTIFACT_PATH
