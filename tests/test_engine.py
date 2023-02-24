import unittest
from inex.engine import Engine


class InexEngine(unittest.TestCase):
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
          'number1',
          'number2',
          'number3',
          'runner',
        ],
        'number1': {
            'module': 'tests.plugins.collection/Number',
            'imports': {},
            'exports': ['value'],
            'options': {
                'value': 1,
            }
        },
        'number2': {
            'module': 'tests.plugins.collection/Number',
            'imports': {},
            'exports': ['value'],
            'options': {
                'value': 2,
            }
        },
        'number3': {
            'module': 'tests.plugins.collection/Number',
            'imports': {},
            'exports': ['value'],
            'options': {
                'value': 3,
            }
        },
        'runner': {
            'module': 'tests.plugins.collection/Runner',
            'imports': {
                'number3': 'number3.value',
                'arr_val1': ['number3.value', 'number1.value', 'number2.value'],
                'dic_val1': {3: 'number3.value', 1: 'number1.value', 2: 'number2.value'},
                'plugin1': 'plugins.number1',
                'plugin2': 'plugins.number2',
                'plugin3': 'plugins.number3',
            },
            'exports': [],
            'options': {
                'number1': 1,
                'number2': 2,
            }
        },
        'execute': {
            'method': 'plugins.runner/check',
            'imports': {
                'number3': 'number3.value',
                'arr_val2': ['number3.value', 'number1.value', 'number2.value'],
                'dic_val2': {3: 'number3.value', 1: 'number1.value', 2: 'number2.value'},
                'plugin1': 'plugins.number1',
                'plugin2': 'plugins.number2',
                'plugin3': 'plugins.number3',
            },
            'options': {
                'number1': 1,
                'number2': 2,
                'number4': 23,
                'arr_val3': [3, 1, 2],
                'dic_val3': {1: 1, 2: 2, 3: 3},
            }
        },
    }

    config3 = {
        'plugins': [
          'number1',
          'number2',
          'number3',
          'resolve',
        ],
        'number1': {
            'module': 'tests.plugins.collection/Number',
            'imports': {},
            'exports': ['value'],
            'options': {
                'value': 1,
            }
        },
        'number2': {
            'module': 'tests.plugins.collection/Number',
            'imports': {},
            'exports': ['value'],
            'options': {
                'value': 2,
            }
        },
        'number3': {
            'module': 'tests.plugins.collection/Number',
            'imports': {},
            'exports': ['value'],
            'options': {
                'value': 3,
            }
        },
        'resolve': {
            'module': 'tests.plugins.collection/TestResolve',
            'imports': {
                'data1': ['number1.value', ['number1.value', 'number2.value', 'number3.value'], {1: 'plugins.number1', 2: 'plugins.number2', 3: 'plugins.number3'}],
                'data2': {1: 'plugins.number1', 2: ['number1.value', 'number2.value', 'number3.value'], 3: {1: 'plugins.number1', 2: 'plugins.number2', 3: 'plugins.number3'}},
            },
            'exports': [],
            'options': {},
        },
        'execute': {
            'method': 'plugins.resolve/test',
            'imports': {
                'data1': ['number1.value', ['number1.value', 'number2.value', 'number3.value'], {1: 'plugins.number1', 2: 'plugins.number2', 3: 'plugins.number3'}],
                'data2': {1: 'plugins.number1', 2: ['number1.value', 'number2.value', 'number3.value'], 3: {1: 'plugins.number1', 2: 'plugins.number2', 3: 'plugins.number3'}},
            },
            'options': {}
        },
    }

    def test_base(self):
        state = dict()
        engine = Engine(self.config1, state)
        dataset = engine()
        self.assertEqual(100, len(dataset))
        for chunk in dataset:
            self.assertEqual(20, chunk.shape[0])
            self.assertEqual(40, chunk.shape[1])

    def test_advanced(self):
        state = dict()
        engine = Engine(self.config2, state)
        engine()

    def test_resolve(self):
        state = dict()
        engine = Engine(self.config3, state)
        engine()


if __name__ == '__main__':
    unittest.main()
