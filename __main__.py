import core


__author__ = 'Michael Bradley <michael@sigm.io>'
__copyright__ = 'GNU General Public License V3'


menu_items = [
    'Main Menu',
    ['Start', leave],
    ['Help', ],
    [
        'Options',
        [
            'client',
            ['change terminal width', menus.primary.change_terminal_width]
        ]
    ],
    ['Exit', leave]
]


main_menu = core.Menu(menu_items)
main_menu.prompt()
