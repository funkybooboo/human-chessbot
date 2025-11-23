== Chess Engines

While early chess engines relied on traditional search algorithms like minimax and alpha-beta pruning, the field has been transformed by neural network approaches. These early engines, including Deep Blue, used handcrafted evaluation functions that required extensive manual tuning of positional and material factors.

The introduction of deep neural networks marked a paradigm shift in computer chess. Modern engines employ sophisticated architectures: AlphaZero uses a deep residual network with 20 residual blocks, each containing convolutional layers and batch normalization. This network processes the 8x8x73 board representation to output both a position evaluation and a policy distribution over possible moves. Leela Chess Zero (LC0), an open-source implementation of similar principles, utilizes a network with 24 residual blocks and generates 256 channels in its intermediate layers.

MAIA, specifically designed for human-like play, employs a modified version of LC0's architecture. Instead of learning through self-play, MAIA is trained on millions of human games using supervised learning. Its network consists of multiple convolutional layers followed by a policy head that predicts move probabilities and a value head that evaluates positions. MAIA processes the board state through 12 input planes (6 piece types × 2 colors) and incorporates additional features like player ratings. Recent hybrid approaches, such as Stockfish's NNUE (Efficiently Updatable Neural Network), combine traditional search with a smaller neural network containing roughly 40,000 parameters that can be efficiently updated during search.

== Human-Like Chess AI

While the pursuit of optimal play has been the primary focus of chess engine development, there is a growing interest in creating AI that plays in a more human-like manner. The MAIA project, by McIlroy-Young et al., represents a significant step in this direction. Instead of using reinforcement learning to find the best possible move, MAIA is trained on a large dataset of human games to predict the move a human player would make in a given position. This supervised learning approach results in an engine that exhibits more human-like characteristics, including making mistakes that are typical of human players at a certain skill level instead of the optimal move. This leads to a much more human learning experience instead of the current method of leveling the playing field by purposefully choosing non-optimal moves.

== Dataset and Training Data

The Lichess database is a massive, publicly available collection of chess games played on the Lichess.org platform. It contains billions of games played by humans of all skill levels, making it an invaluable resource for training human-like chess models. The games are stored in the Portable Game Notation (PGN) format, which includes the moves of the game, the players' ratings (Elo), and the game's outcome.
