#!/bin/env bash

lr=0.00064
batch_size=64
num_epochs=10

train_dir=train_effnet_${lr}_${batch_size}_${num_epochs}
mkdir -p $train_dir
cp train.yaml effnet.yaml $train_dir
script=$train_dir/train.sh
cat << EOF > $script
#!/bin/env bash
srun \\
  --partition=gpu \\
  --gres=gpu:1 \\
  --cpus-per-task=8 \\
  --export=PATH,LD_LIBRARY_PATH \\
  ./train.yaml \\
    -l INFO \\
    -s . \\
    -m effnet.yaml \\
    -u train_dir=$train_dir \\
    -u lr=$lr \\
    -u batch_size=$batch_size \\
    -u num_epochs=$num_epochs \\
    -u train_loader.options.num_workers=4 \\
    -u train_loader.options.pin_memory=true \\
    -u valid_loader.options.num_workers=4 \\
    -u valid_loader.options.pin_memory=true || exit 1
EOF
chmod +x $script

$script |& tee $train_dir/train.log
