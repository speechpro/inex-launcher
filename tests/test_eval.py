import unittest
import numpy as np
from pathlib import Path
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        result = call_engine(config)
        assert result['a+b'] == 5
        assert np.array_equal(result['mul'], np.array([5, 10, 15]))


if __name__ == '__main__':
    unittest.main()
