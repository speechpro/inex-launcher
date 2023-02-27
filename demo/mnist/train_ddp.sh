#!/bin/env bash

#export NCCL_DEBUG=INFO
#export NCCL_DEBUG_SUBSYS=ALL
export NCCL_SOCKET_IFNAME=enp94s0f0
export MASTER_PORT=5518

num_nodes=2
nper_node=2
lr=0.00064
batch_size=16
num_epochs=10

train_dir=train_effnet_${lr}_${batch_size}_${num_epochs}_ddp
mkdir -p $train_dir
cp train.yaml effnet.yaml ddp.yaml $train_dir
script=$train_dir/train.sh
cat << EOF > $script
#!/bin/env bash
srun \\
  ./train.yaml \\
    -l INFO \\
    -s . \\
    -m effnet.yaml \\
    -m ddp.yaml \\
    -u train_dir=$train_dir \\
    -u num_nodes=$num_nodes \\
    -u devices=$nper_node \\
    -u lr=$lr \\
    -u batch_size=$batch_size \\
    -u num_epochs=$num_epochs \\
    -u train_loader.options.num_workers=4 \\
    -u train_loader.options.pin_memory=true \\
    -u valid_loader.options.num_workers=4 \\
    -u valid_loader.options.pin_memory=true \\
    -u progress.options.refresh_rate=0 || exit 1
EOF
chmod +x $script

[ -f $train_dir/train.log ] && rm $train_dir/train.log

sbatch \
  --exclude=sc14 \
  --partition=gpu \
  --cpus-per-task=8 \
  --nodes=$num_nodes \
  --gres=gpu:$nper_node \
  --ntasks-per-node=$nper_node \
  --export=PATH,LD_LIBRARY_PATH,NCCL_DEBUG,NCCL_DEBUG_SUBSYS,NCCL_SOCKET_IFNAME,MASTER_PORT \
  --open-mode=append \
  -e $train_dir/train.log \
  -o $train_dir/train.log \
  $script
