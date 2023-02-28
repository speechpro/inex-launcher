import os
import sys
import logging
from omegaconf import OmegaConf
from logging import StreamHandler, FileHandler


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


def resolve_option(option, state):
    if isinstance(option, list):
        for i, value in enumerate(option):
            if isinstance(value, list) or isinstance(value, dict):
                option[i] = resolve_option(value, state)
            elif isinstance(value, str) and (value in state):
                option[i] = state[value]
    elif isinstance(option, dict):
        for key, value in option.items():
            if isinstance(value, list) or isinstance(value, dict):
                option[key] = resolve_option(value, state)
            elif isinstance(value, str) and (value in state):
                option[key] = state[value]
    elif isinstance(option, str) and (option in state):
        option = state[option]
    return option


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
            options[key] = resolve_option(value, state)
    logging.debug(f'Creating plugin {name} from config\n{options}')
    if modname.startswith('plugins.') and (modname in state):
        plugin = state[modname]
        if classname is None:
            plugin = plugin(**options)
        else:
            assert hasattr(plugin, classname), f'Plugin {modname} does not have attribute {classname}'
            method = getattr(plugin, classname)
            plugin = method(**options)
    else:
        logging.debug(f'Loading module {modname}')
        module = __import__(modname, fromlist=[''])
        if classname is None:
            logging.debug(f'Creating plugin {name} using class factory create() from module {modname}')
            plugin = module.create(options)
        else:
            logging.debug(f'Creating plugin {name} with class name {classname} from module {modname}')
            parts = classname.split('.')
            if len(parts) == 1:
                assert hasattr(module, classname), f'Module {modname} does not have class {classname}'
                classtype = getattr(module, classname)
                plugin = classtype(**options)
            else:
                classname = parts[0]
                attribute = parts[1]
                assert hasattr(module, classname), f'Module {modname} does not have class {classname}'
                classtype = getattr(module, classname)
                assert hasattr(classtype, attribute), f'Class {classname} does not have attribute {attribute}'
                method = getattr(classtype, attribute)
                plugin = method(**options)
    if 'exports' in params:
        for attr in params['exports']:
            if hasattr(plugin, 'export'):
                state[f'{name}.{attr}'] = plugin.export(attr)
            elif hasattr(plugin, attr):
                state[f'{name}.{attr}'] = getattr(plugin, attr)
            else:
                assert False, f'Plugin {type(plugin)} does not have attribute {attr}'
    state[f'plugins.{name}'] = plugin
