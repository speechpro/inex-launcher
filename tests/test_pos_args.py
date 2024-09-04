import unittest
from typing import List
from pathlib import Path
from tests.utils import call_engine


class Object:
    def __init__(self, a, b, c, d, e, f, g):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f
        self.g = g


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        objects: List[Object] = call_engine(config)
        for object in objects:
            assert object.a == 1
            assert object.b == 2
            assert object.c == [3, 4]
            assert object.d == 5
            assert object.e == 6
            assert object.f == 7
            assert object.g == 8


if __name__ == '__main__':
    unittest.main()
