#!/usr/bin/env python3
"""
Evaluation harness for the UAMAS reliability pipeline.
Tests the pipeline on diverse product inputs and collects metrics.
"""

import sys
import time
import json
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from reliable_genai import ReliabilityPipeline, ProductInput


def load_test_dataset():
    """Return a curated set of test products covering different scenarios."""
    return [
        # Scenario 1: Clear electronics
        ProductInput(
            title="Samsung 65-inch 4K Smart TV",
            description="Ultra HD television with HDR10+ support, 120Hz refresh rate, smart apps"
        ),
        # Scenario 2: Ambiguous/hybrid product
        ProductInput(
            title="Multi-function Instant Pot Duo",
            description="Electric pressure cooker that also functions as slow cooker, rice cooker, steamer"
        ),
        # Scenario 3: Fashion/apparel (fewer attributes)
        ProductInput(
            title="Nike Air Max Running Shoes - Men's",
            description="Lightweight cushioned running shoe with mesh upper, black and white colorway"
        ),
        # Scenario 4: Home goods
        ProductInput(
            title="IKEA Billy Bookcase - White",
            description="5-shelf wooden bookcase, flat-pack assembly, dimensions 80x28x106 cm"
        ),
        # Scenario 5: Generic/vague (should test abstention)
        ProductInput(
            title="Thing",
            description="A product"
        ),
        # Scenario 6: Beauty/personal care
        ProductInput(
            title="L'Oreal Paris Revitalift Anti-Wrinkle Cream",
            description="Moisturizing facial cream with collagen-boost formula for mature skin"
        ),
        # Scenario 7: Kitchen appliances
        ProductInput(
            title="Dyson V15 Detect Cordless Vacuum",
            description="Lightweight stick vacuum with laser dust detection, 60-min battery, HEPA filter"
        ),
        # Scenario 8: Sports equipment
        ProductInput(
            title="Yonex Badminton Racket - Professional Grade",
            description="Lightweight carbon composite frame, grip tape, strung with synthetic strings"
        ),
    ]


def run_evaluation(use_mock=False, alpha=None, max_set_size=None):
    """
    Run the pipeline on test dataset and collect metrics.
    
    Args:
        use_mock: If True, uses mock LLM instead of live GitHub Models
        alpha: Override confidence level (default from env)
        max_set_size: Override max set size (default from env)
    
    Returns:
        dict with aggregated results
    """
    print("[INFO] Initializing pipeline...")
    
    # Temporarily override environment for evaluation
    if alpha is not None:
        os.environ["ALPHA"] = str(alpha)
    if max_set_size is not None:
        os.environ["MAX_SET_SIZE"] = str(max_set_size)
    
    pipeline = ReliabilityPipeline()
    
    # Override mock mode if requested
    if use_mock:
        pipeline.llm_client.use_mock = True
        print("[INFO] Using MOCK LLM mode")
    else:
        print("[INFO] Using LIVE GitHub Models")
    
    dataset = load_test_dataset()
    results = []
    
    print(f"\n[INFO] Running evaluation on {len(dataset)} products...\n")
    
    for idx, product in enumerate(dataset, 1):
        print(f"[{idx}/{len(dataset)}] Predicting: {product.title[:50]}...")
        
        start = time.time()
        response = pipeline.predict(product)
        elapsed = time.time() - start
        
        result_entry = {
            "product_id": idx,
            "title": product.title,
            "description": product.description[:80] + "...",
            "category_set": response.category_set,
            "set_size": len(response.category_set),
            "attributes": response.attributes.model_dump(),
            "reliability": response.reliability.model_dump(),
            "runtime_ms": round(elapsed * 1000, 2),
            "abstained": response.reliability.abstained,
        }
        results.append(result_entry)
        
        print(f"    → Set: {response.category_set} | Size: {len(response.category_set)} | Abstained: {response.reliability.abstained} | {elapsed:.3f}s")
    
    # Aggregate metrics
    aggregated = {
        "timestamp": datetime.now().isoformat(),
        "total_products": len(results),
        "results": results,
        "metrics": {
            "avg_set_size": round(sum(r["set_size"] for r in results) / len(results), 2),
            "max_set_size": max(r["set_size"] for r in results),
            "min_set_size": min(r["set_size"] for r in results),
            "abstention_count": sum(1 for r in results if r["abstained"]),
            "abstention_rate": round(sum(1 for r in results if r["abstained"]) / len(results), 2),
            "avg_runtime_ms": round(sum(r["runtime_ms"] for r in results) / len(results), 2),
            "max_runtime_ms": max(r["runtime_ms"] for r in results),
        }
    }
    
    return aggregated


def save_results(aggregated, output_path="reports/results.md"):
    """Save aggregated results to markdown report."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    metrics = aggregated["metrics"]
    
    with open(output_path, "w") as f:
        f.write("# UAMAS Evaluation Results\n\n")
        f.write(f"**Generated:** {aggregated['timestamp']}\n\n")
        
        f.write("## Summary Metrics\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total Products Tested | {aggregated['total_products']} |\n")
        f.write(f"| Avg Confidence Set Size | {metrics['avg_set_size']} |\n")
        f.write(f"| Max Set Size | {metrics['max_set_size']} |\n")
        f.write(f"| Min Set Size | {metrics['min_set_size']} |\n")
        f.write(f"| Abstention Rate | {metrics['abstention_rate']*100:.1f}% ({metrics['abstention_count']} products) |\n")
        f.write(f"| Avg Runtime | {metrics['avg_runtime_ms']:.0f}ms |\n")
        f.write(f"| Max Runtime | {metrics['max_runtime_ms']:.0f}ms |\n\n")
        
        f.write("## Interpretation\n\n")
        f.write("- **Confidence Set Size**: Smaller sets indicate higher confidence; larger sets indicate uncertainty\n")
        f.write("- **Abstention Rate**: Products where the pipeline refused to predict (set too large or empty)\n")
        f.write("- **Runtime**: Includes LLM API latency for attribute extraction\n\n")
        
        f.write("## Per-Product Results\n\n")
        f.write("| # | Product | Set Size | Abstained | Runtime (ms) |\n")
        f.write("|---|---------|----------|-----------|---------------|\n")
        
        for r in aggregated["results"]:
            abstain_mark = "✓" if r["abstained"] else "—"
            f.write(f"| {r['product_id']} | {r['title'][:40]} | {r['set_size']} | {abstain_mark} | {r['runtime_ms']} |\n")
        
        f.write("\n## Full JSON Results\n\n")
        f.write("```json\n")
        f.write(json.dumps(aggregated, indent=2))
        f.write("\n```\n")
    
    print(f"\n[INFO] Results saved to {output_path}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Load environment from project root, overriding existing variables
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    load_dotenv(dotenv_path=str(env_file), override=True)
    
    try:
        aggregated = run_evaluation()
        save_results(aggregated)
        
        # Print summary to console
        metrics = aggregated["metrics"]
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"Avg Set Size: {metrics['avg_set_size']}")
        print(f"Abstention Rate: {metrics['abstention_rate']*100:.1f}%")
        print(f"Avg Runtime: {metrics['avg_runtime_ms']:.0f}ms")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
