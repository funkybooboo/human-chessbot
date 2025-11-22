# Models

## NeuralNetwork

Feedforward network for chess move prediction.

**Architecture:** `Input(772) -> Linear(512) -> Linear(32)x5 -> Linear(2104) -> Softmax`

### Input (772 dims)

| Range   | Component | Description                                 |
|---------|-----------|---------------------------------------------|
| [0:2]   | ELO       | Z-normalized (mean=1638.43, std=185.80)     |
| [2:4]   | Turn      | One-hot [white, black]                      |
| [4:772] | Board     | 8x8x12 flattened (6 piece types x 2 colors) |

### Output (2104 dims)

Probability distribution over all valid chess moves. Use `LegalMovesDataset` to convert indices <-> UCI strings.

### Usage

```python
from packages.train.src.models.neural_network import NeuralNetwork

model = NeuralNetwork()
model.load_state_dict(torch.load('model.pth'))
model.eval()

output = model(input_tensor)  # (batch, 2104)
move_idx = torch.argmax(output, dim=1)
```
