import unittest
from pathlib import Path
from tests.utils import call_engine


def return_value(value):
    return value


class InexEngine(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        value = call_engine(config)
        assert value == 5

    @staticmethod
    def test_config_dict():
        config = {
            'execute': {
                'method': 'tests.test_01_execute/return_value',
                'options': {
                    'value': 7,
                },
            },
        }
        value = call_engine(config)
        assert value == 7


if __name__ == '__main__':
    unittest.main()
