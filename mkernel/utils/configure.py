import os
import sys
import logging
from omegaconf import OmegaConf
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
        config = OmegaConf.create(conf_path)
    elif conf_path == '-':
        config = OmegaConf.create(sys.stdin.read())
    else:
        assert len(conf_path) > 0, 'Failed to load config: config path is empty string'
        if os.path.isfile(conf_path):
            config = OmegaConf.load(conf_path)
        else:
            config = OmegaConf.create(conf_path)
    return config


def create_plugin(name, config, state):
    assert name in config, f'Failed find module {name} in config\n{config}'
    params = config[name]
    assert 'module' in params, f'Failed find module for plugin {name} in config\n{config}'
    modname = params['module']
    parts = modname.split('/')
    if len(parts) > 1:
        assert len(parts) == 2, f'Wrong module name format ({modname}) for plugin {name} in config\n{config}'
        modname = parts[0]
        classname = parts[1]
    else:
        classname = None
    options = params['options'] if 'options' in params else dict()
    if 'imports' in params:
        imports = params['imports']
        for key, value in imports.items():
            if isinstance(value, list):
                values = list()
                for value1 in value:
                    values.append(state[value1])
                options[key] = values
            elif isinstance(value, dict):
                values = dict()
                for key1, value1 in value.items():
                    values[key1] = state[value1]
                options[key] = values
            else:
                options[key] = state[value]
    logging.debug(f'Creating plugin {name} from config\n{options}')
    logging.info(f'Loading module {modname}')
    module = __import__(modname, fromlist=[''])
    if classname is None:
        logging.info(f'Creating plugin {name} using class factory create() from module {modname}')
        plugin = module.create(options)
    else:
        logging.info(f'Creating plugin {name} with class name {classname} from module {modname}')
        classtype = getattr(module, classname)
        plugin = classtype(**options)
    if 'exports' in params:
        for attr in params['exports']:
            if hasattr(plugin, 'export'):
                state[f'{name}.{attr}'] = plugin.export(attr)
            elif hasattr(plugin, attr):
                state[f'{name}.{attr}'] = getattr(plugin, attr)
            elif hasattr(plugin, 'get'):
                state[f'{name}.{attr}'] = plugin.get(attr)
            else:
                assert False, f'Plugin {type(plugin)} does not have attribute {attr}'
    state[f'plugins.{name}'] = plugin


def get_as_is(config, key, default=None, required=False):
    if key in config:
        return config[key]
    else:
        assert not required, f'Failed to find {key} in config\n{config}'
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
