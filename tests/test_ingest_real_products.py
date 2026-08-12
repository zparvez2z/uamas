import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from reliable_genai.models import (
    PRODUCT_DESCRIPTION_MAX_LENGTH,
    PRODUCT_TITLE_MAX_LENGTH,
)
from scripts import ingest_real_products as ingest


class FakeImageFeature:
    pass


class FakeTextFeature:
    pass


class FakeStreamingDataset:
    def __init__(self) -> None:
        self.features = {
            "product_image": FakeImageFeature(),
            "product_title": FakeTextFeature(),
        }
        self.removed_columns: list[str] = []

    def remove_columns(self, columns):
        self.removed_columns.extend(columns)
        return self

    def __iter__(self):
        yield {
            "product_image": {"path": "ignored.jpg"},
            "product_title": "Running Shoes",
            "ground_truth_category": "Shoes",
        }


def test_map_category_maps_common_taxonomy_paths() -> None:
    assert ingest.map_category("Apparel & Accessories > Shoes") == "Shoes"
    assert ingest.map_category("Apparel & Accessories > Clothing") == "Clothing"
    assert ingest.map_category("Electronics > Audio") == "Electronics"
    assert ingest.map_category("Home & Garden > Kitchen") == "Home"
    assert ingest.map_category("Health & Beauty > Skincare") == "Beauty"
    assert ingest.map_category("Sporting Goods > Fitness") == "Sports"
    assert ingest.map_category("Books") is None


def test_normalize_source_row_extracts_current_pipeline_contract() -> None:
    row = {
        "product_title": "Trail Running Shoes",
        "product_description": "Lightweight outdoor footwear",
        "ground_truth_category": "Apparel & Accessories > Shoes",
        "ground_truth_brand": "Acme",
        "color": "Black",
        "product_image": "https://example.com/shoe.jpg",
    }

    normalized, reason = ingest.normalize_source_row(row, 7)

    assert reason is None
    assert normalized is not None
    assert normalized["ean"] == "REAL00000007"
    assert normalized["title"] == "Trail Running Shoes"
    assert normalized["description"] == "Lightweight outdoor footwear"
    assert normalized["category"] == "Shoes"
    assert normalized["manufacturer"] == "Acme"
    assert normalized["colour"] == "Black"
    assert normalized["picture"] == "https://example.com/shoe.jpg"


def test_normalize_source_row_bounds_oversized_product_text() -> None:
    normalized, reason = ingest.normalize_source_row(
        {
            "product_title": "T" * (PRODUCT_TITLE_MAX_LENGTH + 10),
            "product_description": (
                "D" * (PRODUCT_DESCRIPTION_MAX_LENGTH + 10)
            ),
            "ground_truth_category": "Shoes",
        },
        1,
    )

    assert reason is None
    assert normalized is not None
    assert len(normalized["title"]) == PRODUCT_TITLE_MAX_LENGTH
    assert (
        len(normalized["description"])
        == PRODUCT_DESCRIPTION_MAX_LENGTH
    )


def test_normalize_rows_filters_unmapped_and_caps_categories() -> None:
    source_rows = [
        {"title": "Running Shoes", "description": "", "category": "Shoes"},
        {"title": "Trail Boots", "description": "", "category": "Footwear"},
        {"title": "Mystery Novel", "description": "", "category": "Books"},
        {"title": "", "description": "", "category": "Electronics"},
    ]

    result = ingest.normalize_rows(source_rows, sample_size=10, max_per_category=1)

    assert [row["title"] for row in result.rows] == ["Running Shoes"]
    assert result.metadata["skipped_counts"] == {
        "category_cap": 1,
        "missing_title": 1,
        "unmapped_category": 1,
    }
    assert result.metadata["category_counts"] == {"Shoes": 1}


def test_normalize_rows_zero_caps_mean_unlimited() -> None:
    source_rows = [
        {"title": "Running Shoes", "description": "", "category": "Shoes"},
        {"title": "Trail Boots", "description": "", "category": "Footwear"},
    ]

    result = ingest.normalize_rows(source_rows, sample_size=0, max_per_category=0)

    assert [row["title"] for row in result.rows] == ["Running Shoes", "Trail Boots"]
    assert result.metadata["skipped_counts"] == {}
    assert result.metadata["category_counts"] == {"Shoes": 2}


def test_ingest_real_products_local_cli_writes_splits_and_metadata(tmp_path: Path) -> None:
    input_path = tmp_path / "products.json"
    output_dir = tmp_path / "processed"
    rows = [
        {"product_title": "Running Shoes", "product_description": "cushioned footwear", "ground_truth_category": "Shoes"},
        {"product_title": "Trail Boots", "product_description": "outdoor footwear", "ground_truth_category": "Footwear"},
        {"product_title": "Cotton Shirt", "product_description": "casual apparel", "ground_truth_category": "Clothing"},
        {"product_title": "Denim Jacket", "product_description": "apparel layer", "ground_truth_category": "Apparel"},
        {"product_title": "Bluetooth Speaker", "product_description": "portable audio", "ground_truth_category": "Electronics"},
        {"product_title": "Phone Charger", "product_description": "usb electronic", "ground_truth_category": "Electronics"},
        {"product_title": "Kitchen Lamp", "product_description": "home lighting", "ground_truth_category": "Home & Garden"},
        {"product_title": "Storage Box", "product_description": "household storage", "ground_truth_category": "Home"},
        {"product_title": "Face Serum", "product_description": "skincare formula", "ground_truth_category": "Beauty"},
        {"product_title": "Mascara", "product_description": "cosmetics", "ground_truth_category": "Cosmetics"},
        {"product_title": "Yoga Mat", "product_description": "fitness gear", "ground_truth_category": "Sports"},
        {"product_title": "Cycling Jersey", "product_description": "athletic wear", "ground_truth_category": "Sporting Goods"},
    ]
    input_path.write_text(json.dumps(rows), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/ingest_real_products.py",
            "--source",
            "local",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--sample-size",
            "12",
            "--max-per-category",
            "3",
            "--max-source-rows",
            "20",
            "--seed",
            "7",
        ],
        check=True,
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )

    train = json.loads((output_dir / "train.json").read_text(encoding="utf-8"))
    calibration = json.loads((output_dir / "calibration.json").read_text(encoding="utf-8"))
    test = json.loads((output_dir / "test.json").read_text(encoding="utf-8"))
    feedback_pool = json.loads(
        (output_dir / "feedback_pool.json").read_text(encoding="utf-8")
    )
    metadata = json.loads((output_dir / "dataset_metadata.json").read_text(encoding="utf-8"))

    assert "Normalized rows: 12" in completed.stdout
    assert len(train) + len(calibration) + len(test) + len(feedback_pool) == 12
    assert metadata["source"] == f"local:{input_path}"
    assert metadata["split_seed"] == 7
    assert metadata["mapping_version"] == 2
    assert metadata["normalized_rows"] == 12
    assert metadata["split_counts"] == {
        "train": len(train),
        "calibration": len(calibration),
        "test": len(test),
        "feedback_pool": len(feedback_pool),
    }
    assert metadata["split_id_field"] == "ean"
    assert set(metadata["split_fingerprints_sha256"]) == {
        "train",
        "calibration",
        "test",
        "feedback_pool",
    }
    assert sorted(metadata["category_counts"]) == sorted(ingest.TARGET_LABELS)


def test_feedback_pool_partition_is_balanced_deterministic_and_disjoint() -> None:
    from scripts.load_dataset import partition_feedback_pool, validate_disjoint_splits

    test_rows = [
        {
            "ean": f"{category}-{index}",
            "title": f"{category} {index}",
            "category": category,
        }
        for category in ingest.TARGET_LABELS
        for index in range(5)
    ]

    first = partition_feedback_pool(
        {"train": [], "calibration": [], "test": test_rows},
        per_category=2,
        seed=17,
    )
    second = partition_feedback_pool(
        {"train": [], "calibration": [], "test": test_rows},
        per_category=2,
        seed=17,
    )

    assert first == second
    assert len(first["feedback_pool"]) == 12
    assert len(first["test"]) == 18
    assert Counter(row["category"] for row in first["feedback_pool"]) == {
        category: 2 for category in ingest.TARGET_LABELS
    }
    validate_disjoint_splits(first)


def test_committed_processed_splits_are_disjoint_and_fingerprinted() -> None:
    from scripts.load_dataset import split_fingerprint, validate_disjoint_splits

    processed_dir = Path(__file__).parent.parent / "data" / "processed"
    split_names = ("train", "calibration", "test", "feedback_pool")
    splits = {
        name: json.loads(
            (processed_dir / f"{name}.json").read_text(encoding="utf-8")
        )
        for name in split_names
    }
    metadata = json.loads(
        (processed_dir / "dataset_metadata.json").read_text(encoding="utf-8")
    )

    validate_disjoint_splits(splits)
    assert metadata["split_counts"] == {
        name: len(rows) for name, rows in splits.items()
    }
    assert metadata["split_fingerprints_sha256"] == {
        name: split_fingerprint(rows) for name, rows in splits.items()
    }
    assert Counter(row["category"] for row in splits["feedback_pool"]) == {
        category: 20 for category in ingest.TARGET_LABELS
    }


def test_load_shopify_rows_drops_image_columns(monkeypatch) -> None:
    fake_dataset = FakeStreamingDataset()

    def fake_load_dataset(name, split, streaming):
        assert name == "Shopify/product-catalogue"
        assert split == "train"
        assert streaming is True
        return fake_dataset

    class FakeDatasetsModule:
        load_dataset = staticmethod(fake_load_dataset)

    monkeypatch.setitem(sys.modules, "datasets", FakeDatasetsModule)

    rows = ingest.load_shopify_rows("train", max_source_rows=1)

    assert rows[0]["product_title"] == "Running Shoes"
    assert fake_dataset.removed_columns == ["product_image"]


def test_load_shopify_api_rows_paginates_without_network(monkeypatch) -> None:
    calls = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeRequests:
        @staticmethod
        def get(url, params, timeout):
            calls.append(params.copy())
            offset = params["offset"]
            rows = [
                {"row": {"product_title": f"Product {index}", "ground_truth_category": "Electronics"}}
                for index in range(offset, min(offset + params["length"], 3))
            ]
            return FakeResponse({"num_rows_total": 3, "rows": rows})

    monkeypatch.setitem(sys.modules, "requests", FakeRequests)
    monkeypatch.setattr(ingest.time, "sleep", lambda _: None)

    rows = ingest.load_shopify_api_rows("train", max_source_rows=0, page_size=2)

    assert [row["product_title"] for row in rows] == ["Product 0", "Product 1", "Product 2"]
    assert [call["offset"] for call in calls] == [0, 2]


def test_load_local_rows_reads_projected_parquet_columns(tmp_path: Path) -> None:
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")

    input_path = tmp_path / "products.parquet"
    table = pa.table(
        {
            "product_title": ["Running Shoes"],
            "product_description": ["cushioned footwear"],
            "ground_truth_category": ["Shoes"],
            "product_image": [{"bytes": b"heavy-unused-image"}],
            "ignored_column": ["not needed"],
        }
    )
    pq.write_table(table, input_path)

    rows = ingest.load_local_rows(input_path)

    assert rows == [
        {
            "product_title": "Running Shoes",
            "product_description": "cushioned footwear",
            "ground_truth_category": "Shoes",
        }
    ]
