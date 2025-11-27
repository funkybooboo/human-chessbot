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
    background: linear-gradient(135deg, #ccccff 0%, #a754fbff 100%);
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
    color: #7777ea;
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

**Rylee** - All the above AND
- Maia is a **large complex model** that takes a **lots of compute power** to train and run
- Goal: Get about the **same accuracy** but train and run on a **raspberry pi** 😎

---

# Introduction - Motivation

**Maia**
- **Training partners**: Engines at human skill levels
- **Chess education**: Learn from human-like mistakes
- **Research**: Model human decision-making in games

**Rylee** - all the above AND
- Playing chess on edge devices
- Maia can't play openings

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
---

| Setting          | Value                              |
|------------------|------------------------------------|
| Chosen Move Loss | CrossEntropyLoss                   |
| Valid Moves Loss | BCE with LogitsLoss                |
| Optimizer        | Adam                               |
| Hyperparameters  | learning_rate, decay, beta1, beta2 |
| Search Method    | Random Search                      |

---

# Experiments - Dataset

* **Source:** Lichess Open Database
* **Games:** Human rated games
* **Positions:** Each game produces multiple board snapshots (one per move)
* **Scope:** 860,000 million games -> 25 million snapshots
* **Action Space:** 2,104 legal move classes
* **Legal Moves**: Indexes of Legal Moves from a given board state

---

# Experiments - Data Split

| Split      | Percentage | Snapshots      |
|------------|------------|----------------|
| Training   | 80%        | **20,000,000** |
| Validation | 10%        | **2,500,000**  |
| Test       | 10%        | **2,500,000**  |

---

# Experiments - Baselines

| Method            | Description                                         |
|-------------------|-----------------------------------------------------|
| **Random**        | Uniform random choice among all legal moves         |
| **Random Forest** | Classic ML baseline using handcrafted features      |
| **Stockfish 15**  | Strong traditional engine (anchor baseline)         |
| **Leela 4200**    | High-strength neural chess engine (anchor baseline) |
| **Maia1 1500**    | Human-aligned prediction model (anchor baseline)    |

---

# Experiments - Evaluation Metrics

- **Top-1 Accuracy**: Predicted move = actual move

# Experiments - Comparisons

| Method            | Top-1 Accuracy |
|-------------------|----------------|
| **Random**        | **6%**         |
| **Random Forest** | **13%**        |
| **Stockfish 15**  | **40%**        |
| **Leela 4200**    | **44%**        |
| **Maia1 1500**    | **51%**        |
| **Rylee (Ours)**  | **46%**        |

---

# Conclusions - Discussions

| Metric          | Value  |
|-----------------|--------|
| Training Loss   | [TODO] |
| Validation Loss | [TODO] |
| Top-1 Accuracy  | [TODO] |
| Top-5 Accuracy  | [TODO] |

---

# Conclusions - Future Work

- More training data
- More computational resources
- Larger models
- Data augmentation (board flipping)
- Elo predictor
- Human vs Bot discriminator
- GAN implementation
- Blunder detection

---

<!-- _class: lead -->

# Questions?

**Rylee**: Human-Like Chess Engine

Ethan Gee & Nate Stott
