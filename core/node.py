from hashlib import sha256
from io import RawIOBase, BufferedIOBase, BytesIO
from core.ld import LinearDict


__author__ = 'Michael Bradley <michael@sigm.io>'
__copyright__ = 'GNU General Public License V3'


class Error(Exception):
    pass


# flags
BASE = b'b'
CHILD = b'c'


class NodeError(Error):
    pass


class DecodeError(NodeError):
    pass


class Node:
    """Store story information for data movement."""

    def __init__(self, msg: str, parent: bytes = None):
        """Initialize node object."""

        if len(parent) != 32:
            raise ValueError('incorrect parent signature')

        self._msg = msg.encode('utf-8')
        if len(self._msg) <= 2**16:
            self._len = len(self._msg).to_bytes(2, 'little')
        else:
            raise ValueError('node message too long')
        self._parent = parent

        if parent:
            self._flag = CHILD
        else:
            self._flag = BASE
            self._parent = bytes(32)

        self._sha = sha256(self._flag +
                           self._parent +
                           self._len +
                           self._msg).digest()

        self._cache = None

    @property
    def msg(self) -> bytes:
        return self._msg

    @property
    def parent(self) -> bytes:
        return self._parent if self._flag == CHILD else None

    @property
    def sha(self) -> bytes:
        return self._sha

    @property
    def flag(self) -> bytes:
        return self._flag

    def to_bytes(self) -> bytes:
        if self._cache:
            return self._cache
        else:
            result = bytearray()

            result.extend(self._flag)
            result.extend(self._parent)
            result.extend(self._len)
            result.extend(self._msg)
            result.extend(self._sha)

            self._cache = bytes(result)
            return self._cache

    @classmethod
    def from_bytes(cls, stream):
        if not isinstance(stream, (RawIOBase, BufferedIOBase)):
            stream = BytesIO(stream)

        flag = stream.read(1)
        if flag == BASE:
            stream.read(32)
            parent = None
        elif flag == CHILD:
            parent = stream.read(32)
        else:
            raise DecodeError('invalid flag %r' % flag)

        length = int.from_bytes(stream.read(2), 'little')
        if length > 2**16:
            raise DecodeError('message size too large')
        msg = stream.read(length)

        sha = stream.read(32)
        if sha256(flag + parent + length + msg).digest() != sha:
            raise DecodeError('incorrect hash')

        return cls(msg, parent)


class LinkageError(Error):
    pass


class Tree:
    def __init__(self, node: Node):
        if node.flag != BASE:
            raise TypeError('cannot start tree from non-base node')
        self._nodes = {node.sha: node}

    @property
    def nodes(self):
        return self._nodes

    def __contains__(self, node):
        return node.sha in self._nodes

    def __iter__(self):
        return iter(self._nodes)

    def link(self, node: Node):
        if node.parent in self._nodes:
            self._nodes[node.sha] = node
        else:
            raise LinkageError('parent node not in tree')

    def unlink(self, node: Node):
        del self._nodes[node.sha]

    def retrace(self, node: Node):
        while True:
            parent = self._nodes[node.sha].parent
            if parent:
                try:
                    node = self._nodes[parent]
                except KeyError:
                    raise LinkageError(
                        'attempt to retrace broken node tree'
                    ) from None
                yield node
            else:
                break

    def bind_ld(self, file):
        return LinearDict(file, ByteDict(self))


class ByteDict(dict):
    def __init__(self, tree: Tree):
        super().__init__()
        self._nodes = tree.nodes

    def clear(self):
        self._nodes.clear()

    def __getitem__(self, key):
        return self._nodes[key].to_bytes()

    def __setitem__(self, key, value):
        self._nodes[key] = Node.from_bytes(value)

    def __iter__(self):
        return iter(self._nodes)

    def items(self):
        for key in self:
            yield key, self[key]
