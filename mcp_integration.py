"""
File: mcp_integration.py
Project: MCP-Link Fusion 360 Add-in
Component: MCP Integration - Core infrastructure for connecting Fusion 360 to MCP-Link server
Author: Christopher Nathan Drake (cnd)
Created: 2025-11-03
Last Modified: 2025-11-03 by cnd
SPDX-License-Identifier: Proprietary
Copyright: (c) 2025 Christopher Nathan Drake. All rights reserved.

This module provides the core MCP integration functionality:
- Auto-connects to MCP server on add-in startup
- Registers Fusion 360 as a remote tool
- Handles incoming tool calls via generic API executor
- NOT a UI command - runs automatically as infrastructure
"""

import adsk.core
import os
from .lib import fusionAddInUtils as futil
from .lib import mcp_client
from . import config

app = adsk.core.Application.get()
ui = app.userInterface

# Global MCP client instance (maintains connection throughout add-in lifecycle)
mcp_client_instance = None


def _create_mcp_client():
  """
  Create and configure the MCP client instance.
  
  Returns:
    Configured MCPClient instance ready to connect
  """
  tool_name = "fusion360"
  tool_description = "Autodesk Fusion 360 - AI-powered CAD/CAM/CAE software for product design and manufacturing"
  tool_readme = """
Fusion 360 MCP Tool - Generic API Access

This tool provides COMPLETE, DATA-DRIVEN access to Autodesk Fusion 360's API.
NO custom code needed - just specify the API path and arguments!

## Command Format

{
  "api_path": "path.to.method",          // Required: Dotted path to API method/property
  "args": [...],                         // Optional: Positional arguments
  "kwargs": {...},                       // Optional: Keyword arguments
  "store_as": "variable_name",           // Optional: Store result for later use
  "return_properties": ["name", "type"]  // Optional: Which properties to return
}

## Path Shortcuts

- `app` → Application.get()
- `ui` → Application.get().userInterface
- `design` → Application.get().activeProduct
- `rootComponent` → Application.get().activeProduct.rootComponent
- `$variable_name` → Previously stored object

## Examples

### Create a Sketch
{
  "api_path": "rootComponent.sketches.add",
  "args": ["rootComponent.xYConstructionPlane"],
  "store_as": "sketch1",
  "return_properties": ["name", "isVisible"]
}

### Add Lines to Sketch
{
  "api_path": "$sketch1.sketchCurves.sketchLines.addByTwoPoints",
  "args": [
    {"type": "Point3D", "x": 0, "y": 0, "z": 0},
    {"type": "Point3D", "x": 10, "y": 0, "z": 0}
  ],
  "store_as": "line1"
}

### Create Rectangle
{
  "api_path": "$sketch1.sketchCurves.sketchLines.addTwoPointRectangle",
  "args": [
    {"type": "Point3D", "x": 4, "y": 0, "z": 0},
    {"type": "Point3D", "x": 7, "y": 2, "z": 0}
  ]
}

### Query Properties
{
  "api_path": "design.rootComponent.bRepBodies",
  "return_properties": ["count"]
}

## Object Constructors

Use dicts with "type" field to construct Fusion objects:

- `{"type": "Point3D", "x": 0, "y": 0, "z": 0}`
- `{"type": "Vector3D", "x": 1, "y": 0, "z": 0}`

## Multi-Step Operations

Store intermediate results with `store_as`, then reference them with `$name`:

1. Create sketch → store as `$sketch1`
2. Add lines to `$sketch1.sketchCurves.sketchLines`
3. Add constraints to stored lines

## Note

Fusion 360 must be running with the MCP-Link add-in active.
The add-in maintains a session context for stored objects across multiple calls.
"""
  
  # Storage for intermediate results (for multi-step operations)
  fusion_context = {}
  
  def fusion_tool_handler(call_data):
    """
    Handle incoming tool calls from MCP server.
    
    This is a COMPLETELY GENERIC handler that can execute ANY Fusion 360 API call
    without custom code. Commands are data-driven via api_path navigation.
    
    Command format:
    {
      "api_path": "rootComponent.sketches.add",  // Path to method/property
      "args": ["xYConstructionPlane"],            // Positional args (can reference stored objects or paths)
      "kwargs": {},                               // Keyword arguments
      "store_as": "sketch1",                      // Optional: store result with this key
      "return_properties": ["name", "isVisible"] // Optional: which properties to return
    }
    
    Example - Create a sketch:
    {
      "api_path": "activeProduct.rootComponent.sketches.add",
      "args": ["activeProduct.rootComponent.xYConstructionPlane"],
      "store_as": "my_sketch"
    }
    
    Example - Add lines to sketch:
    {
      "api_path": "$my_sketch.sketchCurves.sketchLines.addByTwoPoints",
      "args": [{"type": "Point3D", "x": 0, "y": 0, "z": 0}, 
               {"type": "Point3D", "x": 10, "y": 0, "z": 0}]
    }
    """
    try:
      import adsk.core
      import adsk.fusion
      import os
      
      # Extract command parameters
      params = call_data.get('params', {})
      arguments = params.get('arguments', {})
      
      api_path = arguments.get('api_path', '')
      args = arguments.get('args', [])
      kwargs = arguments.get('kwargs', {})
      store_as = arguments.get('store_as')
      return_properties = arguments.get('return_properties', [])
      
      # Handle special commands
      if api_path == 'get_pid':
        pid = os.getpid()
        futil.log(f"[TOOL CALL] Fusion 360 PID: {pid}")
        return {
          "content": [{
            "type": "text",
            "text": f"Fusion 360 Process ID: {pid}"
          }],
          "isError": False
        }
      
      if api_path == 'clear_context':
        count = len(fusion_context)
        fusion_context.clear()
        futil.log(f"[TOOL CALL] Cleared {count} stored objects")
        return {
          "content": [{
            "type": "text",
            "text": f"Cleared {count} stored objects from context"
          }],
          "isError": False
        }
      
      futil.log(f"[TOOL CALL] API Path: {api_path}")
      futil.log(f"[TOOL CALL] Args: {args}")
      futil.log(f"[TOOL CALL] Kwargs: {kwargs}")
      
      # Resolve the API path to an actual object/method
      target = _resolve_api_path(api_path, fusion_context)
      
      # Resolve arguments (they might reference stored objects or API paths)
      resolved_args = [_resolve_argument(arg, fusion_context) for arg in args]
      resolved_kwargs = {k: _resolve_argument(v, fusion_context) for k, v in kwargs.items()}
      
      # Execute the call
      if callable(target):
        result = target(*resolved_args, **resolved_kwargs)
      else:
        result = target  # It's a property, not a method
      
      # Store result if requested
      if store_as:
        fusion_context[store_as] = result
        futil.log(f"[TOOL CALL] Stored result as '{store_as}'")
      
      # Extract return properties
      result_info = _extract_result_info(result, return_properties)
      
      futil.log(f"[TOOL CALL] Result: {result_info}")
      
      # Build detailed success report for AI
      success_report = []
      success_report.append(f"✅ SUCCESS: {api_path}")
      success_report.append(f"\n📊 RESULT:")
      success_report.append(f"  {result_info}")
      if store_as:
        success_report.append(f"\n💾 STORED AS: '{store_as}'")
        success_report.append(f"  Use: ${{store_as}}.method() in future calls")
      success_report.append(f"\n🔍 RESULT TYPE: {type(result).__name__}")
      if result is not None and hasattr(result, '__class__'):
        success_report.append(f"  Module: {type(result).__module__}")
      success_report.append(f"\n💾 CONTEXT: {len(fusion_context)} stored object(s): {list(fusion_context.keys())}")
      
      success_text = "\n".join(success_report)
      
      return {
        "content": [{
          "type": "text",
          "text": success_text
        }],
        "isError": False
      }
      
    except Exception as e:
      import traceback
      error_trace = traceback.format_exc()
      
      # Build detailed error report for AI debugging
      error_report = []
      error_report.append(f"❌ ERROR: {type(e).__name__}: {str(e)}")
      error_report.append(f"\n📍 CALL DETAILS:")
      error_report.append(f"  api_path: {api_path}")
      error_report.append(f"  args: {args}")
      error_report.append(f"  kwargs: {kwargs}")
      error_report.append(f"  store_as: {store_as}")
      error_report.append(f"  return_properties: {return_properties}")
      error_report.append(f"\n💾 CONTEXT STATE:")
      error_report.append(f"  Stored objects: {list(fusion_context.keys())}")
      error_report.append(f"\n📚 FULL TRACEBACK:")
      error_report.append(error_trace)
      error_report.append(f"\n💡 HINTS:")
      if "has no attribute" in str(e):
        error_report.append(f"  - The object doesn't have the requested attribute/method")
        error_report.append(f"  - Check Fusion 360 API documentation for correct method names")
        error_report.append(f"  - Verify the object type supports this operation")
      if "takes" in str(e) and "positional argument" in str(e):
        error_report.append(f"  - Wrong number of arguments provided")
        error_report.append(f"  - Check the API signature for required parameters")
      if "NoneType" in str(e):
        error_report.append(f"  - An intermediate object in the path returned None")
        error_report.append(f"  - Check that the document/design is active and valid")
      
      error_text = "\n".join(error_report)
      
      futil.log(f"ERROR in fusion_tool_handler: {e}", adsk.core.LogLevels.ErrorLogLevel)
      futil.log(error_trace, adsk.core.LogLevels.ErrorLogLevel)
      
      return {
        "content": [{
          "type": "text",
          "text": error_text
        }],
        "isError": True
      }
  
  
  def _resolve_api_path(path, context):
    """
    Resolve an API path to an actual Fusion object/method.
    
    Supports:
    - Direct API paths: "app.activeProduct.rootComponent"
    - Stored references: "$my_sketch.sketchCurves"
    - Special keywords: "app", "ui", "design", "rootComponent"
    """
    import adsk.core
    import adsk.fusion
    
    if not path:
      raise ValueError("api_path is required")
    
    # Handle stored object references (start with $)
    if path.startswith('$'):
      parts = path[1:].split('.', 1)
      obj = context.get(parts[0])
      if obj is None:
        raise ValueError(f"Stored object '{parts[0]}' not found. Available: {list(context.keys())}")
      if len(parts) > 1:
        return _navigate_path(obj, parts[1])
      return obj
    
    # Handle full module paths (e.g., adsk.core.ValueInput.createByString)
    if path.startswith('adsk.core.'):
      remaining = path[10:]  # Remove 'adsk.core.'
      return _navigate_path(adsk.core, remaining)
    elif path.startswith('adsk.fusion.'):
      remaining = path[12:]  # Remove 'adsk.fusion.'
      return _navigate_path(adsk.fusion, remaining)
    
    # Start from app or special shortcuts
    if path.startswith('app.'):
      root = adsk.core.Application.get()
      remaining = path[4:]  # Remove 'app.'
    elif path.startswith('ui.'):
      root = adsk.core.Application.get().userInterface
      remaining = path[3:]  # Remove 'ui.'
    elif path.startswith('design.'):
      app = adsk.core.Application.get()
      root = app.activeProduct
      remaining = path[7:]  # Remove 'design.'
    elif path.startswith('rootComponent.'):
      app = adsk.core.Application.get()
      root = app.activeProduct.rootComponent
      remaining = path[14:]  # Remove 'rootComponent.'
    elif path == 'app':
      return adsk.core.Application.get()
    elif path == 'ui':
      return adsk.core.Application.get().userInterface
    elif path == 'design':
      return adsk.core.Application.get().activeProduct
    elif path == 'rootComponent':
      return adsk.core.Application.get().activeProduct.rootComponent
    else:
      # Assume it starts from app
      root = adsk.core.Application.get()
      remaining = path
    
    return _navigate_path(root, remaining)
  
  
  def _navigate_path(obj, path):
    """Navigate a dotted path from an object."""
    parts = path.split('.')
    current = obj
    
    for part in parts:
      if not part:
        continue
      current = getattr(current, part)
      if current is None:
        raise ValueError(f"Path '{path}' resolved to None at '{part}'")
    
    return current
  
  
  def _resolve_argument(arg, context):
    """
    Resolve an argument that might be:
    - A literal value (string, number, bool)
    - An API path reference
    - A stored object reference ($name)
    - A constructor call ({"type": "Point3D", "x": 0, "y": 0, "z": 0})
    """
    import adsk.core
    import adsk.fusion
    
    # Handle None, booleans, numbers
    if arg is None or isinstance(arg, (bool, int, float)):
      return arg
    
    # Handle strings - could be API paths or literal strings
    if isinstance(arg, str):
      # If it looks like an API path or stored reference, resolve it
      if '.' in arg or arg.startswith('$') or arg in ['app', 'ui', 'design', 'rootComponent']:
        try:
          return _resolve_api_path(arg, context)
        except:
          # If resolution fails, treat as literal string
          return arg
      return arg
    
    # Handle constructor calls
    if isinstance(arg, dict) and 'type' in arg:
      return _construct_object(arg)
    
    # Handle lists
    if isinstance(arg, list):
      return [_resolve_argument(item, context) for item in arg]
    
    return arg
  
  
  def _construct_object(spec):
    """
    Construct a Fusion 360 object from a specification.
    
    Example: {"type": "Point3D", "x": 0, "y": 0, "z": 0}
    """
    import adsk.core
    import adsk.fusion
    
    obj_type = spec.get('type')
    if not obj_type:
      raise ValueError("Object spec must have 'type' field")
    
    # Find the class in adsk.core or adsk.fusion
    cls = getattr(adsk.core, obj_type, None)
    if cls is None:
      cls = getattr(adsk.fusion, obj_type, None)
    if cls is None:
      raise ValueError(f"Unknown type: {obj_type}")
    
    # Get constructor parameters (everything except 'type')
    params = {k: v for k, v in spec.items() if k != 'type'}
    
    # Try to find a 'create' class method (common pattern in Fusion API)
    if hasattr(cls, 'create'):
      # Extract positional args based on common patterns
      if obj_type == 'Point3D':
        return cls.create(params.get('x', 0), params.get('y', 0), params.get('z', 0))
      elif obj_type == 'Vector3D':
        return cls.create(params.get('x', 0), params.get('y', 0), params.get('z', 0))
      else:
        # Generic approach - try with all params as kwargs
        return cls.create(**params)
    else:
      # Try direct instantiation
      return cls(**params)
  
  
  def _extract_result_info(result, properties=None):
    """Extract information from a result object."""
    if result is None:
      return "None"
    
    # If it's a primitive type, just return it
    if isinstance(result, (str, int, float, bool)):
      return str(result)
    
    # Extract requested properties
    if properties:
      info = {}
      for prop in properties:
        try:
          value = getattr(result, prop, None)
          info[prop] = str(value) if value is not None else "None"
        except:
          info[prop] = "Error accessing property"
      return str(info)
    
    # Default: return type and basic info
    result_type = type(result).__name__
    try:
      if hasattr(result, 'name'):
        return f"{result_type}(name='{result.name}')"
      elif hasattr(result, 'count'):
        return f"{result_type}(count={result.count})"
      elif hasattr(result, 'objectType'):
        return f"{result.objectType}"
      else:
        return result_type
    except:
      return result_type
  
  def log_callback(message):
    """Log callback for MCP client."""
    futil.log(f"[MCP] {message}")
  
  # Create and return the client
  return mcp_client.MCPClient(
    tool_name=tool_name,
    tool_description=tool_description,
    tool_readme=tool_readme,
    tool_handler=fusion_tool_handler,
    log_callback=log_callback
  )


def _auto_connect():
  """
  Automatically connect to MCP server (called during startup if MCP_AUTO_CONNECT is True).
  Does not show message boxes - logs only.
  """
  global mcp_client_instance
  
  if mcp_client_instance and mcp_client_instance.is_connected:
    futil.log("Already connected to MCP server")
    return
  
  futil.log("Starting auto-connect to MCP server...")
  
  # Create and connect
  mcp_client_instance = _create_mcp_client()
  success = mcp_client_instance.connect()
  
  if success:
    futil.log("[SUCCESS] Auto-connected to MCP server!")
  else:
    futil.log("Auto-connect failed - check logs above for details", adsk.core.LogLevels.WarningLogLevel)
    mcp_client_instance = None


def start():
  """Initialize MCP integration when add-in starts."""
  futil.log("="*60)
  futil.log("MCP Integration: start() called")
  futil.log("="*60)
  
  # Auto-connect to MCP server (no UI button - this is infrastructure)
  if config.MCP_AUTO_CONNECT:
    futil.log("MCP_AUTO_CONNECT is True - attempting auto-connect...")
    try:
      _auto_connect()
      futil.log("[OK] MCP Integration started successfully")
    except Exception as e:
      futil.log(f"ERROR: Auto-connect failed: {e}", adsk.core.LogLevels.ErrorLogLevel)
      import traceback
      futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
  else:
    futil.log("MCP_AUTO_CONNECT is False - MCP integration disabled")
    futil.log("Set MCP_AUTO_CONNECT = True in config.py to enable")


def stop():
  """Cleanup when add-in stops."""
  global mcp_client_instance
  
  futil.log("MCP Integration: stop() called")
  
  # Disconnect MCP client if connected
  if mcp_client_instance and mcp_client_instance.is_connected:
    futil.log("Disconnecting from MCP server...")
    mcp_client_instance.disconnect()
    mcp_client_instance = None
    futil.log("[OK] MCP Integration stopped")
  else:
    futil.log("MCP Integration was not connected")


# Note: UI command handlers removed - mcp_integration is now pure infrastructure
# If you need a manual connect/disconnect button, create a new command in commands/

