# UAMAS Demo Runbook

This is the exact operator runbook for demo execution.

## 1) One-time Setup
```bash
cd /home/pz/projects/uamas
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2) Pre-Demo Health Check (Deterministic)
Run from project root:
```bash
source .venv/bin/activate
env -u ALPHA -u CLASSIFIER_MODEL_TYPE -u STRICT_ARTIFACT_METADATA -u CLASSIFIER_ARTIFACT_MISMATCH_POLICY \
  RUNTIME_PROFILE_PATH=config/runtime_profile.json \
  .venv/bin/python scripts/train_classifier.py --force

env -u ALPHA -u CLASSIFIER_MODEL_TYPE -u STRICT_ARTIFACT_METADATA -u CLASSIFIER_ARTIFACT_MISMATCH_POLICY \
  RUNTIME_PROFILE_PATH=config/runtime_profile.json \
  .venv/bin/python scripts/evaluate.py --mock --with-review-acceptance-check --output /tmp/uamas-pre-demo-results.md
```

Expected signal:
- Evaluation completes without errors.
- Output file exists: `/tmp/uamas-pre-demo-results.md`.

## 3) Mock Demo Path (Safe Fallback)
Terminal 1:
```bash
cd /home/pz/projects/uamas
source .venv/bin/activate
USE_MOCK_LLM=true .venv/bin/python -m uvicorn app.main:app --reload
```

Open:
- http://127.0.0.1:8000
- http://127.0.0.1:8000/diagnostics

Expected diagnostics:
- `runtime_mode: "MOCK"`
- `classifier_runtime: "ARTIFACT"`

## 4) Live Demo Path (Primary)
Make sure `.env` has valid:
- `GITHUB_TOKEN`
- `GITHUB_MODELS_ENDPOINT`
- `GITHUB_MODELS_MODEL`

Terminal 1:
```bash
cd /home/pz/projects/uamas
source .venv/bin/activate
USE_MOCK_LLM=false .venv/bin/python -m uvicorn app.main:app --reload
```

Terminal 2 (strict host-side verification):
```bash
cd /home/pz/projects/uamas
source .venv/bin/activate
./host_side_verfication_pass.sh
```

Expected success signal:
- Every `PREDICT_*` block shows:
  - `"llm_runtime": "LIVE"`
  - `"diag_last_runtime": "LIVE"`
  - `"diag_llm_last_error": None`

## 5) Demo Inputs to Use in UI
### Input A (clear case)
- Title: `Nike running shoes black size 42`
- Description: `Breathable mesh upper and cushioned sole`

Expected behavior:
- category set is small and shoe-related,
- abstention is usually false.

### Input B (ambiguous case)
- Title: `Spa Gift Set`
- Description: `Body lotion, scented candle, decorative storage box`

Expected behavior:
- larger uncertainty or abstention may appear,
- reliability metadata clearly explains outcome.

## 6) What to Show in 3-5 Minutes
1. `/diagnostics` page: runtime mode, classifier runtime, review graph status.
2. Run Input A: show category set + attributes + reliability metadata.
3. Run Input B: show uncertainty handling (set size/abstain behavior).
4. Mention that live failures degrade gracefully to fallback mock with `llm_last_error`.
5. Point to `reports/results.md` for deterministic evidence and acceptance metrics.

## 7) Fast Troubleshooting
### If live requests return `FALLBACK_MOCK`
- Check `GET /diagnostics` -> `llm_last_error`.
- Verify `.env` token and endpoint.
- Re-run `./host_side_verfication_pass.sh`.

### If classifier is not `ARTIFACT`
```bash
source .venv/bin/activate
env -u ALPHA -u CLASSIFIER_MODEL_TYPE -u STRICT_ARTIFACT_METADATA -u CLASSIFIER_ARTIFACT_MISMATCH_POLICY \
  RUNTIME_PROFILE_PATH=config/runtime_profile.json \
  .venv/bin/python scripts/train_classifier.py --force
```

### If port 8000 is busy
```bash
USE_MOCK_LLM=true .venv/bin/python -m uvicorn app.main:app --reload --port 8001
```
