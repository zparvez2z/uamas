from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.load_dataset import (
    partition_feedback_pool,
    split_fingerprint,
    validate_disjoint_splits,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministically move a balanced subset of processed test data "
            "into a leakage-safe feedback pool."
        )
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed"),
    )
    parser.add_argument("--per-category", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write test.json, feedback_pool.json, and dataset metadata.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    test_path = args.processed_dir / "test.json"
    feedback_path = args.processed_dir / "feedback_pool.json"
    metadata_path = args.processed_dir / "dataset_metadata.json"
    test_rows = json.loads(test_path.read_text(encoding="utf-8"))
    if feedback_path.exists():
        test_rows.extend(json.loads(feedback_path.read_text(encoding="utf-8")))

    splits = partition_feedback_pool(
        {"test": test_rows},
        per_category=args.per_category,
        seed=args.seed,
    )
    validate_disjoint_splits(splits)
    preview = {
        "applied": args.apply,
        "seed": args.seed,
        "per_category": args.per_category,
        "test_count": len(splits["test"]),
        "feedback_pool_count": len(splits["feedback_pool"]),
        "feedback_category_counts": dict(
            sorted(Counter(row["category"] for row in splits["feedback_pool"]).items())
        ),
    }
    if args.apply:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        write_json(test_path, splits["test"])
        write_json(feedback_path, splits["feedback_pool"])
        metadata["mapping_version"] = 2
        metadata["feedback_pool_per_category"] = args.per_category
        metadata["split_counts"]["test"] = len(splits["test"])
        metadata["split_counts"]["feedback_pool"] = len(splits["feedback_pool"])
        fingerprints = metadata.setdefault("split_fingerprints_sha256", {})
        for split_name in ("test", "feedback_pool"):
            fingerprints[split_name] = split_fingerprint(splits[split_name])
        for split_name in ("train", "calibration"):
            path = args.processed_dir / f"{split_name}.json"
            fingerprints[split_name] = split_fingerprint(
                json.loads(path.read_text(encoding="utf-8"))
            )
        metadata["split_id_field"] = "ean"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(preview, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
