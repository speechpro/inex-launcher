---
name: inex-launcher
description: >-
  Design Python modules and YAML configs for inex-launcher (InEx) CLI utilities.
  Use when creating inex configs, plugin modules, data pipelines, inference tools,
  or training configs with inex, inex-launcher, or YAML-driven Python CLIs.
---

# InEx Launcher — CLI utility development

Guide for designing **Python modules** and **YAML configs** for [inex-launcher](https://github.com/speechpro/inex-launcher) (CLI: `inex`). This skill does **not** cover shell wrappers or how to invoke `inex` from the terminal.

For syntax tables and resolver details, see [reference.md](reference.md). For complete annotated config examples, see [examples.md](examples.md). For authoritative upstream examples and implementation, see the [inex-launcher GitHub repository](https://github.com/speechpro/inex-launcher).

---

## When to use InEx

Use inex-launcher when a CLI utility is best described as:

1. **Top-level parameters** — paths, hyperparameters, flags (YAML keys or `???` placeholders)
2. **A plugin chain** — objects built in dependency order (data loaders → transforms → model → writer)
3. **One execute step** — a function or method that runs the job using wired plugins

Benefits: swap implementations in YAML without rewriting entry points; reuse plugins across configs; compose pipelines from small, testable Python units.

---

## Workflow: create a new CLI utility

### Step 1 — Define the plugin graph

List stages left-to-right. Each stage becomes one plugin key in the `plugins:` list.

Typical patterns:

| Utility type | Plugin chain |
|--------------|--------------|
| **Simple I/O** | load inputs → `execute` function |
| **Data pipeline** | init → load tables → transform → dataset → dataloader → write |
| **Inference** | init torch → load checkpoint → load features → score class → write output |
| **Training** | init → datasets → model → optimizer/scheduler → Lightning module → `execute: trainer/train` |

Draw dependencies: anything passed into a constructor or function via `imports` must appear **earlier** in `plugins:`.

### Step 2 — Write Python modules

Place code under your project package (e.g. `myproject/utils/`, `myproject/data/`).

Pick one binding style per plugin (see [Module binding styles](#module-binding-styles)):

- **Class** — stateful objects (datasets, models, score computers)
- **Function** — side-effect entry points (`write_batches`, `pack_items`, `train`)
- **Factory function** — `from_name(name, **kwargs)` when architecture is selected by name
- **Instance method** — `plugins.align_set/insert_sil` to call a method on an earlier plugin

**Design rules:**

1. **`__init__` / function signature = YAML contract** — parameter names must match `imports` keys and `options` keys.
2. **Use `imports` for plugin objects** — datasets, models, devices, tokenizers built upstream.
3. **Use `options` for literals and config** — paths, scalars, nested dicts via `${}` interpolation.
4. **Return the useful object** — inex stores it as `plugins.<name>` in state.
5. **`exports` lists only referenced attributes** — include a property in `exports` only if some `imports` block in the same config references it as `plugin_name.property_name` (see [Exports rule](#exports-rule)). Omit unreferenced properties. If a property is referenced but missing from `exports`, inex raises a runtime error.
6. **Prefer explicit `/ClassName` or `/function`** — use `pkg.mod/MyClass` or `pkg.mod/run`; avoid module-level `create()` unless you have a reason.

Shared utility pattern: `utils/init_torch.py` with `set_random_seed`, `init_cudnn`.

### Step 3 — Write the YAML config

Create one YAML per CLI utility (e.g. `conf/my_tool.yaml`).

Minimal skeleton:

```yaml
#!/bin/env inex

__log_level__: INFO          # optional

param1: ???                   # required override
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

Conventions:

- **`#!/bin/env inex`** shebang at top (configs are self-describing)
- **`???`** for values that must be supplied at run time (via merge or `-u`)
- **`${..parent}`** OmegaConf interpolation for nested keys
- **`__mute__: [__all__]`** to suppress per-plugin debug logs in large configs
- **`exists:`** list with `${__path_is_file__:...}` for preflight path checks
- **Plugin keys** — `snake_case`; Python packages — `snake_case`

### Step 4 — Wire third-party and helper modules

You can use any importable module directly in YAML:

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
```

Built-in helpers from `inex.helpers` (see [reference.md](reference.md)):

- `assign` — pass-through / assemble return dict
- `evaluate` — compute derived values (`total_steps`, dynamic expressions)
- `_import_` — load a plugin from another inex config (checkpoint reload)
- `compose` — merge YAML fragments inside a config (multi-stage meta-configs)

### Step 5 — Validate the design

Before finishing, verify:

- [ ] Every name in `plugins:` has a matching top-level block
- [ ] Every `imports: plugins.X` references a plugin initialized earlier
- [ ] `execute.method` signature matches `imports` + `options`
- [ ] Required params use `???` or have defaults
- [ ] Plugin classes/functions are importable from the project package
- [ ] Each plugin's `exports` lists **only** attributes referenced as `plugin_name.attr` in some `imports` block (plugins or `execute`); every such reference has a matching `exports` entry

Cross-check against [examples.md](examples.md) for the pattern you are implementing.

---

## Exports rule

The `exports` field declares which attributes of a plugin instance are visible in config state as `plugin_name.attribute_name`.

**How references work:**

| Import form | Needs `exports`? |
|-------------|------------------|
| `plugins.audio` | No — whole plugin instance passed |
| `audio.waveform` | Yes — `waveform` must appear in `audio` plugin's `exports` |
| `train_dataset.length` | Yes — `length` must appear in `train_dataset` plugin's `exports` |
| `plugins.model/parameters` | No — attribute/method access on plugin instance |

**Rules when writing configs:**

1. Scan all `imports` blocks (every plugin and `execute`) for references of the form `plugin_name.property_name`.
2. List **only** those property names in that plugin's `exports`. Do not export attributes that nothing in the config references.
3. If a reference like `audio.waveform` exists but `waveform` is missing from `audio`'s `exports`, inex fails at runtime.
4. Passing `plugins.audio` to `execute` or another plugin does **not** require listing individual properties in `exports` — the receiver gets the full object.

Example — attribute wiring:

```yaml
audio:
  module: myproject.audio/MonoWaveform
  exports: [waveform, sample_rate]    # only because segmenter imports these below
  options:
    audio_path: ${audio_path}

segmenter:
  module: myproject.audio/Segmenter
  imports:
    waveform: audio.waveform
    sample_rate: audio.sample_rate
```

Example — whole plugin, no exports needed:

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

See [examples.md §16](examples.md#16-exports-only-referenced-attributes) for full patterns.

---

## Module binding styles

InEx resolves `module:` and `execute.method` as `package.module/Name`.

| YAML | Python | When to use |
|------|--------|-------------|
| `pkg.mod/MyClass` | `class MyClass: def __init__(self, ...)` | Datasets, models, transforms, score classes |
| `pkg.mod/my_func` | `def my_func(...)` | CLI entry points, writers, one-shot jobs |
| `pkg.mod/from_name` | `def from_name(name, **kwargs)` | Model/architecture factory |
| `plugins.prev/method` | method on instance from plugin `prev` | Post-process an object (`insert_sil`, `Load`, `generate`) |
| `plugins.model/parameters` | PyTorch `.parameters()` | Optimizer wiring |
| `torch/device`, `numpy/array` | third-party constructors | Device, arrays without wrapper code |

If `module:` has no `/ClassName`, inex calls `pkg.mod.create(*args, **kwargs)`. Prefer explicit class or function names instead.

---

## Passing arguments: imports vs options

| Mechanism | Purpose | Example |
|-----------|---------|---------|
| **`options`** | Literals, paths, flags, nested config blobs | `path: ${feats_path}`, `__kwargs__: ${model_opts}` |
| **`imports`** | Other plugins or exported attributes | `model: plugins.blank_model`, `epoch_size: train_dataset.length` |
| **`imports` list** | Positional args (`__args__`) | `callbacks: [plugins.cb1, plugins.cb2]` |
| **`options.__args__`** | Positional constructor args | `__args__: [[1, 2, 3]]` |
| **`options.__kwargs__`** | Expand a dict into kwargs | `__kwargs__: ${loader_opts}` |

Rule: **plugin objects → `imports`; configuration values → `options`.**

---

## Common pipeline patterns

Each pattern has a full annotated example in [examples.md](examples.md).

| Pattern | Best for | See examples.md |
|---------|----------|-----------------|
| **A — Minimal utility** | pack/write/convert tools | §1 |
| **B — Linear data pipeline** | load → transform → dataset → write | §2, §4 |
| **C — Inference from checkpoint** | score/eval/export | §5, §6 |
| **D — Callback-composed dataset** | flexible sample/batch transforms | §7 |
| **E — Training (Lightning)** | train configs | §8 |
| **F — Multi-source execute** | several plugins → one function | §3 |
| **G — Exports hygiene** | list only referenced `plugin.attr` | §16 |
| **H — Args/kwargs wiring** | positional and dict expansion | §9 |
| **I — Resolvers & placeholders** | dynamic values, preflight checks | §10, §11 |
| **J — Skip-if-done hooks** | incremental pipelines | §12 |
| **K — Sub-config import** | reuse plugins from another YAML | §13 |
| **L — Meta-config compose** | generate configs programmatically | §14 |
| **M — Model factory** | architecture selected by name | §15 |

---

## Package layout conventions

```
myproject/
├── myproject/
│   ├── __init__.py
│   ├── utils/
│   │   └── init_torch.py      # set_random_seed, init_cudnn
│   ├── data/
│   │   ├── io.py              # read_lines, load tables
│   │   └── dataset.py         # Dataset classes
│   ├── models/
│   │   └── models.py          # Model classes, from_name()
│   └── lightning/
│       ├── module.py          # LightningModule wrapper
│       └── trainer.py         # train() function for execute
├── conf/
│   └── my_utility.yaml
└── pyproject.toml or setup.py
```

---

## ML Experiment Engineering Guidelines

InEx was designed for scientific ML work: data cleaning and annotation, dataset preparation, neural network training and fine-tuning, inference, embedding extraction, decoding, statistics, and result analysis. The guidelines below apply whenever you create or modify Python modules and YAML configs in this context.

#### 1. Purpose and philosophy

The primary goal of inex-launcher is to make creating and configuring ML experiment CLIs as simple and transparent as possible. A single YAML file should be enough for a reader to understand what a utility does, what its components are, and how they connect — without reading the Python source first.

#### 2. Reuse before creating

Before writing a new module, check whether an existing class, function, or utility in the current project already solves the problem. If it does, import it in YAML directly. If a publicly installable package (e.g. `torch`, `torchaudio`, `datasets`, `librosa`, `sklearn`) covers the need, wire it as a plugin rather than wrapping it in new code. Write new code only when no suitable existing component exists.

```yaml
# Prefer: wire existing public class directly
normalizer:
  module: sklearn.preprocessing/StandardScaler

# Avoid: writing a thin MyNormalizer wrapper just to call StandardScaler
```

#### 3. Design modules for reuse

When writing a new Python module, design its interface as if it will be used in multiple future projects. Concretely:

- Accept domain objects through `imports` (datasets, models, tokenizers) and plain values through `options` (paths, scalars, flags). Avoid hardcoding project-specific paths or constants inside classes.
- Prefer narrow, single-responsibility classes and functions over feature-rich "super-modules". A focused `AudioReader`, `FeatureExtractor`, `ScoreComputer` is easier to reuse than a monolithic `Pipeline` that does everything.
- Use standard Python typing where it adds clarity without verbosity.

#### 4. Backward compatibility when modifying shared modules

If you need to extend or fix an existing module that is already used by other utilities in the project, preserve backward compatibility:

- Do not change or remove existing `__init__` / function parameters that are already referenced in YAML configs.
- Add new parameters with default values so that existing configs continue to work unchanged.
- If a behavioral change is unavoidable, introduce it under a new parameter flag (e.g. `use_new_logic: bool = False`) rather than silently altering the default behavior.

```python
# Good: add optional parameter with a safe default
class FeatureExtractor:
    def __init__(self, sample_rate: int, normalize: bool = False):
        ...

# Bad: change existing parameter semantics without a default guard
```

#### 5. Testable and mockable code

In scientific work, 100% unit-test coverage is often impractical. Still, new code should be written so that unit tests and mocking are straightforward:

- Keep side effects (file I/O, network calls, GPU operations) at the boundary — in the `execute` function or a clearly named `write_*` / `load_*` helper — not buried inside constructors or core logic methods.
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

#### 6. Avoid super-modules

Do not create large modules that try to handle data loading, transformation, model forward pass, and output writing in one class. Split functionality into small, focused classes/functions and use the plugin chain to compose them in YAML. A module that is too large to describe in one sentence is probably doing too much.

```python
# Avoid
class ExperimentRunner:
    def run(self, input_path, checkpoint, output_path): ...

# Prefer: separate plugins composed in YAML
# plugins: [reader, model, scorer, writer]
```

#### 7. YAML config as a readable document

The YAML config is the primary documentation of a CLI utility's structure. Write it so that a new team member can understand what the utility does by reading the config alone:

- Use descriptive `snake_case` plugin keys that reflect the component's role (`audio_reader`, `feature_extractor`, `score_computer`, `result_writer`), not generic names (`obj1`, `stage2`).
- Group plugin definitions in the order they execute — top-down mirrors the data flow.
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

#### 8. Comments in configs and modules

Short, purposeful comments are welcome and encouraged:

- In YAML: add a brief inline comment on parameters whose purpose is not obvious from the name (units, valid ranges, relationship to a paper's notation). Group-level comments (`# --- Feature extraction ---`) help orient readers in long configs.
- In Python: add docstrings to public classes and functions when the interface contract is non-trivial. Inline comments should explain *why*, not restate *what* the code does.
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

- Putting plugin objects in `options` instead of `imports` (won't resolve from state)
- Referencing `plugins.X` before `X` appears in `plugins:` list
- Mismatched parameter names between Python signature and YAML keys
- Giant monolithic plugin instead of composable stages
- Using `create()` when a named class or function is clearer
- Listing attributes in `exports` that no `imports` block references as `plugin_name.attr`
- Referencing `plugin_name.attr` in `imports` without listing `attr` in that plugin's `exports` (runtime error)

---

## Reference map

| Topic | Location |
|-------|----------|
| Config syntax, resolvers, helpers | [reference.md](reference.md) |
| Annotated config examples | [examples.md](examples.md) |
| Overview & minimal config | [README](https://github.com/speechpro/inex-launcher/blob/main/README.md) |
| Contract test configs | [tests/](https://github.com/speechpro/inex-launcher/tree/main/tests) |
| Plugin engine implementation | [inex/utils/configure.py](https://github.com/speechpro/inex-launcher/blob/main/inex/utils/configure.py) |
| Built-in helpers | [inex/helpers.py](https://github.com/speechpro/inex-launcher/blob/main/inex/helpers.py) |
| Resolvers & CLI entry | [inex/inex.py](https://github.com/speechpro/inex-launcher/blob/main/inex/inex.py) |
