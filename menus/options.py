"""Option menu.

Generally control the information in the config file.

"""

from core.client import Menu, menu_log
from core import conf, dump_after


options = Menu('Options', doc="""This is the options menu.

From here you can control the configuration of p2pg and how it behaves on your machine.

""")


# client options
client = options.add_menu('Client', doc='Control display options.')


@dump_after
def terminal_width():
    """Control width of terminal.

    The `terminal_width` will control the wrapping mechanism of p2pg.

    Note:
        Certain text may not obey the terminal width.
        * Menu Names
        * Menu Items

        File a bug report if a body of text does not wrap to 40 characters or greater.
        Url: %(support)s

    """

    r = input('New terminal width [%s]: ' % conf.terminal_width)
    try:
        n = int(r)
        conf.terminal_width = n
    except ValueError:
        menu_log.warning('invalid value for terminal width %r', r)
client.add_func('Terminal Width', terminal_width)


@dump_after
def clear_menu():
    """Control whether to clear screen after functions.

    The `clear_menu` will determine if extra lines will be printed before elements are displayed to make the design
    neater. The only correct option are 'y' and 'n', True and False respectively.

    Note:
        Number of lines to scroll can be set by Clear Length option.

    """

    r = input('Clear menu [y/n]: ').strip().lower()
    if r == 'y':
        conf.clear_menu = True
    elif r == 'n':
        conf.clear_menu = False
    else:
        menu_log.warning('invalid value for clear menu %r', r)
client.add_func('Clear Menu', clear_menu)


@dump_after
def clear_len():
    """Control number of lines to scroll on clear.

    Note:
        This option only has an effect if Clear Menu is enabled.

    """

    r = input('Clear length [%s]: ' % conf.clear_len)
    try:
        n = int(r)
        conf.clear_len = n
    except ValueError:
        menu_log.warning('invalid value for clear len %r', r)
client.add_func('Clear Length', clear_len)


@dump_after
def menu_name_char():
    """Determine underlining character of menu names.

    Note:
        Character must be have a length of one.

    """

    r = input('Menu underline character [%s]: ' % conf.menu_name_char)
    if len(r) == 1:
        conf.menu_name_char = r
    else:
        menu_log.warning('invalid menu name char length %r', r)
client.add_func('Menu Character', menu_name_char)


# server options
server = options.add_menu('Server', doc='Control network options.')


@dump_after
def bandwidth():
    """Set limit on network bandwidth.

    P2pg will attempt to keep its bandwidth usage under this limit. If the bandwidth is set to "-1", p2pg will assume
    that there is no bandwidth limit.

    Note:
        P2pg may exceed this limit depending on circumstance.

    """

    r = input('Bandwidth limit in KB [%s]: ' % conf.bandwidth)
    try:
        n = int(r)
        conf.bandwidth = n
    except ValueError:
        menu_log.warning('invalid value for bandwidth limit %r', r)
server.add_func('Bandwidth Limit', bandwidth)


@dump_after
def network():
    """Set daily limit on network usage.

    P2pg will attempt to limit its daily network usage to this value. If the usage limit is set to "-1", p2pg will
    assume that there is no network usage limit.

    Note:
        P2pg may exceed this limit depending on circumstance.

    """

    r = input('Network limit in MB [%s]: ' % conf.network)
    try:
        n = int(r)
        conf.network = n
    except ValueError:
        menu_log.warning('invalid value for network limit %r', r)
server.add_func('Network Limit', network)


@dump_after
def disk():
    """Set disk limit for node storage.

    P2pg will keep the size of its node storage files under this limit. If the limit is set to "-1", p2pg will assume
    that there is no disk space limit.

    """

    r = input('Node storage limit in MB [%s]: ' % conf.disk)
    try:
        n = int(r)
        conf.disk = n
    except ValueError:
        menu_log.warning('invalid value for disk limit %r', r)
