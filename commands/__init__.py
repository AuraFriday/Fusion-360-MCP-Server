# Commands that will be added to the Fusion 360 UI
# These are user-triggered actions (buttons, menus, etc.)
# 
# NOTE: The MCP integration is NOT a command - it's core infrastructure
# that auto-starts in MCP-Link.py. Only add actual UI commands here.

# Sample commands (for reference - can be removed if not needed)
from .samples.commandDialog import sample_dialog_command as commandDialog
from .samples.paletteShow import sample_palette_show as paletteShow
from .samples.paletteSend import sample_palette_send as paletteSend

# Active commands list - add your custom commands here
# NOTE: Sample commands are included but you can remove them if not needed
commands = [
    commandDialog,
    paletteShow,
    paletteSend
]


# Assumes you defined a "start" function in each of your modules.
# The start function will be run when the add-in is started.
def start():
    for command in commands:
        command.start()


# Assumes you defined a "stop" function in each of your modules.
# The stop function will be run when the add-in is stopped.
def stop():
    for command in commands:
        command.stop()