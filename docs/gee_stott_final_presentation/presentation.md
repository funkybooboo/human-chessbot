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

# Rylee
## A Human-Like Chess Engine

**Ethan Gee & Nate Stott**

---

# Agenda

1. **Introduction & Motivation**
2. **Methodology**
3. **Experiments**
4. **Conclusions & Future Work**

---

# Introduction - Problem Definition

**Maia**
- Traditional chess engines (Stockfish, LC0) play **optimally**
- They don't play like humans
- Goal: Predict what move a **human** would make

**Rylee**
- asdf

---

# Introduction - Motivation

**Maia**
- **Training partners**: Engines at human skill levels
- **Chess education**: Learn from human-like mistakes
- **Research**: Model human decision-making in games

**Rylee**
- asdf

---

# Methodology - Proposed Solution

```
+------------------+     +------------------+     +------------------+
|  Human Games     | --> |  Neural Network  | --> |  Move Prediction |
|  (Lichess)       |     |  (CNN + FC)      |     |  (2104 classes)  |
+------------------+     +------------------+     +------------------+
```

Train on millions of human chess positions to predict the next move.

---

# Methodology - Data Pipeline

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

# Methodology - ML Models

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

| Setting | Value |
| ------- | ----- |
| Loss Function | CrossEntropyLoss |
| Optimizer | Adam |
| Hyperparameters | learning_rate, decay, beta1, beta2 |
| Search Method | Random Search |

---

# Experiments - Dataset

* **Source:** Lichess Open Database
* **Games:** Human vs. human rated games
* **Positions:** Each game produces multiple board snapshots (one per move)
* **Scope:** 1.6 million games -> 25 million snapshots
* **Action Space:** 2,104 legal move classes

---

# Experiments - Data Split

| Split      | Percentage | Snapshots      |
| ---------- | ---------- | -------------- |
| Training   | 80%        | **20,000,000** |
| Validation | 10%        | **2,500,000**  |
| Test       | 10%        | **2,500,000**  |

---

# Experiments - Baselines

| Method            | Description                                        | Accuracy |
| ----------------- | -------------------------------------------------- | -------- |
| **Random**        | Uniform random choice among all legal moves        | **0%**   |
| **Random Forest** | Classic ML baseline using handcrafted features     | **13%**  |
| **Stockfish 15**  | Strong traditional engine (anchor baseline)        | **40%**  |
| **Leela 4200**    | High-strength neural chess engine (anchor baseline)| **44%**  |
| **Maia1 1500**    | Human-aligned prediction model (anchor baseline)   | **51%**  |
| **Rylee (Ours)**  | CNN + fully connected network for move prediction  | **0%**   |

---

# Experiments - Evaluation Metrics

- **Top-1 Accuracy**: Predicted move = actual move
- **Top-5 Accuracy**: Actual move in top 5 predictions
- **Cross-Entropy Loss**: Training convergence

---

# Experiments - Comparisons

| Method | Top-1 Accuracy |
|--------|----------------|
| Random | ~0.03% (1/30 legal moves avg) |
| Popular Move | [TODO] |
| **Rylee (Ours)** | [TODO] |

---

# Conclusions - Discussions

[TODO: Add training curves]

| Metric | Value |
|--------|-------|
| Training Loss | [TODO] |
| Validation Loss | [TODO] |
| Top-1 Accuracy | [TODO] |
| Top-5 Accuracy | [TODO] |

---

# Conclusions - Limitations

- Dataset size constraints
- Computational resources
- No modeling of player skill level

---

# Conclusions - Future Work

- Larger models (transformers)
- Rating-specific models
- More training data
- Data augmentation (board flipping)

---

<!-- _class: lead -->

# Questions?

**Rylee**: Human-Like Chess Engine

Ethan Gee & Nate Stott
