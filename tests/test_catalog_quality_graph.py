from pathlib import Path

from reliable_genai.agents import AttributeExtractionAgent, PolicyAgent
from reliable_genai.catalog_quality_graph import CatalogQualityGraph
from reliable_genai.models import (
    ClassifierResult,
    ListingInput,
    ProductAttributes,
    ProductInput,
)
from reliable_genai.persistence import SQLiteReviewStore
from reliable_genai.pipeline import (
    AttributeExtractionStageResult,
    ClassificationStageResult,
    ReliabilityPipeline,
)
from reliable_genai.scoring import PolicyDecision
from reliable_genai.semantic_scorer import SemanticConsistencyResult


class StubStagePipeline:
    alpha = 0.1
    max_set_size = 3
    enable_abstain = True

    def __init__(
        self,
        *,
        confidence: float = 0.9,
        category_set: list[str] | None = None,
        semantic_score: float | None = 0.8,
        semantic_status: str = "ok",
        extraction_runtime: str = "MOCK",
    ) -> None:
        self.confidence = confidence
        self.category_set = category_set if category_set is not None else ["Shoes"]
        self.semantic_score = semantic_score
        self.semantic_status = semantic_status
        self.extraction_runtime = extraction_runtime
        self.classify_calls = 0
        self.extract_calls = 0
        self.semantic_calls = 0

    def classify(self, item: ProductInput) -> ClassificationStageResult:
        self.classify_calls += 1
        other_probability = max(0.0, 1.0 - self.confidence) / 5
        probabilities = {
            "Shoes": self.confidence,
            "Sports": other_probability,
            "Clothing": other_probability,
            "Electronics": other_probability,
            "Home": other_probability,
            "Beauty": other_probability,
        }
        abstained = not self.category_set
        return ClassificationStageResult(
            classifier_result=ClassifierResult(
                probabilities=probabilities,
                sorted_labels=["Shoes", "Sports"],
            ),
            candidate_category_set=list(self.category_set),
            policy=PolicyDecision(
                category_set=list(self.category_set),
                abstained=abstained,
                reason="Prediction set outside usability constraints" if abstained else None,
                action="abstain" if abstained else "set_output",
            ),
            diagnostics={
                "runtime": "ARTIFACT",
                "reason": None,
                "artifact_path": "artifacts/classifier.joblib",
                "model_type": "embedding",
                "artifact_load_attempted": True,
                "artifact_load_status": "loaded",
                "artifact_rejection_reason": None,
                "artifact_rebuild_attempted": False,
                "artifact_rebuild_status": "not_needed",
                "artifact_rebuild_reason": None,
                "coverage_threshold": 0.9,
            },
        )

    def extract_attributes(self, item: ProductInput) -> AttributeExtractionStageResult:
        self.extract_calls += 1
        return AttributeExtractionStageResult(
            attributes=ProductAttributes(
                brand="Acme",
                color="black",
                material="mesh",
                size="42",
            ),
            runtime=self.extraction_runtime,
            model="test-model",
            error="provider_failed" if self.extraction_runtime == "FALLBACK_MOCK" else None,
        )

    def score_semantic(
        self,
        item: ProductInput,
        *,
        candidate_labels: list[str],
    ) -> SemanticConsistencyResult:
        self.semantic_calls += 1
        return SemanticConsistencyResult(
            score=self.semantic_score,
            status=self.semantic_status,
            reason="embedding_client_unavailable" if self.semantic_status == "degraded" else None,
        )

    def assemble_prediction(self, **kwargs):
        return ReliabilityPipeline.assemble_prediction(self, **kwargs)


class StubReviewRunner:
    def __init__(self) -> None:
        self.calls = 0

    def review_first_pass(self, item: ProductInput, first_response):
        self.calls += 1
        response = first_response.model_copy(deep=True)
        response.reliability.review_outcome = "disabled"
        return response

    @staticmethod
    def diagnostics() -> dict[str, object]:
        return {
            "confidence_threshold": 0.55,
            "semantic_threshold": 0.4,
        }


def _build_graph(
    tmp_path: Path,
    pipeline: StubStagePipeline,
) -> tuple[CatalogQualityGraph, SQLiteReviewStore, StubReviewRunner]:
    store = SQLiteReviewStore(tmp_path / "uamas.db")
    review_runner = StubReviewRunner()
    graph = CatalogQualityGraph(
        pipeline,
        review_runner,
        store,
        confidence_threshold=0.55,
        semantic_threshold=0.4,
        max_auto_accept_set_size=3,
    )
    return graph, store, review_runner


def test_catalog_graph_auto_accepts_with_one_call_per_specialist(tmp_path: Path) -> None:
    pipeline = StubStagePipeline()
    graph, store, review_runner = _build_graph(tmp_path, pipeline)

    decision = graph.analyze(
        ListingInput(
            external_id="seller-123",
            title="Acme running shoe",
            description="Black mesh road shoe size 42",
        )
    )

    assert decision.decision == "auto_accept"
    assert decision.risk_level == "low"
    assert decision.review_task_id is None
    assert pipeline.classify_calls == 1
    assert pipeline.extract_calls == 1
    assert pipeline.semantic_calls == 1
    assert review_runner.calls == 1
    assert [trace.agent for trace in decision.agent_trace] == [
        "classifier_agent",
        "attribute_extraction_agent",
        "semantic_critic_agent",
        "policy_agent",
        "human_review_agent",
        "decision_agent",
    ]
    assert decision.agent_trace[-2].status == "skipped"
    assert store.diagnostics()["review_task_count"] == 0


def test_catalog_graph_routes_low_confidence_to_human_review(tmp_path: Path) -> None:
    pipeline = StubStagePipeline(confidence=0.2)
    graph, store, _ = _build_graph(tmp_path, pipeline)

    decision = graph.analyze(
        ListingInput(title="Ambiguous product", description="Could fit multiple categories")
    )

    assert decision.decision == "needs_human_review"
    assert decision.review_task_id is not None
    task = store.get_review_task(decision.review_task_id)
    assert task is not None
    assert task.reason == "low_confidence"
    human_trace = next(trace for trace in decision.agent_trace if trace.agent == "human_review_agent")
    assert human_trace.status == "created"


def test_catalog_graph_ignores_degraded_semantic_score_for_policy(tmp_path: Path) -> None:
    pipeline = StubStagePipeline(
        confidence=0.9,
        semantic_score=None,
        semantic_status="degraded",
    )
    graph, _, _ = _build_graph(tmp_path, pipeline)

    decision = graph.analyze(
        ListingInput(title="Acme running shoe", description="Black mesh road shoe")
    )

    assert decision.decision == "auto_accept"
    semantic_trace = next(trace for trace in decision.agent_trace if trace.agent == "semantic_critic_agent")
    assert semantic_trace.status == "degraded"
    assert semantic_trace.reason == "embedding_client_unavailable"


def test_catalog_graph_sequential_fallback_matches_graph_routing(tmp_path: Path) -> None:
    graph_pipeline = StubStagePipeline(confidence=0.9, semantic_score=0.1)
    graph, _, _ = _build_graph(tmp_path / "graph", graph_pipeline)
    graph_decision = graph.analyze(ListingInput(title="Conflicting listing", description="Unrelated content"))

    sequential_pipeline = StubStagePipeline(confidence=0.9, semantic_score=0.1)
    sequential, _, _ = _build_graph(tmp_path / "sequential", sequential_pipeline)
    sequential._graph = None
    sequential.available = False
    sequential.backend = "sequential"
    sequential.reason = "test_fallback"
    sequential_decision = sequential.analyze(
        ListingInput(title="Conflicting listing", description="Unrelated content")
    )

    assert graph_decision.decision == sequential_decision.decision == "needs_human_review"
    assert graph_decision.risk_level == sequential_decision.risk_level == "high"
    assert graph_decision.explanation == sequential_decision.explanation
    assert graph_decision.reliability == sequential_decision.reliability
    assert [trace.agent for trace in graph_decision.agent_trace] == [
        trace.agent for trace in sequential_decision.agent_trace
    ]


def test_policy_agent_preserves_semantic_degrade_and_low_score_rules() -> None:
    policy = PolicyAgent(
        confidence_threshold=0.55,
        semantic_threshold=0.4,
        max_auto_accept_set_size=3,
    )
    pipeline = StubStagePipeline(semantic_score=None, semantic_status="degraded")
    item = ProductInput(title="shoe", description="mesh")
    degraded_prediction = pipeline.assemble_prediction(
        classification=pipeline.classify(item),
        extraction=pipeline.extract_attributes(item),
        semantic=pipeline.score_semantic(item, candidate_labels=["Shoes"]),
    )

    assert policy.run(degraded_prediction).decision == "auto_accept"

    low_semantic_pipeline = StubStagePipeline(semantic_score=0.1, semantic_status="ok")
    low_prediction = low_semantic_pipeline.assemble_prediction(
        classification=low_semantic_pipeline.classify(item),
        extraction=low_semantic_pipeline.extract_attributes(item),
        semantic=low_semantic_pipeline.score_semantic(item, candidate_labels=["Shoes"]),
    )

    result = policy.run(low_prediction)
    assert result.decision == "needs_human_review"
    assert result.reason == "low_semantic_consistency"


def test_attribute_agent_trace_marks_live_fallback_as_degraded() -> None:
    pipeline = StubStagePipeline(extraction_runtime="FALLBACK_MOCK")
    agent = AttributeExtractionAgent(pipeline)

    result = agent.run(ProductInput(title="shoe", description="mesh"))
    trace = agent.trace(result)

    assert trace.status == "degraded"
    assert trace.reason == "provider_failed"
