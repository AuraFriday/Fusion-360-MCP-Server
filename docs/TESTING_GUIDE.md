# MCP-Link Fusion 360 Add-in - Testing Guide

## Overview

This guide explains how to test the MCP-Link add-in with comprehensive logging to diagnose connection issues.

## What We've Added

### 1. Debug Flags in `config.py`

```python
# General debug mode (for all add-in features)
DEBUG = True

# MCP-specific debug mode (verbose MCP connection logs)
MCP_DEBUG = True

# Auto-connect on startup (connects automatically when add-in loads)
MCP_AUTO_CONNECT = True
```

### 2. Comprehensive Logging

The add-in now logs detailed information at every step:

- **Add-in lifecycle**: When run() and stop() are called
- **Command registration**: When the "Connect to MCP" button is created
- **Auto-connect**: Automatic connection attempts on startup
- **MCP connection flow**: All 7 steps of the connection process
- **Tool registration**: When Fusion 360 registers as a remote tool
- **Tool calls**: When AI sends commands to Fusion 360

All logs appear in Fusion 360's **TEXT COMMANDS** window.

## Testing Steps

### Step 1: Enable TEXT COMMANDS Window in Fusion 360

1. Open Fusion 360
2. Go to the menu: **View → Show Panel → Text Commands**
   - Or press **Ctrl+Shift+C** (Windows) or **Cmd+Shift+C** (Mac)
3. The TEXT COMMANDS window should appear at the bottom of the screen

### Step 2: Install/Reload the Add-in

1. In Fusion 360, open **Scripts and Add-Ins** (Shift+S)
2. Navigate to the **Add-Ins** tab
3. Click the **"+"** button and select the `MCP-Link-fusion-new` folder
4. Select "MCP-Link" from the list
5. Click **Run** (or check **Run on Startup** for automatic loading)
6. Click **Close**

### Step 3: Check Initial Logs

You should immediately see logs in the TEXT COMMANDS window:

```
============================================================
MCP-Link Add-in: run() called
DEBUG mode: True
MCP_DEBUG mode: True
MCP_AUTO_CONNECT: True
============================================================
============================================================
MCP-Link mcpConnect: start() called
============================================================
Creating 'Connect to MCP' button...
[OK] Button created and added to UI
MCP_AUTO_CONNECT is True - attempting auto-connect...
Starting auto-connect to MCP server...
============================================================
MCP Client Connection Starting
============================================================
Step 1: Finding native messaging manifest...
```

### Step 4: Watch the Connection Flow

If everything is working, you'll see:

```
[OK] Found manifest: C:\Users\...\AuraFriday\com.aurafriday.shim.json
Step 2: Reading manifest...
[OK] Manifest loaded
Step 3: Discovering MCP server endpoint...
[OK] Server configuration received
Step 4: Extracting server URL and auth...
[OK] Server URL: https://127-0-0-1.local.aurafriday.com:XXXXX/sse
Step 5: Connecting to SSE endpoint...
[OK] SSE Connected! Session ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Step 6: Checking for remote tool...
[OK] Remote tool found
Step 7: Registering fusion360 with MCP server...
============================================================
[SUCCESS] fusion360 registered successfully!
Listening for reverse tool calls in background...
============================================================
[SUCCESS] Auto-connected to MCP server!
[OK] MCP-Link Add-in started successfully
```

### Step 5: Check Server Logs

On your system, check the MCP server logs:

```powershell
# View last 100 lines, excluding ping messages
tail -100 C:\Users\cnd\AppData\Local\Temp\friday.log | grep -v ": ping"
```

You should see:
- SSE connection from Fusion 360
- Tools/list request
- Tools/call for registration
- Confirmation that "fusion360" tool was registered

## Troubleshooting

### Issue: No logs appear at all

**Problem**: The add-in isn't running.

**Solution**:
1. Check Scripts and Add-Ins dialog - is the add-in listed?
2. Try clicking "Stop" then "Run" again
3. Check for Python syntax errors in the TEXT COMMANDS window

### Issue: "ERROR: Could not find native messaging manifest"

**Problem**: The Aura Friday native messaging shim isn't installed.

**Solution**:
1. Verify the manifest exists: `C:\Users\cnd\AppData\Local\AuraFriday\com.aurafriday.shim.json`
2. If missing, reinstall Aura Friday MCP-Link server
3. Check that the path matches what's expected (see logs)

### Issue: "ERROR: Could not get configuration from native binary"

**Problem**: The MCP server isn't running.

**Solution**:
1. Start the Aura Friday MCP-Link server
2. Verify it's running by checking for the process
3. Check server logs for startup issues

### Issue: "ERROR: Could not connect to SSE endpoint"

**Problem**: Network/SSL issues or server not accepting connections.

**Solution**:
1. Check that the server URL is correct in logs
2. Verify firewall isn't blocking the connection
3. Try accessing the URL in a browser (should show SSE stream)

### Issue: "ERROR: Server does not have 'remote' tool"

**Problem**: The MCP server doesn't support remote tool registration.

**Solution**:
1. Update to the latest version of the MCP server
2. Verify the server has the "remote" tool enabled

### Issue: Connection works but no tool calls received

**Problem**: Tool registered but AI isn't calling it.

**Solution**:
1. Verify tool registration: `grep "Successfully registered tool" server.log`
2. Try calling the tool manually via MCP client
3. Check that tool name is "fusion360" (case-sensitive)

## Manual Connection

If auto-connect is disabled or fails, you can connect manually:

1. Set `MCP_AUTO_CONNECT = False` in `config.py`
2. Reload the add-in
3. Click the **"Connect to MCP"** button in the toolbar
4. Watch the TEXT COMMANDS window for logs

## Testing Tool Calls

Once connected, test the tool from the AI:

```python
# Via MCP client or Cursor
result = mcp.call_tool("fusion360", {
  "command": "echo_test",
  "parameters": {
    "message": "Hello from AI!"
  }
})
```

You should see in Fusion's TEXT COMMANDS:

```
[MCP] [CALL] Reverse call received for fusion360
[TOOL CALL] Executing Fusion 360 command: echo_test
[TOOL CALL] Parameters: {'message': 'Hello from AI!'}
[MCP] [OK] Sent tools/reply for call_id xxxxx
```

## Viewing Logs Programmatically

You can also read the TEXT COMMANDS window content via the Fusion API:

```python
import adsk.core
app = adsk.core.Application.get()
ui = app.userInterface
textPalette = ui.palettes.itemById('TextCommands')
if textPalette:
    # The palette content is visible as text
    print(f"Palette visible: {textPalette.isVisible}")
```

## Debug Mode Control

To reduce log verbosity once it's working:

```python
# In config.py
DEBUG = True          # Keep general logging
MCP_DEBUG = False     # Disable verbose MCP logs
MCP_AUTO_CONNECT = True  # Keep auto-connect
```

This will still show important messages but hide the detailed connection steps.

## Next Steps

Once connection is verified:

1. Implement actual Fusion 360 commands in `fusion_tool_handler()`
2. Add command validation and error handling
3. Test with real CAD operations
4. Document available commands for AI agents

## Common Log Patterns

### Success Pattern
```
[OK] ... → [OK] ... → [OK] ... → [SUCCESS]
```

### Failure Pattern
```
[OK] ... → [OK] ... → ERROR: [specific error message]
```

Look for the last `[OK]` before the `ERROR:` to identify which step failed.

