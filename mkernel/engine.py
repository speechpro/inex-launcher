from mkernel.utils.configure import create_plugin, get_as_is


class Engine:
    def __init__(self, config, state):
        plugins = config.as_is('plugins', required=True)
        assert isinstance(plugins, list), f'Wrong type of the "plugins" {type(plugins)} (must be list)'
        for plugin in plugins:
            create_plugin(plugin, config, state)
        if 'execute' in config:
            exopts = config.as_is('execute', required=True)
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
                    self.params[key] = state[value]
        else:
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
