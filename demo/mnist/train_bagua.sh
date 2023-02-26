#!/bin/env bash

num_gpus=3

srun \
  -p gpu \
  -c $((8 * num_gpus)) \
  --gres=gpu:$num_gpus \
  --export=PATH,LD_LIBRARY_PATH \
    ./train.yaml \
      -s . \
      -m effnet.yaml \
      -m bagua.yaml \
      -u devices=$num_gpus \
      -u lr=0.00064 \
      -u batch_size=64 \
      -u num_epochs=10 \
      -u train_loader.options.num_workers=$((2 * num_gpus)) \
      -u train_loader.options.pin_memory=true \
      -u valid_loader.options.num_workers=$((2 * num_gpus)) \
      -u valid_loader.options.pin_memory=true
