from torch import nn


class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()

        # this is identical to the stock fish -engineered features
        self.shared = nn.Sequential(
            nn.Linear(772, 512),
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
            nn.Linear(32, 32),
        )

        # here we split into two heads to handle move and promote predictions separately
        self.move_head = nn.Sequential(nn.Linear(32, 4096), nn.Softmax(dim=1))
        self.promote_head = nn.Sequential(nn.Linear(32, 4), nn.Softmax(dim=1))

    def forward(self, x):
        shared_output = self.shared(x)
        # output both move and promote predictions as a tuple
        return self.move_head(shared_output), self.promote_head(shared_output)
