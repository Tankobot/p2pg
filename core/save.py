"""Module of Save class and utilities."""

from abc import ABCMeta, abstractmethod
from pathlib import Path
from threading import Lock
from collections import namedtuple


Info = namedtuple('Info', 'offset key_size converter')


class Error(Exception):
    pass


class FixedMeta(ABCMeta):
    def __new__(mcs, *args, s_type=NotImplemented):
        cls = super().__new__(mcs, *args)
        if s_type is not NotImplemented:
            mcs._supported_types[s_type] = cls
        return cls

    def __init__(cls, *args, **kwargs):
        del kwargs
        super().__init__(*args)

    @classmethod
    def get_converter(mcs, s_type, size: int, *args, **kwargs):
        try:
            return mcs._supported_types[s_type](size, *args, **kwargs)
        except KeyError:
            raise TypeError('%r does not have a converter' % s_type)

    _supported_types = {}


class ConverterBase(metaclass=FixedMeta):
    def __init__(self, size: int):
        self._size = size

    @abstractmethod
    def to_bytes(self, obj) -> bytes:
        """Convert object to bytes."""

    @abstractmethod
    def from_bytes(self, b):
        """Convert bytes to correct object."""


class BytesConverter(ConverterBase, s_type=bytes):
    def to_bytes(self, obj) -> bytes:
        return obj

    def from_bytes(self, b):
        return b


class Save:
    """Store objects in static length sections.

    Save objects efficiently partition storage for fixed key_size objects.

    Example:
        >>> s = Save('example')
        >>> s.register('key', 4)(b'byte')
        >>> s['key']  # b'byte'
        >>> s['key'] = b'4chr'
        >>> s['key']  # b'4chr'
        >>> s.close()

    Supported dictionary methods include:
        __getitem__
        __setitem__

    """

    def __init__(self, name: str, flag='r+b'):
        """Initialize a Save object.

        The name argument will automatically be preceded by the `home` module variable. It will also automatically be
        followed by the file extension '.sve'.

        :param name: the name of the file to save to
        :param flag: the flags to use when opening the file (see `open`)

        """
        path = Path(name)
        path = path.with_suffix('.sve')
        if not path.exists():
            self._existed = False
            file = path.open('w')
            file.close()
        else:
            self._existed = True
        self._path = path
        self._flag = flag
        self._file = path.open(flag, buffering=0)
        self._is_closed = False

        # set current offset for registering
        self._offset = 0
        self._binding = {}
        self._cache = {}

        # implement thread safe locking
        self._lock = Lock()

    def register(self, name: str, size: int, s_type=bytes, *args, **kwargs):
        """Register section.

        Sections are limited to one type and require a converter to function correctly.

        :param name: name of the section (dictionary key)
        :param size: key_size in bytes of the section
        :param s_type: object type to store in the section
        :param args: extra args to pass to the converter
        :param kwargs: extra kwargs to pass to the converter

        """

        converter = FixedMeta.get_converter(s_type, size, *args, **kwargs)
        self._binding[name] = Info(self._offset,
                                   size,
                                   converter)
        if not self._existed:
            self._file.seek(self._offset)
            self._file.write(bytes(size))
        self._offset += size

        def hook(default):
            self.default(name, default)
        return hook

    @property
    def binding(self):
        return self._binding.copy()

    @binding.setter
    def binding(self, bind: dict):
        self._binding = bind.copy()

    def info(self, key):
        return self._binding[key]

    def __getitem__(self, key):
        try:
            info = self._binding[key]
        except KeyError:
            raise Error('no binding for key %r' % key) from None
        try:
            return self._cache[key]
        except KeyError:
            self._file.seek(info.offset)
            data = self._file.read(info.size)
            obj = info.converter.from_bytes(data)
            self._cache[key] = obj
            return obj

    def __setitem__(self, key, obj):
        try:
            info = self._binding[key]
        except KeyError:
            raise Error('no binding for key %r' % key) from None
        data = info.converter.to_bytes(obj)

        if len(data) != info.size:
            raise Error('data key_size != %s' % info.size)
        self._file.seek(info.offset)
        self._file.write(data)
        self._cache[key] = obj

    def default(self, key, obj):
        if not self._existed:
            self[key] = obj

    def __enter__(self):
        """Enable with syntax for save.

        The with syntax also enables thread-safe use.

        Example:
            >>> s = Save('example')
            >>> s.register('key', 4)(b'byte')
            >>> with s:
            >>>     s  # <Save at 0x_>
            >>>     s['key']  # b'byte'
            >>>     s['key'] = b'bits'
            >>> s  # <closed Save at 0x_>

        """

        self._lock.acquire()
        self.open()
        return self

    def __exit__(self, *args):
        del args
        self.close()
        self._lock.release()

    def open(self):
        if self.is_closed:
            self._file = self._path.open(self._flag, buffering=0)

    def close(self):
        self._file.close()
        self._is_closed = True

    @property
    def is_closed(self):
        return self._is_closed

    def __repr__(self):
        info = (self.__class__.__name__, hex(id(self)))
        if self.is_closed:
            return '<closed %s at %s>' % info
        else:
            return '<%s at %s>' % info


class IntConverter(ConverterBase, s_type=int):
    def __init__(self, size: int, endian='little', *, signed=False):
        super().__init__(size)
        self._endian = endian
        self._signed = signed

    def to_bytes(self, obj) -> bytes:
        if not isinstance(obj, int):
            raise TypeError('%r is not an int' % obj)
        return obj.to_bytes(self._size, self._endian, signed=self._signed)

    def from_bytes(self, b):
        return int.from_bytes(b, self._endian, signed=self._signed)


class StrConverter(ConverterBase, s_type=str):
    def __init__(self, size: int, encoding='utf-8', errors='strict'):
        super().__init__(size)
        self._encoding = encoding
        self._errors = errors

    def to_bytes(self, obj) -> bytes:
        if not isinstance(obj, str):
            raise TypeError('%r is not a str' % obj)
        if len(obj) > self._size:
            raise ValueError('len(str) must be < %s' % self._size)
        return obj.encode(self._encoding, self._errors) + bytes(self._size - len(obj))

    def from_bytes(self, b):
        return b.rstrip(b'\x00').decode(self._encoding, self._errors)
