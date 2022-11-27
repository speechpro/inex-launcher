from random import randint


class Chunker:
    def __init__(self, left_context, window_length, right_context):
        self.left_context = int(left_context)
        self.window_length = int(window_length)
        self.right_context = int(right_context)

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
