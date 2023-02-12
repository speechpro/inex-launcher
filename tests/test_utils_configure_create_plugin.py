import unittest
from inex.utils.configure import create_plugin


class UtilsConfigureCreatePlugin(unittest.TestCase):
    config = {
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
    }

    @staticmethod
    def num_frames(frame_length, frame_shift, lengths):
        return (lengths - frame_length) // frame_shift + 1

    def test_create_features(self):
        state = dict()
        create_plugin('features', self.config, state)
        self.assertTrue('plugins.features' in state)
        self.assertEqual(16000, state['features.frequency'])
        frame_length = state['features.frame_length']
        self.assertEqual(400, frame_length)
        frame_shift = state['features.frame_shift']
        self.assertEqual(160, frame_shift)
        self.assertEqual(40, state['features.feature_dim'])
        get_num_frames = state['features.get_num_frames']
        lengths = 12345
        num_frames = self.num_frames(frame_length, frame_shift, lengths)
        self.assertEqual(num_frames, get_num_frames(lengths))
        features = state['plugins.features']
        self.assertEqual(num_frames, features.get_num_frames(lengths))

    def test_create_chunker(self):
        state = dict()
        create_plugin('chunker', self.config, state)
        self.assertTrue('plugins.chunker' in state)
        self.assertEqual(7, state['chunker.left_context'])
        self.assertEqual(10, state['chunker.window_length'])
        self.assertEqual(3, state['chunker.right_context'])


if __name__ == '__main__':
    unittest.main()
