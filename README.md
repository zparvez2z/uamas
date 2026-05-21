# Reliable GenAI Demo

This repository contains a stakeholder-facing demo for reliable GenAI in product classification and structured extraction. The goal is to show clear uncertainty handling, validated outputs, and a practical path from research ideas to working code.

For implementation details, see [TECHNICAL.md](TECHNICAL.md).

## What the demo shows
- A FastAPI web app that accepts product title and description.
- A reliability pipeline that returns a category set, structured attributes, and confidence metadata.
- An uncertainty-aware policy that can answer, abstain, or escalate.
- A live GitHub Models integration for attribute extraction.
- A diagnostics view that shows runtime readiness before a demo.

## Why it is useful
- It demonstrates research-to-code translation.
- It shows uncertainty-aware GenAI behavior instead of forced single-label answers.
- It includes a visible UI for stakeholders.

## Quick start
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
USE_MOCK_LLM=false .venv/bin/python -m uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000

## Checks
```bash
.venv/bin/python scripts/train_classifier.py --force
.venv/bin/python -m pytest
USE_MOCK_LLM=true .venv/bin/python scripts/evaluate.py
```

## Environment
Required variables:
- `GITHUB_MODELS_ENDPOINT`
- `GITHUB_TOKEN`
- `GITHUB_MODELS_MODEL`

Useful runtime flags:
- `USE_MOCK_LLM`
- `ALPHA`
- `MAX_SET_SIZE`
- `LLM_MAX_RETRIES`
- `ENABLE_ABSTAIN`

## Demo inputs
Use a clear case first, then an ambiguous one.

Example:
- Title: `Nike running shoes black size 42`
- Description: `Breathable mesh upper and cushioned sole`

## Repository contents
- `app/` web UI and API
- `reliable_genai/` reliability pipeline and model wrappers
- `scripts/` evaluation and data preparation entry points
- `reports/` experiment results

## Notes
- Public or synthetic data only.
- No internal Schwarz data is included.
