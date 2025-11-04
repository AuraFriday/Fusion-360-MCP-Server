# Fusion 360 MCP Server

**Control Fusion 360 with any AI through Model Context Protocol (MCP)**

[![Watch Demo](https://img.youtube.com/vi/Hpu5dopidKc/maxresdefault.jpg)](https://www.youtube.com/watch?v=Hpu5dopidKc)

*Click above to watch AI create "Fusion Rocks!" in 3D*

## What This Is

A Fusion 360 add-in that exposes Fusion's **entire API** to AI agents via the Model Context Protocol. No hardcoded commands—just a generic API executor that lets AI do anything Fusion can do.

## Key Features

- 🤖 **100% Generic API** - Works with ANY Fusion 360 command, no custom handlers needed
- 🔗 **MCP Protocol** - Industry-standard AI-to-tool communication (Anthropic, OpenAI, etc.)
- 🎯 **Full Module Path Support** - Direct access to static methods like `adsk.core.Point3D.create()`
- 💾 **Context Management** - Store and reuse objects across multiple commands using `$variables`
- 🐛 **Enhanced Error Reporting** - Detailed tracebacks and hints for AI debugging
- ⚡ **Real-Time Execution** - See designs appear as AI creates them

## What AI Can Do

- Create parametric sketches with precise dimensions
- Add text and extrude it to 3D
- Generate mounting holes, brackets, and mechanical parts
- Execute any Fusion 360 API command through natural language
- Build complex multi-step designs in seconds

## Installation

### Prerequisites

1. **Download MCP-Link Server**  
   Get the latest release from: https://github.com/AuraFriday/mcp-link-server/releases/tag/latest

2. **Clone This Repository**  
   ```bash
   git clone https://github.com/AuraFriday/Fusion-360-MCP-Server.git
   ```

3. **Load as Fusion 360 Add-in**  
   - Open Fusion 360
   - Press `Shift+S` to open Scripts and Add-Ins
   - Click the **Add-Ins** tab
   - Click the green **+** button next to "My Add-Ins"
   - Navigate to the cloned repository folder
   - Select the folder and click **OK**
   - Click **Run** to start the add-in

### Configuration

The add-in auto-connects to the MCP server on startup. Check the **TEXT COMMANDS** window in Fusion 360 to see connection logs.

## Quick Start Example

Once installed, AI can execute commands like:

```python
# Create a sketch
fusion360.execute({
  "api_path": "design.rootComponent.sketches.add",
  "args": ["design.rootComponent.xYConstructionPlane"],
  "store_as": "my_sketch"
})

# Add a rectangle
fusion360.execute({
  "api_path": "$my_sketch.sketchCurves.sketchLines.addTwoPointRectangle",
  "args": [
    {"type": "Point3D", "x": 0, "y": 0, "z": 0},
    {"type": "Point3D", "x": 10, "y": 5, "z": 0}
  ]
})
```

## How It Works

1. **Add-in loads** and connects to local MCP server
2. **Registers itself** as a `fusion360` tool via reverse connection
3. **AI sends commands** specifying API paths and arguments
4. **Generic handler** resolves paths, constructs objects, executes API calls
5. **Results returned** to AI with full context and type information

## Architecture

- **MCP-Link Server** - Routes AI requests to the add-in
- **Generic API Handler** (`mcp_integration.py`) - Dynamically executes any Fusion API call
- **Context Manager** - Stores intermediate objects for multi-step operations
- **Enhanced Reporting** - Provides detailed success/error information for AI

## Supported Patterns

### API Paths
```python
"design.rootComponent.sketches.add"              # Access via app object
"$sketch.sketchCurves.sketchCircles.addByCenterRadius"  # Use stored objects
"adsk.core.Point3D.create"                       # Full module paths
"adsk.core.ValueInput.createByString"            # Static methods
```

### Object Construction
```python
{"type": "Point3D", "x": 5, "y": 10, "z": 0}    # Construct from dict
"$my_sketch.originPoint"                         # Reference stored object
0                                                 # Enum as integer
```

### Context Storage
```python
"store_as": "my_object"                          # Store result as $my_object
"$my_object.someMethod"                          # Use in next command
```

## Limitations

- Enum values must be passed as integers (e.g., `0` for `NewBodyFeatureOperation`)
- Some complex objects need specific construction patterns
- Context is lost when add-in is reloaded (working as intended for session isolation)

## Demo Script

See [`demo.md`](demo.md) for complete working examples, including:
- Parametric mounting plate with precision holes
- 3D extruded text ("Fusion Rocks!" demo)
- Common patterns and best practices

## Use Cases

- **AI Design Assistants** - Natural language to CAD
- **Automated Toolpath Generation** - AI-driven CAM workflows
- **Design Exploration** - Rapidly iterate parametric variations
- **Educational Tools** - Learn Fusion API through AI guidance
- **Batch Operations** - Automate repetitive modeling tasks

## Technical Details

- Built with Fusion 360's native Python API
- Uses Server-Sent Events (SSE) for MCP connection
- JSON-RPC protocol for command execution
- Zero overhead on Fusion performance
- All operations run locally (no cloud dependencies)

## Future Enhancements

- Semantic search integration for auto-documentation
- Batch operation optimization
- Undo/redo helpers
- Extended enum handling
- More intuitive object construction patterns

## License

MIT License - See LICENSE file for details

## Author

Created by [AiraFriday](https://github.com/AuraFriday)  
With 15,000+ users trusting previous Fusion 360 add-ins

## Links

- **MCP-Link Server**: https://github.com/AuraFriday/mcp-link-server
- **Model Context Protocol**: https://modelcontextprotocol.io
- **Fusion 360 API**: https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-A92A4B10-3781-4925-94C6-47DA85A4F65A

---

**Questions?** Open an issue or check the documentation in [`docs/`](docs/)

**Want to Contribute?** PRs welcome! This is the future of AI-powered CAD. 🚀
