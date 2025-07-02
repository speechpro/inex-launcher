import tempfile
import unittest
from pathlib import Path
from tests.utils import call_engine


class TestModule(unittest.TestCase):
    @staticmethod
    def test_cli_default_warning():
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)
            conf_path = tempdir / 'test_log_path.yaml'
            log_path = tempdir / 'test_log_path.log'
            config = f'''
            execute:
              method: logging/warning
              options:
                msg: 'This is warning message'
            '''
            conf_path.write_text(config, encoding='utf-8')
            call_engine(conf_path, log_path=log_path)
            assert log_path.is_file()
            log_text = log_path.read_text(encoding='utf-8')
            conf_path.unlink()
            log_path.unlink()
        assert 'WARNING - This is warning message' in log_text

    @staticmethod
    def test_cli_default_debug():
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)
            conf_path = tempdir / 'test_log_path.yaml'
            log_path = tempdir / 'test_log_path.log'
            config = f'''
            execute:
              method: logging/debug
              options:
                msg: 'This is debug message'
            '''
            conf_path.write_text(config, encoding='utf-8')
            call_engine(conf_path, log_path=log_path)
            assert log_path.is_file()
            log_text = log_path.read_text(encoding='utf-8')
            conf_path.unlink()
            log_path.unlink()
        assert len(log_text) == 0

    @staticmethod
    def test_cli_debug():
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)
            conf_path = tempdir / 'test_log_path.yaml'
            log_path = tempdir / 'test_log_path.log'
            config = f'''
            execute:
              method: logging/debug
              options:
                msg: 'This is debug message'
            '''
            conf_path.write_text(config, encoding='utf-8')
            call_engine(conf_path, log_level='DEBUG', log_path=log_path)
            assert log_path.is_file()
            log_text = log_path.read_text(encoding='utf-8')
            conf_path.unlink()
            log_path.unlink()
        assert 'DEBUG - This is debug message' in log_text

    @staticmethod
    def test_config_debug():
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)
            conf_path = tempdir / 'test_log_path.yaml'
            log_path = tempdir / 'test_log_path.log'
            config = f'''
            __log_level__: DEBUG
            __log_path__: {str(log_path)}
            execute:
              method: logging/debug
              options:
                msg: 'This is debug message'
            '''
            conf_path.write_text(config, encoding='utf-8')
            call_engine(conf_path)
            assert log_path.is_file()
            log_text = log_path.read_text(encoding='utf-8')
            conf_path.unlink()
            log_path.unlink()
        assert 'DEBUG - This is debug message' in log_text

    @staticmethod
    def test_config_warning():
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)
            conf_path = tempdir / 'test_log_path.yaml'
            log_path = tempdir / 'test_log_path.log'
            config = f'''
            __log_level__: WARNING
            __log_path__: {str(log_path)}
            execute:
              method: logging/warning
              options:
                msg: 'This is warning message'
            '''
            conf_path.write_text(config, encoding='utf-8')
            call_engine(conf_path)
            assert log_path.is_file()
            log_text = log_path.read_text(encoding='utf-8')
            conf_path.unlink()
            log_path.unlink()
        assert 'WARNING - This is warning message' in log_text


if __name__ == '__main__':
    unittest.main()
