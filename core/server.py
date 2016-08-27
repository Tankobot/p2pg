from sys import exit as end_program
import threading
from core.node import Node
from pathlib import PurePath


try:
    from dbm import open as dbm_open
except ImportError:
    dbm_open = object
    print('GNU Database Manager not installed.')
    print('Please install Gnu DBM for Python3.')
    print('Exiting...')
    end_program()


class ServerError(Exception):
    pass


class NodeHandler:
    def __init__(self, node_path: PurePath):
        self.database = dbm_open(str(node_path), 'c')
        self.cache = {}
        self.lock = threading.Lock()

    def load(self, location: bytes):
        node = Node.from_bytes(self.database[location])
        self.cache[location] = node

    def unload(self, location: bytes):
        del self.cache[location]

    def add(self, node: Node):
        """Add a node to the current database."""
        save = node.to_bytes()
        self.database[node.sha()] = save
        self.cache[node.sha()] = node

    def remove(self, location: bytes):
        try:
            self.unload(location)
        except IndexError:
            pass
        del self.database[location]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        try:
            pass
        finally:
            self.database.close()
