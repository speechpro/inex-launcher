# InEx Launcher — annotated examples

Self-contained config and Python examples for inex-launcher patterns. All snippets use a generic `myproject` package — adapt names to your project.

**Upstream reference:** The [inex-launcher repository](https://github.com/speechpro/inex-launcher) contains official contract tests and source code. Browse [`tests/*.yaml`](https://github.com/speechpro/inex-launcher/tree/main/tests) for minimal working configs that exercise each inex feature; see [reference.md](reference.md) for a feature-to-test mapping. The [README](https://github.com/speechpro/inex-launcher/blob/main/README.md) shows the canonical minimal training-style config.

---

## 1. Minimal utility — one plugin + execute function

**Pattern:** Load inputs with a small I/O plugin; run one Python function in `execute`.

Best for: pack, convert, write, or transform tools with a single data source.

```yaml
#!/bin/env inex

__log_level__: INFO

frequency: 16000
input_path: ???
output_dir: ???

exists:
  - ${__path_is_file__:${input_path}}

__mute__: [__all__]

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
from pathlib import Path
from typing import List, Union

def read_lines(pathnames: Union[str, List[str]]) -> List[str]:
    ...

# myproject/cli.py
def pack_items(
    items: List[str],
    output_dir: Union[str, Path],
    frequency: int = 16000,
) -> None:
    ...
```

**Takeaways:**
- One plugin builds data; `execute` is the CLI entry point
- Plugin objects go in `imports`; hyperparameters in `options`
- `exists:` preflight with `${__path_is_file__:...}`; `__mute__` reduces log noise

---

## 2. Data prep — linear pipeline with method plugin

**Pattern:** Init → build object → call method on it → prepare samples → execute writer.

Best for: tokenization, feature extraction, batch writing.

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
  module: plugins.tokenizer/Load          # method on prior plugin instance
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
    def __init__(self, vocab_size: int):
        ...

    def Load(self, model_file: str):
        # load weights; return self or None
        ...

# myproject/cli.py
def write_batches(data_set, sample_maker, batch_size: int, result_dir: str) -> None:
    ...
```

**Takeaways:**
- `plugins.tokenizer/Load` calls an instance method after construction
- `execute.method` is a plain function — the main side-effect entry point
- Required runtime params use `???` at top level

---

## 3. Multi-source execute function

**Pattern:** Several parallel data plugins feed one execute function.

Best for: mixing, merging, or combining multiple inputs.

```yaml
#!/bin/env inex

classes_path: ???
align_path: ???
noise_path: ???
data_root: ???
snr_range: [10, 20]
result_dir: ???

wavesets: [plugins.waveset1, plugins.waveset2, plugins.waveset3]

plugins:
  - classes
  - alignset
  - noiseset
  - waveset1
  - waveset2
  - waveset3

classes:
  module: myproject.data/Classes
  options:
    path: ${classes_path}

alignset:
  module: myproject.data/AlignSet
  options:
    pathname: ${align_path}

noiseset:
  module: myproject.data/WaveSet
  options:
    pathname: ${noise_path}

waveset1:
  module: myproject.data/WaveSet
  options:
    pathname: ${data_root}/part1.scp

waveset2:
  module: myproject.data/WaveSet
  options:
    pathname: ${data_root}/part2.scp

waveset3:
  module: myproject.data/WaveSet
  options:
    pathname: ${data_root}/part3.scp

execute:
  method: myproject.cli/make_mixtures
  imports:
    classes: plugins.classes
    alignset: plugins.alignset
    noiseset: plugins.noiseset
    wavesets: ${wavesets}
  options:
    result_dir: ${result_dir}
    snr_range: ${snr_range}
    num_mixtures: 1000
```

```python
# myproject/cli.py
def make_mixtures(
    classes,
    alignset,
    noiseset,
    wavesets: list,
    result_dir: str,
    snr_range: tuple,
    num_mixtures: int,
) -> None:
    ...
```

**Takeaways:**
- Reuse the same class (`WaveSet`) with different plugin keys
- Top-level `${wavesets}` list can hold `plugins.*` references
- Domain logic stays in one execute function

---

## 4. Callback pipeline on dataset

**Pattern:** Transform plugins wired as callback lists into a dataset; third-party DataLoader.

Best for: audio/ML pipelines with sample-level and batch-level transforms.

```yaml
#!/bin/env inex

accelerator: cuda
trim_len: 0.01
loader_opts:
  batch_size: 32
  shuffle: true
  num_workers: 4
result_dir: ???

plugins:
  - device
  - align_set
  - update_ali
  - manifests
  - augment
  - to_tensors
  - dataset
  - loader

device:
  module: torch/device
  options:
    device: ${accelerator}

align_set:
  module: myproject.data/AlignSet
  options:
    path: ???

update_ali:
  module: plugins.align_set/insert_sil
  imports:
    reco2dur: plugins.reco2dur
  options:
    trim_len: ${trim_len}

augment:
  module: myproject.transform/Augment
  imports:
    device: plugins.device
    noise_set: plugins.noise_set
    rir_set: plugins.rir_set

to_tensors:
  module: myproject.transform/MakeTensors
  options:
    names: [mixture, targets, texts]

dataset:
  module: myproject.data/ChunkDataset
  imports:
    wav_scp: plugins.wav_scp
    samples: plugins.manifests
    callbacks:
      - plugins.augment
      - plugins.to_tensors

loader:
  module: torch.utils.data.dataloader/DataLoader
  imports:
    dataset: plugins.dataset
    collate_fn: plugins.dataset
  options:
    __kwargs__: ${loader_opts}

execute:
  method: plugins.manifests/log_stats
  options:
    path: ${result_dir}/info.txt
```

```python
# myproject/data/alignment.py
class AlignSet:
    def insert_sil(self, reco2dur, trim_len: float = 0.0):
        ...

# myproject/data/dataset.py
class ChunkDataset:
    def __init__(self, wav_scp, samples, callbacks=None):
        self.callbacks = callbacks or []

    def __getitem__(self, idx):
        sample = ...
        for cb in self.callbacks:
            sample = cb(sample)
        return sample

    def __call__(self, batch):       # used as collate_fn
        ...
        return batch

    def log_stats(self, path: str):
        ...
```

**Takeaways:**
- `plugins.X/method` for in-place processing without new wrapper classes
- Callback list avoids N nearly identical pipeline plugins
- `DataLoader` used directly from PyTorch
- `execute` can target a method on any prior plugin

---

## 5. Inference with checkpoint import

**Pattern:** Reload model architecture from a saved training config; run scoring; write output.

Best for: evaluation, scoring, inference CLIs.

```yaml
#!/bin/env inex

random_seed: 0
model_dir: ???
model_name: epoch=10.ckpt
feats_path: ???
result_path: ???

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
  options:
    seed: ${random_seed}

initialize_torch:
  module: myproject.utils.init_torch/init_cudnn
  options:
    cudnn_enabled: true
    cudnn_benchmark: false
    cudnn_deterministic: false

device:
  module: torch/device
  options:
    device: cuda

blank_model:
  module: inex.helpers/_import_
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
  options:
    pathname: ${feats_path}

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
    file_path: ${result_path}
```

```python
# myproject/lightning/module.py
def load_model(ckpt_path: str, model):
    """Load checkpoint into model; return unwrapped nn.Module."""
    ...

# myproject/infer.py
class ScoreComputer:
    def __init__(self, device, model, feats_set, batch_size: int):
        ...
```

**Takeaways:**
- `_import_` loads the `model` plugin definition from a prior training YAML
- `load_model(ckpt_path, model)` strips training wrappers (e.g. Lightning)
- Scoring is a class plugin; I/O is a separate function in `execute`

---

## 6. Export nested attribute for third-party execute

**Pattern:** Chain plugins to extract a sub-object; save with a library function.

Best for: checkpoint export, weight extraction, artifact saving.

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
  options:
    plugin: model
    config: ${model_dir}/final_config.yaml

model:
  module: myproject.lightning.module/load_model
  imports:
    model: plugins.blank_model
  exports: [model]
  options:
    ckpt_path: ${model_dir}/${model_name}

inner_model:
  module: inex.helpers/assign
  imports:
    value: model.model

state_dict:
  module: plugins.inner_model/state_dict

execute:
  method: torch/save
  imports:
    obj: plugins.state_dict
  options:
    f: ${save_path}
```

**Takeaways:**
- `exports: [model]` enables `model.model` in downstream `imports` — list `model` only because `inner` references `model.model`
- `inex.helpers/assign` peels nested attributes
- `plugins.inner_model/state_dict` calls a method on the nn.Module
- `execute` can use third-party functions (`torch/save`) directly

---

## 7. Callback-composed dataset

**Pattern:** Lists of transform plugins passed as `sample_cbs` / `batch_cbs`.

Best for: training data pipelines where transforms are easy to reorder in YAML.

```yaml
plugins:
  - add_masks
  - set_target
  - add_embed
  - make_tensors
  - normalize

valid_dataset:
  module: myproject.data/ListDataset
  exports: [length]
  imports:
    batches: plugins.valid_batches
    sample_cbs:
      - plugins.add_masks
      - plugins.set_target
      - plugins.add_embed
    batch_cbs:
      - plugins.make_tensors
      - plugins.normalize
```

```python
# myproject/data/dataset.py
from torch.utils.data import Dataset

class ListDataset(Dataset):
    def __init__(self, batches, sample_cbs=None, batch_cbs=None):
        self.batches = batches
        self.sample_cbs = sample_cbs or []
        self.batch_cbs = batch_cbs or []

    @property
    def length(self):
        return len(self.batches)

    def __len__(self):
        return self.length

    def __getitem__(self, item):
        batch = load_batch(self.batches[item])
        for callback in self.sample_cbs:
            batch = callback(batch)
        return batch

    def __call__(self, batch):          # used as collate_fn
        for callback in self.batch_cbs:
            batch = callback(batch)
        return batch
```

**Takeaways:**
- Each transform is its own plugin — reorder by editing YAML lists
- Same dataset plugin serves as `collate_fn` via `__call__`
- `exports: [length]` exposes size for scheduler step calculation — list `length` only because `total_steps` references `train_dataset.length`

---

## 8. Training config — Lightning module + trainer execute

**Pattern:** Full training stack ending with a project `train()` function.

Best for: PyTorch Lightning (or similar) training CLIs.

```yaml
#!/bin/env inex

num_epochs: ???
lr: ???
train_dir: ???
accelerator: cuda
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
  - loss_func
  - module
  - progress
  - logger

set_random_seed:
  module: myproject.utils.init_torch/set_random_seed
  options:
    seed: 0

train_dataset:
  module: myproject.data/ListDataset
  exports: [length]
  imports:
    batches: plugins.train_batches

total_steps:
  module: inex.helpers/evaluate
  imports:
    epoch_size: train_dataset.length
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
  imports:
    params: plugins.parameters
  options:
    lr: ${lr}

scheduler:
  module: torch.optim.lr_scheduler/OneCycleLR
  imports:
    optimizer: plugins.optimizer
    total_steps: plugins.total_steps
  options:
    max_lr: ${lr}

module:
  module: myproject.lightning.module/Module
  imports:
    model: plugins.network
    train_dataset: plugins.train_dataset
    valid_dataset: plugins.valid_dataset
    optimizer: plugins.optimizer
    scheduler: plugins.scheduler
    loss_func: plugins.loss_func

progress:
  module: pytorch_lightning.callbacks.progress/TQDMProgressBar
  options:
    refresh_rate: 5

logger:
  module: pytorch_lightning.loggers/CSVLogger
  options:
    save_dir: ${train_dir}

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
# myproject/lightning/module.py
class Module(L.LightningModule):
    def __init__(self, model, train_dataset, valid_dataset,
                 optimizer, scheduler, loss_func):
        ...

# myproject/lightning/trainer.py
def train(module, callbacks, logger, num_epochs, accelerator,
          devices, default_root_dir, **kwargs):
    trainer = L.Trainer(...)
    trainer.fit(module)
```

**Takeaways:**
- `exports: [length]` + `inex.helpers/evaluate` for scheduler step count
- `plugins.network/parameters` wires PyTorch optimizer
- `Module` plugin aggregates training dependencies via `imports`
- `execute` delegates to a project `train()` function, not Lightning directly

---

## 9. `__args__` and `__kwargs__`

**Pattern:** Pass positional arguments or expand a dict into constructor kwargs.

```yaml
params:
  a: 1
  b: 2
  c: [3, 4]

plugins:
  - object1
  - object2

object1:
  module: myproject.utils/Object
  options:
    __kwargs__: ${params}       # expand dict: a=1, b=2, c=[3,4]

object2:
  module: myproject.utils/Object
  imports:
    __kwargs__: ${params}       # same via imports

execute:
  method: inex.helpers/assign
  imports:
    value: [plugins.object1, plugins.object2]
```

Positional args:

```yaml
object3:
  module: numpy/array
  options:
    __args__: [[1, 2, 3]]       # np.array([1, 2, 3])

object4:
  module: myproject.utils/Object
  options:
    d: 5
    e: 6
    __args__: [1, 2, [3, 4]]
    __kwargs__: {f: 7, g: 8}
```

**Takeaways:**
- `__kwargs__: ${dict}` splats a top-level or nested dict into kwargs
- `__args__` in `options` or `imports` supplies positional arguments
- Works with both `options` and `imports` on the plugin block

---

## 10. Built-in resolvers

**Pattern:** Compute values at config-resolve time using inex resolvers.

```yaml
#!/bin/env inex

a: 2
b: 3
evaluate1: ${__evaluate__:'${a}^2 + ${b}'}
evaluate2: ${__evaluate__:'int(np.sum(np.array([1, 2, 3])))', [import numpy as np]}

seven_set: ${__setenv__:Seven, 7}
seven_get: ${__getenv__:Seven, int}

input_path: /data/input.txt
path_parent: ${__path_parent__:${input_path}}
path_stem: ${__path_stem__:${input_path}}

execute:
  method: inex.helpers/assign
  options:
    value:
      evaluate1: ${evaluate1}
      evaluate2: ${evaluate2}
      seven_get: ${seven_get}
      path_parent: ${path_parent}
      path_stem: ${path_stem}
```

Load value from external config:

```yaml
shared_params: ${__fetch__:conf/base.yaml}
learning_rate: ${__fetch__:conf/base.yaml, train.lr}
```

**Takeaways:**
- Resolvers run during config resolution, before plugins are created
- `${__evaluate__:...}` supports `initialize:` list for imports (e.g. `import numpy as np`)
- `${__path_*__}` resolvers assert paths exist — useful in `exists:` preflight lists
- `${__fetch__:file.yaml, key.subkey}` pulls values from other config files

---

## 11. Required placeholders (`???`)

**Pattern:** Mark parameters that must be overridden before the config can resolve.

```yaml
option1: ???
option2: ???

plugins:
  - value1
  - value2

value1:
  module: inex.helpers/assign
  options:
    value: ${option1}

value2:
  module: inex.helpers/assign
  options:
    value: ${option2}

execute:
  method: inex.helpers/assign
  imports:
    value:
      a: plugins.value1
      b: plugins.value2
```

Override at run time via merge file or `-u option1=foo -u option2=bar`.

**Takeaways:**
- `???` fails resolution if not set — enforces required CLI parameters
- Pair with sensible defaults for optional params at the top level

---

## 12. Skip-if-done with before/after hooks

**Pattern:** Skip plugin initialization when a marker file exists; run filesystem prep/cleanup.

```yaml
is_done: exp/run/.done

plugins:
  - stage1
  - stage2

stage1:
  module: myproject.pipeline/run_stage
  is_done: ${is_done}
  before:
    exists: input/data.txt
    delete: output/old.txt
    mkdir: output/temp
  after:
    exists: output/temp
    delete: [output/temp]
  options:
    input: input/data.txt
    output: output/result.txt

stage2:
  module: myproject.pipeline/finalize
  is_done: ${is_done}
  options:
    path: output/result.txt

execute:
  method: inex.helpers/assign
  imports:
    value: plugins.stage2
```

**Takeaways:**
- `is_done:` path — if file exists, plugin returns `None` and skips work
- `before:` / `after:` support `exists`, `mkdir`, `delete`
- All plugins sharing the same `is_done` marker skip together once done

---

## 13. Sub-config import (`_import_`)

**Pattern:** Load a plugin from another inex config; cache shared across imports of the same config path.

Sub-config (`conf/train_model.yaml`):

```yaml
plugins:
  - model

model:
  module: myproject.models/Network
  options:
    hidden_dim: 128
```

Main config:

```yaml
plugins:
  - blank_model
  - loaded_weights

blank_model:
  module: inex.helpers/_import_
  options:
    plugin: model
    config: conf/train_model.yaml

loaded_weights:
  module: myproject.lightning.module/load_model
  imports:
    model: plugins.blank_model
  options:
    ckpt_path: checkpoints/best.ckpt

execute:
  method: myproject.infer/predict
  imports:
    model: plugins.loaded_weights
  options:
    input_path: ???
    output_path: ???
```

Import multiple plugins from the same sub-config:

```yaml
value1:
  module: inex.helpers/_import_
  options:
    config: conf/shared.yaml
    plugin: encoder

value2:
  module: inex.helpers/_import_
  options:
    config: conf/shared.yaml
    plugin: decoder
```

**Takeaways:**
- Sub-config must list the target plugin in its own `plugins:` section
- Same `config` path shares plugin cache — dependencies initialized once
- Optional kwargs on `_import_` merge into the sub-config

---

## 14. Meta-config with compose

**Pattern:** Build or merge configs programmatically inside a plugin chain.

```yaml
params:
  train:
    lr: 0.001
    epochs: 10
  model:
    hidden_dim: 256

params_path: exp/run/params.yaml
train_config: exp/run/train.yaml

plugins:
  - write_parameters
  - make_train_config

write_parameters:
  module: inex.helpers/compose
  options:
    config: ${params}
    result_path: ${params_path}

make_train_config:
  module: inex.helpers/compose
  options:
    config_path: conf/train_template.yaml
    override:
      params_path: ${params_path}
    result_path: ${train_config}

execute:
  module: inex.helpers/_import_
  options:
    plugin: train
    config: ${train_config}
```

**Takeaways:**
- `compose` merges dicts, files, and dot-list overrides
- `result_path` writes the resolved YAML for inspection or reuse
- `check_file`: `override`, `fail_if_exists`, or `fail_if_different`

---

## 15. Model factory

**Pattern:** Select model architecture by name at config time.

```yaml
model_name: EfficientNet
num_classes: 10

plugins:
  - classes
  - model

classes:
  module: myproject.data/ClassRegistry
  options:
    path: data/classes.txt

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

**Takeaways:**
- Factory function receives `imports` and `options` like any other module
- Swap architecture by changing `model_name` in YAML or via `-u`

---

## 16. Exports: only referenced attributes

**Pattern:** List a property in `exports` only when some `imports` block in the same config references it as `plugin_name.property_name`. Omit properties that are not referenced. Missing `exports` entries for referenced properties cause a runtime error.

### Whole plugin passed — no exports

When downstream code receives the full plugin via `plugins.<name>`, individual properties do not need to be exported:

```yaml
plugins:
  - device
  - embedder
  - audio

device:
  module: torch/device
  options:
    device: cuda

embedder:
  module: myproject.embeddings/Embedder
  imports:
    device: plugins.device
  options:
    model_repo: ${embedding_repo}

audio:
  module: myproject.audio/MonoWaveform
  options:
    audio_path: ${audio_path}
    channel: ${channel}

execute:
  method: myproject.cli/dump_single_speaker
  imports:
    embedder: plugins.embedder
    audio: plugins.audio
  options:
    output_path: ${output_path}
```

The Python `dump_single_speaker` function receives plugin objects and reads attributes in code — no `exports` on `audio` or `embedder`.

### Attribute references — exports required

When `imports` references specific attributes as `plugin_name.attr`, list **only those** attrs in `exports`:

```yaml
plugins:
  - device
  - embedder
  - audio
  - segmenter

device:
  module: torch/device
  options:
    device: cuda

embedder:
  module: myproject.embeddings/Embedder
  imports:
    device: plugins.device
  exports: [dimension, min_num_samples]
  options:
    model_repo: ${embedding_repo}

audio:
  module: myproject.audio/MonoWaveform
  exports: [waveform, sample_rate]
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
  options:
    rttm_path: ${rttm_path}

execute:
  method: myproject.cli/dump_rttm_speakers
  imports:
    segmenter: plugins.segmenter
  options:
    output_path: ${output_path}
```

**Checklist for `audio` plugin:**
- `waveform` → in `exports` because `segmenter` imports `audio.waveform`
- `sample_rate` → in `exports` because `segmenter` imports `audio.sample_rate`
- `num_samples`, `duration_seconds`, `audio_path`, `channel` → **not** in `exports` if nothing references `audio.num_samples`, etc.

**Checklist for `embedder` plugin:**
- `dimension`, `min_num_samples` → in `exports` if referenced as `embedder.dimension`, `embedder.min_num_samples`
- Do not export `metric`, `embedding_path` unless some `imports` block references them

### Function vs class with one exported attr

```yaml
plugins:
  - scalar
  - wrapper

scalar:
  module: myproject.utils/return_value
  options:
    value: 5

wrapper:
  module: myproject.utils/ValueHolder
  exports: [value]
  options:
    value: 7

execute:
  method: inex.helpers/assign
  imports:
    value:
      - plugins.scalar
      - wrapper.value
```

```python
def return_value(value):
    return value

class ValueHolder:
    def __init__(self, value):
        self.value = value
```

**Takeaways:**
- `exports: [value]` is required because `execute` imports `wrapper.value`
- Functions work as plugins when referenced as `pkg.mod/func`
- Scan the entire config before finalizing each plugin's `exports` list

---

## 17. Plugin indexing (`^N`) and `exports: [__all__]`

**Pattern:** Index into plugin results; export all public attributes.

```yaml
plugins:
  - array
  - first_elem
  - shape_dim

array:
  module: inex.helpers/evaluate
  options:
    initialize:
      - import numpy as np
    expression: 'np.array([1, 2, 3])'

first_elem:
  module: inex.helpers/assign
  imports:
    value: plugins.array^0          # plugins.array[0]

shape_dim:
  module: inex.helpers/assign
  imports:
    value: array_obj.shape^0       # after exports below

array_obj:
  module: numpy/array
  exports: [__all__]
  options:
    __args__: [[1, 2, 3]]

execute:
  method: inex.helpers/assign
  imports:
    value:
      first: plugins.first_elem
      shape: plugins.shape_dim
```

**Takeaways:**
- `plugins.name^N` indexes into the plugin result
- `exports: [__all__]` publishes all non-callable public attributes — use only when multiple attrs are referenced as `plugin_name.attr`; prefer an explicit list matching actual references
- Attribute references (`array_obj.shape^0`) use exported state keys

---

## 18. Built-in Python plugins

**Pattern:** Use Python builtins directly without wrapper modules.

```yaml
plugins:
  - max_val
  - eval_expr
  - tuple_val

max_val:
  module: /max
  options:
    __args__: [1, 2]

eval_expr:
  module: /eval
  options:
    __args__: ['min(5 * 3, 2 * 10)']

tuple_val:
  module: /tuple
  options:
    __args__: [[1, 2, 3]]

execute:
  method: inex.helpers/assign
  imports:
    value:
      max: plugins.max_val
      eval: plugins.eval_expr
      tuple: plugins.tuple_val
```

**Takeaways:**
- Leading `/` refers to a Python builtin or eval target
- Useful for quick arithmetic or literal construction in configs
- Prefer project modules for anything non-trivial

---

## 19. Stacked dataset plugins (training prep)

**Pattern:** Many small data plugins compose into train/valid datasets.

Best for: complex feature pipelines (multi-file inputs, fusion, masking).

```yaml
plugins:
  - valid_feats
  - valid_channels
  - valid_align
  - valid_speakers
  - valid_dataset
  - train_feats
  - train_channels
  - train_align
  - train_speakers
  - train_dataset

valid_feats:
  module: myproject.data/FeatureSet
  options:
    path: ${valid_feats_path}

valid_channels:
  module: myproject.data/Channels
  imports:
    feats: plugins.valid_feats

valid_align:
  module: myproject.data/Alignment
  options:
    path: ${valid_align_path}

valid_speakers:
  module: myproject.data/Speakers
  imports:
    align: plugins.valid_align

valid_dataset:
  module: myproject.data/FusionDataset
  imports:
    channels: plugins.valid_channels
    speakers: plugins.valid_speakers
    align: plugins.valid_align

train_feats:
  module: myproject.data/FeatureSet
  options:
    path: ${train_feats_path}

train_channels:
  module: myproject.data/Channels
  imports:
    feats: plugins.train_feats

train_align:
  module: myproject.data/Alignment
  options:
    path: ${train_align_path}

train_speakers:
  module: myproject.data/Speakers
  imports:
    align: plugins.train_align

train_dataset:
  module: myproject.data/FusionDataset
  imports:
    channels: plugins.train_channels
    speakers: plugins.train_speakers
    align: plugins.train_align
    masker: plugins.va_masker
```

**Takeaways:**
- One plugin per logical data source — easy to test and swap
- Parallel valid/train chains share the same class types
- Final dataset plugin aggregates all upstream pieces via `imports`

---

## 20. Quick-start template

Copy and adapt for a new CLI utility:

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
def load_inputs(path: str) -> dict:
    ...

# myproject/cli.py
def process(inputs: dict, output_dir: str) -> None:
    ...
```

---

## Pattern selection guide

| Goal | Start with section |
|------|---------------------|
| Simple file processing | §1, §20 |
| Multi-step data pipeline | §2, §4 |
| Combine multiple inputs | §3 |
| ML inference from checkpoint | §5, §13 |
| Export model weights | §6 |
| Flexible transforms | §7 |
| Training with Lightning | §8, §19 |
| Dynamic config values | §10, §11 |
| Resumable pipeline stages | §12 |
| Reuse another config's plugins | §13 |
| Generate configs from templates | §14 |
| Swappable model architectures | §15 |
| Exports: only referenced attrs | §16 |

---

## Upstream examples on GitHub

When you need to confirm exact inex behavior, prefer the official tests over guessing:

| What you need | GitHub link |
|---------------|-------------|
| Minimal plugins + execute | [README.md](https://github.com/speechpro/inex-launcher/blob/main/README.md) |
| All contract test YAMLs | [tests/](https://github.com/speechpro/inex-launcher/tree/main/tests) |
| How plugins are instantiated | [inex/utils/configure.py](https://github.com/speechpro/inex-launcher/blob/main/inex/utils/configure.py) |
| Helper implementations | [inex/helpers.py](https://github.com/speechpro/inex-launcher/blob/main/inex/helpers.py) |
| Install | `pip install -U inex-launcher` ([PyPI](https://pypi.org/project/inex-launcher/)) |
