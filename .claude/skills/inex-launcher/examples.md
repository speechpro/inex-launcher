# InEx Launcher — annotated examples

Self-contained config + Python examples for common inex-launcher patterns. All
snippets use a generic `myproject` package — rename for your project. For syntax
tables see [reference.md](reference.md); for design rules see [SKILL.md](SKILL.md).

When you need to confirm exact behavior, the upstream
[contract tests](https://github.com/speechpro/inex-launcher/tree/main/tests) are
minimal working configs that exercise each feature.

Contents:

1. [Minimal utility — one plugin + execute function](#1-minimal-utility)
2. [Data prep — readers + method plugin + writer](#2-data-prep)
3. [Multi-source execute](#3-multi-source-execute)
4. [Callback pipeline on a dataset + DataLoader](#4-callback-pipeline)
5. [Inference with checkpoint reload (`_import_`)](#5-inference-with-checkpoint-reload)
6. [Export a nested attribute for a third-party execute](#6-export-nested-attribute)
7. [Training stack (Lightning) ending in `train()`](#7-training-stack)
8. [`__args__` / `__kwargs__` and positional args](#8-args-and-kwargs)
9. [Built-in resolvers and `???` placeholders](#9-resolvers-and-placeholders)
10. [Resumable stages with `is_done` / `before` / `after`](#10-resumable-stages)
11. [Sub-config import that surfaces a derived value](#11-import-with-derived-value)
12. [Model factory selected by name](#12-model-factory)
13. [The exports rule in practice](#13-the-exports-rule-in-practice)
14. [Quick-start template](#14-quick-start-template)

---

## 1. Minimal utility

One I/O plugin builds the data; one `execute` function does the work. Best for
pack/convert/write tools with a single input.

```yaml
#!/bin/env inex

__log_level__: INFO

frequency: 16000
input_path: ???
output_dir: ???

exists:
  - ${__path_is_file__:${input_path}}

plugins:
  - input_list

input_list:
  module: myproject.data.io/read_lines
  options:
    pathnames: ${input_path}

execute:
  method: myproject.cli/pack_items
  imports:
    items: plugins.input_list
  options:
    frequency: ${frequency}
    output_dir: ${output_dir}
```

```python
# myproject/data/io.py
from typing import List, Union

def read_lines(pathnames: Union[str, List[str]]) -> List[str]:
    ...

# myproject/cli.py
def pack_items(items: List[str], output_dir: str, frequency: int = 16000) -> None:
    ...
```

Takeaways: the plugin object goes through `imports`; scalars through `options`;
`exists:` preflights the input with a path resolver.

---

## 2. Data prep

Seed → build an object → call a method on it → load data → run a writer. The
`module: plugins.<name>/Method` form mutates/configures an already-built plugin.

```yaml
#!/bin/env inex

random_seed: 0
model_path: ???
data_path: ???
batch_size: ???
result_dir: ???

plugins:
  - set_random_seed
  - tokenizer
  - load_tokenizer
  - data_set
  - sample_maker

set_random_seed:
  module: myproject.utils.init_torch/set_random_seed
  options:
    seed: ${random_seed}

tokenizer:
  module: myproject.text/Tokenizer
  options:
    vocab_size: 5000

load_tokenizer:
  module: plugins.tokenizer/Load        # method on the prior plugin instance
  options:
    model_file: ${model_path}

data_set:
  module: myproject.data/load_dataset
  options:
    path: ${data_path}

sample_maker:
  module: myproject.features/SampleMaker
  imports:
    tokenizer: plugins.tokenizer

execute:
  method: myproject.cli/write_batches
  imports:
    data_set: plugins.data_set
    sample_maker: plugins.sample_maker
  options:
    batch_size: ${batch_size}
    result_dir: ${result_dir}
```

```python
# myproject/text.py
class Tokenizer:
    def __init__(self, vocab_size: int): ...
    def Load(self, model_file: str): ...      # load weights; return self or None
```

---

## 3. Multi-source execute

Several parallel data plugins (often reusing one class) feed a single function.
A top-level list collects `plugins.*` references and is imported as one argument.

```yaml
#!/bin/env inex

classes_path: ???
noise_path: ???
data_root: ???
snr_range: [10, 20]
result_dir: ???

wavesets: [plugins.waveset1, plugins.waveset2, plugins.waveset3]

plugins:
  - classes
  - noiseset
  - waveset1
  - waveset2
  - waveset3

classes:    { module: myproject.data/Classes, options: { path: ${classes_path} } }
noiseset:   { module: myproject.data/WaveSet, options: { pathname: ${noise_path} } }
waveset1:   { module: myproject.data/WaveSet, options: { pathname: ${data_root}/part1.scp } }
waveset2:   { module: myproject.data/WaveSet, options: { pathname: ${data_root}/part2.scp } }
waveset3:   { module: myproject.data/WaveSet, options: { pathname: ${data_root}/part3.scp } }

execute:
  method: myproject.cli/make_mixtures
  imports:
    classes: plugins.classes
    noiseset: plugins.noiseset
    wavesets: ${wavesets}        # list of plugin references → list argument
  options:
    result_dir: ${result_dir}
    snr_range: ${snr_range}
    num_mixtures: 1000
```

```python
# myproject/cli.py
def make_mixtures(classes, noiseset, wavesets: list, result_dir: str,
                  snr_range: list, num_mixtures: int) -> None:
    ...
```

---

## 4. Callback pipeline

Transform plugins are wired into a dataset as a callback list; a third-party
`DataLoader` consumes it. The dataset doubles as its own `collate_fn` via
`__call__`.

```yaml
#!/bin/env inex

accelerator: cuda
loader_opts:
  batch_size: 32
  shuffle: true
  num_workers: 4
result_dir: ???

plugins:
  - device
  - augment
  - to_tensors
  - dataset
  - loader

device:
  module: torch/device
  options: { device: ${accelerator} }

augment:
  module: myproject.transform/Augment
  imports:
    device: plugins.device

to_tensors:
  module: myproject.transform/MakeTensors
  options:
    names: [mixture, targets, texts]

dataset:
  module: myproject.data/ChunkDataset
  imports:
    samples: plugins.manifests
    callbacks:
      - plugins.augment
      - plugins.to_tensors

loader:
  module: torch.utils.data.dataloader/DataLoader
  imports:
    dataset: plugins.dataset
    collate_fn: plugins.dataset      # same object, used as collate_fn
  options:
    __kwargs__: ${loader_opts}

execute:
  method: plugins.dataset/log_stats   # execute can target a method on a plugin
  options:
    path: ${result_dir}/info.txt
```

```python
# myproject/data/dataset.py
class ChunkDataset:
    def __init__(self, samples, callbacks=None):
        self.samples = samples
        self.callbacks = callbacks or []

    def __getitem__(self, idx):
        sample = self.samples[idx]
        for cb in self.callbacks:
            sample = cb(sample)
        return sample

    def __call__(self, batch):          # used as collate_fn
        return batch

    def log_stats(self, path: str): ...
```

---

## 5. Inference with checkpoint reload

Reload the model architecture from the training run's saved `final_config.yaml`
with `_import_`, then load weights into it. Best for scoring/eval/inference CLIs.

```yaml
#!/bin/env inex

random_seed: 0
cudnn_enabled: true
cudnn_benchmark: false
cudnn_deterministic: false

model_dir: ???
model_name: epoch=10.ckpt
feats_path: ???
result_dir: ???

plugins:
  - set_random_seed
  - initialize_torch
  - device
  - blank_model
  - model
  - feats
  - scores

set_random_seed:
  module: myproject.utils.init_torch/set_random_seed
  options: { seed: ${random_seed} }

initialize_torch:
  module: myproject.utils.init_torch/init_cudnn
  options:
    cudnn_enabled: ${cudnn_enabled}
    cudnn_benchmark: ${cudnn_benchmark}
    cudnn_deterministic: ${cudnn_deterministic}

device:
  module: torch/device
  options: { device: cuda }

blank_model:
  module: inex.helpers/_import_       # build the architecture from the training config
  options:
    plugin: model
    config: ${model_dir}/final_config.yaml

model:
  module: myproject.lightning.module/load_model
  imports:
    model: plugins.blank_model
  options:
    ckpt_path: ${model_dir}/${model_name}

feats:
  module: myproject.data/FeatureSet
  options: { pathname: ${feats_path} }

scores:
  module: myproject.infer/ScoreComputer
  imports:
    device: plugins.device
    model: plugins.model
    feats_set: plugins.feats
  options:
    batch_size: 256

execute:
  method: myproject.data.io/write_results
  imports:
    data_set: plugins.scores
  options:
    directory: ${result_dir}
```

```python
# myproject/lightning/module.py
def load_model(ckpt_path: str, model):
    """Load checkpoint weights into `model`; return the unwrapped nn.Module."""
    ...
```

Deriving `model_dir`/`result_dir` from a single checkpoint path is idiomatic:

```yaml
model_path: ???
model_dir:  ${__path_parent__:${model_path}}
model_stem: ${__path_stem__:${model_path}}
result_dir: ${model_dir}/infer_${model_stem}
```

---

## 6. Export nested attribute

Chain plugins to peel a sub-object out of a wrapper, then save it with a library
function. `exports: [model]` is present only because `inner_model` imports
`model.model`.

```yaml
#!/bin/env inex

model_dir: ???
model_name: epoch=10.ckpt
save_path: ${model_dir}/weights.pt

plugins:
  - blank_model
  - model
  - inner_model
  - state_dict

blank_model:
  module: inex.helpers/_import_
  options: { plugin: model, config: ${model_dir}/final_config.yaml }

model:
  module: myproject.lightning.module/load_model
  imports: { model: plugins.blank_model }
  exports: [model]                    # enables model.model below
  options: { ckpt_path: ${model_dir}/${model_name} }

inner_model:
  module: inex.helpers/assign
  imports: { value: model.model }

state_dict:
  module: plugins.inner_model/state_dict

execute:
  method: torch/save
  imports: { obj: plugins.state_dict }
  options: { f: ${save_path} }
```

---

## 7. Training stack

A full PyTorch/Lightning training pipeline ending in a project `train()`
function. Shows `evaluate` for the scheduler step count, `plugins.network/parameters`
for the optimizer, and callbacks as a list import.

```yaml
#!/bin/env inex

num_epochs: ???
lr: ???
train_dir: ???
accelerator: gpu
devices: 1

model_opts:
  hidden_dim: 128
  num_layers: 6

plugins:
  - set_random_seed
  - train_dataset
  - valid_dataset
  - total_steps
  - network
  - parameters
  - optimizer
  - scheduler
  - criterion
  - module
  - progress
  - logger

set_random_seed:
  module: myproject.utils.init_torch/set_random_seed
  options: { seed: 0 }

train_dataset:
  module: myproject.data/ListDataset
  exports: [length]                   # only because total_steps imports train_dataset.length
  imports: { batches: plugins.train_batches }

valid_dataset:
  module: myproject.data/ListDataset
  imports: { batches: plugins.valid_batches }

total_steps:
  module: inex.helpers/evaluate
  imports: { epoch_size: train_dataset.length }
  options:
    expression: 'int(1.001 * {num_epochs} * {epoch_size})'
    num_epochs: ${num_epochs}

network:
  module: myproject.models/Network
  options:
    __kwargs__: ${model_opts}

parameters:
  module: plugins.network/parameters

optimizer:
  module: torch.optim/Adam
  imports: { params: plugins.parameters }
  options: { lr: ${lr} }

scheduler:
  module: torch.optim.lr_scheduler/OneCycleLR
  imports:
    optimizer: plugins.optimizer
    total_steps: plugins.total_steps
  options: { max_lr: ${lr} }

criterion:
  module: torch.nn/MSELoss

module:
  module: myproject.lightning.module/Module
  imports:
    model: plugins.network
    train_dataset: plugins.train_dataset
    valid_dataset: plugins.valid_dataset
    optimizer: plugins.optimizer
    scheduler: plugins.scheduler
    criterion: plugins.criterion

progress:
  module: pytorch_lightning.callbacks.progress/TQDMProgressBar
  options: { refresh_rate: 5 }

logger:
  module: pytorch_lightning.loggers/CSVLogger
  options: { save_dir: ${train_dir} }

execute:
  method: myproject.lightning.trainer/train
  imports:
    module: plugins.module
    callbacks: [plugins.progress]
    logger: plugins.logger
  options:
    num_epochs: ${num_epochs}
    accelerator: ${accelerator}
    devices: ${devices}
    default_root_dir: ${train_dir}
```

```python
# myproject/lightning/trainer.py
def train(module, callbacks, logger, num_epochs, accelerator,
          devices, default_root_dir, **kwargs):
    import pytorch_lightning as L
    trainer = L.Trainer(max_epochs=num_epochs, accelerator=accelerator,
                        devices=devices, callbacks=callbacks, logger=logger,
                        default_root_dir=default_root_dir)
    trainer.fit(module)
```

---

## 8. Args and kwargs

```yaml
params: { a: 1, b: 2, c: [3, 4] }

plugins: [object1, object2, array, builtin_max]

object1:
  module: myproject.utils/Object
  options:
    __kwargs__: ${params}        # → Object(a=1, b=2, c=[3, 4])

object2:
  module: myproject.utils/Object
  imports:
    __kwargs__: ${params}        # same, via imports

array:
  module: numpy/array
  options:
    __args__: [[1, 2, 3]]        # → np.array([1, 2, 3])

builtin_max:
  module: /max
  options:
    __args__: [1, 2]             # → max(1, 2)

execute:
  method: inex.helpers/assign
  imports:
    value: [plugins.object1, plugins.object2, plugins.array, plugins.builtin_max]
```

A bare list as `options` becomes positional args: `options: [1]` → `f(1)`.

---

## 9. Resolvers and placeholders

```yaml
#!/bin/env inex

a: 2
b: 3
sum_ab: ${__evaluate__:'${a} + ${b}'}            # interpolate values into the expression

input_path: ???
model_path: ???

# Derived paths
out_dir: ${__path_parent__:${model_path}}/out_${__path_stem__:${input_path}}

# Pull a value from another config
learning_rate: ${__fetch__:conf/base.yaml, train.lr}

# Count lines, clamp parallelism
num_lines: ${__num_lines__:${input_path}}
num_jobs:  ${__evaluate__:'min(${num_lines}, 16)'}

# Preflight checks (assert-only resolvers)
exists:
  - ${__path_is_file__:${input_path}}
  - ${__path_is_file__:${model_path}}

plugins: [job]

job:
  module: myproject.cli/run
  options:
    out_dir: ${out_dir}
    num_jobs: ${num_jobs}
    lr: ${learning_rate}

execute:
  method: inex.helpers/assign
  imports: { value: plugins.job }
```

`???` forces resolution to fail until the value is supplied via `--merge` or
`-u`, enforcing required parameters.

---

## 10. Resumable stages

`is_done` skips a stage whose marker file exists; `before`/`after` manage
filesystem side effects. `title` prints a banner.

```yaml
#!/bin/env inex

work_dir: ???

plugins: [split, compute, finalize]

split:
  module: myproject.pipeline/split_data
  title: 'Splitting data'
  is_done: ${work_dir}/.done_split
  before:
    exists: ${work_dir}/input.list
    mkdir: ${work_dir}/parts
  options:
    input: ${work_dir}/input.list
    output_dir: ${work_dir}/parts

compute:
  module: myproject.pipeline/compute
  title: 'Computing'
  is_done: ${work_dir}/.done_compute
  options:
    parts_dir: ${work_dir}/parts
    output_dir: ${work_dir}/preds

finalize:
  module: myproject.pipeline/finalize
  is_done: ${work_dir}/.done_final
  after:
    delete: [${work_dir}/parts]
  options:
    preds_dir: ${work_dir}/preds
    result: ${work_dir}/result.txt

execute:
  method: inex.helpers/assign
  imports: { value: plugins.finalize }
```

---

## 11. Import with derived value

A real inference idiom: pull an architecture-derived value (e.g. `chunk_size`)
out of the saved training config by giving the `_import_` plugin `exports`, then
import it into the model.

```yaml
plugins: [chunker, blank_model, model]

chunker:
  module: inex.helpers/_import_
  exports: [chunk_size]                # surface chunk_size from the imported plugin
  options:
    plugin: chunker
    config: ${model_dir}/final_config.yaml

blank_model:
  module: inex.helpers/_import_
  options:
    plugin: model
    config: ${model_dir}/final_config.yaml

model:
  module: myproject.models/Model
  imports:
    image_size: chunker.chunk_size     # the matching reference
    weights: plugins.blank_model
  options:
    model_name: ${model_name}
```

---

## 12. Model factory

Select an implementation by name at config time. The factory receives `imports`
and `options` like any plugin.

```yaml
model_name: EfficientNet
num_classes: 10

plugins: [classes, model]

classes:
  module: myproject.data/ClassRegistry
  exports: [num_classes]
  options: { path: data/classes.txt }

model:
  module: myproject.models/from_name
  imports:
    output_dim: classes.num_classes
  options:
    model_name: ${model_name}
    dropout: 0.1
```

```python
# myproject/models/models.py
def from_name(model_name: str, output_dim: int, **kwargs):
    if model_name == 'EfficientNet':
        return EfficientNet(output_dim=output_dim, **kwargs)
    if model_name == 'ResNet':
        return ResNet(output_dim=output_dim, **kwargs)
    raise ValueError(f'Unknown model: {model_name}')
```

---

## 13. The exports rule in practice

Decide each plugin's `exports` by scanning the **whole** config for
`plugin_name.attr` references.

**Whole plugin passed — no exports.** Downstream Python reads attributes itself.

```yaml
plugins: [embedder, audio]

embedder:
  module: myproject.embeddings/Embedder
  options: { model_repo: ${embedding_repo} }

audio:
  module: myproject.audio/MonoWaveform
  options:
    audio_path: ${audio_path}
    channel: ${channel}

execute:
  method: myproject.cli/dump_single_speaker
  imports:
    embedder: plugins.embedder        # full objects — no exports needed
    audio: plugins.audio
  options:
    output_path: ${output_path}
```

**Attribute references — exports required, list only what is referenced.**

```yaml
plugins: [embedder, audio, segmenter]

embedder:
  module: myproject.embeddings/Embedder
  exports: [min_num_samples]          # because segmenter imports embedder.min_num_samples
  options: { model_repo: ${embedding_repo} }

audio:
  module: myproject.audio/MonoWaveform
  exports: [waveform, sample_rate]    # because segmenter imports both
  options:
    audio_path: ${audio_path}
    channel: ${channel}

segmenter:
  module: myproject.audio/RttmSegmenter
  imports:
    embedder: plugins.embedder
    waveform: audio.waveform
    sample_rate: audio.sample_rate
    min_num_samples: embedder.min_num_samples
  options: { rttm_path: ${rttm_path} }
```

Checklist for `audio`: export `waveform` and `sample_rate` (referenced); do
**not** export `num_samples`, `duration`, `audio_path`, `channel` unless
something references `audio.<that>`. A referenced-but-unexported attr is a
runtime error; an exported-but-unreferenced attr is dead weight.

---

## 14. Quick-start template

```yaml
#!/bin/env inex

__log_level__: INFO

input_path: ???
output_dir: ???

plugins:
  - inputs

inputs:
  module: myproject.data.io/load_inputs
  options:
    path: ${input_path}

execute:
  method: myproject.cli/process
  imports:
    inputs: plugins.inputs
  options:
    output_dir: ${output_dir}
```

```python
# myproject/data/io.py
def load_inputs(path: str) -> dict: ...

# myproject/cli.py
def process(inputs: dict, output_dir: str) -> None: ...
```

| Goal | Start from |
|------|-----------|
| Simple file processing | §1, §14 |
| Multi-step data prep | §2, §4 |
| Combine multiple inputs | §3 |
| Inference from a checkpoint | §5, §11 |
| Export model weights | §6 |
| Training (Lightning) | §7 |
| Dynamic / derived config values | §9 |
| Resumable pipeline stages | §10 |
| Swappable implementations | §12 |
| Getting `exports` right | §13 |
