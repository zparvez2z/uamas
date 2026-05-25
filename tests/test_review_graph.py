from reliable_genai.models import (
    ClassifierResult,
    PredictionResponse,
    ProductAttributes,
    ProductInput,
    ReliabilityMeta,
)
from reliable_genai.review_graph import ReviewGraphRunner


def build_response(
    *,
    confidence: float,
    set_size: int,
    abstained: bool = False,
) -> PredictionResponse:
    category_set = [] if abstained else [f"L{i}" for i in range(set_size)]
    return PredictionResponse(
        category_set=category_set,
        attributes=ProductAttributes(),
        reliability=ReliabilityMeta(
            alpha=0.1,
            coverage_target=0.9,
            set_size=len(category_set),
            confidence=confidence,
            abstained=abstained,
            reason="abstained" if abstained else None,
            policy_action="abstain" if abstained else "set_output",
            llm_runtime="MOCK",
            llm_model="test-model",
            classifier_runtime="TRAINED",
            classifier_reason=None,
            classifier_artifact_path=None,
            classifier_model_type="embedding",
            coverage_threshold=0.7,
        ),
    )


class StubPipeline:
    def __init__(self, responses, second_pass_confidences=None):
        self.responses = responses
        self.predict_calls = 0
        self.classify_calls = 0
        self.max_set_size = 3
        self.enable_abstain = True
        self.second_pass_confidences = second_pass_confidences or []

    def predict(self, item: ProductInput) -> PredictionResponse:
        idx = min(self.predict_calls, len(self.responses) - 1)
        self.predict_calls += 1
        return self.responses[idx]

    def _classify(self, item: ProductInput) -> ClassifierResult:
        idx = min(self.classify_calls, len(self.second_pass_confidences) - 1)
        self.classify_calls += 1
        confidence = self.second_pass_confidences[idx]
        return ClassifierResult(
            probabilities={"L0": confidence, "L1": 1.0 - confidence},
            sorted_labels=["L0", "L1"],
        )

    def _conformal_set(self, result: ClassifierResult):
        if result.probabilities["L0"] >= 0.5:
            return ["L0"]
        return []


def test_review_graph_disabled_keeps_single_pass() -> None:
    pipeline = StubPipeline([build_response(confidence=0.9, set_size=1)])
    runner = ReviewGraphRunner(pipeline, enabled=False)

    response = runner.predict(ProductInput(title="product", description="desc"))

    assert pipeline.predict_calls == 1
    assert pipeline.classify_calls == 0
    assert response.reliability.review_graph_used is False
    assert response.reliability.review_trigger_reason is None
    assert response.reliability.review_outcome == "disabled"


def test_review_graph_enabled_not_triggered_keeps_first_pass() -> None:
    pipeline = StubPipeline([build_response(confidence=0.9, set_size=1)])
    runner = ReviewGraphRunner(
        pipeline,
        enabled=True,
        confidence_threshold=0.5,
        set_size_trigger=3,
    )

    response = runner.predict(ProductInput(title="product", description="desc"))

    assert pipeline.predict_calls == 1
    assert pipeline.classify_calls == 0
    assert response.reliability.review_graph_used is False
    assert response.reliability.review_trigger_reason is None
    assert response.reliability.review_outcome == "not_triggered"


def test_review_graph_triggered_runs_second_pass_and_selects_better_response() -> None:
    pipeline = StubPipeline(
        [build_response(confidence=0.2, set_size=1)],
        second_pass_confidences=[0.85],
    )
    runner = ReviewGraphRunner(
        pipeline,
        enabled=True,
        confidence_threshold=0.5,
        set_size_trigger=3,
    )

    response = runner.predict(ProductInput(title="product", description="desc"))

    assert pipeline.predict_calls == 1
    assert pipeline.classify_calls == 1
    assert response.reliability.review_graph_used is True
    assert response.reliability.review_trigger_reason == "low_confidence"
    assert response.reliability.review_outcome == "second_pass_selected"
    assert response.reliability.confidence == 0.85


def test_review_graph_cache_hits_on_repeated_triggered_input() -> None:
    pipeline = StubPipeline(
        [build_response(confidence=0.2, set_size=1)],
        second_pass_confidences=[0.85],
    )
    runner = ReviewGraphRunner(
        pipeline,
        enabled=True,
        confidence_threshold=0.5,
        set_size_trigger=3,
        cache_ttl_seconds=300,
    )
    item = ProductInput(title="same item", description="same description")

    first = runner.predict(item)
    second = runner.predict(item)
    diagnostics = runner.diagnostics()

    assert first.reliability.review_outcome == "second_pass_selected"
    assert second.reliability.review_outcome == "second_pass_selected"
    assert pipeline.predict_calls == 2
    assert pipeline.classify_calls == 1
    assert diagnostics["review_graph_cached_step_count"] >= 1
    assert diagnostics["review_graph_cache_hit_rate"] > 0.0


def test_invoke_context_overrides_env_defaults(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_LANGGRAPH_REVIEW", "false")
    monkeypatch.setenv("REVIEW_CONFIDENCE_THRESHOLD", "0.95")

    pipeline = StubPipeline(
        [build_response(confidence=0.2, set_size=1)],
        second_pass_confidences=[0.85],
    )
    runner = ReviewGraphRunner(pipeline)
    response = runner.predict(
        ProductInput(title="product", description="desc"),
        context={"enabled": True, "confidence_threshold": 0.5},
    )

    assert response.reliability.review_trigger_reason == "low_confidence"
    assert response.reliability.review_outcome == "second_pass_selected"
