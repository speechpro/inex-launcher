from random import randint


class Generator:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def get(self, name):
        if name == 'value':
            return self.__call__()

    def __call__(self):
        return randint(self.a, self.b)
