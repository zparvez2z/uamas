import json
from pathlib import Path

from reliable_genai.runtime_profile import resolve_runtime_settings


def test_runtime_profile_uses_profile_when_env_and_cli_are_absent(monkeypatch, tmp_path: Path) -> None:
    profile_path = tmp_path / "runtime_profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "alpha": 0.2,
                "classifier_model_type": "tfidf",
                "strict_artifact_metadata": False,
                "classifier_artifact_mismatch_policy": "in_memory",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("RUNTIME_PROFILE_PATH", str(profile_path))
    for key in (
        "ALPHA",
        "CLASSIFIER_MODEL_TYPE",
        "STRICT_ARTIFACT_METADATA",
        "CLASSIFIER_ARTIFACT_MISMATCH_POLICY",
    ):
        monkeypatch.delenv(key, raising=False)

    settings = resolve_runtime_settings()

    assert settings.alpha == 0.2
    assert settings.classifier_model_type == "tfidf"
    assert settings.strict_artifact_metadata is False
    assert settings.classifier_artifact_mismatch_policy == "in_memory"


def test_runtime_profile_env_overrides_profile(monkeypatch, tmp_path: Path) -> None:
    profile_path = tmp_path / "runtime_profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "alpha": 0.1,
                "classifier_model_type": "embedding",
                "strict_artifact_metadata": True,
                "classifier_artifact_mismatch_policy": "auto_rebuild",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("RUNTIME_PROFILE_PATH", str(profile_path))
    monkeypatch.setenv("ALPHA", "0.3")
    monkeypatch.setenv("CLASSIFIER_MODEL_TYPE", "tfidf")
    monkeypatch.setenv("STRICT_ARTIFACT_METADATA", "false")
    monkeypatch.setenv("CLASSIFIER_ARTIFACT_MISMATCH_POLICY", "fail_fast")

    settings = resolve_runtime_settings()

    assert settings.alpha == 0.3
    assert settings.classifier_model_type == "tfidf"
    assert settings.strict_artifact_metadata is False
    assert settings.classifier_artifact_mismatch_policy == "fail_fast"


def test_runtime_profile_cli_overrides_env_and_profile(monkeypatch, tmp_path: Path) -> None:
    profile_path = tmp_path / "runtime_profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "alpha": 0.1,
                "classifier_model_type": "embedding",
                "strict_artifact_metadata": True,
                "classifier_artifact_mismatch_policy": "auto_rebuild",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("RUNTIME_PROFILE_PATH", str(profile_path))
    monkeypatch.setenv("ALPHA", "0.3")
    monkeypatch.setenv("CLASSIFIER_MODEL_TYPE", "tfidf")
    monkeypatch.setenv("STRICT_ARTIFACT_METADATA", "false")
    monkeypatch.setenv("CLASSIFIER_ARTIFACT_MISMATCH_POLICY", "fail_fast")

    settings = resolve_runtime_settings(
        {
            "alpha": 0.4,
            "classifier_model_type": "embedding",
            "strict_artifact_metadata": True,
            "classifier_artifact_mismatch_policy": "in_memory",
        }
    )

    assert settings.alpha == 0.4
    assert settings.classifier_model_type == "embedding"
    assert settings.strict_artifact_metadata is True
    assert settings.classifier_artifact_mismatch_policy == "in_memory"
