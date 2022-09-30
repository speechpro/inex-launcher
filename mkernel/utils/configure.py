import os
import sys
import copy
import json
import yaml
import logging
from logging import StreamHandler, FileHandler
from mkernel.utils.convert import str_to_bool


def configure_logging(log_level, log_path=None):
    log_level = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }[log_level]
    handlers = [StreamHandler()]
    if log_path is not None:
        handlers.append(FileHandler(log_path, mode='w', encoding='utf-8'))
    logging.basicConfig(
        level=log_level,
        datefmt='%Y-%m-%d %H:%M:%S',
        format='%(asctime)s %(name)s %(pathname)s:%(lineno)d - %(levelname)s - %(message)s',
        handlers=handlers
    )


def load_config(conf_path):
    assert conf_path is not None, 'Failed to load config: config path is None'
    if isinstance(conf_path, dict):
        config = copy.copy(conf_path)
    elif conf_path == '-':
        config = yaml.safe_load(sys.stdin.read())
    else:
        assert len(conf_path) > 0, 'Failed to load config: config path is empty string'
        if os.path.isfile(conf_path):
            with open(conf_path, encoding='utf-8') as stream:
                ext = os.path.splitext(conf_path)[1]
                if ext == '.json':
                    config = json.load(stream)
                else:
                    config = yaml.safe_load(stream)
        else:
            config = yaml.safe_load(conf_path)
    return config


def create_plugin(name, config, state):
    assert name in config, f'Failed find module "{name}" in config\n{config}'
    params = config[name]
    assert 'module' in params, f'Failed find module for plugin {name} in config \n{config}'
    modname = params['module']
    options = params['options'] if 'options' in params else dict()
    if 'imports' in params:
        imports = params['imports']
        for key, value in imports.items():
            options[key] = state[value]
    logging.debug(f'Creating plugin {name} from config "{options}"')
    logging.info(f'Loading module "{modname}"')
    module = __import__(modname, fromlist=[''])
    logging.info(f'Creating plugin {name} from module "{modname}"')
    plugin = module.create(options)
    if 'exports' in params:
        for key in params['exports']:
            state[f'{name}.{key}'] = plugin.get(key)
    state[f'plugins.{name}'] = plugin


def get_as_is(config, key, default=None, required=False):
    if key in config:
        return config[key]
    else:
        assert not required, f'Failed to find "{key}" in config\n{config}'
        return default


def get_as_bool(config, key, default=False, required=False):
    value = get_as_is(config, key, default, required)
    if isinstance(value, str):
        return str_to_bool(value)
    else:
        return bool(value)


def get_as_type(config, key, dtype, default, required):
    return dtype(get_as_is(config, key, default, required))


def get_as_str(config, key, default=None, required=False):
    return get_as_type(config, key, str, default, required)


def get_as_int(config, key, default=None, required=False):
    return get_as_type(config, key, int, default, required)


def get_as_float(config, key, default=None, required=False):
    return get_as_type(config, key, float, default, required)
