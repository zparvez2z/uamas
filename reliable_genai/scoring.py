from __future__ import annotations

from dataclasses import dataclass

from .models import ClassifierResult


@dataclass(frozen=True)
class PolicyDecision:
    category_set: list[str]
    abstained: bool
    reason: str | None
    action: str


def build_prediction_set(result: ClassifierResult, cumulative_threshold: float) -> list[str]:
    cumulative = 0.0
    selected: list[str] = []

    for label in result.sorted_labels:
        selected.append(label)
        cumulative += result.probabilities[label]
        if cumulative >= cumulative_threshold:
            break

    if not selected and result.sorted_labels:
        selected = [result.sorted_labels[0]]

    return selected


def apply_abstention_policy(
    category_set: list[str],
    max_set_size: int,
    enable_abstain: bool,
) -> PolicyDecision:
    if enable_abstain and (len(category_set) == 0 or len(category_set) > max_set_size):
        return PolicyDecision(
            category_set=[],
            abstained=True,
            reason="Prediction set outside usability constraints",
            action="abstain",
        )

    return PolicyDecision(
        category_set=category_set,
        abstained=False,
        reason=None,
        action="set_output",
    )
