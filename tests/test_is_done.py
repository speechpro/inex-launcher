import unittest
from pathlib import Path
from typing import Dict, Any
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_config_file():
        Path('tests/.done').unlink(missing_ok=True)
        Path('tests/src_data.txt').touch()
        Path('tests/old_data.txt').touch()
        config = Path(__file__).with_suffix('.yaml')
        assert config.is_file()
        values: Dict[str, Any] = call_engine(config)
        assert values['value1'] == 5
        assert values['value2'] is None
        assert not Path('tests/src_data.txt').exists()
        assert not Path('tests/old_data.txt').exists()
        assert not Path('tests/temp_dir').exists()
        Path('tests/.done').unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
