# InEx Launcher — configuration reference

Detailed syntax for YAML configs and Python module binding. For workflow and patterns, see [SKILL.md](SKILL.md). For complete annotated examples, see [examples.md](examples.md).

**Upstream source:** [speechpro/inex-launcher](https://github.com/speechpro/inex-launcher) on GitHub — use it to verify behavior, browse contract tests, and read the implementation when this skill is ambiguous.

| Resource | URL |
|----------|-----|
| Repository | https://github.com/speechpro/inex-launcher |
| README (minimal example) | https://github.com/speechpro/inex-launcher/blob/main/README.md |
| Test configs (`tests/*.yaml`) | https://github.com/speechpro/inex-launcher/tree/main/tests |
| Plugin creation (`create_plugin`) | https://github.com/speechpro/inex-launcher/blob/main/inex/utils/configure.py |
| Helpers (`assign`, `compose`, `_import_`, …) | https://github.com/speechpro/inex-launcher/blob/main/inex/helpers.py |
| Resolvers & CLI (`inex` command) | https://github.com/speechpro/inex-launcher/blob/main/inex/inex.py |
| Execution engine | https://github.com/speechpro/inex-launcher/blob/main/inex/engine.py |

---

## Config file structure

```yaml
#!/bin/env inex                    # optional shebang

__log_level__: INFO                 # root logger level (default: WARNING)
__sys_path__: .                     # paths added to sys.path (also: CLI -s)
__mute__: [plugin_a, __all__]       # suppress debug logs for listed plugins
__unmute__: [plugin_b]              # exceptions when __all__ is muted

# Top-level experiment parameters
param: value
required_param: ???                 # must be overridden before resolve

plugins:                            # initialization order (required for multi-plugin configs)
  - plugin_a
  - plugin_b

plugin_a:
  module: package.module/ClassName  # or method for execute block
  title: 'Stage title'              # printed when plugin is created
  is_done: path/to/.done            # skip plugin if file exists; touch after success
  before:                           # filesystem commands before plugin init
    exists: path/or/glob
    mkdir: output/dir
    delete: [old/file, old/dir]
  after:                            # filesystem commands after plugin init
    delete: temp/dir
  depends: [other_plugin]           # explicit dependency (usually auto-inferred)
  imports:                          # wire from plugin state
    model: plugins.other
    attr: other.exported_attr
  exports: [model, length]          # expose attributes to state as plugin_name.attr
  options:                          # constructor kwargs / function kwargs
    path: ${param}
    __args__: [1, 2, 3]             # positional args
    __kwargs__: ${nested_dict}       # expand dict into kwargs

execute:
  method: package.module/run        # final call (same binding rules as module)
  title: 'Execute stage'
  imports: { ... }
  options: { ... }
```

If `plugins:` is omitted, inex auto-detects plugin keys as any top-level dict containing `module` or `method`.

---

## Module string grammar

Format: `package.module/Name` or `package.module/Class.method`

| Form | Meaning |
|------|---------|
| `pkg.mod/MyClass` | `getattr(import pkg.mod, 'MyClass')(*args, **kwargs)` |
| `pkg.mod/my_func` | `pkg.mod.my_func(*args, **kwargs)` |
| `pkg.mod/Class.method` | bound static/class method |
| `pkg.mod^2` | take index 2 from result (`__getitem__`) |
| `plugins.foo/bar` | call `bar` on instance stored as `plugins.foo` |
| `plugins.model/parameters` | attribute access on plugin (e.g. PyTorch params) |
| `pkg.mod` (no slash) | call `pkg.mod.create(*args, **kwargs)` |
| `/max`, `/eval`, `/tuple` | built-in Python (`eval` with empty modname) |

### Index and attribute references in imports

| Import value | Resolves to |
|--------------|-------------|
| `plugins.value1` | plugin instance |
| `value2.value` | exported attribute from plugin `value2` |
| `plugins.array^0` | `plugins.array[0]` |
| `object1.a` | state key `object1.a` (from exports) |

---

## Plugin state keys

After plugin `my_plugin` is created:

| State key | Content |
|-----------|---------|
| `plugins.my_plugin` | return value of constructor/function |
| `my_plugin.attr` | each name in `exports` list |
| `command_line` | full argv string (in execute state) |
| `config_path` | path to main config |

---

## imports and options resolution

### imports shapes

```yaml
# Dict — named parameters (most common)
imports:
  model: plugins.model
  device: plugins.device

# List — positional __args__
imports:
  __args__: [plugins.a, plugins.b]

# Mixed
imports:
  dataset: plugins.dataset
  collate_fn: plugins.dataset    # same object, two param names
  __kwargs__: ${extra_opts}
```

### options shapes

```yaml
# Plain kwargs
options:
  path: /data/train
  batch_size: 32

# Positional via __args__
options:
  __args__: [[1, 2, 3]]

# Expand dict
options:
  __kwargs__: ${loader_opts}

# Positional + kwargs together
options:
  d: 5
  __args__: ${args_list}
  __kwargs__: ${kwargs_dict}
```

When `options` is a bare list at plugin top level, it is treated as `__args__`:

```yaml
value2:
  module: numpy/array
  options: [[1, 2, 3]]
```

---

## exports

The `exports` field publishes selected attributes from a plugin instance into config state under keys `plugin_name.attribute_name`. Other plugins and `execute` can then import them as `plugin_name.attr` (not `plugins.plugin_name.attr`).

### Exports rule (required)

1. **Include** a property in `exports` only if some `imports` block in the **same config** references it as `plugin_name.property_name`.
2. **Exclude** properties from `exports` if nothing in the config references them that way.
3. **Runtime error** if a reference like `audio.waveform` exists but `waveform` is not listed in the `audio` plugin's `exports`.

Importing the whole plugin as `plugins.audio` does **not** require individual properties in `exports` — the full instance is passed.

### Examples

```yaml
# Attribute references — exports required, list ONLY referenced attrs
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

# Whole plugin — no exports needed
audio:
  module: myproject.audio/MonoWaveform
  options:
    audio_path: ${audio_path}

execute:
  method: myproject.cli/run
  imports:
    audio: plugins.audio

# Nested object export
model:
  module: myproject.models/ModelWrapper
  exports: [model]           # enables model.model downstream

inner:
  module: inex.helpers/assign
  imports:
    value: model.model

# Dataset size for scheduler
dataset:
  module: myproject.data/Dataset
  exports: [length]          # enables train_dataset.length

scheduler:
  module: torch.optim.lr_scheduler/OneCycleLR
  imports:
    total_steps: train_dataset.length

# Bulk export (use sparingly — prefer explicit list matching references)
object:
  module: numpy/array
  exports: [__all__]         # all non-callable public attributes
```

### Common import forms

```yaml
optimizer:
  module: torch.optim/Adam
  imports:
    params: plugins.model/parameters   # method/attr on plugin — no exports entry

scheduler:
  module: torch.optim.lr_scheduler/OneCycleLR
  imports:
    total_steps: train_dataset.length  # exported attr — must be in exports
```

---

## is_done, before, after

Skip completed stages and manage filesystem side effects:

```yaml
is_done: exp/run/.done

my_plugin:
  module: myproject/run_stage
  is_done: ${is_done}
  before:
    exists: input/data.txt
    mkdir: output/
    delete: [output/old.txt, temp/]
  after:
    delete: [temp/]
  options:
    ...
```

Commands in `before`/`after`: `exists`, `mkdir`, `delete`.

See [examples.md §12](examples.md#12-skip-if-done-with-beforeafter-hooks) for a full example.

---

## OmegaConf interpolation

Standard OmegaConf syntax in configs:

```yaml
child: ${parent}                   # sibling/top-level reference
nested: ${..parent}               # parent struct reference
list_item: ${paths[0]}            # list index
default: ${oc.env:VAR,default}     # env with default
```

Placeholders:

```yaml
required: ???                     # must be set via merge or -u before resolve
```

See [examples.md §11](examples.md#11-required-placeholders-) for usage.

---

## Built-in resolvers

Registered by inex at startup (use as `${__name__:...}`):

| Resolver | Purpose | Example |
|----------|---------|---------|
| `__evaluate__` | Python eval expression | `${__evaluate__:'{a} + {b}', a: 2, b: 3}` |
| `__fetch__` | Load value from another YAML/JSON file | `${__fetch__:path/to/file.yaml}` or `${__fetch__:file.yaml, key.subkey}` |
| `__getenv__` | Read env var (optional cast) | `${__getenv__:HOME}` or `${__getenv__:PORT, int}` |
| `__setenv__` | Set env var, return value | `${__setenv__:MY_VAR, value}` |
| `__read_text__` | Read file as string (optional cast) | `${__read_text__:path.txt, int}` |
| `__num_lines__` | Count lines in file or list | `${__num_lines__:file.txt}` |
| `__path_parent__` | Parent directory | `${__path_parent__:${config_path}}` |
| `__path_name__` | Filename with extension | |
| `__path_stem__` | Filename without extension | |
| `__path_suffix__` | File extension | |
| `__path_is_file__` | Assert is file (returns None) | Use in `exists:` lists |
| `__path_is_dir__` | Assert is directory | |
| `__path_exists__` | Assert path exists | |

Example:

```yaml
a: 2
b: 3
evaluate1: ${__evaluate__:'${a}^2 + ${b}'}
path_is_file: ${__path_is_file__:${input_path}}
```

See [examples.md §10](examples.md#10-built-in-resolvers) for a full resolver example.

---

## inex.helpers modules

Available as `inex.helpers/FunctionName` in YAML.

### assign

Return value unchanged. Used in `execute` to bundle results or pass through.

```yaml
execute:
  method: inex.helpers/assign
  imports:
    value:
      a: plugins.plugin_a
      b: plugins.plugin_b
```

### evaluate

Evaluate a Python expression with optional `initialize` imports.

```yaml
total_steps:
  module: inex.helpers/evaluate
  imports:
    epoch_size: train_dataset.length
  options:
    expression: 'int(1.001 * {num_epochs} * {epoch_size})'
    num_epochs: ${num_epochs}
```

With numpy:

```yaml
options:
  initialize:
    - import numpy as np
  expression: '{x} * np.array([1, 2, 3])'
```

### _import_

Load a plugin from another inex config file (cached per config path).

```yaml
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
    ckpt_path: ${ckpt_path}
```

Options: `plugin`, `config`, optional `depends`, `ignore`, `use_cache`, plus kwargs merged into sub-config.

See [examples.md §13](examples.md#13-sub-config-import-_import_).

### compose

Merge configs programmatically; optionally write result file.

```yaml
write_parameters:
  module: inex.helpers/compose
  options:
    config: ${params}
    result_path: ${params_path}
```

Also supports: `config_path`, `merge_paths`, `merge_dicts`, `override`, `check_file`.

See [examples.md §14](examples.md#14-meta-config-with-compose).

### attribute

Load attribute from a module by name.

```yaml
collate_fn:
  module: inex.helpers/attribute
  options:
    modname: myproject.data.collate
    attname: collate_fn
```

### show

Debug-print plugin values (type, id, value).

```yaml
execute:
  method: inex.helpers/show
  imports:
    model: plugins.model
```

---

## Dependency graph

`bind_plugins()` builds a directed graph from:

1. `imports` values referencing `plugins.X` or `X.attr`
2. `module: plugins.X/...` references
3. Explicit `depends: [...]`

All transitive dependencies are added to each plugin's `depends` list. Plugins in `plugins:` must be initialized before dependents.

Plugin names may contain `+` (e.g. `a+b`) — valid YAML keys for expression-chaining plugins.

---

## execute block

Exactly one `execute` section runs after all plugins (unless `stop-after` CLI flag stops earlier).

```yaml
execute:
  method: myproject.cli/run
  imports:
    model: plugins.model
    data: plugins.dataset
  options:
    output_dir: ${output_dir}
```

Alternative — call method on existing plugin:

```yaml
execute:
  method: plugins.generator/generate
  options:
    num_samples: 1000
```

Alternative — third-party function:

```yaml
execute:
  method: torch/save
  imports:
    obj: plugins.state_dict
  options:
    f: ${save_path}
```

---

## Special config keys summary

| Key | Scope | Purpose |
|-----|-------|---------|
| `plugins` | top | Ordered plugin initialization list |
| `execute` | top | Final method invocation |
| `__log_level__` | top | Logging level |
| `__sys_path__` | top | Extra sys.path entries |
| `__mute__` / `__unmute__` | top | Control plugin debug logging |
| `module` | plugin | Class/function to instantiate |
| `method` | execute | Function to call (same as module) |
| `options` | plugin | Kwargs and `__args__`/`__kwargs__` |
| `imports` | plugin | State wiring |
| `exports` | plugin | Publish attributes referenced as `plugin_name.attr` elsewhere in config |
| `depends` | plugin | Force dependency edges |
| `is_done` | plugin | Skip-if-done marker file |
| `before` / `after` | plugin | Filesystem hooks |
| `title` | plugin | Banner printed at init |

---

## Feature index

Map of inex features to skill examples and upstream test configs on GitHub:

| Feature | examples.md | Upstream test |
|---------|-------------|---------------|
| plugins + execute; function vs class | §16 | [test_basic.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_basic.yaml) |
| exports: only referenced attributes | §16 | [test_export.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_export.yaml) |
| `__args__` via options and imports | §9 | [test_args.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_args.yaml) |
| `__kwargs__` via options and imports | §9 | [test_kwargs.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_kwargs.yaml) |
| mixed positional/kwargs | §9 | [test_pos_args.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_pos_args.yaml) |
| `plugins.value^N` indexing | §17 | [test_item.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_item.yaml) |
| `_import_` helper; cache sharing | §13 | [test_import.3.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_import.3.yaml) |
| `evaluate`; plugin names with `+` | §10 | [test_eval.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_eval.yaml) |
| all built-in resolvers | §10 | [test_resolvers.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_resolvers.yaml) |
| `__fetch__` resolver | §10 | [test_fetch.2.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_fetch.2.yaml) |
| is_done; before/after commands | §12 | [test_is_done.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_is_done.yaml) |
| `???` placeholders | §11 | [test_compose.1.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_compose.1.yaml) |
| `compose` merge | §14 | [test_compose.py](https://github.com/speechpro/inex-launcher/blob/main/tests/test_compose.py) |
| `/max`, `/eval`, `/tuple` built-ins | §18 | [test_built_in.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_built_in.yaml) |
| third-party modules (torch, numpy) | §2, §4, §8 | [test_numpy.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_numpy.yaml) |
| callback lists in dataset | §7 | — |
| Lightning training split | §8 | — |
| model factory `from_name` | §15 | — |
| checkpoint export chain | §6 | — |
