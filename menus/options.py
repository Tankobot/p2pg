"""Option menu."""

from core.client import Menu


options = Menu('Options')
client = options.add_menu('Client')
server = options.add_menu('Server')
