import pytest
import unittest
import tempfile
from pathlib import Path
from omegaconf import OmegaConf
from inex.helpers import compose


class TestModule(unittest.TestCase):
    @staticmethod
    def test_compose():
        path = Path(__file__).with_suffix('.1.yaml')
        assert path.is_file()
        config = OmegaConf.load(path)
        config = OmegaConf.to_container(config)
        merge_path = Path(__file__).with_suffix('.2.yaml')
        assert merge_path.is_file()
        with tempfile.TemporaryDirectory() as tempdir:
            result_path = Path(tempdir) / 'config.yaml'
            config = compose(
                config=config,
                merge_paths=str(merge_path),
                merge_dicts=[
                    {'option4': 4},
                    {'option5': 5},
                ],
                override=[
                    'option1=1',
                    'option2=2',
                    'option3=3',
                ],
                result_path=str(result_path),
            )
            result = OmegaConf.load(result_path)
        result = OmegaConf.to_container(result)
        for i in [1, 2, 3]:
            assert config[f'option{i}'] == i
            assert config[f'value{i}']['options']['value'] == i
        for i in [4, 5]:
            assert config[f'option{i}'] == i
        assert result == config

    @staticmethod
    def test_compose_load():
        config_path = Path(__file__).with_suffix('.1.yaml')
        assert config_path.is_file()
        merge_path = Path(__file__).with_suffix('.2.yaml')
        assert merge_path.is_file()
        with tempfile.TemporaryDirectory() as tempdir:
            result_path = Path(tempdir) / 'config.yaml'
            config = compose(
                config_path=str(config_path),
                merge_paths=str(merge_path),
                merge_dicts=[
                    {'option4': 4},
                    {'option5': 5},
                ],
                override=[
                    'option1=1',
                    'option2=2',
                    'option3=3',
                ],
                result_path=str(result_path),
            )
            result = OmegaConf.load(result_path)
        result = OmegaConf.to_container(result)
        for i in [1, 2, 3]:
            assert config[f'option{i}'] == i
            assert config[f'value{i}']['options']['value'] == i
        for i in [4, 5]:
            assert config[f'option{i}'] == i
        assert result == config

    @staticmethod
    def test_compose_check_exists():
        config_path = Path(__file__).with_suffix('.1.yaml')
        assert config_path.is_file()
        merge_path = Path(__file__).with_suffix('.2.yaml')
        assert merge_path.is_file()
        with pytest.raises(AssertionError) as excinfo:
            with tempfile.TemporaryDirectory() as tempdir:
                result_path = Path(tempdir) / 'config.yaml'
                compose(
                    config_path=str(config_path),
                    merge_paths=str(merge_path),
                    merge_dicts=[
                        {'option4': 4},
                        {'option5': 5},
                    ],
                    override=[
                        'option1=1',
                        'option2=2',
                        'option3=3',
                    ],
                    result_path=str(result_path),
                )
                compose(
                    config_path=str(config_path),
                    merge_paths=str(merge_path),
                    merge_dicts=[
                        {'option4': 4},
                        {'option5': 5},
                    ],
                    override=[
                        'option1=1',
                        'option2=2',
                        'option3=3',
                    ],
                    result_path=str(result_path),
                    check_file='fail_if_exists',
                )
        assert str(excinfo.value).find('already exists') > 0

    @staticmethod
    def test_compose_check_diff():
        config_path = Path(__file__).with_suffix('.1.yaml')
        assert config_path.is_file()
        merge_path = Path(__file__).with_suffix('.2.yaml')
        assert merge_path.is_file()
        with pytest.raises(AssertionError) as excinfo:
            with tempfile.TemporaryDirectory() as tempdir:
                result_path = Path(tempdir) / 'config.yaml'
                compose(
                    config_path=str(config_path),
                    merge_paths=str(merge_path),
                    merge_dicts=[
                        {'option4': 4},
                        {'option5': 5},
                    ],
                    override=[
                        'option1=1',
                        'option2=2',
                        'option3=3',
                    ],
                    result_path=str(result_path),
                )
                compose(
                    config_path=str(config_path),
                    merge_paths=str(merge_path),
                    merge_dicts=[
                        {'option4': 3},
                        {'option5': 5},
                    ],
                    override=[
                        'option1=1',
                        'option2=2',
                        'option3=3',
                    ],
                    result_path=str(result_path),
                )
        assert str(excinfo.value).startswith('New config and existing')


if __name__ == '__main__':
    unittest.main()
