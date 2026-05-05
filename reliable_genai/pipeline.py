import os
from typing import Dict, List

from .llm_wrappers import GitHubModelsClient
from .models import ClassifierResult, PredictionResponse, ProductInput, ReliabilityMeta


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

    def __init__(self) -> None:
        self.alpha = float(os.getenv("ALPHA", "0.1"))
        self.max_set_size = int(os.getenv("MAX_SET_SIZE", "3"))
        self.enable_abstain = os.getenv("ENABLE_ABSTAIN", "true").lower() == "true"
        self.llm = GitHubModelsClient()

    def predict(self, item: ProductInput) -> PredictionResponse:
        classifier_result = self._classify(item)
        category_set = self._conformal_set(classifier_result)

        abstained = False
        reason = None
        action = "set_output"

        if self.enable_abstain and (len(category_set) == 0 or len(category_set) > self.max_set_size):
            abstained = True
            reason = "Prediction set outside usability constraints"
            action = "abstain"
            category_set = []

        attributes = self.llm.extract_attributes(item.title, item.description)

        reliability = ReliabilityMeta(
            alpha=self.alpha,
            coverage_target=1.0 - self.alpha,
            set_size=len(category_set),
            confidence=max(classifier_result.probabilities.values()),
            abstained=abstained,
            reason=reason,
            policy_action=action,
            llm_runtime=self.llm.last_runtime,
            llm_model=self.llm.model,
        )

        return PredictionResponse(
            category_set=category_set,
            attributes=attributes,
            reliability=reliability,
        )

    def _classify(self, item: ProductInput) -> ClassifierResult:
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
        # Demo approximation: include labels while cumulative mass <= target coverage.
        target = 1.0 - self.alpha
        cumulative = 0.0
        selected: List[str] = []

        for label in result.sorted_labels:
            selected.append(label)
            cumulative += result.probabilities[label]
            if cumulative >= target:
                break

        # Enforce a non-empty set in non-abstain mode.
        if not selected and result.sorted_labels:
            selected = [result.sorted_labels[0]]

        return selected
