from core.client import Menu, Func
from sys import exit

from .options import options


home = Menu('Home')


def holder():
    """Placeholder function."""


# Home Menu
def play():
    pass  # start game
home.add_func('Play', play)
options = home.add_menu(options)
home.add_func('Quit', Func(exit, 0))
