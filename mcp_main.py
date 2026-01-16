# -*- coding: utf-8 -*-
"""
File: mcp_main.py
Project: MCP-Link Fusion 360 Add-in
Component: Main Add-in Logic (UPDATABLE)
Author: Christopher Nathan Drake (cnd)
Created: 2025-01-07
SPDX-License-Identifier: Proprietary
Copyright: (c) 2025 Aura Friday. All rights reserved.

This module contains the main add-in logic, separated from the loader stub.
It is loaded by MCP-Link.py AFTER any pending updates have been applied.

This file CAN be updated via the auto-update system.
"""

from . import commands
from . import mcp_integration
from .lib import fusionAddInUtils as futil
from . import config


def run(context):
  """Main add-in entry point - called after update check."""
  try:
    # Print welcome banner with version
    import os
    from datetime import datetime
    
    # Get version from VERSION.txt
    version = "unknown"
    try:
      version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION.txt")
      with open(version_file, 'r') as f:
        version = f.read().strip()
    except:
      pass
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Print welcome banner
    mcp_integration.log(f"Welcome to MCP-Link Add-in v{version} on {timestamp}")
    mcp_integration.log("="*60)
    mcp_integration.log("MCP-Link Add-in: run() called")
    mcp_integration.log(f"DEBUG mode: {config.DEBUG}")
    mcp_integration.log(f"MCP_DEBUG mode: {config.MCP_DEBUG}")
    mcp_integration.log(f"MCP_AUTO_CONNECT: {config.MCP_AUTO_CONNECT}")
    mcp_integration.log("="*60)
    
    # Start MCP integration (core infrastructure - not a command)
    mcp_integration.start()
    
    # Start any UI commands (buttons, palettes, etc.)
    commands.start()
    
    # Schedule background update check (non-blocking)
    _schedule_update_check()
    
    mcp_integration.log("[OK] MCP-Link Add-in started successfully")

  except:
    futil.handle_error('run')


def stop(context):
  """Clean shutdown - called when add-in stops."""
  try:
    mcp_integration.log("="*60)
    mcp_integration.log("MCP-Link Add-in: stop() called")
    mcp_integration.log("="*60)
    
    # Stop MCP integration first
    mcp_integration.stop()
    
    # Stop UI commands
    commands.stop()
    
    # Remove all event handlers
    futil.clear_handlers()
    
    mcp_integration.log("[OK] MCP-Link Add-in stopped")

  except:
    futil.handle_error('stop')


def _schedule_update_check():
  """
  Schedule a background update check.
  
  This downloads updates (if available) which will be applied on next startup.
  Runs in a background thread to avoid blocking the UI.
  """
  import threading
  import os
  
  def check_updates():
    try:
      # Import here to avoid circular imports
      from .lib.update_loader import download_update_if_available
      
      # Get add-in directory
      addin_dir = os.path.dirname(os.path.abspath(__file__))
      
      # Check for updates (rate-limited to once per 24 hours)
      result = download_update_if_available(addin_dir)
      
      if result:
        mcp_integration.log(f"[UPDATE] Update downloaded - will be applied on next restart")
    except Exception as e:
      # Silent failure - don't crash the add-in for update check failures
      try:
        mcp_integration.log(f"[UPDATE] Background check failed: {e}")
      except:
        pass
  
  # Run in background thread (daemon so it doesn't block shutdown)
  update_thread = threading.Thread(target=check_updates, daemon=True)
  update_thread.start()
