import logging
from inex.utils.configure import optional_int, resolve_option, create_plugin


def execute(config, state):
    logging.debug('Creating plugins')
    if 'plugins' in config:
        plugins = config['plugins']
        assert isinstance(plugins, list), f'Wrong type of "plugins" {type(plugins)} (must be list)'
        for plugin in plugins:
            create_plugin(plugin, config, state)
    logging.debug('Looking for execution options')
    assert 'execute' in config, f'Failed to find "execute" section in config\n{config}'
    logging.debug('Loading execution options')
    exopts = config['execute']
    logging.debug(f'Loading execution options from options\n{exopts}')
    assert 'method' in exopts, f'Failed to find "method" in options\n{exopts}'
    plugin = exopts['method']
    parts = plugin.split('^')
    if len(parts) == 1:
        index = None
    else:
        assert len(parts) == 2, f'Wrong method index format ({parts=}) in options\n{exopts}'
        plugin = parts[0]
        index = parts[1]
    parts = plugin.split('/')
    if len(parts) > 1:
        plugin = parts[0]
        method = parts[1]
    else:
        method = None
    if plugin in state:
        plugin = state[plugin]
    else:
        logging.debug(f'Loading module {plugin}')
        plugin = __import__(plugin, fromlist=[''])
    if method is None:
        method = plugin
    else:
        assert hasattr(plugin, method), f'Plugin {type(plugin)} does not have attribute "{method}"'
        method = getattr(plugin, method)
    if index is not None:
        assert hasattr(method, '__getitem__'), f'Class {type(method)} does not have attribute __getitem__ in options\n{exopts}'
        method = method[optional_int(index)]
    params = exopts['options'] if 'options' in exopts else dict()
    if 'imports' in exopts:
        imports = exopts['imports']
        for key, value in imports.items():
            if isinstance(value, str):
                parts = value.split('^')
                if len(parts) == 1:
                    idx = None
                else:
                    assert len(parts) == 2, f'Wrong importing value index format ({parts=}) in options\n{exopts}'
                    value = parts[0]
                    idx = parts[1]
                assert value in state, f'Failed to resolve value {value} in options\n{exopts}'
                value = state[value]
                if idx is not None:
                    assert hasattr(value, '__getitem__'), f'Imported class {type(value)} does not have attribute __getitem__ in options\n{exopts}'
                    value = value[optional_int(idx)]
                params[key] = value
            else:
                params[key] = resolve_option(value, state)
    method(**params)
