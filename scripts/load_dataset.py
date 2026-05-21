#!/usr/bin/env python3
"""Load a Kaufland-style CSV and split it into train/calibration/test sets."""

from __future__ import annotations

import argparse
import csv
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
    metadata = {
        "total_rows": len(rows),
        "categories": sorted({row["category"] for row in rows}),
        "split_counts": {name: len(split_rows) for name, split_rows in splits.items()},
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to the source CSV file")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for split outputs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for shuffling")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.input)
    splits = split_rows(rows, SplitConfig(seed=args.seed))

    write_json(args.output_dir / "train.json", splits["train"])
    write_json(args.output_dir / "calibration.json", splits["calibration"])
    write_json(args.output_dir / "test.json", splits["test"])
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