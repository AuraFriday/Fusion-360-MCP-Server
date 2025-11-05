# Testing Python Integration - Quick Start Guide

**Status**: Ready to test in Fusion 360!  
**Time**: ~15-30 minutes for full testing

---

## Prerequisites

1. ✅ Fusion 360 running
2. ✅ MCP-Link add-in loaded
3. ✅ MCP server running
4. ✅ Connection established (check Text Commands window)

---

## Test 1: Simple Python Execution

**Goal**: Verify basic Python execution works

```python
fusion360({
  "operation": "execute_python",
  "code": "print('Hello from Fusion 360!')\nprint(f'Version: {app.version}')"
})
```

**Expected Output**:
```json
{
  "stdout": "Hello from Fusion 360!\nVersion: 2.0.xxxx\n",
  "stderr": "",
  "return_value": null,
  "session_variables": [],
  "success": true
}
```

---

## Test 2: Access Fusion API

**Goal**: Verify access to Fusion objects

```python
fusion360({
  "operation": "execute_python",
  "code": "import adsk.core\nimport adsk.fusion\n\ndesign = adsk.fusion.Design.cast(app.activeProduct)\nprint(f'Design name: {design.rootComponent.name}')\nprint(f'Bodies: {design.rootComponent.bRepBodies.count}')"
})
```

**Expected**: Should print design name and body count

---

## Test 3: Create Geometry with Python

**Goal**: Verify we can create CAD geometry

```python
fusion360({
  "operation": "execute_python",
  "code": """import adsk.core
import adsk.fusion

design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

# Create sketch
sketch = root.sketches.add(root.xYConstructionPlane)

# Draw rectangle
lines = sketch.sketchCurves.sketchLines
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(5, 3, 0)
)

print(f'Created sketch: {sketch.name}')
print(f'Lines: {sketch.sketchCurves.sketchLines.count}')
"""
})
```

**Expected**: Should create a rectangle sketch in Fusion 360

---

## Test 4: MCP Tool Calling from Python

**Goal**: Verify Python can call other MCP tools

```python
fusion360({
  "operation": "execute_python",
  "code": """# Create a test table in SQLite
result = mcp.call("sqlite", {
    "input": {
        "sql": "CREATE TABLE IF NOT EXISTS fusion_test (id INTEGER PRIMARY KEY, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)",
        "database": "test.db",
        "tool_unlock_token": "29e63eb5"
    }
})

print(f"Table creation result: {result}")

# Insert a record
result2 = mcp.call("sqlite", {
    "input": {
        "sql": "INSERT INTO fusion_test (message) VALUES (?)",
        "params": ["Hello from Fusion Python!"],
        "database": "test.db",
        "tool_unlock_token": "29e63eb5"
    }
})

print(f"Insert result: {result2}")
"""
})
```

**Expected**: Should create table and insert record in SQLite

---

## Test 5: Direct MCP Tool Call

**Goal**: Verify direct tool calling works

```python
fusion360({
  "operation": "call_tool",
  "tool_name": "sqlite",
  "arguments": {
    "input": {
      "sql": "SELECT * FROM fusion_test ORDER BY timestamp DESC LIMIT 5",
      "database": "test.db",
      "tool_unlock_token": "29e63eb5"
    }
  }
})
```

**Expected**: Should return the records we inserted

---

## Test 6: Session Persistence

**Goal**: Verify variables persist across executions

```python
# Execution 1: Define a function
fusion360({
  "operation": "execute_python",
  "session_id": "test_session",
  "persistent": true,
  "code": """def my_helper_function():
    return "This function persists!"

my_variable = 42
print(f"Defined function and variable")
"""
})

# Execution 2: Use the function
fusion360({
  "operation": "execute_python",
  "session_id": "test_session",
  "persistent": true,
  "code": """# Function should still exist!
print(my_helper_function())
print(f"Variable value: {my_variable}")
"""
})
```

**Expected**: Second execution should successfully call the function and access the variable

---

## Test 7: Script Management

**Goal**: Verify script save/load/list/delete

```python
# Save a script
fusion360({
  "operation": "save_script",
  "filename": "test_workflow.py",
  "code": "print('This is a test workflow')\nprint(f'Fusion version: {app.version}')"
})

# List scripts
fusion360({
  "operation": "list_scripts"
})

# Load the script
fusion360({
  "operation": "load_script",
  "filename": "test_workflow.py"
})

# Delete the script
fusion360({
  "operation": "delete_script",
  "filename": "test_workflow.py"
})
```

**Expected**: Should save, list, load, and delete the script successfully

---

## Test 8: Error Handling

**Goal**: Verify proper error reporting

```python
fusion360({
  "operation": "execute_python",
  "code": "this_will_cause_an_error()"
})
```

**Expected**: Should return error with traceback showing `<ai-code>` filename

---

## Test 9: Complex Integration

**Goal**: Combine everything - geometry + database + popup

```python
fusion360({
  "operation": "execute_python",
  "code": """import adsk.core
import adsk.fusion

design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

# Create sketch
sketch = root.sketches.add(root.xYConstructionPlane)
lines = sketch.sketchCurves.sketchLines
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(8, 5, 0)
)

# Store in database
mcp.call("sqlite", {
    "input": {
        "sql": "CREATE TABLE IF NOT EXISTS sketches (id INTEGER PRIMARY KEY, name TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)",
        "database": "fusion_projects.db",
        "tool_unlock_token": "29e63eb5"
    }
})

mcp.call("sqlite", {
    "input": {
        "sql": "INSERT INTO sketches (name) VALUES (?)",
        "params": [sketch.name],
        "database": "fusion_projects.db",
        "tool_unlock_token": "29e63eb5"
    }
})

# Show popup
mcp.call("user", {
    "input": {
        "operation": "show_popup",
        "html": f"<h1>Sketch Created!</h1><p>Name: {sketch.name}<br>Stored in database</p>",
        "width": 300,
        "height": 150,
        "tool_unlock_token": "1d9bf6a0"
    }
})

print(f"Created {sketch.name} and stored in database")
"""
})
```

**Expected**: Should create sketch, store in database, and show popup

---

## Test 10: Backward Compatibility

**Goal**: Verify generic API calls still work

```python
fusion360({
  "api_path": "get_pid"
})
```

**Expected**: Should return Fusion 360 process ID

---

## Troubleshooting

### If Python execution fails:
1. Check Text Commands window for error messages
2. Verify MCP client is connected
3. Check that `native_binary_path` was stored during discovery
4. Try reloading the add-in

### If MCP tool calling fails:
1. Verify the tool_unlock_token is correct
2. Check that the MCP server is running
3. Verify the tool exists: `fusion360({"operation": "call_tool", "tool_name": "server_control", "arguments": {"operation": "get_pid"}})`

### If script management fails:
1. Check that scripts directory was created
2. Verify write permissions
3. Check Text Commands window for path information

---

## Success Criteria

✅ All 10 tests pass  
✅ No errors in Text Commands window  
✅ Geometry created in Fusion 360  
✅ Data stored in SQLite  
✅ Popups display correctly  
✅ Scripts save/load successfully  

---

## Next: Demo Preparation

Once all tests pass, we're ready to create the Autodesk demo!

See `demo.md` for the presentation workflow.

