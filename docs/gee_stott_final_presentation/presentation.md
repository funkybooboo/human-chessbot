---
marp: true
theme: default
paginate: true
style: |
  section {
    background-color: #f5f5f5;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
  section.lead {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
  }
  section.lead h1 {
    font-size: 3em;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
  }
  h1 {
    color: #2c3e50;
    border-bottom: 4px solid #667eea;
    padding-bottom: 10px;
  }
  h2 {
    color: #34495e;
    margin-top: 1em;
  }
  strong {
    color: #667eea;
  }
  code {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 2px 6px;
    border-radius: 3px;
  }
  pre {
    background-color: #2c3e50;
    border-radius: 8px;
    padding: 20px;
  }
  pre code {
    background-color: transparent;
  }
  ul, ol {
    line-height: 1.8;
  }
  li {
    margin: 0.5em 0;
  }
  blockquote {
    border-left: 5px solid #667eea;
    padding-left: 1em;
    font-style: italic;
    color: #555;
  }
  footer {
    color: #7f8c8d;
  }
  section::after {
    color: #7f8c8d;
    font-weight: bold;
  }
---

<!-- _class: lead -->

# Enia
## A Human-Like Chess Engine

**Ethan Gee & Nate Stott**

---

# Agenda

1. **Introduction & Motivation** (22%)
2. **Methodology** (27%)
3. **Experiments** (32%)
4. **Conclusions & Future Work** (12%)

---

# Introduction

## Problem Definition

- Traditional chess engines (Stockfish, LC0) play **optimally**
- They don't play like humans
- Goal: Predict what move a **human** would make

---

# Introduction

## Motivation

- **Training partners**: Engines at human skill levels
- **Chess education**: Learn from human-like mistakes
- **Research**: Model human decision-making in games

---

# Methodology

## Approach: Supervised Learning

```
+------------------+     +------------------+     +------------------+
|  Human Games     | --> |  Neural Network  | --> |  Move Prediction |
|  (Lichess)       |     |  (CNN + FC)      |     |  (2104 classes)  |
+------------------+     +------------------+     +------------------+
```

Train on millions of human chess positions to predict the next move.

---

# Methodology

## Data Pipeline

```
  +----------------+
  | Lichess Server |
  | (PGN.zst files)|
  +-------+--------+
          | HTTP download
          v
  +-------+--------+
  | Zstd Decompress|
  +-------+--------+
          | Split by game
          v
  +-------+--------+      +------------------+
  |   raw_games    |----->| game_statistics  |
  | (full PGN text)|      | (elo, result)    |
  +-------+--------+      +------------------+
          | Parse moves
          v
  +-------+--------+
  | game_snapshots |
  | (fen + move)   |
  +-------+--------+
          | Encode tensors
          v
  +-------+--------+
  | PyTorch Dataset|
  | (board, meta)  |
  +----------------+
```

---

# Methodology

## Database Schema

```
+------------------+       +------------------+       +------------------+
|  file_metadata   |       |    raw_games     |       | game_statistics  |
+------------------+       +------------------+       +------------------+
| id (PK)          |<--+   | id (PK)          |<----->| id (PK)          |
| url              |   +---| file_id (FK)     |       | raw_game_id (FK) |
| filename         |       | pgn              |       | white_elo        |
| games            |       | processed        |       | black_elo        |
| size_gb          |       +------------------+       | result           |
| processed        |               |                  | time_control     |
+------------------+               |                  | opening          |
                                   | 1:N              | eco              |
                                   v                  +------------------+
                          +------------------+
                          | game_snapshots   |
                          +------------------+
                          | id (PK)          |
                          | raw_game_id (FK) |
                          | move_number      |
                          | turn             |
                          | move             |
                          | fen              |
                          +------------------+
```

---

# Methodology

## Neural Network Architecture

```
                 +----------------+
   Board  -----> | Conv Layers    |
  (12,8,8)       | 6x Conv2d(64)  |
                 | 8x8 kernel     |
                 +----------------+
                         |
                         v
                 +----------------+
                 | Flatten (4096) |
                 +----------------+
                         |
Metadata (4) ------------+
                         |
                         v
                 +----------------------------+
                 | FC Layers (4100->512->32)  |
                 +----------------------------+
                         |
                         v
                 +----------------------------+
                 | Move Head (32->2104)       |
                 | Softmax                    |
                 +----------------------------+
```

---

# Methodology

## Output: Move Encoding

```
2104 possible moves indexed by:
  - Start square (0-63)
  - End square (0-63)
  - Promotion piece (N, B, R, Q)

Move prediction = classification over 2104 classes
```

---

# Experiments

## Dataset

- **Source**: Lichess open database
- **Games**: Human vs. human rated games
- **Positions**: Each game -> multiple snapshots (1 per move)
- **Size**: [TODO: number of games/positions]

---

# Experiments

## Data Split

| Split | Percentage |
|-------|------------|
| Training | 80% |
| Validation | 10% |
| Test | 10% |

---

# Experiments

## Training Setup

| Setting | Value |
|---------|-------|
| Loss Function | CrossEntropyLoss |
| Optimizer | Adam |
| Hyperparameters | learning_rate, decay, beta1, beta2 |
| Search Method | Random Search |

---

# Experiments

## Baselines

| Method | Description |
|--------|-------------|
| **Random** | Uniform random over legal moves |
| **Popular Move** | Most common move in training set |
| **Enia (Ours)** | CNN + FC neural network |

---

# Experiments

## Evaluation Metrics

- **Top-1 Accuracy**: Predicted move = actual move
- **Top-5 Accuracy**: Actual move in top 5 predictions
- **Cross-Entropy Loss**: Training convergence

---

# Experiments

## Results

[TODO: Add training curves]

| Metric | Value |
|--------|-------|
| Training Loss | [TODO] |
| Validation Loss | [TODO] |
| Top-1 Accuracy | [TODO] |
| Top-5 Accuracy | [TODO] |

---

# Experiments

## Comparison to Baselines

| Method | Top-1 Accuracy |
|--------|----------------|
| Random | ~0.03% (1/30 legal moves avg) |
| Popular Move | [TODO] |
| **Enia (Ours)** | [TODO] |

---

# Conclusions

## Summary

- Built end-to-end pipeline: Lichess -> SQLite -> PyTorch
- CNN architecture for spatial pattern recognition
- Supervised learning to predict human moves

---

# Conclusions

## Limitations

- Dataset size constraints
- Computational resources
- No modeling of player skill level

---

# Conclusions

## Future Work

- Larger models (transformers)
- Rating-specific models
- More training data
- Data augmentation (board flipping)

---

<!-- _class: lead -->

# Questions?

**Enia**: Human-Like Chess Engine

Ethan Gee & Nate Stott
