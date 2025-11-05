# Bug Fixes Applied to MCP Client

**Date**: November 5, 2025  
**Files Modified**: `lib/mcp_client.py`

## Summary

Applied two critical bug fixes from the updated `reverse_mcp.py` template to our Fusion 360 MCP client:

1. **Native Messaging Protocol Bug** (CRITICAL)
2. **Auto-Reconnection Feature** (Important for production)

---

## 1. Native Messaging Protocol Bug Fix

### The Problem

The original code tried to read JSON output from the native binary by:
- Reading bytes one at a time
- Searching for the `{` character to find where JSON starts
- Attempting to parse partial JSON strings

This approach **violated the Chrome Native Messaging protocol**, which requires:
1. Read exactly 4 bytes (little-endian uint32) = message length
2. Read exactly that many bytes = JSON payload

### The Fix

Replaced the byte-by-byte search with proper protocol handling:

```python
# Step 1: Read the 4-byte length prefix (little-endian uint32)
length_bytes = b""
while len(length_bytes) < 4 and time.time() - start_time < timeout:
    chunk = proc.stdout.read(4 - len(length_bytes))
    if not chunk:
        time.sleep(0.01)
        continue
    length_bytes += chunk

# Convert little-endian bytes to int
message_length = struct.unpack('<I', length_bytes)[0]

# Step 2: Read exactly message_length bytes of JSON
json_bytes = b""
while len(json_bytes) < message_length and time.time() - start_time < timeout:
    chunk = proc.stdout.read(message_length - len(json_bytes))
    if not chunk:
        time.sleep(0.01)
        continue
    json_bytes += chunk

# Step 3: Decode and parse the JSON
json_data = json.loads(json_bytes.decode('utf-8'))
```

### Impact

- **Before**: Unreliable connection, could read garbage data, intermittent failures
- **After**: Reliable connection following proper Chrome Native Messaging protocol

---

## 2. Auto-Reconnection Feature

### The Problem

If the MCP server restarted or the network connection dropped, the Fusion 360 add-in would:
- Lose connection permanently
- Require manual reload of the add-in
- Stop responding to AI commands

This is **critical for the Autodesk demo** where we can't have the connection fail mid-presentation!

### The Fix

Added comprehensive auto-reconnection with exponential backoff:

#### New Architecture

```
connect(enable_auto_reconnect=True)
  └─> _connection_worker_with_reconnect() [background thread]
       └─> while not stopped:
            ├─> _attempt_connection()
            │    ├─> Find manifest
            │    ├─> Discover endpoint
            │    ├─> Connect SSE
            │    ├─> Register tool
            │    └─> return True/False
            │
            ├─> _listen_for_calls() [blocks until disconnect]
            │    └─> Check connection health every 1 second
            │         └─> Return if SSE thread dies
            │
            └─> If connection lost:
                 ├─> Calculate exponential backoff delay
                 ├─> Wait: 2s, 4s, 8s, 16s, 32s, 60s (max)
                 └─> Retry connection
```

#### Key Features

1. **Exponential Backoff**: Retry delays increase: 2s → 4s → 8s → 16s → 32s → 60s (max)
2. **Connection Health Monitoring**: Checks SSE reader thread every second
3. **Automatic Re-registration**: Tool is automatically re-registered after reconnection
4. **Graceful Shutdown**: Respects `stop_event` for clean disconnection
5. **Retry Forever**: Keeps trying until manually stopped (perfect for long-running add-ins)

#### New API

```python
# Auto-reconnect enabled (default)
client.connect(enable_auto_reconnect=True)

# Single connection attempt (old behavior)
client.connect(enable_auto_reconnect=False)
```

### Impact

- **Before**: Connection loss = permanent failure, manual reload required
- **After**: Connection loss = automatic reconnection with backoff, no manual intervention

---

## 3. Enhanced Error Reporting

While fixing the bugs, also improved error reporting in `_listen_for_calls()`:

```python
except Exception as e:
    self.log(f"ERROR: Tool handler failed: {e}")
    import traceback
    self.log(traceback.format_exc())
    error_result = {
        "content": [{
            "type": "text",
            "text": f"Error: {str(e)}\n\n{traceback.format_exc()}"
        }],
        "isError": True
    }
    self._send_tool_reply(call_id, error_result)
```

Now when a tool handler crashes, the AI receives:
- The error message
- Full Python traceback
- Context about what failed

---

## New Tool-Calling Capability in reverse_mcp.py

### Discovery

The updated `reverse_mcp.py` template now includes a `call_mcp_tool()` function that allows remote tools to call **other** MCP tools on the server!

### How It Works

```python
def call_mcp_tool(sse_connection: Dict[str, Any], server_url: str, auth_header: str, 
                  tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Call another MCP tool on the server.
    
    This function demonstrates how to call other MCP tools from within your remote tool handler.
    It uses the existing SSE connection and JSON-RPC infrastructure to make tool calls.
    """
    tool_call_params = {
        "name": tool_name,
        "arguments": arguments
    }
    
    response = send_this_jsonrpc_request_and_wait_for_this_response(
        sse_connection,
        server_url,
        auth_header,
        "tools/call",
        tool_call_params,
        timeout_seconds=30.0  # Longer timeout for tool calls
    )
    
    return response
```

### Example Usage

```python
# From within a remote tool handler (e.g., fusion360 tool):

# Call sqlite tool to store data
result = call_mcp_tool(
    sse_connection,
    server_url,
    auth_header,
    "sqlite",
    {"input": {"sql": "INSERT INTO designs VALUES (?)", "params": ["my_design"]}}
)

# Call browser tool to open documentation
result = call_mcp_tool(
    sse_connection,
    server_url,
    auth_header,
    "browser",
    {"input": {"operation": "navigate", "url": "https://help.autodesk.com/..."}}
)

# Call user tool to show popup
result = call_mcp_tool(
    sse_connection,
    server_url,
    auth_header,
    "user",
    {"input": {"operation": "show_popup", "html": "<h1>Design Complete!</h1>"}}
)
```

### Future Python Execution Feature

**User's Request**: Add ability to run arbitrary Python code from within Fusion 360 context.

**How This Would Work**:

1. **AI sends Python code** via `fusion360` tool
2. **Fusion 360 executes it** in its Python environment (with access to `adsk` modules)
3. **Python code can call other MCP tools** using `call_mcp_tool()`:
   - Store results in SQLite database
   - Show popups to user
   - Open browser tabs with documentation
   - Call other remote tools

**Example Flow**:

```python
# AI sends this to fusion360 tool:
{
    "api_path": "execute_python",
    "code": """
import adsk.core
import adsk.fusion

# Create a sketch
design = adsk.fusion.Design.cast(app.activeProduct)
sketch = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)

# Add a circle
sketch.sketchCurves.sketchCircles.addByCenterRadius(sketch.originPoint, 5)

# Store result in database via MCP
result = call_mcp_tool(
    sse_connection,
    server_url,
    auth_header,
    "sqlite",
    {"input": {"sql": "INSERT INTO sketches (name, type) VALUES (?, ?)", 
               "params": [sketch.name, "circle"]}}
)

# Show success popup
call_mcp_tool(
    sse_connection,
    server_url,
    auth_header,
    "user",
    {"input": {"operation": "show_popup", 
               "html": "<h1>Circle created!</h1><p>Stored in database</p>"}}
)

return {"sketch_name": sketch.name, "circle_radius": 5}
"""
}
```

**Benefits**:

- **Full Fusion 360 API access** from arbitrary Python code
- **MCP tool integration** for data storage, UI, browser control, etc.
- **AI can write complex workflows** that span multiple tools
- **No need to pre-define every possible operation** in the generic API handler

**Implementation Notes** (for later):

1. Add `execute_python` special command to `fusion_tool_handler`
2. Pass `sse_connection`, `server_url`, `auth_header` to execution context
3. Provide `call_mcp_tool` function in execution globals
4. Execute code using `exec()` with proper error handling
5. Return result to AI

---

## Testing Notes

### Before Deploying

1. **Test native messaging fix**: Restart MCP server, reload add-in, verify connection
2. **Test auto-reconnect**: Kill MCP server, wait for reconnect, verify tool still works
3. **Test exponential backoff**: Monitor logs during reconnection attempts
4. **Test graceful shutdown**: Stop add-in, verify no hanging threads

### For Autodesk Demo

- Auto-reconnect ensures demo won't fail if network hiccups
- Native messaging fix ensures reliable initial connection
- Enhanced error reporting helps debug any issues during demo

---

## Files Modified

- `lib/mcp_client.py`:
  - Fixed `_discover_server_endpoint()` to use proper Chrome Native Messaging protocol
  - Added `retry_count` and `max_retry_delay` to `__init__()`
  - Refactored `connect()` to support auto-reconnect
  - Added `_connection_worker_with_reconnect()` for background reconnection
  - Added `_attempt_connection()` for single connection attempts
  - Enhanced `_listen_for_calls()` with connection health monitoring
  - Improved error reporting with full tracebacks

## Files Analyzed (Not Modified)

- `python_mcp/server/reverse_mcp.py`:
  - Identified new `call_mcp_tool()` function
  - Documented for future Python execution feature

---

## Status

✅ **Native Messaging Bug**: FIXED  
✅ **Auto-Reconnection**: IMPLEMENTED  
✅ **Enhanced Error Reporting**: ADDED  
📋 **Python Execution Feature**: DOCUMENTED (not implemented yet)

Ready for testing and Autodesk demo!

