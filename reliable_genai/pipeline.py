import os
from typing import Dict, List

from .classifier import CalibratedTextClassifier
from .llm_wrappers import GitHubModelsClient
from .models import ClassifierResult, PredictionResponse, ProductInput, ReliabilityMeta
from .runtime_profile import resolve_runtime_settings
from .scoring import apply_abstention_policy, build_prediction_set


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
        self.classifier = CalibratedTextClassifier(
            self.LABELS,
            self.alpha,
            model_type=settings.classifier_model_type,
            strict_artifact_metadata=settings.strict_artifact_metadata,
            artifact_mismatch_policy=settings.classifier_artifact_mismatch_policy,
        )

    def predict(self, item: ProductInput) -> PredictionResponse:
        classifier_result = self._classify(item)
        category_set = self._conformal_set(classifier_result)
        classifier_diagnostics = self.classifier.diagnostics()
        policy = apply_abstention_policy(
            category_set=category_set,
            max_set_size=self.max_set_size,
            enable_abstain=self.enable_abstain,
        )

        attributes = self.llm.extract_attributes(item.title, item.description)

        reliability = ReliabilityMeta(
            alpha=self.alpha,
            coverage_target=1.0 - self.alpha,
            set_size=len(policy.category_set),
            confidence=max(classifier_result.probabilities.values()),
            abstained=policy.abstained,
            reason=policy.reason,
            policy_action=policy.action,
            llm_runtime=self.llm.last_runtime,
            llm_model=self.llm.model,
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
            coverage_threshold=float(classifier_diagnostics["coverage_threshold"]),
        )

        return PredictionResponse(
            category_set=policy.category_set,
            attributes=attributes,
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
