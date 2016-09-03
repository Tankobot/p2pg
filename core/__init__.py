"""The core of p2pg."""

import logging
from threading import Lock
from .conf import conf, dump_after


__author__ = 'Michael Bradley <michael@sigm.io>'
__copyright__ = 'GNU General Public License V3'
__copy_link__ = 'https://www.gnu.org/licenses/gpl-3.0.txt'
__website__ = 'https://p2pg.sigm.io/'
__support__ = 'https://p2pg.sigm.io/support/'


info_form = {
    'author': __author__,
    'copyright': __copyright__,
    'copy-link': __copy_link__,
    'website': __website__,
    'support': __support__
}


log = logging.getLogger(__name__)


class StopException(Exception):
    def __init__(self, reason):
        super().__init__()
        log.info('stop exception raised because of %s', reason)
        self.reason = reason


class StateTracker:
    def __init__(self, n_state):
        self._val = n_state
        self._lock = Lock()

    def __call__(self, *value):
        with self._lock:
            if value:
                self._val = value[0]
            else:
                return self._val


# variable meant to be changed by main as signal to threads
STARTING = object()
RUNNING = object()
STOPPING = object()
state = StateTracker(None)
