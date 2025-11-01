# Experimental Results

## Available Results

This directory contains:

1. **batch_results_all_all.json**: Sample results from one model on all 250 prompts
   - Format: List of 250 test results
   - Each result includes Turn 1 and Turn 2 attempts with detailed evaluations
   - File size: ~2MB

2. **full_experiment_results.json**: Metadata from the complete experiment
   - 4 models tested
   - 250 prompts per model
   - 1,000 total tests
   - Execution time: ~5.6 hours

## Paper Results Summary

The full experimental results reported in the paper include:

### Models Tested
- anthropic/claude-4-sonnet-thinking-off
- openai/gpt-4.1
- openai/gpt-4.1-mini
- google/gemini-2.5-flash-thinking-off

### Overall Performance (aggregated across all 1,000 tests)

| Metric | Turn 1 | Turn 2 | Change |
|--------|--------|--------|--------|
| Average Score | 0.925 | 0.954 | +0.030 |
| Std Deviation | 0.099 | 0.066 | -0.033 |
| Perfect Scores | 192/250 | 232/250 | +40 |
| Perfect Rate | 76.8% | 92.8% | +16.0% |
| Median Score | 0.970 | 0.985 | +0.015 |

### Per-Model Performance (Turn 2)

| Model | Perfect Rate | Avg Score |
|-------|-------------|-----------|
| Claude-4 Sonnet | 94.4% | 0.959 |
| GPT-4.1 | 93.2% | 0.957 |
| Gemini-2.5 Flash | 92.0% | 0.952 |
| GPT-4.1-mini | 90.8% | 0.946 |

## Reproducing Results

To reproduce the full experimental results:

```bash
cd src
python run_full_experiment.py --models all --dataset ../data/dataset_consolidated.json
```

This will:
1. Test all 4 models on all 250 prompts
2. Generate batch_results files for each model
3. Save metadata to full_experiment_results_[timestamp].json
4. Take approximately 5-6 hours to complete

## Result File Format

Each result in `batch_results_all_all.json` has the following structure:

```json
{
  "id": "basic_001",
  "category": "basic_shapes",
  "difficulty": "easy",
  "results": [
    {
      "turn": 1,
      "actions": [...],
      "evaluation": {
        "score": 0.85,
        "errors": [...],
        "metrics": {...}
      },
      "feedback": {...}
    },
    {
      "turn": 2,
      "actions": [...],
      "evaluation": {
        "score": 1.0,
        "errors": [],
        "metrics": {...}
      }
    }
  ]
}
```

## Note on Full Results

Due to file size limitations, this repository includes sample results from one model. The full results dataset (all 4 models × 250 tasks = 1,000 tests) will be made available:

1. Upon publication at a permanent repository
2. By running the experiment script with your own API keys

For questions about the complete experimental data, please open an issue.
