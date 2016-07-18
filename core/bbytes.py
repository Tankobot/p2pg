class Byte(int):
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        if self < 0 or self > 255:
            raise ValueError('int is too big')
        return self

    def __getitem__(self, item):
        # reverse endian
        pos = 7 - item
        return 1 if (self // 2**pos) % 2 else 0

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           super().__repr__())


class ByteArray(bytearray):
    def __getitem__(self, item):
        if isinstance(item, tuple):
            # single bit
            return Byte(super().__getitem__(item[0]))[item[1]]
        elif isinstance(item, int):
            # entire byte
            return Byte(super().__getitem__(item))
        elif isinstance(item, slice):
            return ByteArray(super().__getitem__(item))
        else:
            return super().__getitem__(item)

    def bit(self, n: int, v: int = None):
        byte = n // 8
        carry = n - byte
        if v:
            self[byte, carry] = v
        else:
            return self[byte, carry]

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            # single bit
            byte = self[key[0]]
            # reverse endian
            pos = 7 - key[1]
            place = 2**pos
            bit = (byte // place) % 2
            if value == 1:
                byte += 0 if bit else place
            elif value == 0:
                byte -= place if bit else 0
            else:
                raise ValueError('attempt to assign non 1 or 0')
            super().__setitem__(key[0], byte)
        elif isinstance(key, int):
            # whole byte
            super().__setitem__(key, value)
        else:
            super().__setitem__(key, value)

    def __repr__(self):
        end = super().__repr__().lstrip(bytearray.__name__)
        return '%s%s' % (self.__class__.__name__, end)
