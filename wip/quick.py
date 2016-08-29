"""Use pickle to quickly store and load nodes."""

import pickle
from io import BufferedIOBase
from timeit import timeit


# provide ability to change default protocol
default_protocol = pickle.HIGHEST_PROTOCOL


class Error(Exception):
    pass


class Quick:
    def __init__(self, file: BufferedIOBase,
                 src: dict = None,
                 protocol=default_protocol):
        self.file = file
        self.src = src or {}
        self.protocol = protocol
        self.changed = False

    def __getitem__(self, key):
        return self.src[key]

    def __setitem__(self, key, value):
        assert isinstance(key, bytes)
        assert isinstance(value, bytes)
        self.src[key] = value
        self.changed = True

    def dump(self):
        self.file.seek(0)
        pickle.dump(self.src, self.file, protocol=self.protocol)
        self.changed = False

    def load(self):
        if self.changed:
            raise Error('cannot load with changes')
        else:
            try:
                self.file.seek(0)
                pickle.load(self.file)
            except EOFError:
                self.src = {}
                self.changed = True

    def close(self):
        self.file.close()

    @property
    def time(self):
        d_speed = timeit('self.dump()', number=1, globals=locals())
        l_speed = timeit('self.load()', number=1, globals=locals())
        return d_speed, l_speed


class Priority:
    pass


class _Dict(dict):
    pass
