# MCP-Link Fusion 360 Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AI Agent (e.g., Claude)                    │
│                                                                     │
│  "Create a 10cm cube in Fusion 360"                                 │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ MCP Protocol (JSON-RPC over HTTPS)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Aura Friday MCP-Link Server                      │
│                         (server/friday.py)                          │
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ Chrome Browser │  │  Fusion 360    │  │  Other Tools   │         │
│  │    Tool        │  │     Tool       │  │   (demo_tool)  │         │
│  │  (Extension)   │  │  (Remote Tool) │  │                │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                     │
│  Tool Registry:                                                     │
│  - chrome_browser (extension registers itself)                      │
│  - fusion360 (add-in registers itself) ◄── This project!            │
│  - demo_tool (reverse_mcp.py/js/go/java/pl)                         │
│  - sqlite, server_control, etc. (built-in)                          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ SSE (Server-Sent Events) + POST
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Fusion 360 with MCP-Link Add-in                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   Fusion 360 Main Thread                     │   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │   │
│  │  │ Command      │  │ Palette      │  │  MCP Connect │        │   │
│  │  │ Dialog       │  │ Show         │  │   Button     │◄───────┼───┼─ User clicks
│  │  └──────────────┘  └──────────────┘  └──────┬───────┘        │   │
│  │                                                │             │   │
│  │                                                │             │   │
│  │                                    Creates     │             │   │
│  │                                                ▼             │   │
│  │                                    ┌─────────────────────┐   │   │
│  │                                    │   MCPClient         │   │   │
│  │                                    │  (mcp_client.py)    │   │   │
│  │                                    │                     │   │   │
│  │                                    │  - tool_name        │   │   │
│  │                                    │  - tool_handler     │   │   │
│  │                                    │  - connect()        │   │   │
│  │                                    │  - disconnect()     │   │   │
│  │                                    └──────────┬──────────┘   │   │
│  └───────────────────────────────────────────────┼──────────────┘   │
│                                                  │                  │
│                                       Spawns     │                  │
│                                                  ▼                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  Background Threads                           │  │
│  │                                                               │  │
│  │  ┌───────────────────────┐    ┌────────────────────────────┐  │  │
│  │  │  SSE Reader Thread    │    │ Reverse Call Listener      │  │  │
│  │  │                       │    │      Thread                │  │  │
│  │  │  - Reads SSE stream   │    │                            │  │  │
│  │  │  - Parses events      │    │  while not stopped:        │  │  │
│  │  │  - Routes messages    │    │    msg = queue.get()       │  │  │
│  │  │    to queues          │    │    if msg.tool ==          │  │  │
│  │  │                       │    │       'fusion360':         │  │  │
│  │  │  SSE Stream           │    │      result = handler()    │  │  │
│  │  │    ▼                  │    │      send_reply(result)    │  │  │
│  │  │  ┌─────────────────┐──│    │                            │  │  │
│  │  │  │ Response Queues │  │    │    ▲                       │  │  │
│  │  │  │ (by request_id) │  │    │    │                       │  │  │
│  │  │  └─────────────────┘──│    │    │ Reads from            │  │  │
│  │  │  ┌─────────────────┐──│    │    │                       │  │  │
│  │  │  │ Reverse Queue   ├  ┼────┼────┘                       │  │  │
│  │  │  │ (reverse calls) │  │    │                            │  │  │
│  │  │  └─────────────────┘──│    │                            │  │  │
│  │  └───────────────────────┘    └────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │              Fusion 360 API (when implemented)             │     │
│  │                                                            │     │
│  │  - app.activeProduct.rootComponent                         │     │
│  │  - rootComponent.sketches.add()                            │     │
│  │  - sketch.sketchCurves.sketchLines.addTwoPointRectangle()  │     │
│  │  - rootComponent.features.extrudeFeatures.addSimple()      │     │
│  │  - etc.                                                    │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### 1. Connection Sequence

```
User                Fusion 360           MCPClient              Native Binary       MCP Server
  │                    │                     │                       │                   │
  │ Click "Connect"    │                     │                       │                   │
  ├───────────────────>│                     │                       │                   │
  │                    │ new MCPClient()     │                       │                   │
  │                    ├────────────────────>│                       │                   │
  │                    │                     │ find_manifest()       │                   │
  │                    │                     ├──────────────────────>│                   │
  │                    │                     │<──────────────────────┤                   │
  │                    │                     │ read_manifest()       │                   │
  │                    │                     ├──────────────────────>│                   │
  │                    │                     │<──────────────────────┤                   │
  │                    │                     │ run_binary()          │                   │
  │                    │                     ├──────────────────────>│                   │
  │                    │                     │<──────────────────────┤                   │
  │                    │                     │   (JSON config)       │                   │
  │                    │                     │                       │                   │
  │                    │                     │ connect_sse()         │                   │
  │                    │                     ├──────────────────────────────────────────>│
  │                    │                     │<──────────────────────────────────────────┤
  │                    │                     │   (session_id)        │                   │
  │                    │                     │                       │                   │
  │                    │                     │ register_tool()       │                   │
  │                    │                     ├──────────────────────────────────────────>│
  │                    │                     │<──────────────────────────────────────────┤
  │                    │                     │   (success)           │                   │
  │                    │                     │                       │                   │
  │                    │                     │ start_listener()      │                   │
  │                    │                     ├──────────────┐        │                   │
  │                    │                     │              │        │                   │
  │                    │                     │<─────────────┘        │                   │
  │                    │<────────────────────┤                       │                   │
  │<───────────────────┤                     │                       │                   │
  │  (Connected!)      │                     │                       │                   │
  │                    │                     │                       │                   │
```

### 2. Reverse Call Sequence

```
AI Agent          MCP Server         SSE Reader        Reverse Listener    Tool Handler     Fusion 360 API
   │                  │                  │                     │                 │                │
   │ "Create cube"    │                  │                     │                 │                │
   ├─────────────────>│                  │                     │                 │                │
   │                  │ tools/call       │                     │                 │                │
   │                  │ fusion360        │                     │                 │                │
   │                  ├─────────────────>│                     │                 │                │
   │                  │ (SSE message)    │                     │                 │                │
   │                  │                  │ Parse JSON          │                 │                │
   │                  │                  ├────────────────────>│                 │                │
   │                  │                  │  reverse_queue.put()│                 │                │
   │                  │                  │                     │ queue.get()     │                │
   │                  │                  │                     ├────────────────>│                │
   │                  │                  │                     │ handler()       │                │
   │                  │                  │                     ├────────────────>│                │
   │                  │                  │                     │                 │ create_box()   │
   │                  │                  │                     │                 ├───────────────>│
   │                  │                  │                     │                 │<───────────────┤
   │                  │                  │                     │                 │  (result)      │
   │                  │                  │                     │<────────────────┤                │
   │                  │                  │                     │                 │                │
   │                  │                  │                     │ send_reply()    │                │
   │                  │<───────────────────────────────────────┤                 │                │
   │                  │ tools/reply      │                     │                 │                │
   │<─────────────────┤                  │                     │                 │                │
   │  (result)        │                  │                     │                 │                │
   │                  │                  │                     │                 │                │
```

## Data Flow: Message Routing

### SSE Reader Thread → Message Queues

```python
# SSE Reader receives event:
data: {"id": "req-123", "result": {...}}          # Response to a request
  → Lookup pending_responses["req-123"]
  → Put into that specific queue
  → Waiting thread wakes up and gets response

data: {"reverse": {"tool": "fusion360", ...}}    # Reverse call
  → Put into reverse_queue
  → Listener thread wakes up and processes
```

### Queues Usage

```python
# For outgoing requests (e.g., tools/list):
request_id = uuid.uuid4()
response_queue = Queue()
pending_responses[request_id] = response_queue
send_post(request)
result = response_queue.get(timeout=10)  # Blocks until response arrives

# For incoming reverse calls:
while not stopped:
    msg = reverse_queue.get(timeout=1)  # Blocks until call arrives
    if msg.tool == 'fusion360':
        result = handler(msg.input)
        send_reply(msg.call_id, result)
```

## Threading Safety

### Thread Ownership

| Component | Thread | Blocks? | Purpose |
|-----------|--------|---------|---------|
| UI Button Click | Main Thread | No | Creates MCPClient |
| `connect()` | Main Thread | ~5s | Discovery & setup |
| SSE Reader | Background | Indefinite | Read SSE stream |
| Reverse Listener | Background | Indefinite | Process calls |
| POST Requests | Temporary | ~1s | Send messages |

### Synchronization Points

1. **pending_responses dictionary**:
   - Protected by `pending_responses_lock`
   - Read/write from SSE reader and request senders

2. **reverse_queue**:
   - Thread-safe `queue.Queue`
   - Written by SSE reader, read by listener

3. **stop_event**:
   - `threading.Event` for graceful shutdown
   - Set by disconnect(), checked by threads

## Error Handling Strategy

### Connection Errors

```python
try:
    client = MCPClient(...)
    success = client.connect()
    if not success:
        ui.messageBox("Connection failed")
except Exception as e:
    futil.handle_error("Connection error", show_message_box=True)
```

### Runtime Errors

```python
try:
    result = handler(call_data)
except Exception as e:
    # Return error result to AI
    result = {
        "content": [{"type": "text", "text": f"Error: {e}"}],
        "isError": True
    }
    send_reply(call_id, result)
```

### Cleanup Errors

```python
try:
    stop_event.set()
    thread.join(timeout=2)
except:
    pass  # Best effort cleanup
```

## Protocol Details

### JSON-RPC Request Format

```json
{
  "jsonrpc": "2.0",
  "id": "uuid-here",
  "method": "tools/call",
  "params": {
    "name": "fusion360",
    "arguments": {
      "command": "create_box",
      "parameters": {
        "length": 10,
        "width": 10,
        "height": 10,
        "units": "cm"
      }
    }
  }
}
```

### JSON-RPC Response Format

```json
{
  "jsonrpc": "2.0",
  "id": "uuid-here",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Created 10cm cube successfully"
      }
    ],
    "isError": false
  }
}
```

### SSE Message Format

```
event: endpoint
data: /messages/?session_id=abc123

event: message
data: {"jsonrpc": "2.0", "id": "uuid", "result": {...}}

event: message
data: {"reverse": {"tool": "fusion360", "call_id": "xyz", "input": {...}}}
```

## Performance Characteristics

### Latency

- **Connection time**: ~2-5 seconds (native binary + SSE handshake)
- **Command execution**: <100ms (network) + actual Fusion 360 operation time
- **Background overhead**: Minimal (~10MB RAM, negligible CPU)

### Scalability

- **Concurrent connections**: 1 per Fusion 360 instance
- **Commands per second**: Limited by Fusion 360 API, not MCP infrastructure
- **Message queue size**: Unbounded (Python queue.Queue)

### Resource Management

- **Memory**: ~10-20MB for MCP client + threads
- **CPU**: <1% idle, spikes during command processing
- **Network**: Persistent SSE connection + occasional POST requests

## Security Considerations

### Authentication

- **Bearer token**: Provided by native binary, unique per session
- **Callback endpoint**: Verified by MCP server
- **TOOL_API_KEY**: Identifies this specific client

### SSL/TLS

- **Server certificate**: Self-signed by MCP-Link server
- **Certificate verification**: Disabled (local server, trusted environment)
- **Hostname verification**: Disabled (127-0-0-1.local.aurafriday.com)

### Trust Model

```
User trusts:
  ├─ Fusion 360 (installed locally)
  ├─ MCP-Link server (installed locally)
  ├─ Native messaging (OS-level integration)
  └─ This add-in (loaded in Fusion 360)

Add-in trusts:
  ├─ Native binary (signed by Aura Friday)
  ├─ MCP server (via bearer token)
  └─ AI agent (via MCP server authentication)
```

## Comparison with Chrome Extension

| Aspect | Chrome Extension | Fusion 360 Add-in |
|--------|------------------|-------------------|
| **Language** | JavaScript | Python |
| **Environment** | Browser sandbox | Fusion 360 process |
| **Threading** | Event loop | Explicit threads |
| **UI Integration** | Browser API | Fusion 360 API |
| **Discovery** | Native messaging | Same |
| **Connection** | SSE | Same |
| **Registration** | `remote` tool | Same |
| **Tool name** | `chrome_browser` | `fusion360` |
| **Capabilities** | Web automation | CAD operations |

## Future Architecture Enhancements

### Phase 1: Command Implementation

```
Tool Handler
  ├─ Command Router
  │  ├─ create_box() → Fusion 360 API
  │  ├─ create_cylinder() → Fusion 360 API
  │  ├─ create_sketch() → Fusion 360 API
  │  └─ export_model() → Fusion 360 API
  │
  └─ Result Formatter
     └─ Convert Fusion 360 objects → JSON
```

### Phase 2: Advanced Features

```
Tool Handler
  ├─ Command Validator
  │  └─ Check parameters before execution
  │
  ├─ Transaction Manager
  │  └─ Wrap commands in undo groups
  │
  ├─ Progress Reporter
  │  └─ Stream updates via SSE
  │
  └─ Error Recovery
     └─ Rollback on failure
```

### Phase 3: AI Enhancements

```
Tool Handler
  ├─ NLP Parser
  │  └─ "make a gear" → create_gear(teeth=20, ...)
  │
  ├─ Context Analyzer
  │  └─ Use current document state for smart defaults
  │
  ├─ Multi-step Planner
  │  └─ Chain commands for complex designs
  │
  └─ Export/Preview
     └─ Generate images/STL for AI feedback
```

---

This architecture provides a **solid foundation** for AI-controlled Fusion 360, with clean separation of concerns, robust error handling, and clear extension points for future development! 🏗️

