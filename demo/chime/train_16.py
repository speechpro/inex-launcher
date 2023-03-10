#!/bin/env python

model_id = 16
model_name = 'baseline'
data_dir = 'data_06'

random_seed = 0
cudnn_enabled = True
cudnn_benchmark = False
cudnn_deterministic = True

root_dir = '/mnt/asr/prisyach/CHIME7/espnet/egs2/chime7_task1/asr1'
path_tokens = f'{root_dir}/data/en_token_list/bpe_unigram500/tokens.txt'
path_bpe_model = f'{root_dir}/data/en_token_list/bpe_unigram500/bpe.model'
download_dir = 'hub'

train_wave = f'{data_dir}/train/wav.scp'
train_wave_shape = f'{data_dir}/train/speech_shape'
train_text = f'{data_dir}/train/text'
train_text_shape = f'{data_dir}/train/text_shape.bpe'

valid_wave = f'{data_dir}/valid/wav.scp'
valid_wave_shape = f'{data_dir}/valid/speech_shape'
valid_text = f'{data_dir}/valid/text'
valid_text_shape = f'{data_dir}/valid/text_shape.bpe'

train_dir = f'exp/train_{model_id}'

accelerator = 'gpu'
devices = 1
num_nodes = 1

batch_size = 32
batch_bins = 1000000
fold_lengths = [80000, 150]
num_workers = 1
pin_memory = True
num_epochs = 8
stop_after = 1
log_aver = 2000
resume_training = True
val_check_interval = 0.1

lr = 0.0004
warmup_steps = 8500

project_name = 'YK-CHiME7-ASR'
task_name = f'{model_name} #{model_id}'
task_info = f'Model: {model_name} #{model_id}, lr: {lr}, warmup_steps: {warmup_steps}, num_epochs: {num_epochs}, batch_size: {batch_size}, batch_bins: {batch_bins}, fold_lengths: {fold_lengths}, data_dir: {data_dir}'

dtype = 'float32'

from chime.plugins.logging.clearml import ClearML
plugins_clearml = ClearML(
    command_line='command_line',
    config_path='config_path',
    enable=False,
    project_name=project_name,
    task_name=task_name,
    task_info=task_info,
)

from chime.plugins.asr.init_torch import set_random_seed
plugins_set_random_seed = set_random_seed(seed=random_seed)

from chime.plugins.asr.init_torch import init_cudnn
plugins_init_cudnn = init_cudnn(
    cudnn_enabled=cudnn_enabled,
    cudnn_benchmark=cudnn_benchmark,
    cudnn_deterministic=cudnn_deterministic,
)

from inex.helpers import attribute
plugins_data_type = attribute(modname='torch', attname=dtype)

from torch import device
plugins_device = device(type='cuda')

from chime.plugins.asr.tokens import Tokens
plugins_tokens = Tokens(path=path_tokens)

from espnet2.train.preprocessor import CommonPreprocessor
plugins_preprocess_fn = CommonPreprocessor(
    token_list=plugins_tokens.tokens,
    train=True,
    token_type='bpe',
    bpemodel=path_bpe_model,
    text_cleaner=None,
)

from espnet2.train.collate_fn import CommonCollateFn
plugins_collate_fn = CommonCollateFn(float_pad_value=0.0, int_pad_value=-1)

train_path_name_type = [[train_wave, 'speech', 'sound'], [train_text, 'text', 'text']]

train_shapes = [train_wave_shape, train_text_shape]

from espnet2.train.dataset import ESPnetDataset
plugins_train_dataset = ESPnetDataset(
    preprocess=plugins_preprocess_fn,
    path_name_type_list=train_path_name_type,
    float_dtype=dtype,
    int_dtype='long',
    max_cache_size=0.0,
    max_cache_fd=32,
)

from espnet2.samplers.folded_batch_sampler import FoldedBatchSampler
plugins_train_sampler = FoldedBatchSampler(
    shape_files=train_shapes,
    batch_size=batch_size,
    fold_lengths=fold_lengths,
    min_batch_size=1,
    sort_in_batch='descending',
    sort_batch='descending',
    drop_last=False,
    utt2category_file=None,
)

from chime.plugins.asr.utils import get_batches
plugins_train_batches = get_batches(sampler=plugins_train_sampler, shuffle=True, seed=-1)

from torch.utils.data.dataloader import DataLoader
plugins_train_loader = DataLoader(
    dataset=plugins_train_dataset,
    batch_sampler=plugins_train_batches,
    collate_fn=plugins_collate_fn,
    num_workers=num_workers,
    pin_memory=pin_memory,
)

valid_path_name_type = [[valid_wave, 'speech', 'sound'], [valid_text, 'text', 'text']]

valid_shapes = [valid_wave_shape, valid_text_shape]

from espnet2.train.dataset import ESPnetDataset
plugins_valid_dataset = ESPnetDataset(
    preprocess=plugins_preprocess_fn,
    path_name_type_list=valid_path_name_type,
    float_dtype=dtype,
    int_dtype='long',
    max_cache_size=0.0,
    max_cache_fd=32,
)

from espnet2.samplers.folded_batch_sampler import FoldedBatchSampler
plugins_valid_sampler = FoldedBatchSampler(
    shape_files=valid_shapes,
    batch_size=batch_size,
    fold_lengths=fold_lengths,
    min_batch_size=1,
    sort_in_batch='descending',
    sort_batch='descending',
    drop_last=False,
    utt2category_file=None,
)

from chime.plugins.asr.utils import get_batches
plugins_valid_batches = get_batches(sampler=plugins_valid_sampler, shuffle=False, seed=0)

from torch.utils.data.dataloader import DataLoader
plugins_valid_loader = DataLoader(
    dataset=plugins_valid_dataset,
    batch_sampler=plugins_valid_batches,
    collate_fn=plugins_collate_fn,
    num_workers=num_workers,
    pin_memory=pin_memory,
)

from espnet2.asr.frontend.s3prl import S3prlFrontend
plugins_frontend = S3prlFrontend(
    frontend_conf={'upstream': 'wavlm_large'},
    download_dir=download_dir,
    multilayer_feature=True,
    fs='16k',
)

plugins_frontend_size = plugins_frontend.output_size()

from espnet2.asr.specaug.specaug import SpecAug
plugins_specaug = SpecAug(
    apply_time_warp=False,
    time_warp_window=5,
    time_warp_mode='bicubic',
    apply_freq_mask=False,
    freq_mask_width_range=[0, 150],
    num_freq_mask=4,
    apply_time_mask=True,
    time_mask_width_ratio_range=[0.0, 0.15],
    num_time_mask=3,
)

from espnet2.layers.utterance_mvn import UtteranceMVN
plugins_normalize = UtteranceMVN()

from espnet2.asr.preencoder.linear import LinearProjection
plugins_preencoder = LinearProjection(input_size=plugins_frontend_size, output_size=128, dropout=0.2)

plugins_preencoder_size = plugins_preencoder.output_size()

from espnet2.asr.encoder.transformer_encoder import TransformerEncoder
plugins_encoder = TransformerEncoder(
    input_size=plugins_preencoder_size,
    output_size=256,
    attention_heads=4,
    linear_units=2048,
    num_blocks=12,
    dropout_rate=0.1,
    attention_dropout_rate=0.0,
    input_layer='conv2d2',
    normalize_before=True,
)

plugins_encoder_size = plugins_encoder.output_size()

from espnet2.asr.decoder.transformer_decoder import TransformerDecoder
plugins_decoder = TransformerDecoder(
    vocab_size=plugins_tokens.num_tokens,
    encoder_output_size=plugins_encoder_size,
    input_layer='embed',
    attention_heads=4,
    linear_units=2048,
    num_blocks=6,
    dropout_rate=0.1,
    positional_dropout_rate=0.0,
    self_attention_dropout_rate=0.0,
    src_attention_dropout_rate=0.0,
)

from espnet2.asr.ctc import CTC
plugins_ctc = CTC(
    odim=plugins_tokens.num_tokens,
    encoder_output_size=plugins_encoder_size,
    dropout_rate=0.0,
    ctc_type='builtin',
    reduce=True,
    ignore_nan_grad=None,
    zero_infinity=True,
)

from espnet2.asr.espnet_model import ESPnetASRModel
plugins_model = ESPnetASRModel(
    frontend=plugins_frontend,
    specaug=plugins_specaug,
    normalize=plugins_normalize,
    preencoder=plugins_preencoder,
    encoder=plugins_encoder,
    decoder=plugins_decoder,
    ctc=plugins_ctc,
    token_list=plugins_tokens.tokens,
    vocab_size=plugins_tokens.num_tokens,
    postencoder=None,
    joint_network=None,
    ctc_weight=0.3,
    lsm_weight=0.1,
    length_normalized_loss=False,
    extract_feats_in_collect_stats=False,
)

from espnet2.torch_utils.initialize import initialize
plugins_initialize = initialize(model=plugins_model, init='xavier_uniform')

plugins_model_to = plugins_model.to(dtype=plugins_data_type, device=plugins_device)

from chime.plugins.asr.freeze import freeze
plugins_freeze = freeze(model=plugins_model, names=['frontend.upstream'])

plugins_parameters = plugins_model.parameters()

from torch.optim import Adam
plugins_optimizer = Adam(params=plugins_parameters, lr=lr)

from espnet2.schedulers.warmup_lr import WarmupLR
plugins_scheduler = WarmupLR(optimizer=plugins_optimizer, warmup_steps=warmup_steps)

from chime.plugins.asr.module import Module
plugins_module = Module(
    model=plugins_model,
    optimizer=plugins_optimizer,
    scheduler=plugins_scheduler,
    cml_task=plugins_clearml.task,
    log_aver=log_aver,
    train_bar_keys={'loss': 'train_loss', 'acc': 'train_acc', 'lr': 'lr'},
    train_log_keys={'loss_ctc': 'train_loss_ctc', 'cer_ctc': 'train_cer_ctc', 'loss_att': 'train_loss_att', 'cer': 'train_cer', 'wer': 'train_wer'},
    valid_bar_keys={'loss': 'val_loss', 'acc': 'val_acc'},
    valid_log_keys={'loss_ctc': 'val_loss_ctc', 'cer_ctc': 'val_cer_ctc', 'loss_att': 'val_loss_att', 'cer': 'val_cer', 'wer': 'val_wer'},
)

from inex.helpers import none
plugins_strategy = none()

from pytorch_lightning.callbacks import ModelCheckpoint
plugins_checkpoint = ModelCheckpoint(
    dirpath=train_dir,
    monitor='val_acc',
    mode='max',
    save_top_k=15,
)

from pytorch_lightning.callbacks.progress import TQDMProgressBar
plugins_progress = TQDMProgressBar(refresh_rate=5)

from pytorch_lightning.loggers import CSVLogger
plugins_logger = CSVLogger(save_dir=train_dir)

from chime.plugins.asr.trainer import train
train(
    module=plugins_module,
    train_data=plugins_train_loader,
    valid_data=plugins_valid_loader,
    cml_task=plugins_clearml.task,
    strategy=plugins_strategy,
    callbacks=[plugins_progress, plugins_checkpoint],
    logger=plugins_logger,
    num_epochs=num_epochs,
    stop_after=stop_after,
    resume_training=resume_training,
    accelerator=accelerator,
    devices=devices,
    num_nodes=num_nodes,
    val_check_interval=val_check_interval,
    num_sanity_val_steps=0,
    default_root_dir=train_dir,
)
