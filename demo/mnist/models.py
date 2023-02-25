import torch
import logging
from torch import nn
from torch.nn import functional as F
from efficientnet_pytorch import EfficientNet


class MLP(nn.Module):
    def __init__(self, channels, width, height, hidden_size, num_classes, dropout):
        super().__init__()
        self.model = nn.Sequential(
            nn.Flatten(),
            nn.Linear(channels * width * height, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_classes),
        )

    def forward(self, x):
        x = self.model(x)
        return F.log_softmax(x, dim=1)


class EffNet(nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        kwargs['in_channels'] = 1
        self.model = EfficientNet.from_name(**kwargs)

    def forward(self, x):
        x = self.model(x)
        return F.log_softmax(x, dim=1)
