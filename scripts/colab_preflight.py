#!/usr/bin/env python3
"""Bootstrap the repository in Colab and run the local-model preflight."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_URL = os.getenv("UAMAS_REPO_URL", "https://github.com/zparvez2z/uamas.git")
REPO_REF = os.getenv("UAMAS_REPO_REF", "main")
PROJECT_DIR = Path(os.getenv("UAMAS_COLAB_PROJECT_DIR", "/content/uamas"))


def run(command: list[str], *, cwd: Path | None = None) -> None:
    print(f"[COLAB] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def bootstrap() -> None:
    if not (PROJECT_DIR / ".git").exists():
        run(["git", "clone", REPO_URL, str(PROJECT_DIR)])
    run(["git", "fetch", "origin", REPO_REF], cwd=PROJECT_DIR)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=PROJECT_DIR)
    run([sys.executable, "-m", "pip", "install", "-r", "requirements-colab.txt"], cwd=PROJECT_DIR)


def main() -> int:
    bootstrap()
    env = os.environ.copy()
    env.update(
        ATTRIBUTE_PROVIDER="huggingface_local",
        ENABLE_SEMANTIC_SCORER="true",
        SEMANTIC_PROVIDER="sentence_transformers",
    )
    subprocess.run(
        [sys.executable, "scripts/model_runtime_preflight.py"],
        cwd=PROJECT_DIR,
        env=env,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
