# UAMAS Demo Walkthrough

This document provides concrete test cases and expected behaviors for a live demo.

## Quick Demo (3 minutes)

### Setup
```bash
# Terminal 1: Start the web server
cd /home/pz/projects/uamas
.venv/bin/python -m uvicorn app.main:app --reload

# Terminal 2: Open browser
# Navigate to http://localhost:8000
```

---

## Test Case 1: High-Confidence Product (Electronics)

**Scenario:** Clear, unambiguous product

**Input:**
- Title: `Samsung 65-inch 4K Smart TV`
- Description: `Ultra HD television with HDR10+ support, 120Hz refresh rate, smart apps`

**Expected Output:**
- Runtime: **LIVE** (green badge)
- Category Set: `["electronics"]` or `["electronics", "home appliances"]` (small set)
- Attributes: 
  - Brand: `Samsung`
  - Color: `Black` (inferred)
  - Material: `Metal and plastic`
  - Size: `65 inch`
- Confidence: High (set size ≤ 2)
- No abstention

**Why this works:** Electronics terminology is clear and unambiguous.

---

## Test Case 2: Moderate-Confidence Product (Hybrid Kitchen Appliance)

**Scenario:** Product that fits multiple categories

**Input:**
- Title: `Multi-function Instant Pot Duo`
- Description: `Electric pressure cooker that also functions as slow cooker, rice cooker, steamer`

**Expected Output:**
- Runtime: **LIVE**
- Category Set: `["kitchen appliances", "cookware", "small appliances"]` (medium set, 2-3 items)
- Attributes:
  - Brand: `Instant Pot`
  - Material: `Stainless steel`
  - Size: `6-quart` (inferred from model)
- Confidence: Moderate (set size 2-3)
- No abstention

**Why this works:** Multi-function products naturally have larger confidence sets due to ambiguity.

---

## Test Case 3: Low-Confidence / Abstention Case

**Scenario:** Vague product that triggers abstention policy

**Input:**
- Title: `Thing`
- Description: `A product`

**Expected Output:**
- Runtime: **LIVE**
- Category Set: `[]` (empty)
- Attributes: All `"unknown"`
- Confidence: 
  - `abstained: true`
  - `policy_action: "abstain"`
  - `reason: "Insufficient product information or confidence set exceeds threshold"`
- No attributes extracted

**Why this works:** Insufficient product description triggers the abstention policy (empty set rejected as unreliable).

---

## Test Case 4: Check Runtime Diagnostics

**Scenario:** Verify API connectivity and mock fallback

**In Browser Console (F12):**
```javascript
// Check current runtime status
fetch('http://localhost:8000/diagnostics').then(r => r.json()).then(d => console.log(d))
```

**Expected Output:**
```json
{
  "mode": "LIVE",
  "last_runtime": "LIVE",
  "token_present": true,
  "endpoint": "https://models.github.ai/inference"
}
```

**If GitHub Models is down or token invalid, you should see:**
```json
{
  "mode": "LIVE",
  "last_runtime": "FALLBACK_MOCK",
  "token_present": true,
  "endpoint": "https://models.github.ai/inference"
}
```

---

## Running Full Evaluation

To generate a full report with 8 diverse test products:

```bash
cd /home/pz/projects/uamas
.venv/bin/python scripts/evaluate.py
```

This generates `reports/results.md` with:
- Summary metrics (avg set size, abstention rate, runtime)
- Per-product breakdown
- Full JSON results for analysis

---

## Demo Talking Points

### Point 1: Uncertainty Quantification
*"Most ML systems output a single prediction. We output a **confidence set** — a set of plausible categories rather than guessing one. If we're confident, the set is small (1-2 items). If we're uncertain, the set is larger."*

**Demo:** Contrast Test Case 1 (small set) with Test Case 2 (larger set).

### Point 2: Reliability Policy
*"We have a **policy layer** that refuses to predict if uncertainty is too high (empty set or set exceeds threshold). This prevents overconfident wrong predictions."*

**Demo:** Show Test Case 3 abstaining and explain why.

### Point 3: Live LLM Integration
*"The pipeline uses **GitHub Models (GPT-4.1)** via live API to extract structured attributes (brand, color, material, size). The runtime badge shows whether we're using the live API or fallback mock mode."*

**Demo:** Point to green LIVE badge; run diagnostics endpoint to show token is present.

### Point 4: Production-Ready Reliability
*"Every prediction includes **reliability metadata**: confidence level, coverage target (alpha), whether we abstained, and why. This gives stakeholders full transparency."*

**Demo:** Inspect the "Reliability Metadata" section in the UI response.

---

## Troubleshooting

### "MOCK" or "FALLBACK_MOCK" badge appears
- **Cause:** GitHub token is missing or invalid
- **Fix:** Check `.env` file has `GITHUB_TOKEN` with valid personal access token

### Empty response / error
- **Cause:** `.venv` not activated or dependencies not installed
- **Fix:** Run `pip install -r requirements.txt` in activated `.venv`

### Slow responses (>5s)
- **Cause:** LLM API latency (normal for first call)
- **Fix:** Subsequent calls within same session use cache; this is expected

---

## Expected Metrics (from evaluate.py)

After running `scripts/evaluate.py`, you should see approximately:
- **Avg Set Size:** 1.5 - 2.5 (tight confidence sets for clear products)
- **Abstention Rate:** 10-20% (only truly vague products)
- **Avg Runtime:** 2-4 seconds (includes LLM latency)

If metrics show:
- **Set size >> 3:** Classifier may need tuning
- **Abstention rate > 50%:** Alpha (confidence threshold) may be too strict
- **Runtime >> 5s:** LLM API degradation or network latency
