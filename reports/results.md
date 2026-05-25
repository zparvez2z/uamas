# UAMAS Evaluation Results

**Generated:** deterministic

**Classifier:** embedding_logreg_calibrated

**Classifier Runtime:** TRAINED

**Artifact Load Status:** rejected

**Artifact Rejection Reason:** classifier artifact alpha does not match runtime alpha

**LLM Runtime:** MOCK

## Review Trigger Reduction Acceptance Check (2026-05-25)

- Runtime mode: `USE_MOCK_LLM=true`, `ENABLE_LANGGRAPH_REVIEW=true`
- Baseline config: `REVIEW_GATE_STRATEGY=legacy`, `REVIEW_SET_SIZE_TRIGGER=3`
- Tuned config: `REVIEW_GATE_STRATEGY=latency_v1`, `REVIEW_SET_SIZE_TRIGGER=4`, `REVIEW_VERY_LOW_CONFIDENCE_FLOOR=0.35`
- Baseline trigger rate: **0.419**
- Tuned trigger rate: **0.065** (target: `<= 0.250`)
- Baseline second-pass rate: **0.419**
- Tuned second-pass rate: **0.065** (aligned with trigger rate)
- Empirical coverage delta (`latency_v1 - legacy`): **0.000** (guardrail: no worse than `-0.010`)

## Review Graph Tuning

- Backend: langgraph
- Available: True
- Gate Strategy: latency_v1
- Very Low Confidence Floor: 0.35
- Trigger Rate: 0.065
- Second-Pass Rate: 0.065
- Cache Hit Rate: 0.000
- Trigger Reasons:
  - abstained: 0
  - very_low_confidence: 2
  - low_confidence_large_set: 0
  - low_confidence: 0
  - large_set: 0

## Summary Metrics

| Metric | Value |
|--------|-------|
| Total Products Tested | 31 |
| Target Coverage | 0.700 |
| Calibrated Cumulative Threshold | 0.6198 |
| Empirical Coverage | 1.000 |
| Selective Coverage | 1.0 |
| Top-1 Accuracy | 1.000 |
| Avg Confidence Set Size | 1.94 |
| Avg Non-Abstained Set Size | 1.94 |
| Abstention Rate | 0.0% (0 products) |

## Interpretation

- **Empirical Coverage**: fraction of all test rows where the true label is in the returned set.
- **Selective Coverage**: coverage after abstentions are removed from the denominator.
- **Calibrated Cumulative Threshold**: cumulative probability mass needed to include labels after calibration.
- **Abstention Rate**: products where the policy refused to return a category set.

## Per-Product Results

| # | Product | True Label | Category Set | Covered | Abstained |
|---|---------|------------|--------------|---------|-----------|
| 1 | soft T-Shirt for everyday wear | Clothing | Clothing | yes | no |
| 2 | Philips Bluetooth Monitor | Electronics | Electronics | yes | no |
| 3 | JBL compact Vacuum smart | Electronics | Electronics | yes | no |
| 4 | Nike Sweater in a practical design | Clothing | Clothing, Shoes | yes | no |
| 5 | functional Laundry Basket for everyday h | Home | Home, Sports | yes | no |
| 6 | Puma Walking Shoes with grippy support | Shoes | Shoes, Electronics | yes | no |
| 7 | Puma Running Shoes with cushioned suppor | Shoes | Shoes, Clothing, Sports | yes | no |
| 8 | Running Racket for active performance an | Sports | Sports | yes | no |
| 9 | calming Shampoo for daily skincare | Beauty | Beauty, Home | yes | no |
| 10 | Home&More Storage Box with practical mul | Home | Home, Electronics, Shoes | yes | no |
| 11 | rich Shampoo for daily skincare | Beauty | Beauty, Home, Clothing | yes | no |
| 12 | Decathlon Fitness Tracker with breathabl | Sports | Sports, Shoes | yes | no |
| 13 | Tom Tailor Shirt with regular fit finish | Clothing | Clothing, Electronics, Beauty | yes | no |
| 14 | sporty Training Shoes for daily comfort | Shoes | Shoes | yes | no |
| 15 | Sony Bluetooth Monitor | Electronics | Electronics | yes | no |
| 16 | functional Coffee Mug Set for everyday h | Home | Home, Clothing | yes | no |
| 17 | Puma Running Shoes with breathable suppo | Shoes | Shoes, Clothing, Sports | yes | no |
| 18 | Babolat Yoga Mat with breathable design | Sports | Sports, Shoes | yes | no |
| 19 | Dumbbell Set for active performance and  | Sports | Sports, Electronics | yes | no |
| 20 | Face Cream for radiant skin and comfort | Beauty | Beauty | yes | no |
| 21 | Water Bottle for active performance and  | Sports | Sports | yes | no |
| 22 | Nike Slip-Ons for everyday use | Shoes | Shoes, Sports, Clothing | yes | no |
| 23 | minimal Floor Lamp for everyday home use | Home | Home, Clothing | yes | no |
| 24 | Spa Gift Set | Beauty | Beauty, Electronics, Home, Clothing | yes | no |
| 25 | CeraVe Mascara with modern styling | Beauty | Beauty, Home | yes | no |
| 26 | Sony mini Wireless Headphones | Electronics | Electronics, Home | yes | no |
| 27 | Jeans in classic Grau style | Clothing | Clothing | yes | no |
| 28 | JBL intelligent Wireless Headphones ener | Electronics | Electronics | yes | no |
| 29 | classic Leggings for everyday wear | Clothing | Clothing | yes | no |
| 30 | Philips Storage Box with practical easy- | Home | Home, Electronics, Beauty | yes | no |
| 31 | Sony sleek Bluetooth Speaker mini | Electronics | Electronics, Beauty | yes | no |

## Full JSON Results

```json
{
  "timestamp": "deterministic",
  "total_products": 31,
  "classifier_mode": "embedding_logreg_calibrated",
  "classifier_ready": true,
  "classifier_reason": "model_type=embedding",
  "classifier_runtime": "TRAINED",
  "classifier_model_type": "embedding",
  "classifier_artifact_load_attempted": true,
  "classifier_artifact_load_status": "rejected",
  "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
  "classifier_artifact_path": "artifacts/classifier.joblib",
  "coverage_threshold": 0.6197909946346115,
  "classifier_artifact_metadata": {},
  "classifier_artifact_format_version": null,
  "classifier_dataset_fingerprint": null,
  "review_graph_backend": "langgraph",
  "review_graph_available": true,
  "review_graph_gate_strategy": "latency_v1",
  "review_graph_very_low_confidence_floor": 0.35,
  "review_graph_trigger_rate": 0.065,
  "review_graph_second_pass_rate": 0.065,
  "review_graph_trigger_reason_counts": {
    "abstained": 0,
    "very_low_confidence": 2,
    "low_confidence_large_set": 0,
    "low_confidence": 0,
    "large_set": 0
  },
  "review_graph_trigger_reason_rates": {
    "abstained": 0.0,
    "very_low_confidence": 0.065,
    "low_confidence_large_set": 0.0,
    "low_confidence": 0.0,
    "large_set": 0.0
  },
  "review_graph_cache_hit_rate": 0.0,
  "review_graph_cached_step_count": 0,
  "llm_runtime_mode": "MOCK",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.7133176190892522,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 2,
      "title": "Philips Bluetooth Monitor",
      "true_label": "Electronics",
      "category_set": [
        "Electronics"
      ],
      "top_label": "Electronics",
      "covered": true,
      "top1_correct": true,
      "set_size": 1,
      "attributes": {
        "brand": "unknown",
        "color": "blue",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.6320395303135132,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 3,
      "title": "JBL compact Vacuum smart",
      "true_label": "Electronics",
      "category_set": [
        "Electronics"
      ],
      "top_label": "Electronics",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.6498986579848766,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.5823729650781936,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 5,
      "title": "functional Laundry Basket for everyday home use",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Sports"
      ],
      "top_label": "Home",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.6021993598815641,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 6,
      "title": "Puma Walking Shoes with grippy support",
      "true_label": "Shoes",
      "category_set": [
        "Shoes",
        "Electronics"
      ],
      "top_label": "Shoes",
      "covered": true,
      "top1_correct": true,
      "set_size": 2,
      "attributes": {
        "brand": "puma",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.523194172092312,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.46482891731000925,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 8,
      "title": "Running Racket for active performance and fitness",
      "true_label": "Sports",
      "category_set": [
        "Sports"
      ],
      "top_label": "Sports",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.6500434530812301,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 9,
      "title": "calming Shampoo for daily skincare",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.4897945594090371,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.43701070848812984,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 11,
      "title": "rich Shampoo for daily skincare",
      "true_label": "Beauty",
      "category_set": [
        "Beauty",
        "Home",
        "Clothing"
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.3440390359571206,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": "very_low_confidence",
        "review_outcome": "first_pass_retained",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 12,
      "title": "Decathlon Fitness Tracker with breathable design",
      "true_label": "Sports",
      "category_set": [
        "Sports",
        "Shoes"
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.5153206048219836,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 13,
      "title": "Tom Tailor Shirt with regular fit finish",
      "true_label": "Clothing",
      "category_set": [
        "Clothing",
        "Electronics",
        "Beauty"
      ],
      "top_label": "Clothing",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.3566874831871658,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.7278714616269216,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 15,
      "title": "Sony Bluetooth Monitor",
      "true_label": "Electronics",
      "category_set": [
        "Electronics"
      ],
      "top_label": "Electronics",
      "covered": true,
      "top1_correct": true,
      "set_size": 1,
      "attributes": {
        "brand": "unknown",
        "color": "blue",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.6479533095366047,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 16,
      "title": "functional Coffee Mug Set for everyday home use",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Clothing"
      ],
      "top_label": "Home",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.561558865240932,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 17,
      "title": "Puma Running Shoes with breathable support",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.4595148945526751,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 18,
      "title": "Babolat Yoga Mat with breathable design",
      "true_label": "Sports",
      "category_set": [
        "Sports",
        "Shoes"
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.5821729595561453,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 19,
      "title": "Dumbbell Set for active performance and fitness",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.5685531649677456,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 20,
      "title": "Face Cream for radiant skin and comfort",
      "true_label": "Beauty",
      "category_set": [
        "Beauty"
      ],
      "top_label": "Beauty",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.6558763481109089,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 21,
      "title": "Water Bottle for active performance and fitness",
      "true_label": "Sports",
      "category_set": [
        "Sports"
      ],
      "top_label": "Sports",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.6532386262278025,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.4356930490370697,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 23,
      "title": "minimal Floor Lamp for everyday home use",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Clothing"
      ],
      "top_label": "Home",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.504735971518365,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 24,
      "title": "Spa Gift Set",
      "true_label": "Beauty",
      "category_set": [
        "Beauty",
        "Electronics",
        "Home",
        "Clothing"
      ],
      "top_label": "Beauty",
      "covered": true,
      "top1_correct": true,
      "set_size": 4,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 4,
        "confidence": 0.30900419324167083,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": "very_low_confidence",
        "review_outcome": "first_pass_retained",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.5981128063640427,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 26,
      "title": "Sony mini Wireless Headphones",
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
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.49769890369122566,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 27,
      "title": "Jeans in classic Grau style",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.6904732511186548,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 28,
      "title": "JBL intelligent Wireless Headphones energy-saving",
      "true_label": "Electronics",
      "category_set": [
        "Electronics"
      ],
      "top_label": "Electronics",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.6580074348653486,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 1,
        "confidence": 0.7305776354644902,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.49681464777052947,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    },
    {
      "product_id": 31,
      "title": "Sony sleek Bluetooth Speaker mini",
      "true_label": "Electronics",
      "category_set": [
        "Electronics",
        "Beauty"
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.6192470638781034,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "classifier_artifact_load_attempted": true,
        "classifier_artifact_load_status": "rejected",
        "classifier_artifact_rejection_reason": "classifier artifact alpha does not match runtime alpha",
        "review_graph_used": false,
        "review_trigger_reason": null,
        "review_outcome": "not_triggered",
        "coverage_threshold": 0.6197909946346115
      },
      "abstained": false
    }
  ],
  "metrics": {
    "target_coverage": 0.7,
    "calibrated_cumulative_threshold": 0.6198,
    "empirical_coverage": 1.0,
    "selective_coverage": 1.0,
    "top1_accuracy": 1.0,
    "avg_set_size": 1.94,
    "avg_non_abstained_set_size": 1.94,
    "max_set_size": 4,
    "min_set_size": 1,
    "abstention_count": 0,
    "abstention_rate": 0.0
  },
  "runtime_breakdown": {
    "live_count": 0,
    "mock_count": 31,
    "fallback_mock_count": 0,
    "fallback_rate": 0.0
  },
  "include_runtime": false
}
```
