"""Runtime provider boundaries for model-backed pipeline stages."""

from .attributes import (
    DEFAULT_ATTRIBUTE_MODEL,
    DEFAULT_ATTRIBUTE_REVISION,
    AttributeExtractionClient,
    ExtractionOutcome,
    attribute_runtime_config_from_env,
)
from .embeddings import (
    DEFAULT_SEMANTIC_MODEL,
    DEFAULT_SEMANTIC_REVISION,
    EmbeddingBackend,
    SentenceTransformerEmbeddingBackend,
    semantic_runtime_config_from_env,
)

__all__ = [
    "DEFAULT_ATTRIBUTE_MODEL",
    "DEFAULT_ATTRIBUTE_REVISION",
    "DEFAULT_SEMANTIC_MODEL",
    "DEFAULT_SEMANTIC_REVISION",
    "AttributeExtractionClient",
    "EmbeddingBackend",
    "ExtractionOutcome",
    "SentenceTransformerEmbeddingBackend",
    "attribute_runtime_config_from_env",
    "semantic_runtime_config_from_env",
]
