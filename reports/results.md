# UAMAS Evaluation Results

**Generated:** 2026-05-05T15:20:56.803769

## Summary Metrics

| Metric | Value |
|--------|-------|
| Total Products Tested | 8 |
| Avg Confidence Set Size | 1.0 |
| Max Set Size | 3 |
| Min Set Size | 0 |
| Abstention Rate | 62.0% (5 products) |
| Avg Runtime | 1796ms |
| Max Runtime | 2759ms |

## Interpretation

- **Confidence Set Size**: Smaller sets indicate higher confidence; larger sets indicate uncertainty
- **Abstention Rate**: Products where the pipeline refused to predict (set too large or empty)
- **Runtime**: Includes LLM API latency for attribute extraction

## Per-Product Results

| # | Product | Set Size | Abstained | Runtime (ms) |
|---|---------|----------|-----------|---------------|
| 1 | Samsung 65-inch 4K Smart TV | 3 | — | 1898.58 |
| 2 | Multi-function Instant Pot Duo | 0 | ✓ | 1697.86 |
| 3 | Nike Air Max Running Shoes - Men's | 2 | — | 2117.72 |
| 4 | IKEA Billy Bookcase - White | 0 | ✓ | 2759.23 |
| 5 | Thing | 0 | ✓ | 2073.4 |
| 6 | L'Oreal Paris Revitalift Anti-Wrinkle Cr | 3 | — | 1673.1 |
| 7 | Dyson V15 Detect Cordless Vacuum | 0 | ✓ | 1038.37 |
| 8 | Yonex Badminton Racket - Professional Gr | 0 | ✓ | 1110.41 |

## Full JSON Results

```json
{
  "timestamp": "2026-05-05T15:20:56.803769",
  "total_products": 8,
  "results": [
    {
      "product_id": 1,
      "title": "Samsung 65-inch 4K Smart TV",
      "description": "Ultra HD television with HDR10+ support, 120Hz refresh rate, smart apps...",
      "category_set": [
        "Electronics",
        "Shoes",
        "Clothing"
      ],
      "set_size": 3,
      "attributes": {
        "brand": "Samsung",
        "color": "unknown",
        "material": "unknown",
        "size": "65-inch"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.5000000000000001,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "LIVE",
        "llm_model": "openai/gpt-4.1"
      },
      "runtime_ms": 1898.58,
      "abstained": false
    },
    {
      "product_id": 2,
      "title": "Multi-function Instant Pot Duo",
      "description": "Electric pressure cooker that also functions as slow cooker, rice cooker, steame...",
      "category_set": [],
      "set_size": 0,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 0,
        "confidence": 0.16666666666666669,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "LIVE",
        "llm_model": "openai/gpt-4.1"
      },
      "runtime_ms": 1697.86,
      "abstained": true
    },
    {
      "product_id": 3,
      "title": "Nike Air Max Running Shoes - Men's",
      "description": "Lightweight cushioned running shoe with mesh upper, black and white colorway...",
      "category_set": [
        "Shoes",
        "Clothing"
      ],
      "set_size": 2,
      "attributes": {
        "brand": "Nike",
        "color": "black and white",
        "material": "mesh",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 2,
        "confidence": 0.6428571428571427,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "LIVE",
        "llm_model": "openai/gpt-4.1"
      },
      "runtime_ms": 2117.72,
      "abstained": false
    },
    {
      "product_id": 4,
      "title": "IKEA Billy Bookcase - White",
      "description": "5-shelf wooden bookcase, flat-pack assembly, dimensions 80x28x106 cm...",
      "category_set": [],
      "set_size": 0,
      "attributes": {
        "brand": "IKEA",
        "color": "White",
        "material": "Wood",
        "size": "80x28x106 cm"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 0,
        "confidence": 0.16666666666666669,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "LIVE",
        "llm_model": "openai/gpt-4.1"
      },
      "runtime_ms": 2759.23,
      "abstained": true
    },
    {
      "product_id": 5,
      "title": "Thing",
      "description": "A product...",
      "category_set": [],
      "set_size": 0,
      "attributes": {
        "brand": "unknown",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 0,
        "confidence": 0.16666666666666669,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "LIVE",
        "llm_model": "openai/gpt-4.1"
      },
      "runtime_ms": 2073.4,
      "abstained": true
    },
    {
      "product_id": 6,
      "title": "L'Oreal Paris Revitalift Anti-Wrinkle Cream",
      "description": "Moisturizing facial cream with collagen-boost formula for mature skin...",
      "category_set": [
        "Beauty",
        "Shoes",
        "Clothing"
      ],
      "set_size": 3,
      "attributes": {
        "brand": "L'Oreal Paris",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 3,
        "confidence": 0.5,
        "abstained": false,
        "reason": null,
        "policy_action": "set_output",
        "llm_runtime": "LIVE",
        "llm_model": "openai/gpt-4.1"
      },
      "runtime_ms": 1673.1,
      "abstained": false
    },
    {
      "product_id": 7,
      "title": "Dyson V15 Detect Cordless Vacuum",
      "description": "Lightweight stick vacuum with laser dust detection, 60-min battery, HEPA filter...",
      "category_set": [],
      "set_size": 0,
      "attributes": {
        "brand": "Dyson",
        "color": "unknown",
        "material": "unknown",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 0,
        "confidence": 0.16666666666666669,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "LIVE",
        "llm_model": "openai/gpt-4.1"
      },
      "runtime_ms": 1038.37,
      "abstained": true
    },
    {
      "product_id": 8,
      "title": "Yonex Badminton Racket - Professional Grade",
      "description": "Lightweight carbon composite frame, grip tape, strung with synthetic strings...",
      "category_set": [],
      "set_size": 0,
      "attributes": {
        "brand": "Yonex",
        "color": "unknown",
        "material": "carbon composite",
        "size": "unknown"
      },
      "reliability": {
        "alpha": 0.3,
        "coverage_target": 0.7,
        "set_size": 0,
        "confidence": 0.16666666666666669,
        "abstained": true,
        "reason": "Prediction set outside usability constraints",
        "policy_action": "abstain",
        "llm_runtime": "LIVE",
        "llm_model": "openai/gpt-4.1"
      },
      "runtime_ms": 1110.41,
      "abstained": true
    }
  ],
  "metrics": {
    "avg_set_size": 1.0,
    "max_set_size": 3,
    "min_set_size": 0,
    "abstention_count": 5,
    "abstention_rate": 0.62,
    "avg_runtime_ms": 1796.08,
    "max_runtime_ms": 2759.23
  }
}
```
