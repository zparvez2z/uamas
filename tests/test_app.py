from app.main import build_diagnostics


def test_diagnostics_include_classifier_runtime_metadata() -> None:
    diagnostics = build_diagnostics()

    assert diagnostics["classifier_runtime"] in {"ARTIFACT", "TRAINED", "FALLBACK"}
    assert "classifier_ready" in diagnostics
    assert "classifier_reason" in diagnostics
    assert "classifier_artifact_path" in diagnostics
    assert isinstance(diagnostics["coverage_threshold"], float)
