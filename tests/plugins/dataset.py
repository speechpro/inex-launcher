import logging
from random import randint
from inex.utils.configure import get_as_is, get_as_int


class Dataset:
    def __init__(self, config):
        logging.info(f'Creating dataset from config\n{config}')
        self.frame_length = get_as_int(config, 'frame_length', required=True)
        self.frame_shift = get_as_int(config, 'frame_shift', required=True)
        self.feature_dim = get_as_int(config, 'feature_dim', required=True)
        self.left_context = get_as_int(config, 'left_context', required=True)
        self.window_length = get_as_int(config, 'window_length', required=True)
        self.right_context = get_as_int(config, 'right_context', required=True)
        self.features = get_as_is(config, 'features', required=True)
        self.chunker = get_as_is(config, 'chunker', required=True)
        self.num_chunks = get_as_int(config, 'num_chunks', required=True)

    def run(self):
        chunk_size = self.left_context + self.window_length + self.right_context
        min_len = (chunk_size - 1) * self.frame_shift + self.frame_length
        data = list()
        for _ in range(self.num_chunks):
            features = self.features(min_len + self.frame_shift * randint(10, 100))
            assert features.shape[1] == self.feature_dim
            chunk = self.chunker(features)
            assert chunk.shape[0] == chunk_size
            data.append(chunk)
        return data


def create(config):
    return Dataset(config)
