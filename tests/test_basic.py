import unittest
from pathlib import Path
from tests.utils import call_engine


def return_value(value):
    return value


class Value:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'[Value: {self.value}]'


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        value1, value2 = call_engine(config)
        assert value1 == 5
        assert value2 == 7

    @staticmethod
    def test_config_dict():
        config = {
            'plugins': ['value1', 'value2'],
            'value1': {
                'module': 'tests.test_basic/return_value',
                'options': {
                    'value': 5,
                },
            },
            'value2': {
                'module': 'tests.test_basic/Value',
                'exports': ['value'],
                'options': {
                    'value': 7,
                },
            },
            'execute': {
                'method': 'inex.helpers/assign',
                'imports': {
                    'value': ['plugins.value1', 'value2.value'],
                },
            },
        }
        value1, value2 = call_engine(config)
        assert value1 == 5
        assert value2 == 7


if __name__ == '__main__':
    unittest.main()
