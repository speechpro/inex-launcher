
![GitHub License](https://img.shields.io/github/license/speechpro/inex-launcher)
![PyPI - Version](https://img.shields.io/pypi/v/inex-launcher)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/inex-launcher.svg)

<a href="https://github.com/speechpro/inex-launcher/stargazers"><img src="https://img.shields.io/github/stars/speechpro/inex-launcher" alt="Stars Badge"/></a>
<a href="https://github.com/speechpro/inex-launcher/network/members"><img src="https://img.shields.io/github/forks/speechpro/inex-launcher" alt="Forks Badge"/></a>
<a href="https://github.com/speechpro/inex-launcher/pulls"><img src="https://img.shields.io/github/issues-pr/speechpro/inex-launcher" alt="Pull Requests Badge"/></a>
<a href="https://github.com/speechpro/inex-launcher/issues"><img src="https://img.shields.io/github/issues/speechpro/inex-launcher" alt="Issues Badge"/></a>
<a href="https://github.com/speechpro/inex-launcher/graphs/contributors"><img alt="GitHub contributors" src="https://img.shields.io/github/contributors/speechpro/inex-launcher?color=2b9348"></a>

# InEx Launcher

**InEx** (Initialize & Execute) is a lightweight, highly configurable Python launcher based on a microkernel architecture. You describe a pipeline in a single YAML (or JSON) file: a ordered list of **plugins** builds Python objects, then an **execute** block runs the final function.

Use it to build CLI utilities, data pipelines, training jobs, and inference tools without writing bespoke entry-point scripts for every experiment.

---

## Table of contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [Command-line interface](#command-line-interface)
- [Configuration overview](#configuration-overview)
- [Writing Python modules](#writing-python-modules)
- [Module reference syntax](#module-reference-syntax)
- [imports and options](#imports-and-options)
- [exports](#exports)
- [Plugin features](#plugin-features)
- [Built-in resolvers](#built-in-resolvers)
- [inex.helpers](#inexhelpers)
- [Third-party modules](#third-party-modules)
- [Examples](#examples)
- [Test suite](#test-suite)
- [Architecture](#architecture)

---

## Installation

```bash
pip install -U inex-launcher
```

Requirements: Python ≥ 3.8, `omegaconf`, `networkx`.

Development install from source:

```bash
git clone https://github.com/speechpro/inex-launcher.git
cd inex-launcher
pip install -e .
python -m pytest tests/
```

---

## Quick start

**1. Python module** (`myproject/cli.py`):

```python
def run(loader, epochs: int):
    data = loader.load()
    print(f"Training for {epochs} epochs on {len(data)} samples")
```

**2. Config** (`config.yaml`):

```yaml
#!/bin/env inex

epochs: 10

plugins:
  - loader

loader:
  module: myproject.data/Loader
  options:
    path: data/train.csv

execute:
  method: myproject.cli/run
  imports:
    loader: plugins.loader
  options:
    epochs: ${epochs}
```

**3. Run:**

```bash
inex config.yaml
inex config.yaml -u epochs=20
inex config.yaml -l DEBUG -s .
```

The `-s .` flag adds the current directory to `sys.path` so `myproject` is importable.

---

## Command-line interface

```
inex [-h] [--version] [--log-level LOG_LEVEL] [--log-path LOG_PATH]
     [--sys-path SYS_PATH] [--merge MERGE] [--update UPDATE]
     [--stop-after STOP_AFTER] [--final-path FINAL_PATH]
     config_path
```

| Option | Short | Description |
|--------|-------|-------------|
| `config_path` | — | Path to YAML/JSON config, or inline YAML string |
| `--log-level` | `-l` | Root logger level (`DEBUG`, `INFO`, `WARNING`, …) |
| `--log-path` | `-g` | Write log to file |
| `--sys-path` | `-s` | Paths to append to `sys.path` (separated by `:`, `;`, `,`, or `\|` on Linux) |
| `--merge` | `-m` | Merge additional config file(s); repeatable |
| `--update` | `-u` | Override values using dot notation (`key.subkey=value`); repeatable |
| `--stop-after` | `-a` | Stop after initializing the named plugin (debugging) |
| `--final-path` | `-f` | Write fully resolved config to file |

**Examples:**

```bash
# Merge override file and set nested values
inex config.yaml -m experiment.yaml -u trainer.epochs=20 model.hidden=64

# Dump resolved config without running execute (stop after last plugin)
inex config.yaml -a trainer -f final_config.yaml

# Config can also be inline YAML
inex "plugins: []"
```

Config-level alternatives to CLI flags:

```yaml
__log_level__: INFO
__sys_path__: .
```

---

## Configuration overview

A typical config has four layers:

```yaml
#!/bin/env inex              # optional shebang — marks file as inex config

# 1. Top-level parameters (hyperparameters, paths, flags)
batch_size: 32
data_path: ???                # required — must be set via -u or merge

# 2. Special keys
__log_level__: INFO
__mute__: [__all__]           # suppress per-plugin debug logs

# 3. Plugin chain (initialization order)
plugins:
  - loader
  - model
  - trainer

loader:
  module: myproject.data/Loader
  options:
    path: ${data_path}

model:
  module: myproject.nn/Model
  options:
    hidden: 128

trainer:
  module: myproject.training/Trainer
  imports:
    model: plugins.model
    data: plugins.loader
  options:
    epochs: 10

# 4. Final execution
execute:
  method: myproject.training/run
  imports:
    trainer: plugins.trainer
```

### Config keys reference

| Key | Scope | Purpose |
|-----|-------|---------|
| `plugins` | top | Ordered list of plugin names to initialize |
| `execute` | top | Final method to call after all plugins |
| `module` | plugin | Python class or function to instantiate |
| `method` | execute | Same as `module` — function to call at the end |
| `options` | plugin / execute | Keyword arguments (and `__args__` / `__kwargs__`) |
| `imports` | plugin / execute | Wire values from plugin state |
| `exports` | plugin | Publish attributes as `plugin_name.attr` |
| `depends` | plugin | Explicit dependency list (usually auto-inferred) |
| `is_done` | plugin | Skip plugin if marker file exists |
| `before` / `after` | plugin | Filesystem hooks (`exists`, `mkdir`, `delete`) |
| `title` | plugin | Print banner when plugin is created |
| `__log_level__` | top | Logging level |
| `__sys_path__` | top | Extra `sys.path` entries |
| `__mute__` / `__unmute__` | top | Control debug logging per plugin |

If `plugins:` is omitted, inex auto-detects plugin keys as any top-level dict containing `module` or `method`.

Placeholders: use `???` for values that must be overridden before resolution (via `-u` or `--merge`).

Interpolation: standard [OmegaConf](https://omegaconf.readthedocs.io/) syntax — `${param}`, `${..parent}`, `${list[0]}`.

---

## Writing Python modules

Design Python code so its constructor or function signature matches what the YAML will pass via `options` and `imports`.

### Binding styles

| YAML | Python | Result |
|------|--------|--------|
| `pkg.mod/MyClass` | `class MyClass: def __init__(self, ...)` | Instantiate class |
| `pkg.mod/my_func` | `def my_func(...)` | Call function |
| `pkg.mod/Class.method` | class method | Call bound method |
| `pkg.mod` (no `/Name`) | `def create(*args, **kwargs)` | Call module factory |
| `plugins.prev/method` | instance method | Call method on existing plugin |
| `plugins.model/parameters` | attribute | Access attribute on plugin instance |

**Class plugin:**

```python
# myproject/data.py
class Loader:
    def __init__(self, path: str):
        self.path = path

    def load(self):
        ...
```

```yaml
loader:
  module: myproject.data/Loader
  options:
    path: data/train.csv
```

**Function plugin:**

```python
# myproject/utils.py
def return_value(value):
    return value
```

```yaml
value1:
  module: myproject.utils/return_value
  options:
    value: 5
```

**Method on prior plugin:**

```python
class Tokenizer:
    def Load(self, model_file: str):
        ...
```

```yaml
load_tokenizer:
  module: plugins.tokenizer/Load
  options:
    model_file: model.bin
```

**Factory (uncommon):**

```python
def create(**kwargs):
    return MyClass(**kwargs)
```

```yaml
handler:
  module: myproject.handlers
  options:
    mode: train
```

### Design guidelines

1. **Plugin objects → `imports`**; literals and config values → `options`.
2. Parameter names in Python must match keys in `imports` and `options`.
3. Each plugin should return the object downstream steps need.
4. Prefer explicit `/ClassName` or `/function` over bare `pkg.mod` + `create()`.
5. Use `exports` only for attributes referenced as `plugin_name.attr` in the config (see [exports](#exports)).

---

## Module reference syntax

Format: `package.module/Name`

```
myproject.data/Loader          → class Loader from myproject.data
myproject.cli/run              → function run from myproject.cli
plugins.loader/process         → call .process() on plugins.loader instance
plugins.model/parameters       → access .parameters on plugins.model
numpy/array                    → third-party constructor
/max                           → Python builtin max()
```

**Indexing:** append `^N` to take the N-th element: `plugins.array^0` → `plugins.array[0]`.

**State keys** after plugin `foo` is created:

| Key | Content |
|-----|---------|
| `plugins.foo` | plugin return value |
| `foo.attr` | each name listed in `exports` |

---

## imports and options

### imports — wire plugin state

```yaml
trainer:
  module: myproject.training/Trainer
  imports:
    model: plugins.model          # whole plugin instance
    data: plugins.loader
    waveform: audio.waveform      # exported attribute (requires exports)
```

List form passes positional arguments:

```yaml
object1:
  module: myproject.utils/Object
  imports:
    __args__: [1, 2, [3, 4]]
```

### options — literals and configuration

```yaml
loader:
  module: myproject.data/Loader
  options:
    path: ${data_path}
    batch_size: 32
```

**Expand a dict into kwargs:**

```yaml
loader_opts:
  batch_size: 32
  shuffle: true

loader:
  module: torch.utils.data.dataloader/DataLoader
  options:
    __kwargs__: ${loader_opts}
```

**Positional arguments:**

```yaml
array:
  module: numpy/array
  options:
    __args__: [[1, 2, 3]]
```

A bare list as `options` is treated as `__args__`:

```yaml
array:
  module: numpy/array
  options: [[1, 2, 3]]
```

---

## exports

The `exports` field publishes selected attributes from a plugin instance so other plugins can import them as `plugin_name.attribute_name`.

### Rules

1. **Include** a property in `exports` only if some `imports` block in the **same config** references it as `plugin_name.property_name`.
2. **Exclude** properties that are not referenced that way.
3. **Runtime error** if a reference like `audio.waveform` exists but `waveform` is missing from the `audio` plugin's `exports`.

Importing the whole plugin (`plugins.audio`) does **not** require individual properties in `exports`.

### Whole plugin — no exports

```yaml
audio:
  module: myproject.audio/MonoWaveform
  options:
    audio_path: ${audio_path}

execute:
  method: myproject.cli/run
  imports:
    audio: plugins.audio
```

### Attribute references — exports required

```yaml
audio:
  module: myproject.audio/MonoWaveform
  exports: [waveform, sample_rate]
  options:
    audio_path: ${audio_path}

segmenter:
  module: myproject.audio/Segmenter
  imports:
    waveform: audio.waveform
    sample_rate: audio.sample_rate
```

### Special export values

| Value | Effect |
|-------|--------|
| `[model]` | publish `plugin_name.model` |
| `[length]` | publish `plugin_name.length` (e.g. for schedulers) |
| `[__all__]` | publish all non-callable public attributes |

Example from `tests/test_basic.yaml`:

```yaml
value2:
  module: tests.test_basic/Value
  exports: [value]
  options:
    value: 7

execute:
  method: inex.helpers/assign
  imports:
    value:
      - plugins.value1
      - value2.value
```

---

## Plugin features

### Skip-if-done (`is_done`)

Skip plugin initialization when a marker file already exists; touch the file after success.

```yaml
is_done: exp/run/.done

stage1:
  module: myproject.pipeline/run
  is_done: ${is_done}
  options:
    ...
```

### Filesystem hooks (`before` / `after`)

```yaml
stage1:
  module: myproject.pipeline/run
  before:
    exists: input/data.txt
    mkdir: output/
    delete: [output/old.txt, temp/]
  after:
    delete: [temp/]
```

Commands: `exists`, `mkdir`, `delete`.

### Dependency graph

`bind_plugins()` auto-builds dependencies from:

- `imports` values referencing `plugins.X` or `X.attr`
- `module: plugins.X/...` references
- explicit `depends: [...]` lists

Plugins must appear in `plugins:` before anything that imports them.

---

## Built-in resolvers

Registered at startup; use in config values as `${__name__:...}`:

| Resolver | Example |
|----------|---------|
| `__evaluate__` | `${__evaluate__:'{a} + {b}', a: 2, b: 3}` |
| `__fetch__` | `${__fetch__:other.yaml}` or `${__fetch__:other.yaml, key.subkey}` |
| `__getenv__` | `${__getenv__:HOME}` or `${__getenv__:PORT, int}` |
| `__setenv__` | `${__setenv__:MY_VAR, value}` |
| `__read_text__` | `${__read_text__:file.txt}` |
| `__num_lines__` | `${__num_lines__:file.txt}` |
| `__path_parent__` | `${__path_parent__:${config_path}}` |
| `__path_name__` | filename with extension |
| `__path_stem__` | filename without extension |
| `__path_suffix__` | file extension |
| `__path_is_file__` | assert path is a file |
| `__path_is_dir__` | assert path is a directory |
| `__path_exists__` | assert path exists |

Preflight checks:

```yaml
exists:
  - ${__path_is_file__:${data_path}}
```

See `tests/test_resolvers.yaml` for a full resolver demo.

---

## inex.helpers

Built-in utilities available as `inex.helpers/FunctionName`:

| Function | Purpose |
|----------|---------|
| `assign` | Return value unchanged; bundle results in `execute` |
| `evaluate` | Evaluate Python expression (`expression`, optional `initialize`) |
| `_import_` | Load a plugin from another inex config (cached per config path) |
| `compose` | Merge configs; optionally write result to file |
| `attribute` | Load attribute from module (`modname`, `attname`) |
| `show` | Debug-print plugin values (type, id, value) |
| `stage` | Run a sub-config with done-mark and filesystem checks |
| `execute` | Run external command via subprocess |
| `system` | Run shell command |

**`_import_` — reuse plugins from another config:**

```yaml
blank_model:
  module: inex.helpers/_import_
  options:
    plugin: model
    config: ${model_dir}/final_config.yaml

model:
  module: myproject.lightning/load_model
  imports:
    model: plugins.blank_model
  options:
    ckpt_path: ${ckpt_path}
```

**`compose` — merge and write config:**

```yaml
write_params:
  module: inex.helpers/compose
  options:
    config: ${params}
    result_path: exp/params.yaml
```

**`evaluate` — derived values:**

```yaml
total_steps:
  module: inex.helpers/evaluate
  imports:
    epoch_size: train_dataset.length
  options:
    expression: 'int(1.001 * {num_epochs} * {epoch_size})'
    num_epochs: ${num_epochs}
```

---

## Third-party modules

Any importable Python module can be used directly:

```yaml
device:
  module: torch/device
  options:
    device: cuda

loader:
  module: torch.utils.data.dataloader/DataLoader
  imports:
    dataset: plugins.dataset
  options:
    batch_size: 32

execute:
  method: torch/save
  imports:
    obj: plugins.state_dict
  options:
    f: ${save_path}
```

Built-in Python callables use a leading `/`:

```yaml
max_val:
  module: /max
  options:
    __args__: [1, 2]
```

---

## Examples

### Minimal — function and class with exports

From `tests/test_basic.yaml`:

```yaml
plugins:
  - value1
  - value2

value1:
  module: tests.test_basic/return_value
  options:
    value: 5

value2:
  module: tests.test_basic/Value
  exports: [value]
  options:
    value: 7

execute:
  method: inex.helpers/assign
  imports:
    value:
      - plugins.value1
      - value2.value
```

### Data pipeline with PyTorch

```yaml
plugins:
  - device
  - dataset
  - loader

device:
  module: torch/device
  options:
    device: cuda

dataset:
  module: myproject.data/MyDataset
  options:
    path: ${data_path}

loader:
  module: torch.utils.data.dataloader/DataLoader
  imports:
    dataset: plugins.dataset
  options:
    batch_size: 32
    shuffle: true

execute:
  method: myproject.cli/process
  imports:
    loader: plugins.loader
    device: plugins.device
  options:
    output_dir: ${output_dir}
```

### Inference with checkpoint reload

```yaml
plugins:
  - blank_model
  - model
  - features
  - scorer

blank_model:
  module: inex.helpers/_import_
  options:
    plugin: model
    config: ${model_dir}/final_config.yaml

model:
  module: myproject.lightning/load_model
  imports:
    model: plugins.blank_model
  options:
    ckpt_path: ${model_dir}/best.ckpt

features:
  module: myproject.data/FeatureSet
  options:
    path: ${feats_path}

scorer:
  module: myproject.infer/Scorer
  imports:
    model: plugins.model
    features: plugins.features

execute:
  method: myproject.cli/write_scores
  imports:
    scorer: plugins.scorer
  options:
    output_path: ${output_path}
```

### Training with scheduler step count

```yaml
train_dataset:
  module: myproject.data/Dataset
  exports: [length]
  options:
    path: ${train_path}

total_steps:
  module: inex.helpers/evaluate
  imports:
    epoch_size: train_dataset.length
  options:
    expression: 'int({num_epochs} * {epoch_size})'
    num_epochs: ${num_epochs}

scheduler:
  module: torch.optim.lr_scheduler/OneCycleLR
  imports:
    optimizer: plugins.optimizer
    total_steps: plugins.total_steps
  options:
    max_lr: ${lr}
```

---

## Test suite

The `tests/` directory contains contract tests — minimal YAML configs that exercise every feature. Run:

```bash
python -m pytest tests/
```

| Test file | Demonstrates |
|-----------|--------------|
| `test_basic.yaml` | plugins + execute; function vs class; exports |
| `test_args.yaml` | `__args__` via options and imports |
| `test_kwargs.yaml` | `__kwargs__` via options and imports |
| `test_pos_args.yaml` | mixed positional/kwargs |
| `test_export.yaml` | exports; `^index` on attributes |
| `test_item.yaml` | `plugins.value^N` indexing |
| `test_import.1–4.yaml` | `_import_` helper; cache sharing |
| `test_eval.yaml` | `evaluate`; plugin names with `+` |
| `test_resolvers.yaml` | all built-in resolvers |
| `test_fetch.*.yaml` | `__fetch__` resolver |
| `test_is_done.yaml` | `is_done`; `before`/`after` commands |
| `test_compose.*.yaml` | `???` placeholders; `compose` |
| `test_built_in.yaml` | `/max`, `/eval`, `/tuple` |
| `test_stop_after.yaml` | partial init (`-a` flag) |
| `test_numpy.yaml` | third-party module binding |

---

## Architecture

```
inex config.yaml
       │
       ▼
  load & resolve (OmegaConf + resolvers)
       │
       ▼
  bind_plugins() ──► dependency graph
       │
       ▼
  for each plugin in plugins[]:
       create_plugin() ──► state['plugins.<name>']
       │
       ▼
  create_plugin('execute') ──► final result
```

| Module | Role |
|--------|------|
| `inex/inex.py` | CLI, resolvers, `start()` |
| `inex/engine.py` | `execute()` — plugin loop |
| `inex/utils/configure.py` | `create_plugin()`, `bind_plugins()`, config loading |
| `inex/helpers.py` | `assign`, `compose`, `_import_`, `stage`, `execute`, … |
| `inex/utils/fsystem.py` | `before`/`after` filesystem commands |

---

## License

MIT — see [LICENSE](LICENSE).
