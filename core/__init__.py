import core.nodes
from .nodes import Node
from .nodes import NodeError

import core.server
from .server import NodeHandler

import core.client
from .client import Controller
from .client import Menu

from core.save import Save


conf = Save('conf')
conf.register('terminal_length', 1, int)(40)
conf.register('bandwidth_KB', 4, int)(0)
conf.register('network_MB', 4, int)(0)
conf.register('disk_MB', 8, int)(0)
conf.close()
