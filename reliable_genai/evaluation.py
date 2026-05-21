from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvaluationMetrics:
    target_coverage: float
    calibrated_cumulative_threshold: float
    empirical_coverage: float
    selective_coverage: float | None
    top1_accuracy: float
    avg_set_size: float
    avg_non_abstained_set_size: float | None
    max_set_size: int
    min_set_size: int
    abstention_count: int
    abstention_rate: float
    avg_runtime_ms: float
    max_runtime_ms: float

    def model_dump(self) -> dict[str, Any]:
        return {
            "target_coverage": self.target_coverage,
            "calibrated_cumulative_threshold": self.calibrated_cumulative_threshold,
            "empirical_coverage": self.empirical_coverage,
            "selective_coverage": self.selective_coverage,
            "top1_accuracy": self.top1_accuracy,
            "avg_set_size": self.avg_set_size,
            "avg_non_abstained_set_size": self.avg_non_abstained_set_size,
            "max_set_size": self.max_set_size,
            "min_set_size": self.min_set_size,
            "abstention_count": self.abstention_count,
            "abstention_rate": self.abstention_rate,
            "avg_runtime_ms": self.avg_runtime_ms,
            "max_runtime_ms": self.max_runtime_ms,
        }


def compute_metrics(
    results: list[dict[str, Any]],
    target_coverage: float,
    calibrated_cumulative_threshold: float,
) -> EvaluationMetrics:
    non_abstained = [result for result in results if not result["abstained"]]
    covered = sum(1 for result in results if result["covered"])
    top1_correct = sum(1 for result in results if result["top1_correct"])
    non_abstained_covered = sum(1 for result in non_abstained if result["covered"])

    return EvaluationMetrics(
        target_coverage=round(target_coverage, 3),
        calibrated_cumulative_threshold=round(calibrated_cumulative_threshold, 4),
        empirical_coverage=round(covered / len(results), 3),
        selective_coverage=round(non_abstained_covered / len(non_abstained), 3) if non_abstained else None,
        top1_accuracy=round(top1_correct / len(results), 3),
        avg_set_size=round(sum(result["set_size"] for result in results) / len(results), 2),
        avg_non_abstained_set_size=(
            round(sum(result["set_size"] for result in non_abstained) / len(non_abstained), 2)
            if non_abstained
            else None
        ),
        max_set_size=max(result["set_size"] for result in results),
        min_set_size=min(result["set_size"] for result in results),
        abstention_count=sum(1 for result in results if result["abstained"]),
        abstention_rate=round(sum(1 for result in results if result["abstained"]) / len(results), 3),
        avg_runtime_ms=round(sum(result["runtime_ms"] for result in results) / len(results), 2),
        max_runtime_ms=max(result["runtime_ms"] for result in results),
    )
