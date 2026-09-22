#!/usr/bin/env python3
"""Load local model providers and fail unless both produce usable output."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from reliable_genai.pipeline import ReliabilityPipeline


def main() -> int:
    os.environ.setdefault("ATTRIBUTE_PROVIDER", "huggingface_local")
    os.environ.setdefault("ENABLE_SEMANTIC_SCORER", "true")
    os.environ.setdefault("SEMANTIC_PROVIDER", "sentence_transformers")
    pipeline = ReliabilityPipeline()
    result = pipeline.preflight()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["llm_runtime"] != "LOCAL_HF":
        raise RuntimeError(f"attribute preflight failed: {result}")
    if result["semantic_status"] != "ok":
        raise RuntimeError(f"semantic preflight failed: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
