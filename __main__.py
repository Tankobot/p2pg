import core
import menus
from sys import exit as leave


menu_items = [
    'Main Menu',
    [
        'Options',
        ['client', ]
    ],
    ['Exit', leave]
]


menu = core.Menu(menu_items)
menu.prompt()
