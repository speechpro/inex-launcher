from mkernel.utils.configure import create_plugin, get_as_is


class Engine:
    def __init__(self, config, state):
        plugins = config.as_is('plugins', required=True)
        assert isinstance(plugins, list), f'Wrong type of the "plugins" {type(plugins)} (must be list)'
        for plugin in plugins:
            create_plugin(plugin, config, state)
        self.start = get_as_is(state, config.as_is('start', required=True), required=True)

    def run(self):
        return self.start.run()
