#!/usr/bin/env python3
"""Run a strict live-mode smoke verification against app pipeline objects."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import build_diagnostics, review_graph
from reliable_genai.models import ProductInput


def main() -> None:
    initial = build_diagnostics()
    print(
        "INITIAL:",
        json.dumps(
            {
                "runtime_mode": initial.get("runtime_mode"),
                "last_runtime": initial.get("last_runtime"),
                "llm_last_error": initial.get("llm_last_error"),
                "model": initial.get("model"),
                "endpoint": initial.get("endpoint"),
                "token_present": initial.get("token_present"),
            },
            sort_keys=True,
        ),
    )

    failures: list[str] = []
    if initial.get("runtime_mode") != "LIVE":
        failures.append(f"runtime_mode must be LIVE, got {initial.get('runtime_mode')}")
    if not initial.get("token_present"):
        failures.append("token_present must be true in live smoke mode")

    samples = [
        ProductInput(
            title="Nike running shoes black size 42",
            description="Breathable mesh upper and cushioned sole",
        ),
        ProductInput(
            title="Sony mini Wireless Headphones",
            description="Bluetooth over-ear headphones black",
        ),
        ProductInput(
            title="Spa Gift Set",
            description="Body lotion, scented candle, decorative storage box",
        ),
    ]

    for index, item in enumerate(samples, 1):
        prediction = review_graph.predict(item)
        diagnostics = build_diagnostics()
        row = {
            "llm_runtime": prediction.reliability.llm_runtime,
            "diag_last_runtime": diagnostics.get("last_runtime"),
            "diag_llm_last_error": diagnostics.get("llm_last_error"),
            "category_set": prediction.category_set,
        }
        print(f"PREDICT_{index}:", json.dumps(row, sort_keys=True))

        if prediction.reliability.llm_runtime != "LIVE":
            failures.append(
                f"sample {index}: expected prediction llm_runtime LIVE, got {prediction.reliability.llm_runtime}"
            )
        if diagnostics.get("last_runtime") != "LIVE":
            failures.append(
                f"sample {index}: expected diagnostics last_runtime LIVE, got {diagnostics.get('last_runtime')}"
            )
        if diagnostics.get("llm_last_error") is not None:
            failures.append(
                f"sample {index}: expected diagnostics llm_last_error None, got {diagnostics.get('llm_last_error')}"
            )

    if failures:
        raise SystemExit("LIVE smoke verification failed:\n- " + "\n- ".join(failures))

    print("LIVE_SMOKE_STATUS: PASS")


if __name__ == "__main__":
    main()
