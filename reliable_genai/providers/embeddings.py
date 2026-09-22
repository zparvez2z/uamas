from __future__ import annotations

import os
from typing import Protocol


DEFAULT_SEMANTIC_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_SEMANTIC_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


class EmbeddingBackend(Protocol):
    provider: str
    model: str
    revision: str | None
    device: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def semantic_runtime_config_from_env() -> dict[str, object]:
    enabled = os.getenv("ENABLE_SEMANTIC_SCORER", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    provider = os.getenv(
        "SEMANTIC_PROVIDER",
        "sentence_transformers" if enabled else "disabled",
    ).strip().lower()
    if not enabled:
        provider = "disabled"
    if provider not in {"disabled", "sentence_transformers"}:
        raise ValueError(
            "SEMANTIC_PROVIDER must be 'disabled' or 'sentence_transformers'"
        )
    return {
        "provider": provider,
        "model": os.getenv("SEMANTIC_MODEL", DEFAULT_SEMANTIC_MODEL),
        "revision": os.getenv("SEMANTIC_MODEL_REVISION", DEFAULT_SEMANTIC_REVISION),
        "device": os.getenv("SEMANTIC_DEVICE", "cpu"),
    }


class SentenceTransformerEmbeddingBackend:
    def __init__(
        self,
        *,
        model: str = DEFAULT_SEMANTIC_MODEL,
        revision: str = DEFAULT_SEMANTIC_REVISION,
        device: str = "cpu",
    ) -> None:
        self.provider = "sentence_transformers"
        self.model = model
        self.revision = revision
        self.device = device
        self._encoder = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is not installed; install requirements-colab.txt"
                ) from exc
            self._encoder = SentenceTransformer(
                self.model,
                revision=self.revision,
                device=self.device,
            )
        values = self._encoder.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [[float(value) for value in vector] for vector in values]
