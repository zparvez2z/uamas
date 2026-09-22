#!/usr/bin/env python3
"""Bootstrap UAMAS in Colab and run the fixed extraction benchmark."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_URL = os.getenv("UAMAS_REPO_URL", "https://github.com/zparvez2z/uamas.git")
REPO_REF = os.getenv("UAMAS_REPO_REF", "main")
PROJECT_DIR = Path(os.getenv("UAMAS_COLAB_PROJECT_DIR", "/content/uamas"))
OUTPUT = Path(os.getenv("UAMAS_BENCHMARK_OUTPUT", "/content/uamas-output/attribute-benchmark.json"))


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print(f"[COLAB] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main() -> int:
    if not (PROJECT_DIR / ".git").exists():
        run(["git", "clone", REPO_URL, str(PROJECT_DIR)])
    run(["git", "fetch", "origin", REPO_REF], cwd=PROJECT_DIR)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=PROJECT_DIR)
    run([sys.executable, "-m", "pip", "install", "-r", "requirements-colab.txt"], cwd=PROJECT_DIR)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        ATTRIBUTE_PROVIDER="huggingface_local",
        ENABLE_SEMANTIC_SCORER="true",
        SEMANTIC_PROVIDER="sentence_transformers",
    )
    run(
        [
            sys.executable,
            "scripts/benchmark_attribute_extraction.py",
            "--output",
            str(OUTPUT),
        ],
        cwd=PROJECT_DIR,
        env=env,
    )
    print(f"[COLAB] benchmark artifact: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
