# UAMAS Evaluation Results

**Generated:** deterministic

**Classifier:** tfidf_logreg_calibrated

**Classifier Runtime:** ARTIFACT

**LLM Runtime:** MOCK

## Summary Metrics

| Metric | Value |
|--------|-------|
| Total Products Tested | 31 |
| Target Coverage | 0.700 |
| Calibrated Cumulative Threshold | 0.6376 |
| Empirical Coverage | 1.000 |
| Selective Coverage | 1.0 |
| Top-1 Accuracy | 1.000 |
| Avg Confidence Set Size | 2.0 |
| Avg Non-Abstained Set Size | 2.0 |
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
| 2 | Philips Bluetooth Monitor | Electronics | Electronics, Home | yes | no |
| 3 | JBL compact Vacuum smart | Electronics | Electronics | yes | no |
| 4 | Nike Sweater in a practical design | Clothing | Clothing, Shoes | yes | no |
| 5 | functional Laundry Basket for everyday h | Home | Home, Sports | yes | no |
| 6 | Puma Walking Shoes with grippy support | Shoes | Shoes, Electronics | yes | no |
| 7 | Puma Running Shoes with cushioned suppor | Shoes | Shoes, Clothing, Sports | yes | no |
| 8 | Running Racket for active performance an | Sports | Sports, Electronics | yes | no |
| 9 | calming Shampoo for daily skincare | Beauty | Beauty, Home | yes | no |
| 10 | Home&More Storage Box with practical mul | Home | Home, Electronics, Shoes | yes | no |
| 11 | rich Shampoo for daily skincare | Beauty | Beauty, Home, Clothing | yes | no |
| 12 | Decathlon Fitness Tracker with breathabl | Sports | Sports, Home | yes | no |
| 13 | Tom Tailor Shirt with regular fit finish | Clothing | Clothing, Electronics, Beauty | yes | no |
| 14 | sporty Training Shoes for daily comfort | Shoes | Shoes | yes | no |
| 15 | Sony Bluetooth Monitor | Electronics | Electronics, Sports | yes | no |
| 16 | functional Coffee Mug Set for everyday h | Home | Home, Clothing | yes | no |
| 17 | Puma Running Shoes with breathable suppo | Shoes | Shoes, Sports, Clothing | yes | no |
| 18 | Babolat Yoga Mat with breathable design | Sports | Sports, Shoes | yes | no |
| 19 | Dumbbell Set for active performance and  | Sports | Sports, Electronics | yes | no |
| 20 | Face Cream for radiant skin and comfort | Beauty | Beauty, Electronics | yes | no |
| 21 | Water Bottle for active performance and  | Sports | Sports | yes | no |
| 22 | Nike Slip-Ons for everyday use | Shoes | Shoes, Sports, Clothing | yes | no |
| 23 | minimal Floor Lamp for everyday home use | Home | Home, Clothing, Electronics | yes | no |
| 24 | Spa Gift Set | Beauty | Beauty, Home, Sports | yes | no |
| 25 | CeraVe Mascara with modern styling | Beauty | Beauty, Home | yes | no |
| 26 | Sony mini Wireless Headphones | Electronics | Electronics, Home | yes | no |
| 27 | Jeans in classic Grau style | Clothing | Clothing | yes | no |
| 28 | JBL intelligent Wireless Headphones ener | Electronics | Electronics | yes | no |
| 29 | classic Leggings for everyday wear | Clothing | Clothing | yes | no |
| 30 | Philips Storage Box with practical easy- | Home | Home, Electronics | yes | no |
| 31 | Sony sleek Bluetooth Speaker mini | Electronics | Electronics | yes | no |

## Full JSON Results

```json
{
  "timestamp": "deterministic",
  "total_products": 31,
  "classifier_mode": "tfidf_logreg_calibrated",
  "classifier_ready": true,
  "classifier_reason": null,
  "classifier_runtime": "ARTIFACT",
  "classifier_artifact_path": "artifacts/classifier.joblib",
  "coverage_threshold": 0.6376491214016037,
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
        "confidence": 0.7429780034516262,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.6295100160740561,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.6816309386286228,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.6235957213692008,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.5778241116981411,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.5834788385259829,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.4896193860104397,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.6352238876495673,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.5675100296747375,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.47962883504723347,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.42468794182828046,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
      },
      "abstained": false
    },
    {
      "product_id": 12,
      "title": "Decathlon Fitness Tracker with breathable design",
      "true_label": "Sports",
      "category_set": [
        "Sports",
        "Home"
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
        "confidence": 0.5629896996478495,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.3860132839747743,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.737769822609563,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.6350957526089742,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.5756374334529396,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.46114370830771967,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.6001812225299202,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.581626432768668,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
      },
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.6350011140877913,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.6378956597629981,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.5157267704538417,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.5011288522052885,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
      },
      "abstained": false
    },
    {
      "product_id": 24,
      "title": "Spa Gift Set",
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
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.34641550267619114,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.6183307710234923,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.5630236249071985,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.6729673925576961,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.6583700396448608,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
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
        "confidence": 0.730863423857075,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
      },
      "abstained": false
    },
    {
      "product_id": 30,
      "title": "Philips Storage Box with practical easy-clean",
      "true_label": "Home",
      "category_set": [
        "Home",
        "Electronics"
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
        "confidence": 0.5321698705349399,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
      },
      "abstained": false
    },
    {
      "product_id": 31,
      "title": "Sony sleek Bluetooth Speaker mini",
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
        "confidence": 0.666053838695884,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "MOCK",
        "llm_model": "openai/gpt-4.1",
        "classifier_runtime": "ARTIFACT",
        "classifier_reason": null,
        "classifier_artifact_path": "artifacts/classifier.joblib",
        "coverage_threshold": 0.6376491214016037
      },
      "abstained": false
    }
  ],
  "metrics": {
    "target_coverage": 0.7,
    "calibrated_cumulative_threshold": 0.6376,
    "empirical_coverage": 1.0,
    "selective_coverage": 1.0,
    "top1_accuracy": 1.0,
    "avg_set_size": 2.0,
    "avg_non_abstained_set_size": 2.0,
    "max_set_size": 3,
    "min_set_size": 1,
    "abstention_count": 0,
    "abstention_rate": 0.0
  },
  "include_runtime": false
}
```
