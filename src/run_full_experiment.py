#!/usr/bin/env python3
"""
Full Experiment Runner for Drawing Benchmark
Runs complete benchmark on all models and generates comprehensive analysis
"""

import os
import json
import time
from datetime import datetime
from test_llm import run_batch_test, load_dataset

def run_full_experiment():
    """Run complete experiment on all models and prompts"""
    
    print("🚀 Starting Full Drawing Benchmark Experiment")
    print("="*80)
    
    # Define models to test
    models = [
        "anthropic/claude-4-sonnet-thinking-off",
        "openai/gpt-4.1", 
        "openai/gpt-4.1-mini",
        "google/gemini-2.5-flash-thinking-off"
    ]
    
    # Load dataset
    dataset = load_dataset()
    total_prompts = len(dataset["prompts"])
    
    print(f"📊 Experiment Configuration:")
    print(f"  Models: {len(models)}")
    print(f"  Prompts: {total_prompts}")
    print(f"  Total Tests: {len(models) * total_prompts}")
    print(f"  Estimated Time: ~1 hour")
    print()
    
    # Track results
    all_results = {}
    start_time = time.time()
    
    # Test each model
    for i, model in enumerate(models, 1):
        model_start = time.time()
        print(f"🔬 Testing Model {i}/{len(models)}: {model}")
        print("-" * 60)
        
        try:
            # Run batch test on all prompts
            results = run_batch_test(
                dataset=dataset,
                model=model,
                category=None,  # All categories
                difficulty=None,  # All difficulties
                limit=None  # All prompts
            )
            
            all_results[model] = {
                "status": "success",
                "results": results,
                "time_taken": time.time() - model_start
            }
            
            print(f"✅ {model} completed in {time.time() - model_start:.1f} seconds")
            
        except Exception as e:
            print(f"❌ {model} failed: {str(e)}")
            all_results[model] = {
                "status": "failed",
                "error": str(e),
                "time_taken": time.time() - model_start
            }
        
        print()
    
    # Calculate total time
    total_time = time.time() - start_time
    
    # Save comprehensive results
    experiment_results = {
        "timestamp": datetime.now().isoformat(),
        "total_time_seconds": total_time,
        "total_time_minutes": total_time / 60,
        "models_tested": len(models),
        "prompts_tested": total_prompts,
        "total_tests": len(models) * total_prompts,
        "results": all_results
    }
    
    # Save to file
    output_file = f"full_experiment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(experiment_results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("="*80)
    print("🎉 FULL EXPERIMENT COMPLETED")
    print("="*80)
    print(f"Total Time: {total_time/60:.1f} minutes")
    print(f"Results saved to: {output_file}")
    print()
    
    # Print model summary
    print("📊 MODEL SUMMARY:")
    for model, result in all_results.items():
        if result["status"] == "success":
            print(f"  ✅ {model}: {result['time_taken']:.1f}s")
        else:
            print(f"  ❌ {model}: Failed - {result['error']}")
    
    print()
    print("🔍 Next Steps:")
    print("  1. Run: python analyze_full_results.py")
    print("  2. Generate model comparison report")
    print("  3. Create visualizations")
    print("  4. Start paper writing")
    
    return experiment_results

if __name__ == "__main__":
    run_full_experiment()
