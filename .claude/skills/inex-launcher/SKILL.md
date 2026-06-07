---
name: inex-launcher
description: >-
  Design Python modules and YAML/JSON configs for inex-launcher (InEx) CLI utilities.
  Use when creating or reviewing inex configs, writing importable plugin modules,
  wiring plugin chains with options/imports/exports/execute, debugging config
  resolution or plugin dependency errors, or building data-prep, inference, or
  training CLIs driven by inex / inex-launcher / YAML-driven Python. Focused on
  Python module and config design, not shell wrappers, Slurm, or how to launch inex.
---

# InEx Launcher — building CLI utilities

Guide for designing **Python modules** and **YAML configs** for
[inex-launcher](https://github.com/speechpro/inex-launcher) (CLI command: `inex`).

InEx (**In**itialize & **Ex**ecute) is a microkernel launcher. A single config
describes a pipeline: an ordered list of **plugins** builds Python objects in
dependency order, each result is stored in a state dictionary, and a final
**execute** block calls one function to do the work. You write ordinary
importable Python; the YAML wires it together. This means you swap
implementations, paths, and hyperparameters in YAML without writing a new
entry-point script per experiment.

This skill covers **how to write the Python modules and the config**. It does
**not** cover shell wrappers, Slurm, or how a user runs the `inex` command.

For exhaustive syntax tables, see [reference.md](reference.md). For complete
annotated, copy-pasteable configs, see [examples.md](examples.md). When exact
behavior matters, the upstream source is the source of truth:
<https://github.com/speechpro/inex-launcher.git>.

---

## Mental model

A run proceeds in this order (see `inex/inex.py` → `inex/engine.py` →
`inex/utils/configure.py` upstream):

1. **Load** the config (YAML/JSON file, inline YAML string, or stdin `-`).
2. **Merge** any `--merge` files and apply `--update key=value` overrides.
3. **Resolve** all OmegaConf interpolations (`${...}`) and built-in resolvers
   (`${__name__:...}`). At this point `???` placeholders must be filled or
   resolution fails.
4. **Bind** the dependency graph from `imports`, `module: plugins.X/...`, and
   explicit `depends`.
5. **Create plugins** in the order listed in `plugins:`. Each plugin's return
   value is stored in state as `plugins.<name>`; listed `exports` are stored as
   `<name>.<attr>`.
6. **Execute** the `execute` block (one final method call) and return its result.

Key consequence: anything a plugin imports must be created **earlier** in the
`plugins:` list. InEx auto-orders dependencies it can see, but the human-readable
order should already be correct.

---

## Workflow: create a new CLI utility

### Step 1 — Decompose the job into a plugin graph

Describe the utility as: **top-level parameters** → **a chain of plugin objects**
→ **one execute function**. List stages in reading order; each becomes one key
in `plugins:`.

Common shapes (full versions in [examples.md](examples.md)):

| Utility type  | Plugin chain |
|---------------|--------------|
| Simple I/O / convert | load inputs → `execute` function |
| Data prep     | seed → readers → transform/method → dataset → (dataloader) → `execute` writer |
| Inference     | seed → init torch → device → `_import_` model arch → load checkpoint → features → scorer → `execute` writer |
| Training      | seed → datasets → model → params → optimizer/scheduler → loss → Lightning module → callbacks/logger → `execute: train` |
| Meta / multi-stage | `compose` to write configs → `execute`/`_import_` sub-configs |

### Step 2 — Write the Python modules

Place code under your project package (e.g. `myproject/data/`, `myproject/cli.py`).
Write **normal importable Python** — the module must be importable via install,
`PYTHONPATH`, or config `__sys_path__`. Pick one binding style per plugin (see
[Module binding styles](#module-binding-styles)):

- **Class** for stateful objects (datasets, models, scorers, tokenizers).
- **Function** for entry points and one-shot jobs (`write_batches`, `train`, `process`).
- **Factory function** like `from_name(name, **kwargs)` when an implementation is
  selected by a string.
- **Method on a prior plugin** to post-process an already-built object.

**Design rules:**

1. **The signature is the YAML contract.** Parameter names must match the keys
   used in `imports` and `options`. A mismatch is a runtime `TypeError`.
2. **Plugin objects come through `imports`; literals/config come through
   `options`.** Don't reconstruct an upstream object from a path if a prior
   plugin already built it — import it.
3. **Return the object downstream needs.** It becomes `plugins.<name>`. Setup
   side-effect plugins may return `None`, but then nothing can import a value
   from them.
4. **Expose derived values as attributes/properties**, then list them in
   `exports` *only if* another plugin references them (see
   [The exports rule](#the-exports-rule)).
5. **Don't parse argv inside modules.** InEx owns configuration; modules receive
   already-resolved values and objects. Keep `execute` thin: it receives
   assembled objects + plain options and runs the job.
6. **Prefer explicit `/ClassName` or `/function`** over a bare module that
   relies on a `create()` factory.

### Step 3 — Write the config

One YAML per CLI utility. Minimal skeleton:

```yaml
#!/bin/env inex                  # optional shebang — marks the file as an inex config

__log_level__: INFO             # optional; or set with -l on the CLI

param1: ???                      # required — must be supplied via -u or --merge
param2: default_value
nested_opts:
  key: value

plugins:
  - plugin_a
  - plugin_b

plugin_a:
  module: myproject.data/Loader
  options:
    path: ${param1}

plugin_b:
  module: myproject.data/Transform
  imports:
    loader: plugins.plugin_a
  options:
    __kwargs__: ${nested_opts}

execute:
  method: myproject.cli/run
  imports:
    data: plugins.plugin_b
  options:
    result_dir: ${param2}
```

Conventions seen across real projects:

- `#!/bin/env inex` shebang at the top; configs are self-describing.
- `???` for values that must be supplied at run time.
- `snake_case` for plugin keys and Python packages.
- Group related options under a nested key (e.g. `model_opts:`) and splat them
  with `__kwargs__: ${model_opts}`; reference sub-values as `${model_opts.dim}`.
- `__mute__: [__all__]` to silence per-plugin debug logs in large object-heavy
  configs; `__unmute__: [name]` to re-enable one when debugging.
- A top-level `exists:` list of `${__path_is_file__:...}` for preflight checks.
- A standard `init` prelude for ML jobs: `set_random_seed`, `init_cudnn`,
  `torch/device`.

### Step 4 — Wire third-party and helper modules

Any importable callable works directly — no wrapper needed:

```yaml
device:
  module: torch/device
  options: { device: cuda }

loader:
  module: torch.utils.data.dataloader/DataLoader
  imports:
    dataset: plugins.dataset
    collate_fn: plugins.dataset      # same object used two ways
  options:
    __kwargs__: ${loader_opts}
```

Built-in helpers from `inex.helpers` (details in [reference.md](reference.md)):
`assign` (pass-through/bundle), `evaluate` (derived values), `_import_` (reuse a
plugin from another config), `compose` (build/merge configs), `attribute`,
`show` (debug print).

### Step 5 — Validate the design

- [ ] Every name in `plugins:` has a matching top-level block.
- [ ] Every `imports: plugins.X` (or `X.attr`) references a plugin listed earlier.
- [ ] Each `module:`/`method:` target is importable and matches its binding style.
- [ ] Each plugin's constructor/function signature matches the union of its
      `options`, `imports`, `__args__`, and `__kwargs__`.
- [ ] Required parameters use `???`; optional ones have defaults.
- [ ] `exports` lists **only** attributes referenced elsewhere as `name.attr`,
      and every such reference has a matching `exports` entry (see below).
- [ ] `execute` is the only place doing the final work (unless a plugin is an
      intentional setup side effect).

Cross-check the closest pattern in [examples.md](examples.md).

---

## Module binding styles

InEx resolves `module:` / `method:` as `package.module/Name`. The full grammar
(indexing `^N`, `Class.method`, builtins) is in
[reference.md](reference.md#module-string-grammar).

| YAML | Python | When to use |
|------|--------|-------------|
| `pkg.mod/MyClass` | `class MyClass: def __init__(self, ...)` | Datasets, models, scorers, transforms |
| `pkg.mod/my_func` | `def my_func(...)` | CLI entry points, writers, one-shot jobs |
| `pkg.mod/Class.method` | bound class/static method | Alternate constructors |
| `pkg.mod` (no `/Name`) | `def create(*args, **kwargs)` | Module factory (prefer an explicit name instead) |
| `plugins.prev/method` | method on the instance from plugin `prev` | Post-process / mutate an already-built object |
| `plugins.model/parameters` | attribute/method on a plugin instance | e.g. wire PyTorch params into an optimizer |
| `torch/device`, `numpy/array` | third-party callable | Use libraries with no wrapper code |
| `/max`, `/eval`, `/tuple` | Python builtin (empty module name) | Quick literals/arithmetic |

In `execute`, the same forms apply via `method:`. Calling a method on an
existing plugin is common: `method: plugins.generator/generate`.

---

## imports vs options

Rule of thumb: **plugin objects and exported attributes → `imports`;
literals, paths, scalars, and config dicts → `options`.**

| Mechanism | Carries | Example |
|-----------|---------|---------|
| `options` (mapping) | keyword args | `path: ${data_path}` |
| `options` (bare list) | positional args | `options: [1]` → `f(1)` |
| `options.__args__` | positional args | `__args__: [[1, 2, 3]]` |
| `options.__kwargs__` | dict splatted into kwargs | `__kwargs__: ${model_opts}` |
| `imports` (mapping) | named plugin objects / exported attrs | `model: plugins.model` |
| `imports` (list) | positional plugin objects | `[plugins.cb1, plugins.cb2]` |
| `imports.__args__` / `__kwargs__` | positional / splatted plugin objects | `__kwargs__: ${obj_opts}` |

Import reference forms:

- `plugins.<name>` — the whole object returned by plugin `<name>`.
- `<name>.<attr>` — an **exported** attribute of plugin `<name>`.
- `plugins.<name>^N` — index into the result (`result[N]`).
- A single object wrapped in a list (`feats_src: [plugins.valid_feats]`) passes
  it as a one-element list — match this in the Python signature.
- The special state keys `command_line` and `config_path` can be imported
  directly (e.g. a logging plugin importing `command_line: command_line`).

Lists and dicts under `imports` are resolved **recursively**, so callbacks,
metric maps, and nested bundles can contain `plugins.*` references at any depth.

---

## The exports rule

`exports` publishes selected attributes of a plugin instance into state as
`<plugin_name>.<attribute>`, so other plugins (or `execute`) can import them as
`plugin_name.attr` (note: **not** `plugins.plugin_name.attr`).

```yaml
audio:
  module: myproject.audio/MonoWaveform
  exports: [waveform]          # ONLY because something below imports audio.waveform
  options:
    audio_path: ${audio_path}
    channel: ${channel}

features:
  module: myproject.features/compute
  imports:
    waveform: audio.waveform   # the matching reference
```

Rules — apply them in both directions:

1. **List an attribute in `exports` only if** some `imports` block in the
   **same config** references it as `plugin_name.attribute`.
2. **Do not export** attributes that nothing references that way.
3. **Runtime error** if a reference like `audio.waveform` exists but `waveform`
   is missing from `audio`'s `exports`.
4. Passing the **whole** plugin (`plugins.audio`) does **not** require any
   `exports` — the receiver gets the full object and reads attributes in Python.

| Import form | Needs `exports`? |
|-------------|------------------|
| `plugins.audio` | No — whole instance |
| `audio.waveform` | Yes — `waveform` in `audio.exports` |
| `train_dataset.length` | Yes — `length` in `train_dataset.exports` |
| `plugins.model/parameters` | No — method/attr access on the instance |

Resolution order for an exported attr: InEx calls `plugin.export(attr)` if the
plugin defines an `export` method, otherwise `getattr(plugin, attr)`. Special
value `exports: [__all__]` publishes all dict items / `__dict__` values /
non-callable public attributes — use sparingly; prefer an explicit list that
matches the actual references.

A frequent real pattern: an `inex.helpers/_import_` plugin that reuses a plugin
from a saved training config can itself carry `exports` to surface a derived
value (e.g. `exports: [chunk_size]`) so an inference plugin can import
`chunker.chunk_size`.

---

## Plugin stage features

Per-plugin keys for pipeline ergonomics (full reference in
[reference.md](reference.md)):

- `title: 'Stage name'` — printed when the plugin is created.
- `is_done: path/.done` — if the marker file exists, skip the plugin (returns
  `None`); the file is touched after success. Makes pipelines resumable.
- `before:` / `after:` — filesystem hooks with commands `exists`, `mkdir`,
  `delete` (run before/after plugin creation).
- `depends: [other]` — force a dependency edge that isn't visible through
  `imports` or `module: plugins.X/...`. Usually unnecessary.

---

## Built-in resolvers (config-resolve time)

Use as `${__name__:args}` in config values; they run before plugins are created.
Full table in [reference.md](reference.md#built-in-resolvers). Highlights:

- `${__evaluate__:'expr'}` — evaluate a small Python expression.
- `${__fetch__:other.yaml, key.subkey}` — pull a value from another config file.
- `${__getenv__:NAME, int}` / `${__setenv__:NAME, value}` — environment vars.
- `${__read_text__:file, int}` / `${__num_lines__:file}` — file-derived values.
- `${__path_parent__:p}`, `${__path_stem__:p}`, `${__path_name__:p}`,
  `${__path_suffix__:p}` — path parts (common for deriving `model_dir` /
  `result_dir` from a checkpoint path).
- `${__path_is_file__:p}`, `${__path_is_dir__:p}`, `${__path_exists__:p}` —
  assertions; put them in an `exists:` list for preflight checks.

Keep resolver expressions tiny. Move non-trivial logic into a Python module so
it can be tested.

---

## Suggested package layout

```
myproject/
├── myproject/
│   ├── __init__.py
│   ├── utils/
│   │   └── init_torch.py     # set_random_seed, init_cudnn
│   ├── data/
│   │   ├── io.py             # read_lines, load tables, write_results
│   │   └── dataset.py        # Dataset classes
│   ├── models/
│   │   └── models.py         # Model classes, from_name() factory
│   ├── infer/
│   │   └── compute.py        # scorer / inference classes
│   ├── lightning/
│   │   ├── module.py         # LightningModule + load_model()
│   │   └── trainer.py        # train() for execute
│   └── cli.py                # execute entry points
├── conf/  (or configs/)
│   └── my_utility.yaml
└── pyproject.toml  (or setup.py)
```

---

## ML Experiment Engineering Guidelines

InEx was designed for scientific ML work: data cleaning and annotation, dataset
preparation, neural network training and fine-tuning, inference, embedding
extraction, decoding, statistics, and result analysis. The guidelines below
apply whenever you create or modify Python modules and YAML configs in this
context.

### 1. Purpose and philosophy

The primary goal of inex-launcher is to make creating and configuring ML
experiment CLIs as simple and transparent as possible. A single YAML file should
be enough for a reader to understand what a utility does, what its components
are, and how they connect — without reading the Python source first.

### 2. Reuse before creating

Before writing a new module, check whether an existing class, function, or
utility in the current project already solves the problem. If it does, import it
in YAML directly. If a publicly installable package (e.g. `torch`, `torchaudio`,
`datasets`, `librosa`, `sklearn`) covers the need, wire it as a plugin rather
than wrapping it in new code. Write new code only when no suitable existing
component exists.

```yaml
# Prefer: wire existing public class directly
normalizer:
  module: sklearn.preprocessing/StandardScaler

# Avoid: writing a thin MyNormalizer wrapper just to call StandardScaler
```

### 3. Design modules for reuse

When writing a new Python module, design its interface as if it will be used in
multiple future projects. Concretely:

- Accept domain objects through `imports` (datasets, models, tokenizers) and
  plain values through `options` (paths, scalars, flags). Avoid hardcoding
  project-specific paths or constants inside classes.
- Prefer narrow, single-responsibility classes and functions over feature-rich
  "super-modules". A focused `AudioReader`, `FeatureExtractor`, `ScoreComputer`
  is easier to reuse than a monolithic `Pipeline` that does everything.
- Use standard Python typing where it adds clarity without verbosity.

### 4. Backward compatibility when modifying shared modules

If you need to extend or fix an existing module that is already used by other
utilities in the project, preserve backward compatibility:

- Do not change or remove existing `__init__` / function parameters that are
  already referenced in YAML configs.
- Add new parameters with default values so that existing configs continue to
  work unchanged.
- If a behavioral change is unavoidable, introduce it under a new parameter flag
  (e.g. `use_new_logic: bool = False`) rather than silently altering the default
  behavior.

```python
# Good: add optional parameter with a safe default
class FeatureExtractor:
    def __init__(self, sample_rate: int, normalize: bool = False):
        ...

# Bad: change existing parameter semantics without a default guard
```

### 5. Testable and mockable code

In scientific work, 100% unit-test coverage is often impractical. Still, new
code should be written so that unit tests and mocking are straightforward:

- Keep side effects (file I/O, network calls, GPU operations) at the boundary —
  in the `execute` function or a clearly named `write_*` / `load_*` helper — not
  buried inside constructors or core logic methods.
- Prefer dependency injection (pass `model`, `device`, `reader` as constructor
  arguments via `imports`) over creating them internally. Injected objects can
  be mocked easily in tests.
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

Do not create large modules that try to handle data loading, transformation,
model forward pass, and output writing in one class. Split functionality into
small, focused classes/functions and use the plugin chain to compose them in
YAML. A module that is too large to describe in one sentence is probably doing
too much.

```python
# Avoid
class ExperimentRunner:
    def run(self, input_path, checkpoint, output_path): ...

# Prefer: separate plugins composed in YAML
# plugins: [reader, model, scorer, writer]
```

### 7. YAML config as a readable document

The YAML config is the primary documentation of a CLI utility's structure. Write
it so that a new team member can understand what the utility does by reading the
config alone:

- Use descriptive `snake_case` plugin keys that reflect the component's role
  (`audio_reader`, `feature_extractor`, `score_computer`, `result_writer`), not
  generic names (`obj1`, `stage2`).
- Group plugin definitions in the order they execute — top-down mirrors the data
  flow.
- Keep top-level parameter names clear and concise (`input_dir`,
  `checkpoint_path`, `output_dir`, `batch_size`), not abbreviated to the point of
  obscurity.
- Use `???` for required parameters; provide sensible defaults for optional
  tuning parameters at the top of the config.

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

- In YAML: add a brief inline comment on parameters whose purpose is not obvious
  from the name (units, valid ranges, relationship to a paper's notation).
  Group-level comments (`# --- Feature extraction ---`) help orient readers in
  long configs.
- In Python: add docstrings to public classes and functions when the interface
  contract is non-trivial. Inline comments should explain *why*, not restate
  *what* the code does.
- Do not add comments that just echo the code or inflate line count.

```yaml
sample_rate: 16000    # Hz; must match the training data sample rate
hop_length: 160       # samples; 10 ms at 16 kHz
n_mels: 80            # mel filterbank bins

# --- Acoustic model ---
acoustic_model:
  module: myproject.models/AcousticModel
```

---

## Anti-patterns

- Putting a plugin object in `options` instead of `imports` (won't resolve from
  state — it stays a string).
- Referencing `plugins.X` before `X` appears in `plugins:`.
- Mismatched names between a Python signature and the YAML `options`/`imports` keys.
- One giant monolithic plugin instead of small composable stages.
- Relying on a bare-module `create()` factory when a named class/function is clearer.
- Listing attributes in `exports` that nothing references as `plugin_name.attr`.
- Referencing `plugin_name.attr` without listing `attr` in that plugin's
  `exports` (runtime error).
- Parsing CLI args or reading global state inside plugin modules.

---

## Reference map

| Topic | Location |
|-------|----------|
| Config syntax, grammar, resolvers, helpers | [reference.md](reference.md) |
| Annotated end-to-end config examples | [examples.md](examples.md) |
| Overview & minimal config | [README](https://github.com/speechpro/inex-launcher/blob/main/README.md) |
| Contract test configs | [tests/](https://github.com/speechpro/inex-launcher/tree/main/tests) |
| Plugin engine (`create_plugin`, `bind_plugins`) | [inex/utils/configure.py](https://github.com/speechpro/inex-launcher/blob/main/inex/utils/configure.py) |
| Built-in helpers | [inex/helpers.py](https://github.com/speechpro/inex-launcher/blob/main/inex/helpers.py) |
| Resolvers & CLI entry | [inex/inex.py](https://github.com/speechpro/inex-launcher/blob/main/inex/inex.py) |
