from reliable_genai.models import PredictionResponse, ProductAttributes, ReliabilityMeta
from reliable_genai.evaluation import compute_metrics
from scripts import evaluate


class FakeClassifier:
    is_ready = True
    reason = None
    coverage_threshold = 0.7


class FakeLLM:
    use_mock = True


class FakePipeline:
    alpha = 0.3
    classifier = FakeClassifier()
    llm = FakeLLM()

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
            ),
        )


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

    assert aggregated["classifier_mode"] == "tfidf_logreg_calibrated"
    assert aggregated["llm_runtime_mode"] == "MOCK"
    assert metrics["target_coverage"] == 0.7
    assert metrics["calibrated_cumulative_threshold"] == 0.7
    assert metrics["empirical_coverage"] == 0.667
    assert metrics["selective_coverage"] == 1.0
    assert metrics["top1_accuracy"] == 0.333
    assert metrics["avg_set_size"] == 1.0
    assert metrics["avg_non_abstained_set_size"] == 1.5
    assert metrics["abstention_count"] == 1
    assert metrics["abstention_rate"] == 0.333


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
