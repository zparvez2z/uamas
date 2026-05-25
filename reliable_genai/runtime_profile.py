from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUNTIME_PROFILE_PATH = PROJECT_ROOT / "config" / "runtime_profile.json"
SUPPORTED_CLASSIFIER_MODEL_TYPES = {"embedding", "tfidf"}
SUPPORTED_ARTIFACT_MISMATCH_POLICIES = {"auto_rebuild", "fail_fast", "in_memory"}


@dataclass(frozen=True)
class RuntimeSettings:
    alpha: float = 0.1
    classifier_model_type: str = "embedding"
    strict_artifact_metadata: bool = True
    classifier_artifact_mismatch_policy: str = "auto_rebuild"


def _parse_bool(value: Any, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    raise RuntimeError(f"Invalid boolean for {field_name}: {value!r}")


def _parse_float(value: Any, *, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Invalid float for {field_name}: {value!r}") from exc


def _parse_model_type(value: Any) -> str:
    normalized = str(value).strip().lower()
    if normalized in SUPPORTED_CLASSIFIER_MODEL_TYPES:
        return normalized
    raise RuntimeError(
        "Invalid classifier model type: "
        f"{value!r}. Supported values: {sorted(SUPPORTED_CLASSIFIER_MODEL_TYPES)}"
    )


def _parse_mismatch_policy(value: Any) -> str:
    normalized = str(value).strip().lower()
    if normalized in SUPPORTED_ARTIFACT_MISMATCH_POLICIES:
        return normalized
    raise RuntimeError(
        "Invalid classifier artifact mismatch policy: "
        f"{value!r}. Supported values: {sorted(SUPPORTED_ARTIFACT_MISMATCH_POLICIES)}"
    )


def _load_profile_data(profile_path: Path) -> dict[str, Any]:
    if not profile_path.exists():
        return {}
    try:
        raw = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to read runtime profile {profile_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError(f"Runtime profile must be a JSON object: {profile_path}")
    return raw


def resolve_runtime_settings(cli_overrides: dict[str, Any] | None = None) -> RuntimeSettings:
    overrides = cli_overrides or {}
    profile_path = Path(os.getenv("RUNTIME_PROFILE_PATH", str(DEFAULT_RUNTIME_PROFILE_PATH)))
    profile = _load_profile_data(profile_path)

    def choose_value(key: str, env_key: str, default: Any) -> Any:
        if key in overrides and overrides[key] is not None:
            return overrides[key]
        if env_key in os.environ:
            return os.environ[env_key]
        if key in profile:
            return profile[key]
        return default

    alpha = _parse_float(choose_value("alpha", "ALPHA", 0.1), field_name="alpha")
    model_type = _parse_model_type(choose_value("classifier_model_type", "CLASSIFIER_MODEL_TYPE", "embedding"))
    strict_metadata = _parse_bool(
        choose_value("strict_artifact_metadata", "STRICT_ARTIFACT_METADATA", True),
        field_name="strict_artifact_metadata",
    )
    mismatch_policy = _parse_mismatch_policy(
        choose_value(
            "classifier_artifact_mismatch_policy",
            "CLASSIFIER_ARTIFACT_MISMATCH_POLICY",
            "auto_rebuild",
        )
    )

    return RuntimeSettings(
        alpha=alpha,
        classifier_model_type=model_type,
        strict_artifact_metadata=strict_metadata,
        classifier_artifact_mismatch_policy=mismatch_policy,
    )
