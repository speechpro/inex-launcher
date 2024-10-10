import logging
from inex.utils.configure import create_plugin


def execute(config, state, stop_after=None):
    logging.debug('Creating plugins')
    plugin = None
    if 'plugins' in config:
        plugins = config['plugins']
        assert isinstance(plugins, list), f'Wrong type of "plugins" {type(plugins)} (must be list)'
        for plug_name in plugins:
            plugin = create_plugin(plug_name, config, state)
            if (stop_after is not None) and (plug_name == stop_after):
                logging.info(f'Execution stopped: condition "{plug_name} == {stop_after}" reached.')
                return plugin
    logging.debug('Looking for execution options')
    if 'execute' in config:
        logging.debug('Loading execution options')
        plugin = create_plugin('execute', config, state)
    else:
        logging.debug(f'Execution section does not exist in config\n{config}')
    return plugin
