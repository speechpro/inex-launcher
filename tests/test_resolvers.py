import os
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
        assert values['evaluate1'] == 7
        assert values['evaluate2'] == 6
        assert os.getenv('Seven') == '7'
        assert values['seven_set'] == 7
        assert values['seven_get'] == 7
        assert values['path_parent'].endswith('tests')
        assert values['path_name'] == 'test_resolvers.yaml'
        assert values['path_stem'] == 'test_resolvers'
        assert values['path_suffix'] == '.yaml'
        assert values['path_is_file']
        assert not values['path_is_dir']
        assert values['path_exists']


if __name__ == '__main__':
    unittest.main()
