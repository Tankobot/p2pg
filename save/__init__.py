from save.save import *


conf = Save('conf')
conf.register('terminal_length', 1, IntConverter(1))
