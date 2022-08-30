import logging
from random import randint
from mkernel.utils.configure import get_as_int


class Chunker:
    def __init__(self, config):
        super().__init__()
        logging.info(f'Creating chunker from config\n{config}')
        self.left_context = get_as_int(config, 'left_context', required=True)
        self.window_length = get_as_int(config, 'window_length', required=True)
        self.right_context = get_as_int(config, 'right_context', required=True)

    def get(self, key):
        if key == 'left_context':
            return self.left_context
        elif key == 'window_length':
            return self.window_length
        elif key == 'right_context':
            return self.right_context
        else:
            return None

    def __call__(self, features):
        length = len(features)
        width = self.left_context + self.window_length + self.right_context
        shift = randint(0, length - width)
        feats_chunk = features[shift: shift + width]
        return feats_chunk


def create(config):
    return Chunker(config)
