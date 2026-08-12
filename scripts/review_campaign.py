from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from reliable_genai.catalog_quality_graph import CatalogQualityGraph
from reliable_genai.persistence import SQLiteReviewStore
from reliable_genai.pipeline import ReliabilityPipeline
from reliable_genai.review_campaigns import ReviewCampaignService
from reliable_genai.review_graph import ReviewGraphRunner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan, execute, monitor, and report review campaigns."
    )
    parser.add_argument("--db-path")
    parser.add_argument(
        "--feedback-pool",
        type=Path,
        default=Path("data/processed/feedback_pool.json"),
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("data/processed/dataset_metadata.json"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("plan", "create"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--name", required=True)
        subparser.add_argument("--per-category", type=int, default=20)
        subparser.add_argument("--seed", type=int, default=42)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("campaign_id")
    run_parser.add_argument("--limit", type=int, default=20)
    run_parser.add_argument("--retry-failed", action="store_true")
    run_parser.add_argument(
        "--recover-processing",
        action="store_true",
        help=(
            "Mark items left processing by an interrupted runner as failed; "
            "combine with --retry-failed to process them now."
        ),
    )

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("campaign_id")

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("campaign_id")
    report_parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _service(args: argparse.Namespace, *, with_analyzer: bool) -> ReviewCampaignService:
    store = None if args.command == "plan" else SQLiteReviewStore(args.db_path)
    analyzer = None
    if with_analyzer:
        assert store is not None
        pipeline = ReliabilityPipeline()
        review_graph = ReviewGraphRunner(pipeline)
        analyzer = CatalogQualityGraph(pipeline, review_graph, store)
    return ReviewCampaignService(
        store,
        analyzer=analyzer,
        feedback_pool_path=args.feedback_pool,
        metadata_path=args.metadata,
    )


def main() -> int:
    load_dotenv()
    args = parse_args()
    runtime_mode = "MOCK" if os.getenv("USE_MOCK_LLM", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    } else "LIVE"
    service = _service(args, with_analyzer=args.command == "run")
    if args.command == "plan":
        result = service.plan(
            name=args.name,
            per_category=args.per_category,
            seed=args.seed,
            runtime_mode=runtime_mode,
        )
        result = {key: value for key, value in result.items() if key != "items"}
    elif args.command == "create":
        result = service.create(
            name=args.name,
            per_category=args.per_category,
            seed=args.seed,
            runtime_mode=runtime_mode,
        )
    elif args.command == "run":
        result = service.run(
            args.campaign_id,
            limit=args.limit,
            retry_failed=args.retry_failed,
            recover_processing=args.recover_processing,
            progress=lambda current, total, source_id: print(
                f"[INFO] processing {current}/{total} source={source_id}",
                file=sys.stderr,
                flush=True,
            ),
        )
    elif args.command == "status":
        result = service.status(args.campaign_id)
    else:
        result = service.report(args.campaign_id)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
