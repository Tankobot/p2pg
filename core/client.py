"""Manage the p2pg client side display."""

from logging import getLogger, Logger, NullHandler
from core import info_form, conf, StopException
from weakref import ref
from collections import namedtuple
from textwrap import dedent, wrap


log = getLogger(__name__)


class Error(Exception):
    pass


def clear():
    """Clear screen."""
    if conf.clear_menu:
        print('\n' * conf.clear_len)


def form_doc(doc):
    """Trim docstring for printing."""

    i = doc.find('\n') + 1
    doc = doc % info_form
    header = doc[:i]

    body = doc[i:]
    body = dedent(body)

    lines = body.split('\n')
    wrapped = []
    for _ in range(len(lines)):
        wrapped.extend(wrap(lines.pop(0), conf.terminal_width) or [''])

    body = '\n'.join(wrapped)
    return header + body


class Printer:
    """Print nodes form mutable list."""


class Controller:
    """Control the play portion of the game."""


Option = namedtuple('Option', 'name action')


# create section specific logger
menu_log = log.getChild('menu')  # type: Logger
menu_log.addHandler(NullHandler())


class Menu:
    """Navigate user through menus."""

    def __init__(self, name: str, parent=None, *, doc=None):
        """Initialize menu."""

        if parent and not isinstance(parent, self.__class__):
            raise TypeError('invalid parent %r' % parent)

        self.name = name
        self._parent = ref(parent) if parent else ref(self)
        self.doc = doc
        self._options = []  # type: list[Option]

    def __iter__(self):
        return iter(self._options)

    def add_menu(self, menu, *, doc=None):
        """Register option that points to a menu.

        The newly created menu will have the current menu as its parent.

        :rtype: Menu

        """

        if isinstance(menu, self.__class__):
            # link menu outside menu to self
            menu._parent = ref(self)
        elif isinstance(menu, str):
            # create new menu
            menu = self.__class__(menu, self, doc=doc+'\n'*2)
        else:
            raise TypeError('menu %r is not Menu or string' % menu)
        self._options.append(Option(menu.name, menu))
        return menu

    def add_func(self, name: str, func=None):
        """Register option that points to a function.

        Note:
            The function will automatically print out its doc when called.

        """

        if func is None:
            func = self._place_holder
        if not callable(func):
            raise TypeError('function %r not callable' % func)
        self._options.append(Option(name, _Func(func)))
        return func

    def prompt(self):
        """Display prompt for user selection.

        Special key commands include:
            'h' | 'help': print this message
            'b': move to the previous menu
            'q': quit p2pg

        :rtype: Menu | _Func

        """

        clear()

        print(self.name)
        print(conf.menu_name_char * len(self.name))
        print()  # add line between menu name and items

        # print doc info if possible
        if self.doc:
            print(form_doc(self.doc))

        for i, opt in enumerate(self._options):
            print(' %s: %s' % (i, opt.name))

        print()  # add line between items and input
        r = input('> ').strip()
        if r == 'b':
            return self._parent()
        elif r == 'q':
            raise StopException('exit menu command')
        elif r == 'h' or r == 'help':
            clear()
            print(form_doc(self.prompt.__doc__))
            input('Press enter to continue.')  # wait for the user to read

        # convert response
        try:
            r = int(r)
            # only accept selection from front of list
            if r < 0:
                raise ValueError('response too large %r' % r)
        except ValueError:
            # default to self
            return self

        # select action
        try:
            return self._options[r].action
        except IndexError:
            # default to self
            return self

    # prompt on call
    def __call__(self):
        return self.prompt()

    @staticmethod
    def _place_holder():
        menu_log.warning('place holder called')


class _Func:
    def __init__(self, func, *args, **kwargs):
        if not callable(func):
            raise TypeError('function %r not callable' % func)
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        clear()
        # print help information
        if self._func.__doc__:
            print(form_doc(self._func.__doc__))
        return self._func(*self._args, **self._kwargs)
