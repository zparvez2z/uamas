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
# Optional: explicitly train TF-IDF mode
.venv/bin/python scripts/train_classifier.py --force --model-type tfidf
.venv/bin/python -m pytest
USE_MOCK_LLM=true .venv/bin/python scripts/evaluate.py
# Optional timing run:
USE_MOCK_LLM=true .venv/bin/python scripts/evaluate.py --include-runtime --output /tmp/uamas-results.md
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
- `CLASSIFIER_MODEL_TYPE` (`embedding` default, optional `tfidf`)
- `STRICT_ARTIFACT_METADATA` (`true` default; set to `false` to allow loading artifacts without dataset metadata checks)

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


## Pre-demo live validation checklist
1. Export the required GitHub Models environment variables (`GITHUB_MODELS_ENDPOINT`, `GITHUB_TOKEN`, `GITHUB_MODELS_MODEL`).
2. Start the app with live mode enabled:
   `USE_MOCK_LLM=false .venv/bin/python -m uvicorn app.main:app --reload`
3. Verify runtime readiness:
   `curl -s http://127.0.0.1:8000/diagnostics | python -m json.tool`
4. Run one clear and one ambiguous prediction through `POST /predict`.
5. Confirm `reliability.llm_runtime` and diagnostics `last_runtime` show the expected live/fallback path.
6. If a fallback path appears, capture the reason and include it in demo notes.
## Merge safety checklist
- Keep each PR single-purpose (for example: evaluation logic, tests, or docs), instead of mixing concerns.
- Rebase your branch on `main` before opening a PR and again before merge.
- Prefer append-only edits in large test files to reduce overlapping insertion hunks.
- Use feature-scoped unique test names (for example: `test_eval_runtime_*`) to avoid duplicate definitions.
- Avoid committing generated report artifacts unless reviewers explicitly request them.
- For stacked work, split follow-up updates into small PRs that touch fewer hotspot files.


## Classifier runtime notes
- Default classifier mode is **embedding-first** (`HashingVectorizer + TruncatedSVD + LogisticRegression`).
- You can switch training/runtime mode with `CLASSIFIER_MODEL_TYPE=tfidf` for compatibility checks.
- Artifact metadata validation is enabled by default. If train/calibration row counts or hashes drift, the artifact is rejected and the classifier retrains from dataset files.
- For emergency compatibility fallback, set `STRICT_ARTIFACT_METADATA=false` and rebuild a fresh artifact as soon as possible.
- `GET /diagnostics` exposes `classifier_model_type`, `classifier_runtime`, and calibration threshold for demo verification.
