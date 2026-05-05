import json
import os
from typing import Any, Dict, Optional

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from pydantic import ValidationError

from .models import LLMExtraction, ProductAttributes


class GitHubModelsClient:
    """Thin wrapper around GitHub Models endpoint with retry and schema validation."""

    def __init__(self) -> None:
        self.endpoint = os.getenv("GITHUB_MODELS_ENDPOINT", "https://models.github.ai/inference")
        self.api_key = os.getenv("GITHUB_TOKEN", os.getenv("GITHUB_MODELS_API_KEY", ""))
        self.model = os.getenv("GITHUB_MODELS_MODEL", "openai/gpt-4.1")
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
        self.use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
        self.last_runtime = "MOCK" if self.use_mock else "LIVE"

        self._client: Optional[ChatCompletionsClient] = None
        if self.api_key:
            self._client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key),
            )

    def extract_attributes(self, title: str, description: str) -> ProductAttributes:
        if self.use_mock or not self._client:
            self.last_runtime = "MOCK"
            return self._mock_extract(title, description)

        system_prompt = (
            "You extract product attributes. Respond as strict JSON with this shape: "
            '{"attributes":{"brand":"string","color":"string","material":"string","size":"string"}}. '
            "Use 'unknown' when not present."
        )
        user_prompt = f"Title: {title}\nDescription: {description}"

        for _ in range(self.max_retries + 1):
            try:
                completion = self._client.complete(
                    model=self.model,
                    temperature=0,
                    messages=[
                        SystemMessage(content=system_prompt),
                        UserMessage(content=user_prompt),
                    ],
                )
                payload = completion.choices[0].message.content or "{}"
                parsed = self._parse_json(payload)
                extraction = LLMExtraction.model_validate(parsed)
                self.last_runtime = "LIVE"
                return extraction.attributes
            except Exception:
                continue

            self.last_runtime = "FALLBACK_MOCK"
        return self._mock_extract(title, description)

    @staticmethod
    def _parse_json(content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Attempt to recover JSON from markdown-style fenced output.
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                return json.loads(content[start : end + 1])
            raise

    @staticmethod
    def _mock_extract(title: str, description: str) -> ProductAttributes:
        text = f"{title} {description}".lower()

        brand = "unknown"
        for candidate in ["nike", "adidas", "puma", "apple", "samsung", "ikea"]:
            if candidate in text:
                brand = candidate
                break

        color = "unknown"
        for candidate in ["black", "white", "blue", "red", "green", "gray"]:
            if candidate in text:
                color = candidate
                break

        material = "unknown"
        for candidate in ["cotton", "leather", "plastic", "mesh", "wood", "metal"]:
            if candidate in text:
                material = candidate
                break

        size = "unknown"
        for candidate in ["xl", "l", "m", "s", "42", "43", "44", "1l", "500ml"]:
            if f" {candidate} " in f" {text} ":
                size = candidate
                break

        try:
            return ProductAttributes(brand=brand, color=color, material=material, size=size)
        except ValidationError:
            return ProductAttributes()
