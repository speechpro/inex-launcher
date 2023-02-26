import torch
from pytorch_lightning import LightningModule


class Module(LightningModule):
    def __init__(self, model, optimizer, scheduler, criterion, accuracy):
        super().__init__()
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.criterion = criterion
        self.accuracy = accuracy

    def configure_optimizers(self):
        return [self.optimizer], [self.scheduler]

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self.model(x)
        loss = self.criterion(logits, y)
        self.log('lr', self.scheduler.get_last_lr()[0], prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self.model(x)
        loss = self.criterion(logits, y)
        preds = torch.argmax(logits, dim=1)
        self.accuracy.update(preds, y)
        self.log("val_loss", loss, prog_bar=True, sync_dist=True)
        self.log("val_acc", 100 * self.accuracy, metric_attribute='accuracy', prog_bar=True, sync_dist=True)
