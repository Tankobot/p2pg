from hashlib import sha256
from io import BufferedIOBase
from math import log2


class KeyMap:
    """Quickly generate position of data.

    `KeyMap`s are not meant to be used on their own. They are instead meant to be paired with a `Database`.

    """

    def __init__(self, size: int, block=1):
        assert size <= 2**256, 'size too large'
        self._size = size
        self._mod = 2**256 // size
        self._max = self._mod * size
        self._byte = int(log2(size)//8) + 1
        self._block = block
        self.extra = None

    @property
    def size(self) -> int:
        return self._size

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__,
                               self._size,
                               self._block)

    @property
    def speed(self) -> float:
        return 1/(1 - (2**256 % self._size)/2**256)

    def __getitem__(self, key: bytes):
        """Generate bucket position.

        Getitem assumes that the key is already uniformly distributed.

        """

        assert isinstance(key, bytes), 'KeyMap only supports bytes'
        h = sha256()

        extra = 0

        def redo(new_key):
            h.update(new_key)
            new_key = h.digest()
            return int.from_bytes(new_key, 'little'), new_key

        i, key = redo(key)
        extra += 1
        while i >= self._max:
            i, key = redo(key)
            extra += 1
        i %= self._size
        self.extra = extra

        return i * self._block

    def increase(self, portion: float):
        return self.__class__(round(self._size * portion), self._block)


def db_open(name: str, size: int, mode='r+b', block=512):
    assert 'b' in mode, 'db must be opened in binary mode'

    # setup file
    file = open(name, mode)
    file.seek(size - 1)
    file.write(b'\0')

    # determine correct block size
    key_size = int(log2(size)//1) + 1

    # generate key map
    keys = KeyMap(key_size, block)


class DBError(Exception):
    pass


class ExpansionError(DBError):
    pass


class SparseDatabase:
    def __init__(self, file_obj: BufferedIOBase,
                 key_map: KeyMap,
                 init=False, *,
                 portion=3/4):
        self.file = file_obj
        self.maps = [key_map]
        self._portion = portion

        # set the first and last pointers
        file_obj.seek(0)
        if init:
            # empty pointers
            self._first = None
            self._last = None
            # start fill tracking
            self._filled = 0
        else:
            # read pointers
            self._first = int.from_bytes(file_obj.read(32), 'little')
            self._last = int.from_bytes(file_obj.read(32), 'little')
            # get current fill
            self._filled = int.from_bytes(file_obj.read(32), 'little')
        # add offset for pointers
        self._pos = 64

        # initialize key cache
        self._keys = {}

        # track if currently expanding db
        self._expansion = None

        # set up iterable variable
        self._current = None

    def __iter__(self):
        self._current = self._first
        return self

    def __next__(self):
        self._seek(self._current + 32)
        self._current = int.from_bytes(self.file.read(32), 'little')

    def clear_cache(self):
        """Reset the tracked keys."""
        self._keys = {}

    def expand(self, portion: int):
        """Expand the size of the database and start remapping."""

        if self._expansion:
            raise ExpansionError('attempt to expand expanding database')
        self.maps.append(self.maps[-1].increase(portion))
        self._expansion = self._first

    @property
    def expanding(self):
        return self._expansion

    def _seek(self, pos: int):
        self.file.seek(self._pos + pos)

    def __getitem__(self, item):
        """Retrieve item from the database file."""

    def __setitem__(self, key, value):
        """Put item into the database file."""

    def close(self):
        if self._expansion is not None:
            raise ExpansionError('attempt to close expanding database')
        self.file.close()


class _Object:
    def __init__(self, key: bytes, n_key: bytes, data: bytes = None):
        self.key = key
        self.n_key = n_key
        self.data = data

    key_size = 32

    @classmethod
    def read_object(cls, file: BufferedIOBase):
        new_key = file.read(cls.key_size)

        obj_size = file.read(cls.key_size)
        obj_size = int.from_bytes(obj_size, 'little')

        new_data = file.read(obj_size)

        return cls(new_key, new_data)

    def byte_object(self, file: BufferedIOBase):
        file.write(self.key)
        file.write(len(self.data).to_bytes(len(self.key), 'little'))
        file.write(self.data)
