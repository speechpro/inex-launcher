import unittest
import numpy as np
from pathlib import Path
from typing import Dict, Any
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.3.yaml')
        assert config.is_file()
        values: Dict[str, Any] = call_engine(config)
        assert values['value1'] == 7
        assert np.array_equal(values['value2'], np.array([1, 2, 3]))
        assert np.array_equal(values['value3'], np.array([1, 2, 3]))
        id2 = id(values['value2'])
        id3 = id(values['value3'])
        assert id3 == id2


if __name__ == '__main__':
    unittest.main()
