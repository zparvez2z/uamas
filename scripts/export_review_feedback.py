from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from reliable_genai.feedback import FeedbackExporter
from reliable_genai.persistence import SQLiteReviewStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export resolved human reviews as validated, versioned feedback "
            "evidence and training examples."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write and register the export. Without this flag, only preview it.",
    )
    parser.add_argument(
        "--db-path",
        help="Override UAMAS_DB_PATH for this command.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/feedback",
        help="Export root directory (default: data/feedback).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exporter = FeedbackExporter(
        SQLiteReviewStore(args.db_path),
        output_root=args.output_dir,
    )
    result = exporter.run(apply=args.apply)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
