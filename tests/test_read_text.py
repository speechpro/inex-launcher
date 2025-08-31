import unittest
from pathlib import Path
from typing import Dict, Any
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        values: Dict[str, Any] = call_engine(config)
        assert values['value_str'] == '17'
        assert values['value_int'] == 17
        assert values['value_float'] == 17.0
        assert values['value_bool']


if __name__ == '__main__':
    unittest.main()
