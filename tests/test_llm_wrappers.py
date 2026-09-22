from reliable_genai.llm_wrappers import GitHubModelsClient
from reliable_genai.models import ProductAttributes
from reliable_genai.providers.attributes import ExtractionOutcome


class FailingExtractor:
    config = {
        "provider": "huggingface_local",
        "model": "Qwen/Qwen3.5-9B",
        "revision": "test-revision",
        "quantization": "nf4",
        "compute_dtype": "float16",
        "device": "cuda:0",
    }

    def extract(self, title: str, description: str) -> ExtractionOutcome:
        return ExtractionOutcome(
            attributes=ProductAttributes(),
            runtime="FAILED",
            provider="huggingface_local",
            model="Qwen/Qwen3.5-9B",
            revision="test-revision",
            quantization="nf4",
            compute_dtype="float16",
            device="cuda:0",
            error="RuntimeError: forced_local_failure",
        )


def test_extract_attributes_uses_mock_mode_without_error(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    client = GitHubModelsClient()
    attributes = client.extract_attributes("Nike running shoes", "black mesh")

    assert isinstance(attributes, ProductAttributes)
    assert client.last_runtime == "MOCK"
    assert client.last_error is None


def test_extract_attributes_reports_failure_without_mock_fallback() -> None:
    client = GitHubModelsClient(extractor=FailingExtractor())

    attributes = client.extract_attributes("Nike running shoes", "black mesh")

    assert isinstance(attributes, ProductAttributes)
    assert attributes == ProductAttributes()
    assert client.last_runtime == "FAILED"
    assert "RuntimeError: forced_local_failure" in (client.last_error or "")
    assert client.provider == "huggingface_local"


def test_explicit_provider_takes_precedence_over_legacy_mock_flag(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    monkeypatch.setenv("ATTRIBUTE_PROVIDER", "huggingface_local")

    client = GitHubModelsClient()

    assert client.provider == "huggingface_local"
    assert client.use_mock is False
    assert client.model == "Qwen/Qwen3.5-9B"
    assert client.revision == "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
