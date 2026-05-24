# UAMAS Evaluation Results

**Generated:** deterministic

**Classifier:** embedding_logreg_calibrated

**Classifier Runtime:** TRAINED

**LLM Runtime:** MOCK

## Summary Metrics

| Metric | Value |
|--------|-------|
| Total Products Tested | 31 |
| Target Coverage | 0.900 |
| Calibrated Cumulative Threshold | 0.6908 |
| Empirical Coverage | 0.903 |
| Selective Coverage | 1.0 |
| Top-1 Accuracy | 0.903 |
| Avg Confidence Set Size | 2.19 |
| Avg Non-Abstained Set Size | 2.43 |
| Abstention Rate | 9.7% (3 products) |

## Interpretation

- **Empirical Coverage**: fraction of all test rows where the true label is in the returned set.
- **Selective Coverage**: coverage after abstentions are removed from the denominator.
- **Calibrated Cumulative Threshold**: cumulative probability mass needed to include labels after calibration.
- **Abstention Rate**: products where the policy refused to return a category set.

## Per-Product Results

| # | Product | True Label | Category Set | Covered | Abstained |
|---|---------|------------|--------------|---------|-----------|
| 1 | soft T-Shirt for everyday wear | Clothing | Clothing | yes | no |
| 2 | Philips Bluetooth Monitor | Electronics | Electronics, Home | yes | no |
| 3 | JBL compact Vacuum smart | Electronics | Electronics, Beauty | yes | no |
| 4 | Nike Sweater in a practical design | Clothing | Clothing, Shoes, Home | yes | no |
| 5 | functional Laundry Basket for everyday h | Home | Home, Sports | yes | no |
| 6 | Puma Walking Shoes with grippy support | Shoes | Shoes, Electronics, Beauty | yes | no |
| 7 | Puma Running Shoes with cushioned suppor | Shoes | Shoes, Clothing, Sports | yes | no |
| 8 | Running Racket for active performance an | Sports | Sports, Shoes | yes | no |
| 9 | calming Shampoo for daily skincare | Beauty | Beauty, Home, Sports | yes | no |
| 10 | Home&More Storage Box with practical mul | Home | Home, Electronics, Shoes | yes | no |
| 11 | rich Shampoo for daily skincare | Beauty | [] | no | yes |
| 12 | Decathlon Fitness Tracker with breathabl | Sports | Sports, Shoes, Home | yes | no |
| 13 | Tom Tailor Shirt with regular fit finish | Clothing | [] | no | yes |
| 14 | sporty Training Shoes for daily comfort | Shoes | Shoes | yes | no |
| 15 | Sony Bluetooth Monitor | Electronics | Electronics, Beauty | yes | no |
| 16 | functional Coffee Mug Set for everyday h | Home | Home, Clothing, Beauty | yes | no |
| 17 | Puma Running Shoes with breathable suppo | Shoes | Shoes, Clothing, Sports | yes | no |
| 18 | Babolat Yoga Mat with breathable design | Sports | Sports, Shoes, Home | yes | no |
| 19 | Dumbbell Set for active performance and  | Sports | Sports, Electronics, Shoes | yes | no |
| 20 | Face Cream for radiant skin and comfort | Beauty | Beauty, Shoes | yes | no |
| 21 | Water Bottle for active performance and  | Sports | Sports, Shoes | yes | no |
| 22 | Nike Slip-Ons for everyday use | Shoes | Shoes, Sports, Clothing | yes | no |
| 23 | minimal Floor Lamp for everyday home use | Home | Home, Clothing, Beauty | yes | no |
| 24 | Spa Gift Set | Beauty | [] | no | yes |
| 25 | CeraVe Mascara with modern styling | Beauty | Beauty, Home, Clothing | yes | no |
| 26 | Sony mini Wireless Headphones | Electronics | Electronics, Home, Sports | yes | no |
| 27 | Jeans in classic Grau style | Clothing | Clothing, Shoes | yes | no |
| 28 | JBL intelligent Wireless Headphones ener | Electronics | Electronics, Beauty | yes | no |
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
  "classifier_artifact_path": "artifacts/classifier.joblib",
  "coverage_threshold": 0.6907956431930701,
  "classifier_artifact_metadata": {},
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 1,
        "confidence": 0.713317619089252,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
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
        "confidence": 0.632039530313513,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 3,
      "title": "JBL compact Vacuum smart",
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
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6498986579848759,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 4,
      "title": "Nike Sweater in a practical design",
      "true_label": "Clothing",
      "category_set": [
        "Clothing",
        "Shoes",
        "Home"
      ],
      "top_label": "Clothing",
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
        "confidence": 0.5823729650781935,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6021993598815638,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 6,
      "title": "Puma Walking Shoes with grippy support",
      "true_label": "Shoes",
      "category_set": [
        "Shoes",
        "Electronics",
        "Beauty"
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
        "confidence": 0.523194172092311,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.46482891731000886,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 8,
      "title": "Running Racket for active performance and fitness",
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
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
        "coverage_threshold": 0.6907956431930701
      },
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
        "confidence": 0.4897945594090369,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.43701070848812945,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
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
        "confidence": 0.3440390359571207,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": true
    },
    {
      "product_id": 12,
      "title": "Decathlon Fitness Tracker with breathable design",
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
        "confidence": 0.5153206048219838,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
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
        "confidence": 0.3566874831871661,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
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
        "confidence": 0.7278714616269213,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 15,
      "title": "Sony Bluetooth Monitor",
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6479533095366042,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 16,
      "title": "functional Coffee Mug Set for everyday home use",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Clothing",
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
        "confidence": 0.5615588652409318,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.4595148945526748,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
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
        "confidence": 0.5821729595561456,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
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
        "confidence": 0.5685531649677454,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 20,
      "title": "Face Cream for radiant skin and comfort",
      "true_label": "Beauty",
      "category_set": [
        "Beauty",
        "Shoes"
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
        "confidence": 0.6558763481109088,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 21,
      "title": "Water Bottle for active performance and fitness",
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6532386262278024,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.43569304903706935,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 23,
      "title": "minimal Floor Lamp for everyday home use",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Clothing",
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
        "confidence": 0.5047359715183646,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
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
        "confidence": 0.30900419324167083,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": true
    },
    {
      "product_id": 25,
      "title": "CeraVe Mascara with modern styling",
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.5981128063640424,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 26,
      "title": "Sony mini Wireless Headphones",
      "true_label": "Electronics",
      "category_set": [
        "Electronics",
        "Home",
        "Sports"
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
        "confidence": 0.4976989036912261,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
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
        "confidence": 0.6904732511186544,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    },
    {
      "product_id": 28,
      "title": "JBL intelligent Wireless Headphones energy-saving",
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
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6580074348653483,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 1,
        "confidence": 0.73057763546449,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 3,
        "confidence": 0.49681464777052914,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
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
        "alpha": 0.1,
        "coverage_target": 0.9,
        "set_size": 2,
        "confidence": 0.6192470638781029,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "TRAINED",
        "classifier_reason": "model_type=embedding",
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "classifier_model_type": "embedding",
        "coverage_threshold": 0.6907956431930701
      },
      "abstained": false
    }
  ],
  "metrics": {
    "target_coverage": 0.9,
    "calibrated_cumulative_threshold": 0.6908,
    "empirical_coverage": 0.903,
    "selective_coverage": 1.0,
    "top1_accuracy": 0.903,
    "avg_set_size": 2.19,
    "avg_non_abstained_set_size": 2.43,
    "max_set_size": 3,
    "min_set_size": 0,
    "abstention_count": 3,
    "abstention_rate": 0.097
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
