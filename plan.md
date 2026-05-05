# Demo Project Plan: Reliable GenAI Classification and Extraction

## 1) Goal and Audience
Build a small, credible demo that mirrors the role: a Python library and demo pipeline that improves reliability of LLM-based classification and structured extraction. The output should be easy for a senior engineer to review in 10 to 15 minutes and should show research-to-code ability without overclaiming.

## 2) Problem Statement
Given a product title and description, generate:
- A product category (single label or small set of likely labels).
- A structured attribute payload (brand, size, material, color, etc.).

Reliability requirements:
- Provide calibrated uncertainty (coverage guarantees for the label set).
- Validate outputs with strict schemas.
- Fallback or abstain when confidence is low.

## 3) Scope
In scope:
- A dataset aligned to the Kaufland Seller API CSV schema (schema-compatible even without live API access).
- A Python package that implements calibration and evaluation utilities.
- A stakeholder-facing web demo (FastAPI + simple UI).
- Clear metrics and reproducible evaluation.

Out of scope:
- Production-grade infrastructure, full multi-agent orchestration, or enterprise integrations.
- Closed data or any internal Schwarz data.

## 4) Tech Stack (consistent with job ad)
- Python 3.11
- Pydantic (schema validation)
- LLM runtime: GitHub Models (Azure OpenAI GPT-4.1) via OpenAI-compatible API
- Scoring and calibration: numpy, scikit-learn, MAPIE or custom conformal implementation
- Embedding model for baseline classifier (sentence-transformers)
- FastAPI + simple UI (Jinja templates or HTMX)

## 5) Core Deliverables
- A small Python library: reliable_genai
  - calibration.py: conformal calibration for label sets
  - scoring.py: nonconformity scoring and abstention logic
  - evaluation.py: coverage, set size, accuracy, abstention rate, latency
  - llm_wrappers.py: structured output and retry policy
- Demo pipeline (FastAPI + simple web UI):
  - Input: product title + description
  - Output: category set, attributes, confidence metadata
- A short evaluation report with charts and conclusions
- A 3 to 5 minute demo walkthrough script

## 6) Architecture Overview
1) Data ingestion
  - Use Kaufland Seller API CSV schema (semicolon-separated, UTF-8)
  - Convert a public product dataset into schema-compatible CSV

2) Preprocess
  - Normalize title/description, remove noise
  - Embed text for baseline classifier

2) Baseline classifier
   - Train a lightweight classifier on embeddings
   - Produce probability distribution over categories

3) Conformal calibration
   - Use a held-out calibration set to compute thresholds
   - Return a label set with guaranteed coverage at 1 - alpha

4) LLM extraction
   - Ask the LLM for structured attributes via JSON schema
   - Validate with Pydantic, repair or fallback if invalid

5) Reliability policy
   - If label set is too large or empty, abstain or request a second pass
   - Attach reliability metadata to the output

7) Evaluation
   - Coverage, set size, accuracy, abstention rate, latency
   - Compare baseline vs calibrated

8) Demo UI
  - FastAPI endpoint and a clean, minimal web page for stakeholders

## 7) Evaluation Metrics
- Coverage: fraction of test examples where true label is in the set
- Set size: average number of labels returned
- Accuracy: top-1 or top-set accuracy
- Abstention rate: how often the model refuses to answer
- Latency: end-to-end response time

Target (demo-level):
- Coverage at least 0.90 with set size under 3
- Abstention under 10 percent on clean inputs

## 8) Detailed Implementation Plan (10 working days)

Day 1 - Requirements and data
- Use the Kaufland Seller API CSV schema as the data contract
- Select a public e-commerce dataset and map it into the schema
- Define label taxonomy and map to a manageable set of classes
- Build data loader and train/validation/calibration split

Day 2 - Baseline classifier
- Create embeddings and train a simple classifier
- Baseline metrics on validation set
- Save model artifacts

Day 3 - Calibration module
- Implement conformal calibration for label sets
- Validate coverage on calibration set
- Add unit tests for edge cases

Day 4 - LLM structured extraction
- Define Pydantic schemas for product attributes
- Build LLM wrapper with JSON output, retries, and validation
- Add a small sample test set

Day 5 - Reliability policy
- Combine classifier and LLM in a single pipeline
- Implement abstention and fallback logic
- Log reliability metadata for each output

Day 6 - Evaluation harness
- Build evaluation script for coverage, set size, accuracy
- Compare baseline vs calibrated vs abstention
- Capture latency stats

Day 7 - Demo interface
- FastAPI endpoint with a stakeholder-facing web page
- Example inputs and responses
- Add README with setup and usage

Day 8 - Polish and documentation
- Clean up package structure and typing
- Document design decisions and tradeoffs
- Add a short engineering note on reliability guarantees

Day 9 - Demo script and slides
- Prepare a short demo walkthrough
- Highlight metrics and reliability tradeoffs
- Include a clear next-steps section

Day 10 - Final review
- Re-run evaluation
- Fix defects and improve clarity
- Prepare final deliverables

## 9) Repo Structure
- reliable_genai/
  - __init__.py
  - calibration.py
  - scoring.py
  - evaluation.py
  - llm_wrappers.py
  - pipeline.py
- app/
  - main.py
  - templates/
  - static/
- data/
  - raw/
  - processed/
- scripts/
  - train_baseline.py
  - calibrate.py
  - evaluate.py
  - demo_web.py
- reports/
  - results.md
  - figures/
- .env.example
- README.md

## 10) Risks and Mitigations
- Data label noise: use a smaller clean subset and document limitations
- LLM JSON instability: strict Pydantic validation and retries
- Calibration failure: verify coverage and adjust alpha
- Time overrun: keep label set small and avoid extra features

## 11) Stretch Goals (only if time remains)
- Add a small LangGraph workflow for optional second-pass review
- Add a second model for semantic consistency scoring
- Export a small dashboard for reliability metrics

## 12) Demo Walkthrough (3 to 5 minutes)
1) Show the web UI with a raw product input
2) Show baseline prediction and failure cases
3) Show calibrated label set and reliability metadata
4) Show structured attribute extraction and schema validation
5) Show evaluation summary and tradeoffs

## 13) How This Maps to the Role
- Research-to-code: conformal calibration into a working library
- Software engineering: Python package, tests, clear API
- Benchmarking: metrics and evaluation harness
- Uncertainty-aware GenAI: label sets and abstention policy
