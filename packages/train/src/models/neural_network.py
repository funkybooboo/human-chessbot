import torch
from torch import nn


class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()

        self.convolution = nn.Sequential(
            nn.Conv2d(12, 64, kernel_size=8, stride=1, padding="same"),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=8, stride=1, padding="same"),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=8, stride=1, padding="same"),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=8, stride=1, padding="same"),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=8, stride=1, padding="same"),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=8, stride=1, padding="same"),
            nn.ReLU(),
        )

        self.fully_connected = nn.Sequential(
            nn.Linear(4100, 512),
            nn.ReLU(),
            nn.Linear(512, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
        )

        # here we split into two heads to handle move and auxilary predictions separately
        self.move_head = nn.Sequential(nn.Linear(32, 2104), nn.Softmax(dim=1))
        self.auxiliary_head = nn.Sequential(nn.Linear(32, 2104), nn.Softmax(dim=1))

    def forward(self, metadata: torch.Tensor, board: torch.Tensor):
        board = self.convolution(board)
        board = torch.flatten(board, 1)

        x = torch.cat((board, metadata), dim=1)
        shared_output = self.fully_connected(x)
        return self.move_head(shared_output), self.auxiliary_head(shared_output)
