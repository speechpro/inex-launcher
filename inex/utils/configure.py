import os
import re
import sys
import logging
import logging.config
import networkx as nx
from omegaconf import OmegaConf


def configure_logging(log_level, log_path=None):
    handlers = {
        "inex_out": {
            "class": "logging.StreamHandler",
            "formatter": "inex_basic",
            "stream": "ext://sys.stderr",
        }
    }
    if log_path is not None:
        handlers['inex_file'] = {
            "class": "logging.FileHandler",
            "formatter": "inex_basic",
            "filename": log_path,
            "mode": "w",
            "encoding": "utf-8"
        }
    CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"inex_basic": {"format": '%(asctime)s %(name)s %(pathname)s:%(lineno)d - %(levelname)s - %(message)s'}},
        "handlers": handlers,
        "loggers": {"inex": {"handlers": handlers.keys(), "level": log_level}},
        "root": {"handlers": handlers.keys(), "level": log_level}
    }
    logging.config.dictConfig(CONFIG)


def get_inex_logger():
    return logging.getLogger('inex')


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


def add_depends(graph, plugin, module, plugins):
    if isinstance(module, str):
        module = module.split('^')[0]
        parts = module.split('.')
        if len(parts) == 2:
            if parts[0] == 'plugins':
                if parts[1] in plugins:
                    graph.add_edge(plugin, parts[1])
            else:
                if parts[0] in plugins:
                    graph.add_edge(plugin, parts[0])
    elif isinstance(module, list):
        for item in module:
            add_depends(graph=graph, plugin=plugin, module=item, plugins=plugins)
    elif isinstance(module, dict):
        for item in module.values():
            add_depends(graph=graph, plugin=plugin, module=item, plugins=plugins)


def bind_plugins(config):
    if 'plugins' in config:
        plugins = set(config['plugins'])
        if 'execute' in config:
            plugins.add('execute')
    else:
        plugins = set()
        for key, opts in config.items():
            if isinstance(opts, dict) and (('module' in opts) or ('method' in opts)):
                plugins.add(key)
    graph = nx.DiGraph()
    for plugin in plugins:
        graph.add_node(plugin)
    for plugin in plugins:
        opts = config[plugin]
        module = opts['module'] if 'module' in opts else opts['method']
        if module.startswith('plugins.'):
            module = module.split('/')[0]
            module = module.split('^')[0]
            parts = module.split('.')
            assert len(parts) == 2, f'Wrong plugin reference format {module} (must be in the form plugins.<name>)'
            graph.add_edge(plugin, parts[1])
        if 'imports' in opts:
            imports = opts['imports']
            for module in imports.values():
                add_depends(graph=graph, plugin=plugin, module=module, plugins=plugins)
        if 'depends' in opts:
            deps = opts['depends']
            assert isinstance(deps, list), f'Wrong plugin dependencies type {type(deps)} (must be a list)'
            for item in deps:
                graph.add_edge(plugin, item)
    for plugin in plugins:
        nodes = nx.descendants(graph, plugin)
        if len(nodes) > 0:
            opts = config[plugin]
            deps = set(opts['depends']) if 'depends' in opts else set()
            deps.update(nodes)
            opts['depends'] = list(deps)


def optional_int(value):
    return value if re.match(r'^-?\d+$', value) is None else int(value)


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
    if name == 'execute':
        assert 'method' in params, f'Failed to find "method" in execute section\n{params}'
        modname = params['method']
    else:
        assert 'module' in params, f'Failed find "module" for plugin {name} in section\n{params}'
        modname = params['module']
    parts = modname.split('^')
    if len(parts) == 1:
        index = None
    else:
        assert len(parts) == 2, f'Wrong module index format ({parts=}) for plugin {name} in config\n{config}'
        modname = parts[0]
        index = parts[1]
    parts = modname.split('/')
    if len(parts) > 1:
        assert len(parts) == 2, f'Wrong module name format ({parts=}) for plugin {name} in config\n{config}'
        modname = parts[0]
        classname = parts[1]
    else:
        classname = None
    options = params['options'] if 'options' in params else dict()
    if 'imports' in params:
        imports = params['imports']
        for key, value in imports.items():
            if key == '__kwargs__':
                options.update(resolve_option(value, state))
            elif isinstance(value, str):
                parts = value.split('^')
                if len(parts) == 1:
                    idx = None
                else:
                    assert len(parts) == 2, \
                        f'Wrong importing value index format ({parts=}) for plugin {name} in config\n{config}'
                    value = parts[0]
                    idx = parts[1]
                assert value in state, f'Failed to resolve importing value {value} for plugin {name} in config\n{config}'
                value = state[value]
                if idx is not None:
                    assert hasattr(value, '__getitem__'), \
                        f'Imported class {type(value)} does not have attribute ' \
                        f'__getitem__ for plugin {name} in config\n{config}'
                    value = value[optional_int(idx)]
                options[key] = value
            else:
                options[key] = resolve_option(value, state)
    if (
            ('__mute__' in config)
            and ((name in config['__mute__']) or ('__all__' in config['__mute__']))
            and (('__unmute__' not in config) or (name not in config['__unmute__']))
    ):
        logging.debug(f'Creating plugin {name}')
    else:
        logging.debug(f'Creating plugin {name} from config\n{options}')
    if modname.startswith('plugins.') and (modname in state):
        plugin = state[modname]
        if classname is None:
            plugin = plugin(**options)
        else:
            assert hasattr(plugin, classname), \
                f'Plugin {modname} does not have attribute {classname} for plugin {name} in config\n{config}'
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
                assert hasattr(module, classname), \
                    f'Module {modname} does not have class {classname} for plugin {name} in config\n{config}'
                classtype = getattr(module, classname)
                plugin = classtype(**options)
            else:
                classname = parts[0]
                attribute = parts[1]
                assert hasattr(module, classname), \
                    f'Module {modname} does not have class {classname} for plugin {name} in config\n{config}'
                classtype = getattr(module, classname)
                assert hasattr(classtype, attribute), \
                    f'Class {classname} does not have attribute {attribute} for plugin {name} in config\n{config}'
                method = getattr(classtype, attribute)
                plugin = method(**options)
    if index is not None:
        assert hasattr(plugin, '__getitem__'), \
            f'Class {type(plugin)} does not have attribute __getitem__ for plugin {name} in config\n{config}'
        plugin = plugin[optional_int(index)]
    if 'exports' in params:
        for attr in params['exports']:
            if hasattr(plugin, 'export'):
                state[f'{name}.{attr}'] = plugin.export(attr)
            elif hasattr(plugin, attr):
                state[f'{name}.{attr}'] = getattr(plugin, attr)
            else:
                assert False, f'Plugin {type(plugin)} does not have attribute {attr} for plugin {name} in config\n{config}'
    state[f'plugins.{name}'] = plugin
