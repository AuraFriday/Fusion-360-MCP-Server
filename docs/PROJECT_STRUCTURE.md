# MCP-Link Fusion 360 Add-in - Project Structure

## Clean, Logical Organization

This document explains the refactored project structure.

## Root Level Files

```
MCP-Link-fusion-new/
├── MCP-Link.py              # Main entry point (Fusion calls run() and stop())
├── MCP-Link.manifest        # Fusion 360 add-in manifest
├── mcp_integration.py       # MCP connection + generic Fusion API handler
├── config.py                # Global configuration (DEBUG flags, tool name)
├── readme.md                # Main documentation
└── Aura_Friday_Logo.svg     # Project logo
```

### Key Files Explained:

- **`MCP-Link.py`** - Entry point. Fusion 360 calls `run()` on startup and `stop()` on shutdown.
  - Starts `mcp_integration` (core infrastructure)
  - Starts `commands` (UI buttons/palettes)

- **`mcp_integration.py`** - Core MCP functionality (moved from `commands/mcpConnect/`)
  - Auto-connects to MCP server on startup
  - Registers `fusion360` tool with MCP server
  - Handles incoming tool calls via generic API executor
  - NOT a UI command - runs automatically in background

- **`config.py`** - Configuration constants
  - `DEBUG` - Enable/disable debug logging
  - `MCP_DEBUG` - Enable/disable verbose MCP logging
  - `MCP_AUTO_CONNECT` - Auto-connect to MCP on startup
  - `COMPANY_NAME`, `ADDIN_NAME` - Identity constants

## Library Code

```
lib/
├── mcp_client.py            # MCP client library (SSE connection, tool registration)
└── fusionAddInUtils/        # Fusion 360 utilities
    ├── __init__.py
    ├── event_utils.py       # Event handler helpers
    └── general_utils.py     # Logging, error handling
```

### Purpose:

- **`mcp_client.py`** - Reusable MCP client library
  - Discovers MCP server via native messaging
  - Connects via Server-Sent Events (SSE)
  - Registers as remote tool
  - Handles reverse tool calls

- **`fusionAddInUtils/`** - Fusion 360 helper functions
  - Logging to TEXT COMMANDS window
  - Error handling and formatting
  - Event handler registration/cleanup

## Commands (UI Elements)

```
commands/
├── __init__.py              # Command registry (imports and starts all commands)
└── samples/                 # Sample commands (for reference)
    ├── commandDialog/       # Sample dialog command
    ├── paletteShow/         # Sample palette show command
    └── paletteSend/         # Sample palette send command
```

### Purpose:

- **Commands are UI elements** - buttons, palettes, dialogs that users interact with
- **Samples are for reference** - show how to create Fusion 360 commands
- **User commands go here** - future commands that let users inside Fusion interact with AI

### Why samples are kept:

Future feature: Users inside Fusion 360 could click a button to connect to AI and get design help.

## Documentation

```
docs/
├── ARCHITECTURE.md          # System architecture overview
├── GENERIC_API_DESIGN.md    # Generic API handler design
├── IMPLEMENTATION_SUMMARY.md # What was implemented and how
├── INTEGRATION_GUIDE.md     # How the add-in integrates with Fusion
├── INTEGRATION_SUMMARY.md   # Integration summary
├── PROJECT_STRUCTURE.md     # This file
├── QUICK_START.md           # Quick start guide
└── TESTING_GUIDE.md         # Testing instructions
```

### Why separate docs folder:

- Keeps root clean and focused on code
- Easy to find all documentation in one place
- Clear separation between code and docs

## Key Architectural Decisions

### 1. MCP Integration is NOT a Command

**Before (Wrong):**
```
commands/
  mcpConnect/              # Treated as optional UI command
    entry.py              # Had to be manually triggered
```

**After (Correct):**
```
mcp_integration.py         # Core infrastructure at root level
                          # Auto-starts on add-in load
```

**Why:** MCP connection is fundamental infrastructure, not an optional UI feature.

### 2. Commands are ONLY UI Elements

**Before:**
- Unclear mix of infrastructure (MCP) and UI (dialogs, palettes)

**After:**
- `commands/` contains ONLY user-triggered UI elements
- Core functionality lives at root level

**Why:** Clear separation of concerns makes the codebase easier to understand.

### 3. Descriptive File Names

**Before:**
```
commands/commandDialog/entry.py    # What does "entry" mean?
commands/mcpConnect/entry.py       # Same filename everywhere!
```

**After:**
```
mcp_integration.py                                    # Clear purpose
commands/samples/commandDialog/sample_dialog_command.py  # Obvious it's a sample
```

**Why:** File names should describe their complete purpose and context.

## Development Workflow

### Adding a New Command:

1. Create `commands/myCommand/` folder
2. Add `__init__.py` with `start()` and `stop()` functions
3. Import in `commands/__init__.py`
4. Add to `commands` list

### Modifying MCP Integration:

1. Edit `mcp_integration.py` directly
2. Reload add-in in Fusion 360 (see readme.md for automation)
3. Test with AI tool calls

### Updating Configuration:

1. Edit `config.py`
2. Reload add-in for changes to take effect

## Testing the Refactored Structure

The add-in needs to be reloaded in Fusion 360 to pick up the structural changes.

See `readme.md` for detailed instructions on:
- Automated reload via `system` MCP tool
- Manual reload via Scripts and Add-Ins dialog
- Verifying the changes worked

## Benefits of New Structure

✅ **Clear separation** - Infrastructure vs UI commands
✅ **Obvious file purposes** - No more generic "entry.py"  
✅ **Clean root directory** - Only essential files visible
✅ **Organized docs** - All documentation in one place
✅ **Easy to extend** - Clear patterns for adding features
✅ **Better naming** - Follows naming rules throughout

## Migration Notes

If you have the old structure cached:

1. Delete `commands/mcpConnect/` completely
2. Reload add-in in Fusion 360
3. Check TEXT COMMANDS window for any import errors
4. Verify MCP connection still works

The refactoring is **backward compatible** with existing tool calls - the API hasn't changed, only the organization.

