import threading
import logging
from io import BufferedIOBase
from weakref import ref
from math import isinf
import abc


class AsynchronousCall:
    def __init__(self, target, *args, **kwargs):
        self._lock = threading.Lock()
        self._result = ()
        self._thread = threading.Thread(target=self.catch(target),
                                        args=args,
                                        kwargs=kwargs)
        self._thread.daemon = True
        self._thread.start()

    NotDone = type('NotDoneType', (), {
        '__bool__': lambda self: False,
        '__repr__': lambda self: 'NotDone'
    })()

    def catch(self, target):
        def f(*args, **kwargs):
            result = target(*args, **kwargs)
            with self._lock:
                self._result = result
        return f

    @property
    def daemon(self):
        return self._thread.daemon

    @daemon.setter
    def daemon(self, value):
        self._thread.daemon = value

    def __call__(self):
        if self._thread.is_alive():
            return self.NotDone
        with self._lock:
            return self._result


class DBError(Exception):
    pass


logger = logging.getLogger(__name__)


def db_open(name: str, size: int):
    """Setup a HDDB."""

    # try to open file
    try:
        logger.info('HDDB %s opened', name)
        file = open(name, 'r+b')
    except FileNotFoundError:
        logger.info('HDDB %s created', name)
        file = open(name, 'w+b')
    if not file.seekable():
        logger.critical('HDDB %s is not seekable', name)
        raise DBError('HDDB %s is not seekable' % name)

    # determine best values for step and key size
    pass

    return HighDensityDB


class HighDensityDB:
    """High density database.

    The HDDB is made for storing and retrieving large data.

    """

    def __init__(self, file_obj, step=256, key_size=5):
        assert isinstance(file_obj, BufferedIOBase), 'file_obj must support BufferedIOBase'
        assert key_size*256 % step, 'key_size not divisible by step'

        self.file = file_obj

        self._step = step
        self._jumps = key_size*256 // step
        # default key size enables up to 1TB HDDB
        self._key_size = key_size
        self._status = 1
        self._root = _Index(self, 0)
        self._item = None

    @property
    def size(self):
        self.file.seek(0, 2)
        return self.file.tell()

    @property
    def step(self):
        return self._step

    @property
    def key_size(self):
        return self._key_size

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, x: float):
        assert 0 <= x <= 1, 'status must be in range 0 <= x <= 1'
        self._status = x

    @property
    def speed(self):
        return self._key_size * 8 // self._step

    @property
    def capacity(self):
        return 2**(self._key_size * 8)

    @property
    def index_size(self):
        return self._jumps * self._step * self._key_size

    def mark(self, s: str = None):
        if s is None:
            return sections[int.from_bytes(self.file.read(1), 'little')]
        else:
            self.file.write(r_sections[s])

    @property
    def item(self) -> Section:
        return self._item

    @item.setter
    def item(self, value):
        if self.item is not value:
            self.item.finalize()
            self._item = value

    def load_item(self):
        m = self.mark()
        if m == 'index':
            return _Index(self, self.file.tell())
        elif m == 'data':
            size = self.file.read(self.key_size)
            size = int.from_bytes(size, 'little')
            return _Data(self, self.file.tell(), size)

    def __getitem__(self, key: bytes):
        if len(key) != self.key_size:
            raise ValueError('incorrect key size')
        item = self._root

        for i in key[:-1]:
            pos = item[i]
            if pos:
                self.file.seek(pos)
                item = self.load_item()
            else:
                item[i] = self.size
                item = _Index(self, self.size)

        return item

    def remap(self, name: str, chunk_size=1024):
        return NotImplemented

    def close(self):
        self.file.close()

    def __exit__(self, *args):
        del args
        self.close()


sections = [
    'index',
    'data'
]
r_sections = {v: i for i, v in enumerate(sections)}


class Section(abc.ABC):
    @abc.abstractmethod
    def finalize(self):
        """Set a boundary on the section."""


class _Index(Section):
    """Save location of next sections."""

    def __init__(self, db: HighDensityDB, pos: int):
        """Initialize index handler."""

        self._db = ref(db)
        self._file = ref(db.file)
        self._pos = pos

    def finalize(self):
        pass  # indices are fixed length

    def blank(self):
        self.seek(0)
        self.file.write(b'\0' * self.db.key_size * self.db.step)

    @property
    def db(self) -> HighDensityDB:
        return self._db()

    @property
    def file(self) -> BufferedIOBase:
        return self._file()

    @property
    def size(self):
        return self.db.key_size * self.db.step

    def seek(self, key: int):
        if key > self.db.step:
            raise ValueError('key out of index')
        offset = self.db.key_size * key
        self.file.seek(self._pos + offset)

    def __getitem__(self, key: int):
        self.seek(key)
        next_pos = self.file.read(self.db.key_size)
        next_pos = int.from_bytes(next_pos, 'little')
        if not next_pos:
            raise KeyError('unset index')
        return next_pos

    def __setitem__(self, key: int, value: bytes):
        if len(value) != self.db.key_size:
            raise ValueError('incorrect byte length')
        self.seek(key)
        self.file.write(value)


class _Data(Section):
    """Store extendible data."""

    def __init__(self, db: HighDensityDB, pos: int, limit: int = None):
        """Initialize data handler."""

        self._db = ref(db)
        self._file = ref(db.file)
        self._pos = pos
        self._cursor = pos
        if limit is not None and limit <= self.db.key_size * 2:
            raise ValueError('limit too small')
        self._size = limit or 0
        self._limit = limit or float('inf')
        try:
            self._next = self._find_next()
        except DBError:
            self._next = None

    def finalize(self):
        if isinf(self._limit):
            self._limit = self._size + 2*self.db.key_size
        elif self._next:
            self.next.finalize()

    @property
    def db(self) -> HighDensityDB:
        return self._db()

    @property
    def file(self) -> BufferedIOBase:
        return self._file()

    @property
    def next(self):
        if self._next:
            return self._next
        else:
            self._next = self.extend()
            return self._next

    def _find_next(self):
        # grab pointer
        self.seek(self.limit)
        place = self.file.read(self.db.key_size)
        place = int.from_bytes(place, 'little')

        # handle no pointer
        if not place:
            raise DBError('file does not have extension')

        # ensure the section is type Data
        self.file.seek(place)
        m = self.db.mark()
        if m != 'data':
            raise TypeError('found non data object at next')
        else:
            # set up the next section
            size = int.from_bytes(self.file.read(self.db.key_size), 'little')
            return self.__class__(self.db, place + 1, size)

    @property
    def fragments(self):
        """Calculate length of Data chain."""
        return self._count()

    def _count(self, n=0):
        if self._next:
            return self._count(n + 1)
        else:
            return n

    @property
    def limit(self):
        return self._limit - 2*self.db.key_size

    def tell(self):
        return self._cursor

    def seek(self, offset):
        self._cursor = offset

        if offset < self.limit:
            # prevent over seek extending limited file
            self.file.seek(self._pos + self.db.key_size + offset)
        else:
            # pass extra offset onto the next section
            self.next.seek(offset - self._size)

        # set new data size
        self._size = max(self._size, offset)

    def refresh(self):
        """Reposition the file cursor."""
        self.seek(self.tell())

    def write(self, data: bytes):
        # seek to cursor
        self.refresh()

        # pass data to next section if cursor is too far forward
        if self.tell() >= self.limit:
            return self.next.write(data)

        cut = self.limit - self.tell()
        if len(data) <= cut:
            # write data to current section
            self.file.write(data)
        else:
            # handle too much data for current section
            self.file.write(data[:cut])
            self.next.write(data[cut:])

        # move cursor forward
        self.seek(self.tell() + len(data))

    def read(self, n=0):
        assert n >= 0, 'n cannot be negative'

        # seek to cursor
        self.refresh()

        cut = self._size - self.tell()

        # handle custom read length
        if n:
            if n <= cut:
                # perform read
                return self.file.read(min(n, cut))
            else:
                # attempt to split read
                data = self.file.read(cut)
                if self._next:
                    data += self.next.read(n - cut)
                return data

        # read rest of file
        else:
            if self._next:
                # split read
                return self.file.read(cut) + self.next.read()
            else:
                # perform read
                return self.file.read(self._size - self.tell())

    def extend(self):
        # create pointer to next section
        assert not isinf(self.limit), 'cannot extend infinite limit'
        self.seek(self.limit)
        place = self.db.size.to_bytes(self.db.key_size, 'little')
        self.file.write(place)

        # set up the next section
        self.file.seek(self.db.size)
        self.db.mark('data')
        return self.__class__(self.db, place + 1)

    def close(self):
        # handle extended Data
        if self._next:
            self._next.close()

        # record current section size
        self.seek(-self.db.key_size)
        size = self._size.to_bytes(self.db.key_size, 'little')
        self.file.write(size)


def test_hash(f, c=1000, r=(0, 1), space=False, x=20, y=60):
    """Test hashes for distribution.

    Prints a histogram to the screen.

    """

    step = r[1] / x
    hist = [0 for _ in range(x)]
    for i in range(c):
        e = f(i) % r[1]
        for j in range(x):
            if e <= step*(j + 1):
                hist[j] += 1
                break
    m = r[1] if space else max(hist)
    for i, v in enumerate(hist):
        hist[i] = '-' * round(v / m * y)
    for line in hist:
        assert isinstance(line, str)
        print(line + ' '*(y - len(line)) + '|')


def test_map(key_map: KeyMap, mod: int, space=False):
    def f(x: int):
        return key_map[int.to_bytes(x, key_map.key_size, 'little')] % mod
    test_hash(f, 2**(key_map.key_size * 8), (0, 2**(key_map.key_size * 8)-1), space)
