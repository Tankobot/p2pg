"""Home to choose play modes and options."""

from core.client import Menu, form_doc
from core import StopException
from .options import options


home = Menu('Home', doc="""Welcome to p2pg!

This is the home menu. From here you can choose whether to play the game or configure options.

""")


home.add_func('Play')  # TODO build play mode
home.add_menu(options)


def reset():
    print('Run reset script. ($ python reset.py)')
    raise StopException('reset from menu')
home.add_func('Reset', reset)


def menu_stop():
    raise StopException('quit menu button')
home.add_func('Quit', menu_stop)


def info():
    print(form_doc("""P2PG Game Information

    Author: %(author)s
    Copyright: %(copyright)s
    Link to License: %(copy-link)s
    Website: %(website)s
    Support: %(support)s

    """))
    input('Press enter to continue.')
home.add_func('Info', info)
