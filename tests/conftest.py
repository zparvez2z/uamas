from __future__ import annotations

import os


# Test collection imports app.main, which constructs the runtime pipeline.
# Keep that import deterministic and prevent local .env drift from rewriting the
# shared classifier artifact before individual tests can install fixtures.
os.environ.setdefault("ALPHA", "0.1")
os.environ.setdefault("CLASSIFIER_MODEL_TYPE", "embedding")
os.environ.setdefault("STRICT_ARTIFACT_METADATA", "true")
os.environ.setdefault(
    "CLASSIFIER_ARTIFACT_PATH",
    f"/tmp/uamas-pytest-classifier-{os.getpid()}.joblib",
)
os.environ.setdefault("USE_MOCK_LLM", "true")
os.environ.setdefault("ENABLE_SEMANTIC_SCORER", "false")
