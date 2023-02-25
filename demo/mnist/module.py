import torch
from pytorch_lightning import LightningModule


class Module(LightningModule):
    def __init__(self, model, optimizer, criterion, accuracy):
        super().__init__()
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.accuracy = accuracy

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.criterion(logits, y)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.criterion(logits, y)
        preds = torch.argmax(logits, dim=1)
        self.accuracy.update(preds, y)
        self.log("val_loss", loss, prog_bar=True)
        self.log("val_acc", self.accuracy, prog_bar=True)

    def configure_optimizers(self):
        return self.optimizer
