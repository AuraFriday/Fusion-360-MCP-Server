# Commands that will be added to the Fusion 360 UI
# These are user-triggered actions (buttons, menus, etc.)
# 
# NOTE: The MCP integration is NOT a command - it's core infrastructure
# that auto-starts in MCP-Link.py. Only add actual UI commands here.

# MCP About command - shows information about the add-in
from .mcpAbout import mcp_about_command as mcpAbout

# Active commands list
commands = [
    mcpAbout
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