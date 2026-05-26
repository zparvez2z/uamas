#!/usr/bin/env bash
set -euo pipefail

USE_MOCK_LLM=false .venv/bin/python - <<'PY'
from app.main import build_diagnostics, review_graph
from reliable_genai.models import ProductInput

print("INITIAL:", {k: build_diagnostics().get(k) for k in ["runtime_mode", "last_runtime", "llm_last_error", "model", "endpoint"]})

samples = [
    ProductInput(title="Nike running shoes black size 42", description="Breathable mesh upper and cushioned sole"),
    ProductInput(title="Sony mini Wireless Headphones", description="Bluetooth over-ear headphones black"),
    ProductInput(title="Spa Gift Set", description="Body lotion, scented candle, decorative storage box"),
]

for i, item in enumerate(samples, 1):
    response = review_graph.predict(item)
    diag = build_diagnostics()
    print(f"PREDICT_{i}:", {
        "llm_runtime": response.reliability.llm_runtime,
        "diag_last_runtime": diag.get("last_runtime"),
        "diag_llm_last_error": diag.get("llm_last_error"),
        "category_set": response.category_set,
    })
PY
