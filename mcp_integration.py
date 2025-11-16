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
import adsk.fusion
import os
import json
import queue
import threading
import time
from .lib import fusionAddInUtils as futil
from .lib import mcp_client
from . import config

app = adsk.core.Application.get()
ui = app.userInterface

# Global MCP client instance (maintains connection throughout add-in lifecycle)
mcp_client_instance = None

# Global reference to the actual handler implementation
# Set by _create_mcp_client() so _process_fusion_api_work_queue() can call it
_fusion_tool_handler_impl_ref = None

# Python execution sessions (module-level for true inline access)
# Each session stores variables that persist across executions
python_sessions = {}

# ============================================
# THREAD-SAFE API CALL INFRASTRUCTURE
# ============================================

# Queue for daemon threads to request Fusion API work
fusion_api_work_queue = queue.Queue()

# Custom event for main thread processing
fusion_api_custom_event = None
fusion_api_event_handler = None

# Timer thread for firing events
fusion_api_timer_thread = None
fusion_api_stop_event = threading.Event()

# Reentrant call guard
fusion_api_processing_lock = threading.Lock()

# ============================================
# THREAD-SAFE LOGGING INFRASTRUCTURE
# ============================================

# Log buffer - ALL threads append here (thread-safe)
fusion_log_buffer = []
fusion_log_buffer_lock = threading.Lock()


def log(message: str, level=None):
  """
  Thread-safe logging - can be called from ANY thread.
  
  If called from main thread: logs immediately (for real-time debugging)
  If called from daemon thread: buffers for main thread to flush
  
  Args:
    message: The message to log
    level: Optional adsk.core.LogLevels (e.g., ErrorLogLevel, WarningLogLevel)
  """
  # If we're on main thread, log immediately for real-time visibility
  if threading.current_thread() == threading.main_thread():
    if level:
      futil.log(message, level)
    else:
      futil.log(message)
  else:
    # Daemon thread - buffer for main thread to flush
    fusion_log_buffer.append((message, level))


def _flush_log_buffer():
  """
  Flush queued log messages - ONLY called from main thread.
  
  This is the ONLY place in the entire codebase that calls futil.log()
  """
  global fusion_log_buffer
  
  if not fusion_log_buffer:
    return
  
  # Get all messages atomically
  with fusion_log_buffer_lock:
    messages = fusion_log_buffer[:]
    fusion_log_buffer.clear()
  
  # Log them all (we're on main thread - safe!)
  for message, level in messages:
    if level:
      futil.log(message, level)
    else:
      futil.log(message)


def _create_mcp_client():
  """
  Create and configure the MCP client instance.
  
  Returns:
    Configured MCPClient instance ready to connect
  """
  tool_name = "fusion360"
  tool_readme = "Autodesk Fusion 360 - Use this to perform CAD/CAM/CAE/ECAD and 3D-Printing/Milling"
  tool_description = """
Fusion 360 MCP Tool - UNLIMITED API Access + Python Execution + MCP Integration

⚠️ MAXIMUM ACCESS MODE ⚠️
This tool gives AI COMPLETE, UNRESTRICTED access to:
- Entire Fusion 360 API (CAD, CAM, CAE, Drawing)
- Python execution with TRUE INLINE access to everything
- All other MCP tools (SQLite, browser, user, etc.)
- File system, network, system commands
- All loaded add-ins and global state

## Three Powerful Capabilities

### 1. Generic API Calls (Simple Operations)

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

### 2. Python Execution (Complex Workflows)

Execute arbitrary Python code with MAXIMUM access to Fusion 360 environment:

{
  "operation": "execute_python",
  "code": "import adsk.core\\nprint(f'Fusion version: {app.version}')",
  "session_id": "my_session",
  "persistent": true
}

Python code has access to:
- `app` - Fusion Application object
- `ui` - User interface object
- `adsk.core`, `adsk.fusion`, `adsk.cam` - Full Fusion API
- `mcp` - MCP bridge for calling other tools
- `fusion_context` - Session context dict
- ALL module globals - true inline execution!

Example - Create parametric bracket with database storage:
{
  "operation": "execute_python",
  "code": "import adsk.core\\nimport adsk.fusion\\n\\n# Create sketch\\nsketch = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)\\nlines = sketch.sketchCurves.sketchLines\\nlines.addTwoPointRectangle(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(10,8,0))\\n\\n# Store in database\\nmcp.call('sqlite', {'input': {'sql': 'INSERT INTO designs (name) VALUES (?)', 'params': [sketch.name], 'tool_unlock_token': '29e63eb5'}})\\n\\nprint(f'Created {sketch.name}')"
}

### 3. MCP Tool Calling (Integration)

Call other MCP tools from Fusion 360:

{
  "operation": "call_tool",
  "tool_name": "sqlite",
  "arguments": {
    "input": {
      "sql": "SELECT * FROM designs",
      "tool_unlock_token": "29e63eb5"
    }
  }
}

Available MCP tools: sqlite, browser, user, python, system, and more!

## Script Management

Save and reuse Python workflows:
- `save_script` - Save code to file
- `load_script` - Load saved code
- `list_scripts` - List all scripts
- `delete_script` - Delete script

Scripts stored in: `<AuraFriday>/user_data/python_scripts/`

## Note

Fusion 360 must be running with the MCP-Link add-in active.
The add-in maintains a session context for stored objects across multiple calls.

⚠️ Python execution has FULL system access - use responsibly!
"""
  
  # Storage for intermediate results (for multi-step operations)
  fusion_context = {}
  
  def fusion_tool_handler(call_data):
    """
    THREAD-SAFE PROXY for Fusion API calls.
    
    This function can be called from ANY thread. If called from a daemon thread,
    it queues the work and waits for the main thread to process it.
    
    If called from the main thread, it executes directly.
    """
    current_thread = threading.current_thread()
    main_thread = threading.main_thread()
    
    # Check if we're already on main thread
    if current_thread == main_thread:
      # Already on main thread - execute directly
      return _fusion_tool_handler_impl(call_data)
    
    # We're on a daemon thread - queue the work for main thread
    result_queue = queue.Queue()
    
    work_item = {
      'call_data': call_data,
      'result_queue': result_queue
    }
    
    # Queue the work (thread-safe)
    fusion_api_work_queue.put(work_item)
    
    # IMMEDIATELY fire the CustomEvent to wake up main thread
    # This is THREAD-SAFE - just sends a message to Fusion
    try:
      app.fireCustomEvent('FusionAPIProcessorEvent')
    except Exception as e:
      log(f"ERROR firing CustomEvent: {e}", adsk.core.LogLevels.ErrorLogLevel)
    
    # Wait for main thread to process it
    # This blocks (sleeps) until result arrives - no CPU usage
    result = result_queue.get()
    
    return result
  
  
  def _fusion_tool_handler_impl(call_data):
    """
    ACTUAL implementation - MUST run on main thread.
    
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
      
      # Check for operation type (new multi-operation support)
      operation = arguments.get('operation')
      
      # Route to appropriate handler based on operation
      if operation == 'execute_python':
        return _handle_python_execution(arguments)
      elif operation == 'call_tool':
        # MCP tool calling
        tool_name = arguments.get('tool_name')
        tool_arguments = arguments.get('arguments', {})
        if not tool_name:
          return {
            "content": [{"type": "text", "text": "ERROR: 'tool_name' required for call_tool operation"}],
            "isError": True
          }
        result = mcp_client_instance.call_mcp_tool(tool_name, tool_arguments)
        return {
          "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
          "isError": False
        }
      elif operation == 'save_script':
        return _handle_save_script(arguments)
      elif operation == 'load_script':
        return _handle_load_script(arguments)
      elif operation == 'list_scripts':
        return _handle_list_scripts(arguments)
      elif operation == 'delete_script':
        return _handle_delete_script(arguments)
      
      # Default: Generic API call (backward compatible - no operation specified)
      api_path = arguments.get('api_path', '')
      args = arguments.get('args', [])
      kwargs = arguments.get('kwargs', {})
      store_as = arguments.get('store_as')
      return_properties = arguments.get('return_properties', [])
      
      # Handle special commands
      if api_path == 'get_pid':
        pid = os.getpid()
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
        return {
          "content": [{
            "type": "text",
            "text": f"Cleared {count} stored objects from context"
          }],
          "isError": False
        }
      
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
      
      # Extract return properties
      result_info = _extract_result_info(result, return_properties)
      
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
      
      log(f"ERROR in fusion_tool_handler: {e}", adsk.core.LogLevels.ErrorLogLevel)
      log(error_trace, adsk.core.LogLevels.ErrorLogLevel)
      
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
    log(f"[MCP] {message}")
  
  # Store reference to implementation at module level
  # so _process_fusion_api_work_queue() can call it
  global _fusion_tool_handler_impl_ref
  _fusion_tool_handler_impl_ref = _fusion_tool_handler_impl
  
  # Create and return the client
  return mcp_client.MCPClient(
    tool_name=tool_name,
    tool_description=tool_description,
    tool_readme=tool_readme,
    tool_handler=fusion_tool_handler,
    log_callback=log_callback
  )


def _get_scripts_directory():
  """
  Get the MCP server's python_scripts directory.
  
  Calculates path relative to native messaging binary:
  binary_path/../../user_data/python_scripts/
  
  Returns:
    Absolute path to scripts directory
  
  Raises:
    RuntimeError: If native binary path not available
  """
  global mcp_client_instance
  
  if not mcp_client_instance:
    raise RuntimeError("MCP client not initialized")
  
  if not hasattr(mcp_client_instance, 'native_binary_path'):
    raise RuntimeError("Native binary path not stored in MCP client")
  
  binary_path = mcp_client_instance.native_binary_path
  if not binary_path:
    raise RuntimeError("Native binary path is None")
  
  from pathlib import Path
  
  # Calculate: binary_path/../../user_data/python_scripts/
  aura_friday_root = Path(binary_path).parent.parent
  scripts_dir = aura_friday_root / "user_data" / "python_scripts"
  
  # Create directory if it doesn't exist
  scripts_dir.mkdir(parents=True, exist_ok=True)
  
  log(f"[MCP] Scripts directory: {scripts_dir}")
  
  return str(scripts_dir)


def _create_mcp_bridge():
  """
  Create MCP bridge for Python execution.
  
  Returns:
    mcp_bridge module with call() function
  """
  from .lib import mcp_bridge
  
  # Set the MCP client instance
  global mcp_client_instance
  mcp_bridge.set_mcp_client(mcp_client_instance)
  
  return mcp_bridge


def _handle_python_execution(arguments: dict) -> dict:
  """
  Execute arbitrary Python code with ABSOLUTE MAXIMUM access.
  
  Uses TRUE INLINE EXECUTION via exec(compile(code, "<ai-code>", "exec"), globals()).
  """
  import io
  import contextlib
  import traceback
  
  code = arguments.get('code')
  if not code:
    return {
      "content": [{"type": "text", "text": "ERROR: 'code' parameter required"}],
      "isError": True
    }
  
  session_id = arguments.get('session_id', 'default')
  persistent = arguments.get('persistent', True)
  
  # Capture stdout and stderr
  stdout_capture = io.StringIO()
  stderr_capture = io.StringIO()
  
  try:
    # Inject MCP bridge into REAL globals
    globals()['mcp'] = _create_mcp_bridge()
    
    # If persistent session, restore previous session variables
    if persistent and session_id in python_sessions:
      for key, value in python_sessions[session_id].items():
        globals()[key] = value
    
    # Execute with REAL globals - TRUE INLINE EXECUTION
    with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
      exec(compile(code, "<ai-code>", "exec"), globals())
    
    # Save session state if persistent
    if persistent:
      new_vars = {}
      for key, value in globals().items():
        if (not key.startswith('_') and 
            key not in ['app', 'ui', 'adsk', 'futil', 'config', 'mcp_client_instance', 
                        'fusion_context', 'python_sessions', 'mcp', 'os', 'json'] and
            not callable(value)):
          new_vars[key] = value
      
      python_sessions[session_id] = new_vars
    
    # Extract return value if AI set __return__
    return_value = globals().get('__return__', None)
    if '__return__' in globals():
      del globals()['__return__']
    
    return {
      "content": [{
        "type": "text",
        "text": json.dumps({
          "stdout": stdout_capture.getvalue(),
          "stderr": stderr_capture.getvalue(),
          "return_value": str(return_value) if return_value else None,
          "session_variables": list(python_sessions.get(session_id, {}).keys()) if persistent else [],
          "success": True
        }, indent=2)
      }],
      "isError": False
    }
    
  except Exception as e:
    error_trace = traceback.format_exc()
    
    return {
      "content": [{
        "type": "text",
        "text": json.dumps({
          "stdout": stdout_capture.getvalue(),
          "stderr": stderr_capture.getvalue(),
          "error": str(e),
          "traceback": error_trace,
          "success": False
        }, indent=2)
      }],
      "isError": True
    }


def _handle_save_script(arguments: dict) -> dict:
  """Save Python script to file."""
  filename = arguments.get('filename')
  code = arguments.get('code')
  
  if not filename or not code:
    return {
      "content": [{"type": "text", "text": "ERROR: 'filename' and 'code' required"}],
      "isError": True
    }
  
  try:
    scripts_dir = _get_scripts_directory()
    script_path = os.path.join(scripts_dir, filename)
    
    with open(script_path, 'w', encoding='utf-8') as f:
      f.write(code)
    
    log(f"[MCP] Saved script: {script_path}")
    
    return {
      "content": [{"type": "text", "text": json.dumps({
        "filename": filename,
        "path": script_path,
        "size": len(code),
        "saved": True
      }, indent=2)}],
      "isError": False
    }
  except Exception as e:
    return {
      "content": [{"type": "text", "text": f"ERROR saving script: {str(e)}"}],
      "isError": True
    }


def _handle_load_script(arguments: dict) -> dict:
  """Load Python script from file."""
  filename = arguments.get('filename')
  
  if not filename:
    return {
      "content": [{"type": "text", "text": "ERROR: 'filename' required"}],
      "isError": True
    }
  
  try:
    scripts_dir = _get_scripts_directory()
    script_path = os.path.join(scripts_dir, filename)
    
    if not os.path.exists(script_path):
      return {
        "content": [{"type": "text", "text": f"ERROR: Script not found: {filename}"}],
        "isError": True
      }
    
    with open(script_path, 'r', encoding='utf-8') as f:
      code = f.read()
    
    log(f"[MCP] Loaded script: {script_path}")
    
    return {
      "content": [{"type": "text", "text": json.dumps({
        "filename": filename,
        "code": code,
        "size": len(code),
        "path": script_path
      }, indent=2)}],
      "isError": False
    }
  except Exception as e:
    return {
      "content": [{"type": "text", "text": f"ERROR loading script: {str(e)}"}],
      "isError": True
    }


def _handle_list_scripts(arguments: dict) -> dict:
  """List all saved Python scripts."""
  try:
    scripts_dir = _get_scripts_directory()
    
    scripts = []
    for filename in os.listdir(scripts_dir):
      if filename.endswith('.py'):
        script_path = os.path.join(scripts_dir, filename)
        stat = os.stat(script_path)
        scripts.append({
          "filename": filename,
          "size": stat.st_size,
          "modified": stat.st_mtime,
          "path": script_path
        })
    
    scripts.sort(key=lambda x: x["filename"])
    
    log(f"[MCP] Listed {len(scripts)} scripts")
    
    return {
      "content": [{"type": "text", "text": json.dumps({
        "scripts": scripts,
        "count": len(scripts),
        "directory": scripts_dir
      }, indent=2)}],
      "isError": False
    }
  except Exception as e:
    return {
      "content": [{"type": "text", "text": f"ERROR listing scripts: {str(e)}"}],
      "isError": True
    }


def _handle_delete_script(arguments: dict) -> dict:
  """Delete a saved Python script."""
  filename = arguments.get('filename')
  
  if not filename:
    return {
      "content": [{"type": "text", "text": "ERROR: 'filename' required"}],
      "isError": True
    }
  
  try:
    scripts_dir = _get_scripts_directory()
    script_path = os.path.join(scripts_dir, filename)
    
    if not os.path.exists(script_path):
      return {
        "content": [{"type": "text", "text": f"ERROR: Script not found: {filename}"}],
        "isError": True
      }
    
    os.remove(script_path)
    
    log(f"[MCP] Deleted script: {script_path}")
    
    return {
      "content": [{"type": "text", "text": json.dumps({
        "filename": filename,
        "deleted": True
      }, indent=2)}],
      "isError": False
    }
  except Exception as e:
    return {
      "content": [{"type": "text", "text": f"ERROR deleting script: {str(e)}"}],
      "isError": True
    }


def _process_fusion_api_work_queue():
  """
  Process queued Fusion API work - RUNS ON MAIN THREAD.
  
  Called by Fusion when CustomEvent fires. This is where all the actual
  Fusion API calls happen, safely on the main thread.
  
  Uses a lock to prevent reentrant calls (if CustomEvent fires while we're already processing).
  """
  # Try to acquire lock - if already processing, skip this call
  if not fusion_api_processing_lock.acquire(blocking=False):
    return
  
  try:
    # Flush any queued log messages first
    _flush_log_buffer()
    
    # Process all pending work (but don't hog the main thread)
    max_per_batch = 10
    processed = 0
    
    while processed < max_per_batch:
      try:
        work_item = fusion_api_work_queue.get_nowait()
      except queue.Empty:
        break
      
      call_data = work_item['call_data']
      result_queue = work_item['result_queue']
      
      # CRITICAL: Always return a result, even if processing fails
      try:
        # Execute the actual work on main thread (SAFE!)
        result = _fusion_tool_handler_impl_ref(call_data)
      except Exception as e:
        # If processing fails, return an error result
        import traceback
        error_trace = traceback.format_exc()
        log(f"ERROR during processing: {e}", adsk.core.LogLevels.ErrorLogLevel)
        log(error_trace, adsk.core.LogLevels.ErrorLogLevel)
        result = {
          "content": [{
            "type": "text",
            "text": f"FATAL ERROR in work queue processor:\n{error_trace}"
          }],
          "isError": True
        }
      
      # Return result to waiting thread (ALWAYS happens, even on error)
      result_queue.put(result)
      
      processed += 1
    
    # Flush logs again after processing work
    _flush_log_buffer()
  
  finally:
    # Always release the lock
    fusion_api_processing_lock.release()


def _timer_loop():
  """
  Timer thread that fires custom events when work is queued.
  
  This runs on a daemon thread but NEVER calls Fusion API directly.
  It only tells Fusion to fire an event, which Fusion processes on its main thread.
  
  Fires event every 1 second max as a keepalive/fallback, and immediately when work detected.
  """
  event_id = 'FusionAPIProcessorEvent'
  last_fire_time = 0
  
  while not fusion_api_stop_event.is_set():
    try:
      current_time = time.time()
      should_fire = False
      
      # Check if there's work to do (fast - just checks queue size)
      if not fusion_api_work_queue.empty():
        should_fire = True
      # Also fire every 1 second as keepalive (to flush logs, etc)
      elif current_time - last_fire_time >= 1.0:
        should_fire = True
      
      if should_fire:
        # Tell Fusion to fire our custom event
        # This is THREAD-SAFE - just sends a message to Fusion
        # Fusion will call our handler on ITS main thread
        app.fireCustomEvent(event_id)
        last_fire_time = current_time
    except Exception as e:
      log(f"Timer loop error: {e}", adsk.core.LogLevels.ErrorLogLevel)
    
    # Check every 50ms for good responsiveness
    time.sleep(0.05)


def _setup_fusion_api_processor():
  """
  Set up the main thread processor for queued API calls.
  
  Creates a CustomEvent that Fusion will call on its main thread,
  and starts a timer thread to fire that event when work is queued.
  """
  global fusion_api_custom_event, fusion_api_event_handler, fusion_api_timer_thread
  
  # Register custom event with Fusion
  event_id = 'FusionAPIProcessorEvent'
  fusion_api_custom_event = app.registerCustomEvent(event_id)
  
  # Create event handler that processes the queue
  class FusionAPIEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
      super().__init__()
    
    def notify(self, args):
      # THIS RUNS ON FUSION'S MAIN THREAD!
      _process_fusion_api_work_queue()
  
  # Register the handler
  fusion_api_event_handler = FusionAPIEventHandler()
  fusion_api_custom_event.add(fusion_api_event_handler)
  
  # Start timer thread to fire events when work is queued
  fusion_api_timer_thread = threading.Thread(target=_timer_loop, daemon=True)
  fusion_api_timer_thread.start()


def _auto_connect():
  """
  Automatically connect to MCP server (called during startup if MCP_AUTO_CONNECT is True).
  Does not show message boxes - logs only.
  """
  global mcp_client_instance
  
  if mcp_client_instance and mcp_client_instance.is_connected:
    log("Already connected to MCP server")
    return
  
  log("Starting auto-connect to MCP server...")
  
  # Create and connect
  mcp_client_instance = _create_mcp_client()
  success = mcp_client_instance.connect()
  
  if success:
    log("[SUCCESS] Auto-connected to MCP server!")
  else:
    log("Auto-connect failed - check logs above for details", adsk.core.LogLevels.WarningLogLevel)
    mcp_client_instance = None


def start():
  """Initialize MCP integration when add-in starts."""
  log("MCP Integration starting...")
  
  # Set up thread-safe API processor FIRST
  try:
    _setup_fusion_api_processor()
  except Exception as e:
    log(f"ERROR: Failed to setup API processor: {e}", adsk.core.LogLevels.ErrorLogLevel)
    import traceback
    log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    return
  
  # Auto-connect to MCP server (no UI button - this is infrastructure)
  if config.MCP_AUTO_CONNECT:
    try:
      _auto_connect()
      log("MCP Integration started successfully")
    except Exception as e:
      log(f"ERROR: Auto-connect failed: {e}", adsk.core.LogLevels.ErrorLogLevel)
      import traceback
      log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
  else:
    log("MCP_AUTO_CONNECT is False - MCP integration disabled")
    log("Set MCP_AUTO_CONNECT = True in config.py to enable")
  
  # Flush initial logs
  _flush_log_buffer()


def stop():
  """Cleanup when add-in stops."""
  global mcp_client_instance, fusion_api_custom_event, fusion_api_event_handler, fusion_api_timer_thread
  
  log("MCP Integration stopping...")
  
  # Stop the timer thread
  fusion_api_stop_event.set()
  
  # Wait for timer thread to actually stop
  if fusion_api_timer_thread and fusion_api_timer_thread.is_alive():
    fusion_api_timer_thread.join(timeout=3.0)
    if fusion_api_timer_thread.is_alive():
      log("WARNING: Timer thread did not stop in time", adsk.core.LogLevels.WarningLogLevel)
  
  # Disconnect MCP client if connected
  if mcp_client_instance:
    if mcp_client_instance.is_connected:
      mcp_client_instance.disconnect()
    mcp_client_instance = None
  
  # Clean up event handler
  if fusion_api_custom_event and fusion_api_event_handler:
    try:
      fusion_api_custom_event.remove(fusion_api_event_handler)
    except Exception as e:
      log(f"Error removing event handler: {e}", adsk.core.LogLevels.WarningLogLevel)
    fusion_api_event_handler = None
    fusion_api_custom_event = None
  
  log("MCP Integration stopped")
  
  # Flush final logs
  _flush_log_buffer()


# Note: UI command handlers removed - mcp_integration is now pure infrastructure
# If you need a manual connect/disconnect button, create a new command in commands/

