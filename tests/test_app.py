from app.main import build_diagnostics


def test_diagnostics_include_classifier_runtime_metadata() -> None:
    diagnostics = build_diagnostics()

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
