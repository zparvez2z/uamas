#!/usr/bin/env python3
"""Train and persist the calibrated text classifier artifact."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from reliable_genai.classifier import CalibratedTextClassifier
from reliable_genai.classifier import DEFAULT_ARTIFACT_PATH, DEFAULT_CALIBRATION_PATH, DEFAULT_TRAIN_PATH
from reliable_genai.pipeline import ReliabilityPipeline


def resolve_default_alpha() -> float:
    configured = os.getenv("ALPHA", "0.1")
    try:
        return float(configured)
    except ValueError:
        return 0.1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-path", type=Path, default=DEFAULT_TRAIN_PATH)
    parser.add_argument("--calibration-path", type=Path, default=DEFAULT_CALIBRATION_PATH)
    parser.add_argument("--artifact-path", type=Path, default=DEFAULT_ARTIFACT_PATH)
    parser.add_argument(
        "--calibration-artifact-path",
        type=Path,
        default=DEFAULT_ARTIFACT_PATH.with_name("calibration.json"),
    )
    parser.add_argument("--alpha", type=float, default=resolve_default_alpha())
    parser.add_argument("--model-type", choices=["embedding", "tfidf"], default="embedding")
    parser.add_argument("--force", action="store_true", help="Retrain even if an artifact already exists")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ["CLASSIFIER_MODEL_TYPE"] = args.model_type
    classifier = CalibratedTextClassifier(
        labels=ReliabilityPipeline.LABELS,
        alpha=args.alpha,
        train_path=args.train_path,
        calibration_path=args.calibration_path,
        artifact_path=args.artifact_path,
        save_artifact=True,
        prefer_artifact=not args.force,
    )

    if not classifier.is_ready:
        raise SystemExit(f"Classifier training failed: {classifier.reason}")

    if not args.artifact_path.exists():
        raise SystemExit(f"Classifier artifact was not written: {args.artifact_path}")

    args.calibration_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    with args.calibration_artifact_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "alpha": classifier.alpha,
                "coverage_target": 1.0 - classifier.alpha,
                "cumulative_threshold": classifier.coverage_threshold,
                "labels": classifier.labels,
                "classifier_artifact": str(args.artifact_path),
                "model_type": classifier.model_type,
            },
            handle,
            indent=2,
        )

    print(f"Classifier artifact: {args.artifact_path}")
    print(f"Calibration artifact: {args.calibration_artifact_path}")
    print(f"Coverage threshold: {classifier.coverage_threshold:.4f}")


if __name__ == "__main__":
    main()
