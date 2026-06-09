# InEx Launcher — configuration reference

Detailed syntax for YAML/JSON configs and Python module binding. For workflow and
design rules, see [SKILL.md](SKILL.md). For complete annotated examples, see
[examples.md](examples.md).

**Upstream source of truth:** [speechpro/inex-launcher](https://github.com/speechpro/inex-launcher).
Browse the contract tests and read the implementation when this skill is ambiguous.

| Resource | URL |
|----------|-----|
| Repository | https://github.com/speechpro/inex-launcher |
| README (minimal example) | https://github.com/speechpro/inex-launcher/blob/main/README.md |
| Test configs (`tests/*.yaml`) | https://github.com/speechpro/inex-launcher/tree/main/tests |
| Plugin creation (`create_plugin`, `bind_plugins`) | https://github.com/speechpro/inex-launcher/blob/main/inex/utils/configure.py |
| Helpers (`assign`, `compose`, `_import_`, …) | https://github.com/speechpro/inex-launcher/blob/main/inex/helpers.py |
| Resolvers & CLI entry (`start`, `main`) | https://github.com/speechpro/inex-launcher/blob/main/inex/inex.py |
| Execution engine | https://github.com/speechpro/inex-launcher/blob/main/inex/engine.py |

---

## Config file structure

```yaml
#!/bin/env inex                     # optional shebang

__log_level__: INFO                  # root logger level (default: WARNING)
__sys_path__: .                      # paths added to sys.path
__mute__: [plugin_a, __all__]        # suppress debug logs for listed plugins
__unmute__: [plugin_b]               # exceptions when __all__ is muted

# Top-level parameters (hyperparameters, paths, flags)
param: value
required_param: ???                  # must be overridden before resolution

plugins:                             # ordered initialization list
  - plugin_a
  - plugin_b

plugin_a:
  module: package.module/ClassName   # binding target (see grammar below)
  title: 'Stage title'               # printed when plugin is created
  is_done: path/.done                # skip plugin if file exists; touch after success
  before:                            # filesystem commands before init
    exists: path/or/glob
    mkdir: output/dir
    delete: [old/file, old/dir]
  after:                             # filesystem commands after init
    delete: temp/dir
  depends: [other_plugin]            # explicit dependency edge (usually auto-inferred)
  imports:                           # wire from plugin state
    model: plugins.other
    attr: other.exported_attr
  exports: [model, length]           # publish attributes to state as plugin_name.attr
  options:                           # constructor / function arguments
    path: ${param}
    __args__: [1, 2, 3]              # positional args
    __kwargs__: ${nested_dict}        # dict splatted into kwargs

execute:
  method: package.module/run         # final call (same binding rules as module)
  title: 'Execute stage'
  imports: { ... }
  options: { ... }
```

If `plugins:` is omitted, InEx auto-detects plugin keys as any top-level mapping
that contains a `module` or `method` key.

### Special / reserved keys

| Key | Scope | Purpose |
|-----|-------|---------|
| `plugins` | top | Ordered plugin initialization list |
| `execute` | top | Final method invocation (uses `method:`, not `module:`) |
| `module` | plugin | Class/function/method to build the plugin |
| `method` | execute | Same as `module` but for the execute block |
| `options` | plugin/execute | Args: mapping, bare list, or `__args__`/`__kwargs__` |
| `imports` | plugin/execute | State wiring: mapping, list, or `__args__`/`__kwargs__` |
| `exports` | plugin | Publish attributes referenced elsewhere as `name.attr` |
| `depends` | plugin | Force dependency edges |
| `is_done` | plugin | Skip-if-done marker file |
| `before` / `after` | plugin | Filesystem hooks |
| `title` | plugin | Banner printed at init |
| `__log_level__` | top | Logging level (CLI `-l` overrides) |
| `__log_path__` | top | Log file path (CLI `-g` overrides) |
| `__sys_path__` | top | Extra `sys.path` entries (CLI `-s` overrides) |
| `__mute__` / `__unmute__` | top | Control per-plugin debug logging |

---

## Module string grammar

Format: `package.module/Name` or `package.module/Class.method`.

| Form | Meaning |
|------|---------|
| `pkg.mod/MyClass` | import `pkg.mod`, call `MyClass(*args, **kwargs)` |
| `pkg.mod/my_func` | call `my_func(*args, **kwargs)` |
| `pkg.mod/Class.method` | call bound `Class.method(*args, **kwargs)` |
| `pkg.mod` (no slash) | call `pkg.mod.create(*args, **kwargs)` |
| `plugins.foo/bar` | call method `bar` on the instance stored as `plugins.foo` |
| `plugins.model/parameters` | attribute/method access on a plugin instance |
| `pkg.mod/Name^N` | take index `N` of the result (requires `__getitem__`) |
| `/max`, `/eval`, `/tuple` | Python builtin (empty module name → `eval(name)`) |

Notes:

- `^N` may follow the whole reference to index into the constructed result.
- A `plugins.X/...` reference automatically adds a dependency edge to `X`.
- For `execute`, use `method:` with the same grammar; calling a method on a
  prior plugin (`method: plugins.gen/generate`) is common.

---

## imports and options resolution

### options shapes

```yaml
# Plain kwargs (most common)
options:
  path: /data/train
  batch_size: 32

# Inline mapping
options: { device: cuda }

# Bare list → positional __args__
options: [1]                 # → f(1)

# Positional via __args__
options:
  __args__: [[1, 2, 3]]      # → f([1, 2, 3])

# Splat a dict into kwargs
options:
  __kwargs__: ${loader_opts}

# Positional + kwargs together
options:
  d: 5
  __args__: [1, 2, [3, 4]]
  __kwargs__: { f: 7, g: 8 }
```

### imports shapes

```yaml
# Dict — named parameters (most common)
imports:
  model: plugins.model
  device: plugins.device

# Exported attribute of another plugin
imports:
  total_steps: train_dataset.length

# Special state keys
imports:
  command_line: command_line
  config_path: config_path

# List — positional __args__
imports:
  __args__: [plugins.a, plugins.b]

# Single object wrapped in a list (one-element list arg)
imports:
  feats_src: [plugins.valid_feats]

# Index into a prior plugin's result
imports:
  first: plugins.array^0       # plugins.array[0]

# Mixed; nested structures are resolved recursively
imports:
  dataset: plugins.dataset
  callbacks:
    - plugins.augment
    - plugins.to_tensors
  __kwargs__: ${extra_opts}
```

Resolution detail: in `imports`, a string value that matches a state key is
replaced by the stored object; lists and dicts are walked recursively so
`plugins.*` and `name.attr` references resolve at any depth. `value^N` /
`value^key` indexes into an imported sequence/mapping.

---

## Plugin state keys

After plugin `my_plugin` is created:

| State key | Content |
|-----------|---------|
| `plugins.my_plugin` | return value of the constructor/function |
| `my_plugin.attr` | each name listed in `exports` |
| `command_line` | full argv string (available to import) |
| `config_path` | path to the main config (available to import) |

---

## exports

`exports` publishes attributes of a plugin instance into state under
`plugin_name.attribute_name`. Import them elsewhere as `plugin_name.attr`
(**not** `plugins.plugin_name.attr`).

### The rule (required)

1. **Include** an attribute in `exports` only if some `imports` block in the
   **same config** references it as `plugin_name.attribute_name`.
2. **Exclude** attributes that nothing references that way.
3. **Runtime error** if a reference like `audio.waveform` exists but `waveform`
   is not in `audio`'s `exports`.
4. Importing the whole plugin (`plugins.audio`) needs **no** `exports`.

### Resolution

For each name in `exports`, InEx stores:

- `plugin.export(name)` if the plugin defines an `export(self, name)` method, else
- `getattr(plugin, name)`.

`exports: [__all__]` publishes everything: dict items (if the plugin is a dict),
`__dict__` values, or all non-callable public attributes. Prefer an explicit
list that matches actual references.

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

# exports on an _import_ plugin to surface a derived value from another config
chunker:
  module: inex.helpers/_import_
  exports: [chunk_size]
  options:
    plugin: chunker
    config: ${model_dir}/final_config.yaml

model:
  module: myproject.models/Model
  imports:
    image_size: chunker.chunk_size
```

---

## is_done, before, after, title

```yaml
my_plugin:
  module: myproject.pipeline/run_stage
  title: 'Running stage 1'
  is_done: exp/run/.done       # if it exists: print "[ Done ]", return None, skip
  before:
    exists: input/data.txt     # assert path/glob exists
    mkdir: output/             # create directory
    delete: [output/old.txt]   # remove file(s)/dir(s)/glob(s)
  after:
    delete: [temp/]
  options:
    input: input/data.txt
    output: output/result.txt
```

Commands available in `before`/`after`: `exists`, `mkdir`, `delete`. After a
plugin with `is_done` finishes, the marker file is created automatically.

---

## OmegaConf interpolation and placeholders

```yaml
child: ${parent}              # sibling / top-level reference
nested: ${..parent.key}       # relative (parent-scope) reference
list_item: ${paths[0]}       # list index
group_value: ${opts.sub.key} # nested mapping reference
required: ???                 # must be set via --merge or -u before resolution
```

`???` (OmegaConf "missing") fails resolution if still unset — use it to enforce
required parameters. Combine grouped option blobs with `__kwargs__`:

```yaml
model_opts:
  hidden_dim: 128
  num_layers: 6

network:
  module: myproject.models/Network
  options:
    __kwargs__: ${model_opts}
```

---

## Built-in resolvers

Registered at startup; use as `${__name__:args}`. They evaluate during config
resolution, before any plugin is created.

| Resolver | Purpose | Example |
|----------|---------|---------|
| `__evaluate__` | Evaluate a Python expression | `${__evaluate__:'min(${n}, 16)'}` |
| `__fetch__` | Load a value from another YAML/JSON | `${__fetch__:base.yaml, train.lr}` |
| `__getenv__` | Read env var (optional cast) | `${__getenv__:PORT, int}` |
| `__setenv__` | Set env var, return value | `${__setenv__:MY_VAR, value}` |
| `__read_text__` | Read file as string (optional cast) | `${__read_text__:n.txt, int}` |
| `__num_lines__` | Count lines in a file (or len of a list) | `${__num_lines__:list.txt}` |
| `__path_parent__` | Parent directory | `${__path_parent__:${ckpt}}` |
| `__path_name__` | Filename with extension | `${__path_name__:${ckpt}}` |
| `__path_stem__` | Filename without extension | `${__path_stem__:${ckpt}}` |
| `__path_suffix__` | File extension | `${__path_suffix__:${ckpt}}` |
| `__path_is_file__` | Assert path is a file (returns None) | in `exists:` lists |
| `__path_is_dir__` | Assert path is a directory | in `exists:` lists |
| `__path_exists__` | Assert path exists | in `exists:` lists |

`__evaluate__` accepts an `initialize` list to run setup statements first, e.g.
`${__evaluate__:'int(np.sum(np.array([1,2,3])))', [import numpy as np]}`.

---

## inex.helpers modules

Use as `inex.helpers/Name` in `module:` or `method:`.

### assign

Return the value unchanged. Used in `execute` to bundle several results or to
peel an exported attribute into its own plugin.

```yaml
execute:
  method: inex.helpers/assign
  imports:
    value:
      a: plugins.plugin_a
      b: plugins.plugin_b
```

### evaluate

Evaluate a Python expression with imported values formatted in. Optional
`initialize` runs `exec` statements first (e.g. imports).

```yaml
total_steps:
  module: inex.helpers/evaluate
  imports:
    epoch_size: train_dataset.length
  options:
    expression: 'int(1.001 * {num_epochs} * {epoch_size})'
    num_epochs: ${num_epochs}
```

### _import_

Load a single plugin (and its dependencies) from another inex config. Results
are cached per config path, so importing several plugins from the same config
initializes shared dependencies once.

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
    ckpt_path: ${model_dir}/${model_name}
```

Options: `plugin`, `config`, optional `depends`, `ignore`, `use_cache`, plus any
extra kwargs that are merged into the sub-config before resolution. An `_import_`
plugin may also carry `exports` to surface a derived value (see exports above).

### compose

Merge configs (dicts, files, dot-list overrides) and optionally write the result
to a file. Used for meta-configs that generate other configs.

```yaml
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
```

Also supports `merge_paths`, `merge_dicts`, and `check_file`
(`override` | `fail_if_exists` | `fail_if_different`).

### attribute

Load a named attribute from a module (e.g. to pass a function object).

```yaml
collate_fn:
  module: inex.helpers/attribute
  options:
    modname: myproject.data.collate
    attname: collate_fn
```

### show

Debug-print plugin values (type, id, value) — handy as a temporary `execute`.

```yaml
execute:
  method: inex.helpers/show
  imports:
    model: plugins.model
```

> `inex.helpers` also provides `stage`, `execute`, `system`, and `write_script`
> for orchestrating sub-configs and external commands. Those are deployment and
> orchestration-design concerns and out of scope for this skill, which focuses
> on Python-module and config design. Running `inex` locally to validate a new
> utility, collect traces, and debug config/module wiring is in scope.

---

## Dependency graph

`bind_plugins()` builds a directed graph and augments each plugin's `depends`
from three sources:

1. `imports` values referencing `plugins.X` or `X.attr`.
2. `module: plugins.X/...` references.
3. Explicit `depends: [...]` lists.

Transitive dependencies are folded into each plugin's `depends`. Plugins must be
listed in `plugins:` ahead of anything that depends on them. Plugin names may
contain `+` (valid YAML keys), used by some expression-chaining patterns.

---

## execute block

Exactly one `execute` section runs after all plugins (unless the `--stop-after`
CLI flag halts earlier). Same binding grammar as `module:`, via `method:`.

```yaml
# Project function
execute:
  method: myproject.cli/run
  imports:
    model: plugins.model
    data: plugins.dataset
  options:
    output_dir: ${output_dir}

# Method on an existing plugin
execute:
  method: plugins.generator/generate
  options:
    num_samples: 1000

# Third-party function
execute:
  method: torch/save
  imports:
    obj: plugins.state_dict
  options:
    f: ${save_path}
```

---

## Feature → upstream test map

When you need to confirm exact behavior, read the matching contract test.

| Feature | Upstream test |
|---------|---------------|
| plugins + execute; function vs class; exports | [test_basic.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_basic.yaml) |
| exports + `^index` on attributes | [test_export.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_export.yaml) |
| `__args__` via options and imports | [test_args.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_args.yaml) |
| `__kwargs__` via options and imports | [test_kwargs.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_kwargs.yaml) |
| mixed positional/kwargs | [test_pos_args.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_pos_args.yaml) |
| `plugins.value^N` indexing | [test_item.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_item.yaml) |
| `_import_` helper; cache sharing | [test_import.3.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_import.3.yaml) |
| `evaluate`; plugin names with `+` | [test_eval.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_eval.yaml) |
| all built-in resolvers | [test_resolvers.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_resolvers.yaml) |
| `__fetch__` resolver | [test_fetch.2.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_fetch.2.yaml) |
| `is_done`; before/after commands | [test_is_done.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_is_done.yaml) |
| `???` placeholders; `compose` | [test_compose.1.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_compose.1.yaml) |
| `/max`, `/eval`, `/tuple` builtins | [test_built_in.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_built_in.yaml) |
| third-party module binding | [test_numpy.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_numpy.yaml) |
| partial init (`--stop-after`) | [test_stop_after.yaml](https://github.com/speechpro/inex-launcher/blob/main/tests/test_stop_after.yaml) |
