import unittest
from pathlib import Path
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_stop_after1():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        result = call_engine(config, stop_after='plugin1')
        assert result == 1

    @staticmethod
    def test_stop_after2():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        result = call_engine(config, stop_after='plugin2')
        assert result == 2

    @staticmethod
    def test_stop_after3():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        result = call_engine(config, stop_after='plugin3')
        assert result == 3


if __name__ == '__main__':
    unittest.main()
