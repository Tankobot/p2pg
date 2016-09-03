from core.ld import EasyConfig
from typing import List


class Conf(EasyConfig):
    def __init__(self):
        super().__init__(defaults={
            'story_path': [],  # game progress
            'terminal_width': 60,  # client terminal width
            'clear_menu': True,  # clear the screen after menu actions
            'clear_len': 50,  # number of lines to scroll down for clear
            'menu_name_char': '-',  # character to print under menu names
            'bandwidth_KB': -1,  # total bandwidth to use at one time
            'network_MB': -1,  # total bandwidth to use per day
            'disk_MB': -1,  # disk space limit for nodes
        })

    @property
    def story_path(self) -> List[str]:
        """List describing the current saved story path."""
        return self.dict['story_path']

    @story_path.setter
    def story_path(self, value: List[str]):
        self.dict['story_path'] = value

    ##
    # client
    ##

    @property
    def terminal_width(self) -> int:
        """Integer describing width of terminal."""
        return self.dict['terminal_width']

    @terminal_width.setter
    def terminal_width(self, value: int):
        self.dict['terminal_width'] = value

    @property
    def clear_menu(self) -> bool:
        """Boolean describing whether to clear screen before menus."""
        return self.dict['clear_menu']

    @clear_menu.setter
    def clear_menu(self, value: bool):
        self.dict['clear_menu'] = value

    @property
    def clear_len(self) -> int:
        """Amount to scroll when clearing screen."""
        return self.dict['clear_len']

    @clear_len.setter
    def clear_len(self, value: int):
        self.dict['clear_len'] = value

    @property
    def menu_name_char(self) -> str:
        """Character to use as underline for menu names."""
        return self.dict['menu_name_char']

    @menu_name_char.setter
    def menu_name_char(self, value: str):
        self.dict['menu_name_char'] = value

    ##
    # server
    ##

    @property
    def bandwidth(self) -> int:
        """Bandwidth limit in kilobytes."""
        return self.dict['bandwidth_KB']

    @bandwidth.setter
    def bandwidth(self, value: int):
        self.dict['bandwidth_KB'] = value

    @property
    def network(self) -> int:
        """Network limit in megabytes."""
        return self.dict['network_MB']

    @network.setter
    def network(self, value: int):
        self.dict['network_MB'] = value

    @property
    def disk(self) -> int:
        """Disk limit for nodes in megabytes."""
        return self.dict['disk_MB']

    @disk.setter
    def disk(self, value: int):
        self.dict['disk_MB'] = value


conf = Conf()


def dump_after(f):
    def g(*args, **kwargs):
        f(*args, **kwargs)
        conf.dump()
    # preserve name and doc of function
    g.__name__ = f.__name__
    g.__doc__ = f.__doc__
    return g


def close():
    conf.close()
