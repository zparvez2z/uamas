# UAMAS Catalog Quality Assistant

[![CI](https://github.com/zparvez2z/uamas/actions/workflows/ci.yml/badge.svg)](https://github.com/zparvez2z/uamas/actions/workflows/ci.yml)

**UAMAS** stands for **Uncertainty-Aware Multi-Agent System**. It analyzes product listings without pretending every model answer is equally reliable.

Given a title and description, UAMAS can:
- predict a calibrated set of possible product categories,
- extract structured attributes such as brand, color, material, and size,
- check whether the category prediction is semantically consistent with the listing,
- automatically accept low-risk results,
- route uncertain results to a human reviewer,
- and preserve the workflow and every agent execution for later inspection.

The current real-world use case is product catalog quality control. The design can later support other workflows where model confidence, human review, and traceable decisions matter.

## Why This Exists

Catalog data is often incomplete, ambiguous, or inconsistent. A conventional classifier still returns one label even when the evidence is weak. UAMAS instead exposes uncertainty and turns it into an operational decision:

- **Clear listing:** accept automatically.
- **Uncertain listing:** return a bounded candidate set and request review.
- **Provider failure:** degrade gracefully instead of losing the entire request.
- **Agent failure:** preserve the failed workflow and error history for diagnosis.

## How It Works

1. The classifier agent creates category probabilities and a calibrated candidate set.
2. The extraction agent independently identifies structured product attributes.
3. The semantic critic checks whether the listing supports the proposed categories.
4. The policy agent combines confidence, set size, abstention, and semantic evidence.
5. The decision agent either accepts the result or the human-review agent creates a queue task.
6. SQLite stores the listing, prediction, review task, workflow status, and per-agent history.

![UAMAS architecture](docs/architecture.svg)

The homepage keeps the original `/predict` experience for compatibility. The complete multi-agent workflow runs through `POST /api/listings/analyze`.

## Current Status

Implemented:
- six explicit catalog-quality agents coordinated through LangGraph, with sequential fallback,
- calibrated classification trained on processed public product data,
- semantic consistency scoring using a second embedding model,
- deterministic policy routing and a browser-based human-review queue,
- durable SQLite workflow and per-agent execution history,
- leakage-safe review campaigns over a dedicated feedback pool,
- validated, deduplicated feedback exports and correction reports,
- production fail-closed authentication and CSRF-protected review actions,
- audited retention cleanup with dry-run preview and pre-change backups,
- operational diagnostics, metrics, dashboard, and evaluation artifacts,
- mock mode, live GitHub Models mode, automated CI, and a manual live smoke workflow.

Next:
- run and resolve the first balanced review campaign,
- train a candidate classifier from eligible reviewer evidence,
- and compare it against the active artifact before explicit promotion.

See [TECHNICAL.md](TECHNICAL.md) for the implementation details and current engineering roadmap.

## Quick Start

Create the environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Start in deterministic local mode:

```bash
USE_MOCK_LLM=true ENABLE_SEMANTIC_SCORER=false \
  .venv/bin/python -m uvicorn app.main:app --reload
```

Open:
- Application: http://127.0.0.1:8000
- Review queue: http://127.0.0.1:8000/review
- Operations dashboard: http://127.0.0.1:8000/dashboard
- Interactive API documentation: http://127.0.0.1:8000/docs

## Run a Multi-Agent Analysis

```bash
curl -X POST http://127.0.0.1:8000/api/listings/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "sample-001",
    "title": "Nike black running shoes size 42",
    "description": "Breathable mesh upper with a cushioned rubber sole"
  }'
```

The response contains the final decision, reliability evidence, agent trace, optional review-task ID, and durable workflow-run ID.

Inspect that workflow afterward:

```bash
curl http://127.0.0.1:8000/api/workflow-runs/WORKFLOW_RUN_ID
```

## Live GitHub Models Mode

Set `GITHUB_TOKEN`, `GITHUB_MODELS_ENDPOINT`, and `GITHUB_MODELS_MODEL` in `.env`, then run:

```bash
USE_MOCK_LLM=false .venv/bin/python -m uvicorn app.main:app --reload
```

Check `/diagnostics` after a request to confirm whether the latest model call used `LIVE`, `MOCK`, or `FALLBACK_MOCK`.

## Production Security

Set `UAMAS_ENV=production` and provide distinct strong values for:
- `UAMAS_ADMIN_TOKEN`
- `UAMAS_API_TOKEN`
- `UAMAS_SESSION_SECRET`
- `UAMAS_ALLOWED_HOSTS`

Production startup fails when this configuration is missing or unsafe. Browser operations use an administrator session; machine APIs require `Authorization: Bearer <UAMAS_API_TOKEN>`.

See [SECURITY.md](SECURITY.md) for secret handling and deployment requirements.

## Retention Cleanup

Preview cleanup without changing workflow data:

```bash
.venv/bin/python scripts/cleanup_operational_data.py
```

Apply cleanup after reviewing the report:

```bash
.venv/bin/python scripts/cleanup_operational_data.py --apply
```

Applied cleanup creates a backup, prunes expired detailed agent history, and preserves workflow summaries and human-review evidence.

## Feedback Evidence

Preview resolved human reviews that are ready for export:

```bash
.venv/bin/python scripts/export_review_feedback.py
```

Write a versioned, deduplicated evidence batch after reviewing the preview:

```bash
.venv/bin/python scripts/export_review_feedback.py --apply
```

Each batch separates complete review evidence, training-eligible examples, and excluded records with validation reasons. Generated feedback artifacts remain local under `data/feedback/`; retraining and classifier promotion are still explicit operations.

## Data

The processed dataset comes from the public [Shopify Product Catalogue](https://huggingface.co/datasets/Shopify/product-catalogue).

Current processed data:
- 27,108 normalized listings,
- 18,972 training examples,
- 4,063 calibration examples,
- 3,953 untouched test examples,
- 120 balanced feedback-pool examples,
- six target categories: Beauty, Clothing, Electronics, Home, Shoes, and Sports.

Large upstream cache files are intentionally not stored in the repository. Source provenance, category counts, and split metadata are recorded in `data/processed/dataset_metadata.json`.

No private company data is included.

## Review Campaigns

Preview a deterministic, balanced campaign without model or database writes:

```bash
USE_MOCK_LLM=true .venv/bin/python scripts/review_campaign.py \
  plan --name baseline-01 --per-category 20 --seed 42
```

Create it, then process bounded batches:

```bash
USE_MOCK_LLM=true .venv/bin/python scripts/review_campaign.py \
  create --name baseline-01 --per-category 20 --seed 42

USE_MOCK_LLM=true .venv/bin/python scripts/review_campaign.py \
  run CAMPAIGN_ID --limit 20

.venv/bin/python scripts/review_campaign.py status CAMPAIGN_ID
.venv/bin/python scripts/review_campaign.py report CAMPAIGN_ID
```

Review queued items at `/review?campaign_id=CAMPAIGN_ID`. Dataset reference labels remain hidden from reviewer HTML and APIs; they are used only for aggregate post-review comparison.

## Validation

```bash
.venv/bin/python scripts/train_classifier.py --force
.venv/bin/python -m pytest
USE_MOCK_LLM=true .venv/bin/python scripts/evaluate.py
```

Evaluation evidence is available in:
- [reports/results.md](reports/results.md)
- [reports/results.json](reports/results.json)

## Project Guide

- [TECHNICAL.md](TECHNICAL.md): architecture, runtime behavior, configuration, reliability controls, and roadmap
- [SECURITY.md](SECURITY.md): production access, secret handling, and vulnerability reporting
- [plan.md](plan.md): phased product and engineering plan
- [DEMO.md](DEMO.md): demonstration runbook
- `app/`: FastAPI routes, templates, and operational interfaces
- `reliable_genai/`: agents, graphs, reliability pipeline, models, and persistence
- `scripts/`: ingestion, training, evaluation, and live-smoke commands
- `tests/`: unit and integration coverage
