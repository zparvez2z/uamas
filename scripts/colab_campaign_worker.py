#!/usr/bin/env python3
"""Run one strict, resumable UAMAS campaign operation in a Colab session."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_URL = os.getenv("UAMAS_REPO_URL", "https://github.com/zparvez2z/uamas.git")
REPO_REF = os.getenv("UAMAS_REPO_REF", "main")
PROJECT_DIR = Path(os.getenv("UAMAS_COLAB_PROJECT_DIR", "/content/uamas"))
DB_PATH = Path(os.getenv("UAMAS_CAMPAIGN_DB", "/content/uamas-qwen-campaign.db"))
OUTPUT_DIR = Path(os.getenv("UAMAS_OUTPUT_DIR", "/content/uamas-output"))


def run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    print(f"[COLAB] {' '.join(command)}", flush=True)
    return subprocess.run(
        command,
        cwd=PROJECT_DIR,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )


def main() -> int:
    action = os.getenv("UAMAS_CAMPAIGN_ACTION", "status").lower()
    campaign_id = os.getenv("UAMAS_CAMPAIGN_ID", "")
    if not (PROJECT_DIR / ".git").exists():
        subprocess.run(["git", "clone", REPO_URL, str(PROJECT_DIR)], check=True)
    subprocess.run(["git", "fetch", "origin", REPO_REF], cwd=PROJECT_DIR, check=True)
    subprocess.run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=PROJECT_DIR, check=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements-colab.txt"],
        cwd=PROJECT_DIR,
        check=True,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        ATTRIBUTE_PROVIDER="huggingface_local",
        ENABLE_SEMANTIC_SCORER="true",
        SEMANTIC_PROVIDER="sentence_transformers",
        UAMAS_DB_PATH=str(DB_PATH),
    )
    base = [sys.executable, "scripts/review_campaign.py", "--db-path", str(DB_PATH)]
    if action == "create":
        command = base + [
            "create",
            "--name",
            os.getenv("UAMAS_CAMPAIGN_NAME", "qwen35-real-review-v1"),
            "--per-category",
            os.getenv("UAMAS_CAMPAIGN_PER_CATEGORY", "20"),
            "--seed",
            os.getenv("UAMAS_CAMPAIGN_SEED", "42"),
        ]
    elif action == "run":
        if not campaign_id:
            raise ValueError("UAMAS_CAMPAIGN_ID is required for run")
        command = base + [
            "run",
            campaign_id,
            "--limit",
            os.getenv("UAMAS_CAMPAIGN_BATCH_SIZE", "20"),
            "--require-runtime",
            "LOCAL_HF",
            "--abort-on-degraded",
            "--max-consecutive-failures",
            "1",
        ]
    elif action in {"status", "report"}:
        if not campaign_id:
            raise ValueError(f"UAMAS_CAMPAIGN_ID is required for {action}")
        command = base + [action, campaign_id]
    else:
        raise ValueError("UAMAS_CAMPAIGN_ACTION must be create, run, status, or report")

    completed = run(command, env=env)
    print(completed.stderr, file=sys.stderr, end="")
    print(completed.stdout, end="")
    result = json.loads(completed.stdout)
    (OUTPUT_DIR / "campaign-last.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if DB_PATH.exists():
        snapshot_env = env | {
            "UAMAS_CAMPAIGN_DB": str(DB_PATH),
            "UAMAS_OUTPUT_DIR": str(OUTPUT_DIR),
        }
        subprocess.run(
            [sys.executable, "scripts/colab_snapshot.py"],
            cwd=PROJECT_DIR,
            env=snapshot_env,
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
