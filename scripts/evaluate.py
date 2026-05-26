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
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from reliable_genai import ProductInput, ReliabilityPipeline, ReviewGraphRunner
from reliable_genai.evaluation import compute_metrics


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEST_PATH = PROJECT_ROOT / "data" / "processed" / "test.json"
DEFAULT_ACCEPTANCE_BASELINE_SET_SIZE_TRIGGER = 3
DEFAULT_ACCEPTANCE_TUNED_SET_SIZE_TRIGGER = 4
DEFAULT_ACCEPTANCE_VERY_LOW_CONFIDENCE_FLOOR = 0.35
DEFAULT_ACCEPTANCE_TRIGGER_RATE_TARGET = 0.25
DEFAULT_ACCEPTANCE_COVERAGE_DELTA_FLOOR = -0.01


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


def resolve_use_mock(args: argparse.Namespace) -> bool:
    """Resolve mutually exclusive CLI flags into a single mode."""
    if args.live:
        return False
    if args.mock:
        return True
    return True


@contextmanager
def temporary_env(overrides: dict[str, str | None]):
    previous: dict[str, str | None] = {key: os.environ.get(key) for key in overrides}
    try:
        for key, value in overrides.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_review_trigger_acceptance_check(use_mock: bool = True) -> dict[str, object]:
    baseline_overrides = {
        "ENABLE_LANGGRAPH_REVIEW": "true",
        "REVIEW_GATE_STRATEGY": "legacy",
        "REVIEW_SET_SIZE_TRIGGER": str(DEFAULT_ACCEPTANCE_BASELINE_SET_SIZE_TRIGGER),
    }
    tuned_overrides = {
        "ENABLE_LANGGRAPH_REVIEW": "true",
        "REVIEW_GATE_STRATEGY": "latency_v1",
        "REVIEW_SET_SIZE_TRIGGER": str(DEFAULT_ACCEPTANCE_TUNED_SET_SIZE_TRIGGER),
        "REVIEW_VERY_LOW_CONFIDENCE_FLOOR": str(DEFAULT_ACCEPTANCE_VERY_LOW_CONFIDENCE_FLOOR),
    }

    with temporary_env(baseline_overrides):
        baseline = run_evaluation(use_mock=use_mock, include_runtime=False)
    with temporary_env(tuned_overrides):
        tuned = run_evaluation(use_mock=use_mock, include_runtime=False)

    coverage_delta = round(tuned["metrics"]["empirical_coverage"] - baseline["metrics"]["empirical_coverage"], 3)
    return {
        "date": datetime.now().date().isoformat(),
        "runtime_mode": f"USE_MOCK_LLM={'true' if use_mock else 'false'}, ENABLE_LANGGRAPH_REVIEW=true",
        "baseline_config": {
            "review_gate_strategy": "legacy",
            "review_set_size_trigger": DEFAULT_ACCEPTANCE_BASELINE_SET_SIZE_TRIGGER,
        },
        "tuned_config": {
            "review_gate_strategy": "latency_v1",
            "review_set_size_trigger": DEFAULT_ACCEPTANCE_TUNED_SET_SIZE_TRIGGER,
            "review_very_low_confidence_floor": DEFAULT_ACCEPTANCE_VERY_LOW_CONFIDENCE_FLOOR,
        },
        "baseline_trigger_rate": baseline["review_graph_trigger_rate"],
        "tuned_trigger_rate": tuned["review_graph_trigger_rate"],
        "trigger_rate_target": DEFAULT_ACCEPTANCE_TRIGGER_RATE_TARGET,
        "baseline_second_pass_rate": baseline["review_graph_second_pass_rate"],
        "tuned_second_pass_rate": tuned["review_graph_second_pass_rate"],
        "baseline_empirical_coverage": baseline["metrics"]["empirical_coverage"],
        "tuned_empirical_coverage": tuned["metrics"]["empirical_coverage"],
        "coverage_delta": coverage_delta,
        "coverage_delta_floor": DEFAULT_ACCEPTANCE_COVERAGE_DELTA_FLOOR,
    }


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
    os.environ["USE_MOCK_LLM"] = "true" if use_mock else "false"

    print("[INFO] Initializing pipeline...")
    pipeline = ReliabilityPipeline()
    review_graph = ReviewGraphRunner(pipeline)
    classifier_diagnostics = pipeline.classifier.diagnostics()
    review_diagnostics = review_graph.diagnostics()
    classifier_model_type = str(classifier_diagnostics.get("model_type") or "unknown")
    classifier_mode = f"{classifier_model_type}_logreg_calibrated" if pipeline.classifier.is_ready else "keyword_fallback"
    print(f"[INFO] Classifier mode: {classifier_mode}")
    print(f"[INFO] Classifier runtime: {classifier_diagnostics['runtime']}")
    if pipeline.classifier.reason:
        print(f"[INFO] Classifier fallback reason: {pipeline.classifier.reason}")
    print(f"[INFO] LLM mode: {'MOCK' if pipeline.llm.use_mock else 'LIVE'}")
    print(
        "[INFO] Review graph: "
        f"enabled={review_diagnostics['enabled']} "
        f"available={review_diagnostics['available']} "
        f"backend={review_diagnostics['backend']} "
        f"strategy={review_diagnostics['gate_strategy']}"
    )

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
        response = review_graph.predict(product)
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

    runtime_breakdown = {
        "live_count": 0,
        "mock_count": 0,
        "fallback_mock_count": 0,
    }
    expected_live_mode = not pipeline.llm.use_mock
    for result in results:
        runtime = result["reliability"].get("llm_runtime")
        if runtime == "LIVE":
            runtime_breakdown["live_count"] += 1
        elif runtime == "FALLBACK_MOCK":
            runtime_breakdown["fallback_mock_count"] += 1
        elif runtime == "MOCK":
            if expected_live_mode:
                runtime_breakdown["fallback_mock_count"] += 1
            else:
                runtime_breakdown["mock_count"] += 1
        else:
            runtime_breakdown["mock_count"] += 1
    runtime_breakdown["fallback_rate"] = (
        round(runtime_breakdown["fallback_mock_count"] / len(results), 3) if results else 0.0
    )
    review_trigger_count = sum(1 for result in results if result["reliability"].get("review_trigger_reason"))
    review_second_pass_count = sum(
        1
        for result in results
        if result["reliability"].get("review_outcome") in {"second_pass_selected", "first_pass_retained"}
    )
    known_trigger_reasons = (
        "abstained",
        "very_low_confidence",
        "low_confidence_large_set",
        "low_confidence",
        "large_set",
        "low_semantic_consistency",
    )
    review_trigger_reason_counts = {
        reason: sum(1 for result in results if result["reliability"].get("review_trigger_reason") == reason)
        for reason in known_trigger_reasons
    }
    review_trigger_reason_rates = {
        reason: round(count / len(results), 3) if results else 0.0
        for reason, count in review_trigger_reason_counts.items()
    }
    review_diagnostics = review_graph.diagnostics()
    artifact_metadata = classifier_diagnostics.get("artifact_metadata", {}) or {}
    semantic_scored_count = sum(
        1 for result in results if result["reliability"].get("semantic_consistency_score") is not None
    )
    semantic_degraded_count = sum(
        1
        for result in results
        if result["reliability"].get("semantic_consistency_status") == "degraded"
    )
    semantic_threshold = float(review_diagnostics.get("semantic_threshold", 0.4))
    semantic_low_count = sum(
        1
        for result in results
        if result["reliability"].get("semantic_consistency_status") == "ok"
        and result["reliability"].get("semantic_consistency_score") is not None
        and float(result["reliability"]["semantic_consistency_score"]) < semantic_threshold
    )

    return {
        "timestamp": datetime.now().isoformat() if include_runtime else DETERMINISTIC_TIMESTAMP,
        "total_products": len(results),
        "classifier_mode": classifier_mode,
        "classifier_ready": pipeline.classifier.is_ready,
        "classifier_reason": pipeline.classifier.reason,
        "classifier_runtime": classifier_diagnostics["runtime"],
        "classifier_model_type": classifier_model_type,
        "classifier_artifact_load_attempted": classifier_diagnostics.get("artifact_load_attempted", False),
        "classifier_artifact_load_status": classifier_diagnostics.get("artifact_load_status", "not_attempted"),
        "classifier_artifact_rejection_reason": classifier_diagnostics.get("artifact_rejection_reason"),
        "classifier_artifact_rebuild_attempted": classifier_diagnostics.get("artifact_rebuild_attempted", False),
        "classifier_artifact_rebuild_status": classifier_diagnostics.get("artifact_rebuild_status", "not_needed"),
        "classifier_artifact_rebuild_reason": classifier_diagnostics.get("artifact_rebuild_reason"),
        "classifier_artifact_path": display_path(
            classifier_diagnostics["artifact_path"],
            deterministic=not include_runtime,
        ),
        "coverage_threshold": classifier_diagnostics["coverage_threshold"],
        "classifier_artifact_metadata": artifact_metadata,
        "classifier_artifact_format_version": artifact_metadata.get("artifact_format_version"),
        "classifier_dataset_fingerprint": artifact_metadata.get("dataset_fingerprint_sha256"),
        "review_graph_backend": review_diagnostics["backend"],
        "review_graph_available": review_diagnostics["available"],
        "review_graph_gate_strategy": review_diagnostics["gate_strategy"],
        "review_graph_very_low_confidence_floor": review_diagnostics["very_low_confidence_floor"],
        "review_graph_semantic_threshold": review_diagnostics.get("semantic_threshold"),
        "review_graph_trigger_rate": round(review_trigger_count / len(results), 3) if results else 0.0,
        "review_graph_second_pass_rate": round(review_second_pass_count / len(results), 3) if results else 0.0,
        "review_graph_semantic_trigger_rate": review_diagnostics.get("review_graph_semantic_trigger_rate", 0.0),
        "review_graph_trigger_reason_counts": review_trigger_reason_counts,
        "review_graph_trigger_reason_rates": review_trigger_reason_rates,
        "review_graph_cache_hit_rate": review_diagnostics["review_graph_cache_hit_rate"],
        "review_graph_cached_step_count": review_diagnostics["review_graph_cached_step_count"],
        "semantic_score_availability_rate": round(semantic_scored_count / len(results), 3) if results else 0.0,
        "semantic_degraded_rate": round(semantic_degraded_count / len(results), 3) if results else 0.0,
        "semantic_low_consistency_rate": round(semantic_low_count / len(results), 3) if results else 0.0,
        "semantic_low_consistency_count": semantic_low_count,
        "semantic_degraded_count": semantic_degraded_count,
        "llm_runtime_mode": "MOCK" if pipeline.llm.use_mock else "LIVE",
        "results": results,
        "metrics": metrics,
        "runtime_breakdown": runtime_breakdown,
        "include_runtime": include_runtime,
    }


def save_results(
    aggregated: dict,
    output_path: str = "reports/results.md",
    review_acceptance_check: dict[str, object] | None = None,
) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    json_output_path = str(Path(output_path).with_suffix(".json"))
    metrics = aggregated["metrics"]
    include_runtime = bool(aggregated.get("include_runtime", True))
    report_payload = copy.deepcopy(aggregated)
    if not include_runtime:
        report_payload["metrics"].pop("avg_runtime_ms", None)
        report_payload["metrics"].pop("max_runtime_ms", None)
        for result in report_payload["results"]:
            result.pop("runtime_ms", None)
    if review_acceptance_check:
        report_payload["review_trigger_acceptance_check"] = review_acceptance_check

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("# UAMAS Evaluation Results\n\n")
        handle.write(f"**Generated:** {aggregated['timestamp']}\n\n")
        handle.write(f"**Classifier:** {aggregated['classifier_mode']}\n\n")
        handle.write(f"**Classifier Runtime:** {aggregated['classifier_runtime']}\n\n")
        handle.write(f"**Artifact Load Status:** {aggregated.get('classifier_artifact_load_status')}\n\n")
        if aggregated.get("classifier_artifact_rejection_reason"):
            handle.write(
                f"**Artifact Rejection Reason:** {aggregated.get('classifier_artifact_rejection_reason')}\n\n"
            )
        handle.write(f"**Artifact Rebuild Status:** {aggregated.get('classifier_artifact_rebuild_status')}\n\n")
        if aggregated.get("classifier_artifact_rebuild_reason"):
            handle.write(
                f"**Artifact Rebuild Reason:** {aggregated.get('classifier_artifact_rebuild_reason')}\n\n"
            )
        handle.write(f"**LLM Runtime:** {aggregated['llm_runtime_mode']}\n\n")
        if review_acceptance_check:
            baseline_config = review_acceptance_check["baseline_config"]
            tuned_config = review_acceptance_check["tuned_config"]
            handle.write(f"## Review Trigger Reduction Acceptance Check ({review_acceptance_check['date']})\n\n")
            handle.write(f"- Runtime mode: `{review_acceptance_check['runtime_mode']}`\n")
            handle.write(
                "- Baseline config: "
                f"`REVIEW_GATE_STRATEGY={baseline_config['review_gate_strategy']}`, "
                f"`REVIEW_SET_SIZE_TRIGGER={baseline_config['review_set_size_trigger']}`\n"
            )
            handle.write(
                "- Tuned config: "
                f"`REVIEW_GATE_STRATEGY={tuned_config['review_gate_strategy']}`, "
                f"`REVIEW_SET_SIZE_TRIGGER={tuned_config['review_set_size_trigger']}`, "
                f"`REVIEW_VERY_LOW_CONFIDENCE_FLOOR={tuned_config['review_very_low_confidence_floor']}`\n"
            )
            handle.write(f"- Baseline trigger rate: **{review_acceptance_check['baseline_trigger_rate']:.3f}**\n")
            handle.write(
                "- Tuned trigger rate: "
                f"**{review_acceptance_check['tuned_trigger_rate']:.3f}** "
                f"(target: `<= {review_acceptance_check['trigger_rate_target']:.3f}`)\n"
            )
            handle.write(
                f"- Baseline second-pass rate: **{review_acceptance_check['baseline_second_pass_rate']:.3f}**\n"
            )
            handle.write(
                "- Tuned second-pass rate: "
                f"**{review_acceptance_check['tuned_second_pass_rate']:.3f}** "
                "(aligned with trigger rate)\n"
            )
            handle.write(
                "- Empirical coverage delta (`latency_v1 - legacy`): "
                f"**{review_acceptance_check['coverage_delta']:.3f}** "
                f"(guardrail: no worse than `{review_acceptance_check['coverage_delta_floor']:.3f}`)\n\n"
            )
        handle.write("## Review Graph Tuning\n\n")
        handle.write(f"- Backend: {aggregated.get('review_graph_backend')}\n")
        handle.write(f"- Available: {aggregated.get('review_graph_available')}\n")
        handle.write(f"- Gate Strategy: {aggregated.get('review_graph_gate_strategy')}\n")
        handle.write(
            f"- Very Low Confidence Floor: {aggregated.get('review_graph_very_low_confidence_floor')}\n"
        )
        handle.write(f"- Semantic Threshold: {aggregated.get('review_graph_semantic_threshold')}\n")
        handle.write(f"- Trigger Rate: {aggregated.get('review_graph_trigger_rate', 0.0):.3f}\n")
        handle.write(f"- Second-Pass Rate: {aggregated.get('review_graph_second_pass_rate', 0.0):.3f}\n")
        handle.write(f"- Semantic Trigger Rate: {aggregated.get('review_graph_semantic_trigger_rate', 0.0):.3f}\n")
        handle.write(f"- Cache Hit Rate: {aggregated.get('review_graph_cache_hit_rate', 0.0):.3f}\n")
        trigger_reason_counts = aggregated.get("review_graph_trigger_reason_counts", {})
        handle.write("- Trigger Reasons:\n")
        for reason in (
            "abstained",
            "very_low_confidence",
            "low_confidence_large_set",
            "low_confidence",
            "large_set",
            "low_semantic_consistency",
        ):
            handle.write(f"  - {reason}: {trigger_reason_counts.get(reason, 0)}\n")
        handle.write("\n")

        handle.write("## Semantic Consistency\n\n")
        handle.write(f"- Score availability rate: {aggregated.get('semantic_score_availability_rate', 0.0):.3f}\n")
        handle.write(f"- Degraded rate: {aggregated.get('semantic_degraded_rate', 0.0):.3f}\n")
        handle.write(
            f"- Low-consistency rate (< threshold): {aggregated.get('semantic_low_consistency_rate', 0.0):.3f}\n"
        )
        handle.write(f"- Low-consistency count: {aggregated.get('semantic_low_consistency_count', 0)}\n")
        handle.write(f"- Degraded count: {aggregated.get('semantic_degraded_count', 0)}\n\n")

        runtime_breakdown = aggregated.get("runtime_breakdown") or {}
        should_render_runtime_breakdown = (
            aggregated.get("llm_runtime_mode") == "LIVE"
            or runtime_breakdown.get("fallback_mock_count", 0) > 0
        )
        if should_render_runtime_breakdown:
            handle.write("## LLM Runtime Breakdown\n\n")
            handle.write(f"- LIVE calls: {runtime_breakdown.get('live_count', 0)}\n")
            handle.write(f"- MOCK calls: {runtime_breakdown.get('mock_count', 0)}\n")
            handle.write(f"- FALLBACK_MOCK calls: {runtime_breakdown.get('fallback_mock_count', 0)}\n")
            handle.write(f"- Fallback rate: {runtime_breakdown.get('fallback_rate', 0.0):.3f}\n\n")

        metadata = aggregated.get("classifier_artifact_metadata") or {}
        if metadata:
            handle.write("## Artifact Provenance\n\n")
            handle.write(f"- Artifact Format Version: {metadata.get('artifact_format_version')}\n")
            handle.write(f"- Classifier Family: {metadata.get('classifier_family')}\n")
            handle.write(f"- Model Type: {metadata.get('model_type')}\n")
            handle.write(f"- Created At (UTC): {metadata.get('created_at_utc')}\n")
            handle.write(f"- Python Version: {metadata.get('python_version')}\n")
            handle.write(f"- scikit-learn Version: {metadata.get('sklearn_version')}\n")
            handle.write(f"- Train Rows: {metadata.get('train_row_count')}\n")
            handle.write(f"- Calibration Rows: {metadata.get('calibration_row_count')}\n")
            handle.write(f"- Train SHA-256: {metadata.get('train_data_sha256')}\n")
            handle.write(f"- Calibration SHA-256: {metadata.get('calibration_data_sha256')}\n\n")
            handle.write(f"- Dataset Fingerprint SHA-256: {metadata.get('dataset_fingerprint_sha256')}\n\n")

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

    with open(json_output_path, "w", encoding="utf-8") as handle:
        json.dump(report_payload, handle, indent=2)

    print(f"\n[INFO] Results saved to {output_path}")
    print(f"[INFO] Results JSON saved to {json_output_path}")


if __name__ == "__main__":
    env_file = PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=str(env_file), override=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-runtime", action="store_true", help="Include wall-clock timing in saved results")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--live", action="store_true", help="Run evaluation with USE_MOCK_LLM=false")
    mode_group.add_argument("--mock", action="store_true", help="Run evaluation with USE_MOCK_LLM=true (default)")
    parser.add_argument(
        "--with-review-acceptance-check",
        action="store_true",
        help="Run legacy vs latency_v1 benchmark and include acceptance section in report",
    )
    parser.add_argument("--output", default="reports/results.md", help="Markdown report output path")
    args = parser.parse_args()

    try:
        use_mock = resolve_use_mock(args)
        aggregated_results = run_evaluation(use_mock=use_mock, include_runtime=args.include_runtime)
        review_acceptance_check = (
            run_review_trigger_acceptance_check(use_mock=use_mock)
            if args.with_review_acceptance_check
            else None
        )
        save_results(
            aggregated_results,
            output_path=args.output,
            review_acceptance_check=review_acceptance_check,
        )

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
