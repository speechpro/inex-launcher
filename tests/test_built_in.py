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
        assert values['max'] == 2
        assert values['eval'] == 15
        assert isinstance(values['tuple'], tuple)
        assert values['tuple'] == (1, 2, 3)


if __name__ == '__main__':
    unittest.main()
