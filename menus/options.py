"""Option menu.

Generally control the information in the config file.

"""

from core.client import Menu


options = Menu('Options')
client = options.add_menu('Client')
server = options.add_menu('Server')
