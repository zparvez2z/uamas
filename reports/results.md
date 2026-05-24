# UAMAS Evaluation Results

**Generated:** 2026-05-24T13:38:49.474506

**Classifier:** tfidf_logreg_calibrated

**Classifier Runtime:** TRAINED

**LLM Runtime:** LIVE

## LLM Runtime Breakdown

- LIVE calls: 0
- MOCK calls: 0
- FALLBACK_MOCK calls: 31
- Fallback rate: 1.000

## Summary Metrics

| Metric | Value |
|--------|-------|
| Total Products Tested | 31 |
| Target Coverage | 0.900 |
| Calibrated Cumulative Threshold | 0.6933 |
| Empirical Coverage | 0.903 |
| Selective Coverage | 1.0 |
| Top-1 Accuracy | 0.903 |
| Avg Confidence Set Size | 2.16 |
| Avg Non-Abstained Set Size | 2.39 |
| Abstention Rate | 9.7% (3 products) |
| Avg Runtime | 1ms |
| Max Runtime | 1ms |


## Live Validation Notes

This report captures deterministic mock-evaluation output only (`LLM Runtime: MOCK`).

Before stakeholder demos, run a live validation pass (`USE_MOCK_LLM=false`) and append:
- validation date/time,
- number of live prediction requests,
- count of `LIVE` vs fallback runtime paths,
- any abstentions and reasons,
- latency observations for representative requests.

## Interpretation

- **Empirical Coverage**: fraction of all test rows where the true label is in the returned set.
- **Selective Coverage**: coverage after abstentions are removed from the denominator.
- **Calibrated Cumulative Threshold**: cumulative probability mass needed to include labels after calibration.
- **Abstention Rate**: products where the policy refused to return a category set.

## Per-Product Results

| # | Product | True Label | Category Set | Covered | Abstained | Runtime (ms) |
|---|---------|------------|--------------|---------|-----------|--------------|
| 1 | soft T-Shirt for everyday wear | Clothing | Clothing | yes | no | 0.79 |
| 2 | Philips Bluetooth Monitor | Electronics | Electronics, Home | yes | no | 0.65 |
| 3 | JBL compact Vacuum smart | Electronics | Electronics, Sports | yes | no | 0.57 |
| 4 | Nike Sweater in a practical design | Clothing | Clothing, Shoes | yes | no | 0.66 |
| 5 | functional Laundry Basket for everyday h | Home | Home, Sports, Electronics | yes | no | 0.56 |
| 6 | Puma Walking Shoes with grippy support | Shoes | Shoes, Electronics, Home | yes | no | 0.54 |
| 7 | Puma Running Shoes with cushioned suppor | Shoes | Shoes, Clothing, Sports | yes | no | 0.68 |
| 8 | Running Racket for active performance an | Sports | Sports, Electronics | yes | no | 0.55 |
| 9 | calming Shampoo for daily skincare | Beauty | Beauty, Home, Sports | yes | no | 0.55 |
| 10 | Home&More Storage Box with practical mul | Home | Home, Electronics, Shoes | yes | no | 0.56 |
| 11 | rich Shampoo for daily skincare | Beauty | [] | no | yes | 0.53 |
| 12 | Decathlon Fitness Tracker with breathabl | Sports | Sports, Home, Electronics | yes | no | 0.52 |
| 13 | Tom Tailor Shirt with regular fit finish | Clothing | [] | no | yes | 0.57 |
| 14 | sporty Training Shoes for daily comfort | Shoes | Shoes | yes | no | 0.54 |
| 15 | Sony Bluetooth Monitor | Electronics | Electronics, Sports | yes | no | 0.54 |
| 16 | functional Coffee Mug Set for everyday h | Home | Home, Clothing, Sports | yes | no | 0.52 |
| 17 | Puma Running Shoes with breathable suppo | Shoes | Shoes, Sports, Clothing | yes | no | 0.5 |
| 18 | Babolat Yoga Mat with breathable design | Sports | Sports, Shoes, Home | yes | no | 0.56 |
| 19 | Dumbbell Set for active performance and  | Sports | Sports, Electronics, Shoes | yes | no | 0.68 |
| 20 | Face Cream for radiant skin and comfort | Beauty | Beauty, Electronics | yes | no | 0.56 |
| 21 | Water Bottle for active performance and  | Sports | Sports, Electronics | yes | no | 0.55 |
| 22 | Nike Slip-Ons for everyday use | Shoes | Shoes, Sports, Clothing | yes | no | 0.49 |
| 23 | minimal Floor Lamp for everyday home use | Home | Home, Clothing, Electronics | yes | no | 0.51 |
| 24 | Spa Gift Set | Beauty | [] | no | yes | 0.5 |
| 25 | CeraVe Mascara with modern styling | Beauty | Beauty, Home | yes | no | 0.52 |
| 26 | Sony mini Wireless Headphones | Electronics | Electronics, Home, Beauty | yes | no | 0.5 |
| 27 | Jeans in classic Grau style | Clothing | Clothing, Shoes | yes | no | 0.53 |
| 28 | JBL intelligent Wireless Headphones ener | Electronics | Electronics, Sports | yes | no | 0.52 |
| 29 | classic Leggings for everyday wear | Clothing | Clothing | yes | no | 0.49 |
| 30 | Philips Storage Box with practical easy- | Home | Home, Electronics, Beauty | yes | no | 0.49 |
| 31 | Sony sleek Bluetooth Speaker mini | Electronics | Electronics, Sports | yes | no | 0.51 |

## Full JSON Results

```json
{
  "timestamp": "2026-05-24T13:38:49.474506",
  "total_products": 31,
  "classifier_mode": "tfidf_logreg_calibrated",
  "classifier_ready": true,
  "classifier_reason": null,
  "classifier_runtime": "TRAINED",
  "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
  "coverage_threshold": 0.6933126304754237,
  "classifier_artifact_metadata": {},
  "llm_runtime_mode": "LIVE",
  "results": [
    {
      "product_id": 1,
      "title": "soft T-Shirt for everyday wear",
      "true_label": "Clothing",
      "category_set": [
        "Clothing"
      ],
      "top_label": "Clothing",
      "covered": true,
      "top1_correct": true,
      "set_size": 1,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 1,
        "confidence": 0.742978003451626,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.79,
      "abstained": false
    },
    {
      "product_id": 2,
      "title": "Philips Bluetooth Monitor",
      "true_label": "Electronics",
      "category_set": [
        "Electronics",
        "Home"
      ],
      "top_label": "Electronics",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "blue",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.629510016074056,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.65,
      "abstained": false
    },
    {
      "product_id": 3,
      "title": "JBL compact Vacuum smart",
      "true_label": "Electronics",
      "category_set": [
        "Electronics",
        "Sports"
      ],
      "top_label": "Electronics",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6816309386286228,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.57,
      "abstained": false
    },
    {
      "product_id": 4,
      "title": "Nike Sweater in a practical design",
      "true_label": "Clothing",
      "category_set": [
        "Clothing",
        "Shoes"
      ],
      "top_label": "Clothing",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "nike",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6235957213692006,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.66,
      "abstained": false
    },
    {
      "product_id": 5,
      "title": "functional Laundry Basket for everyday home use",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Sports",
        "Electronics"
      ],
      "top_label": "Home",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.5778241116981405,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.56,
      "abstained": false
    },
    {
      "product_id": 6,
      "title": "Puma Walking Shoes with grippy support",
      "true_label": "Shoes",
      "category_set": [
        "Shoes",
        "Electronics",
        "Home"
      ],
      "top_label": "Shoes",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "puma",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.583478838525983,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.54,
      "abstained": false
    },
    {
      "product_id": 7,
      "title": "Puma Running Shoes with cushioned support",
      "true_label": "Shoes",
      "category_set": [
        "Shoes",
        "Clothing",
        "Sports"
      ],
      "top_label": "Shoes",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "puma",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.48961938601043986,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.68,
      "abstained": false
    },
    {
      "product_id": 8,
      "title": "Running Racket for active performance and fitness",
      "true_label": "Sports",
      "category_set": [
        "Sports",
        "Electronics"
      ],
      "top_label": "Sports",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6352238876495672,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.55,
      "abstained": false
    },
    {
      "product_id": 9,
      "title": "calming Shampoo for daily skincare",
      "true_label": "Beauty",
      "category_set": [
        "Beauty",
        "Home",
        "Sports"
      ],
      "top_label": "Beauty",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.567510029674738,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.55,
      "abstained": false
    },
    {
      "product_id": 10,
      "title": "Home&More Storage Box with practical multi-purpose",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Electronics",
        "Shoes"
      ],
      "top_label": "Home",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.4796288350472327,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.56,
      "abstained": false
    },
    {
      "product_id": 11,
      "title": "rich Shampoo for daily skincare",
      "true_label": "Beauty",
      "category_set": [],
      "top_label": null,
      "covered": false,
      "top1_correct": false,
      "set_size": 0,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 0,
        "confidence": 0.424687941828281,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.53,
      "abstained": true
    },
    {
      "product_id": 12,
      "title": "Decathlon Fitness Tracker with breathable design",
      "true_label": "Sports",
      "category_set": [
        "Sports",
        "Home",
        "Electronics"
      ],
      "top_label": "Sports",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.5629896996478495,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.52,
      "abstained": false
    },
    {
      "product_id": 13,
      "title": "Tom Tailor Shirt with regular fit finish",
      "true_label": "Clothing",
      "category_set": [],
      "top_label": null,
      "covered": false,
      "top1_correct": false,
      "set_size": 0,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 0,
        "confidence": 0.386013283974774,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.57,
      "abstained": true
    },
    {
      "product_id": 14,
      "title": "sporty Training Shoes for daily comfort",
      "true_label": "Shoes",
      "category_set": [
        "Shoes"
      ],
      "top_label": "Shoes",
      "covered": true,
      "top1_correct": true,
      "set_size": 1,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 1,
        "confidence": 0.7377698226095631,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.54,
      "abstained": false
    },
    {
      "product_id": 15,
      "title": "Sony Bluetooth Monitor",
      "true_label": "Electronics",
      "category_set": [
        "Electronics",
        "Sports"
      ],
      "top_label": "Electronics",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "blue",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6350957526089742,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.54,
      "abstained": false
    },
    {
      "product_id": 16,
      "title": "functional Coffee Mug Set for everyday home use",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Clothing",
        "Sports"
      ],
      "top_label": "Home",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.5756374334529387,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.52,
      "abstained": false
    },
    {
      "product_id": 17,
      "title": "Puma Running Shoes with breathable support",
      "true_label": "Shoes",
      "category_set": [
        "Shoes",
        "Sports",
        "Clothing"
      ],
      "top_label": "Shoes",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "puma",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.46114370830771984,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.5,
      "abstained": false
    },
    {
      "product_id": 18,
      "title": "Babolat Yoga Mat with breathable design",
      "true_label": "Sports",
      "category_set": [
        "Sports",
        "Shoes",
        "Home"
      ],
      "top_label": "Sports",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.6001812225299203,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.56,
      "abstained": false
    },
    {
      "product_id": 19,
      "title": "Dumbbell Set for active performance and fitness",
      "true_label": "Sports",
      "category_set": [
        "Sports",
        "Electronics",
        "Shoes"
      ],
      "top_label": "Sports",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.581626432768668,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.68,
      "abstained": false
    },
    {
      "product_id": 20,
      "title": "Face Cream for radiant skin and comfort",
      "true_label": "Beauty",
      "category_set": [
        "Beauty",
        "Electronics"
      ],
      "top_label": "Beauty",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6350011140877917,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.56,
      "abstained": false
    },
    {
      "product_id": 21,
      "title": "Water Bottle for active performance and fitness",
      "true_label": "Sports",
      "category_set": [
        "Sports",
        "Electronics"
      ],
      "top_label": "Sports",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6378956597629982,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.55,
      "abstained": false
    },
    {
      "product_id": 22,
      "title": "Nike Slip-Ons for everyday use",
      "true_label": "Shoes",
      "category_set": [
        "Shoes",
        "Sports",
        "Clothing"
      ],
      "top_label": "Shoes",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "nike",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.515726770453842,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.49,
      "abstained": false
    },
    {
      "product_id": 23,
      "title": "minimal Floor Lamp for everyday home use",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Clothing",
        "Electronics"
      ],
      "top_label": "Home",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.5011288522052879,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.51,
      "abstained": false
    },
    {
      "product_id": 24,
      "title": "Spa Gift Set",
      "true_label": "Beauty",
      "category_set": [],
      "top_label": null,
      "covered": false,
      "top1_correct": false,
      "set_size": 0,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 0,
        "confidence": 0.34641550267619164,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.5,
      "abstained": true
    },
    {
      "product_id": 25,
      "title": "CeraVe Mascara with modern styling",
      "true_label": "Beauty",
      "category_set": [
        "Beauty",
        "Home"
      ],
      "top_label": "Beauty",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6183307710234927,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.52,
      "abstained": false
    },
    {
      "product_id": 26,
      "title": "Sony mini Wireless Headphones",
      "true_label": "Electronics",
      "category_set": [
        "Electronics",
        "Home",
        "Beauty"
      ],
      "top_label": "Electronics",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.5630236249071986,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.5,
      "abstained": false
    },
    {
      "product_id": 27,
      "title": "Jeans in classic Grau style",
      "true_label": "Clothing",
      "category_set": [
        "Clothing",
        "Shoes"
      ],
      "top_label": "Clothing",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.672967392557696,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.53,
      "abstained": false
    },
    {
      "product_id": 28,
      "title": "JBL intelligent Wireless Headphones energy-saving",
      "true_label": "Electronics",
      "category_set": [
        "Electronics",
        "Sports"
      ],
      "top_label": "Electronics",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6583700396448608,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.52,
      "abstained": false
    },
    {
      "product_id": 29,
      "title": "classic Leggings for everyday wear",
      "true_label": "Clothing",
      "category_set": [
        "Clothing"
      ],
      "top_label": "Clothing",
      "covered": true,
      "top1_correct": true,
      "set_size": 1,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 1,
        "confidence": 0.7308634238570749,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.49,
      "abstained": false
    },
    {
      "product_id": 30,
      "title": "Philips Storage Box with practical easy-clean",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Electronics",
        "Beauty"
      ],
      "top_label": "Home",
      "covered": true,
      "top1_correct": true,
      "set_size": 3,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.5321698705349392,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.49,
      "abstained": false
    },
    {
      "product_id": 31,
      "title": "Sony sleek Bluetooth Speaker mini",
      "true_label": "Electronics",
      "category_set": [
        "Electronics",
        "Sports"
      ],
      "top_label": "Electronics",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "unknown",
        "color": "blue",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6660538386958839,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": null,
        "classifier_artifact_path": "/workspace/uamas/artifacts/classifier.joblib",
        "coverage_threshold": 0.6933126304754237
      },
      "runtime_ms": 0.51,
      "abstained": false
    }
  ],
  "metrics": {
    "target_coverage": 0.9,
    "calibrated_cumulative_threshold": 0.6933,
    "empirical_coverage": 0.903,
    "selective_coverage": 1.0,
    "top1_accuracy": 0.903,
    "avg_set_size": 2.16,
    "avg_non_abstained_set_size": 2.39,
    "max_set_size": 3,
    "min_set_size": 0,
    "abstention_count": 3,
    "abstention_rate": 0.097,
    "avg_runtime_ms": 0.56,
    "max_runtime_ms": 0.79
  },
  "runtime_breakdown": {
    "live_count": 0,
    "mock_count": 0,
    "fallback_mock_count": 31,
    "fallback_rate": 1.0
  },
  "include_runtime": true
}
```
