from copy import deepcopy
from mkernel.utils.convert import str_to_bool


class Options:
    def __init__(self, data=None):
        self.data = dict() if data is None else deepcopy(data)

    def resolve(self, data=None, root=None):
        if data is None:
            data = self.data
            root = None
        for key, value in data.items():
            if isinstance(value, str) and value.startswith('<<'):
                path = key if root is None else root + '.' + key
                value = self.__getitem__(path)
                data[key] = value
            if isinstance(value, dict):
                path = key if root is None else root + '.' + key
                self.resolve(value, path)

    def as_is(self, path, default=None, required=False):
        if self.__contains__(path):
            return self.__getitem__(path)
        else:
            assert not required, f'Failed to find "{path}" in config\n{self.data}'
            return default

    def as_bool(self, path, default=False, required=False):
        value = self.as_is(path, default, required)
        if isinstance(value, str):
            return str_to_bool(value)
        else:
            return bool(value)

    def as_type(self, path, dtype, default, required):
        return dtype(self.as_is(path, default, required))

    def as_str(self, path, default=None, required=False):
        return self.as_type(path, str, default, required)

    def as_int(self, path, default=None, required=False):
        return self.as_type(path, int, default, required)

    def as_float(self, path, default=None, required=False):
        return self.as_type(path, float, default, required)

    def __setitem__(self, path, item):
        assert path is not None, 'Path is None in Options.__setitem__()'
        assert isinstance(path, str), f'Parameter "path" ({path}) must be a string in Options.__setitem__()'
        keys = path.split('.')
        if len(keys) == 1:
            self.data[path] = item
        else:
            data = self.data
            for key in keys[: -1]:
                assert isinstance(data, dict), f'Failed to follow by path "{path}" in Options.__setitem__()'
                if key not in data:
                    data[key] = dict()
                data = data[key]
            assert isinstance(data, dict), f'Failed to follow by path "{path}" in Options.__setitem__()'
            data[keys[-1]] = item

    def __getitem__(self, path):
        assert path is not None, 'Path is None in Options.__getitem__()'
        assert isinstance(path, str), f'Parameter "path" ({path}) must be a string in Options.__getitem__()'
        keys = path.split('.')
        if len(keys) == 1:
            value = self.data[path] if path in self.data else None
        else:
            value = self.data
            for key in keys:
                if not isinstance(value, dict) or (key not in value):
                    return None
                value = value[key]
        if isinstance(value, str) and value.startswith('<<'):
            path = value[2:].strip()
            assert self.__contains__(path), f'The key "{path}" does not exist in config:\n{self.data}'
            value = self.__getitem__(path)
        return value

    def __contains__(self, path):
        assert path is not None, 'Path is None in Options.__getitem__()'
        assert isinstance(path, str), f'Parameter "path" ({path}) must be a string in Options.__getitem__()'
        keys = path.split('.')
        if len(keys) == 1:
            return path in self.data
        else:
            data = self.data
            for key in keys:
                if not isinstance(data, dict) or (key not in data):
                    return False
                data = data[key]
            return data is not None

    def __delitem__(self, path):
        assert path is not None, 'Path is None in Options.__delitem__()'
        assert isinstance(path, str), f'Parameter "path" ({path}) must be a string in Options.__delitem__()'
        keys = path.split('.')
        if len(keys) == 1:
            if path in self.data:
                del self.data[path]
        else:
            data = self.data
            for key in keys[: -1]:
                assert isinstance(data, dict), f'Failed to follow by path "{path}" in Options.__delitem__()'
                if key not in data:
                    data[key] = dict()
                data = data[key]
            assert isinstance(data, dict), f'Failed to follow by path "{path}" in Options.__delitem__()'
            key = keys[-1]
            if key in data:
                del data[key]

    def __repr__(self):
        return self.data.__repr__()

    def __str__(self):
        return self.data.__str__()
