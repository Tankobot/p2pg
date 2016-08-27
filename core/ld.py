"""Easy data storage options."""

from logging import getLogger
from io import RawIOBase, TextIOWrapper
from threading import Lock
import json
from pathlib import Path


__author__ = 'Michael Bradley <michael@sigm.io>'
__copyright__ = 'GNU General Public License V3'


log = getLogger(__name__)


class Error(Exception):
    pass


class AttrDict:
    def __init__(self, d: dict = None):
        self._hidden_dict = d or {}

    @property
    def hidden_dictionary(self):
        return self._hidden_dict

    def __getattr__(self, key):
        try:
            return self._hidden_dict[key]
        except KeyError:
            return vars(self)[key]

    def __setattr__(self, key, value):
        s = key.startswith('_hidden') if isinstance(key, str) else False
        if s:
            vars(self)[key] = value
        else:
            self._hidden_dict[key] = value

    def __dir__(self):
        return list(set(super().__dir__()) | set(self._hidden_dict))


class JSONDict:
    def __init__(self, file: TextIOWrapper, d: dict = None):
        self._d = d or {}
        self._file = file

    @property
    def dict(self):
        return self._d

    def dump(self):
        self._file.seek(0)
        self._file.truncate()
        json.dump(self._d, self._file, indent=4, sort_keys=True)

    def load(self):
        self._d.clear()
        self._file.seek(0)
        self._d.update(json.load(self._file))

    def default_update(self):
        self._file.seek(0)
        self._d.update(json.load(self._file))


class EasyConfig:
    def __init__(self, name='conf.json', defaults: dict = None):
        if not Path(name).exists():
            with Path(name).open('w') as file:
                json.dump({}, file)
        self._file = open(name, 'r+')
        self._json = JSONDict(self._file, defaults)
        self._attr = AttrDict(self._json.dict)
        if defaults:
            self._json.default_update()
            self.dump()

    @property
    def keys(self):
        return self._attr

    def dump(self):
        self._json.dump()
        self._file.flush()

    def load(self):
        return self._json.load()

    def close(self):
        self._file.close()


class LoaderError(Error):
    pass


class LinearDict:
    """Convert and save dictionary to file."""

    def __init__(self, file: RawIOBase, d: dict = None):
        self._file = file
        self._d = d or {}
        self._lock = Lock()

    @property
    def d(self):
        log.warning('unprotected access to linear dictionary source')
        return self._d

    def __getattr__(self, attr):
        bad = object()
        result = getattr(self, attr, bad)
        if result is bad:
            result = getattr(self._d, attr, bad)

        if result is bad:
            raise AttributeError('linear dictionary does not support %s' % attr)
        else:
            return result

    def __dir__(self):
        return list(set(super().__dir__()) | set(dir(self._d)))

    def __getitem__(self, key) -> bytes:
        with self._lock:
            return self._d[key]

    def __setitem__(self, key, value):
        with self._lock:
            if not (isinstance(key, bytes) and isinstance(value, bytes)):
                raise TypeError('linear dictionary only supports bytes')
            if len(key) >= 2**(2*8):
                raise ValueError('key cannot be larger than sixty-four kilobytes')
            if len(value) >= 2**(4*8):
                raise ValueError('value cannot be larger than four gigabytes')
            self._d[key] = value

    def dump(self):
        for _ in self.iter_dump():
            pass

    def visual_dump(self, name='Dumping LD'):
        progress(self.iter_dump(), self.get_length(), name)

    def iter_dump(self):
        self._file.seek(0)
        self._file.truncate()
        i = 0
        with self._lock:
            # dump dictionary length
            self._file.write(len(self._d).to_bytes(8, 'little'))
            for k, v in self._d.items():
                i += 1
                # dump key
                self._file.write(len(k).to_bytes(2, 'little'))
                self._file.write(k)
                # dump value
                self._file.write(len(v).to_bytes(4, 'little'))
                self._file.write(v)
                # return progress
                log.debug('linear dumped {0}:{1}'.format(k[:4], v[:4]))
                yield i
        log.info('finished dumping %r' % self)

    def load(self):
        for _ in self.iter_load():
            pass

    def visual_load(self, name='Loading LD'):
        progress(self.iter_load(), self.get_length(), name)

    def iter_load(self):
        # prepare read location
        self.get_length()
        self._d.clear()
        i = 0
        while True:
            i += 1
            # check for end of file
            tmp = self._file.read(2)
            if not tmp:
                raise StopIteration
            # load key
            k_len = int.from_bytes(tmp, 'little')
            k = self._file.read(k_len)
            if len(k) != k_len:
                log.warning('performed partial load')
                raise LoaderError('unable to read key %s' % k)
            # load value
            v_len = int.from_bytes(self._file.read(4), 'little')
            v = self._file.read(v_len)
            if len(v) != v_len:
                log.warning('performed partial load')
                raise LoaderError('unable to read value for %s' % k)
            # set value into key
            self._d[k] = v
            # return progress
            log.debug('linear loaded {0}:{1}'.format(k[:4], v[:4]))
            yield i
        log.info('finished loading %r' % self)

    def get_length(self):
        self._file.seek(0)
        r = self._file.read(8)
        if r and not len(self._d):
            return int.from_bytes(r, 'little')
        else:
            return len(self._d)


def fill_percent(n: float, precision: int, fill=' '):
    l = precision + 4
    n *= 100
    i, d = divmod(n, 1)
    i = str(int(i))
    d = str(d)[2:precision+2]
    result = fill*(l - precision - 1 - len(i)) + i + '.' + d
    result += '0'*(precision - len(d))
    return result


def progress(iterable, total: int, info='Dictionary', form='{info} {pro}%', precision=4):
    info += ' '
    for p in iterable:
        percentage = p / total
        print(form.format(info=info, pro=fill_percent(percentage, precision)), end='\r')
    print()


def random_dictionary(entries: int, key_size: int, value_size: int):
    from os import urandom
    d = {}
    for i in range(entries):
        d[urandom(key_size)] = urandom(value_size)
    return d
