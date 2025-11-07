# Fusion 360 + Python Integration Plan V3 FINAL
## "Absolute Maximum Access - True Inline Execution"

**Date**: November 5, 2025  
**Philosophy**: TRUE inline execution - behaves exactly as if code was written directly in the module  
**Goal**: Give AI indistinguishable-from-inline access to Fusion 360 environment

---

## 🔓 The Correct Approach: True Inline Execution

### ❌ WRONG (V2): `globals().copy()`
```python
exec_globals = globals().copy()  # Creates a SHADOW COPY
exec_globals['mcp'] = mcp_bridge
exec(code, exec_globals)  # Changes don't affect real globals
```

**Problems**:
- Creates shadow copy - mutations don't persist
- Can't modify real global state
- Some Python objects won't survive the copy
- Not true "inline" behavior

### ✅ CORRECT (V3): Direct `globals()` Reference
```python
# At module level (where fusion_tool_handler is defined):
exec(compile(code, "<ai-code>", "exec"), globals())
```

**Benefits**:
- TRUE inline execution - indistinguishable from code written directly in module
- All mutations persist in real globals
- Full access to everything
- Proper stack traces with `compile()`
- No shadow copies or restrictions

---

## Implementation: Maximum Access Python Execution

### File: `mcp_integration.py`

**Add at module level** (for session persistence):
```python
# Python execution sessions (module-level for true inline access)
python_sessions = {}
```

**The Handler**:
```python
def _handle_python_execution(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute arbitrary Python code with ABSOLUTE MAXIMUM access.
    
    Uses TRUE INLINE EXECUTION - behaves exactly as if code was written
    directly in this module. All mutations persist in real globals.
    
    Philosophy: Give AI indistinguishable-from-inline access to everything.
    
    The executed code has REAL access to:
    - ALL module globals (app, ui, adsk, fusion_context, etc.)
    - ALL imported modules
    - ALL loaded Fusion 360 add-ins
    - The MCP bridge for calling other tools
    - Can mutate global state directly
    - Can define new globals that persist
    
    Args:
        arguments: {
            "code": "Python code to execute",
            "session_id": "optional session identifier",
            "persistent": true/false (default: true)
        }
    
    Returns:
        Execution results with stdout, stderr, and return value
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
        # Inject MCP bridge into REAL globals (not a copy)
        globals()['mcp'] = _create_mcp_bridge()
        
        # If persistent session, restore previous session variables
        if persistent and session_id in python_sessions:
            for key, value in python_sessions[session_id].items():
                globals()[key] = value
        
        # Execute with REAL globals - TRUE INLINE EXECUTION
        # compile() gives us proper tracebacks with "<ai-code>" filename
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(compile(code, "<ai-code>", "exec"), globals())
        
        # Save session state if persistent
        # Only save NEW variables created by AI code
        if persistent:
            # Get list of keys that existed before execution
            original_keys = set(python_sessions.get(session_id, {}).keys())
            
            # Find new variables created by AI
            new_vars = {}
            for key, value in globals().items():
                # Skip private, builtins, and our infrastructure
                if (not key.startswith('_') and 
                    key not in ['app', 'ui', 'adsk', 'futil', 'config', 'mcp_client_instance', 
                                'fusion_context', 'python_sessions', 'mcp'] and
                    callable(value) == False):  # Skip functions
                    new_vars[key] = value
            
            python_sessions[session_id] = new_vars
        
        # Extract return value if AI set __return__
        return_value = globals().get('__return__', None)
        if '__return__' in globals():
            del globals()['__return__']  # Clean up
        
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
        # Get full traceback with proper context
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
```

---

## What This Enables

### 1. True Global Mutation
```python
fusion360.execute_python({
  "code": """
# This ACTUALLY modifies the real global
fusion_context['my_data'] = {'design': 'bracket_v2'}

# This ACTUALLY creates a new global variable
my_persistent_counter = 42

# Next execution in same session will see these changes!
"""
})
```

### 2. Define Functions That Persist
```python
fusion360.execute_python({
  "code": """
def create_mounting_plate(width, height):
    sketch = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(width, height, 0)
    )
    return sketch

# This function is now available in subsequent executions!
"""
})

# Later, in another execution:
fusion360.execute_python({
  "code": """
# Call the function we defined earlier
plate = create_mounting_plate(10, 8)
print(f"Created: {plate.name}")
"""
})
```

### 3. Import and Persist Modules
```python
fusion360.execute_python({
  "code": """
import math
import datetime

# These imports persist for the session
# Can use them in subsequent executions
"""
})
```

### 4. Access Everything - No Restrictions
```python
fusion360.execute_python({
  "code": """
# Access other loaded add-ins
import sys
for name in sys.modules:
    if 'addin' in name.lower():
        print(f"Found add-in: {name}")

# Modify MCP client state
print(f"MCP connected: {mcp_client_instance.is_connected}")

# Access Fusion app directly
print(f"Fusion version: {app.version}")

# Call other MCP tools
mcp.call("sqlite", {"input": {"sql": "SELECT 1"}})

# Everything works exactly like inline code!
"""
})
```

---

## MCP Bridge Implementation

### File: `lib/mcp_bridge.py` (new file)

```python
"""
MCP Bridge for Fusion 360 Python Execution

Provides mcp.call() function for calling other MCP tools from within
Python code executed in Fusion 360 context.
"""

from typing import Dict, Any, Optional

# Global reference to MCP client (set by mcp_integration.py)
_mcp_client = None

def set_mcp_client(client):
    """Set the MCP client instance for tool calling."""
    global _mcp_client
    _mcp_client = client

def call(tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Call another MCP tool.
    
    Args:
        tool_name: Name of the tool to call (e.g., "sqlite", "browser", "user")
        arguments: Arguments to pass to the tool
        
    Returns:
        Tool response dictionary
        
    Example:
        # Store data in SQLite
        result = mcp.call("sqlite", {
            "input": {
                "sql": "INSERT INTO designs (name) VALUES (?)",
                "params": ["my_design"],
                "tool_unlock_token": "29e63eb5"
            }
        })
        
        # Show popup
        mcp.call("user", {
            "input": {
                "operation": "show_popup",
                "html": "<h1>Success!</h1>",
                "tool_unlock_token": "1d9bf6a0"
            }
        })
    """
    if not _mcp_client:
        raise RuntimeError("MCP client not initialized - cannot call MCP tools")
    
    return _mcp_client.call_mcp_tool(tool_name, arguments)
```

### File: `mcp_integration.py` - Create Bridge

```python
def _create_mcp_bridge():
    """
    Create MCP bridge for Python execution.
    
    Returns a module-like object with call() method.
    """
    from .lib import mcp_bridge
    
    # Set the MCP client instance
    global mcp_client_instance
    mcp_bridge.set_mcp_client(mcp_client_instance)
    
    return mcp_bridge
```

---

## Script Storage Implementation

### File: `lib/mcp_client.py` - Store Binary Path

```python
def _discover_server_endpoint(self, manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Run the native binary to discover the server endpoint.
    
    ALSO stores the binary path for later use (script storage location).
    """
    import subprocess
    import struct
    
    binary_path = manifest.get('path')
    if not binary_path or not Path(binary_path).exists():
        return None
    
    # STORE the binary path for script directory calculation
    self.native_binary_path = str(binary_path)
    
    self.log(f"Running native binary: {binary_path}")
    self.log("[DEBUG] Native messaging protocol uses 4-byte length prefix (little-endian uint32)")
    
    # ... rest of discovery code (already fixed with proper protocol) ...
```

### File: `mcp_integration.py` - Script Directory

```python
def _get_scripts_directory():
    """
    Get the MCP server's python_scripts directory.
    
    Calculates path relative to native messaging binary:
    binary_path/../../user_data/python_scripts/
    
    Example:
    - Binary: C:/Users/user/AppData/Local/AuraFriday/bin/native_messaging.exe
    - Scripts: C:/Users/user/AppData/Local/AuraFriday/user_data/python_scripts/
    
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
    # Example: C:/path/to/AuraFriday/bin/native_messaging.exe
    #       -> C:/path/to/AuraFriday/bin
    #       -> C:/path/to/AuraFriday
    #       -> C:/path/to/AuraFriday/user_data/python_scripts
    aura_friday_root = Path(binary_path).parent.parent
    scripts_dir = aura_friday_root / "user_data" / "python_scripts"
    
    # Create directory if it doesn't exist
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    futil.log(f"[MCP] Scripts directory: {scripts_dir}")
    
    return str(scripts_dir)
```

---

## Complete Implementation Checklist

### Phase 1: MCP Tool Calling ✓
- [x] Add `call_mcp_tool()` to `MCPClient` class
- [x] Store `sse_connection`, `server_url`, `auth_header` as instance variables
- [x] Test calling SQLite from Fusion
- [x] Test calling user popup from Fusion

### Phase 2: Python Execution (TRUE INLINE)
- [x] Store `native_binary_path` in `MCPClient._discover_server_endpoint()`
- [x] Create `lib/mcp_bridge.py` with `call()` function
- [x] Implement `_get_scripts_directory()` using binary path calculation
- [x] Implement `_handle_python_execution()` with **TRUE inline execution** (`exec(compile(code, "<ai-code>", "exec"), globals())`)
- [x] Add `python_sessions` dict at module level
- [x] Implement `_create_mcp_bridge()` function
- [x] Test simple Python execution
- [x] Test global mutation persistence
- [x] Test function definition persistence
- [x] Test Python calling MCP tools
- [x] Test proper error tracebacks

### Phase 3: Script Management
- [x] Implement `_handle_save_script()` using MCP scripts directory
- [x] Implement `_handle_load_script()`
- [x] Implement `_handle_list_scripts()`
- [x] Implement `_handle_delete_script()`
- [x] Test script persistence
- [x] Verify scripts appear in same location as `python` tool scripts

### Phase 4: Integration & Testing
- [x] Update `fusion_tool_handler` to route operations
- [x] Update tool registration with new operations
- [x] Test end-to-end workflows
- [x] Create demo script for Autodesk
- [x] Document all capabilities

---

## Key Differences from V2

| Aspect | V2 (Wrong) | V3 (Correct) |
|--------|-----------|--------------|
| **Execution** | `exec(code, globals().copy())` | `exec(compile(code, "<ai-code>", "exec"), globals())` |
| **Globals** | Shadow copy | Real reference |
| **Mutations** | Don't persist | Persist in real globals |
| **Behavior** | Sandboxed | True inline |
| **Tracebacks** | Generic | Proper with `<ai-code>` filename |
| **Functions** | Lost after execution | Persist if defined |
| **Imports** | Lost after execution | Persist in real globals |

---

## Example: Persistent Function Definitions

```python
# Execution 1: Define helper functions
fusion360.execute_python({
  "session_id": "cad_helpers",
  "code": """
import adsk.core
import adsk.fusion

def create_rectangle_sketch(width, height, plane=None):
    '''Create a rectangle sketch on specified plane'''
    if plane is None:
        plane = design.rootComponent.xYConstructionPlane
    
    sketch = design.rootComponent.sketches.add(plane)
    lines = sketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(width, height, 0)
    )
    return sketch

def add_mounting_holes(sketch, positions, diameter):
    '''Add circular holes at specified positions'''
    circles = sketch.sketchCurves.sketchCircles
    for x, y in positions:
        circles.addByCenterRadius(
            adsk.core.Point3D.create(x, y, 0),
            diameter / 2
        )
    return len(positions)

print("Helper functions defined!")
"""
})

# Execution 2: Use the functions we defined
fusion360.execute_python({
  "session_id": "cad_helpers",
  "code": """
# These functions are available because they're in real globals!
plate = create_rectangle_sketch(10, 8)
holes = add_mounting_holes(plate, [(1, 1), (9, 1), (1, 7), (9, 7)], 0.5)

# Store in database
mcp.call("sqlite", {
    "input": {
        "sql": "INSERT INTO designs (name, holes) VALUES (?, ?)",
        "params": [plate.name, holes],
        "tool_unlock_token": "29e63eb5"
    }
})

print(f"Created {plate.name} with {holes} holes")
"""
})
```

---
