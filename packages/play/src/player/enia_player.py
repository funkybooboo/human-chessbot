"""Enia chess engine player implementation."""

import os
from pathlib import Path

import chess
import torch

from packages.play.src.constants import ENIA_MODEL_PATH, ENIA_SKILL_LEVEL
from packages.play.src.player.player import Player, PlayerConfig
from packages.train.src.dataset.loaders.game_snapshots import GameSnapshotsDataset
from packages.train.src.dataset.loaders.legal_moves import LegalMovesDataset
from packages.train.src.models.neural_network import NeuralNetwork


class EniaPlayerConfig(PlayerConfig):
    """
    Configuration for the Enia neural-network chess engine.

    Attributes:
        name: Player name
        color: True for white, False for black
        skill_level: Enia skill level (1100–1900 elo score)
        wins: Number of wins (tracked automatically)
        losses: Number of losses (tracked automatically)
        model_path: Filesystem path to the .pt model file
    """

    name: str = "Enia"
    color: bool = True
    skill_level: int = ENIA_SKILL_LEVEL
    model_path: str = ENIA_MODEL_PATH


class EniaPlayer(Player):
    """
    Chess bot powered by the Enia neural-network engine.

    Uses a neural network trained on chess games to predict moves.
    The model takes board position, ELO ratings, and turn indicator as input
    and outputs a probability distribution over 2104 possible moves.
    """

    def __init__(self, config: EniaPlayerConfig) -> None:
        super().__init__(config)

        self.skill_level = config.skill_level
        self.model_path = str(Path(os.path.expanduser(config.model_path)).resolve())

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Enia model not found at: {self.model_path}")

        # Determine device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load PyTorch model
        self.model = self._load_model()
        self.model.to(self.device)
        self.model.eval()

        # Load legal moves vocabulary for move decoding
        self.legal_moves_dataset: LegalMovesDataset | None = LegalMovesDataset()

        print(
            f"Initialized Enia player '{config.name}' "
            f"(skill={self.skill_level}, model='{self.model_path}', device={self.device})"
        )

    def _load_model(self) -> torch.nn.Module:
        """Load the model, handling both state_dict and full model saves."""
        checkpoint = torch.load(self.model_path, map_location="cpu", weights_only=False)

        # Check if it's a state_dict or full model
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            # Training checkpoint format
            model = NeuralNetwork()
            model.load_state_dict(checkpoint["model_state_dict"])
        elif isinstance(checkpoint, dict) and all(
            isinstance(v, torch.Tensor) for v in checkpoint.values()
        ):
            # Pure state_dict
            model = NeuralNetwork()
            model.load_state_dict(checkpoint)
        elif isinstance(checkpoint, torch.nn.Module):
            # Full model saved with torch.save(model, path)
            model = checkpoint
        else:
            # Assume it's a state_dict
            model = NeuralNetwork()
            model.load_state_dict(checkpoint)

        return model

    def get_move(self, board: chess.Board) -> chess.Move | None:
        """
        Generate a move using the Enia NN engine.
        """
        if board.turn != self.config.color:
            return None

        if self.model is None:
            print("ERROR: Enia model is not loaded.")
            return None

        try:
            return self._predict_move(board)
        except Exception as e:
            print(f"ERROR during Enia evaluation: {e}")
            return None

    def _predict_move(self, board: chess.Board) -> chess.Move | None:
        """
        Run neural network inference to predict the best move.

        The model outputs probabilities over 2104 possible moves.
        We filter to only legal moves and select the highest-probability one.
        """
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        if self.legal_moves_dataset is None:
            return None

        # Build input tensor
        input_tensor = self._build_input_tensor(board).to(self.device)

        # Run inference
        with torch.no_grad():
            output = self.model(input_tensor)  # Shape: (1, 2104)

        # Get probabilities for all moves
        probs = output[0].cpu()  # Shape: (2104,)

        # Find the legal move with highest probability
        best_move = None
        best_prob = -1.0

        for move in legal_moves:
            # Convert move to UCI string
            uci_move = move.uci()

            # Look up move index in vocabulary
            move_idx = self.legal_moves_dataset.get_index_from_move(uci_move)

            if move_idx == -1:
                # Move not in vocabulary, skip
                continue

            prob = probs[move_idx].item()
            if prob > best_prob:
                best_prob = prob
                best_move = move

        # Fallback to first legal move if no valid move found
        if best_move is None:
            best_move = legal_moves[0]

        return best_move

    def _build_input_tensor(self, board: chess.Board) -> torch.Tensor:
        """
        Build the full 772-dimensional input tensor for the model.

        Layout: [elo(2), turn(2), board(768)]
        """
        # Use skill_level as both players' ELO for inference
        turn = "w" if board.turn else "b"
        elo_tensor = GameSnapshotsDataset.normalize_elo(self.skill_level, self.skill_level)
        turn_tensor = GameSnapshotsDataset.encode_turn(turn)
        board_tensor = GameSnapshotsDataset.fen_to_tensor(board.fen())

        # Combine into single input tensor
        input_tensor = torch.cat([elo_tensor, turn_tensor, board_tensor], dim=0)
        return input_tensor.unsqueeze(0)  # Add batch dimension

    def close(self) -> None:
        """Unload the model (NN engines do not require engine shutdown)."""
        self.model = None
        self.legal_moves_dataset = None
        print(f"Unloaded Enia model for player '{self.config.name}'")

    def __del__(self) -> None:
        self.close()
