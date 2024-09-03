import unittest
from pathlib import Path
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        result = call_engine(config)
        assert result['copy'] == 1
        assert result['list'] == [2]
        result = result['dict']
        assert result['copy'] == 2
        assert result['list'] == [3]
        assert result['dict']['value'] == [1, 2, 3]


if __name__ == '__main__':
    unittest.main()
