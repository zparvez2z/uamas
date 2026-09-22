#!/usr/bin/env python3
"""Compare deterministic and local-HF attribute extraction on a fixed set."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from reliable_genai.providers.attributes import (
    AttributeExtractionClient,
    HuggingFaceAttributeExtractor,
    MockAttributeExtractor,
)


FIELDS = ("brand", "color", "material", "size")


def _normalize(value: object) -> str:
    return " ".join(str(value or "unknown").strip().lower().split())


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentile)
    return round(ordered[index], 3)


def evaluate(name: str, client: AttributeExtractionClient, rows: list[dict]) -> dict:
    field_correct = 0
    field_total = 0
    unknown_correct = 0
    unknown_total = 0
    hallucinations = 0
    schema_success = 0
    latencies: list[float] = []
    details = []
    for row in rows:
        predicted = client.extract_attributes(row["title"], row["description"])
        outcome = client.last_outcome
        assert outcome is not None
        actual = predicted.model_dump()
        expected = row["attributes"]
        for field in FIELDS:
            expected_value = _normalize(expected[field])
            actual_value = _normalize(actual[field])
            field_total += 1
            field_correct += int(expected_value == actual_value)
            if expected_value == "unknown":
                unknown_total += 1
                unknown_correct += int(actual_value == "unknown")
                hallucinations += int(actual_value != "unknown")
        schema_success += int(outcome.runtime in {"MOCK", "LOCAL_HF"})
        if outcome.latency_ms is not None:
            latencies.append(outcome.latency_ms)
        details.append(
            {
                "title": row["title"],
                "expected": expected,
                "predicted": actual,
                "runtime": outcome.runtime,
                "error": outcome.error,
                "latency_ms": outcome.latency_ms,
            }
        )
    count = len(rows)
    return {
        "name": name,
        "count": count,
        "provider": client.provider,
        "model": client.model,
        "revision": client.revision,
        "schema_success_rate": round(schema_success / count, 3) if count else 0.0,
        "field_exact_accuracy": round(field_correct / field_total, 3) if field_total else 0.0,
        "unknown_correctness_rate": round(unknown_correct / unknown_total, 3) if unknown_total else 0.0,
        "hallucination_rate": round(hallucinations / unknown_total, 3) if unknown_total else 0.0,
        "median_latency_ms": round(statistics.median(latencies), 3) if latencies else 0.0,
        "p95_latency_ms": _percentile(latencies, 0.95),
        "runtime_counts": {
            runtime: sum(1 for item in details if item["runtime"] == runtime)
            for runtime in sorted({str(item["runtime"]) for item in details})
        },
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/benchmarks/attribute_extraction_v1.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/attribute_extraction_benchmark.json"),
    )
    args = parser.parse_args()
    rows = json.loads(args.dataset.read_text(encoding="utf-8"))
    if len(rows) != 30:
        raise ValueError(f"benchmark contract requires 30 rows, got {len(rows)}")

    baseline = AttributeExtractionClient(extractor=MockAttributeExtractor())
    local_hf = AttributeExtractionClient(extractor=HuggingFaceAttributeExtractor())
    warmup = local_hf.extract_attributes(
        "Nike black running shoe size 42",
        "Breathable mesh training footwear.",
    )
    if local_hf.last_runtime != "LOCAL_HF":
        raise RuntimeError(f"local HF warmup failed: {local_hf.last_error}; {warmup}")

    try:
        import torch

        torch.cuda.reset_peak_memory_stats()
    except Exception:
        torch = None

    payload = {
        "schema_version": "1.0",
        "dataset": str(args.dataset),
        "dataset_count": len(rows),
        "deterministic_baseline": evaluate("deterministic_baseline", baseline, rows),
        "qwen_local_hf": evaluate("qwen_local_hf", local_hf, rows),
    }
    payload["gpu_peak_memory_mb"] = (
        round(torch.cuda.max_memory_allocated() / (1024 * 1024), 2)
        if torch is not None and torch.cuda.is_available()
        else None
    )
    qwen = payload["qwen_local_hf"]
    assert isinstance(qwen, dict)
    payload["acceptance"] = {
        "no_fallback_or_failed_calls": qwen["runtime_counts"] == {"LOCAL_HF": 30},
        "schema_success_complete": qwen["schema_success_rate"] == 1.0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in payload.items() if key != "deterministic_baseline" and key != "qwen_local_hf"}, indent=2))
    print(json.dumps({"baseline": payload["deterministic_baseline"] | {"details": "omitted"}, "qwen": qwen | {"details": "omitted"}}, indent=2))
    return 0 if all(payload["acceptance"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
