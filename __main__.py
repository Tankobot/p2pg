from menus import start


__author__ = 'Michael Bradley <michael@sigm.io>'
__copyright__ = 'GNU General Public License V3'


menu = start.prompt()
while True:
    if menu:
        menu.prompt()
    else:
        break
