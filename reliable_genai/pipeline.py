import os
from dataclasses import dataclass
from typing import Any, Dict, List

from .classifier import CalibratedTextClassifier
from .llm_wrappers import GitHubModelsClient
from .models import (
    ClassifierResult,
    PredictionResponse,
    ProductAttributes,
    ProductInput,
    ReliabilityMeta,
)
from .runtime_profile import resolve_runtime_settings
from .semantic_scorer import SemanticConsistencyResult, SemanticConsistencyScorer
from .scoring import PolicyDecision, apply_abstention_policy, build_prediction_set


@dataclass(frozen=True)
class ClassificationStageResult:
    classifier_result: ClassifierResult
    candidate_category_set: list[str]
    policy: PolicyDecision
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class AttributeExtractionStageResult:
    attributes: ProductAttributes
    runtime: str
    model: str
    error: str | None


class ReliabilityPipeline:
    """Minimal uncertainty-aware pipeline for demo purposes."""

    LABELS = [
        "Shoes",
        "Clothing",
        "Electronics",
        "Home",
        "Beauty",
        "Sports",
    ]

    KEYWORDS: Dict[str, List[str]] = {
        "Shoes": ["shoe", "sneaker", "boot", "running"],
        "Clothing": ["shirt", "hoodie", "jacket", "pants", "dress"],
        "Electronics": ["phone", "laptop", "charger", "headphone", "tv"],
        "Home": ["chair", "table", "lamp", "kitchen", "sofa"],
        "Beauty": ["cream", "shampoo", "serum", "makeup"],
        "Sports": ["fitness", "yoga", "dumbbell", "cycling", "ball"],
    }

    def __init__(
        self,
        *,
        alpha: float | None = None,
        classifier_model_type: str | None = None,
        strict_artifact_metadata: bool | None = None,
        classifier_artifact_mismatch_policy: str | None = None,
    ) -> None:
        settings = resolve_runtime_settings(
            {
                "alpha": alpha,
                "classifier_model_type": classifier_model_type,
                "strict_artifact_metadata": strict_artifact_metadata,
                "classifier_artifact_mismatch_policy": classifier_artifact_mismatch_policy,
            }
        )
        self.alpha = settings.alpha
        self.max_set_size = int(os.getenv("MAX_SET_SIZE", "3"))
        self.enable_abstain = os.getenv("ENABLE_ABSTAIN", "true").lower() == "true"
        self.llm = GitHubModelsClient()
        self.semantic_scorer = SemanticConsistencyScorer(self.LABELS)
        self.classifier = CalibratedTextClassifier(
            self.LABELS,
            self.alpha,
            model_type=settings.classifier_model_type,
            strict_artifact_metadata=settings.strict_artifact_metadata,
            artifact_mismatch_policy=settings.classifier_artifact_mismatch_policy,
        )

    def predict(self, item: ProductInput) -> PredictionResponse:
        classification = self.classify(item)
        semantic = self.score_semantic(
            item,
            candidate_labels=classification.candidate_category_set,
        )
        extraction = self.extract_attributes(item)
        return self.assemble_prediction(
            classification=classification,
            extraction=extraction,
            semantic=semantic,
        )

    def classify(self, item: ProductInput) -> ClassificationStageResult:
        classifier_result = self._classify(item)
        category_set = self._conformal_set(classifier_result)
        policy = apply_abstention_policy(
            category_set=category_set,
            max_set_size=self.max_set_size,
            enable_abstain=self.enable_abstain,
        )
        return ClassificationStageResult(
            classifier_result=classifier_result,
            candidate_category_set=category_set,
            policy=policy,
            diagnostics=self.classifier.diagnostics(),
        )

    def extract_attributes(self, item: ProductInput) -> AttributeExtractionStageResult:
        attributes = self.llm.extract_attributes(item.title, item.description)
        return AttributeExtractionStageResult(
            attributes=attributes,
            runtime=self.llm.last_runtime,
            model=self.llm.model,
            error=self.llm.last_error,
        )

    def score_semantic(
        self,
        item: ProductInput,
        *,
        candidate_labels: list[str],
    ) -> SemanticConsistencyResult:
        return self.semantic_scorer.score(item, candidate_labels=candidate_labels)

    def assemble_prediction(
        self,
        *,
        classification: ClassificationStageResult,
        extraction: AttributeExtractionStageResult,
        semantic: SemanticConsistencyResult,
    ) -> PredictionResponse:
        classifier_result = classification.classifier_result
        policy = classification.policy
        classifier_diagnostics = classification.diagnostics

        reliability = ReliabilityMeta(
            alpha=self.alpha,
            coverage_target=1.0 - self.alpha,
            set_size=len(policy.category_set),
            confidence=max(classifier_result.probabilities.values()),
            abstained=policy.abstained,
            reason=policy.reason,
            policy_action=policy.action,
            llm_runtime=extraction.runtime,
            llm_model=extraction.model,
            classifier_runtime=str(classifier_diagnostics["runtime"]),
            classifier_reason=classifier_diagnostics["reason"],
            classifier_artifact_path=classifier_diagnostics["artifact_path"],
            classifier_model_type=classifier_diagnostics.get("model_type"),
            classifier_artifact_load_attempted=bool(classifier_diagnostics.get("artifact_load_attempted", False)),
            classifier_artifact_load_status=str(classifier_diagnostics.get("artifact_load_status", "not_attempted")),
            classifier_artifact_rejection_reason=classifier_diagnostics.get("artifact_rejection_reason"),
            classifier_artifact_rebuild_attempted=bool(classifier_diagnostics.get("artifact_rebuild_attempted", False)),
            classifier_artifact_rebuild_status=str(
                classifier_diagnostics.get("artifact_rebuild_status", "not_needed")
            ),
            classifier_artifact_rebuild_reason=classifier_diagnostics.get("artifact_rebuild_reason"),
            semantic_consistency_score=semantic.score,
            semantic_consistency_status=semantic.status,
            semantic_consistency_reason=semantic.reason,
            coverage_threshold=float(classifier_diagnostics["coverage_threshold"]),
        )

        return PredictionResponse(
            category_set=policy.category_set,
            attributes=extraction.attributes,
            reliability=reliability,
        )

    def _classify(self, item: ProductInput) -> ClassifierResult:
        if self.classifier.is_ready:
            return self.classifier.predict(item)

        text = f"{item.title} {item.description}".lower()
        scores = {label: 0.05 for label in self.LABELS}

        for label, words in self.KEYWORDS.items():
            for word in words:
                if word in text:
                    scores[label] += 0.2

        total = sum(scores.values())
        probs = {k: v / total for k, v in scores.items()}
        sorted_labels = sorted(probs.keys(), key=lambda x: probs[x], reverse=True)
        return ClassifierResult(probabilities=probs, sorted_labels=sorted_labels)

    def _conformal_set(self, result: ClassifierResult) -> List[str]:
        target = self.classifier.coverage_threshold if self.classifier.is_ready else 1.0 - self.alpha
        return build_prediction_set(result, target)
