import unittest
from pathlib import Path
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        result = call_engine(config)
        assert result['copy'] == 5
        assert result['list'] == [5]
        result = result['dict']
        assert result['copy'] == 5
        assert result['list'] == [5]
        assert result['dict']['value'] == 5


if __name__ == '__main__':
    unittest.main()
