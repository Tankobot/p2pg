from hashlib import sha256
from zlib import compress, decompress
from core.bbytes import ByteArray


class NodeError(Exception):
    pass


class Partial:
    def __init__(self, obj):
        self.obj = obj
        self.cursor = 0

    def __call__(self, n: int):
        result = self.obj[self.cursor:self.cursor + n]
        self.cursor += n
        return result


class Node:
    def __init__(self, msg='', parent: bytes = None, flags: ByteArray = None):
        """One point on the story path.

        Used for storing the contents of a story branch in memory.

        """

        self._flags = flags or ByteArray(self.flag_length)

        self.msg = msg or ''
        if parent:
            self.parent = parent
        else:
            self.parent = b'\x00' * 32
            self.set_flag('base', True)
        self._encoded = self.msg.encode('utf-8')
        self._comp = compress(self._encoded, 9)
        self._sha = sha256(self._comp + self.parent).digest()
        self._changed = False
        self._protect = False
    _protect = False

    _flags_list = [
        'base',
    ]

    _flags_dict = {k: v for v, k in enumerate(_flags_list)}

    def set_flag(self, fl: str, v):
        self._flags.bit(self._flags_dict[fl], 1 if v else 0)

    def get_flag(self, fl: str):
        return self._flags.bit(self._flags_dict[fl])

    def branch(self, msg=''):
        """Automate the process of appending nodes to the story."""

        self.refresh()
        return self.__class__(msg, self._sha)

    def is_child(self, other):
        if not isinstance(other, self.__class__):
            class_name = self.__class__.__name__
            raise TypeError('parent not %s' % class_name)
        return True if self.parent == other.sha() else False

    def __setattr__(self, key, value):
        super().__setattr__('_changed', True)
        super().__setattr__(key, value)

    def __repr__(self):
        if self.get_flag('base'):
            form = (self.__class__.__name__,
                    self.msg)

            return '%s(%r)' % form
        else:
            form = (self.__class__.__name__,
                    self.msg,
                    self.parent)

            return '%s(%r, %r)' % form

    def __hash__(self):
        return id(self.sha())

    def __eq__(self, other):
        try:
            assert isinstance(other, self.__class__)
            assert self.sha() == other.sha()
            assert self.parent == other.parent
            assert self.msg == other.msg
            assert self._flags == other._flags
            return True
        except AssertionError:
            return False

    def refresh(self):
        if self._changed:
            for line in self.msg.split('\n'):
                self.check_line(line)
            self._encoded = self.msg.encode('utf-8')
            self._comp = compress(self.msg.encode('utf-8'), 9)
            self._sha = sha256(self._comp + self.parent).digest()
        self._changed = False

    def changed(self):
        return self._changed

    line_length = 100
    msg_max = 2
    flag_length = len(_flags_list) // 8 + 1

    def sha(self):
        self.refresh()
        return self._sha

    def check_line(self, line):
        if not isinstance(line, str):
            raise TypeError('line not string')
        if len(line) > self.line_length:
            raise ValueError('line too long')

    def to_bytes(self):
        """Covert to immutable and writeable version."""
        self.refresh()

        result = bytes()

        if len(self._comp) > 2**(8 * self.msg_max) - 1:
            raise NodeError('compressed message too large')
        # add bytes for length of compressed message
        result += len(self._comp).to_bytes(self.msg_max, 'little')
        result += self._comp

        # add parent's hash (32)
        result += self.parent

        # add hash at the end (32)
        result += self._sha

        # add flag byte(s)
        result += self._flags

        return result

    @classmethod
    def from_bytes(cls, packet: bytes):
        """Convert to viewable node."""

        cursor = Partial(packet)

        # read compressed msg
        msg_length = int.from_bytes(cursor(cls.msg_max), 'little')
        msg_comp = cursor(msg_length)

        # read parent's hash
        parent = cursor(32)

        # verify hash
        node_sig = sha256(msg_comp + parent).digest()
        if not node_sig == cursor(32):
            raise NodeError('hash does not match')

        # read flag byte(s)
        flags = ByteArray(cursor(cls.flag_length))

        # decompress msg
        msg = decompress(msg_comp).decode('utf-8')

        return cls(msg, parent, flags)

    @classmethod
    def node_length(cls, maximum=True):
        size = 0
        # msg allocation bytes
        size += cls.msg_max
        # max msg length
        size += 2**(8 * cls.msg_max) - 1 if maximum else 8
        # parent key_size
        size += 32
        # sha key_size
        size += 32
        # flags key_size
        size += cls.flag_length

        return size


class NodePath:
    def __init__(self, *parts, iterable=None):
        self.path = list(parts or iterable)
        self.bag = set(parts or iterable)

    def __repr__(self):
        name = self.__class__.__name__
        return '%s(%s)' % (name, ', '.join(map(repr, self.path)))

    def __contains__(self, item):
        return item in self.bag

    def add(self, key: str):
        self.path.append(key)
        self.bag.add(key)

    def remove(self, n=-1):
        key = self.path.pop(n)
        self.bag.remove(key)
