"""Start p2pg."""

import logging
import threading
from core import client, StopException, conf, state
from core import STARTING, RUNNING, STOPPING
from menus import start


__author__ = 'Michael Bradley <michael@sigm.io>'
__copyright__ = 'GNU General Public License V3'
__copy_link__ = 'https://www.gnu.org/licenses/gpl-3.0.txt'
__version__ = (0, 1, 0)


# signify to threads startup phase
state(STARTING)


# record all logs
logging.root.setLevel(logging.DEBUG)


# store log
try:
    log_file = open('general.log', 'a')
except FileNotFoundError:
    log_file = open('general.log', 'w')
r_handler = logging.StreamHandler(log_file)
r_handler.setFormatter(logging.Formatter('%(asctime)s: %(name)s - %(levelname)s - %(message)s'))
logging.root.addHandler(r_handler)


logging.root.info('starting up p2pg')


def close():
    """Ensure that threads have config available."""
    state(STOPPING)
    for th in threading.enumerate():
        assert isinstance(th, threading.Thread)
        if th is not threading.main_thread():
            print('Shutting down %s thread...' % th.name)
            th.join()
    conf.close()
    log_file.close()


action = start
# signify normal running phase
state(RUNNING)
try:
    while True:
        result = action()
        if isinstance(result, client.Menu):
            action = result
        elif callable(result):
            result()
        else:
            raise client.Error('invalid menu %s returned %r' % (action.name, result))
except StopException:
    logging.info('p2pg shutdown successfully')
    close()
except (Exception, KeyboardInterrupt) as e:
    logging.critical('p2pg shutdown with %r', e)
    close()
    raise
