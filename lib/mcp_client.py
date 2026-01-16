"""
File: mcp_client.py
Project: MCP-Link Fusion Add-in
Component: MCP client library (adapted from reverse_mcp.py)
Author: Christopher Nathan Drake (cnd)
Created: 2025-11-03
Last Modified: 2025-11-03 by cnd (Integrated into Fusion add-in)
SPDX-License-Identifier: Proprietary
Copyright: (c) 2025 Christopher Nathan Drake. All rights reserved.

This module provides MCP client functionality for Fusion add-ins.
It handles:
- Native messaging discovery
- SSE connection to MCP server
- Remote tool registration
- Reverse call handling

Adapted from reverse_mcp.py for use within Fusion's Python environment.
"""

import os
import sys
import json
import platform
import ssl
import struct
import uuid
import threading
import time
import queue
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from urllib.parse import urljoin, urlparse, parse_qs
import http.client


class MCPClient:
  """
  MCP client for connecting Fusion 360 to the MCP-Link server.
  This allows Fusion 360 to register as a remote tool and receive commands from AI.
  """
  
  def __init__(self, tool_name: str, tool_description: str, tool_readme: str,
               tool_handler: Callable[[Dict[str, Any]], Dict[str, Any]],
               log_callback: Optional[Callable[[str], None]] = None):
    """
    Initialize the MCP client.
    
    Args:
      tool_name: Name of the tool to register (e.g., "fusion360")
      tool_description: Short description of the tool
      tool_readme: Detailed documentation for the tool
      tool_handler: Function to call when a reverse call is received
                   Should accept call_data dict and return result dict
      log_callback: Optional function to call for logging messages
    """
    self.tool_name = tool_name
    self.tool_description = tool_description
    self.tool_readme = tool_readme
    self.tool_handler = tool_handler
    self.log_callback = log_callback
    
    self.sse_connection = None
    self.server_url = None
    self.auth_header = None
    self.worker_thread = None
    self.stop_event = threading.Event()
    self.is_connected = False
    self.retry_count = 0
    self.max_retry_delay = 60  # Max 1 minute between retries
    self.native_binary_path = None  # Stored during discovery for script directory calculation
    
  def log(self, message: str, force: bool = False):
    """
    Log a message via the callback if available.
    
    Args:
      message: The message to log
      force: If True, always log regardless of MCP_DEBUG setting
    """
    # Check if we should log based on MCP_DEBUG setting
    try:
      from .. import config
      should_log = force or config.MCP_DEBUG
    except:
      should_log = True  # Default to logging if config unavailable
    
    if should_log:
      if self.log_callback:
        # Thread-safe! log_callback now uses buffered logging
        self.log_callback(message)
      else:
        print(message, file=sys.stderr)
  
  def connect(self, enable_auto_reconnect: bool = True) -> bool:
    """
    Connect to the MCP server and register the tool.
    
    Args:
      enable_auto_reconnect: If True, automatically reconnect if connection drops
    
    Returns:
      True if connected and registered successfully, False otherwise
    """
    if enable_auto_reconnect:
      # Start worker thread with auto-reconnect
      self.worker_thread = threading.Thread(target=self._connection_worker_with_reconnect, daemon=True)
      self.worker_thread.start()
      
      # Wait a moment for initial connection
      time.sleep(2)
      
      return self.is_connected
    else:
      # Single connection attempt (no auto-reconnect)
      return self._attempt_connection()
  
  def _connection_worker_with_reconnect(self):
    """
    Worker thread that maintains connection with auto-reconnect.
    
    Includes automatic reconnection with exponential backoff if the SSE connection drops.
    Retry delays: 2s, 4s, 8s, 16s, 32s, 60s (max), 60s, 60s...
    """
    self.log("="*60, force=True)
    self.log("MCP Client Connection Worker Starting", force=True)
    self.log("Auto-reconnect enabled with exponential backoff", force=True)
    self.log("="*60, force=True)
    
    # Outer reconnection loop - keeps trying until stopped
    while not self.stop_event.is_set():
      try:
        # Calculate retry delay with exponential backoff
        if self.retry_count > 0:
          delay = min(2 ** self.retry_count, self.max_retry_delay)
          self.log(f"\n[RECONNECT] Waiting {delay} seconds before retry (attempt #{self.retry_count})...", force=True)
          
          # Wait with stop_event check
          if self.stop_event.wait(timeout=delay):
            break  # stop_event was set, exit cleanly
          
          self.log(f"[RECONNECT] Attempting to reconnect...\n", force=True)
        
        # Attempt connection
        if self._attempt_connection():
          # Reset retry count after successful connection
          self.retry_count = 0
          
          # Listen for reverse calls (blocking until connection drops or stop requested)
          self._listen_for_calls()
          
          # If we get here, connection dropped or stop was requested
          if not self.stop_event.is_set():
            self.log("\n[WARN] SSE connection lost - will reconnect...", force=True)
            self.retry_count = 1  # Start with first retry delay
        else:
          # Connection attempt failed
          self.retry_count += 1
        
      except Exception as e:
        self.log(f"\n[ERROR] Unexpected error in connection worker: {e}", force=True)
        import traceback
        self.log(traceback.format_exc(), force=True)
        self.retry_count += 1
    
    self.log("Connection worker stopped", force=True)
  
  def _attempt_connection(self) -> bool:
    """
    Attempt a single connection to the MCP server.
    
    Returns:
      True if connected and registered successfully, False otherwise
    """
    try:
      self.log("="*60, force=True)
      self.log("MCP Client Connection Attempt", force=True)
      self.log("="*60, force=True)
      
      # Step 1: Find the native messaging manifest
      self.log("Step 1: Finding native messaging manifest...")
      manifest_path = self._find_native_messaging_manifest()
      
      if not manifest_path:
        self.log("ERROR: Could not find native messaging manifest", force=True)
        self.log("Expected locations:", force=True)
        self.log("  Windows: %LOCALAPPDATA%\\AuraFriday\\com.aurafriday.shim.json", force=True)
        return False
      
      self.log(f"[OK] Found manifest: {manifest_path}")
      
      # Step 2: Read the manifest
      self.log("Step 2: Reading manifest...")
      manifest = self._read_manifest(manifest_path)
      if not manifest:
        self.log("ERROR: Could not read manifest", force=True)
        return False
      
      self.log("[OK] Manifest loaded")
      
      # Step 3: Run the native binary to get server config
      self.log("Step 3: Discovering MCP server endpoint...")
      config_json = self._discover_server_endpoint(manifest)
      
      if not config_json:
        self.log("ERROR: Could not get configuration from native binary", force=True)
        self.log("Is the Aura Friday MCP server running?", force=True)
        return False
      
      self.log("[OK] Server configuration received")
      
      # Step 4: Extract server URL and auth header
      self.log("Step 4: Extracting server URL and auth...")
      self.server_url = self._extract_server_url(config_json)
      if not self.server_url:
        self.log("ERROR: Could not extract server URL", force=True)
        return False
      
      mcp_servers = config_json.get('mcpServers', {})
      if mcp_servers:
        first_server = next(iter(mcp_servers.values()), None)
        if first_server and 'headers' in first_server:
          self.auth_header = first_server['headers'].get('Authorization')
      
      if not self.auth_header:
        self.log("ERROR: No authorization header found", force=True)
        return False
      
      self.log(f"[OK] Server URL: {self.server_url}")
      
      # Step 5: Connect to SSE endpoint
      self.log("Step 5: Connecting to SSE endpoint...")
      self.sse_connection = self._connect_sse(self.server_url, self.auth_header)
      
      if not self.sse_connection:
        self.log("ERROR: Could not connect to SSE endpoint", force=True)
        return False
      
      self.log(f"[OK] SSE Connected! Session ID: {self.sse_connection['session_id']}")
      
      # Step 6: Check for remote tool
      self.log("Step 6: Checking for remote tool...")
      tools_response = self._send_request("tools/list", {})
      
      if not tools_response:
        self.log("ERROR: Could not get tools list", force=True)
        return False
      
      tools = tools_response.get('result', {}).get('tools', [])
      has_remote = any(tool.get('name') == 'remote' for tool in tools)
      
      if not has_remote:
        self.log("ERROR: Server does not have 'remote' tool", force=True)
        return False
      
      self.log("[OK] Remote tool found")
      
      # Step 7: Register our tool
      self.log(f"Step 7: Registering {self.tool_name} with MCP server...")
      if not self._register_tool():
        self.log("ERROR: Failed to register tool", force=True)
        return False
      
      self.is_connected = True
      self.log("="*60, force=True)
      self.log(f"[SUCCESS] {self.tool_name} registered successfully!", force=True)
      self.log("Listening for reverse tool calls...", force=True)
      self.log("="*60, force=True)
      
      return True
      
    except Exception as e:
      self.log("="*60, force=True)
      self.log(f"ERROR: Connection failed: {e}", force=True)
      import traceback
      self.log(traceback.format_exc(), force=True)
      self.log("="*60, force=True)
      return False
  
  def disconnect(self):
    """Disconnect from the MCP server and clean up resources."""
    self.log("Disconnecting from MCP server...")
    self.stop_event.set()
    
    if self.sse_connection:
      self.sse_connection['stop_event'].set()
      
      # Close the connection to unblock the reader thread
      try:
        if self.sse_connection.get('response'):
          self.log("Closing SSE response stream...")
          self.sse_connection['response'].close()
      except Exception as e:
        self.log(f"Error closing SSE response: {e}")
      
      try:
        if self.sse_connection.get('connection'):
          self.log("Closing SSE connection...")
          self.sse_connection['connection'].close()
      except Exception as e:
        self.log(f"Error closing SSE connection: {e}")
      
      # Now wait for the thread to stop
      if self.sse_connection.get('thread'):
        self.log("Waiting for SSE reader thread to stop...")
        self.sse_connection['thread'].join(timeout=3)
        if self.sse_connection['thread'].is_alive():
          self.log("WARNING: SSE reader thread did not stop in time")
        else:
          self.log("SSE reader thread stopped")
    
    if self.worker_thread:
      self.log("Waiting for worker thread to stop...")
      self.worker_thread.join(timeout=3)
      if self.worker_thread.is_alive():
        self.log("WARNING: Worker thread did not stop in time")
      else:
        self.log("Worker thread stopped")
    
    self.is_connected = False
    self.log("Disconnected")
  
  def _find_native_messaging_manifest(self) -> Optional[Path]:
    """Find the native messaging manifest file."""
    system_name = platform.system().lower()
    possible_paths = []
    
    if system_name == "windows":
      appdata_local = os.environ.get('LOCALAPPDATA')
      if appdata_local:
        possible_paths.append(Path(appdata_local) / "AuraFriday" / "com.aurafriday.shim.json")
      possible_paths.append(Path.home() / "AppData" / "Local" / "AuraFriday" / "com.aurafriday.shim.json")
    elif system_name == "darwin":
      possible_paths.extend([
        Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts" / "com.aurafriday.shim.json",
        Path.home() / "Library" / "Application Support" / "Chromium" / "NativeMessagingHosts" / "com.aurafriday.shim.json",
      ])
    else:
      possible_paths.extend([
        Path.home() / ".config" / "google-chrome" / "NativeMessagingHosts" / "com.aurafriday.shim.json",
        Path.home() / ".config" / "chromium" / "NativeMessagingHosts" / "com.aurafriday.shim.json",
      ])
    
    for path in possible_paths:
      if path.exists():
        return path
    
    return None
  
  def _read_manifest(self, manifest_path: Path) -> Optional[Dict[str, Any]]:
    """Read and parse the manifest file."""
    try:
      with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception as e:
      self.log(f"Error reading manifest: {e}")
      return None
  
  def _extract_mcp_servers_from_truncated_json(self, truncated_text: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to extract the mcpServers section from truncated/incomplete JSON.
    
    When the native binary sends more data than we can receive (due to bugs like
    16-bit length overflow), the JSON gets truncated. This function attempts to
    extract just the mcpServers section which is all we need for connection.
    
    The JSON structure always starts like:
    {
      "mcpServers": {
        "mypc": {
          "url": "https://...",
          "note": "...",
          "headers": {
            "Authorization": "Bearer xxx",
            "Content-Type": "application/json"
          }
        }
      },
      ...more stuff that may be truncated...
    }
    
    Args:
      truncated_text: The incomplete/truncated JSON text
      
    Returns:
      A reconstructed minimal config dict with mcpServers, or None if extraction fails
    """
    self.log("[FALLBACK] Attempting to extract mcpServers from truncated JSON...")
    
    try:
      # Strategy 1: Try to find and extract just the mcpServers section
      # Look for the URL pattern first - this is the most critical piece
      url_match = re.search(r'"url"\s*:\s*"(https?://[^"]+)"', truncated_text)
      if not url_match:
        self.log("[FALLBACK] Could not find URL in truncated JSON")
        return None
      
      extracted_url = url_match.group(1)
      self.log(f"[FALLBACK] Found URL: {extracted_url}")
      
      # Look for the Authorization header
      auth_match = re.search(r'"Authorization"\s*:\s*"(Bearer\s+[^"]+)"', truncated_text)
      if not auth_match:
        self.log("[FALLBACK] Could not find Authorization header in truncated JSON")
        return None
      
      extracted_auth = auth_match.group(1)
      self.log(f"[FALLBACK] Found Authorization header: {extracted_auth[:20]}...")
      
      # Look for the server name (the key under mcpServers, usually "mypc" or hostname)
      server_name_match = re.search(r'"mcpServers"\s*:\s*\{\s*"([^"]+)"', truncated_text)
      server_name = server_name_match.group(1) if server_name_match else "extracted_server"
      
      # Reconstruct a minimal valid config with just what we need
      reconstructed_config = {
        "mcpServers": {
          server_name: {
            "url": extracted_url,
            "headers": {
              "Authorization": extracted_auth,
              "Content-Type": "application/json"
            }
          }
        },
        "_extracted_from_truncated_json": True,
        "_original_size_bytes": len(truncated_text)
      }
      
      self.log(f"[FALLBACK] Successfully reconstructed config from truncated JSON!")
      self.log(f"[FALLBACK] Extracted server: {server_name}")
      return reconstructed_config
      
    except Exception as e:
      self.log(f"[FALLBACK] Failed to extract from truncated JSON: {e}")
      return None
  
  def _discover_server_endpoint(self, manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Run the native binary to discover the server endpoint.
    
    Uses Chrome Native Messaging protocol:
    - Output format: 4-byte length (little-endian uint32) + JSON message
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
    
    try:
      creation_flags = 0
      if platform.system() == 'Windows':
        try:
          creation_flags = subprocess.CREATE_NO_WINDOW
        except AttributeError:
          pass
      
      proc = subprocess.Popen(
        [str(binary_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=False,
        bufsize=0,
        creationflags=creation_flags
      )
      
      json_data = None
      start_time = time.time()
      timeout = 5.0
      
      try:
        # Step 1: Read the 4-byte length prefix (little-endian uint32)
        length_bytes = b""
        while len(length_bytes) < 4 and time.time() - start_time < timeout:
          chunk = proc.stdout.read(4 - len(length_bytes))
          if not chunk:
            time.sleep(0.01)
            continue
          length_bytes += chunk
        
        if len(length_bytes) != 4:
          self.log(f"ERROR: Failed to read 4-byte length prefix (got {len(length_bytes)} bytes)")
          proc.terminate()
          return None
        
        # Convert little-endian bytes to int
        message_length = struct.unpack('<I', length_bytes)[0]
        
        self.log(f"[DEBUG] Message length from native binary: {message_length} bytes")
        
        if message_length <= 0 or message_length > 10_000_000:
          self.log(f"ERROR: Invalid message length: {message_length}")
          proc.terminate()
          return None
        
        # Step 2: Read the JSON payload of the specified length
        json_bytes = b""
        while len(json_bytes) < message_length and time.time() - start_time < timeout:
          chunk = proc.stdout.read(message_length - len(json_bytes))
          if not chunk:
            time.sleep(0.01)
            continue
          json_bytes += chunk
        
        if len(json_bytes) != message_length:
          self.log(f"ERROR: Stream ended after {len(json_bytes)} bytes (expected {message_length})")
          proc.terminate()
          return None
        
        # Step 3: Decode and parse the JSON
        text = None
        try:
          text = json_bytes.decode('utf-8')
          self.log(f"[DEBUG] Successfully read {len(json_bytes)} bytes of JSON")
          self.log(f"[DEBUG] JSON preview: {text[:100]}...")
          json_data = json.loads(text)
        except UnicodeDecodeError:
          # Try latin-1 as fallback
          text = json_bytes.decode('latin-1', errors='ignore')
          self.log(f"[DEBUG] Successfully read {len(json_bytes)} bytes of JSON (latin-1 fallback)")
          self.log(f"[DEBUG] JSON preview: {text[:100]}...")
          try:
            json_data = json.loads(text)
          except json.JSONDecodeError as json_parse_error:
            self.log(f"WARN: Failed to parse JSON: {json_parse_error}")
            self.log(f"Output was ({len(text)} bytes):\n{text}")
            # Try to extract mcpServers from truncated JSON
            json_data = self._extract_mcp_servers_from_truncated_json(text)
            if not json_data:
              proc.terminate()
              return None
        except json.JSONDecodeError as json_parse_error:
          self.log(f"WARN: Failed to parse JSON: {json_parse_error}")
          self.log(f"Output was ({len(text) if text else 0} bytes):\n{text if text else '(no text)'}")
          # Try to extract mcpServers from truncated JSON
          if text:
            json_data = self._extract_mcp_servers_from_truncated_json(text)
          if not json_data:
            proc.terminate()
            return None
        
      finally:
        # Terminate the process (it's waiting for stdin)
        try:
          proc.terminate()
          proc.wait(timeout=1.0)
        except:
          try:
            proc.kill()
          except:
            pass
      
      return json_data
      
    except Exception as e:
      self.log(f"ERROR: Failed to run native binary: {e}")
      import traceback
      self.log(traceback.format_exc())
      return None
  
  def _extract_server_url(self, config_json: Dict[str, Any]) -> Optional[str]:
    """Extract the server URL from config."""
    try:
      mcp_servers = config_json.get('mcpServers', {})
      if not mcp_servers:
        return None
      first_server = next(iter(mcp_servers.values()), None)
      if not first_server:
        return None
      return first_server.get('url')
    except Exception as e:
      self.log(f"ERROR: Failed to extract URL: {e}")
      return None
  
  def _connect_sse(self, server_url: str, auth_header: str) -> Optional[Dict[str, Any]]:
    """Connect to the SSE endpoint."""
    try:
      parsed_url = urlparse(server_url)
      host = parsed_url.netloc
      path = parsed_url.path
      use_https = parsed_url.scheme == 'https'
      
      if use_https:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        conn = http.client.HTTPSConnection(host, context=context, timeout=30)
      else:
        conn = http.client.HTTPConnection(host, timeout=30)
      
      headers = {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Authorization': auth_header,
      }
      
      conn.request('GET', path, headers=headers)
      response = conn.getresponse()
      
      if response.status != 200:
        conn.close()
        return None
      
      session_id = None
      message_endpoint = None
      
      event_type = None
      for _ in range(10):
        line = response.readline().decode('utf-8').strip()
        
        if line.startswith('event:'):
          event_type = line.split(':', 1)[1].strip()
        elif line.startswith('data:'):
          data = line.split(':', 1)[1].strip()
          if event_type == 'endpoint':
            message_endpoint = data
            if 'session_id=' in message_endpoint:
              session_id = message_endpoint.split('session_id=')[1].split('&')[0]
            break
        elif line == '':
          if message_endpoint:
            break
      
      if not message_endpoint or not session_id:
        conn.close()
        return None
      
      reverse_queue = queue.Queue()
      pending_responses = {}
      pending_responses_lock = threading.Lock()
      stop_event = threading.Event()
      
      def sse_reader_thread_function():
        try:
          while not stop_event.is_set():
            line = response.readline()
            if not line:
              break
            
            line_str = line.decode('utf-8', errors='ignore').strip()
            
            if line_str.startswith(':'):
              continue
            
            if line_str.startswith('data:'):
              data_str = line_str.split(':', 1)[1].strip()
              try:
                json_data = json.loads(data_str)
                
                if 'reverse' in json_data:
                  reverse_queue.put(json_data)
                elif 'id' in json_data:
                  request_id = json_data['id']
                  with pending_responses_lock:
                    if request_id in pending_responses:
                      pending_responses[request_id].put(json_data)
                
              except json.JSONDecodeError:
                pass
        except Exception as e:
          if not stop_event.is_set():
            self.log(f"SSE reader thread error: {e}")
      
      reader_thread = threading.Thread(target=sse_reader_thread_function, daemon=True)
      reader_thread.start()
      
      return {
        'session_id': session_id,
        'message_endpoint': message_endpoint,
        'connection': conn,
        'response': response,
        'thread': reader_thread,
        'stop_event': stop_event,
        'reverse_queue': reverse_queue,
        'pending_responses': pending_responses,
        'pending_responses_lock': pending_responses_lock,
        'server_url': server_url,
      }
      
    except Exception as e:
      self.log(f"ERROR: Failed to connect to SSE: {e}")
      return None
  
  def _send_request(self, method: str, params: Dict[str, Any], timeout_seconds: float = 10.0) -> Optional[Dict[str, Any]]:
    """Send a JSON-RPC request and wait for response."""
    try:
      request_id = str(uuid.uuid4())
      
      response_queue = queue.Queue()
      with self.sse_connection['pending_responses_lock']:
        self.sse_connection['pending_responses'][request_id] = response_queue
      
      try:
        jsonrpc_request = {
          "jsonrpc": "2.0",
          "id": request_id,
          "method": method,
          "params": params
        }
        
        request_body = json.dumps(jsonrpc_request)
        
        parsed_url = urlparse(self.server_url)
        host = parsed_url.netloc
        use_https = parsed_url.scheme == 'https'
        
        if use_https:
          context = ssl.create_default_context()
          context.check_hostname = False
          context.verify_mode = ssl.CERT_NONE
          post_conn = http.client.HTTPSConnection(host, context=context, timeout=10)
        else:
          post_conn = http.client.HTTPConnection(host, timeout=10)
        
        headers = {
          'Content-Type': 'application/json',
          'Content-Length': str(len(request_body)),
          'Authorization': self.auth_header,
        }
        
        message_path = self.sse_connection['message_endpoint']
        post_conn.request('POST', message_path, body=request_body, headers=headers)
        post_response = post_conn.getresponse()
        
        if post_response.status != 202:
          post_conn.close()
          return None
        
        post_conn.close()
        
        try:
          response = response_queue.get(timeout=timeout_seconds)
          return response
        except queue.Empty:
          return None
        
      finally:
        with self.sse_connection['pending_responses_lock']:
          self.sse_connection['pending_responses'].pop(request_id, None)
      
    except Exception as e:
      self.log(f"ERROR: Failed to send request: {e}")
      return None
  
  def _register_tool(self) -> bool:
    """Register the tool with the MCP server."""
    registration_params = {
      "name": "remote",
      "arguments": {
        "input": {
          "operation": "register",
          "tool_name": self.tool_name,
          "description": self.tool_description,
          "readme": self.tool_readme,
          "parameters": {
            "type": "object",
            "properties": {
              "command": {
                "type": "string",
                "description": "The command to execute in Fusion"
              },
              "parameters": {
                "type": "object",
                "description": "Parameters for the command"
              }
            },
            "required": ["command"]
          },
          "callback_endpoint": f"fusion360://{self.tool_name}-callback",
          "TOOL_API_KEY": f"fusion360_{self.tool_name}_auth_key"
        }
      }
    }
    
    response = self._send_request("tools/call", registration_params)
    
    if not response:
      return False
    
    if 'result' in response:
      result = response['result']
      if isinstance(result, dict):
        content = result.get('content', [])
        if content and len(content) > 0:
          text = content[0].get('text', '')
          if 'Successfully registered tool' in text:
            return True
    
    return False
  
  def _listen_for_calls(self):
    """
    Listen for reverse calls from the server.
    
    This method blocks until the connection drops or stop_event is set.
    Returns when connection is lost (for auto-reconnect) or when stopped.
    """
    self.log("Listening for reverse tool calls...")
    
    try:
      while not self.stop_event.is_set():
        try:
          # Check if SSE reader thread is still alive
          if self.sse_connection and not self.sse_connection['thread'].is_alive():
            self.log("\n[WARN] SSE reader thread died - connection lost", force=True)
            self.is_connected = False
            return  # Return to trigger reconnection
          
          # Block until a reverse call arrives (timeout allows checking for stop and connection health)
          msg = self.sse_connection['reverse_queue'].get(timeout=1.0)
          
          if isinstance(msg, dict) and 'reverse' in msg:
            reverse_data = msg['reverse']
            tool_name = reverse_data.get('tool')
            call_id = reverse_data.get('call_id')
            input_data = reverse_data.get('input')
            
            self.log(f"[CALL] Reverse call received for {tool_name}")
            
            if tool_name == self.tool_name:
              # Call the user's handler
              try:
                result = self.tool_handler(input_data)
                self._send_tool_reply(call_id, result)
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
        
        except queue.Empty:
          # No messages, just loop again (allows checking stop_event and connection health)
          continue
        
    except Exception as e:
      self.log(f"ERROR: Listen thread failed: {e}", force=True)
      import traceback
      self.log(traceback.format_exc(), force=True)
      self.is_connected = False
  
  def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any], 
                   timeout_seconds: float = 30.0) -> Optional[Dict[str, Any]]:
    """
    Call another MCP tool on the server.
    
    Args:
      tool_name: Name of the tool to call (e.g., "sqlite", "browser", "user")
      arguments: Arguments to pass to the tool
      timeout_seconds: How long to wait for response
      
    Returns:
      JSON-RPC response dictionary, or None on error
      
    Example:
      result = client.call_mcp_tool("sqlite", {
          "input": {
              "sql": "INSERT INTO designs (name) VALUES (?)",
              "params": ["my_design"],
              "tool_unlock_token": "29e63eb5"
          }
      })
    """
    if not self.sse_connection:
      self.log("ERROR: Not connected to server", force=True)
      return None
    
    tool_call_params = {
      "name": tool_name,
      "arguments": arguments
    }
    
    return self._send_request("tools/call", tool_call_params, timeout_seconds)
  
  def _send_tool_reply(self, call_id: str, result: Dict[str, Any]) -> bool:
    """Send a tools/reply back to the server."""
    try:
      reply_request = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": "tools/reply",
        "params": {
          "result": result
        }
      }
      
      request_body = json.dumps(reply_request)
      
      parsed_url = urlparse(self.server_url)
      host = parsed_url.netloc
      use_https = parsed_url.scheme == 'https'
      
      if use_https:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        post_conn = http.client.HTTPSConnection(host, context=context, timeout=10)
      else:
        post_conn = http.client.HTTPConnection(host, timeout=10)
      
      headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(request_body)),
        'Authorization': self.auth_header,
      }
      
      message_path = self.sse_connection['message_endpoint']
      post_conn.request('POST', message_path, body=request_body, headers=headers)
      post_response = post_conn.getresponse()
      
      if post_response.status != 202:
        post_conn.close()
        return False
      
      post_conn.close()
      self.log(f"[OK] Sent tools/reply for call_id {call_id}")
      return True
      
    except Exception as e:
      self.log(f"ERROR: Failed to send tools/reply: {e}")
      return False

