"""Backward-compatible imports for the attribute extraction provider boundary."""

from .providers.attributes import AttributeExtractionClient


# Existing imports keep working, but GitHub Models is no longer an active backend.
GitHubModelsClient = AttributeExtractionClient

__all__ = ["AttributeExtractionClient", "GitHubModelsClient"]
