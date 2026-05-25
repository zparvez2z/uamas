from reliable_genai.models import ClassifierResult, PredictionResponse, ProductAttributes, ReliabilityMeta
from reliable_genai.evaluation import compute_metrics
from scripts import evaluate


class FakeClassifier:
    is_ready = True
    reason = None
    coverage_threshold = 0.7

    @staticmethod
    def diagnostics():
        return {
            "runtime": "TRAINED",
            "ready": True,
            "reason": None,
            "artifact_path": None,
            "model_type": "embedding",
            "coverage_threshold": 0.7,
            "artifact_load_attempted": True,
            "artifact_load_status": "rejected",
            "artifact_rejection_reason": "classifier artifact metadata train hash mismatch",
            "artifact_metadata": {
                "artifact_format_version": 1,
                "classifier_family": "logistic_regression_text",
                "model_type": "embedding",
                "created_at_utc": "deterministic",
                "python_version": "3.11.0",
                "sklearn_version": "1.0.0",
                "train_row_count": 3,
                "calibration_row_count": 3,
                "train_data_sha256": "trainhash",
                "calibration_data_sha256": "calhash",
                "dataset_fingerprint_sha256": "fphash",
            },
        }


class FakeLLM:
    use_mock = True


class FakeLiveLLM:
    use_mock = False


class FakePipeline:
    alpha = 0.3
    classifier = FakeClassifier()
    llm = FakeLLM()
    max_set_size = 3
    enable_abstain = True

    def predict(self, product):
        if "ambiguous" in product.title:
            category_set = ["Electronics", "Home"]
        elif "abstain" in product.title:
            category_set = []
        else:
            category_set = ["Shoes"]

        return PredictionResponse(
            category_set=category_set,
            attributes=ProductAttributes(),
            reliability=ReliabilityMeta(
                alpha=self.alpha,
                coverage_target=1.0 - self.alpha,
                set_size=len(category_set),
                confidence=0.8,
                abstained=len(category_set) == 0,
                reason="test abstain" if not category_set else None,
                policy_action="abstain" if not category_set else "set_output",
                llm_runtime="MOCK",
                llm_model="test-model",
                classifier_runtime="TRAINED",
                classifier_reason=None,
                classifier_artifact_path=None,
                classifier_model_type="embedding",
                coverage_threshold=0.7,
            ),
        )

    def _classify(self, product):
        return ClassifierResult(
            probabilities={"Shoes": 0.8, "Home": 0.2},
            sorted_labels=["Shoes", "Home"],
        )

    def _conformal_set(self, result):
        return [result.sorted_labels[0]]




class FakeLivePipeline(FakePipeline):
    llm = FakeLiveLLM()

    def predict(self, product):
        response = super().predict(product)
        runtime = "FALLBACK_MOCK" if "fallback" in product.title else "LIVE"
        response.reliability.llm_runtime = runtime
        return response


class FakeLiveWithMockRuntimePipeline(FakePipeline):
    llm = FakeLiveLLM()

    def predict(self, product):
        response = super().predict(product)
        response.reliability.llm_runtime = "MOCK"
        return response


def test_run_evaluation_computes_labeled_metrics(monkeypatch) -> None:
    rows = [
        {"title": "shoe product", "description": "", "category": "Shoes"},
        {"title": "ambiguous product", "description": "", "category": "Home"},
        {"title": "abstain product", "description": "", "category": "Beauty"},
    ]
    monkeypatch.setattr(evaluate, "ReliabilityPipeline", FakePipeline)
    monkeypatch.setattr(evaluate, "load_labeled_dataset", lambda: rows)

    aggregated = evaluate.run_evaluation(use_mock=True)
    metrics = aggregated["metrics"]

    assert aggregated["timestamp"] == "deterministic"
    assert aggregated["include_runtime"] is False
    assert aggregated["classifier_mode"] == "embedding_logreg_calibrated"
    assert aggregated["classifier_runtime"] == "TRAINED"
    assert aggregated["classifier_model_type"] == "embedding"
    assert aggregated["classifier_artifact_load_attempted"] is True
    assert aggregated["classifier_artifact_load_status"] == "rejected"
    assert aggregated["classifier_artifact_rejection_reason"] == "classifier artifact metadata train hash mismatch"
    assert aggregated["coverage_threshold"] == 0.7
    assert aggregated["classifier_artifact_format_version"] == 1
    assert aggregated["classifier_dataset_fingerprint"] == "fphash"
    assert aggregated["llm_runtime_mode"] == "MOCK"
    assert aggregated["review_graph_available"] in {True, False}
    assert aggregated["review_graph_backend"] in {"langgraph", "sequential"}
    assert isinstance(aggregated["review_graph_trigger_rate"], float)
    assert isinstance(aggregated["review_graph_second_pass_rate"], float)
    assert isinstance(aggregated["review_graph_cache_hit_rate"], float)
    assert isinstance(aggregated["review_graph_cached_step_count"], int)
    assert aggregated["runtime_breakdown"] == {
        "live_count": 0,
        "mock_count": 3,
        "fallback_mock_count": 0,
        "fallback_rate": 0.0,
    }
    assert metrics["target_coverage"] == 0.7
    assert metrics["calibrated_cumulative_threshold"] == 0.7
    assert metrics["empirical_coverage"] == 0.667
    assert metrics["selective_coverage"] == 1.0
    assert metrics["top1_accuracy"] == 0.333
    assert metrics["avg_set_size"] == 1.0
    assert metrics["avg_non_abstained_set_size"] == 1.5
    assert metrics["abstention_count"] == 1
    assert metrics["abstention_rate"] == 0.333
    assert metrics["avg_runtime_ms"] == 0.0


def test_save_results_is_stable_without_runtime(monkeypatch, tmp_path) -> None:
    rows = [
        {"title": "shoe product", "description": "", "category": "Shoes"},
    ]
    monkeypatch.setattr(evaluate, "ReliabilityPipeline", FakePipeline)
    monkeypatch.setattr(evaluate, "load_labeled_dataset", lambda: rows)

    aggregated = evaluate.run_evaluation(use_mock=True)
    first_path = tmp_path / "first.md"
    second_path = tmp_path / "second.md"

    evaluate.save_results(aggregated, output_path=str(first_path))
    evaluate.save_results(aggregated, output_path=str(second_path))

    report = first_path.read_text(encoding="utf-8")

    assert report == second_path.read_text(encoding="utf-8")
    assert "**Generated:** deterministic" in report
    assert "## LLM Runtime Breakdown" not in report
    assert "Runtime (ms)" not in report
    assert "avg_runtime_ms" not in report
    assert "**Artifact Load Status:** rejected" in report
    assert "**Artifact Rejection Reason:** classifier artifact metadata train hash mismatch" in report
    assert "- Artifact Format Version: 1" in report
    assert "- Dataset Fingerprint SHA-256: fphash" in report


def test_compute_metrics_handles_selective_coverage() -> None:
    results = [
        {"covered": True, "top1_correct": True, "set_size": 1, "abstained": False, "runtime_ms": 1.0},
        {"covered": True, "top1_correct": False, "set_size": 2, "abstained": False, "runtime_ms": 3.0},
        {"covered": False, "top1_correct": False, "set_size": 0, "abstained": True, "runtime_ms": 2.0},
    ]

    metrics = compute_metrics(
        results=results,
        target_coverage=0.7,
        calibrated_cumulative_threshold=0.76543,
    )

    assert metrics.empirical_coverage == 0.667
    assert metrics.selective_coverage == 1.0
    assert metrics.top1_accuracy == 0.333
    assert metrics.avg_set_size == 1.0
    assert metrics.avg_non_abstained_set_size == 1.5
    assert metrics.calibrated_cumulative_threshold == 0.7654


def test_run_evaluation_live_mode_and_runtime_breakdown(monkeypatch) -> None:
    rows = [
        {"title": "live product", "description": "", "category": "Shoes"},
        {"title": "fallback product", "description": "", "category": "Shoes"},
    ]
    monkeypatch.setattr(evaluate, "ReliabilityPipeline", FakeLivePipeline)
    monkeypatch.setattr(evaluate, "load_labeled_dataset", lambda: rows)

    aggregated = evaluate.run_evaluation(use_mock=False)

    assert aggregated["llm_runtime_mode"] == "LIVE"
    assert aggregated["runtime_breakdown"]["live_count"] == 1
    assert aggregated["runtime_breakdown"]["fallback_mock_count"] == 1
    assert aggregated["runtime_breakdown"]["mock_count"] == 0
    assert aggregated["runtime_breakdown"]["fallback_rate"] == 0.5


def test_run_evaluation_live_mode_treats_mock_runtime_as_fallback(monkeypatch) -> None:
    rows = [
        {"title": "live product", "description": "", "category": "Shoes"},
    ]
    monkeypatch.setattr(evaluate, "ReliabilityPipeline", FakeLiveWithMockRuntimePipeline)
    monkeypatch.setattr(evaluate, "load_labeled_dataset", lambda: rows)

    aggregated = evaluate.run_evaluation(use_mock=False)

    assert aggregated["llm_runtime_mode"] == "LIVE"
    assert aggregated["runtime_breakdown"]["live_count"] == 0
    assert aggregated["runtime_breakdown"]["mock_count"] == 0
    assert aggregated["runtime_breakdown"]["fallback_mock_count"] == 1


def test_save_results_includes_runtime_breakdown(monkeypatch, tmp_path) -> None:
    rows = [
        {"title": "live product", "description": "", "category": "Shoes"},
        {"title": "fallback product", "description": "", "category": "Shoes"},
    ]
    monkeypatch.setattr(evaluate, "ReliabilityPipeline", FakeLivePipeline)
    monkeypatch.setattr(evaluate, "load_labeled_dataset", lambda: rows)

    aggregated = evaluate.run_evaluation(use_mock=False)
    output = tmp_path / "report.md"
    evaluate.save_results(aggregated, output_path=str(output))
    report = output.read_text(encoding="utf-8")

    assert "## LLM Runtime Breakdown" in report
    assert "- LIVE calls: 1" in report
    assert "- FALLBACK_MOCK calls: 1" in report


def test_resolve_use_mock_defaults_to_mock() -> None:
    args = evaluate.argparse.Namespace(live=False, mock=False)
    assert evaluate.resolve_use_mock(args) is True


def test_resolve_use_mock_live_overrides_default() -> None:
    args = evaluate.argparse.Namespace(live=True, mock=False)
    assert evaluate.resolve_use_mock(args) is False
