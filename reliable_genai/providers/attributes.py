from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import ValidationError

from ..models import LLMExtraction, ProductAttributes


DEFAULT_ATTRIBUTE_MODEL = "Qwen/Qwen3.5-9B"
DEFAULT_ATTRIBUTE_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_attribute_provider() -> str:
    explicit = os.getenv("ATTRIBUTE_PROVIDER")
    if explicit:
        provider = explicit.strip().lower()
    else:
        provider = (
            "mock"
            if _parse_bool(os.getenv("USE_MOCK_LLM"), default=True)
            else "huggingface_local"
        )
    provider = {
        "hf": "huggingface_local",
        "local_hf": "huggingface_local",
        "huggingface": "huggingface_local",
    }.get(provider, provider)
    if provider not in {"mock", "huggingface_local"}:
        raise ValueError(
            "ATTRIBUTE_PROVIDER must be 'mock' or 'huggingface_local'"
        )
    return provider


def attribute_runtime_config_from_env() -> dict[str, object]:
    provider = resolve_attribute_provider()
    return {
        "provider": provider,
        "model": (
            "deterministic-rule-extractor"
            if provider == "mock"
            else os.getenv("ATTRIBUTE_MODEL", DEFAULT_ATTRIBUTE_MODEL)
        ),
        "revision": (
            None
            if provider == "mock"
            else os.getenv("ATTRIBUTE_MODEL_REVISION", DEFAULT_ATTRIBUTE_REVISION)
        ),
        "quantization": (
            "none"
            if provider == "mock"
            else os.getenv("ATTRIBUTE_QUANTIZATION", "nf4")
        ),
        "compute_dtype": (
            "cpu"
            if provider == "mock"
            else os.getenv("ATTRIBUTE_COMPUTE_DTYPE", "float16")
        ),
        "device": (
            "cpu"
            if provider == "mock"
            else os.getenv("ATTRIBUTE_DEVICE", "auto")
        ),
        "max_input_tokens": int(os.getenv("ATTRIBUTE_MAX_INPUT_TOKENS", "4096")),
        "max_new_tokens": int(os.getenv("ATTRIBUTE_MAX_NEW_TOKENS", "192")),
    }


@dataclass(frozen=True)
class ExtractionOutcome:
    attributes: ProductAttributes
    runtime: str
    provider: str
    model: str
    revision: str | None = None
    quantization: str | None = None
    compute_dtype: str | None = None
    device: str | None = None
    latency_ms: float | None = None
    error: str | None = None


class AttributeExtractor(Protocol):
    config: dict[str, object]

    def extract(self, title: str, description: str) -> ExtractionOutcome: ...


class MockAttributeExtractor:
    def __init__(self) -> None:
        self.config = {
            "provider": "mock",
            "model": "deterministic-rule-extractor",
            "revision": None,
            "quantization": "none",
            "compute_dtype": "cpu",
            "device": "cpu",
            "max_input_tokens": 4096,
            "max_new_tokens": 0,
        }

    def extract(self, title: str, description: str) -> ExtractionOutcome:
        started = time.perf_counter()
        return ExtractionOutcome(
            attributes=self._extract_rules(title, description),
            runtime="MOCK",
            provider="mock",
            model=str(self.config["model"]),
            quantization="none",
            compute_dtype="cpu",
            device="cpu",
            latency_ms=round((time.perf_counter() - started) * 1000, 3),
        )

    @staticmethod
    def _extract_rules(title: str, description: str) -> ProductAttributes:
        text = f"{title} {description}".lower()

        def first(candidates: list[str]) -> str:
            return next((value for value in candidates if value in text), "unknown")

        brand = first(["nike", "adidas", "puma", "apple", "samsung", "ikea"])
        color = first(["black", "white", "blue", "red", "green", "gray"])
        material = first(["cotton", "leather", "plastic", "mesh", "wood", "metal"])
        size = "unknown"
        for candidate in ["xl", "l", "m", "s", "42", "43", "44", "1l", "500ml"]:
            if f" {candidate} " in f" {text} ":
                size = candidate
                break
        try:
            return ProductAttributes(
                brand=brand,
                color=color,
                material=material,
                size=size,
            )
        except ValidationError:
            return ProductAttributes()


class HuggingFaceAttributeExtractor:
    """Lazy, text-only Qwen extractor intended for a Colab T4 runtime."""

    SYSTEM_PROMPT = (
        "Extract only attributes explicitly supported by the product text. "
        "Return strict JSON with exactly this shape: "
        '{"attributes":{"brand":"string","color":"string",'
        '"material":"string","size":"string"}}. '
        "Use 'unknown' for missing values. Do not infer unsupported values."
    )

    def __init__(self) -> None:
        self.config = attribute_runtime_config_from_env()
        self._model: Any = None
        self._processor: Any = None
        self._resolved_device: str | None = None

    def extract(self, title: str, description: str) -> ExtractionOutcome:
        started = time.perf_counter()
        try:
            self._ensure_loaded()
            user_prompt = f"Title: {title}\nDescription: {description}"
            content = self._generate(self.SYSTEM_PROMPT, user_prompt)
            try:
                attributes = self._validate(content)
            except Exception as first_error:
                repair_prompt = (
                    f"The previous response was invalid ({type(first_error).__name__}). "
                    "Return only valid JSON matching the required schema.\n"
                    f"Previous response:\n{content}"
                )
                attributes = self._validate(
                    self._generate(self.SYSTEM_PROMPT, repair_prompt)
                )
            return ExtractionOutcome(
                attributes=attributes,
                runtime="LOCAL_HF",
                provider="huggingface_local",
                model=str(self.config["model"]),
                revision=str(self.config["revision"]),
                quantization=str(self.config["quantization"]),
                compute_dtype=str(self.config["compute_dtype"]),
                device=self._resolved_device or str(self.config["device"]),
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
            )
        except Exception as exc:
            return ExtractionOutcome(
                attributes=ProductAttributes(),
                runtime="FAILED",
                provider="huggingface_local",
                model=str(self.config["model"]),
                revision=str(self.config["revision"]),
                quantization=str(self.config["quantization"]),
                compute_dtype=str(self.config["compute_dtype"]),
                device=self._resolved_device or str(self.config["device"]),
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                error=f"{type(exc).__name__}: {exc}",
            )

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._processor is not None:
            return
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError as exc:
            raise RuntimeError(
                "local Hugging Face runtime dependencies are not installed; "
                "install requirements-colab.txt"
            ) from exc

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA GPU is required for Qwen3.5-9B NF4 runtime")
        if str(self.config["quantization"]).lower() != "nf4":
            raise ValueError("only nf4 quantization is supported by this runtime")

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        common = {
            "revision": self.config["revision"],
            "trust_remote_code": False,
        }
        self._processor = AutoTokenizer.from_pretrained(
            str(self.config["model"]),
            **common,
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            str(self.config["model"]),
            quantization_config=quantization_config,
            device_map="auto",
            dtype=torch.float16,
            low_cpu_mem_usage=True,
            **common,
        )
        self._model.eval()
        self._resolved_device = str(next(self._model.parameters()).device)

    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        rendered = self._processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self._processor(
            text=[rendered],
            return_tensors="pt",
            truncation=True,
            max_length=int(self.config["max_input_tokens"]),
        ).to(self._model.device)
        generated = self._model.generate(
            **inputs,
            max_new_tokens=int(self.config["max_new_tokens"]),
            do_sample=False,
            use_cache=True,
        )
        prompt_length = inputs["input_ids"].shape[1]
        return self._processor.batch_decode(
            generated[:, prompt_length:],
            skip_special_tokens=True,
        )[0].strip()

    @staticmethod
    def _validate(content: str) -> ProductAttributes:
        payload = _parse_json_object(content)
        return LLMExtraction.model_validate(payload).attributes


def _parse_json_object(content: str) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(content[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("model response must be a JSON object")
    return value


class AttributeExtractionClient:
    """Compatibility facade used by the pipeline and diagnostics."""

    def __init__(self, extractor: AttributeExtractor | None = None) -> None:
        provider = resolve_attribute_provider()
        self._extractor = extractor or (
            MockAttributeExtractor()
            if provider == "mock"
            else HuggingFaceAttributeExtractor()
        )
        config = self._extractor.config
        self.provider = str(config["provider"])
        self.model = str(config["model"])
        self.revision = config.get("revision")
        self.quantization = str(config.get("quantization") or "none")
        self.compute_dtype = str(config.get("compute_dtype") or "unknown")
        self.device = str(config.get("device") or "unknown")
        self.endpoint = "in-process"
        self.api_key = ""
        self.use_mock = self.provider == "mock"
        self.last_runtime = "MOCK" if self.use_mock else "LOCAL_HF_NOT_LOADED"
        self.last_error: str | None = None
        self.last_latency_ms: float | None = None
        self.last_outcome: ExtractionOutcome | None = None

    def extract_attributes(self, title: str, description: str) -> ProductAttributes:
        outcome = self._extractor.extract(title, description)
        self.last_outcome = outcome
        self.last_runtime = outcome.runtime
        self.last_error = outcome.error
        self.last_latency_ms = outcome.latency_ms
        self.device = outcome.device or self.device
        return outcome.attributes

    def diagnostics(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "revision": self.revision,
            "quantization": self.quantization,
            "compute_dtype": self.compute_dtype,
            "device": self.device,
            "runtime_mode": "MOCK" if self.use_mock else "LOCAL_HF",
            "last_runtime": self.last_runtime,
            "last_error": self.last_error,
            "last_latency_ms": self.last_latency_ms,
        }
