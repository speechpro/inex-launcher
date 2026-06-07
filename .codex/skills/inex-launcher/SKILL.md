---
name: inex-launcher
description: Guidance for building Python CLI utilities with InEx Launcher YAML configs. Use when Codex needs to create or review an InEx/inex-launcher based utility, write importable Python modules for InEx plugins, design plugin chains with options/imports/exports/execute, debug InEx config wiring, or explain how to structure a YAML/JSON InEx configuration. Focus on Python module and config design, not shell wrappers, Slurm, or operational launch scripts.
---

# InEx Launcher

## Purpose

Use InEx Launcher to turn an importable Python pipeline into a config-driven CLI utility. InEx loads an OmegaConf YAML/JSON config, creates plugin objects in dependency order, stores them in state as `plugins.<name>`, optionally exports selected attributes as `<name>.<attr>`, then calls the final `execute` method.

Use the upstream source as the source of truth when exact behavior matters: `https://github.com/speechpro/inex-launcher.git`.

## Design Workflow

1. Define the CLI utility as a pure Python action: a final function such as `run(...)`, `train(...)`, `decode(...)`, `write_data(...)`, or `main(...)`.
2. Split setup into importable plugin units: data readers, devices, tokenizers, models, datasets, optimizers, postprocessors, writers, and configuration factories.
3. Give each plugin a small constructor/function signature that matches YAML `options` and `imports`.
4. Keep user-tunable values at the top level of the config. Use `???` for required values that must be supplied by overrides or merged configs.
5. Put plugin names in `plugins:` in the order a human would read the pipeline. InEx also infers dependencies from `imports`, `module: plugins.x/...`, and `depends`.
6. Wire objects with `imports:` instead of recreating them from paths or global state.
7. Use `execute:` for the final user-facing action. Keep it thin: it should receive assembled objects and ordinary options, then do the work.
8. Validate export references: every `name.attr` import must be backed by `exports: [attr]` on plugin `name`; do not export attributes that are not imported elsewhere.

## Python Modules

Write normal importable Python. InEx resolves `package.module/Name` with Python import mechanics, so the project package must be importable through installation, `PYTHONPATH`, config-level `__sys_path__`, or the caller's environment.

Prefer these shapes:

```python
def load_items(path: str, shuffle: bool = False):
    ...
    return items


class Processor:
    def __init__(self, model, threshold: float):
        self.model = model
        self.threshold = threshold

    @property
    def labels(self):
        return self.model.labels

    def run(self, data):
        ...


def write_results(data_set, output_dir: str, compress: bool = False):
    ...
```

Design rules:

- Use explicit keyword parameters for values passed by `options:`.
- Use parameters for real Python objects passed by `imports:`.
- Use `**kwargs` only when a config contains a grouped option dictionary such as `__kwargs__: ${model_opts}`.
- Return reusable objects from setup plugins; do not hide them in module globals.
- Make side-effect plugins idempotent where possible. They may return `None`, but downstream plugins can only import useful values if a real object or exported attribute exists.
- Put long-running work in the final `execute` function or in a clearly named method called by `execute`.
- Add properties or an `export(self, name)` method when downstream config needs selected derived values.
- Avoid parsing command-line arguments inside plugin modules. InEx owns config loading; Python modules should accept already-resolved values and objects.

## Module References

Use these reference forms in `module:` or `method:`:

```yaml
reader:
  module: mypkg.data/read_table        # call function

dataset:
  module: mypkg.data/Dataset           # instantiate class

factory:
  module: mypkg.factory                # call module.create(...)

params:
  module: plugins.model/parameters     # call method on plugin object

first_item:
  module: mypkg.load/load_items^0      # select item from returned sequence
```

If `module` has no `/Name`, InEx imports the module and calls its `create(*args, **kwargs)` factory. If the module starts with `plugins.`, InEx calls an existing plugin object or one of its methods.

## Config Pattern

Use this shape for new utilities:

```yaml
#!/bin/env inex

__log_level__: INFO
__mute__: [__all__]

input_path: ???
checkpoint_path: ???
output_dir: ???
threshold: 0.5

exists:
  - ${__path_is_file__:${input_path}}
  - ${__path_is_file__:${checkpoint_path}}

plugins:
  - items
  - model
  - processor

items:
  module: mypkg.io/load_items
  options:
    path: ${input_path}

model:
  module: mypkg.model/load_model
  exports: [labels]
  options:
    checkpoint: ${checkpoint_path}

processor:
  module: mypkg.pipeline/Processor
  imports:
    model: plugins.model
  options:
    threshold: ${threshold}

execute:
  method: mypkg.cli/write_results
  imports:
    data_set: plugins.items
    processor: plugins.processor
    labels: model.labels
  options:
    output_dir: ${output_dir}
```

Notes:

- `plugins.<name>` imports the object returned by plugin `<name>`.
- `<name>.<attr>` imports an exported attribute from plugin `<name>`.
- Lists and dictionaries under `imports:` are recursively resolved, so callbacks, datasets, metric maps, and nested bundles can contain plugin references.
- `options:` may be a list for positional arguments, a mapping for keyword arguments, or a mapping containing `__args__` and `__kwargs__`.
- `imports:` also supports `__args__` and `__kwargs__`.
- Use `value^0` or `value^key` to index into an imported sequence or mapping after it has been placed in state.
- Use `depends:` only for dependencies that are not visible through `imports` or `module: plugins.x/...`.

## Exports

Treat `exports` as part of the public interface of a plugin.

```yaml
audio:
  module: mypkg.audio/MonoWaveform
  exports: [waveform]
  options:
    audio_path: ${audio_path}
    channel: ${channel}

features:
  module: mypkg.features/compute
  imports:
    waveform: audio.waveform
```

Rules:

- If any config import references `audio.waveform`, plugin `audio` must list `waveform` in `exports`.
- If no config import references `audio.waveform`, do not list `waveform` in `exports`.
- Exported attributes are resolved from `plugin.export(attr)` first, then `getattr(plugin, attr)`.
- `exports: [__all__]` publishes all dictionary items, instance `__dict__` values, or non-callable public attributes. Use it sparingly because it makes the plugin interface broad and easier to misuse.
- `exports: []` is usually unnecessary; omit `exports` unless a downstream reference needs exported attributes.

## Useful Built-ins

Use `inex.helpers/assign` to pass through or bundle values. Use `inex.helpers/show` for quick object inspection. Use `inex.helpers/attribute` to load a module attribute by string names. Use `inex.helpers/_import_` only when a config intentionally reuses a plugin from another InEx config; keep ordinary utilities self-contained when possible.

Built-in OmegaConf resolvers available during config resolution include:

- `${__evaluate__:...}` for small Python expressions.
- `${__fetch__:path,to.value}` to fetch config values from another file.
- `${__getenv__:NAME,cast}` and `${__setenv__:NAME,value}` for environment values.
- `${__read_text__:path,cast}` and `${__num_lines__:path}` for simple file-derived values.
- `${__path_parent__:path}`, `${__path_name__:path}`, `${__path_stem__:path}`, `${__path_suffix__:path}`, `${__path_is_file__:path}`, `${__path_is_dir__:path}`, and `${__path_exists__:path}` for path checks and path parts.

Keep resolver expressions small. Move non-trivial logic into Python modules so it can be tested.

## ML Experiment Engineering Guidelines

InEx was designed for scientific ML work: data cleaning and annotation, dataset preparation, neural network training and fine-tuning, inference, embedding extraction, decoding, statistics, and result analysis. The guidelines below apply whenever you create or modify Python modules and YAML configs in this context.

### 1. Purpose and philosophy

The primary goal of inex-launcher is to make creating and configuring ML experiment CLIs as simple and transparent as possible. A single YAML file should be enough for a reader to understand what a utility does, what its components are, and how they connect without reading the Python source first.

### 2. Reuse before creating

Before writing a new module, check whether an existing class, function, or utility in the current project already solves the problem. If it does, import it in YAML directly. If a publicly installable package, such as `torch`, `torchaudio`, `datasets`, `librosa`, or `sklearn`, covers the need, wire it as a plugin rather than wrapping it in new code. Write new code only when no suitable existing component exists.

```yaml
# Prefer: wire existing public class directly
normalizer:
  module: sklearn.preprocessing/StandardScaler

# Avoid: writing a thin MyNormalizer wrapper just to call StandardScaler
```

### 3. Design modules for reuse

When writing a new Python module, design its interface as if it will be used in multiple future projects. Concretely:

- Accept domain objects through `imports` (datasets, models, tokenizers) and plain values through `options` (paths, scalars, flags). Avoid hardcoding project-specific paths or constants inside classes.
- Prefer narrow, single-responsibility classes and functions over feature-rich "super-modules". A focused `AudioReader`, `FeatureExtractor`, or `ScoreComputer` is easier to reuse than a monolithic `Pipeline` that does everything.
- Use standard Python typing where it adds clarity without verbosity.

### 4. Backward compatibility when modifying shared modules

If you need to extend or fix an existing module that is already used by other utilities in the project, preserve backward compatibility:

- Do not change or remove existing `__init__` or function parameters that are already referenced in YAML configs.
- Add new parameters with default values so that existing configs continue to work unchanged.
- If a behavioral change is unavoidable, introduce it under a new parameter flag, such as `use_new_logic: bool = False`, rather than silently altering the default behavior.

```python
# Good: add optional parameter with a safe default
class FeatureExtractor:
    def __init__(self, sample_rate: int, normalize: bool = False):
        ...

# Bad: change existing parameter semantics without a default guard
```

### 5. Testable and mockable code

In scientific work, 100% unit-test coverage is often impractical. Still, new code should be written so that unit tests and mocking are straightforward:

- Keep side effects (file I/O, network calls, GPU operations) at the boundary, in the `execute` function or a clearly named `write_*` / `load_*` helper, not buried inside constructors or core logic methods.
- Prefer dependency injection (pass `model`, `device`, `reader` as constructor arguments via `imports`) over creating them internally. Injected objects can be mocked easily in tests.
- Avoid global state and module-level initialization that runs on import.

```python
# Good: injectable, mockable
class Scorer:
    def __init__(self, model, device):
        self.model = model
        self.device = device

# Avoid: creates its own model internally, hard to test without loading weights
class Scorer:
    def __init__(self, checkpoint_path: str):
        self.model = load_model(checkpoint_path)  # side effect in constructor
```

### 6. Avoid super-modules

Do not create large modules that try to handle data loading, transformation, model forward pass, and output writing in one class. Split functionality into small, focused classes/functions and use the plugin chain to compose them in YAML. A module that is too large to describe in one sentence is probably doing too much.

```python
# Avoid
class ExperimentRunner:
    def run(self, input_path, checkpoint, output_path): ...

# Prefer: separate plugins composed in YAML
# plugins: [reader, model, scorer, writer]
```

### 7. YAML config as a readable document

The YAML config is the primary documentation of a CLI utility's structure. Write it so that a new team member can understand what the utility does by reading the config alone:

- Use descriptive `snake_case` plugin keys that reflect the component's role (`audio_reader`, `feature_extractor`, `score_computer`, `result_writer`), not generic names (`obj1`, `stage2`).
- Group plugin definitions in the order they execute; top-down mirrors the data flow.
- Keep top-level parameter names clear and concise (`input_dir`, `checkpoint_path`, `output_dir`, `batch_size`), not abbreviated to the point of obscurity.
- Use `???` for required parameters; provide sensible defaults for optional tuning parameters at the top of the config.

```yaml
# Good
input_dir: ???
checkpoint_path: ???
output_dir: ???
batch_size: 32
plugins: [feature_reader, acoustic_model, decoder, result_writer]

# Avoid
inp: ???
ckpt: ???
bs: 32
plugins: [p1, p2, p3]
```

### 8. Comments in configs and modules

Short, purposeful comments are welcome and encouraged:

- In YAML: add a brief inline comment on parameters whose purpose is not obvious from the name (units, valid ranges, relationship to a paper's notation). Group-level comments (`# --- Feature extraction ---`) help orient readers in long configs.
- In Python: add docstrings to public classes and functions when the interface contract is non-trivial. Inline comments should explain why, not restate what the code does.
- Do not add comments that just echo the code or inflate line count.

```yaml
sample_rate: 16000    # Hz; must match the training data sample rate
hop_length: 160       # samples; 10 ms at 16 kHz
n_mels: 80            # mel filterbank bins

# --- Acoustic model ---
acoustic_model:
  module: myproject.models/AcousticModel
```

## Review Checklist

Before finishing an InEx utility:

- Confirm every `module:` and `method:` target is importable and has the expected callable/class/factory.
- Confirm constructor/function signatures match the union of `options`, `imports`, `__args__`, and `__kwargs__`.
- Confirm every `name.attr` import has a corresponding `exports: [attr]`.
- Remove unused exports.
- Keep top-level required inputs as `???`.
- Prefer `imports:` over repeated file loading when multiple plugins need the same object.
- Keep `execute:` as the only place that performs the final action unless a plugin is intentionally a setup side effect.
- Use `__mute__: [__all__]` for noisy object-heavy configs, then unmute selectively when debugging.
- Do not add shell, Slurm, or wrapper-script guidance to this skill; keep it focused on Python modules and InEx config design.
