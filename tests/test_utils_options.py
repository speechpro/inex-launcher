import unittest
from omegaconf import OmegaConf
from mkernel.utils.configure import load_config
from mkernel.utils.options import Options


class UtilsOptions(unittest.TestCase):
    options = '''
        num_iters: 100

        features:
          package: mkernel.default.features
          options:
            features_type: kaldi-fbank
            sample_frequency: 16000
            num_mel_bins: 40
            device: cpu

        chunker:
          package: mkernel.default.chunking
          options:
            left_context: 5
            window_length: 1
            right_context: 5

        scheduler:
          package: mkernel.default.schedulers.one_cycle_lr
          options:
            max_lr: 0.001
            total_steps: << trainer.options.num_iters

        trainer:
          package: mkernel.default.trainer
          options:
            train_dir: exp/train
            num_iters: << num_iters
            save_iters: {begin: 70, step: 5}
            device: cuda
    '''

    def test_base(self):
        options = Options()
        options['a'] = 1
        self.assertEqual(1, options['a'])
        options['b.c'] = 2
        self.assertEqual(2, options['b.c'])
        del options['b.c']
        self.assertEqual(None, options['b.c'])
        del options['a']
        self.assertEqual(None, options['a'])

    def test_data(self):
        options = Options(OmegaConf.to_container(load_config(self.options), resolve=True))
        self.assertTrue('features' in options)
        self.assertTrue('chunker' in options)
        self.assertTrue('blabla' not in options)
        self.assertEqual(None, options['blabla'])
        self.assertEqual(None, options['feats.package'])
        self.assertEqual('mkernel.default.features', options['features.package'])
        self.assertEqual('kaldi-fbank', options['features.options.features_type'])
        self.assertEqual(16000, options['features.options.sample_frequency'])
        self.assertEqual(40, options['features.options.num_mel_bins'])
        self.assertEqual('cpu', options['features.options.device'])
        self.assertEqual('mkernel.default.chunking', options['chunker.package'])
        self.assertEqual(5, options['chunker.options.right_context'])

    def test_reference(self):
        options = Options(OmegaConf.to_container(load_config(self.options), resolve=True))
        self.assertTrue('num_iters' in options)
        self.assertEqual(100, options['num_iters'])
        self.assertEqual(100, options['trainer.options.num_iters'])
        self.assertEqual(100, options['scheduler.options.total_steps'])

    def test_resolve(self):
        options = Options(OmegaConf.to_container(load_config(self.options), resolve=True))
        options.resolve()
        options = options.data
        self.assertEqual(100, options['scheduler']['options']['total_steps'])
        self.assertEqual(100, options['trainer']['options']['num_iters'])

    def test_as_type(self):
        value = Options({'value': 5}).as_int('value')
        self.assertTrue(isinstance(value, int))
        self.assertEqual(5, value)
        value = Options({'value': '5'}).as_int('value')
        self.assertTrue(isinstance(value, int))
        self.assertEqual(5, value)
        value = Options({'value': '5'}).as_int('abc', default=3)
        self.assertTrue(isinstance(value, int))
        self.assertEqual(3, value)
        value = Options({'value': '5'}).as_int('abc', default='3')
        self.assertTrue(isinstance(value, int))
        self.assertEqual(3, value)
        value = Options({'value': 5}).as_str('value')
        self.assertTrue(isinstance(value, str))
        self.assertEqual('5', value)
        value = Options({'value': '5'}).as_str('abc', default=3)
        self.assertTrue(isinstance(value, str))
        self.assertEqual('3', value)
        for v1, v2 in [(True, True), (False, False), ('y', True), ('n', False), ('YES', True), ('NO', False)]:
            value = Options({'value': v1}).as_bool('value')
            self.assertTrue(isinstance(value, bool))
            self.assertEqual(v2, value)
        value = Options({'value': 'y'}).as_bool('abc', default='n')
        self.assertTrue(isinstance(value, bool))
        self.assertEqual(False, value)
        value = Options({'value': 3.14}).as_is('value')
        self.assertTrue(isinstance(value, float))
        self.assertEqual(3.14, value)
        value = Options({'value': [1, 2, 3]}).as_is('value')
        self.assertTrue(isinstance(value, list))


if __name__ == '__main__':
    unittest.main()
