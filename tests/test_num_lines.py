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
        assert values['num1'] == 27
        assert values['num2'] == 20
        assert values['num3'] == 3
        assert values['num4'] == 2


if __name__ == '__main__':
    unittest.main()
