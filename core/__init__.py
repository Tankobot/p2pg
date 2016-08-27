import core.node
from .node import Node
from .node import NodeError

import core.server
from .server import NodeHandler

import core.client
from .client import Controller
from .client import Menu

import core.ld
from .ld import LinearDict
from .ld import EasyConfig


__author__ = 'Michael Bradley <michael@sigm.io>'
__copyright__ = 'GNU General Public License V3'


conf = EasyConfig(defaults={
    'terminal_width': 40,
    'bandwidth_KB': -1,
    'network_MB': -1,
    'disk_MB': -1,
    'story_path': [],
})


def close():
    conf.close()
