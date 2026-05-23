#!/usr/bin/env python3
"""Evaluate the reliability pipeline on labeled processed test data."""

from __future__ import annotations

import json
import os
import sys
import time
import argparse
import copy
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


DETERMINISTIC_TIMESTAMP = "deterministic"


def display_path(path: object, deterministic: bool) -> object:
    if not deterministic or not path:
        return path

    candidate = Path(str(path))
    try:
        return str(candidate.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(candidate)


def run_evaluation(
    use_mock: bool = True,
    alpha: float | None = None,
    max_set_size: int | None = None,
    include_runtime: bool = False,
) -> dict:
    if alpha is not None:
        os.environ["ALPHA"] = str(alpha)
    if max_set_size is not None:
        os.environ["MAX_SET_SIZE"] = str(max_set_size)
    if use_mock:
        os.environ["USE_MOCK_LLM"] = "true"

    print("[INFO] Initializing pipeline...")
    pipeline = ReliabilityPipeline()
    classifier_diagnostics = pipeline.classifier.diagnostics()
    classifier_mode = "tfidf_logreg_calibrated" if pipeline.classifier.is_ready else "keyword_fallback"
    print(f"[INFO] Classifier mode: {classifier_mode}")
    print(f"[INFO] Classifier runtime: {classifier_diagnostics['runtime']}")
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
        runtime_ms = round(elapsed * 1000, 2) if include_runtime else 0.0

        top_label = response.category_set[0] if response.category_set else None
        covered = true_label in response.category_set
        top1_correct = top_label == true_label
        reliability = response.reliability.model_dump()
        reliability["classifier_artifact_path"] = display_path(
            reliability.get("classifier_artifact_path"),
            deterministic=not include_runtime,
        )

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
            "reliability": reliability,
            "runtime_ms": runtime_ms,
            "abstained": response.reliability.abstained,
        }
        results.append(result_entry)

        print(
            "    set="
            f"{response.category_set} true={true_label} covered={covered} "
            f"abstained={response.reliability.abstained}"
            + (f" {elapsed:.3f}s" if include_runtime else "")
        )

    metrics = compute_metrics(
        results=results,
        target_coverage=1.0 - pipeline.alpha,
        calibrated_cumulative_threshold=pipeline.classifier.coverage_threshold,
    ).model_dump()

    return {
        "timestamp": datetime.now().isoformat() if include_runtime else DETERMINISTIC_TIMESTAMP,
        "total_products": len(results),
        "classifier_mode": classifier_mode,
        "classifier_ready": pipeline.classifier.is_ready,
        "classifier_reason": pipeline.classifier.reason,
        "classifier_runtime": classifier_diagnostics["runtime"],
        "classifier_artifact_path": display_path(
            classifier_diagnostics["artifact_path"],
            deterministic=not include_runtime,
        ),
        "coverage_threshold": classifier_diagnostics["coverage_threshold"],
        "classifier_artifact_metadata": classifier_diagnostics.get("artifact_metadata", {}),
        "llm_runtime_mode": "MOCK" if pipeline.llm.use_mock else "LIVE",
        "results": results,
        "metrics": metrics,
        "include_runtime": include_runtime,
    }


def save_results(aggregated: dict, output_path: str = "reports/results.md") -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    metrics = aggregated["metrics"]
    include_runtime = bool(aggregated.get("include_runtime", True))
    report_payload = copy.deepcopy(aggregated)
    if not include_runtime:
        report_payload["metrics"].pop("avg_runtime_ms", None)
        report_payload["metrics"].pop("max_runtime_ms", None)
        for result in report_payload["results"]:
            result.pop("runtime_ms", None)

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("# UAMAS Evaluation Results\n\n")
        handle.write(f"**Generated:** {aggregated['timestamp']}\n\n")
        handle.write(f"**Classifier:** {aggregated['classifier_mode']}\n\n")
        handle.write(f"**Classifier Runtime:** {aggregated['classifier_runtime']}\n\n")
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
        if include_runtime:
            handle.write(f"| Avg Runtime | {metrics['avg_runtime_ms']:.0f}ms |\n")
            handle.write(f"| Max Runtime | {metrics['max_runtime_ms']:.0f}ms |\n")
        handle.write("\n")

        handle.write("## Interpretation\n\n")
        handle.write("- **Empirical Coverage**: fraction of all test rows where the true label is in the returned set.\n")
        handle.write("- **Selective Coverage**: coverage after abstentions are removed from the denominator.\n")
        handle.write("- **Calibrated Cumulative Threshold**: cumulative probability mass needed to include labels after calibration.\n")
        handle.write("- **Abstention Rate**: products where the policy refused to return a category set.\n\n")

        handle.write("## Per-Product Results\n\n")
        if include_runtime:
            handle.write("| # | Product | True Label | Category Set | Covered | Abstained | Runtime (ms) |\n")
            handle.write("|---|---------|------------|--------------|---------|-----------|--------------|\n")
        else:
            handle.write("| # | Product | True Label | Category Set | Covered | Abstained |\n")
            handle.write("|---|---------|------------|--------------|---------|-----------|\n")
        for result in aggregated["results"]:
            covered = "yes" if result["covered"] else "no"
            abstained = "yes" if result["abstained"] else "no"
            category_set = ", ".join(result["category_set"]) if result["category_set"] else "[]"
            row = (
                f"| {result['product_id']} | {result['title'][:40]} | {result['true_label']} | "
                f"{category_set} | {covered} | {abstained}"
            )
            if include_runtime:
                row += f" | {result['runtime_ms']}"
            handle.write(f"{row} |\n")

        handle.write("\n## Full JSON Results\n\n")
        handle.write("```json\n")
        handle.write(json.dumps(report_payload, indent=2))
        handle.write("\n```\n")

    print(f"\n[INFO] Results saved to {output_path}")


if __name__ == "__main__":
    env_file = PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=str(env_file), override=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-runtime", action="store_true", help="Include wall-clock timing in saved results")
    parser.add_argument("--output", default="reports/results.md", help="Markdown report output path")
    args = parser.parse_args()

    try:
        aggregated_results = run_evaluation(use_mock=True, include_runtime=args.include_runtime)
        save_results(aggregated_results, output_path=args.output)

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
