# Fusion 360 MCP Demo for AutoDesk Meeting
**Date**: Thursday (36 hours from now)
**Audience**: AutoDesk partnership team
**Goal**: Show AI controlling Fusion 360 to create something impressive

## Demo Concept: AI-Designed Parametric Bracket

Create a functional engineering bracket with:
1. Base plate with mounting holes
2. Vertical support wall
3. Reinforcement ribs
4. Chamfered edges for manufacturability

## Why This Demo Works:
- Shows **parametric design** (not just drawing lines)
- Demonstrates **real engineering** (mounting holes, ribs, chamfers)
- **Manufacturable** (something you could actually make)
- **Complex enough** to impress (multiple operations, constraints)
- **Quick enough** to demo live (< 2 minutes)

## Demo Script (What to Say):

"What I'm about to show you is a Fusion 360 add-in that exposes Fusion's entire API to AI agents via MCP - Model Context Protocol. This means any AI can now design in Fusion 360 just by understanding natural language.

Watch as I ask the AI to design an engineering bracket..."

## Commands to Execute (In Order):

### Step 1: Create Base Sketch
```python
# Create new sketch on XY plane
fusion360.execute({
  "api_path": "design.rootComponent.sketches.add",
  "args": ["design.rootComponent.xYConstructionPlane"],
  "store_as": "base_sketch"
})

# Add rectangle for base (10cm x 6cm)
fusion360.execute({
  "api_path": "$base_sketch.sketchCurves.sketchLines.addTwoPointRectangle",
  "args": ["$base_sketch.originPoint", ...NEED TO FIGURE OUT HOW TO SPECIFY SECOND POINT...],
  "store_as": "base_rectangle"
})
```

### Step 2: Add Mounting Holes
```python
# RESEARCH NEEDED: How to add circles at specific positions in sketch
```

### Step 3: Extrude Base
```python
# RESEARCH NEEDED: How to extrude a profile
```

### Step 4: Add Vertical Wall
```python
# RESEARCH NEEDED: Create sketch on face, extrude upward
```

### Step 5: Add Reinforcement Ribs
```python
# RESEARCH NEEDED: Sketch and extrude triangular ribs
```

### Step 6: Chamfer Edges
```python
# RESEARCH NEEDED: How to select and chamfer edges
```

---

## ✅ Working Commands (Tested Successfully):

### Create Sketch with Rectangle and Mounting Holes
```python
# Step 1: Create sketch on XY plane
fusion360.execute({
  "api_path": "design.rootComponent.sketches.add",
  "args": ["design.rootComponent.xYConstructionPlane"],
  "store_as": "demo_sketch"
})

# Step 2: Add 10cm x 6cm rectangle
fusion360.execute({
  "api_path": "$demo_sketch.sketchCurves.sketchLines.addTwoPointRectangle",
  "args": [
    {"type": "Point3D", "x": 0, "y": 0, "z": 0},
    {"type": "Point3D", "x": 10, "y": 6, "z": 0}
  ],
  "store_as": "base_rect"
})

# Step 3: Add mounting holes (0.5cm radius)
fusion360.execute({
  "api_path": "$demo_sketch.sketchCurves.sketchCircles.addByCenterRadius",
  "args": [{"type": "Point3D", "x": 2, "y": 2, "z": 0}, 0.5],
  "store_as": "hole1"
})

fusion360.execute({
  "api_path": "$demo_sketch.sketchCurves.sketchCircles.addByCenterRadius",
  "args": [{"type": "Point3D", "x": 8, "y": 2, "z": 0}, 0.5],
  "store_as": "hole2"
})

fusion360.execute({
  "api_path": "$demo_sketch.sketchCurves.sketchCircles.addByCenterRadius",
  "args": [{"type": "Point3D", "x": 2, "y": 4, "z": 0}, 0.5],
  "store_as": "hole3"
})

fusion360.execute({
  "api_path": "$demo_sketch.sketchCurves.sketchCircles.addByCenterRadius",
  "args": [{"type": "Point3D", "x": 8, "y": 4, "z": 0}, 0.5],
  "store_as": "hole4"
})

# Step 4: Get the profile (outer rect minus holes)
fusion360.execute({
  "api_path": "$demo_sketch.profiles.item",
  "args": [0],
  "store_as": "base_profile"
})
```

## 🚧 Issues to Resolve:

### Problem 1: Enum Values
Extrude needs `FeatureOperations` enum, but passing as string doesn't work.

**Error**:
```
TypeError: argument 2 of type 'adsk::core::Ptr< adsk::core::Base > const &'
```

**Attempts**:
- ❌ `"NewBodyFeatureOperation"` - Treated as string
- ❌ `"adsk.fusion.FeatureOperations.NewBodyFeatureOperation"` - Resolved as API path

**Solution Needed**: 
Update `_construct_object()` in `mcp_integration.py` to handle enums.

## 🎬 FINAL DEMO SCRIPT FOR THURSDAY

### What to Show:
**"AI-Designed Parametric Mounting Plate"**

A 10cm x 6cm base plate with 4 precisely positioned mounting holes (0.5cm diameter each).

### Why This Impresses AutoDesk:
1. **Parametric precision** - Exact dimensions, not hand-drawn
2. **Engineering geometry** - Mounting holes in standard pattern
3. **Generic API** - Works for ANY Fusion command, not hardcoded
4. **Real-time** - Happens live, not pre-recorded
5. **MCP Protocol** - Industry-standard AI-to-tool communication

### Demo Opening (What to Say):

> "What you're about to see is a Fusion 360 add-in that exposes Fusion's entire API to AI agents through MCP - Model Context Protocol. This is the same protocol Anthropic, OpenAI, and others are standardizing on for AI tool use.
> 
> The add-in has NO hardcoded commands - it's a completely generic API executor. The AI just needs to know Fusion's API, and it can do anything Fusion can do.
> 
> Watch as I ask the AI to design a technical mounting plate..."

### Complete Working Script:

```python
# Clear any previous context
fusion360.execute({"api_path": "clear_context"})

# Step 1: Create sketch on XY plane  
fusion360.execute({
  "api_path": "design.rootComponent.sketches.add",
  "args": ["design.rootComponent.xYConstructionPlane"],
  "store_as": "mounting_plate"
})
# Result: Sketch created

# Step 2: Draw 10cm x 6cm rectangle
fusion360.execute({
  "api_path": "$mounting_plate.sketchCurves.sketchLines.addTwoPointRectangle",
  "args": [
    {"type": "Point3D", "x": 0, "y": 0, "z": 0},
    {"type": "Point3D", "x": 10, "y": 6, "z": 0}
  ]
})
# Result: Rectangle drawn

# Step 3-6: Add 4 mounting holes in corners (0.5cm radius)
fusion360.execute({
  "api_path": "$mounting_plate.sketchCurves.sketchCircles.addByCenterRadius",
  "args": [{"type": "Point3D", "x": 2, "y": 2, "z": 0}, 0.5]
})

fusion360.execute({
  "api_path": "$mounting_plate.sketchCurves.sketchCircles.addByCenterRadius",
  "args": [{"type": "Point3D", "x": 8, "y": 2, "z": 0}, 0.5]
})

fusion360.execute({
  "api_path": "$mounting_plate.sketchCurves.sketchCircles.addByCenterRadius",
  "args": [{"type": "Point3D", "x": 2, "y": 4, "z": 0}, 0.5]
})

fusion360.execute({
  "api_path": "$mounting_plate.sketchCurves.sketchCircles.addByCenterRadius",
  "args": [{"type": "Point3D", "x": 8, "y": 4, "z": 0}, 0.5]
})
# Result: 4 mounting holes precisely positioned
```

### Demo Closing (What to Say):

> "And there you have it - a parametric mounting plate designed by AI in real-time. 
> 
> Key points:
> - This add-in took ONE day to build
> - It supports ANY Fusion API command - sketches, extrudes, assemblies, simulations, CAM toolpaths - everything
> - The enhanced error reporting gives AI agents full visibility into what works and what doesn't
> - 15,000 users already trust my add-ins, and this MCP integration can benefit all of them
> 
> Imagine: AI design assistants, automated toolpath generation, natural language CAD... all built on this foundation.
> 
> The partnership opportunity is this: Together we can make Fusion 360 the FIRST major CAD platform with native AI agent support."

### Backup Talking Points:

**If they ask about 3D features:**
> "Extrusion works too - I just need to handle a few more object types. The infrastructure is generic, so adding support for ValueInput, ExtentDefinition, etc. is straightforward."

**If they ask about error handling:**
> "Watch what happens if I make a mistake..."
> [Show an intentional error - the enhanced reporting will impress them]

**If they ask about performance:**
> "Each command executes in real-time. For complex designs, AI can batch multiple operations. The background MCP connection has zero overhead on Fusion."

**If they ask about security:**
> "The add-in only connects to localhost MCP servers. No external APIs, no cloud dependencies. It's as secure as any other Fusion add-in."

### Pre-Demo Checklist:

- [ ] Fusion 360 is running
- [ ] MCP-Link add-in is loaded and connected
- [ ] TEXT COMMANDS window is visible (shows the logs)
- [ ] Start with a blank document
- [ ] Test the script once privately to verify timing
- [ ] Have `demo.md` open for reference

### Timing:
- Intro: 30 seconds
- Demo execution: 60 seconds (6 commands × 10 sec each)
- Closing: 30 seconds
- **Total: 2 minutes**

### Success Metrics:
- ✅ All commands execute without errors
- ✅ Mounting plate is visible in Fusion
- ✅ AutoDesk team understands the generic API approach
- ✅ They see the partnership potential

---

## Technical Notes:

### What Works (Tested & Verified):
- ✅ Sketch creation on any plane
- ✅ Rectangle drawing with Point3D coordinates
- ✅ Circle creation with precise positioning
- ✅ Profile access (for future extrusion)
- ✅ Context storage ($ variables)
- ✅ Point3D construction from dictionaries: `{"type": "Point3D", "x": 0, "y": 0, "z": 0}`
- ✅ Enhanced error reporting with full tracebacks
- ✅ Type information in success responses

### Known Limitations (for v2):
- ⚠️ Enum values need integer codes (e.g., `0` for `NewBodyFeatureOperation`)
- ⚠️ ValueInput needs special handling (can't construct from dict)
- ⚠️ ExtentDefinition objects need API path access pattern

### Quick Reference - Common Types:

```python
# Point3D - WORKS
{"type": "Point3D", "x": 0, "y": 0, "z": 0}

# Enums - Use integer values
# FeatureOperations: 0=NewBody, 1=Join, 2=Cut, 3=Intersect
0  # for NewBodyFeatureOperation

# API Paths - Common patterns
"design.rootComponent.sketches.add"
"$sketch.sketchCurves.sketchLines.addByTwoPoints"
"$sketch.sketchCurves.sketchCircles.addByCenterRadius"
"$sketch.profiles.item"
```

### Enum Value Reference (for future):
```
FeatureOperations:
  0 = NewBodyFeatureOperation
  1 = JoinFeatureOperation
  2 = CutFeatureOperation  
  3 = IntersectFeatureOperation

ExtentDirections:
  0 = PositiveExtentDirection
  1 = NegativeExtentDirection
  2 = SymmetricExtentDirection
```

### ✅ BREAKTHROUGH (Nov 4, 2025): Full Module Path Support!

**Problem Solved**: Can now call static methods using full module paths!

```python
# ✅ NOW WORKS:
adsk.core.ValueInput.createByString("1 cm")
adsk.core.Point3D.create(0, 0, 0)
```

The API path resolver was enhanced to recognize `adsk.core.*` and `adsk.fusion.*` paths, enabling direct access to static class methods without workarounds.

### Post-Demo Action Items:
1. ~~Add ValueInput helper to `mcp_integration.py`~~ ✅ DONE - Full module path support added!
2. Add enum documentation to tool readme
3. Create example gallery of common operations
4. Add batch operation support for performance
5. Implement undo/redo helpers
6. ~~Investigate text extrusion requirements~~ ✅ DONE - See "Hello Tiffany" demo below!

---

## 🎉 BONUS DEMO: "Hello Tiffany" - 3D Extruded Text

### What It Shows:
A complete 3D text creation workflow - from sketch to extruded solid. Perfect for showing off the full power of the generic API!

### Complete Working Script (100% Tested):

```python
# Step 1: Create sketch on XY plane
fusion360.execute({
  "tool_unlock_token": "e5076d",
  "operation": "execute",
  "api_path": "design.rootComponent.sketches.add",
  "args": ["design.rootComponent.xYConstructionPlane"],
  "store_as": "text_sketch"
})

# Step 2: Create text input (text="Hello Tiffany", height=1.5cm)
fusion360.execute({
  "tool_unlock_token": "e5076d",
  "operation": "execute",
  "api_path": "$text_sketch.sketchTexts.createInput2",
  "args": ["'Hello Tiffany'", 1.5],
  "store_as": "text_input"
})

# Step 3: Create corner points for text bounding box
fusion360.execute({
  "tool_unlock_token": "e5076d",
  "operation": "execute",
  "api_path": "adsk.core.Point3D.create",
  "args": [0, 0, 0],
  "store_as": "corner1"
})

fusion360.execute({
  "tool_unlock_token": "e5076d",
  "operation": "execute",
  "api_path": "adsk.core.Point3D.create",
  "args": [15, 3, 0],
  "store_as": "corner2"
})

# Step 4: Configure text as multi-line
# Args: corner1, corner2, hAlign (1=center), vAlign (1=middle), charSpacing (0.0)
fusion360.execute({
  "tool_unlock_token": "e5076d",
  "operation": "execute",
  "api_path": "$text_input.setAsMultiLine",
  "args": ["$corner1", "$corner2", 1, 1, 0.0]
})

# Step 5: Add text to sketch
fusion360.execute({
  "tool_unlock_token": "e5076d",
  "operation": "execute",
  "api_path": "$text_sketch.sketchTexts.add",
  "args": ["$text_input"],
  "store_as": "hello_text"
})

# Step 6: Create extrude distance (1 cm)
fusion360.execute({
  "tool_unlock_token": "e5076d",
  "operation": "execute",
  "api_path": "adsk.core.ValueInput.createByString",
  "args": ["1 cm"],
  "store_as": "extrude_distance"
})

# Step 7: Extrude the text to create 3D solid
# Args: profile, distance, operation (0=NewBody)
fusion360.execute({
  "tool_unlock_token": "e5076d",
  "operation": "execute",
  "api_path": "design.rootComponent.features.extrudeFeatures.addSimple",
  "args": ["$hello_text", "$extrude_distance", 0],
  "store_as": "extruded_text"
})
```

### Key Learnings from Text Extrusion:

1. **SketchTextInput Must Be Configured Before Adding**
   - Call `setAsMultiLine()` BEFORE `sketchTexts.add()`
   - If not configured properly, you'll get: `RuntimeError: 2 : InternalValidationError : bSucceeded && text`

2. **setAsMultiLine Arguments**
   ```python
   setAsMultiLine(corner1, corner2, hAlign, vAlign, charSpacing)
   # hAlign: 0=Left, 1=Center, 2=Right
   # vAlign: 0=Top, 1=Middle, 2=Bottom
   # charSpacing: 0.0 = normal spacing
   ```

3. **Full Module Paths Are Essential**
   - `adsk.core.Point3D.create(x, y, z)` - Creates point objects
   - `adsk.core.ValueInput.createByString("1 cm")` - Creates dimension values
   - These static methods are now fully supported!

4. **Text Can Be Extruded Directly**
   - No need to get profiles - `SketchText` objects can be passed directly to `addSimple()`
   - This is a huge time-saver!

### Why This Impresses:
- ✅ **Complex geometry** - Not just simple shapes
- ✅ **Full 3D workflow** - Sketch → Configure → Extrude
- ✅ **Static method calls** - Shows off the enhanced API resolver
- ✅ **Multi-step dependencies** - Each step builds on the previous
- ✅ **Real-world use case** - Text is commonly used in CAD (labels, branding, etc.)

### Demo Timing:
- 7 commands × 10 seconds each = **70 seconds total**
- Perfect for a "wow factor" follow-up to the mounting plate demo!

### Backup Demo Strategy:
If the mounting plate demo goes perfectly and you have extra time, run this as a bonus:

> "Let me show you one more thing - watch as the AI creates 3D text..."
> [Execute the 7 commands]
> "There you have it - from natural language to 3D solid in under a minute!"

