from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from reliable_genai.maintenance import OperationalDataCleaner, RetentionPolicy
from reliable_genai.persistence import SQLiteReviewStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prune expired detailed workflow history while preserving workflow "
            "summaries and human-review evidence."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply cleanup. Without this flag, the command is a dry run.",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Run SQLite VACUUM after applied cleanup.",
    )
    parser.add_argument(
        "--db-path",
        help="Override UAMAS_DB_PATH for this command.",
    )
    parser.add_argument(
        "--now",
        help="Use a timezone-aware ISO-8601 time for deterministic validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.vacuum and not args.apply:
        raise SystemExit("--vacuum requires --apply")
    now = datetime.fromisoformat(args.now) if args.now else None
    store = SQLiteReviewStore(args.db_path)
    cleaner = OperationalDataCleaner(store, RetentionPolicy.from_env())
    result = cleaner.run(
        dry_run=not args.apply,
        vacuum=args.vacuum,
        now=now,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
