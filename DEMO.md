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

## 3) Local Application Demo
Terminal 1:
```bash
cd /home/pz/projects/uamas
source .venv/bin/activate
ATTRIBUTE_PROVIDER=mock ENABLE_SEMANTIC_SCORER=false \
  .venv/bin/python -m uvicorn app.main:app --reload
```

Open:
- http://127.0.0.1:8000
- http://127.0.0.1:8000/diagnostics
- http://127.0.0.1:8000/dashboard

Expected diagnostics:
- `runtime_mode: "MOCK"`
- `classifier_runtime: "ARTIFACT"`

## 4) Real-Model Evidence Path
Real Qwen execution is a bounded Colab batch workflow, not a laptop-hosted API mode. Start a retained T4 session and run the strict preflight:

```bash
./scripts/install_colab_cli.sh
source .colab-cli-venv/bin/activate
colab sessions
colab run --gpu T4 --keep -s uamas-qwen --timeout 7200 \
  scripts/colab_preflight.py
```

Then run and retrieve the fixed benchmark:

```bash
colab exec -s uamas-qwen --timeout 7200 \
  -f scripts/colab_model_benchmark.py
colab download -s uamas-qwen \
  /content/uamas-output/attribute-benchmark.json \
  reports/attribute-extraction-qwen35.json
```

Expected success signal:
- all 30 benchmark calls report `LOCAL_HF`,
- schema success is complete,
- no fallback or failed calls are present,
- latency and peak GPU memory are recorded.

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
2. `/dashboard` page: semantic scorer health + latest evaluation summary cards.
3. Run Input A: show category set + attributes + reliability metadata.
4. Run Input B: show uncertainty handling (set size/abstain behavior).
5. Show the downloaded Qwen benchmark evidence and explain that strict campaigns abort on degradation.
6. Point to `reports/results.md` and `reports/results.json` for deterministic evidence.

## 7) Fast Troubleshooting
### If Colab preflight reports `FAILED`
- Confirm the assigned runtime has a CUDA GPU with `colab status -s uamas-qwen`.
- Inspect the reported model-loading or validation error.
- Do not create or resume a real review campaign until preflight passes.

### If classifier is not `ARTIFACT`
```bash
source .venv/bin/activate
env -u ALPHA -u CLASSIFIER_MODEL_TYPE -u STRICT_ARTIFACT_METADATA -u CLASSIFIER_ARTIFACT_MISMATCH_POLICY \
  RUNTIME_PROFILE_PATH=config/runtime_profile.json \
  .venv/bin/python scripts/train_classifier.py --force
```

### If port 8000 is busy
```bash
ATTRIBUTE_PROVIDER=mock .venv/bin/python -m uvicorn app.main:app --reload --port 8001
```
