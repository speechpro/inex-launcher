import unittest
import numpy as np
from typing import List
from pathlib import Path
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        arrays: List[np.ndarray] = call_engine(config)
        assert np.array_equal(arrays[0], np.array([1, 2, 3]))


if __name__ == '__main__':
    unittest.main()
