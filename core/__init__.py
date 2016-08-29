"""The core of p2pg."""

import logging
from sys import exit
from .node import Node
from .node import NodeError
from .ld import LinearDict
from .conf import conf


# hide only the most crucial logs
logging.root.setLevel(logging.INFO)


# store log
try:
    log_file = open('general.log', 'a')
except FileNotFoundError:
    log_file = open('general.log', 'w')
logging.root.addHandler(logging.StreamHandler(log_file))


__author__ = 'Michael Bradley <michael@sigm.io>'
__copyright__ = 'GNU General Public License V3'


def stop():
    """Run code to cleanup game before shutdown."""

    exit(0)
