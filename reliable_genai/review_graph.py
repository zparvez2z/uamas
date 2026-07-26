from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from typing import Any, TypedDict

from .models import PredictionResponse, ProductInput
from .scoring import apply_abstention_policy

try:
    from langgraph.cache.memory import InMemoryCache
    from langgraph.graph import END, START, StateGraph
    from langgraph.runtime import Runtime
    from langgraph.types import CachePolicy, RetryPolicy

    LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - exercised through availability checks.
    LANGGRAPH_AVAILABLE = False


@dataclass(frozen=True)
class ReviewGraphContext:
    enabled: bool = False
    confidence_threshold: float = 0.55
    set_size_trigger: int = 3
    semantic_threshold: float = 0.4
    cache_ttl_seconds: int = 300
    gate_strategy: str = "legacy"
    very_low_confidence_floor: float = 0.35


class ReviewGraphState(TypedDict, total=False):
    item: ProductInput
    first_response: PredictionResponse
    second_response: PredictionResponse
    final_response: PredictionResponse
    review_trigger_reason: str | None
    review_outcome: str
    cache_key_config: dict[str, Any]


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _normalize_gate_strategy(value: str | None) -> str:
    candidate = (value or "legacy").strip().lower()
    if candidate in {"legacy", "latency_v1"}:
        return candidate
    return "legacy"


def _second_pass_cache_key(*args: Any, **kwargs: Any) -> str:
    state = args[0] if args else kwargs.get("state", {})
    item = state.get("item")
    config = state.get("cache_key_config", {})
    payload = {
        "title": getattr(item, "title", ""),
        "description": getattr(item, "description", ""),
        "confidence_threshold": config.get("confidence_threshold"),
        "set_size_trigger": config.get("set_size_trigger"),
        "semantic_threshold": config.get("semantic_threshold"),
        "gate_strategy": config.get("gate_strategy"),
        "very_low_confidence_floor": config.get("very_low_confidence_floor"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class ReviewGraphRunner:
    """Optional review graph wrapper around ReliabilityPipeline."""

    def __init__(
        self,
        pipeline: Any,
        *,
        enabled: bool | None = None,
        confidence_threshold: float | None = None,
        set_size_trigger: int | None = None,
        semantic_threshold: float | None = None,
        cache_ttl_seconds: int | None = None,
        gate_strategy: str | None = None,
        very_low_confidence_floor: float | None = None,
        retry_max_attempts: int | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.default_context = self._build_default_context(
            enabled=enabled,
            confidence_threshold=confidence_threshold,
            set_size_trigger=set_size_trigger,
            semantic_threshold=semantic_threshold,
            cache_ttl_seconds=cache_ttl_seconds,
            gate_strategy=gate_strategy,
            very_low_confidence_floor=very_low_confidence_floor,
        )
        self.retry_max_attempts = retry_max_attempts or int(os.getenv("REVIEW_RETRY_MAX_ATTEMPTS", "2"))
        self.available = LANGGRAPH_AVAILABLE
        self.backend = "langgraph" if self.available else "sequential"
        self.reason = "ok" if self.available else "langgraph_not_installed"
        self._cache_backend = InMemoryCache() if self.available else None
        self._compiled_graphs: dict[int, Any] = {}
        self._stats = {
            "enabled_requests": 0,
            "triggered_requests": 0,
            "second_pass_requests": 0,
            "semantic_triggered_requests": 0,
            "cache_hit_steps": 0,
        }

        if self.available:
            try:
                self._compiled_graphs[self.default_context.cache_ttl_seconds] = self._compile_graph(
                    self.default_context.cache_ttl_seconds
                )
            except Exception as exc:  # pragma: no cover - defensive in case of runtime mismatch
                self.available = False
                self.backend = "sequential"
                self.reason = f"graph_compile_failed: {exc}"
                self._compiled_graphs = {}

    def _build_default_context(
        self,
        *,
        enabled: bool | None,
        confidence_threshold: float | None,
        set_size_trigger: int | None,
        semantic_threshold: float | None,
        cache_ttl_seconds: int | None,
        gate_strategy: str | None,
        very_low_confidence_floor: float | None,
    ) -> ReviewGraphContext:
        enabled_value = (
            enabled
            if enabled is not None
            else _parse_bool(os.getenv("ENABLE_LANGGRAPH_REVIEW"), default=False)
        )
        confidence_value = (
            confidence_threshold
            if confidence_threshold is not None
            else float(os.getenv("REVIEW_CONFIDENCE_THRESHOLD", "0.55"))
        )
        set_size_value = (
            set_size_trigger
            if set_size_trigger is not None
            else int(os.getenv("REVIEW_SET_SIZE_TRIGGER", str(getattr(self.pipeline, "max_set_size", 3))))
        )
        semantic_threshold_value = (
            semantic_threshold
            if semantic_threshold is not None
            else float(os.getenv("SEMANTIC_CONSISTENCY_THRESHOLD", "0.4"))
        )
        cache_ttl_value = (
            cache_ttl_seconds
            if cache_ttl_seconds is not None
            else int(os.getenv("REVIEW_CACHE_TTL_SECONDS", "300"))
        )
        gate_strategy_value = _normalize_gate_strategy(
            gate_strategy if gate_strategy is not None else os.getenv("REVIEW_GATE_STRATEGY", "legacy")
        )
        very_low_confidence_floor_value = (
            very_low_confidence_floor
            if very_low_confidence_floor is not None
            else float(os.getenv("REVIEW_VERY_LOW_CONFIDENCE_FLOOR", "0.35"))
        )
        return ReviewGraphContext(
            enabled=enabled_value,
            confidence_threshold=confidence_value,
            set_size_trigger=set_size_value,
            semantic_threshold=semantic_threshold_value,
            cache_ttl_seconds=max(1, cache_ttl_value),
            gate_strategy=gate_strategy_value,
            very_low_confidence_floor=very_low_confidence_floor_value,
        )

    def _resolve_context(self, context: ReviewGraphContext | dict[str, Any] | None) -> ReviewGraphContext:
        if context is None:
            return self.default_context
        if isinstance(context, ReviewGraphContext):
            return context
        merged = asdict(self.default_context)
        for key in (
            "enabled",
            "confidence_threshold",
            "set_size_trigger",
            "semantic_threshold",
            "cache_ttl_seconds",
            "gate_strategy",
            "very_low_confidence_floor",
        ):
            if key in context and context[key] is not None:
                merged[key] = context[key]
        merged["cache_ttl_seconds"] = max(1, int(merged["cache_ttl_seconds"]))
        merged["gate_strategy"] = _normalize_gate_strategy(str(merged["gate_strategy"]))
        return ReviewGraphContext(**merged)

    def _compile_graph(self, cache_ttl_seconds: int) -> Any:
        builder = StateGraph(ReviewGraphState, context_schema=ReviewGraphContext)
        builder.set_node_defaults(retry_policy=RetryPolicy(max_attempts=self.retry_max_attempts))
        builder.add_node("first_pass", self._node_first_pass)
        builder.add_node("gate", self._node_gate)
        builder.add_node(
            "second_pass",
            self._node_second_pass,
            cache_policy=CachePolicy(ttl=cache_ttl_seconds, key_func=_second_pass_cache_key),
        )
        builder.add_node("finalize", self._node_finalize)
        builder.add_edge(START, "first_pass")
        builder.add_edge("first_pass", "gate")
        builder.add_conditional_edges(
            "gate",
            self._route_after_gate,
            {
                "second_pass": "second_pass",
                "finalize": "finalize",
            },
        )
        builder.add_edge("second_pass", "finalize")
        builder.add_edge("finalize", END)
        return builder.compile(cache=self._cache_backend)

    def _get_compiled_graph(self, cache_ttl_seconds: int) -> Any | None:
        if not self.available:
            return None
        graph = self._compiled_graphs.get(cache_ttl_seconds)
        if graph is not None:
            return graph
        try:
            graph = self._compile_graph(cache_ttl_seconds)
        except Exception as exc:  # pragma: no cover - defensive in case of runtime mismatch
            self.available = False
            self.backend = "sequential"
            self.reason = f"graph_compile_failed: {exc}"
            return None
        self._compiled_graphs[cache_ttl_seconds] = graph
        return graph

    def _node_first_pass(self, state: ReviewGraphState) -> ReviewGraphState:
        if "first_response" in state:
            return {"first_response": state["first_response"]}
        return {"first_response": self.pipeline.predict(state["item"])}

    def _compute_trigger_reason(self, first: PredictionResponse, context: ReviewGraphContext) -> str | None:
        semantic_score = first.reliability.semantic_consistency_score
        semantic_ok = first.reliability.semantic_consistency_status == "ok" and semantic_score is not None
        if context.gate_strategy == "latency_v1":
            if first.reliability.abstained:
                return "abstained"
            if first.reliability.confidence < context.very_low_confidence_floor:
                return "very_low_confidence"
            if (
                first.reliability.confidence < context.confidence_threshold
                and first.reliability.set_size >= context.set_size_trigger
            ):
                return "low_confidence_large_set"
            if semantic_ok and float(semantic_score) < context.semantic_threshold:
                return "low_semantic_consistency"
            return None

        if first.reliability.abstained:
            return "abstained"
        if first.reliability.confidence < context.confidence_threshold:
            return "low_confidence"
        if first.reliability.set_size >= context.set_size_trigger:
            return "large_set"
        if semantic_ok and float(semantic_score) < context.semantic_threshold:
            return "low_semantic_consistency"
        return None

    def _node_gate(self, state: ReviewGraphState, runtime: Runtime[ReviewGraphContext]) -> ReviewGraphState:
        first = state["first_response"]
        reason = self._compute_trigger_reason(first, runtime.context)

        return {
            "review_trigger_reason": reason,
            "review_outcome": "triggered" if reason else "not_triggered",
            "cache_key_config": {
                "confidence_threshold": runtime.context.confidence_threshold,
                "set_size_trigger": runtime.context.set_size_trigger,
                "semantic_threshold": runtime.context.semantic_threshold,
                "gate_strategy": runtime.context.gate_strategy,
                "very_low_confidence_floor": runtime.context.very_low_confidence_floor,
            },
        }

    def _route_after_gate(self, state: ReviewGraphState) -> str:
        return "second_pass" if state.get("review_trigger_reason") else "finalize"

    def _build_second_pass_response(self, item: ProductInput, first: PredictionResponse) -> PredictionResponse:
        classifier_result = self.pipeline._classify(item)
        category_set = self.pipeline._conformal_set(classifier_result)
        policy = apply_abstention_policy(
            category_set=category_set,
            max_set_size=self.pipeline.max_set_size,
            enable_abstain=self.pipeline.enable_abstain,
        )

        second = first.model_copy(deep=True)
        second.category_set = list(policy.category_set)
        second.reliability.set_size = len(policy.category_set)
        second.reliability.confidence = max(classifier_result.probabilities.values())
        second.reliability.abstained = policy.abstained
        second.reliability.reason = policy.reason
        second.reliability.policy_action = policy.action
        return second

    def _node_second_pass(self, state: ReviewGraphState) -> ReviewGraphState:
        first = state["first_response"]
        second = self._build_second_pass_response(state["item"], first)
        return {"second_response": second}

    def _node_finalize(self, state: ReviewGraphState) -> ReviewGraphState:
        first = state["first_response"]
        second = state.get("second_response")
        trigger_reason = state.get("review_trigger_reason")

        selected = first
        outcome = "not_triggered"
        used = False
        if second is not None:
            if second.reliability.abstained and not first.reliability.abstained:
                selected = first
                outcome = "first_pass_retained"
            elif first.reliability.abstained and not second.reliability.abstained:
                selected = second
                outcome = "second_pass_selected"
                used = True
            elif second.reliability.confidence > first.reliability.confidence:
                selected = second
                outcome = "second_pass_selected"
                used = True
            else:
                selected = first
                outcome = "first_pass_retained"

        final = selected.model_copy(deep=True)
        final.reliability.review_graph_used = used
        final.reliability.review_trigger_reason = trigger_reason
        final.reliability.review_outcome = outcome
        return {
            "final_response": final,
            "review_outcome": outcome,
        }

    def _sequential_predict(
        self,
        item: ProductInput,
        context: ReviewGraphContext,
        first_response: PredictionResponse | None = None,
    ) -> PredictionResponse:
        first = first_response or self.pipeline.predict(item)
        trigger_reason = self._compute_trigger_reason(first, context)

        if trigger_reason is None:
            final = first.model_copy(deep=True)
            final.reliability.review_graph_used = False
            final.reliability.review_trigger_reason = None
            final.reliability.review_outcome = "not_triggered"
            return final

        second = self._build_second_pass_response(item, first)
        if first.reliability.abstained and not second.reliability.abstained:
            selected = second
            outcome = "second_pass_selected"
            used = True
        elif second.reliability.abstained and not first.reliability.abstained:
            selected = first
            outcome = "first_pass_retained"
            used = False
        elif second.reliability.confidence > first.reliability.confidence:
            selected = second
            outcome = "second_pass_selected"
            used = True
        else:
            selected = first
            outcome = "first_pass_retained"
            used = False

        final = selected.model_copy(deep=True)
        final.reliability.review_graph_used = used
        final.reliability.review_trigger_reason = trigger_reason
        final.reliability.review_outcome = outcome
        return final

    def _run(
        self,
        item: ProductInput,
        cfg: ReviewGraphContext,
        *,
        first_response: PredictionResponse | None,
    ) -> PredictionResponse:
        if not cfg.enabled:
            response = (first_response or self.pipeline.predict(item)).model_copy(deep=True)
            response.reliability.review_graph_used = False
            response.reliability.review_trigger_reason = None
            response.reliability.review_outcome = "disabled"
            return response

        self._stats["enabled_requests"] += 1
        graph = self._get_compiled_graph(cfg.cache_ttl_seconds)
        if graph is None:
            response = self._sequential_predict(item, cfg, first_response)
            if response.reliability.review_trigger_reason:
                self._stats["triggered_requests"] += 1
                self._stats["second_pass_requests"] += 1
                if response.reliability.review_trigger_reason == "low_semantic_consistency":
                    self._stats["semantic_triggered_requests"] += 1
            return response

        graph_input: ReviewGraphState = {"item": item}
        if first_response is not None:
            graph_input["first_response"] = first_response
        updates = list(graph.stream(graph_input, context=cfg, stream_mode="updates"))
        if any("second_pass" in update for update in updates):
            self._stats["second_pass_requests"] += 1

        final_response: PredictionResponse | None = None
        for update in updates:
            metadata = update.get("__metadata__", {})
            if metadata.get("cached"):
                self._stats["cache_hit_steps"] += 1
            finalize_update = update.get("finalize")
            if finalize_update and finalize_update.get("final_response") is not None:
                final_response = finalize_update["final_response"]

        if final_response is None:
            state = graph.invoke(graph_input, context=cfg)
            final_response = state["final_response"]

        if final_response.reliability.review_trigger_reason:
            self._stats["triggered_requests"] += 1
            if final_response.reliability.review_trigger_reason == "low_semantic_consistency":
                self._stats["semantic_triggered_requests"] += 1

        return final_response

    def predict(
        self,
        item: ProductInput,
        context: ReviewGraphContext | dict[str, Any] | None = None,
    ) -> PredictionResponse:
        return self._run(
            item,
            self._resolve_context(context),
            first_response=None,
        )

    def review_first_pass(
        self,
        item: ProductInput,
        first_response: PredictionResponse,
        context: ReviewGraphContext | dict[str, Any] | None = None,
    ) -> PredictionResponse:
        """Apply the optional review gate to an already-computed first pass."""
        return self._run(
            item,
            self._resolve_context(context),
            first_response=first_response,
        )

    def diagnostics(self) -> dict[str, Any]:
        enabled_requests = self._stats["enabled_requests"]
        triggered = self._stats["triggered_requests"]
        second_pass = self._stats["second_pass_requests"]
        semantic_triggered = self._stats["semantic_triggered_requests"]
        cache_hit_steps = self._stats["cache_hit_steps"]
        return {
            "enabled": self.default_context.enabled,
            "available": self.available,
            "backend": self.backend,
            "reason": self.reason,
            "confidence_threshold": self.default_context.confidence_threshold,
            "set_size_trigger": self.default_context.set_size_trigger,
            "semantic_threshold": self.default_context.semantic_threshold,
            "cache_ttl_seconds": self.default_context.cache_ttl_seconds,
            "gate_strategy": self.default_context.gate_strategy,
            "very_low_confidence_floor": self.default_context.very_low_confidence_floor,
            "review_graph_trigger_rate": round(triggered / enabled_requests, 3) if enabled_requests else 0.0,
            "review_graph_second_pass_rate": round(second_pass / enabled_requests, 3) if enabled_requests else 0.0,
            "review_graph_semantic_trigger_rate": (
                round(semantic_triggered / enabled_requests, 3) if enabled_requests else 0.0
            ),
            "review_graph_cache_hit_rate": round(cache_hit_steps / second_pass, 3) if second_pass else 0.0,
            "review_graph_cached_step_count": cache_hit_steps,
        }
