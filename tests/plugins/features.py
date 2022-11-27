import logging
import numpy as np
from mkernel.utils.configure import get_as_int


class Extractor:
    def __init__(self, config):
        logging.info(f'Creating features extractor from config\n{config}')
        self.frequency = get_as_int(config, 'frequency', required=True)
        self.frame_length = get_as_int(config, 'frame_length', required=True)
        self.frame_shift = get_as_int(config, 'frame_shift', required=True)
        self.feature_dim = get_as_int(config, 'feature_dim', required=True)

    def get(self, key):
        if key == 'frequency':
            return self.frequency
        elif key == 'frame_length':
            return self.frame_length
        elif key == 'frame_shift':
            return self.frame_shift
        elif key == 'feature_dim':
            return self.feature_dim
        elif key == 'get_num_frames':
            return self.get_num_frames
        else:
            return None

    def get_num_frames(self, lengths):
        return (lengths - self.frame_length) // self.frame_shift + 1

    def __call__(self, lengths):
        num_frames = self.get_num_frames(lengths)
        return np.random.rand(num_frames, self.feature_dim).astype(dtype=np.float32)


def create(config):
    return Extractor(config)
