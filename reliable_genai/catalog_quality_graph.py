from __future__ import annotations

import os
from typing import Any, TypedDict

from .agents import (
    AttributeExtractionAgent,
    ClassifierAgent,
    DecisionAgent,
    HumanReviewAgent,
    PolicyAgent,
    SemanticCriticAgent,
    WorkflowPolicyResult,
)
from .models import (
    AgentTrace,
    CatalogQualityDecision,
    ListingInput,
    PredictionResponse,
    ProductInput,
)
from .persistence import SQLiteReviewStore
from .pipeline import (
    AttributeExtractionStageResult,
    ClassificationStageResult,
    ReliabilityPipeline,
)
from .review_graph import ReviewGraphRunner
from .semantic_scorer import SemanticConsistencyResult

try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - exercised through availability checks.
    LANGGRAPH_AVAILABLE = False


class CatalogQualityState(TypedDict, total=False):
    listing: ListingInput
    item: ProductInput
    classification: ClassificationStageResult
    extraction: AttributeExtractionStageResult
    semantic: SemanticConsistencyResult
    prediction: PredictionResponse
    listing_id: str
    prediction_id: str
    policy: WorkflowPolicyResult
    review_task_id: str | None
    classifier_trace: AgentTrace
    extraction_trace: AgentTrace
    semantic_trace: AgentTrace
    policy_trace: AgentTrace
    human_review_trace: AgentTrace
    decision: CatalogQualityDecision


class CatalogQualityGraph:
    """Coordinates specialist catalog agents and operational routing."""

    def __init__(
        self,
        pipeline: ReliabilityPipeline,
        review_graph: ReviewGraphRunner,
        store: SQLiteReviewStore,
        *,
        confidence_threshold: float | None = None,
        semantic_threshold: float | None = None,
        max_auto_accept_set_size: int | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.review_graph = review_graph
        self.store = store

        review_diagnostics = review_graph.diagnostics()
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else float(
                review_diagnostics.get(
                    "confidence_threshold",
                    os.getenv("REVIEW_CONFIDENCE_THRESHOLD", "0.55"),
                )
            )
        )
        self.semantic_threshold = (
            semantic_threshold
            if semantic_threshold is not None
            else float(
                review_diagnostics.get(
                    "semantic_threshold",
                    os.getenv("SEMANTIC_CONSISTENCY_THRESHOLD", "0.4"),
                )
            )
        )
        self.max_auto_accept_set_size = (
            max_auto_accept_set_size
            if max_auto_accept_set_size is not None
            else int(os.getenv("MAX_AUTO_ACCEPT_SET_SIZE", str(pipeline.max_set_size)))
        )

        self.classifier_agent = ClassifierAgent(pipeline)
        self.extraction_agent = AttributeExtractionAgent(pipeline)
        self.semantic_agent = SemanticCriticAgent(
            pipeline,
            threshold=self.semantic_threshold,
        )
        self.policy_agent = PolicyAgent(
            confidence_threshold=self.confidence_threshold,
            semantic_threshold=self.semantic_threshold,
            max_auto_accept_set_size=self.max_auto_accept_set_size,
        )
        self.human_review_agent = HumanReviewAgent(store)
        self.decision_agent = DecisionAgent()

        self.available = LANGGRAPH_AVAILABLE
        self.backend = "langgraph" if self.available else "sequential"
        self.reason = "ok" if self.available else "langgraph_not_installed"
        self._graph: Any | None = None
        if self.available:
            try:
                self._graph = self._compile_graph()
            except Exception as exc:  # pragma: no cover - defensive runtime fallback.
                self.available = False
                self.backend = "sequential"
                self.reason = f"graph_compile_failed: {exc}"

    def _compile_graph(self) -> Any:
        builder = StateGraph(CatalogQualityState)
        builder.add_node("classifier_agent", self._node_classifier)
        builder.add_node("attribute_extraction_agent", self._node_extraction)
        builder.add_node("semantic_critic_agent", self._node_semantic)
        builder.add_node("assemble_prediction", self._node_assemble_prediction)
        builder.add_node("optional_review", self._node_optional_review)
        builder.add_node("persist_analysis", self._node_persist_analysis)
        builder.add_node("policy_agent", self._node_policy)
        builder.add_node("human_review_agent", self._node_human_review)
        builder.add_node("decision_agent", self._node_decision)

        builder.add_edge(START, "classifier_agent")
        builder.add_edge(START, "attribute_extraction_agent")
        builder.add_edge("classifier_agent", "semantic_critic_agent")
        builder.add_edge(
            ["attribute_extraction_agent", "semantic_critic_agent"],
            "assemble_prediction",
        )
        builder.add_edge("assemble_prediction", "optional_review")
        builder.add_edge("optional_review", "persist_analysis")
        builder.add_edge("persist_analysis", "policy_agent")
        builder.add_conditional_edges(
            "policy_agent",
            self._route_after_policy,
            {
                "human_review_agent": "human_review_agent",
                "decision_agent": "decision_agent",
            },
        )
        builder.add_edge("human_review_agent", "decision_agent")
        builder.add_edge("decision_agent", END)
        return builder.compile()

    def _node_classifier(self, state: CatalogQualityState) -> CatalogQualityState:
        result = self.classifier_agent.run(state["item"])
        return {
            "classification": result,
            "classifier_trace": self.classifier_agent.trace(result),
        }

    def _node_extraction(self, state: CatalogQualityState) -> CatalogQualityState:
        result = self.extraction_agent.run(state["item"])
        return {
            "extraction": result,
            "extraction_trace": self.extraction_agent.trace(result),
        }

    def _node_semantic(self, state: CatalogQualityState) -> CatalogQualityState:
        result = self.semantic_agent.run(
            state["item"],
            state["classification"],
        )
        return {
            "semantic": result,
            "semantic_trace": self.semantic_agent.trace(result),
        }

    def _node_assemble_prediction(self, state: CatalogQualityState) -> CatalogQualityState:
        prediction = self.pipeline.assemble_prediction(
            classification=state["classification"],
            extraction=state["extraction"],
            semantic=state["semantic"],
        )
        return {"prediction": prediction}

    def _node_optional_review(self, state: CatalogQualityState) -> CatalogQualityState:
        prediction = self.review_graph.review_first_pass(
            state["item"],
            state["prediction"],
        )
        return {"prediction": prediction}

    def _node_persist_analysis(self, state: CatalogQualityState) -> CatalogQualityState:
        listing_id = self.store.create_listing(state["listing"])
        prediction_id = self.store.create_prediction(listing_id, state["prediction"])
        return {
            "listing_id": listing_id,
            "prediction_id": prediction_id,
        }

    def _node_policy(self, state: CatalogQualityState) -> CatalogQualityState:
        result = self.policy_agent.run(state["prediction"])
        return {
            "policy": result,
            "policy_trace": self.policy_agent.trace(result),
        }

    @staticmethod
    def _route_after_policy(state: CatalogQualityState) -> str:
        if state["policy"].decision == "needs_human_review":
            return "human_review_agent"
        return "decision_agent"

    def _node_human_review(self, state: CatalogQualityState) -> CatalogQualityState:
        review_task_id = self.human_review_agent.run(
            listing_id=state["listing_id"],
            prediction_id=state["prediction_id"],
            policy=state["policy"],
        )
        return {
            "review_task_id": review_task_id,
            "human_review_trace": self.human_review_agent.trace(
                review_task_id=review_task_id,
                reason=state["policy"].reason,
            ),
        }

    def _node_decision(self, state: CatalogQualityState) -> CatalogQualityState:
        human_trace = state.get("human_review_trace")
        if human_trace is None:
            human_trace = self.human_review_agent.trace(
                review_task_id=None,
                reason=state["policy"].reason,
            )
        traces = [
            state["classifier_trace"],
            state["extraction_trace"],
            state["semantic_trace"],
            state["policy_trace"],
            human_trace,
        ]
        decision = self.decision_agent.run(
            listing=state["listing"],
            listing_id=state["listing_id"],
            prediction=state["prediction"],
            policy=state["policy"],
            review_task_id=state.get("review_task_id"),
            agent_trace=traces,
        )
        return {"decision": decision}

    def _sequential_analyze(self, listing: ListingInput) -> CatalogQualityDecision:
        state: CatalogQualityState = {
            "listing": listing,
            "item": ProductInput(title=listing.title, description=listing.description),
        }
        for node in (
            self._node_classifier,
            self._node_extraction,
            self._node_semantic,
            self._node_assemble_prediction,
            self._node_optional_review,
            self._node_persist_analysis,
            self._node_policy,
        ):
            state.update(node(state))
        if self._route_after_policy(state) == "human_review_agent":
            state.update(self._node_human_review(state))
        state.update(self._node_decision(state))
        return state["decision"]

    def analyze(self, listing: ListingInput) -> CatalogQualityDecision:
        graph_input: CatalogQualityState = {
            "listing": listing,
            "item": ProductInput(title=listing.title, description=listing.description),
        }
        if self._graph is None:
            return self._sequential_analyze(listing)
        state = self._graph.invoke(graph_input)
        return state["decision"]

    def diagnostics(self) -> dict[str, object]:
        return {
            "available": self.available,
            "backend": self.backend,
            "reason": self.reason,
            "confidence_threshold": self.confidence_threshold,
            "semantic_threshold": self.semantic_threshold,
            "max_auto_accept_set_size": self.max_auto_accept_set_size,
        }
