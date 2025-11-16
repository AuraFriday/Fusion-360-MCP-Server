# Main entry point for the Fusion 360 add-in
# Fusion calls run() when the add-in starts and stop() when it ends

from . import commands
from . import mcp_integration
from .lib import fusionAddInUtils as futil
from . import config


def run(context):
    try:
        mcp_integration.log("="*60)
        mcp_integration.log("MCP-Link Add-in: run() called")
        mcp_integration.log(f"DEBUG mode: {config.DEBUG}")
        mcp_integration.log(f"MCP_DEBUG mode: {config.MCP_DEBUG}")
        mcp_integration.log(f"MCP_AUTO_CONNECT: {config.MCP_AUTO_CONNECT}")
        mcp_integration.log("="*60)
        
        # Start MCP integration (core infrastructure - not a command)
        mcp_integration.start()
        
        # Start any UI commands (buttons, palettes, etc.)
        commands.start()
        
        mcp_integration.log("[OK] MCP-Link Add-in started successfully")

    except:
        futil.handle_error('run')


def stop(context):
    try:
        mcp_integration.log("="*60)
        mcp_integration.log("MCP-Link Add-in: stop() called")
        mcp_integration.log("="*60)
        
        # Stop MCP integration first
        mcp_integration.stop()
        
        # Stop UI commands
        commands.stop()
        
        # Remove all event handlers
        futil.clear_handlers()
        
        mcp_integration.log("[OK] MCP-Link Add-in stopped")

    except:
        futil.handle_error('stop')