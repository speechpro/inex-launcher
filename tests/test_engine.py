import unittest
from mkernel.utils.options import Options
from mkernel.engine import Engine


class MkernelEngine(unittest.TestCase):
    config1 = {
        'plugins': [
          'features',
          'chunker',
          'dataset',
        ],
        'start': 'plugins.dataset',
        'features': {
            'module': 'tests.plugins.features',
            'imports': {},
            'exports': ['frequency', 'frame_length', 'frame_shift', 'feature_dim', 'get_num_frames'],
            'options': {
                'frequency': 16000,
                'frame_length': 400,
                'frame_shift': 160,
                'feature_dim': 40,
            }
        },
        'chunker': {
            'module': 'tests.plugins.chunker/Chunker',
            'imports': {},
            'exports': ['left_context', 'window_length', 'right_context'],
            'options': {
                'left_context': 7,
                'window_length': 10,
                'right_context': 3,
            }
        },
        'dataset': {
            'module': 'tests.plugins.dataset',
            'imports': {
                'frame_length': 'features.frame_length',
                'frame_shift': 'features.frame_shift',
                'feature_dim': 'features.feature_dim',
                'left_context': 'chunker.left_context',
                'window_length': 'chunker.window_length',
                'right_context': 'chunker.right_context',
                'features': 'plugins.features',
                'chunker': 'plugins.chunker',
            },
            'exports': [],
            'options': {
                'num_chunks': 100
            }
        },
    }

    config2 = {
        'plugins': [
          'plugin',
          'runner',
        ],
        'plugin': {
            'module': 'tests.plugins.collection/Plugin',
            'imports': {},
            'exports': ['value'],
            'options': {
                'value': 17,
            }
        },
        'runner': {
            'module': 'tests.plugins.collection/Runner',
            'imports': {
                'value1': 'plugin.value',
                'plugin': 'plugins.plugin',
            },
            'exports': [],
            'options': {
                'value2': 23,
            }
        },
        'execute': {
            'method': 'plugins.runner/check',
            'imports': {
                'value1': 'plugin.value',
                'plugin': 'plugins.plugin',
            },
            'options': {
                'value2': 23
            }
        },
    }

    def test_base(self):
        state = dict()
        engine = Engine(Options(self.config1), state)
        dataset = engine.run()
        self.assertEqual(100, len(dataset))
        for chunk in dataset:
            self.assertEqual(20, chunk.shape[0])
            self.assertEqual(40, chunk.shape[1])

    def test_advanced(self):
        state = dict()
        engine = Engine(Options(self.config2), state)
        engine.run()


if __name__ == '__main__':
    unittest.main()
