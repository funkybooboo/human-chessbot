# Training

## Quick Start

```bash
python -m packages.train.src.train.main config.json
```

## Config

See `exampleConfig.json`. Key fields:

- `num_iterations`: Random search iterations
- `hyperparameters`: learning_rates, decay_rates, betas, momentums, num_epochs, batch_size
- `database_info`: num_indexes, data_split (train/val/test ratios)
- `checkpoints`: directory, auto_save_interval (seconds)

## Output

```
output_dir/
├── trained_models/<model_name>/
│   ├── *.pth                 # Model weights
│   ├── checkpoint_info.csv   # Save metrics
│   └── epoch_info.csv        # Per-epoch metrics
└── check_points/<model_name>/
    └── epoch_*.pth           # Epoch checkpoints
```

## Analysis

```python
from packages.train.src.train.analysis import Analyzer

analyzer = Analyzer("output_dir")
for model in analyzer.model_directories:
    analyzer._graph_training_curves(model)  # Generates PNG plots
```
