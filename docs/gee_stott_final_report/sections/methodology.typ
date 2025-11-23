// Methodology section

== System Architecture

// TODO: Data flow between components
// TODO: Design decisions
We primarily focused on three separate aspects of the human chess bot. Firstly we converted and processed the data into usable chunks, then we trained the model before finally deploying the model into a playable environment.

== Data Collection and Processing

=== PGN File Processing

Lichess data is stored in the form of PGN files. PGN or Portable Game Notation is made up of 2 parts the tag pairs, which stores game metadata about the game and players, and the move strings of the game stored in UCI.

To make this data usable we stored the players elos, which is a measure of their skill. Then we iterate through the game storing "snapshots" of the board at every state, and the move taken by the current player at that position. The board states are then represented as 3 dimensional tensors that are 8 by 8 (due to the size of the board) with 12 channels with 6 channels for each of the white pieces and 6 for the black.

// TODO: Explain raw_games, game_snapshots, legal_moves tables
// TODO: Indexing and optimization decisions

== Neural Network Architecture

The neural network architecture consists of three main components: a convolutional backbone for processing board states, a fully connected network for feature extraction, and dual output heads for move prediction and auxiliary tasks.

The convolutional backbone processes the 8x8x12 board representation through six convolutional layers. Each layer uses 64 filters with 8x8 kernels, maintaining the spatial dimensions through "same" padding. ReLU activation functions are applied after each convolution to introduce non-linearity.

The fully connected portion begins with a 4100-dimensional input (flattened board features plus metadata) and progressively reduces dimensionality through six layers (512→32→32→32→32→32) with ReLU activations. This creates a compact 32-dimensional representation of the game state.

The network splits into two parallel output heads:
1. Move prediction head: Maps the 32-dimensional state to 2104 move probabilities
2. Auxiliary prediction head: Produces additional chess-relevant predictions

Input representation:
- Board state: 8x8x12 tensor (6 piece types × 2 colors)
- Metadata: Player ratings and game state information
- Combined input: 4100 dimensions (4096 from board + 4 metadata features)

Output representation:
- 2104-dimensional probability distribution over legal moves
- Softmax activation ensures valid probability distribution
- Auxiliary head provides additional game state predictions to augment learning process

The architecture balances computational efficiency with sufficient complexity to capture chess patterns and human play styles. The dual head design allows simultaneous learning of move prediction and auxiliary chess concepts.

== Training Process

=== Implementation Details

The training implementation utilizes PyTorch's ecosystem for deep learning. The training pipeline is encapsulated in a Trainer class that handles data loading, model training, evaluation, and checkpointing. Key components include:

- Data loading with PyTorch DataLoaders for efficient batch processing
- Adam optimizer with configurable learning rate and weight decay
- Cross-entropy loss for both move prediction and valid moves
- Automatic checkpointing and performance logging
- GPU acceleration when available

=== Training Parameters

The model was trained with the following configuration:
- Batch size: 512
- Initial learning rate: 0.001
- Weight decay: 1e-4
- Beta parameters: (0.9, 0.999)
- Number of epochs: 50
- Data split: 80% training, 10% validation, 10% test

=== Optimization Strategy

We employed random search for hyperparameter optimization, exploring combinations of:
- Learning rates: [0.1, 0.01, 0.001, 0.0001]
- Weight decay rates: [1e-3, 1e-4, 1e-5]
- Beta values: [0.9, 0.95, 0.99]
- Momentum values: [0.9, 0.95, 0.99]

The best performing configuration was selected based on validation loss.

=== Hardware Configuration

Training was conducted on embedded AI hardware:

- Platform: NVIDIA Jetson Orin Nano 8GB Developer Kit
- GPU: 1024-core NVIDIA Ampere architecture GPU
- CPU: 6-core Arm Cortex-A78AE v8.2 64-bit CPU
- RAM: 8GB 128-bit LPDDR5
- Storage: 64GB eMMC 5.1

This setup processed approximately 10,000 positions per second during training.
