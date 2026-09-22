#!/usr/bin/env python3
"""Create a consistent SQLite snapshot inside a Colab runtime."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    source = Path(os.getenv("UAMAS_CAMPAIGN_DB", "/content/uamas-qwen-campaign.db"))
    output_dir = Path(os.getenv("UAMAS_OUTPUT_DIR", "/content/uamas-output"))
    if not source.exists():
        raise FileNotFoundError(f"campaign database not found: {source}")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = output_dir / f"uamas-qwen-campaign-{stamp}.db"
    with sqlite3.connect(source) as source_db, sqlite3.connect(destination) as backup_db:
        source_db.backup(backup_db)
    destination.chmod(0o600)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
