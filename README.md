
![GitHub License](https://img.shields.io/github/license/speechpro/inex-launcher)
![PyPI - Version](https://img.shields.io/pypi/v/inex-launcher)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/inex-launcher.svg)

<a href="https://github.com/speechpro/inex-launcher/stargazers"><img src="https://img.shields.io/github/stars/speechpro/inex-launcher" alt="Stars Badge"/></a>
<a href="https://github.com/speechpro/inex-launcher/network/members"><img src="https://img.shields.io/github/forks/speechpro/inex-launcher" alt="Forks Badge"/></a>
<a href="https://github.com/speechpro/inex-launcher/pulls"><img src="https://img.shields.io/github/issues-pr/speechpro/inex-launcher" alt="Pull Requests Badge"/></a>
<a href="https://github.com/speechpro/inex-launcher/issues"><img src="https://img.shields.io/github/issues/speechpro/inex-launcher" alt="Issues Badge"/></a>
<a href="https://github.com/speechpro/inex-launcher/graphs/contributors"><img alt="GitHub contributors" src="https://img.shields.io/github/contributors/speechpro/inex-launcher?color=2b9348"></a>

# InEx Launcher

## Lightweight highly configurable Python launcher based on microkernel architecture

### Installation

```bash
pip install -U inex-launcher
```

### Single-file configuration

`inex-launcher` lets you describe an entire experiment in a single YAML file. The `plugins` list defines the initialization order of handlers. For each handler you only need to provide the module path and its options. The `execute` section describes the final method that will be called.

```yaml
plugins:
  - loader
  - model
  - trainer

loader:
  module: myproject.data/Loader
  options:
    path: data/train.csv

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

execute:
  method: myproject.training/run
  imports:
    trainer: plugins.trainer
```

Run this configuration with:

```bash
inex config.yaml
```

You can fine-tune the experiment by merging it with another file using `--merge` and overriding specific values with `--update`:

```bash
inex config.yaml -m experiment.yaml -u trainer.epochs=20 model.hidden=64
```

This approach lets you modify parameters or even replace handlers with just a few lines of YAML—no need to edit high‑level Python files.

Key benefits of this approach:

- **High modularity** – modules can be swapped directly in the configuration thanks to the plugin-based structure.
- **Clean structure** – a clear sequence of `plugins` followed by a single `execute` block keeps the file readable.
- **Flexibility** – YAML allows complex nested structures, so even advanced scenarios fit in one file.

