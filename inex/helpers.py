import os
import logging
from pathlib import Path
from omegaconf import OmegaConf
from inex.utils.configure import load_config, create_plugin, bind_plugins


def none():
    return None


def zero():
    return 0


def one():
    return 1


def true():
    return True


def false():
    return False


def assign(value):
    return value


def read_text(path):
    path = Path(path)
    assert path.is_file(), f'File {path} does not exist'
    return path.read_text()


def evaluate(
        expression,
        a=None, b=None, c=None, d=None,
        x=None, y=None, z=None, w=None,
        i=None, j=None, k=None,
        m=None, n=None,
):
    return eval(expression)


def attribute(modname, attname):
    logging.debug(f'Loading module {modname}')
    module = __import__(modname, fromlist=[''])
    assert hasattr(module, attname), f'Module {modname} does not have attribute {attname}'
    return getattr(module, attname)


def posit_args(modname, attname, arguments):
    if isinstance(modname, str):
        logging.debug(f'Loading module {modname}')
        module = __import__(modname, fromlist=[''])
    else:
        module = modname
    assert hasattr(module, attname), f'Module {modname} does not have attribute {attname}'
    return getattr(module, attname)(*arguments)


_cache_ = dict()


def _import_(plugin, config, depends=None, ignore=None, **kwargs):
    path = os.path.abspath(config)
    assert os.path.isfile(path), f'File {path} does not exist'
    plugin = plugin.strip()
    assert len(plugin) > 0, 'Empty plugin or attribute name'
    parts = plugin.split('.')
    if len(parts) == 1:
        normal_name = plugin
        cache_name = 'plugins.' + plugin
    else:
        assert len(parts) == 2, f'Wrong plugin or attribute name: "{plugin}"'
        if parts[0] == 'plugins':
            normal_name = parts[1]
            cache_name = plugin
        else:
            normal_name = parts[0]
            cache_name = plugin
    if path in _cache_:
        logging.debug('Getting state dictionary from cache')
        state = _cache_[path]
    else:
        logging.debug('Creating new cache entry for state dictionary')
        state = dict()
        _cache_[path] = state
    if cache_name in state:
        return state[cache_name]
    logging.debug(f'Loading config from {path}')
    config = load_config(path)
    logging.debug(f'Merging config with options\n{kwargs}')
    config = OmegaConf.merge(config, kwargs)
    logging.debug(f'Resolving config\n{config}')
    config = OmegaConf.to_container(config, resolve=True, throw_on_missing=True)
    logging.debug(f'Building plugin dependencies in config\n{config}')
    bind_plugins(config)
    logging.debug(f'Final config:\n{config}')
    assert 'plugins' in config, f'Failed to find "plugins" list in config\n{config}'
    plugins = config['plugins']
    assert isinstance(plugins, list), f'Wrong type of "plugins" {type(plugins)} (must be list)'
    assert normal_name in plugins, f'Failed to find plugin "{normal_name}" in the list of plugins in config\n{config}'
    assert normal_name in config, f'Failed to find plugin "{normal_name}" in config\n{config}'
    options = config[normal_name]
    depends = {normal_name} if depends is None else set(depends) | {normal_name}
    if 'depends' in options:
        depends |= set(options['depends'])
    if ignore is not None:
        ignore = set(ignore)
    value = None
    for name in plugins:
        if name not in depends:
            continue
        elif (ignore is not None) and (name in ignore):
            continue
        cname = f'plugins.{name}'
        if cname in state:
            value = state[cname]
        else:
            create_plugin(name, config, state)
        if name == normal_name:
            assert cache_name in state, f'Failed to find created plugin {name} in the state dictionary'
            value = state[cache_name]
            break
    return value


def show(**kwargs):
    for key, value in kwargs.items():
        print(f'\n{key}\n  type: {type(value)}\n  value: {value}')
