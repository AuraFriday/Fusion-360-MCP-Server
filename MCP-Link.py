# Main entry point for the Fusion 360 add-in
# Fusion calls run() when the add-in starts and stop() when it ends

from . import commands
from . import mcp_integration
from .lib import fusionAddInUtils as futil
from . import config


def run(context):
    try:
        futil.log("="*60)
        futil.log("MCP-Link Add-in: run() called")
        futil.log(f"DEBUG mode: {config.DEBUG}")
        futil.log(f"MCP_DEBUG mode: {config.MCP_DEBUG}")
        futil.log(f"MCP_AUTO_CONNECT: {config.MCP_AUTO_CONNECT}")
        futil.log("="*60)
        
        # Start MCP integration (core infrastructure - not a command)
        mcp_integration.start()
        
        # Start any UI commands (buttons, palettes, etc.)
        commands.start()
        
        futil.log("[OK] MCP-Link Add-in started successfully")

    except:
        futil.handle_error('run')


def stop(context):
    try:
        futil.log("="*60)
        futil.log("MCP-Link Add-in: stop() called")
        futil.log("="*60)
        
        # Stop MCP integration first
        mcp_integration.stop()
        
        # Stop UI commands
        commands.stop()
        
        # Remove all event handlers
        futil.clear_handlers()
        
        futil.log("[OK] MCP-Link Add-in stopped")

    except:
        futil.handle_error('stop')