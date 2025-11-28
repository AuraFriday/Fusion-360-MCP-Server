"""
MCP Bridge for Fusion Python Execution

Provides mcp.call() function for calling other MCP tools from within
Python code executed in Fusion context.

This module is injected into the execution environment of AI-written Python code,
allowing it to call other MCP tools (SQLite, browser, user, etc.) seamlessly.
"""

from typing import Dict, Any, Optional

# Global reference to MCP client (set by mcp_integration.py)
_mcp_client = None

def set_mcp_client(client):
  """
  Set the MCP client instance for tool calling.
  
  Called by mcp_integration.py before Python execution to provide
  access to the MCP client.
  
  Args:
    client: MCPClient instance with call_mcp_tool() method
  """
  global _mcp_client
  _mcp_client = client

def call(tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
  """
  Call another MCP tool from within Python code.
  
  This function is available in the execution environment of AI-written
  Python code, allowing seamless integration with other MCP tools.
  
  Args:
    tool_name: Name of the tool to call (e.g., "sqlite", "browser", "user")
    arguments: Arguments to pass to the tool
    
  Returns:
    Tool response dictionary, or None on error
    
  Raises:
    RuntimeError: If MCP client not initialized
    
  Example:
    # Store data in SQLite
    result = mcp.call("sqlite", {
        "input": {
            "sql": "INSERT INTO designs (name) VALUES (?)",
            "params": ["my_design"],
            "tool_unlock_token": "29e63eb5"
        }
    })
    
    # Show popup to user
    mcp.call("user", {
        "input": {
            "operation": "show_popup",
            "html": "<h1>Design Complete!</h1>",
            "width": 300,
            "height": 150,
            "tool_unlock_token": "1d9bf6a0"
        }
    })
    
    # Open browser to documentation
    mcp.call("browser", {
        "input": {
            "operation": "navigate",
            "url": "https://help.autodesk.com/view/fusion360/",
            "tool_unlock_token": "e5076d"
        }
    })
  """
  if not _mcp_client:
    raise RuntimeError("MCP client not initialized - cannot call MCP tools. This should not happen during normal execution.")
  
  return _mcp_client.call_mcp_tool(tool_name, arguments)

