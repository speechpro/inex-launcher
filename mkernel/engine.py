import logging
from mkernel.utils.configure import resolve_option, create_plugin


class Engine:
    def __init__(self, config, state):
        logging.debug('Creating plugins')
        assert 'plugins' in config, f'Failed to find "plugins" in config\n{config}'
        plugins = config['plugins']
        assert isinstance(plugins, list), f'Wrong type of "plugins" {type(plugins)} (must be list)'
        for plugin in plugins:
            create_plugin(plugin, config, state)
        logging.debug('Looking for execution options')
        if 'execute' in config:
            logging.debug('Loading advanced execution options')
            exopts = config['execute']
            logging.debug(f'Loading execution options from options\n{exopts}')
            assert 'method' in exopts, f'Failed to find "method" in options\n{exopts}'
            value = exopts['method']
            parts = value.split('/')
            if len(parts) == 1:
                plugin = value
                method = 'run'
            else:
                assert len(parts) == 2, f'Wrong execution option format in line\n{value}'
                plugin = parts[0]
                method = parts[1]
            assert plugin in state, f'Failed to find "{plugin}" in options\n{state}'
            plugin = state[plugin]
            assert hasattr(plugin, method), f'Plugin {type(plugins)} does not have attribute "{method}"'
            self.method = getattr(plugin, method)
            self.params = exopts['options'] if 'options' in exopts else dict()
            if 'imports' in exopts:
                imports = exopts['imports']
                for key, value in imports.items():
                    self.params[key] = resolve_option(value, state)
        else:
            logging.debug('Loading base execution options')
            assert 'start' in config, f'Failed to find "start" in config\n{config}'
            value = config['start']
            parts = value.split('/')
            if len(parts) == 1:
                plugin = value
                method = 'run'
            else:
                assert len(parts) == 2, f'Wrong execution option format in line\n{value}'
                plugin = parts[0]
                method = parts[1]
            assert plugin in state, f'Failed to find "{plugin}" in options\n{state}'
            plugin = state[plugin]
            assert hasattr(plugin, method), f'Plugin {type(plugins)} does not have attribute "{method}"'
            self.method = getattr(plugin, method)
            self.params = dict()

    def __call__(self):
        return self.method(**self.params)
