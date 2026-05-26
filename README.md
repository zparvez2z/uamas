# Reliable GenAI Demo

This project is a small end-to-end demo for uncertainty-aware product classification and attribute extraction.

You enter a product title and description, and the app returns:
- a category prediction set,
- extracted attributes,
- and reliability metadata (confidence, abstention behavior, runtime source).

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
