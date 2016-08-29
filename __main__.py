"""Start p2pg."""

from core import client, stop
from menus import start


__author__ = 'Michael Bradley <michael@sigm.io>'
__copyright__ = 'GNU General Public License V3'


action = start
try:
    while True:
        result = action()
        if isinstance(result, client.Menu):
            action = result
        elif callable(result):
            result()
        else:
            raise client.Error('invalid menu return')
finally:
    stop()
