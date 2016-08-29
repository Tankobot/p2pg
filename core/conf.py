from core.ld import EasyConfig

conf = EasyConfig(defaults={
    'terminal_width': 40,  # client terminal width
    'bandwidth_KB': -1,  # total bandwidth to use at one time
    'network_MB': -1,  # total bandwidth to use per day
    'disk_MB': -1,  # soft disk space limit for nodes
    'story_path': [],  # game progress
    'clear_menu': True,  # clear the screen after menu actions
    'clear_len': 50,  # number of lines to scroll down for clear
    'menu_name_char': '-',  # character to print under menu names
})


def close():
    conf.close()
