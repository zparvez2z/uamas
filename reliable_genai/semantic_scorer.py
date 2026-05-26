from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Iterable, Optional

from azure.ai.inference import EmbeddingsClient
from azure.core.credentials import AzureKeyCredential

from .models import ProductInput


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


@dataclass(frozen=True)
class SemanticConsistencyResult:
    score: float | None
    status: str
    reason: str | None


class SemanticConsistencyScorer:
    """Embedding-based semantic consistency scorer with graceful degradation."""

    DEFAULT_PROTOTYPES = {
        "Shoes": "footwear shoes sneakers boots running walking",
        "Clothing": "apparel clothing shirt jacket pants dress fabric",
        "Electronics": "electronics device monitor headphones phone charger",
        "Home": "home household furniture storage lamp kitchen decor",
        "Beauty": "beauty skincare shampoo cream makeup serum cosmetics",
        "Sports": "sports fitness training yoga exercise equipment racket",
    }

    def __init__(
        self,
        labels: Iterable[str],
        *,
        enabled: bool | None = None,
        threshold: float | None = None,
        max_retries: int | None = None,
        endpoint: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        prototypes: dict[str, str] | None = None,
    ) -> None:
        self.labels = list(labels)
        self.enabled = (
            enabled
            if enabled is not None
            else _parse_bool(os.getenv("ENABLE_SEMANTIC_SCORER"), default=True)
        )
        self.threshold = (
            float(threshold)
            if threshold is not None
            else float(os.getenv("SEMANTIC_CONSISTENCY_THRESHOLD", "0.4"))
        )
        self.max_retries = (
            int(max_retries) if max_retries is not None else int(os.getenv("SEMANTIC_MAX_RETRIES", "1"))
        )
        self.endpoint = endpoint or os.getenv("GITHUB_MODELS_ENDPOINT", "https://models.github.ai/inference")
        self.api_key = api_key or os.getenv("GITHUB_TOKEN", os.getenv("GITHUB_MODELS_API_KEY", ""))
        self.model = model or os.getenv("GITHUB_MODELS_EMBEDDING_MODEL", "openai/text-embedding-3-small")
        self.prototypes = dict(self.DEFAULT_PROTOTYPES)
        if prototypes:
            self.prototypes.update(prototypes)

        self._client: Optional[EmbeddingsClient] = None
        if self.enabled and self.api_key:
            self._client = EmbeddingsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key),
            )

        self._prototype_embedding_cache: dict[str, list[float]] = {}
        self._stats = {
            "requests": 0,
            "ok_requests": 0,
            "degraded_requests": 0,
            "disabled_requests": 0,
        }

    def score(self, item: ProductInput, candidate_labels: list[str] | None = None) -> SemanticConsistencyResult:
        self._stats["requests"] += 1

        if not self.enabled:
            self._stats["disabled_requests"] += 1
            return SemanticConsistencyResult(
                score=None,
                status="disabled",
                reason="semantic_scorer_disabled",
            )
        if self._client is None:
            self._stats["degraded_requests"] += 1
            return SemanticConsistencyResult(
                score=None,
                status="degraded",
                reason="embedding_client_unavailable",
            )

        labels = [label for label in (candidate_labels or self.labels) if label in self.prototypes]
        if not labels:
            labels = [label for label in self.labels if label in self.prototypes]
        if not labels:
            self._stats["degraded_requests"] += 1
            return SemanticConsistencyResult(
                score=None,
                status="degraded",
                reason="semantic_label_prototypes_unavailable",
            )

        text = f"{item.title} {item.description}".strip()
        try:
            query_vector = self._embed_texts([text])[0]
            prototype_vectors = self._get_prototype_embeddings(labels)
        except Exception as exc:
            self._stats["degraded_requests"] += 1
            return SemanticConsistencyResult(
                score=None,
                status="degraded",
                reason=f"{type(exc).__name__}: {exc}",
            )

        similarities = [_cosine_similarity(query_vector, vector) for vector in prototype_vectors.values()]
        if not similarities:
            self._stats["degraded_requests"] += 1
            return SemanticConsistencyResult(
                score=None,
                status="degraded",
                reason="semantic_similarity_unavailable",
            )

        score = _clamp((max(similarities) + 1.0) / 2.0, 0.0, 1.0)
        self._stats["ok_requests"] += 1
        return SemanticConsistencyResult(
            score=score,
            status="ok",
            reason=None,
        )

    def diagnostics(self) -> dict[str, object]:
        requests = self._stats["requests"]
        degraded = self._stats["degraded_requests"]
        return {
            "enabled": self.enabled,
            "threshold": self.threshold,
            "model": self.model,
            "endpoint": self.endpoint,
            "client_available": self._client is not None,
            "requests": requests,
            "ok_requests": self._stats["ok_requests"],
            "degraded_requests": degraded,
            "disabled_requests": self._stats["disabled_requests"],
            "degraded_rate": round(degraded / requests, 3) if requests else 0.0,
        }

    def _get_prototype_embeddings(self, labels: list[str]) -> dict[str, list[float]]:
        missing = [label for label in labels if label not in self._prototype_embedding_cache]
        if missing:
            vectors = self._embed_texts([self.prototypes[label] for label in missing])
            for label, vector in zip(missing, vectors):
                self._prototype_embedding_cache[label] = vector
        return {label: self._prototype_embedding_cache[label] for label in labels}

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._client is None:
            raise RuntimeError("embedding client unavailable")
        last_exception: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                result = self._client.embed(input=texts, model=self.model)
                vectors = [self._extract_vector(item) for item in result.data]
                if len(vectors) != len(texts):
                    raise RuntimeError(
                        f"embedding result count mismatch: expected {len(texts)} vectors, got {len(vectors)}"
                    )
                return vectors
            except Exception as exc:  # pragma: no cover - exercised via failure tests
                last_exception = exc
                continue
        raise RuntimeError(f"embedding_request_failed: {last_exception}")

    @staticmethod
    def _extract_vector(item: object) -> list[float]:
        if isinstance(item, dict):
            vector = item.get("embedding", [])
            return [float(value) for value in vector]
        vector = getattr(item, "embedding", [])
        return [float(value) for value in vector]
