#!/usr/bin/env python3
"""Evaluate the reliability pipeline on labeled processed test data."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from reliable_genai import ProductInput, ReliabilityPipeline
from reliable_genai.evaluation import compute_metrics


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEST_PATH = PROJECT_ROOT / "data" / "processed" / "test.json"


def load_labeled_dataset(path: Path = DEFAULT_TEST_PATH) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain a JSON list")
    return rows


def run_evaluation(use_mock: bool = True, alpha: float | None = None, max_set_size: int | None = None) -> dict:
    if alpha is not None:
        os.environ["ALPHA"] = str(alpha)
    if max_set_size is not None:
        os.environ["MAX_SET_SIZE"] = str(max_set_size)
    if use_mock:
        os.environ["USE_MOCK_LLM"] = "true"

    print("[INFO] Initializing pipeline...")
    pipeline = ReliabilityPipeline()
    classifier_mode = "tfidf_logreg_calibrated" if pipeline.classifier.is_ready else "keyword_fallback"
    print(f"[INFO] Classifier mode: {classifier_mode}")
    if pipeline.classifier.reason:
        print(f"[INFO] Classifier fallback reason: {pipeline.classifier.reason}")
    print(f"[INFO] LLM mode: {'MOCK' if pipeline.llm.use_mock else 'LIVE'}")

    rows = load_labeled_dataset()
    results = []

    print(f"\n[INFO] Running labeled evaluation on {len(rows)} products...\n")
    for idx, row in enumerate(rows, 1):
        product = ProductInput(
            title=row["title"],
            description=row.get("description", ""),
        )
        true_label = row["category"]
        print(f"[{idx}/{len(rows)}] Predicting: {product.title[:56]}")

        start = time.time()
        response = pipeline.predict(product)
        elapsed = time.time() - start

        top_label = response.category_set[0] if response.category_set else None
        covered = true_label in response.category_set
        top1_correct = top_label == true_label

        result_entry = {
            "product_id": idx,
            "title": product.title,
            "true_label": true_label,
            "category_set": response.category_set,
            "top_label": top_label,
            "covered": covered,
            "top1_correct": top1_correct,
            "set_size": len(response.category_set),
            "attributes": response.attributes.model_dump(),
            "reliability": response.reliability.model_dump(),
            "runtime_ms": round(elapsed * 1000, 2),
            "abstained": response.reliability.abstained,
        }
        results.append(result_entry)

        print(
            "    set="
            f"{response.category_set} true={true_label} covered={covered} "
            f"abstained={response.reliability.abstained} {elapsed:.3f}s"
        )

    metrics = compute_metrics(
        results=results,
        target_coverage=1.0 - pipeline.alpha,
        calibrated_cumulative_threshold=pipeline.classifier.coverage_threshold,
    ).model_dump()

    return {
        "timestamp": datetime.now().isoformat(),
        "total_products": len(results),
        "classifier_mode": classifier_mode,
        "classifier_ready": pipeline.classifier.is_ready,
        "classifier_reason": pipeline.classifier.reason,
        "llm_runtime_mode": "MOCK" if pipeline.llm.use_mock else "LIVE",
        "results": results,
        "metrics": metrics,
    }


def save_results(aggregated: dict, output_path: str = "reports/results.md") -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    metrics = aggregated["metrics"]

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("# UAMAS Evaluation Results\n\n")
        handle.write(f"**Generated:** {aggregated['timestamp']}\n\n")
        handle.write(f"**Classifier:** {aggregated['classifier_mode']}\n\n")
        handle.write(f"**LLM Runtime:** {aggregated['llm_runtime_mode']}\n\n")

        handle.write("## Summary Metrics\n\n")
        handle.write("| Metric | Value |\n")
        handle.write("|--------|-------|\n")
        handle.write(f"| Total Products Tested | {aggregated['total_products']} |\n")
        handle.write(f"| Target Coverage | {metrics['target_coverage']:.3f} |\n")
        handle.write(f"| Calibrated Cumulative Threshold | {metrics['calibrated_cumulative_threshold']:.4f} |\n")
        handle.write(f"| Empirical Coverage | {metrics['empirical_coverage']:.3f} |\n")
        handle.write(f"| Selective Coverage | {metrics['selective_coverage']} |\n")
        handle.write(f"| Top-1 Accuracy | {metrics['top1_accuracy']:.3f} |\n")
        handle.write(f"| Avg Confidence Set Size | {metrics['avg_set_size']} |\n")
        handle.write(f"| Avg Non-Abstained Set Size | {metrics['avg_non_abstained_set_size']} |\n")
        handle.write(f"| Abstention Rate | {metrics['abstention_rate'] * 100:.1f}% ({metrics['abstention_count']} products) |\n")
        handle.write(f"| Avg Runtime | {metrics['avg_runtime_ms']:.0f}ms |\n")
        handle.write(f"| Max Runtime | {metrics['max_runtime_ms']:.0f}ms |\n\n")

        handle.write("## Interpretation\n\n")
        handle.write("- **Empirical Coverage**: fraction of all test rows where the true label is in the returned set.\n")
        handle.write("- **Selective Coverage**: coverage after abstentions are removed from the denominator.\n")
        handle.write("- **Calibrated Cumulative Threshold**: cumulative probability mass needed to include labels after calibration.\n")
        handle.write("- **Abstention Rate**: products where the policy refused to return a category set.\n\n")

        handle.write("## Per-Product Results\n\n")
        handle.write("| # | Product | True Label | Category Set | Covered | Abstained | Runtime (ms) |\n")
        handle.write("|---|---------|------------|--------------|---------|-----------|--------------|\n")
        for result in aggregated["results"]:
            covered = "yes" if result["covered"] else "no"
            abstained = "yes" if result["abstained"] else "no"
            category_set = ", ".join(result["category_set"]) if result["category_set"] else "[]"
            handle.write(
                f"| {result['product_id']} | {result['title'][:40]} | {result['true_label']} | "
                f"{category_set} | {covered} | {abstained} | {result['runtime_ms']} |\n"
            )

        handle.write("\n## Full JSON Results\n\n")
        handle.write("```json\n")
        handle.write(json.dumps(aggregated, indent=2))
        handle.write("\n```\n")

    print(f"\n[INFO] Results saved to {output_path}")


if __name__ == "__main__":
    env_file = PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=str(env_file), override=True)

    try:
        aggregated_results = run_evaluation(use_mock=True)
        save_results(aggregated_results)

        summary = aggregated_results["metrics"]
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        print(f"Target Coverage: {summary['target_coverage']:.3f}")
        print(f"Empirical Coverage: {summary['empirical_coverage']:.3f}")
        print(f"Selective Coverage: {summary['selective_coverage']}")
        print(f"Top-1 Accuracy: {summary['top1_accuracy']:.3f}")
        print(f"Avg Set Size: {summary['avg_set_size']}")
        print(f"Abstention Rate: {summary['abstention_rate'] * 100:.1f}%")
        print("=" * 60)
    except Exception as exc:
        print(f"\n[ERROR] Evaluation failed: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
