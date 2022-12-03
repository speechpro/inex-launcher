

class Plugin:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


class Runner:
    def __init__(self, plugin, value1, value2):
        self.plugin = plugin
        self.value1 = value1
        self.value2 = value2

    def check(self, plugin, value1, value2):
        assert plugin() == self.plugin()
        assert plugin() == self.value1
        assert value1 == self.value1
        assert value2 == self.value2
