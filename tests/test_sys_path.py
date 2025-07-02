import tempfile
import unittest
from pathlib import Path
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_cli():
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)
            code = 'def get_value(value: int) -> int:\n    return value\n'
            code_path = tempdir / 'my_module_cli.py'
            code_path.write_text(code, encoding='utf-8')
            config = f'''
            execute:
              method: my_module_cli/get_value
              options:
                value: 5
            '''
            conf_path = tempdir / 'test_sys_path.yaml'
            conf_path.write_text(config, encoding='utf-8')
            result = call_engine(conf_path, sys_path=str(tempdir))
        assert result == 5

    @staticmethod
    def test_config():
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)
            code = 'def get_value(value: int) -> int:\n    return value\n'
            code_path = tempdir / 'my_module_config.py'
            code_path.write_text(code, encoding='utf-8')
            config = f'''
            __sys_path__: {tempdir}
            execute:
              method: my_module_config/get_value
              options:
                value: 7
            '''
            conf_path = tempdir / 'test_sys_path.yaml'
            conf_path.write_text(config, encoding='utf-8')
            result = call_engine(conf_path)
        assert result == 7


if __name__ == '__main__':
    unittest.main()
