#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x .venv/bin/python ]]; then
  echo "Create the project .venv first (see README.md)." >&2
  exit 1
fi

if [[ ! -x .venv/bin/uv ]]; then
  .venv/bin/python -m pip install uv
fi

.venv/bin/uv venv --python 3.12 .colab-cli-venv
.venv/bin/uv pip install \
  --python .colab-cli-venv/bin/python \
  "google-colab-cli @ git+https://github.com/googlecolab/google-colab-cli.git@ddf8e3fcf1f7752411f9e139ab94ad276eb5403d"

.colab-cli-venv/bin/colab version
echo "Run 'source .colab-cli-venv/bin/activate', then 'colab sessions' to authorize."
