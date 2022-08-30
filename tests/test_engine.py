import unittest
from mkernel.utils.options import Options
from mkernel.engine import Engine


class MkernelEngine(unittest.TestCase):
    config = {
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
            'module': 'tests.plugins.chunker',
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

    def test_engine(self):
        state = dict()
        engine = Engine(Options(self.config), state)
        dataset = engine.run()
        self.assertEqual(100, len(dataset))
        for chunk in dataset:
            self.assertEqual(20, chunk.shape[0])
            self.assertEqual(40, chunk.shape[1])


if __name__ == '__main__':
    unittest.main()
