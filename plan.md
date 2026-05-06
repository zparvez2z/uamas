# Demo Project Plan: Reliable GenAI Classification and Extraction

## 1) Goal and Audience
Build a small, credible demo that translates conformal prediction research into practice: a Python library and demo pipeline that improves reliability of LLM-based classification and structured extraction using prediction sets with coverage guarantees. The output should be easy for a senior engineer to review in 10 to 15 minutes and should show research-to-code ability grounded in papers like "Conformal Language Modeling" (Quach et al., 2023) and "Towards Uncertainty-Aware Language Agent" (Han et al., 2024) without overclaiming.

## 2) Problem Statement
Given a product title and description, generate:
- A **product category prediction set** C(x) with a distribution-free coverage guarantee: P(true label ∈ C(x)) ≥ 1 - α
- A **structured attribute payload** (brand, size, material, color, etc.) with schema validation.
- **Reliability metadata**: alpha (confidence level), coverage target, set size, abstention reason.

Reliability requirements:
- Provide calibrated uncertainty using the **Learn-Then-Test (LTT) framework** for conformal calibration (Angelopoulos et al., 2021).
- Return a small set of plausible categories instead of a brittle single prediction.
- Validate outputs with strict Pydantic schemas.
- Abstain (return empty set or flag for review) when set size exceeds threshold or confidence is too low.

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
1) **Data ingestion** (Kaufland schema)
  - Use Kaufland Seller API CSV schema (semicolon-separated, UTF-8) as data contract
  - Convert a public product dataset (e.g., sampled e-commerce data) into schema-compatible CSV
  - Split into train (70%), calibration (15%), test (15%)

2) **Text preprocessing**
  - Normalize title/description, remove noise
  - Embed using sentence-transformers to create feature vectors

3) **Baseline classifier** (produces scores for conformal input)
  - Train a lightweight classifier (logistic regression or MLP) on embedding features
  - Produce probability distribution over categories for each input
  - This is the non-conformity scorer input

4) **Conformal calibration** (Learn-Then-Test framework)
  - Use calibration split to compute threshold λ such that coverage guarantee holds
  - Build prediction sets C(x) by accumulating labels until cumulative probability ≥ 1 - α
  - Proof: coverage is guaranteed to hold on unseen test data (distribution-free)
  - Reference: aangelopoulos/conformal-prediction repo for implementation

5) **LLM extraction** (attribute generation)
  - Query GitHub Models (GPT-4.1) for structured attributes given title/description
  - Validate with Pydantic schemas, implement retry logic
  - Fallback to keyword-based extraction if LLM fails

6) **Reliability policy** (abstention logic)
  - If |C(x)| = 0 (no label achieves threshold): abstain, flag for review
  - If |C(x)| > max_set_size: abstain, too much uncertainty
  - Otherwise: output category set, attributes, and reliability metadata
  - Attach alpha, coverage_target, set_size, confidence to each output

7) **Evaluation** (metrics grounded in conformal theory)
  - **Coverage**: fraction of test examples where true label ∈ C(x); target ≥ 1 - α
  - **Set size**: average |C(x)|; target < 3 for demo
  - **Abstention rate**: fraction where |C(x)| = 0 or |C(x)| > threshold; target < 10%
  - **Latency**: end-to-end response time including LLM call
  - Compare calibrated vs. single-label baseline

8) **Demo UI**
  - FastAPI endpoint with Jinja2 template
  - Display category set, attributes, runtime badge (LIVE/MOCK)
  - Show reliability metadata and abstention reason
  - Example walkthrough script in DEMO.md

## 7) Evaluation Metrics (Conformal Framework)

**Core conformal metrics**:
- **Coverage**: P(true label ∈ C(x)) measured on test set; target ≥ 1 - α (e.g., ≥ 0.9 for α = 0.1)
- **Set size**: E[|C(x)|] on test set; target < 3 for product classification
- **Efficiency**: (set size achieved) / (theoretical minimum for desired coverage)

**Practical metrics**:
- **Abstention rate**: fraction of examples where |C(x)| = 0 or |C(x)| > max_set_size; target < 10% on clean inputs
- **Top-1 accuracy within set**: fraction where true label is ranked highest in C(x)
- **Latency**: end-to-end response time including LLM attribute extraction (target < 3s)

**Demo targets** (realistic for heuristic classifier and 6-label taxonomy):
- Coverage ≥ 0.85 with avg set size 1.5–2.5
- Abstention rate 10–20% (expected when classifier is weak)
- No single required accuracy: the guarantee is on the set, not individual predictions

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

Day 3 - Calibration module (Learn-Then-Test framework)
- Implement conformal set builder: accumulate labels until cumulative probability ≥ 1 - alpha
- Use calibration split to find optimal threshold via LTT method (Angelopoulos et al., 2021)
- Validate empirical coverage on calibration set: does it match 1 - alpha?
- Reference: aangelopoulos/conformal-prediction repo for calibration template
- Add unit tests for edge cases (empty set, all labels, single label)

Day 4 - LLM structured extraction
- Define Pydantic schemas for product attributes
- Build LLM wrapper with JSON output, retries, and validation
- Add a small sample test set

Day 5 - Reliability policy
- Combine classifier and LLM in a single pipeline
- Implement abstention and fallback logic
- Log reliability metadata for each output

Day 6 - Evaluation harness (conformal metrics)
- Build evaluation script that measures:
  - Empirical coverage: P(true label ∈ C(x)) on test set
  - Average set size E[|C(x)|]
  - Abstention rate (|C(x)| = 0 or > threshold)
  - Latency per prediction
- Compare single-label baseline vs. conformal sets
- Generate results.md report with metrics table and interpretation
- Verify coverage ≥ 1 - alpha (if not, recalibrate or increase alpha)

Day 7 - Demo interface
- FastAPI endpoint with a stakeholder-facing web page
- Example inputs and responses
- Add README with setup and usage

Day 8 - Polish and documentation
- Clean up package structure and typing
- Document design decisions and tradeoffs in TECHNICAL.md
- Add engineering note explaining:
  - The conformal guarantee (distribution-free, holds on unseen data)
  - Why single-label predictions are risky; why sets are more reliable
  - The alpha parameter (coverage target) and how to tune it
  - Abstention policy and when to escalate to human review
- Reference: Quach et al. (2023), Han et al. (2024), Angelopoulos et al. (2021)

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
- **Research-to-code**: conformal calibration framework (Learn-Then-Test) translated to production-ready Python
- **Software engineering**: clean package structure, validation via Pydantic, reproducible evaluation
- **Benchmarking**: empirical coverage, set size, abstention metrics grounded in conformal theory
- **Uncertainty-aware GenAI**: prediction sets instead of brittle single predictions; uncertainty drives abstention and escalation
- **Literature grounding**: implementation guided by Quach et al. (2023), Han et al. (2024), and Angelopoulos et al. (2021–2023)

The final demo is credible because it translates a peer-reviewed research framework into a working system, measures what it claims, and honestly documents limitations.
