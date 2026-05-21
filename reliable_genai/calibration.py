from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable


ProbabilityMap = dict[str, float]


@dataclass(frozen=True)
class CalibrationResult:
    alpha: float
    target_coverage: float
    cumulative_threshold: float
    sample_count: int


def cumulative_mass_for_label(probabilities: ProbabilityMap, true_label: str) -> float | None:
    cumulative = 0.0
    for label in sorted(probabilities, key=lambda key: probabilities[key], reverse=True):
        cumulative += probabilities[label]
        if label == true_label:
            return cumulative
    return None


def calibrate_cumulative_threshold(
    rows: list[dict[str, str]],
    probability_fn: Callable[[list[str]], list[ProbabilityMap]],
    text_fn: Callable[[dict[str, str]], str],
    alpha: float,
) -> CalibrationResult:
    target_coverage = 1.0 - alpha
    probabilities = probability_fn([text_fn(row) for row in rows])
    scores: list[float] = []

    for row, probability_map in zip(rows, probabilities):
        score = cumulative_mass_for_label(probability_map, row["category"])
        if score is not None:
            scores.append(score)

    if not scores:
        return CalibrationResult(
            alpha=alpha,
            target_coverage=target_coverage,
            cumulative_threshold=target_coverage,
            sample_count=0,
        )

    scores.sort()
    rank = min(math.ceil((len(scores) + 1) * target_coverage), len(scores)) - 1
    return CalibrationResult(
        alpha=alpha,
        target_coverage=target_coverage,
        cumulative_threshold=scores[max(rank, 0)],
        sample_count=len(scores),
    )
