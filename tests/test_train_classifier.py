import json
import os
import subprocess
import sys
from pathlib import Path


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(json.dumps(rows), encoding="utf-8")


def test_train_classifier_script_writes_artifacts(tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    artifact_path = tmp_path / "classifier.joblib"
    calibration_artifact_path = tmp_path / "calibration-summary.json"
    rows = [
        {"title": "running shoe trainer", "description": "shoe sneaker sole", "category": "Shoes"},
        {"title": "trail running shoe", "description": "shoe grip", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt fabric apparel", "category": "Clothing"},
        {"title": "denim jacket", "description": "clothing apparel", "category": "Clothing"},
    ]
    write_rows(train_path, rows)
    write_rows(calibration_path, rows)

    env = dict(os.environ)
    env.pop("ALPHA", None)
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/train_classifier.py",
            "--train-path",
            str(train_path),
            "--calibration-path",
            str(calibration_path),
            "--artifact-path",
            str(artifact_path),
            "--calibration-artifact-path",
            str(calibration_artifact_path),
            "--force",
        ],
        check=True,
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        env=env,
    )

    calibration_summary = json.loads(calibration_artifact_path.read_text(encoding="utf-8"))

    assert "Coverage threshold" in completed.stdout
    assert artifact_path.exists()
    assert calibration_artifact_path.exists()
    assert calibration_summary["alpha"] == 0.1
    assert calibration_summary["coverage_target"] == 0.9
    assert calibration_summary["classifier_artifact"] == str(artifact_path)
    assert calibration_summary["model_type"] == "embedding"


def test_train_classifier_script_uses_alpha_environment_default(tmp_path: Path) -> None:
    train_path = tmp_path / "train.json"
    calibration_path = tmp_path / "calibration.json"
    artifact_path = tmp_path / "classifier.joblib"
    calibration_artifact_path = tmp_path / "calibration-summary.json"
    rows = [
        {"title": "running shoe trainer", "description": "shoe sneaker sole", "category": "Shoes"},
        {"title": "trail running shoe", "description": "shoe grip", "category": "Shoes"},
        {"title": "cotton shirt", "description": "shirt fabric apparel", "category": "Clothing"},
        {"title": "denim jacket", "description": "clothing apparel", "category": "Clothing"},
    ]
    write_rows(train_path, rows)
    write_rows(calibration_path, rows)

    env = dict(os.environ)
    env["ALPHA"] = "0.25"
    subprocess.run(
        [
            sys.executable,
            "scripts/train_classifier.py",
            "--train-path",
            str(train_path),
            "--calibration-path",
            str(calibration_path),
            "--artifact-path",
            str(artifact_path),
            "--calibration-artifact-path",
            str(calibration_artifact_path),
            "--force",
        ],
        check=True,
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        env=env,
    )

    calibration_summary = json.loads(calibration_artifact_path.read_text(encoding="utf-8"))

    assert calibration_summary["alpha"] == 0.25
    assert calibration_summary["coverage_target"] == 0.75
