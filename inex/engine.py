import logging
from inex.utils.configure import create_plugin


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
    create_plugin('execute', config, state)
