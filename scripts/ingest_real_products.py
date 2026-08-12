#!/usr/bin/env python3
"""Ingest real product data into disjoint UAMAS model and feedback splits."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.load_dataset import (
    SplitConfig,
    partition_feedback_pool,
    split_fingerprint,
    split_rows,
    validate_disjoint_splits,
    write_json,
)
from reliable_genai.models import bound_product_text


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
TARGET_LABELS = ("Shoes", "Clothing", "Electronics", "Home", "Beauty", "Sports")
PARQUET_COLUMN_CANDIDATES = (
    "product_title",
    "title",
    "name",
    "product_name",
    "product_description",
    "description",
    "body_html",
    "details",
    "ground_truth_category",
    "category",
    "product_category",
    "categories",
    "potential_product_categories",
    "ean",
    "locale",
    "colour",
    "color",
    "manufacturer",
    "brand",
    "ground_truth_brand",
    "vendor",
    "picture",
    "image_url",
    "material",
    "size",
)


CATEGORY_KEYWORDS = {
    "Shoes": ("shoe", "shoes", "sneaker", "sneakers", "boot", "boots", "footwear", "sandals"),
    "Clothing": ("clothing", "apparel", "shirt", "jacket", "pants", "dress", "jeans", "hoodie", "wear"),
    "Electronics": ("electronics", "electronic", "computer", "phone", "audio", "camera", "tv", "tablet"),
    "Home": ("home", "garden", "furniture", "kitchen", "decor", "household", "bedding", "lighting"),
    "Beauty": ("beauty", "health", "cosmetic", "cosmetics", "skincare", "makeup", "hair", "personal care"),
    "Sports": ("sport", "sports", "sporting", "fitness", "outdoor", "exercise", "athletic", "cycling"),
}


@dataclass(frozen=True)
class IngestionResult:
    rows: list[dict[str, str]]
    metadata: dict[str, Any]


def _first_present(row: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " > ".join(_stringify(item) for item in value if item not in (None, ""))
    if isinstance(value, dict):
        for key in ("name", "title", "label", "category"):
            if key in value:
                return _stringify(value[key])
        return " ".join(_stringify(item) for item in value.values() if item not in (None, ""))
    return str(value).strip()


def map_category(source_category: Any) -> str | None:
    text = _stringify(source_category).lower()
    if not text:
        return None
    for label, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return label
    return None


def normalize_source_row(row: dict[str, Any], index: int) -> tuple[dict[str, str] | None, str | None]:
    title = _stringify(
        _first_present(
            row,
            (
                "product_title",
                "title",
                "name",
                "product_name",
            ),
        )
    )
    description = _stringify(
        _first_present(
            row,
            (
                "product_description",
                "description",
                "body_html",
                "details",
            ),
        )
    )
    title, description = bound_product_text(
        title=title,
        description=description,
    )
    source_category = _first_present(
        row,
        (
            "ground_truth_category",
            "category",
            "product_category",
            "categories",
            "potential_product_categories",
        ),
    )
    category = map_category(source_category)
    if not title:
        return None, "missing_title"
    if category is None:
        return None, "unmapped_category"

    return (
        {
            "ean": _stringify(row.get("ean")) or f"REAL{index:08d}",
            "locale": _stringify(row.get("locale")) or "en-US",
            "title": title,
            "description": description,
            "category": category,
            "colour": _stringify(_first_present(row, ("colour", "color"))) or "unknown",
            "manufacturer": _stringify(_first_present(row, ("manufacturer", "brand", "ground_truth_brand", "vendor")))
            or "unknown",
            "picture": _stringify(_first_present(row, ("picture", "image", "image_url", "product_image"))),
            "material": _stringify(row.get("material")) or "unknown",
            "size": _stringify(row.get("size")) or "unknown",
        },
        None,
    )


def load_local_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"{path} must contain a JSON list")
        return [dict(row) for row in payload if isinstance(row, dict)]
    if suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    if isinstance(row, dict):
                        rows.append(row)
        return rows
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise RuntimeError("Local parquet ingestion requires pyarrow") from exc
        parquet_file = pq.ParquetFile(path)
        available_columns = set(parquet_file.schema_arrow.names)
        selected_columns = [column for column in PARQUET_COLUMN_CANDIDATES if column in available_columns]
        if not selected_columns:
            raise ValueError(f"{path} has no supported product text/category columns")
        return parquet_file.read(columns=selected_columns).to_pylist()
    raise ValueError(f"unsupported input format: {path.suffix}")


def load_shopify_rows(split: str, *, max_source_rows: int, drop_image_columns: bool = True) -> list[dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "Shopify ingestion requires the optional 'datasets' package. "
            "Install it or pass --source local --input <file>."
        ) from exc

    dataset = load_dataset("Shopify/product-catalogue", split=split, streaming=True)
    if drop_image_columns and getattr(dataset, "features", None):
        image_columns = [
            name
            for name, feature in dataset.features.items()
            if "image" in feature.__class__.__name__.lower()
        ]
        if image_columns:
            dataset = dataset.remove_columns(image_columns)
    rows = []
    for row in dataset:
        rows.append(dict(row))
        if len(rows) >= max_source_rows:
            break
    return rows


def load_shopify_api_rows(
    split: str,
    *,
    max_source_rows: int,
    page_size: int = 100,
    max_retries: int = 5,
    progress_every: int = 1000,
) -> list[dict[str, Any]]:
    import requests

    if page_size > 100:
        raise ValueError("Hugging Face rows API page size must be <= 100")

    splits = ("train", "test") if split == "all" else (split,)
    rows: list[dict[str, Any]] = []
    for split_name in splits:
        offset = 0
        total: int | None = None
        while total is None or offset < total:
            if max_source_rows > 0 and len(rows) >= max_source_rows:
                return rows
            length = page_size
            if max_source_rows > 0:
                length = min(length, max_source_rows - len(rows))
            params = {
                "dataset": "Shopify/product-catalogue",
                "config": "default",
                "split": split_name,
                "offset": offset,
                "length": length,
            }
            for attempt in range(max_retries + 1):
                try:
                    response = requests.get(
                        "https://datasets-server.huggingface.co/rows",
                        params=params,
                        timeout=30,
                    )
                    response.raise_for_status()
                    break
                except Exception:
                    if attempt >= max_retries:
                        raise
                    print(
                        f"[WARN] retrying {split_name} offset={offset} attempt={attempt + 1}/{max_retries}",
                        flush=True,
                    )
                    time.sleep(min(2**attempt, 10))
            payload = response.json()
            total = int(payload["num_rows_total"])
            batch = [dict(item["row"]) for item in payload.get("rows", [])]
            if not batch:
                break
            rows.extend(batch)
            offset += len(batch)
            if progress_every > 0 and (offset % progress_every == 0 or offset >= total):
                print(f"[INFO] fetched {split_name} offset={offset}/{total}", flush=True)
            time.sleep(0.05)
    return rows


def normalize_rows(source_rows: list[dict[str, Any]], *, sample_size: int, max_per_category: int) -> IngestionResult:
    normalized: list[dict[str, str]] = []
    skipped = Counter()
    category_counts = Counter()

    for index, row in enumerate(source_rows, start=1):
        normalized_row, reason = normalize_source_row(row, index)
        if reason:
            skipped[reason] += 1
            continue
        assert normalized_row is not None
        category = normalized_row["category"]
        if max_per_category > 0 and category_counts[category] >= max_per_category:
            skipped["category_cap"] += 1
            continue
        normalized.append(normalized_row)
        category_counts[category] += 1
        if sample_size > 0 and len(normalized) >= sample_size:
            break

    metadata = {
        "source_rows": len(source_rows),
        "normalized_rows": len(normalized),
        "skipped_counts": dict(sorted(skipped.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "target_labels": list(TARGET_LABELS),
    }
    return IngestionResult(rows=normalized, metadata=metadata)


def write_metadata(path: Path, *, source: str, split_seed: int, ingestion: IngestionResult, splits: dict[str, list[dict[str, str]]]) -> None:
    validate_disjoint_splits(splits)
    metadata = {
        "source": source,
        "source_url": "https://huggingface.co/datasets/Shopify/product-catalogue"
        if source in {"shopify_hf", "shopify_api"}
        else None,
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "split_seed": split_seed,
        "mapping_version": 2,
        **ingestion.metadata,
        "split_counts": {name: len(rows) for name, rows in splits.items()},
        "split_fingerprints_sha256": {
            name: split_fingerprint(rows) for name, rows in splits.items()
        },
        "split_id_field": "ean",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["shopify_api", "shopify_hf", "local"], default="shopify_api")
    parser.add_argument("--input", type=Path, default=None, help="Local JSON/JSONL/CSV export for --source local")
    parser.add_argument("--hf-split", default="all", help="Hugging Face split for Shopify source: train, test, or all")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sample-size", type=int, default=0, help="Mapped-row cap. Use 0 for no cap.")
    parser.add_argument("--max-per-category", type=int, default=0, help="Per-category cap. Use 0 for no cap.")
    parser.add_argument("--max-source-rows", type=int, default=0, help="Source-row cap. Use 0 for no cap.")
    parser.add_argument("--api-page-size", type=int, default=100)
    parser.add_argument("--api-max-retries", type=int, default=5)
    parser.add_argument("--api-progress-every", type=int, default=1000)
    parser.add_argument(
        "--keep-image-columns",
        action="store_true",
        help="Keep image columns when reading Hugging Face source. Default drops them for text-only ingestion.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--feedback-per-category",
        type=int,
        default=0,
        help="Move this many rows per category from test to feedback_pool.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.source == "local":
        if args.input is None:
            raise SystemExit("--input is required when --source local")
        source_rows = load_local_rows(args.input)
        source_name = f"local:{args.input}"
    elif args.source == "shopify_hf":
        source_rows = load_shopify_rows(
            args.hf_split,
            max_source_rows=args.max_source_rows,
            drop_image_columns=not args.keep_image_columns,
        )
        source_name = "shopify_hf"
    else:
        source_rows = load_shopify_api_rows(
            args.hf_split,
            max_source_rows=args.max_source_rows,
            page_size=args.api_page_size,
            max_retries=args.api_max_retries,
            progress_every=args.api_progress_every,
        )
        source_name = "shopify_api"

    ingestion = normalize_rows(
        source_rows,
        sample_size=args.sample_size,
        max_per_category=args.max_per_category,
    )
    if not ingestion.rows:
        raise SystemExit("No rows were mapped into the target taxonomy")

    splits = split_rows(ingestion.rows, SplitConfig(seed=args.seed))
    splits = partition_feedback_pool(
        splits,
        per_category=args.feedback_per_category,
        seed=args.seed,
    )
    write_json(args.output_dir / "train.json", splits["train"])
    write_json(args.output_dir / "calibration.json", splits["calibration"])
    write_json(args.output_dir / "test.json", splits["test"])
    write_json(args.output_dir / "feedback_pool.json", splits["feedback_pool"])
    write_metadata(
        args.output_dir / "dataset_metadata.json",
        source=source_name,
        split_seed=args.seed,
        ingestion=ingestion,
        splits=splits,
    )

    print(f"Source rows: {len(source_rows)}")
    print(f"Normalized rows: {len(ingestion.rows)}")
    print(f"Category counts: {ingestion.metadata['category_counts']}")
    print(
        "Split sizes: "
        f"train={len(splits['train'])}, "
        f"calibration={len(splits['calibration'])}, "
        f"test={len(splits['test'])}, "
        f"feedback_pool={len(splits['feedback_pool'])}"
    )


if __name__ == "__main__":
    main()
