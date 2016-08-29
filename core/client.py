"""Manage the client portion."""

from core import conf
from core.node import Node
from weakref import ref
from collections import namedtuple
from textwrap import dedent


class ClientError(Exception):
    pass


def clear():
    if conf.keys.clear_menu:
        print('\n' * conf.keys.clear_len)


def form_doc(doc):
    i = doc.find('\n') + 1
    header = doc[:i]
    body = doc[i:]
    return header + dedent(body)


class Printer:
    def __init__(self, length=60, height=None):
        """Format messages for printing."""

        self._length = length
        self._height = height
        self._words = ['\n']
        self._lines = []

    def __len__(self):
        self.unpack()
        value = len(self._words) + 1
        self.pack()
        return value

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value
        self.unpack()
        self.pack()

    @property
    def height(self):
        return len(self._lines) + (1 if self._words else 0)

    @height.setter
    def height(self, value):
        self._height = value
        self.pack()

    def feed(self, text: str):
        self._words.extend(text.strip().split(' '))
        self.pack()

    def release(self, n: int):
        self.unpack()
        self._words[-n:] = []
        self.pack()

    def concat(self, other):
        assert isinstance(other, self.__class__)
        other.unpack()
        self._words.append('\n')
        self._words.extend(other._words)
        self.pack()
        other.pack()

    def unpack(self):
        old_words = []
        for line in self._lines:
            old_words.extend(line)
        self._lines = []
        self._words = old_words + self._words

    def pack(self):
        excess = []

        while self._words:
            is_less = len(' '.join(self._words)) <= self._length
            if is_less:
                line = self._words
                self._words = []
            else:
                line = []
            while len(' '.join(line)) <= self._length:
                try:
                    word = self._words.pop(0)
                    if len(word) > self._length:
                        offset = self._length - 1
                        offset -= len(' '.join(line))
                        cut_word = word[offset:]
                        self._words.insert(0, cut_word)
                        word = word[:offset] + '-'
                    line.append(word)
                except IndexError:
                    excess = line
                    break
            if not excess:
                self._words.insert(0, line.pop())
                self._lines.append(line)

        # trim if necessary
        try:
            # account for excess
            if self._height is None:
                raise ClientError('no height limit')
            more = 1 if excess else 0
            n_lines = len(self._lines)
            self._lines = self._lines[n_lines + more - self._height:]
        except IndexError:
            pass
        except ClientError:
            pass

        self._words = excess

    def print(self):
        for line in self._lines:
            print(' '.join(line))
        # print excess
        if self._words:
            print(' '.join(self._words))


class Controller:
    def __init__(self, prompt: str, length=60, height=None):
        """Execute functions based on user input."""

        self.header = []
        self._header = ''
        self.prompt = prompt
        self._length = length
        self._height = height
        self._commands = {}
        self._top = Printer(length, height)
        self._bottom = Printer(length, height)
        self._paragraphs = []
        self._nodes = []

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value
        self._top.length = value
        self._bottom.length = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value
        self._top._height = value
        self._bottom.height = value

    def ask(self, err_msg=None):
        print(self._header)
        re = input(self.prompt).strip().split()
        try:
            cmd = self._commands[re[0]]
        except IndexError:
            cmd = None
            if err_msg:
                print(err_msg)
        if cmd:
            cmd(*re[1:])

    def register(self, char: str, func):
        if ' ' in char:
            raise ValueError('spaces cannot be in char')
        if not callable(func):
            raise TypeError('func is non callable')
        self._commands[char] = func

    def add_cmd(self, name: str):
        self.header.append(name)
        self.place_header()

    def place_header(self):
        if len(self.header) == 1:
            self._header = self.header[0]
        elif len(self.header) == 2:
            self._header = self.header[0]
            off = self.length
            off -= len(self.header[0])
            off -= len(self.header[1])
            if off < 0:
                raise ValueError('header too large')
            self._header += ' ' * off
            self._header += self.header[1]
        else:
            raise ValueError('too many/little headers')

    def replace(self, other: Printer):
        self._bottom = other

    def default_printer(self):
        return Printer(self._length, self._height)

    def __lshift__(self, node: Node):
        self._paragraphs.append(len(self._bottom))
        self._nodes.append(node)
        self._top.concat(self._bottom)
        self._bottom_node = node
        self._bottom = self.default_printer()
        self._bottom.feed(node.msg.decode('utf-8'))

    def __rshift__(self, value: int):
        if value < 1:
            raise ValueError('can\'t shift by negative')
        cut = sum(self._paragraphs[-value:])
        self._top.release(cut)
        self._nodes[-value + 1:] = []
        self._bottom = self.default_printer()
        self._bottom.feed(self._nodes.pop().msg)


Option = namedtuple('Option', 'name action')


class Menu:
    """Navigate user through menus."""

    def __init__(self, name: str, parent=None):
        """Initialize menu."""

        if parent and not isinstance(parent, self.__class__):
            raise TypeError('invalid parent %r' % parent)

        self.name = name
        self._parent = ref(parent) if parent else ref(self)
        self._options = []  # type: list[Option]

    def __iter__(self):
        return iter(self._options)

    def add_menu(self, menu):
        """Register option that points to a menu.

        The newly created menu will have the current menu as its parent.

        :rtype: Menu

        """

        if isinstance(menu, self.__class__):
            # link menu outside menu to self
            menu._parent = ref(self)
        elif isinstance(menu, str):
            # create new menu
            menu = self.__class__(menu, self)
        else:
            raise TypeError('menu %r is not Menu or string' % menu)
        self._options.append(Option(menu.name, menu))
        return menu

    def add_func(self, name: str, func):
        """Register option that points to a function."""

        if not callable(func):
            raise TypeError('function %r not callable' % func)
        self._options.append(Option(name, func))
        return func

    def prompt(self):
        """Display prompt for user selection.

        Special key commands include:
            'h' | 'help': print this message
            'b': move to the previous menu

        :rtype: Menu | Func

        """

        clear()

        print(self.name)
        print(conf.keys.menu_name_char * len(self.name))
        print()  # add line between menu name and items

        for i, opt in enumerate(self._options):
            print(' %s: %s' % (i, opt.name))

        print()  # add line between items and input
        r = input('> ').strip()
        if r == 'b':
            return self._parent()
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
    __call__ = prompt


class Func:
    def __init__(self, func, *args, **kwargs):
        if not callable(func):
            raise TypeError('function %r not callable' % func)
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        clear()
        return self._func(*self._args, **self._kwargs)
