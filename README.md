# UAMAS Catalog Quality Assistant

UAMAS is an uncertainty-aware multi-agent assistant for product catalog quality.

You submit a product title and description, and specialized agents coordinate to return:
- a category prediction set,
- extracted attributes,
- semantic consistency evidence,
- reliability metadata,
- and either an automatic acceptance decision or a human-review task.

Each analysis also receives a durable workflow ID so agent timing, degradation, outputs, and failures remain queryable after the request completes.

For implementation details, runtime knobs, diagnostics fields, CI workflows, and architecture, see [TECHNICAL.md](TECHNICAL.md).

## Quick start
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Run the app in mock mode:
```bash
USE_MOCK_LLM=true .venv/bin/python -m uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000
Dashboard: http://127.0.0.1:8000/dashboard

## Switch to live mode
Set your GitHub Models credentials in `.env`, then run:
```bash
USE_MOCK_LLM=false .venv/bin/python -m uvicorn app.main:app --reload
```

## Try one sample input
- Title: `Nike running shoes black size 42`
- Description: `Breathable mesh upper and cushioned sole`

## Basic checks
```bash
.venv/bin/python scripts/train_classifier.py --force
.venv/bin/python -m pytest
USE_MOCK_LLM=true .venv/bin/python scripts/evaluate.py
```

## Repository map
- `app/` web UI and API
- `reliable_genai/` pipeline and reliability logic
- `scripts/` train/evaluate helpers
- `reports/` evaluation outputs

## Notes
- Public or synthetic data only.
- No internal Schwarz data is included.
