import os
import logging
from omegaconf import OmegaConf
from inex.utils.configure import load_config, create_plugin


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


def _import_(plugin, config, **kwargs):
    path = os.path.abspath(config)
    assert os.path.isfile(path), f'File {path} does not exist'
    if path in _cache_:
        logging.debug('Getting state from cache')
        state = _cache_[path]
    else:
        logging.debug('Creating new cache entry for state')
        state = dict()
        _cache_[path] = state
    name = f'plugins.{plugin}'
    if name in state:
        return state[name]
    logging.debug(f'Loading config from {path}')
    config = load_config(path)
    logging.debug(f'Merging config with options\n{kwargs}')
    config = OmegaConf.merge(config, kwargs)
    logging.debug(f'Resolving config\n{config}')
    config = OmegaConf.to_container(config, resolve=True, throw_on_missing=True)
    assert 'plugins' in config, f'Failed to find "plugins" list in config\n{config}'
    plugins = config['plugins']
    assert isinstance(plugins, list), f'Wrong type of "plugins" {type(plugins)} (must be list)'
    assert plugin in plugins, f'Failed to find plugin "{plugin}" in config\n{config}'
    value = None
    for name in plugins:
        value = create_plugin(name, config, state)
        if name == plugin:
            break
    return value


def show(**kwargs):
    for key, value in kwargs.items():
        print(f'\n{key}\n  type: {type(value)}\n  value: {value}')
