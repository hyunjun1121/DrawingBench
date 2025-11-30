# DrawingBench: Evaluating Spatial Reasoning and UI Interaction in Large Language Models

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Conference](https://img.shields.io/badge/AAAI%202026-TrustAgent%20Workshop-blue)](https://sites.google.com/view/trustagent-aaai2026)

> **Accepted at AAAI 2026 TrustAgent Workshop**
>
> **Authors**: Hyunjun Kim, Sooyoung Ryu

## Overview

DrawingBench is a **verification framework** for evaluating the trustworthiness of agentic LLMs through spatial reasoning tasks that require generating sequences of low-level GUI actions. Unlike opaque evaluations, DrawingBench provides **transparent, rule-based assessment**: 8 objective criteria enable reproducible scoring, while action-level inspection allows stakeholders to audit agent behavior.

As agentic AI systems increasingly operate autonomously, establishing trust through verifiable evaluation becomes critical. DrawingBench addresses this need by combining spatial understanding, tool manipulation, and sequential planning in a fully auditable framework.

### Key Features

- **250 Diverse Prompts** across 20 categories and 4 difficulty levels
- **8 Objective Evaluation Criteria** with transparent, rule-based assessment
- **External Oversight Mechanism** through multi-turn feedback for human control
- **Browser-based Drawing Application** (1000x700px canvas)
- **Action-level Inspection** for auditing agent behavior
- **Comprehensive Results** from 1,000 tests across 4 state-of-the-art LLMs

## Key Findings

Our evaluation of four state-of-the-art LLMs (Claude-4 Sonnet, GPT-4.1, GPT-4.1-mini, Gemini-2.5 Flash) reveals:

- **92.8% perfect score rate** on Turn 2 (score >= 0.9)
- **+3.2% average improvement** with structured external feedback (up to +32.8% for complex scenes)
- **Specification clarity matters more than task complexity**: models achieved 100% perfect performance when given explicit, verifiable criteria
- **External oversight outperforms self-correction** for guiding agent behavior

## Repository Structure

```text
DrawingBench/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── data/
│   └── dataset_consolidated.json     # 250 drawing prompts with metadata
├── src/
│   ├── app.js                        # Drawing application server
│   ├── index.html                    # Web interface
│   ├── evaluator.py                  # Automated evaluation system
│   └── run_full_experiment.py        # Experiment execution script
├── results/
│   ├── batch_results_all_all.json    # Sample experimental results (250 tasks, single model)
│   └── full_experiment_results.json  # Experiment metadata
│   └── README_RESULTS.md             # Information about obtaining full results
├── docs/
│   ├── UI_COORDINATES.md             # UI layout and coordinates reference
│   └── UI_CONFIG.json                # UI configuration
└── examples/
    └── sample_prompts.json           # Example prompts
```

## Dataset Statistics

### Difficulty Distribution

| Difficulty | Count | Percentage |
|-----------|-------|-----------|
| Easy | 112 | 44.8% |
| Medium | 97 | 38.8% |
| Hard | 21 | 8.4% |
| Very Hard | 20 | 8.0% |

### Category Distribution (Top 10)

| Category | Count | Description |
|----------|-------|-------------|
| Spatial Reasoning | 71 | Position, alignment, relative placement |
| Color Reasoning | 44 | Color selection and matching |
| Numeracy | 36 | Counting, quantity-based tasks |
| General | 24 | General drawing tasks |
| Basic Shapes | 21 | Fundamental geometric shapes |
| Compositional | 11 | Multiple object compositions |
| Objects | 5 | Real-world objects |
| Precision | 4 | High-precision requirements |
| Pattern | 4 | Repetitive patterns |
| Advanced | 3 | Complex advanced tasks |

## Evaluation System

### 8 Objective Criteria

1. **Required Tools** (weight: 0.20) - All specified tools must be used
2. **Required Colors** (weight: 0.20) - All specified colors must be applied
3. **Minimum Segments** (weight: 0.15) - Minimum drawing segments requirement
4. **Canvas Coverage** (weight: 0.10) - Minimum canvas area coverage
5. **Position Constraint** (weight: 0.15) - Spatial positioning requirements
6. **Size Constraint** (weight: 0.10) - Size specifications
7. **Syntax Validity** (weight: 0.05) - Valid JSON action format
8. **Coordinate Bounds** (weight: 0.05) - Actions within canvas boundaries

### 4 Error Types

1. **SYNTAX_ERROR** (severity: critical) - Invalid JSON structure
2. **COORDINATE_ERROR** (severity: high) - Out-of-bounds coordinates
3. **LOGIC_ERROR** (severity: medium) - Unmatched action pairs
4. **EFFICIENCY_WARNING** (severity: low) - Suboptimal action sequences

## Experimental Results

> **Note**: The results below represent aggregated findings from testing 4 state-of-the-art LLMs on all 250 prompts (1,000 total tests). Sample results from one model are included in `results/batch_results_all_all.json`. See `results/README_RESULTS.md` for information on reproducing the full experimental dataset.

### Overall Performance (1,000 tests across 4 models x 250 tasks)

| Metric | Turn 1 | Turn 2 | Change |
|--------|--------|--------|--------|
| Average Score | 0.925 | 0.954 | +0.030 (+3.2%) |
| Std Deviation | 0.099 | 0.066 | -0.033 (-33%) |
| Perfect Scores | 192/250 | 232/250 | +40 |
| Perfect Rate | 76.8% | 92.8% | +16.0% |
| Median Score | 0.970 | 0.985 | +0.015 |

### Performance by Model (Turn 2)

| Model | Perfect Rate | Avg Score |
|-------|-------------|-----------|
| Claude-4 Sonnet | 94.4% | 0.959 |
| GPT-4.1 | 93.2% | 0.957 |
| Gemini-2.5 Flash | 92.0% | 0.952 |
| GPT-4.1-mini | 90.8% | 0.946 |

### Performance by Difficulty (Turn 2)

| Difficulty | Tests | T1 Score | T2 Score | Improvement |
|-----------|-------|----------|----------|-------------|
| Easy | 112 | 0.944 | 0.963 | +0.019 |
| Medium | 97 | 0.925 | 0.958 | +0.033 |
| Hard | 21 | 0.923 | **0.973** | +0.050 |
| Very Hard | 20 | 0.816 | 0.869 | +0.052 |

## Getting Started

### Prerequisites

```bash
# Python 3.8+
pip install selenium webdriver-manager openai anthropic google-generativeai

# Node.js 14+ (for drawing application)
npm install express
```

### Running the Drawing Application

```bash
cd src
node app.js
# Open http://localhost:3000 in browser
```

### Running Evaluation

```bash
cd src
python run_full_experiment.py
```

### Evaluating Custom Actions

```python
from evaluator import DrawingEvaluator

evaluator = DrawingEvaluator()

prompt_data = {
    "id": "custom_001",
    "prompt": "Draw a red circle in the center of the canvas",
    "evaluation_criteria": {
        "required_tools": ["circle"],
        "required_colors": ["#FF0000"],
        "min_segments": 1,
        "min_coverage": 0.05
    }
}

actions = [
    {"action": "click", "x": 35, "y": 445},  # Select circle tool
    {"action": "click", "x": 429, "y": 25},  # Select red color
    {"action": "moveTo", "x": 590, "y": 420},
    {"action": "mouseDown"},
    {"action": "moveTo", "x": 690, "y": 420},
    {"action": "mouseUp"}
]

result = evaluator.evaluate(actions, prompt_data)
print(f"Score: {result['score']}")
print(f"Errors: {result['errors']}")
```

## Dataset Format

Each prompt in `dataset_consolidated.json` contains:

```json
{
  "id": "basic_001",
  "category": "basic_shapes",
  "difficulty": "easy",
  "prompt": "Draw a red circle in the center of the canvas",
  "evaluation_criteria": {
    "required_tools": ["circle"],
    "required_colors": ["#FF0000"],
    "min_segments": 1,
    "min_coverage": 0.05,
    "position_constraint": "center",
    "size_constraint": null
  },
  "source": "original"
}
```

## Key Insights

### 1. Transparent Evaluation Enables Trust

DrawingBench demonstrates that transparent, rule-based evaluation frameworks can establish trust in agentic systems. The 8 objective criteria provide:

- **Reproducible scoring** across different runs and evaluators
- **Action-level auditability** for stakeholder inspection
- **Deterministic assessment** eliminating subjective judgment

### 2. External Oversight Outperforms Self-Correction

Multi-turn structured feedback proved more reliable than self-correction:

- **Average improvement**: +3.2% (Turn 1 to Turn 2)
- **Variance reduction**: -33% (0.099 to 0.066)
- **Complex scenes**: Up to +32.8% improvement

Structured, actionable feedback (e.g., "Required tool 'pen' was not used. Select it by clicking at coordinates (35, 45)") enables models to pinpoint errors and generate targeted corrections.

### 3. Specification Clarity Matters More Than Complexity

Counter-intuitively, "Hard" tasks achieved higher performance than "Medium" tasks:

- **Hard tasks**: 0.973 (100% perfect rate)
- **Medium tasks**: 0.958 (92.8% perfect rate)

**Explanation**: This paradox stems from **specification clarity** rather than inherent complexity. Hard tasks average 4.2 explicit constraints (e.g., "4 squares in each corner") versus Medium tasks' 2.8 constraints (e.g., "draw a house"). When evaluation criteria are deterministic and unambiguous, models reliably satisfy requirements regardless of spatial complexity.

### 4. Systematic Error Patterns Reveal Limitations

| Error Type | Turn 1 | Turn 2 | Reduction |
|-----------|--------|--------|-----------|
| SYNTAX_ERROR | 3 | 0 | -100% |
| COORDINATE_ERROR | 8 | 2 | -75% |
| LOGIC_ERROR | 15 | 5 | -67% |
| EFFICIENCY_WARNING | 42 | 28 | -33% |

**Root causes**:

- **Tool state management** (18 tasks): Implicit tool mentions in task descriptions
- **Long-horizon planning** (12 tasks): Lack of explicit size specifications
- **Specification ambiguity** drives most errors, not model capability limitations

## Citation

```bibtex
@inproceedings{kim2026drawingbench,
  title={DrawingBench: Evaluating Spatial Reasoning and UI Interaction Capabilities of Large Language Models through Mouse-Based Drawing Tasks},
  author={Kim, Hyunjun and Ryu, Sooyoung},
  booktitle={AAAI 2026 Workshop on Trustworthy Agents (TrustAgent)},
  year={2026}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or feedback, please open an issue in this repository or contact the authors:

- Hyunjun Kim
- Sooyoung Ryu
