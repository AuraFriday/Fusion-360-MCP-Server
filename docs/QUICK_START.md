# MCP-Link Fusion - Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Enable TEXT COMMANDS Window
```
Fusion → View → Show Panel → Text Commands
(or press Ctrl+Shift+C)
```

### Step 2: Load the Add-in
```
Fusion → Scripts and Add-Ins (Shift+S)
→ Add-Ins tab
→ Click "+" and select MCP-Link-fusion-new folder
→ Select "MCP-Link" and click "Run"
```

### Step 3: Watch for Success
```
TEXT COMMANDS window should show:
============================================================
[SUCCESS] fusion360 registered successfully!
Listening for reverse tool calls in background...
============================================================
```

## ✅ Verify It's Working

### Check Fusion Logs
Look for these lines in TEXT COMMANDS:
```
[OK] Found manifest: ...
[OK] Server URL: https://127-0-0-1.local.aurafriday.com:...
[OK] SSE Connected! Session ID: ...
[SUCCESS] fusion360 registered successfully!
```

### Check Server Logs
```powershell
tail -100 C:\Users\cnd\AppData\Local\Temp\friday.log | grep -v ": ping"
```

Should show:
```
Successfully registered tool: fusion360
```

## 🎯 Test the Tool

### From AI/Cursor:
```python
result = mcp.call_tool("fusion360", {
  "command": "echo_test",
  "parameters": {
    "message": "Hello from AI!"
  }
})
```

### Expected in TEXT COMMANDS:
```
[TOOL CALL] Executing Fusion 360 command: echo_test
[TOOL CALL] Parameters: {'message': 'Hello from AI!'}
```

## ⚙️ Configuration

### Auto-Connect (Default: ON)
```python
# config.py
MCP_AUTO_CONNECT = True   # Connects automatically on startup
```

### Debug Logging (Default: ON)
```python
# config.py
DEBUG = True              # General add-in logging
MCP_DEBUG = True          # Verbose MCP connection logs
```

## 🔧 Troubleshooting

### ❌ No logs at all
- Add-in not running → Reload via Scripts and Add-Ins

### ❌ "Could not find native messaging manifest"
- MCP server not installed → Install Aura Friday MCP-Link server

### ❌ "Could not get configuration from native binary"
- MCP server not running → Start the server

### ❌ "Could not connect to SSE endpoint"
- Network/firewall issue → Check server logs and firewall

## 📖 Full Documentation

- **TESTING_GUIDE.md**: Detailed testing and troubleshooting
- **IMPLEMENTATION_SUMMARY.md**: Technical details and architecture
- **readme.md**: Project overview and features

## 🎉 Next Steps

Once connected:
1. The `fusion360` tool is now available to AI agents
2. Commands are echoed back (not executed yet)
3. Implement actual Fusion commands in `fusion_tool_handler()`
4. Test with real CAD operations

## 💡 Pro Tips

- Keep TEXT COMMANDS window open during development
- Set `MCP_DEBUG = False` once it's working to reduce noise
- Use manual connect button for testing: set `MCP_AUTO_CONNECT = False`
- Check server logs when tool calls aren't received

## 📞 Common Commands

### Reload Add-in
```
Shift+S → Select "MCP-Link" → Stop → Run
```

### Check Connection Status
Look for "Listening for reverse tool calls in background..." in logs

### Manual Connect
Click "Connect to MCP" button in toolbar (if auto-connect disabled)

### View Server Logs
```powershell
tail -100 C:\Users\cnd\AppData\Local\Temp\friday.log | grep -v ": ping"
```

---

**Ready?** Load the add-in and watch the TEXT COMMANDS window! 🚀

