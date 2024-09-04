import unittest
import numpy as np
from pathlib import Path
from typing import Dict, Any
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.2.yaml')
        assert config.is_file()
        values: Dict[str, Any] = call_engine(config)
        assert values['a'] == 1
        assert values['b'] == 2
        assert values['c'] == [3, 4, 5]


if __name__ == '__main__':
    unittest.main()
