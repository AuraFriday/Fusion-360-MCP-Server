# Application Global Variables
# This module serves as a way to share variables across different
# modules (global variables).

import os

# Flag that indicates to run in Debug mode or not. When running in Debug mode
# more information is written to the Text Command window. Generally, it's useful
# to set this to True while developing an add-in and set it to False when you
# are ready to distribute it.
DEBUG = True

# MCP Debug flag - enables verbose logging for MCP connection and communication
# Set to True for detailed MCP diagnostics, False to reduce log noise
MCP_DEBUG = True

# MCP Auto-connect - if True, automatically connect to MCP server on add-in startup
# Set to False to require manual connection via the "Connect to MCP" button
MCP_AUTO_CONNECT = True

# Gets the name of the add-in from the name of the folder the py file is in.
# This is used when defining unique internal names for various UI elements 
# that need a unique name. It's also recommended to use a company name as 
# part of the ID to better ensure the ID is unique.
# 
# IMPORTANT: Use a fixed name instead of folder name to avoid conflicts
# when the folder name changes (e.g., different versions)
ADDIN_NAME = 'MCPLinkFusion'
COMPANY_NAME = 'AuraFriday'

# Palettes
sample_palette_id = f'{COMPANY_NAME}_{ADDIN_NAME}_palette_id'

# MCP Configuration
MCP_TOOL_NAME = 'fusion360'
MCP_TOOL_DESCRIPTION = 'Autodesk Fusion - AI-powered CAD/CAM/CAE software for product design and manufacturing'
