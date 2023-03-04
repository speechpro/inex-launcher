import logging
from inex.utils.configure import resolve_option, create_plugin


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
    params = exopts['options'] if 'options' in exopts else dict()
    if 'imports' in exopts:
        imports = exopts['imports']
        for key, value in imports.items():
            if isinstance(value, str):
                assert value in state, f'Failed to resolve value {value}'
                params[key] = state[value]
            else:
                params[key] = resolve_option(value, state)
    method(**params)
