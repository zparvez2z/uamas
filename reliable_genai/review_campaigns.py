from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Protocol, Sequence

from .models import CatalogQualityDecision, ListingInput, bound_product_text
from .persistence import SQLiteReviewStore
from .pipeline import ReliabilityPipeline


DEFAULT_FEEDBACK_POOL_PATH = Path("data/processed/feedback_pool.json")
DEFAULT_DATASET_METADATA_PATH = Path("data/processed/dataset_metadata.json")


class CatalogAnalyzer(Protocol):
    def analyze(self, listing: ListingInput) -> CatalogQualityDecision: ...


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class ReviewCampaignService:
    def __init__(
        self,
        store: SQLiteReviewStore | None,
        *,
        analyzer: CatalogAnalyzer | None = None,
        feedback_pool_path: str | Path = DEFAULT_FEEDBACK_POOL_PATH,
        metadata_path: str | Path = DEFAULT_DATASET_METADATA_PATH,
        labels: Sequence[str] = tuple(ReliabilityPipeline.LABELS),
    ) -> None:
        self.store = store
        self.analyzer = analyzer
        self.feedback_pool_path = Path(feedback_pool_path)
        self.metadata_path = Path(metadata_path)
        self.labels = tuple(labels)

    def plan(
        self,
        *,
        name: str,
        per_category: int,
        seed: int,
        runtime_mode: str,
    ) -> dict[str, object]:
        if not name.strip():
            raise ValueError("campaign name must not be empty")
        if per_category <= 0:
            raise ValueError("per-category count must be positive")
        rows, dataset_fingerprint = self._load_feedback_pool()
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            grouped[str(row["category"])].append(row)

        selected: list[dict[str, object]] = []
        for category in self.labels:
            candidates = list(grouped.get(category, []))
            random.Random(f"{seed}:{category}:campaign").shuffle(candidates)
            if len(candidates) < per_category:
                raise ValueError(
                    f"feedback pool has {len(candidates)} rows for {category}; "
                    f"requested {per_category}"
                )
            selected.extend(candidates[:per_category])
        random.Random(f"{seed}:campaign-order").shuffle(selected)

        config = {
            "name": name.strip(),
            "source_split": "feedback_pool",
            "dataset_fingerprint": dataset_fingerprint,
            "seed": seed,
            "per_category": per_category,
            "runtime_mode": runtime_mode.upper(),
            "labels": list(self.labels),
        }
        campaign_id = f"cmp_{_fingerprint(config)[:16]}"
        items = []
        for row in selected:
            source_product_id = str(row["ean"])
            item_id = f"cmi_{_fingerprint([campaign_id, source_product_id])[:20]}"
            source_row = {
                key: row.get(key)
                for key in (
                    "ean",
                    "locale",
                    "title",
                    "description",
                    "category",
                    "colour",
                    "manufacturer",
                    "material",
                    "size",
                )
            }
            items.append(
                {
                    "id": item_id,
                    "source_product_id": source_product_id,
                    "reference_category": str(row["category"]),
                    "source_row": source_row,
                }
            )
        return {
            "campaign_id": campaign_id,
            "config": config,
            "selected_count": len(items),
            "category_counts": {
                category: per_category for category in self.labels
            },
            "items": items,
        }

    def create(
        self,
        *,
        name: str,
        per_category: int,
        seed: int,
        runtime_mode: str,
    ) -> dict[str, object]:
        plan = self.plan(
            name=name,
            per_category=per_category,
            seed=seed,
            runtime_mode=runtime_mode,
        )
        config = plan["config"]
        assert isinstance(config, dict)
        items = plan["items"]
        assert isinstance(items, list)
        return self._require_store().create_review_campaign(
            campaign_id=str(plan["campaign_id"]),
            name=name.strip(),
            source_split="feedback_pool",
            dataset_fingerprint=str(config["dataset_fingerprint"]),
            seed=seed,
            per_category=per_category,
            runtime_mode=runtime_mode.upper(),
            config=config,
            items=items,
        )

    def run(
        self,
        campaign_id: str,
        *,
        limit: int,
        retry_failed: bool = False,
        recover_processing: bool = False,
        progress: Callable[[int, int, str], None] | None = None,
    ) -> dict[str, object]:
        if self.analyzer is None:
            raise RuntimeError("campaign execution requires a catalog analyzer")
        store = self._require_store()
        campaign = store.get_review_campaign(campaign_id)
        if campaign is None:
            raise KeyError(f"review campaign not found: {campaign_id}")
        recovered_count = 0
        if recover_processing:
            recovered_count = store.recover_processing_review_campaign_items(
                campaign_id
            )
        items = store.claim_review_campaign_items(
            campaign_id,
            limit=limit,
            retry_failed=retry_failed,
        )
        succeeded = 0
        failed = 0
        for index, item in enumerate(items, start=1):
            source = item["source_row"]
            assert isinstance(source, dict)
            if progress:
                progress(index, len(items), str(item["source_product_id"]))
            try:
                title, description = bound_product_text(
                    title=str(source.get("title") or ""),
                    description=str(source.get("description") or ""),
                )
                decision = self.analyzer.analyze(
                    ListingInput(
                        external_id=(
                            f"campaign:{campaign_id}:"
                            f"{item['source_product_id']}"
                        ),
                        title=title,
                        description=description,
                    )
                )
                workflow = store.get_workflow_run(
                    str(decision.workflow_run_id)
                )
                if workflow is None or workflow.prediction_id is None:
                    raise RuntimeError("campaign workflow has no prediction")
                review_task_id = decision.review_task_id
                selection_type = "policy_triggered"
                if review_task_id is None:
                    task = store.create_review_task_for_workflow(
                        workflow.id,
                        listing_id=decision.listing_id,
                        prediction_id=workflow.prediction_id,
                        reason="campaign_control",
                        risk_level=decision.risk_level,
                    )
                    review_task_id = task.id
                    selection_type = (
                        "control_auto_accept"
                        if decision.decision == "auto_accept"
                        else "control_forced_review"
                    )
                store.complete_review_campaign_item(
                    str(item["id"]),
                    listing_id=decision.listing_id,
                    prediction_id=workflow.prediction_id,
                    workflow_run_id=workflow.id,
                    review_task_id=review_task_id,
                    natural_decision=decision.decision,
                    selection_type=selection_type,
                )
                succeeded += 1
            except Exception as exc:
                store.fail_review_campaign_item(
                    str(item["id"]),
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
                failed += 1
        status = store.review_campaign_status(campaign_id)
        status["processed_this_run"] = len(items)
        status["succeeded_this_run"] = succeeded
        status["failed_this_run"] = failed
        status["recovered_processing_count"] = recovered_count
        return status

    def status(self, campaign_id: str) -> dict[str, object]:
        return self._require_store().review_campaign_status(campaign_id)

    def report(
        self,
        campaign_id: str,
        *,
        minimum_resolved: int = 100,
        minimum_eligible: int = 80,
        minimum_corrections: int = 10,
        minimum_per_category: int = 10,
    ) -> dict[str, object]:
        store = self._require_store()
        status = store.review_campaign_status(campaign_id)
        rows = store.list_review_campaign_report_rows(campaign_id)
        action_counts: Counter[str] = Counter()
        selection_counts: Counter[str] = Counter()
        final_category_counts: Counter[str] = Counter()
        review_reason_counts: Counter[str] = Counter()
        model_reviewer_matches = 0
        model_reference_matches = 0
        reviewer_reference_matches = 0
        model_comparable = 0
        reviewer_comparable = 0
        three_way_comparable = 0
        degraded_count = 0
        fallback_count = 0

        for row in rows:
            if row.get("selection_type"):
                selection_counts[str(row["selection_type"])] += 1
            review_status = row.get("review_status")
            if review_status not in {"approved", "corrected", "rejected"}:
                continue
            action = {
                "approved": "approve",
                "corrected": "correct",
                "rejected": "reject",
            }[str(review_status)]
            action_counts[action] += 1
            review_reason_counts[str(row.get("review_reason") or "unknown")] += 1
            categories = json.loads(row["category_set_json"] or "[]")
            reliability = json.loads(row["reliability_json"] or "{}")
            model_category = categories[0] if categories else None
            reviewer_category = None
            if review_status == "approved" and len(categories) == 1:
                reviewer_category = categories[0]
            elif review_status == "corrected":
                reviewer_category = row.get("corrected_category")
            reference_category = row["reference_category"]
            if model_category is not None:
                model_comparable += 1
                model_reference_matches += int(
                    model_category == reference_category
                )
            if reviewer_category is not None:
                reviewer_comparable += 1
                final_category_counts[str(reviewer_category)] += 1
                reviewer_reference_matches += int(
                    reviewer_category == reference_category
                )
            if model_category is not None and reviewer_category is not None:
                three_way_comparable += 1
                model_reviewer_matches += int(
                    model_category == reviewer_category
                )
            degraded_count += int(
                reliability.get("semantic_consistency_status") == "degraded"
            )
            fallback_count += int(
                reliability.get("llm_runtime") == "FALLBACK_MOCK"
            )

        resolved_count = sum(action_counts.values())
        eligible_count = sum(final_category_counts.values())
        correction_count = action_counts["correct"]
        item_states = status["item_state_counts"]
        assert isinstance(item_states, dict)
        no_processing_failures = (
            int(item_states.get("failed", 0)) == 0
            and int(item_states.get("selected", 0)) == 0
            and int(item_states.get("processing", 0)) == 0
        )
        category_ready = all(
            final_category_counts[label] >= minimum_per_category
            for label in self.labels
        )
        ready = (
            resolved_count >= minimum_resolved
            and eligible_count >= minimum_eligible
            and correction_count >= minimum_corrections
            and category_ready
            and no_processing_failures
        )

        def rate(numerator: int, denominator: int) -> float:
            return round(numerator / denominator, 3) if denominator else 0.0

        return {
            "campaign_id": campaign_id,
            "campaign_status": status["status"],
            "selected_count": status["selected_count"],
            "resolved_count": resolved_count,
            "training_eligible_count": eligible_count,
            "action_counts": dict(sorted(action_counts.items())),
            "selection_type_counts": dict(sorted(selection_counts.items())),
            "review_reason_counts": dict(sorted(review_reason_counts.items())),
            "final_category_counts": {
                label: final_category_counts[label] for label in self.labels
            },
            "correction_rate": rate(correction_count, eligible_count),
            "model_reviewer_agreement": rate(
                model_reviewer_matches,
                three_way_comparable,
            ),
            "model_reference_agreement": rate(
                model_reference_matches,
                model_comparable,
            ),
            "reviewer_reference_agreement": rate(
                reviewer_reference_matches,
                reviewer_comparable,
            ),
            "semantic_degraded_rate": rate(degraded_count, resolved_count),
            "llm_fallback_rate": rate(fallback_count, resolved_count),
            "readiness": {
                "ready_for_retraining": ready,
                "minimum_resolved": minimum_resolved,
                "minimum_eligible": minimum_eligible,
                "minimum_corrections": minimum_corrections,
                "minimum_per_category": minimum_per_category,
                "category_coverage_ready": category_ready,
                "processing_complete": no_processing_failures,
            },
        }

    def _load_feedback_pool(self) -> tuple[list[dict[str, object]], str]:
        rows = json.loads(self.feedback_pool_path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError("feedback pool must contain a JSON list")
        dataset_fingerprint = _fingerprint(rows)
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        expected = metadata.get("split_fingerprints_sha256", {}).get(
            "feedback_pool"
        )
        if expected and expected != dataset_fingerprint:
            raise ValueError("feedback pool fingerprint does not match metadata")
        seen: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("feedback pool contains a non-object row")
            source_id = str(row.get("ean") or "")
            category = str(row.get("category") or "")
            if not source_id or not row.get("title") or category not in self.labels:
                raise ValueError("feedback pool contains an invalid row")
            if source_id in seen:
                raise ValueError(f"duplicate feedback source id: {source_id}")
            seen.add(source_id)
        return rows, dataset_fingerprint

    def _require_store(self) -> SQLiteReviewStore:
        if self.store is None:
            raise RuntimeError("campaign operation requires a persistence store")
        return self.store
