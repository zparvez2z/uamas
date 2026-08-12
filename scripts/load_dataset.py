#!/usr/bin/env python3
"""Load a catalog CSV and split it into disjoint model and feedback sets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "products.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


REQUIRED_COLUMNS = {"ean", "locale", "title", "category"}


@dataclass(frozen=True)
class SplitConfig:
    train_ratio: float = 0.70
    calibration_ratio: float = 0.15
    test_ratio: float = 0.15
    seed: int = 42


def partition_feedback_pool(
    splits: dict[str, list[dict[str, str]]],
    *,
    per_category: int,
    seed: int,
) -> dict[str, list[dict[str, str]]]:
    if per_category < 0:
        raise ValueError("feedback pool size must not be negative")
    result = {name: list(rows) for name, rows in splits.items()}
    if per_category == 0:
        result["feedback_pool"] = []
        return result

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in result["test"]:
        grouped[row["category"]].append(row)

    selected_ids: set[str] = set()
    for category in sorted(grouped):
        category_rows = sorted(
            grouped[category],
            key=lambda row: str(row["ean"]),
        )
        random.Random(f"{seed}:{category}:feedback").shuffle(category_rows)
        if len(category_rows) <= per_category:
            raise ValueError(
                f"test split has {len(category_rows)} rows for {category}; "
                f"need more than {per_category} to preserve evaluation data"
            )
        selected_ids.update(
            str(row["ean"]) for row in category_rows[:per_category]
        )

    feedback_rows = [
        row for row in result["test"] if str(row["ean"]) in selected_ids
    ]
    remaining_test = [
        row for row in result["test"] if str(row["ean"]) not in selected_ids
    ]
    result["test"] = remaining_test
    result["feedback_pool"] = feedback_rows
    return result


def split_fingerprint(rows: list[dict[str, str]]) -> str:
    payload = json.dumps(
        rows,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_disjoint_splits(
    splits: dict[str, list[dict[str, str]]],
    *,
    id_field: str = "ean",
) -> None:
    ownership: dict[str, str] = {}
    for split_name, rows in splits.items():
        for row in rows:
            row_id = row.get(id_field)
            if not row_id:
                raise ValueError(f"{split_name} row is missing {id_field}")
            previous = ownership.get(row_id)
            if previous is not None:
                raise ValueError(
                    f"{id_field} {row_id} occurs in both {previous} and "
                    f"{split_name}"
                )
            ownership[row_id] = split_name


def load_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if reader.fieldnames is None:
            raise ValueError("CSV file is missing a header row")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV file is missing required columns: {sorted(missing)}")

        rows: list[dict[str, str]] = []
        for line_number, row in enumerate(reader, start=2):
            cleaned = {key: (value or "").strip() for key, value in row.items() if key}
            if not cleaned.get("title") or not cleaned.get("category"):
                raise ValueError(f"Row {line_number} is missing title or category")
            rows.append(cleaned)

    return rows


def split_rows(rows: list[dict[str, str]], config: SplitConfig) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["category"]].append(row)

    random.seed(config.seed)
    for category_rows in grouped.values():
        random.shuffle(category_rows)

    splits = {"train": [], "calibration": [], "test": []}
    for category_rows in grouped.values():
        total = len(category_rows)
        train_end = max(1, int(total * config.train_ratio))
        calibration_end = train_end + max(1, int(total * config.calibration_ratio))

        if calibration_end >= total:
            calibration_end = total - 1
        if train_end >= calibration_end:
            train_end = max(1, calibration_end - 1)

        splits["train"].extend(category_rows[:train_end])
        splits["calibration"].extend(category_rows[train_end:calibration_end])
        splits["test"].extend(category_rows[calibration_end:])

    random.seed(config.seed)
    for split_rows in splits.values():
        random.shuffle(split_rows)

    return splits


def write_json(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, ensure_ascii=False)


def write_metadata(path: Path, rows: list[dict[str, str]], splits: dict[str, list[dict[str, str]]]) -> None:
    validate_disjoint_splits(splits)
    metadata = {
        "total_rows": len(rows),
        "categories": sorted({row["category"] for row in rows}),
        "split_counts": {name: len(split_rows) for name, split_rows in splits.items()},
        "split_fingerprints_sha256": {
            name: split_fingerprint(split_rows)
            for name, split_rows in splits.items()
        },
        "split_id_field": "ean",
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to the source CSV file")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for split outputs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for shuffling")
    parser.add_argument(
        "--feedback-per-category",
        type=int,
        default=0,
        help="Move this many rows per category from test to feedback_pool.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.input)
    splits = split_rows(rows, SplitConfig(seed=args.seed))
    splits = partition_feedback_pool(
        splits,
        per_category=args.feedback_per_category,
        seed=args.seed,
    )

    write_json(args.output_dir / "train.json", splits["train"])
    write_json(args.output_dir / "calibration.json", splits["calibration"])
    write_json(args.output_dir / "test.json", splits["test"])
    write_json(args.output_dir / "feedback_pool.json", splits["feedback_pool"])
    write_metadata(args.output_dir / "dataset_metadata.json", rows, splits)

    print(f"Loaded {len(rows)} rows from {args.input}")
    print(
        "Split sizes: "
        f"train={len(splits['train'])}, "
        f"calibration={len(splits['calibration'])}, "
        f"test={len(splits['test'])}"
    )


if __name__ == "__main__":
    main()
