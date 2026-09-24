from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from reliable_genai.models import ReviewDecision, ReviewQueueItem
from reliable_genai.persistence import SQLiteReviewStore


SCHEMA_VERSION = "1.0"


def export_blind_packet(
    store: SQLiteReviewStore,
    campaign_id: str,
) -> dict[str, object]:
    tasks = store.list_review_tasks(
        status="pending",
        campaign_id=campaign_id,
        limit=100_000,
    )
    items = [_blind_item(task) for task in sorted(tasks, key=lambda item: item.id)]
    packet: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "campaign_id": campaign_id,
        "reviewer_instructions": {
            "allowed_actions": ["approve", "correct", "reject"],
            "categories": [
                "Beauty",
                "Clothing",
                "Electronics",
                "Home",
                "Shoes",
                "Sports",
            ],
            "approve_requires_singleton_prediction": True,
            "confidence_range": [0.0, 1.0],
        },
        "items": items,
    }
    serialized = json.dumps(packet, sort_keys=True)
    if "reference_category" in serialized:
        raise RuntimeError("blind review export contains a reference label")
    return packet


def validate_decision_packet(
    store: SQLiteReviewStore,
    payload: dict[str, Any],
    *,
    campaign_id: str,
    allow_partial: bool = False,
) -> list[tuple[str, ReviewDecision]]:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported decision schema_version")
    if payload.get("campaign_id") != campaign_id:
        raise ValueError("decision packet campaign_id does not match")
    reviewer = payload.get("reviewer")
    if not isinstance(reviewer, dict):
        raise ValueError("decision packet requires reviewer metadata")
    reviewer_id = str(reviewer.get("id") or "").strip()
    if not reviewer_id:
        raise ValueError("AI-assisted decisions require reviewer.id")
    raw_decisions = payload.get("decisions")
    if not isinstance(raw_decisions, list):
        raise ValueError("decision packet requires a decisions list")

    pending = store.list_review_tasks(
        status="pending",
        campaign_id=campaign_id,
        limit=100_000,
    )
    pending_by_id = {task.id: task for task in pending}
    seen: set[str] = set()
    decisions: list[tuple[str, ReviewDecision]] = []
    for index, raw in enumerate(raw_decisions):
        if not isinstance(raw, dict):
            raise ValueError(f"decision {index} must be an object")
        task_id = str(raw.get("task_id") or "")
        if task_id in seen:
            raise ValueError(f"duplicate task_id: {task_id}")
        if task_id not in pending_by_id:
            raise ValueError(f"task is not pending in campaign: {task_id}")
        seen.add(task_id)
        notes = str(raw.get("notes") or "").strip()
        if not notes:
            raise ValueError(f"decision requires rationale notes: {task_id}")
        if raw.get("confidence") is None:
            raise ValueError(f"decision requires confidence: {task_id}")
        decision = ReviewDecision(
            action=raw.get("action"),
            corrected_category=raw.get("corrected_category"),
            corrected_attributes=raw.get("corrected_attributes") or {},
            notes=notes,
            reviewer_type="ai_assisted",
            reviewer_id=reviewer_id,
            reviewer_confidence=raw.get("confidence"),
        )
        task = pending_by_id[task_id]
        if decision.action == "approve":
            category_set = task.prediction.category_set if task.prediction else []
            if len(category_set) != 1:
                raise ValueError(
                    f"approval requires singleton prediction: {task_id}"
                )
        if decision.action == "correct" and not decision.corrected_category:
            raise ValueError(f"correction requires category: {task_id}")
        decisions.append((task_id, decision))

    missing = set(pending_by_id) - seen
    if missing and not allow_partial:
        raise ValueError(
            f"decision packet omits {len(missing)} pending campaign tasks"
        )
    return decisions


def apply_decision_packet(
    store: SQLiteReviewStore,
    payload: dict[str, Any],
    *,
    campaign_id: str,
    allow_partial: bool = False,
) -> dict[str, object]:
    decisions = validate_decision_packet(
        store,
        payload,
        campaign_id=campaign_id,
        allow_partial=allow_partial,
    )
    action_counts: dict[str, int] = {}
    for task_id, decision in decisions:
        store.record_review_decision(task_id, decision)
        action_counts[decision.action] = action_counts.get(decision.action, 0) + 1
    return {
        "campaign_id": campaign_id,
        "applied_count": len(decisions),
        "action_counts": dict(sorted(action_counts.items())),
        "reviewer_type": "ai_assisted",
    }


def _blind_item(task: ReviewQueueItem) -> dict[str, object]:
    prediction = task.prediction
    return {
        "task_id": task.id,
        "title": task.title,
        "description": task.description,
        "review_reason": task.reason,
        "risk_level": task.risk_level,
        "prediction": prediction.model_dump(mode="json") if prediction else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export blind campaign tasks and apply AI-assisted decisions."
    )
    parser.add_argument("--db-path", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("campaign_id")
    export_parser.add_argument("--output", type=Path, required=True)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("campaign_id")
    apply_parser.add_argument("--decisions", type=Path, required=True)
    apply_parser.add_argument("--allow-partial", action="store_true")
    apply_parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist decisions. Without this flag, only validate the packet.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    store = SQLiteReviewStore(args.db_path)
    if args.command == "export":
        result = export_blind_packet(store, args.campaign_id)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        summary = {
            "campaign_id": args.campaign_id,
            "output": str(args.output),
            "item_count": len(result["items"]),
            "blind": True,
        }
    else:
        payload = json.loads(args.decisions.read_text(encoding="utf-8"))
        decisions = validate_decision_packet(
            store,
            payload,
            campaign_id=args.campaign_id,
            allow_partial=args.allow_partial,
        )
        if args.apply:
            summary = apply_decision_packet(
                store,
                payload,
                campaign_id=args.campaign_id,
                allow_partial=args.allow_partial,
            )
        else:
            summary = {
                "campaign_id": args.campaign_id,
                "validated_count": len(decisions),
                "applied_count": 0,
                "reviewer_type": "ai_assisted",
            }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
