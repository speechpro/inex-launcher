import logging
from mkernel.utils.configure import create_plugin, get_as_is


class Engine:
    def __init__(self, config, state):
        logging.debug('Creating plugins')
        plugins = config.as_is('plugins', required=True)
        assert isinstance(plugins, list), f'Wrong type of the "plugins" {type(plugins)} (must be list)'
        for plugin in plugins:
            create_plugin(plugin, config, state)
        logging.debug('Looking for execution options')
        if 'execute' in config:
            logging.debug('Loading advanced execution options')
            exopts = config.as_is('execute', required=True)
            logging.debug(f'Loading execution options from config:\n{exopts}')
            value = get_as_is(exopts, 'method', required=True)
            parts = value.split('/')
            if len(parts) == 1:
                plugin = value
                method = 'run'
            else:
                assert len(parts) == 2, f'Wrong execution option format in line "{value}"'
                plugin = parts[0]
                method = parts[1]
            plugin = get_as_is(state, plugin, required=True)
            assert hasattr(plugin, method), f'Plugin {type(plugins)} does not have attribute {method}'
            self.method = getattr(plugin, method)
            self.params = exopts['options'] if 'options' in exopts else dict()
            if 'imports' in exopts:
                imports = exopts['imports']
                for key, value in imports.items():
                    if isinstance(value, list):
                        values = list()
                        for value1 in value:
                            values.append(state[value1] if value1 in state else value1)
                        self.params[key] = values
                    elif isinstance(value, dict):
                        values = dict()
                        for key1, value1 in value.items():
                            values[key1] = state[value1] if value1 in state else value1
                        self.params[key] = values
                    else:
                        self.params[key] = state[value]
        else:
            logging.debug('Loading base execution options')
            value = config.as_is('start', required=True)
            parts = value.split('/')
            if len(parts) == 1:
                plugin = value
                method = 'run'
            else:
                assert len(parts) == 2, f'Wrong execution option format in line "{value}"'
                plugin = parts[0]
                method = parts[1]
            plugin = get_as_is(state, plugin, required=True)
            assert hasattr(plugin, method), f'Plugin {type(plugins)} does not have attribute {method}'
            self.method = getattr(plugin, method)
            self.params = dict()

    def run(self):
        return self.method(**self.params)
