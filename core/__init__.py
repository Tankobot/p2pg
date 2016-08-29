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
    'terminal_width': 40,  # client terminal width
    'bandwidth_KB': -1,  # total bandwidth to use at one time
    'network_MB': -1,  # total bandwidth to use per day
    'disk_MB': -1,  # soft disk space limit for nodes
    'story_path': [],  # game progress
    'clear_menu': True,  # clear the screen after menu actions
    'clear_len': 50,  # number of lines to scroll down for clear
    'menu_name_char': '-',  # character to print under menu names
})


def close():
    conf.close()
