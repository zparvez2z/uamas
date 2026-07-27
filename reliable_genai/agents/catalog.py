from __future__ import annotations

from dataclasses import dataclass

from reliable_genai.models import (
    AgentTrace,
    CatalogQualityDecision,
    ListingInput,
    PredictionResponse,
    ProductInput,
)
from reliable_genai.persistence import SQLiteReviewStore
from reliable_genai.pipeline import (
    AttributeExtractionStageResult,
    ClassificationStageResult,
    ReliabilityPipeline,
)
from reliable_genai.semantic_scorer import SemanticConsistencyResult


@dataclass(frozen=True)
class WorkflowPolicyResult:
    decision: str
    risk_level: str
    reason: str | None
    explanation: str


class ClassifierAgent:
    def __init__(self, pipeline: ReliabilityPipeline) -> None:
        self.pipeline = pipeline

    def run(self, item: ProductInput) -> ClassificationStageResult:
        return self.pipeline.classify(item)

    @staticmethod
    def trace(result: ClassificationStageResult) -> AgentTrace:
        runtime = str(result.diagnostics["runtime"])
        return AgentTrace(
            agent="classifier_agent",
            status="ok" if runtime in {"ARTIFACT", "TRAINED"} else "degraded",
            output={
                "category_set": result.policy.category_set,
                "confidence": max(result.classifier_result.probabilities.values()),
                "set_size": len(result.policy.category_set),
                "abstained": result.policy.abstained,
                "runtime": runtime,
            },
            reason=result.policy.reason or result.diagnostics.get("reason"),
        )


class AttributeExtractionAgent:
    def __init__(self, pipeline: ReliabilityPipeline) -> None:
        self.pipeline = pipeline

    def run(self, item: ProductInput) -> AttributeExtractionStageResult:
        return self.pipeline.extract_attributes(item)

    @staticmethod
    def trace(result: AttributeExtractionStageResult) -> AgentTrace:
        degraded = result.runtime == "FALLBACK_MOCK"
        return AgentTrace(
            agent="attribute_extraction_agent",
            status="degraded" if degraded else "ok",
            output={
                **result.attributes.model_dump(),
                "runtime": result.runtime,
                "model": result.model,
            },
            reason=result.error,
        )


class SemanticCriticAgent:
    def __init__(self, pipeline: ReliabilityPipeline, *, threshold: float) -> None:
        self.pipeline = pipeline
        self.threshold = threshold

    def run(
        self,
        item: ProductInput,
        classification: ClassificationStageResult,
    ) -> SemanticConsistencyResult:
        return self.pipeline.score_semantic(
            item,
            candidate_labels=classification.candidate_category_set,
        )

    def trace(self, result: SemanticConsistencyResult) -> AgentTrace:
        return AgentTrace(
            agent="semantic_critic_agent",
            status=result.status,
            output={
                "score": result.score,
                "threshold": self.threshold,
            },
            reason=result.reason,
        )


class PolicyAgent:
    def __init__(
        self,
        *,
        confidence_threshold: float,
        semantic_threshold: float,
        max_auto_accept_set_size: int,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.semantic_threshold = semantic_threshold
        self.max_auto_accept_set_size = max_auto_accept_set_size

    def run(self, prediction: PredictionResponse) -> WorkflowPolicyResult:
        reliability = prediction.reliability
        semantic_score = reliability.semantic_consistency_score

        if reliability.abstained or not prediction.category_set:
            reason = reliability.reason or reliability.review_trigger_reason or "abstained"
            return WorkflowPolicyResult(
                decision="needs_human_review",
                risk_level="high",
                reason=reason,
                explanation="Classifier abstained or returned no category set.",
            )

        if len(prediction.category_set) > self.max_auto_accept_set_size:
            return WorkflowPolicyResult(
                decision="needs_human_review",
                risk_level="high",
                reason="large_set",
                explanation="Category set is too large for automatic acceptance.",
            )

        if reliability.confidence < self.confidence_threshold:
            return WorkflowPolicyResult(
                decision="needs_human_review",
                risk_level="high",
                reason="low_confidence",
                explanation="Classifier confidence is below review threshold.",
            )

        if (
            reliability.semantic_consistency_status == "ok"
            and semantic_score is not None
            and semantic_score < self.semantic_threshold
        ):
            return WorkflowPolicyResult(
                decision="needs_human_review",
                risk_level="high",
                reason="low_semantic_consistency",
                explanation="Semantic consistency score is below review threshold.",
            )

        risk_level = "low" if len(prediction.category_set) == 1 else "medium"
        return WorkflowPolicyResult(
            decision="auto_accept",
            risk_level=risk_level,
            reason=None,
            explanation="Listing passed automatic catalog quality checks.",
        )

    @staticmethod
    def trace(result: WorkflowPolicyResult) -> AgentTrace:
        return AgentTrace(
            agent="policy_agent",
            status="ok",
            output={
                "decision": result.decision,
                "risk_level": result.risk_level,
            },
            reason=result.reason,
        )


class HumanReviewAgent:
    def __init__(self, store: SQLiteReviewStore) -> None:
        self.store = store

    def run(
        self,
        *,
        workflow_run_id: str,
        listing_id: str,
        prediction_id: str,
        policy: WorkflowPolicyResult,
    ) -> str:
        task = self.store.create_review_task_for_workflow(
            workflow_run_id,
            listing_id=listing_id,
            prediction_id=prediction_id,
            reason=policy.reason or "needs_human_review",
            risk_level=policy.risk_level,
        )
        return task.id

    @staticmethod
    def trace(
        *,
        review_task_id: str | None,
        reason: str | None,
    ) -> AgentTrace:
        return AgentTrace(
            agent="human_review_agent",
            status="created" if review_task_id else "skipped",
            output={"review_task_id": review_task_id},
            reason=reason,
        )


class DecisionAgent:
    @staticmethod
    def run(
        *,
        listing: ListingInput,
        listing_id: str,
        workflow_run_id: str,
        prediction: PredictionResponse,
        policy: WorkflowPolicyResult,
        review_task_id: str | None,
        agent_trace: list[AgentTrace],
    ) -> CatalogQualityDecision:
        trace = [
            *agent_trace,
            AgentTrace(
                agent="decision_agent",
                status="completed",
                output={
                    "decision": policy.decision,
                    "listing_id": listing_id,
                    "external_id": listing.external_id,
                },
                reason=policy.reason,
            ),
        ]
        return CatalogQualityDecision(
            listing_id=listing_id,
            workflow_run_id=workflow_run_id,
            decision=policy.decision,
            risk_level=policy.risk_level,
            explanation=policy.explanation,
            category_set=prediction.category_set,
            attributes=prediction.attributes,
            reliability=prediction.reliability,
            agent_trace=trace,
            review_task_id=review_task_id,
        )
