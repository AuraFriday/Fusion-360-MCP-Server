import adsk.core
import os
from ...lib import fusionAddInUtils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# Command identity information
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_mcpAbout'
CMD_NAME = 'AuraFriday MCP Server'
CMD_Description = 'Control Fusion with AI'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# Define the location where the command button will be created.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Check if the command already exists and remove it
    # This handles cases where the add-in was previously loaded
    existing_cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if existing_cmd_def:
        futil.log(f'{CMD_NAME}: Removing existing command definition')
        existing_cmd_def.deleteMe()
    
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # Create a read-only text box with thank you message and feedback request
    thank_you_html = '''<div style="font-family: Arial, sans-serif; padding: 10px;">
<h2 style="color: #0696D7;">Thank You for Using AuraFriday MCP Server!</h2>

<p>This add-in enables <strong>AI-powered control</strong> of Fusion through the Model Context Protocol (MCP).</p>

<h3>🌟 Enjoying This Tool?</h3>
<p>If you find this add-in helpful, please consider:</p>
<ul>
    <li><strong>⭐ Leave us a 5-star review</strong> on the Autodesk App Store</li>
    <li><strong>⭐ Star our GitHub repository</strong> at <a href="https://github.com/AuraFriday/Fusion-360-MCP-Server">github.com/AuraFriday/Fusion-360-MCP-Server</a></li>
</ul>

<h3>💡 Not Quite 5-Star Worthy Yet?</h3>
<p>We want to earn your 5 stars! Please help us improve by:</p>
<ul>
    <li><strong>📝 Opening an issue</strong> on our <a href="https://github.com/AuraFriday/Fusion-360-MCP-Server/issues">GitHub Issues page</a></li>
    <li><strong>💬 Telling us what's missing</strong> or what could be better</li>
</ul>

<h3>🚀 What This Add-in Does:</h3>
<ul>
    <li>Connects Fusion to your local MCP server</li>
    <li>Enables AI assistants (like Claude, ChatGPT, etc.) to control Fusion</li>
    <li>Provides a generic API for data-driven CAD automation</li>
    <li>Supports Python execution with MCP tool integration</li>
</ul>

<h3>📚 Learn More:</h3>
<ul>
    <li><strong>Documentation:</strong> <a href="https://github.com/AuraFriday/Fusion-360-MCP-Server">GitHub README</a></li>
    <li><strong>MCP Server Download:</strong> <a href="https://github.com/AuraFriday/mcp-link-server/releases/tag/latest">Get the latest MCP-Link Server</a></li>
    <li><strong>Examples:</strong> Check the repository for demo scripts</li>
    <li><strong>Support:</strong> Open an issue on GitHub</li>
</ul>

<p style="margin-top: 20px; padding-top: 10px; border-top: 1px solid #ccc; color: #666;">
<strong>Version:</strong> 1.2.73<br>
<strong>Author:</strong> Christopher Nathan Drake<br>
<strong>License:</strong> Proprietary<br>
<strong>Website:</strong> <a href="https://www.aurafriday.com">www.aurafriday.com</a>
</p>
</div>'''
    
    inputs.addTextBoxCommandInput('about_text', '', thank_you_html, 20, True)

    # Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')
    
    # Nothing to do - this is just an informational dialog


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []

