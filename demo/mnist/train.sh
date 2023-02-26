#!/bin/env bash

srun \
  -p gpu \
  -c 8 \
  --gres=gpu:1 \
  --export=PATH,LD_LIBRARY_PATH \
    ./train.yaml \
      -s . \
      -m effnet.yaml \
      -u lr=0.00064 \
      -u batch_size=64 \
      -u num_epochs=10 \
      -u train_loader.options.num_workers=4 \
      -u train_loader.options.pin_memory=true \
      -u valid_loader.options.num_workers=4 \
      -u valid_loader.options.pin_memory=true
