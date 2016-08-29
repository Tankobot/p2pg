"""Home to choose play modes and options."""

from core import stop
from core.client import Menu

from .options import options


home = Menu('Home')


home.add_func('Play')
options = home.add_menu(options)
home.add_func('Quit', stop)
