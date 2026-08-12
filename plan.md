# UAMAS Product Plan: Real Multi-Agent Seller Catalog Quality Assistant

## Summary
UAMAS stands for **Uncertainty-Aware Multi-Agent System**.

The project is moving from a reliability demo into a real product direction: a **Seller Catalog Quality Assistant** that helps process messy product listings by coordinating specialized agents.

The real-world problem:
- Sellers submit incomplete, ambiguous, or inconsistent product listings.
- Marketplace/catalog teams need to know which listings can be auto-accepted and which require human review.
- The system should reduce manual review load while making uncertainty and failure modes visible.

Current state:
- Uncertainty-aware classifier is implemented.
- Semantic consistency scorer is implemented.
- Optional LangGraph review flow exists.
- Dashboard, diagnostics, deterministic evaluation artifacts, CI, and live smoke are in place.
- Real Shopify product data is ingested into deterministic processed train/calibration/test splits.
- SQLite persistence is implemented for listings, predictions, and review tasks.
- `CatalogQualityGraph` coordinates explicit classifier, extraction, semantic critic, policy, human-review, and decision agents.

Target state:
- UAMAS becomes a real multi-agent workflow with persistence, human review, API endpoints, operational metrics, and feedback-based improvement.

## Product Goal
Build a system that analyzes product listings and returns:
- proposed category set,
- extracted product attributes,
- semantic consistency signal,
- confidence and uncertainty metadata,
- final workflow decision:
  - `auto_accept`
  - `needs_human_review`
  - `reject_or_request_clarification`

The system should be useful as an internal catalog QA assistant, not only as a model demo.

## Agent Roles
The multi-agent version should introduce explicit agents with clear responsibilities.

### Classifier Agent
- Uses the existing conformal classifier.
- Produces category set, confidence, set size, abstention flag, and classifier diagnostics.

### Attribute Extraction Agent
- Uses the existing GitHub Models/fallback extraction path.
- Produces validated structured attributes.

### Semantic Critic Agent
- Uses the semantic scorer and optional LLM critique.
- Detects category/text mismatch and weak attribute consistency.

### Policy Agent
- Applies workflow rules.
- Decides whether the listing is auto-acceptable, needs review, or should be rejected/request clarification.

### Decision Agent
- Produces final decision, explanation, and risk level.

### Human Review Agent
- Creates review tasks for uncertain listings.
- Stores reviewer decisions and corrections for future evaluation/retraining.

## Roadmap

### Phase 1: Real Product Data Ingestion
Move from synthetic/demo data to a real public product dataset before expanding the operational workflow.

Status: **implemented** for the Shopify Product Catalogue path. Processed split files and provenance metadata are committed under `data/processed/`; large raw/cache data is intentionally not committed.

Preferred first source:
- **Shopify Product Catalogue** because it includes real product titles, descriptions, categories, brand-like fields, and a product taxonomy classification shape close to the current pipeline.

Secondary benchmark source:
- **WDC Product Categorization** for stronger research/benchmark credibility after the Shopify path is stable.

The first ingestion script should:
- load a fixed-size real product sample,
- normalize product title and description into the current training format,
- map source taxonomy labels into the current six-label taxonomy,
- drop or quarantine unmapped rows,
- produce train/calibration/test splits,
- write dataset provenance and category distribution metadata.

Suggested script:
```text
scripts/ingest_real_products.py
```

Current six-label target taxonomy:
```text
Shoes
Clothing
Electronics
Home
Beauty
Sports
```

Initial mapping examples:
- `Apparel & Accessories > Shoes` -> `Shoes`
- `Apparel & Accessories > Clothing` -> `Clothing`
- `Electronics` -> `Electronics`
- `Home & Garden` -> `Home`
- `Health & Beauty` -> `Beauty`
- `Sporting Goods` -> `Sports`

Generated files:
```text
data/processed/train.json
data/processed/calibration.json
data/processed/test.json
data/processed/feedback_pool.json
data/processed/dataset_metadata.json
```

Raw dataset policy:
- Do not commit large raw downloaded datasets.
- Commit only a small curated processed sample if license and size allow.
- Keep ingestion reproducible through script + metadata.

After ingestion:
```bash
.venv/bin/python scripts/train_classifier.py --force
USE_MOCK_LLM=true .venv/bin/python scripts/evaluate.py
```

Real-data acceptance criteria:
- processed splits are generated deterministically from a fixed seed,
- every row has `title`, `description`, and mapped `category`,
- category distribution is recorded,
- classifier trains from real data without artifact mismatch,
- evaluation artifacts are refreshed,
- limitations and source provenance are documented.

### Phase 2: Persistence + Review Queue
Add a minimal operational data layer first. This is the fastest way to make the system real.

Status: **implemented for the first operational slice**. SQLite schema/repository operations are implemented, the API workflow stores analyzed listings, uncertain predictions create review tasks, pending tasks can be listed, approve/correct/reject decisions are recorded, and the browser-based `/review` page lets a reviewer act on queued tasks.

Use SQLite as the first database backend.

Default DB path:
```text
data/uamas.db
```

Environment override:
```text
UAMAS_DB_PATH
```

Store:
- listings submitted for analysis,
- predictions and reliability metadata,
- agent outputs,
- review tasks,
- human decisions,
- corrected categories/attributes,
- timestamps and status history.

Default review task statuses:
- `pending`
- `approved`
- `corrected`
- `rejected`

Workflow:
1. User submits listing.
2. System analyzes it.
3. If policy returns `needs_human_review`, create a review task.
4. Reviewer approves, corrects, or rejects the result.
5. Corrections are stored for future evaluation/retraining.

### Phase 3: Multi-Agent Graph
Introduce a broader catalog quality graph while keeping existing `/predict` behavior backward compatible.

Graph flow:
```text
input_listing
  -> classifier_agent
  -> extraction_agent
  -> semantic_critic_agent
  -> policy_agent
      -> auto_accept -> decision_agent
      -> needs_human_review -> human_review_agent -> decision_agent
      -> reject_or_request_clarification -> decision_agent
```

Default graph name:
```text
CatalogQualityGraph
```

Suggested package direction:
```text
reliable_genai/agents/
reliable_genai/catalog_quality_graph.py
```

The existing `ReviewGraphRunner` can remain during transition, but the product-grade orchestration should move toward the catalog quality graph.

Status: **implemented for the first explicit multi-agent slice**. `POST /api/listings/analyze` now runs through `CatalogQualityGraph`; classifier and attribute extraction execute as independent branches, semantic criticism depends on classifier candidates, policy routing conditionally creates human-review work, and the decision agent assembles the existing response contract. The graph falls back to equivalent sequential execution when LangGraph is unavailable. `/predict` remains backward compatible through `ReviewGraphRunner`.

Deferred from this slice:
- activating `reject_or_request_clarification` policy rules,
- async provider clients and distributed execution.

Durable execution history status: **implemented**. Every catalog analysis creates a `workflow_runs` record before agent execution, records safe per-agent summaries and timings in `agent_runs`, links predictions and review tasks transactionally, and marks the workflow `completed` or `failed`. Read-only history APIs and aggregate duration/failure metrics are available.

### Phase 4: API + UI
Add first-class API endpoints while keeping the existing web UI.

New API endpoints:
- `POST /api/listings/analyze`
  - accepts product title and description,
  - returns final decision, agent outputs, reliability metadata, and optional review task id.
- `GET /api/review-queue`
  - returns pending review tasks.
- `GET /api/review-queue/{task_id}`
  - returns full task details.
- `POST /api/review-queue/{task_id}/decision`
  - accepts reviewer action and optional corrected category/attributes.
- `GET /api/metrics`
  - returns operational metrics.
- `GET /api/workflow-runs`
  - lists durable workflow attempts with optional status filtering.
- `GET /api/workflow-runs/{run_id}`
  - returns one workflow and its agent execution history.
- `GET /api/workflow-runs/{run_id}/agents`
  - returns per-agent status, timing, and safe output summaries.

Status: **implemented for the current product slice**. Listing analysis endpoints, review queue JSON endpoints, the `/review` browser UI, and `/api/metrics` operational metrics are available.

New UI route:
- `GET /review`
  - shows pending review tasks,
  - allows approve/correct/reject actions.

Dashboard updates:
- review queue size,
- auto-accept rate,
- correction rate,
- pending task count,
- semantic degraded rate,
- fallback rate.

### Phase 5: Feedback Loop
Use human corrections as evidence.

Status: **implemented through controlled evidence collection and export**. A balanced, disjoint feedback pool feeds deterministic review campaigns. Campaigns preserve natural policy outcomes, add explicit auto-accept controls, hide source reference labels from reviewers, support bounded execution, report aggregate agreement/readiness, and export validated, deduplicated JSONL evidence. Retraining and artifact promotion remain explicit follow-up work.

Add:
- [x] export reviewed examples,
- [x] compare reviewed labels against model predictions,
- [x] report correction rate by category and review reason,
- [x] prepare validated retraining input from reviewed corrections.
- [x] isolate feedback candidates from untouched evaluation data,
- [x] run durable, resumable, category-balanced review campaigns,
- [x] report model/reviewer/reference agreement and retraining readiness.

Retraining should remain explicit:
```bash
.venv/bin/python scripts/train_classifier.py --force
```

Future retraining promotion rule:
1. Train new artifact.
2. Run evaluation.
3. Compare against previous evidence.
4. Promote only if coverage does not regress and correction rate improves.

### Phase 6: Security + Production Hygiene
Status: **implemented for the first production baseline**.

Implemented:
- production fail-closed configuration with distinct administrator, API, and session secrets,
- signed administrator sessions and CSRF-protected browser writes,
- bearer authentication for machine APIs,
- protected dashboard, diagnostics, metrics, review, artifact, and workflow-history routes,
- removal of token-prefix disclosure,
- bounded request bodies, security headers, and sanitized production errors,
- owner-only SQLite and backup file permissions where supported,
- tracked-file secret scanning, dependency auditing, Dependabot, and `SECURITY.md`,
- explicit retention cleanup with dry-run preview, pre-change backup, maintenance audit records, and optional vacuum.

Current retention behavior:
- running workflows are preserved,
- workflows attached to pending reviews are preserved,
- old completed/failed workflow summaries are retained,
- detailed agent rows and workflow error text are pruned after the configured retention period,
- resolved review evidence remains retained until exported-feedback restore verification is implemented and exercised.

Remaining deployment-specific work:
- TLS and reverse-proxy request throttling,
- backup restoration drills,
- external alerting and log aggregation,
- deployment and recovery runbooks for the selected host.

## Public Interfaces and Types

### New Pydantic Models
Add models for:
- `ListingInput`
- `AgentTrace`
- `CatalogQualityDecision`
- `ReviewTask`
- `ReviewDecision`
- `ReviewQueueItem`
- `WorkflowRun`
- `WorkflowRunDetail`
- `AgentRun`

### Analyze Response Shape
`POST /api/listings/analyze` should return:

```json
{
  "listing_id": "string",
  "workflow_run_id": "string",
  "decision": "auto_accept | needs_human_review | reject_or_request_clarification",
  "risk_level": "low | medium | high",
  "explanation": "string",
  "category_set": ["string"],
  "attributes": {},
  "reliability": {},
  "agent_trace": [],
  "review_task_id": "string | null"
}
```

### Review Decision Request Shape
`POST /api/review-queue/{task_id}/decision` should accept:

```json
{
  "action": "approve | correct | reject",
  "corrected_category": "string | null",
  "corrected_attributes": {},
  "notes": "string | null"
}
```

## Policy Rules
Default `PolicyAgent` rules:

- `needs_human_review` if classifier abstained.
- `needs_human_review` if category set size exceeds configured max.
- `needs_human_review` if classifier confidence is below the review threshold.
- `needs_human_review` if semantic status is `ok` and semantic score is below threshold.
- semantic status `degraded` or `disabled` does not independently trigger review.
- `reject_or_request_clarification` remains a reserved contract value until explicit rejection criteria are evaluated.
- `auto_accept` only if:
  - no abstention,
  - category set is within allowed size,
  - confidence is above threshold,
  - no available semantic score is below threshold.

Default risk levels:
- `low`: auto-accepted, high confidence, semantic ok.
- `medium`: accepted but semantic degraded or category set has multiple labels.
- `high`: review/reject path.

## Test Plan

### Unit Tests
Add tests for:
- category mapping from source taxonomy into UAMAS labels,
- ingestion filtering for missing title/category/unmapped labels,
- deterministic train/calibration/test split behavior,
- each agent role in isolation,
- policy decisions for auto-accept/review/reject,
- semantic degraded behavior,
- invalid listing handling,
- review task creation,
- review decision state transitions,
- SQLite persistence read/write behavior.

### Integration Tests
Add tests for:
- real-data ingestion script produces all processed split files and metadata,
- classifier trains successfully on the ingested real-data sample,
- `POST /api/listings/analyze` auto-accept path,
- `POST /api/listings/analyze` review-required path,
- `GET /api/review-queue`,
- `POST /api/review-queue/{task_id}/decision`,
- `/review` renders pending tasks,
- `/dashboard` shows review metrics.

### Regression Tests
Keep existing tests for:
- classifier artifact consistency,
- runtime profile precedence,
- review graph behavior,
- semantic scorer graceful degrade,
- deterministic evaluation artifacts,
- live/mock fallback behavior.

### Acceptance Criteria
The next milestone is complete when:
- real product data is ingested into deterministic train/calibration/test splits,
- dataset provenance and category distribution are recorded,
- classifier artifact and evaluation evidence are refreshed from real data,
- a submitted ambiguous listing creates a persisted review task,
- reviewer can approve/correct/reject it,
- decision is stored and visible through API/UI,
- dashboard shows review queue metrics,
- full test suite passes,
- CI remains green,
- existing `/predict` behavior remains backward compatible.

## Documentation Plan
Update technical docs to clarify:
- UAMAS now targets a real multi-agent catalog QA workflow,
- real dataset source, license/provenance, mapping rules, and known data limitations,
- current implementation status,
- new agent roles,
- persistence model,
- API endpoints,
- review workflow,
- security requirements.

Update README to stay concise:
- describe UAMAS as a seller catalog quality assistant,
- keep quick start,
- link to `TECHNICAL.md`,
- link to this plan.

Update private notes:
- align `private/design_decisions.md` with the new multi-agent product direction,
- keep a plain-language explanation of the human review workflow for non-technical stakeholders.

## Assumptions and Defaults
- The first real product direction is **Seller Catalog Quality Assistant**.
- The first implementation milestone is **real product data ingestion**.
- The preferred first real-data source is **Shopify Product Catalogue**.
- The current six-label taxonomy remains the first mapped target taxonomy.
- Large raw datasets are not committed to git.
- Processed real-data samples may be committed only if license and size allow.
- After real-data ingestion, the next milestone is **persistence + human review queue**.
- SQLite is the first persistence backend.
- Existing demo behavior stays available while the real workflow is added.
- LangGraph remains the orchestration layer.
- Human review is the mechanism that makes the system operational.
- Security cleanup is required before any public deployment.
