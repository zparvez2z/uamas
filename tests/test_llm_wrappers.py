from reliable_genai.llm_wrappers import GitHubModelsClient
from reliable_genai.models import ProductAttributes


class FailingClient:
    def complete(self, **kwargs):
        raise RuntimeError("forced_live_failure")


def test_extract_attributes_uses_mock_mode_without_error(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    client = GitHubModelsClient()
    attributes = client.extract_attributes("Nike running shoes", "black mesh")

    assert isinstance(attributes, ProductAttributes)
    assert client.last_runtime == "MOCK"
    assert client.last_error is None


def test_extract_attributes_reports_fallback_error_when_live_call_fails(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-token")

    client = GitHubModelsClient()
    client._client = FailingClient()
    client.max_retries = 0

    attributes = client.extract_attributes("Nike running shoes", "black mesh")

    assert isinstance(attributes, ProductAttributes)
    assert client.last_runtime == "FALLBACK_MOCK"
    assert "RuntimeError: forced_live_failure" in (client.last_error or "")

