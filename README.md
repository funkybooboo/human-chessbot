# ♟️ The Human-like Chess Bot

## 📌 Project Summary

Traditional chess bots (CB) like Stockfish and AlphaZero dominate human players (HP), but their gameplay lacks human-like intuition and heuristic-driven decision-making. While these CBs are excellent at playing perfect chess, they are not ideal training partners for human players seeking to improve against other humans.

This project explores how to build **smaller, more human-like chess models** inspired by [MAIA](https://www.maiachess.com/), a bot trained to predict human moves rather than just win. MAIA uses supervised learning to mimic human decision-making rather than brute-force search or reinforcement learning.

### Goals:

* **Reproduce MAIA-like performance using smaller models** (e.g. Stockfish-sized)
* Build a tabular dataset of real human chess games for training
* Use interpretable models (e.g., Random Forests) as a baseline to study human-aligned move prediction

---

## 📁 Project Structure

```text
cs6640_project/
├── data/
│   ├── csv/                   # Processed datasets in CSV format
│   └── pgn/                   # Raw PGN files from Lichess
├── docs/
│   └── papers/                # Research papers and documentation
├── src/
│   ├── pgn_to_csv.py          # PGN to CSV parser script
│   └── random_forest.ipynb    # ML model baseline (e.g. Random Forest)
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation (this file)
```

---

## 📦 Dataset

We use the **[Lichess Database](https://database.lichess.org/)**, a public archive of millions of chess games played online. Each game is stored in PGN format and contains:

* Player ELO ratings
* Full move list
* Game outcome
* Metadata like time control

For our model, we extract the following features **per move**:

* `white_elo`, `black_elo`
* `blacks_move` (boolean)
* 64 board squares encoded as integers (from A1 to H8)
* `selected_move` (target label in UCI format)

---

## 🔄 How to Run the PGN to CSV Parser

### ✅ Step 1: Install Dependencies

Install required Python packages:

```bash
pyenv install 3.11.4  # or latest 3.11.x version
pyenv global 3.11.4
pip install -r requirements.txt
```

> This installs:
>
> * `python-chess` (for PGN parsing)
> * `zstandard` (for reading `.pgn.zst` files)
> * `pandas`, `matplotlib`, `notebook` (for analysis & visualization)

**Note**: If you're not using `pyenv`, you can install Python 3.11.4 manually, or use another version manager. You can also install dependencies directly with `pip` after installing Python.

### 📥 Step 2: Download a PGN File

Download a `.pgn.zst` file from the [Lichess Database](https://database.lichess.org/).

**No need to decompress it manually** — the parser will handle `.zst` files automatically.

For example:

```bash
wget https://database.lichess.org/standard/lichess_db_standard_rated_2013-01.pgn.zst -P data/pgn/
```

### ▶️ Step 3: Run the Parser

From the root directory:

```bash
python src/pgn_to_csv.py data/pgn/lichess_db_standard_rated_2013-01.pgn.zst data/csv/lichess_2013-01.csv
```

This will:

* Read each game in the PGN (compressed or uncompressed)
* Extract board states after every move
* Save the result as a CSV to the given path

### 📄 Example Output (CSV row)

```csv
white_elo,black_elo,blacks_move,A1,A2,...,H8,selected_move
1500,1450,0,4,2,3,5,6,...,0,e2e4
```

---

## 🧠 Project Goals

* Train human-aligned models on real human data
* Compare model size vs accuracy trade-offs
* Improve the learning experience for human players
* Evaluate generalization to unseen board states

---

## 📚 References

* **MAIA Research Paper (University of Toronto)**
  [https://www.cs.toronto.edu/~ashton/pubs/maia-kdd2020.pdf](https://www.cs.toronto.edu/~ashton/pubs/maia-kdd2020.pdf)

* **MAIA-2 Preprint (2024)**
  [https://arxiv.org/abs/2409.20553](https://arxiv.org/abs/2409.20553)

* **AlphaZero (DeepMind, 2018)**
  [https://doi.org/10.1126/science.aar6404](https://doi.org/10.1126/science.aar6404)

* **Stockfish vs Leela Chess Zero**
  [https://webdocs.cs.ualberta.ca/~mmueller/ps/2023/ACG_2023_Stockfish.pdf](https://webdocs.cs.ualberta.ca/~mmueller/ps/2023/ACG_2023_Stockfish.pdf)

---

## 👥 Contributors

* **Ethan Gee**
* **Nate Stott**

For CS6640 – Machine Learning
Utah State University
