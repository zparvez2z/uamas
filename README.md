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

Classifier/runtime profile:
- `RUNTIME_PROFILE_PATH` (default `config/runtime_profile.json`)
- Profile file keys:
  - `alpha` (default `0.1`)
  - `classifier_model_type` (`embedding` default, optional `tfidf`)
  - `strict_artifact_metadata` (`true` default)
  - `classifier_artifact_mismatch_policy` (`auto_rebuild` default; optional `fail_fast`, `in_memory`)

Classifier-critical config precedence is fixed across app and scripts:
- CLI args (when present) > explicit env vars > runtime profile file > hardcoded defaults.

Useful runtime flags:
- `USE_MOCK_LLM`
- `ALPHA` (overrides profile `alpha`)
- `MAX_SET_SIZE`
- `LLM_MAX_RETRIES`
- `ENABLE_ABSTAIN`
- `CLASSIFIER_MODEL_TYPE` (overrides profile `classifier_model_type`)
- `STRICT_ARTIFACT_METADATA` (overrides profile `strict_artifact_metadata`)
- `CLASSIFIER_ARTIFACT_MISMATCH_POLICY` (overrides profile policy: `auto_rebuild`, `fail_fast`, `in_memory`)
- `ENABLE_LANGGRAPH_REVIEW` (`false` default; enables optional second-pass review flow)
- `REVIEW_CONFIDENCE_THRESHOLD` (default `0.55`, second-pass trigger threshold)
- `REVIEW_SET_SIZE_TRIGGER` (default `MAX_SET_SIZE`, second-pass trigger threshold)
- `REVIEW_CACHE_TTL_SECONDS` (default `300`, TTL for cached review second-pass node results)
- `REVIEW_GATE_STRATEGY` (`legacy` default, optional `latency_v1` for stricter review gating)
- `REVIEW_VERY_LOW_CONFIDENCE_FLOOR` (default `0.35`, used by `latency_v1`)

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

Host-side live verification helper:
- Run `./host_side_verfication_pass.sh`
- Expected success signal: each `PREDICT_*` entry shows `llm_runtime: LIVE` and `diag_llm_last_error: None`.

## GitHub Actions live smoke workflow
- Workflow: `.github/workflows/live-smoke.yml`
- Trigger: manual (`workflow_dispatch`) from the Actions tab.
- Required repository secret: `MODELS_API_KEY` (a token with GitHub Models access).
- Runtime defaults in workflow:
  - `USE_MOCK_LLM=false`
  - `GITHUB_MODELS_ENDPOINT=https://models.github.ai/inference`
  - `GITHUB_MODELS_MODEL=openai/gpt-4.1`
- What it validates:
  - live token is present,
  - classifier artifact can be rebuilt,
  - three sample predictions complete with `llm_runtime=LIVE`,
  - diagnostics keep `last_runtime=LIVE` and `llm_last_error=None`.

You can run the same check locally:
```bash
USE_MOCK_LLM=false .venv/bin/python scripts/live_smoke.py
```
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
- Artifact metadata validation is enabled by default. If train/calibration row counts or hashes drift, behavior is controlled by `CLASSIFIER_ARTIFACT_MISMATCH_POLICY`.
- Artifact metadata now includes a format version, classifier family, scikit-learn version, and dataset fingerprint for compatibility checks and auditability.
- Default mismatch policy is `auto_rebuild`: on mismatch, the classifier retrains, rewrites the artifact, and reloads it so runtime ends in `ARTIFACT` when rebuild succeeds.
- `fail_fast` raises immediately on mismatch.
- `in_memory` preserves legacy behavior (reject artifact and continue with in-memory training only).
- For emergency compatibility fallback, set `STRICT_ARTIFACT_METADATA=false` and rebuild a fresh artifact as soon as possible.
- Optional LangGraph review mode can run a second pass for uncertain predictions when `ENABLE_LANGGRAPH_REVIEW=true`.
- `GET /diagnostics` exposes `classifier_model_type`, `classifier_runtime`, and calibration threshold for demo verification.
