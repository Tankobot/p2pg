"""Manage the client portion."""

import logging
from core.node import Node


class ClientError(Exception):
    pass


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
        self._bottom.feed(node.msg)

    def __rshift__(self, value: int):
        if value < 1:
            raise ValueError('can\'t shift by negative')
        cut = sum(self._paragraphs[-value:])
        self._top.release(cut)
        self._nodes[-value + 1:] = []
        self._bottom = self.default_printer()
        self._bottom.feed(self._nodes.pop().msg)


class ExitMenu(Exception):
    pass


class Menu:
    def __init__(self, menu: list, sep=' : '):
        self._cursor = [menu]
        self._sep = sep

    def _parse(self, menu):
        pos = 0

        names = 0
        for item in menu:
            if isinstance(item, str):
                names += 1

        space = len(str(len(menu) - names - 1))
        options = []
        for item in menu:
            if isinstance(item, str):
                print(item, end='\n'*2)
            elif isinstance(item, list):
                extra = ' '*(space - len(str(pos)))
                print(pos, item[0], sep=extra+self._sep)
                options.append(item)
                pos += 1
            else:
                raise TypeError('incorrect menu_items item %r' % item)
        return options

    def prompt(self, prefix='> '):
        while True:
            print('\n' * 50)
            menu = self._cursor[-1]
            options = self._parse(menu)
            print()

            re = input(prefix).strip().lower()

            # protect against menu_items exit
            try:
                # check for integer situation
                try:
                    re = int(re)
                    opt = options[re]
                    if callable(opt[1]):
                        opt[1]()
                    else:
                        self._cursor.append(opt)
                except ValueError:
                    pass
                except IndexError:
                    raise ClientError('incorrect menu') from None

                # check for string commands
                # go back
                if re == 'b':
                    if len(self._cursor) == 1:
                        break
                    self._cursor.pop()
                elif re == 'h' or re == 'help':
                    print('B to go back, enter to continue.')
                    input()
                else:
                    logging.warning('Incorrect input.')
            except ExitMenu:
                break

    def reset(self):
        self._cursor = self._cursor[0]
