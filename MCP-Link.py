# -*- coding: utf-8 -*-
"""
File: MCP-Link.py
Project: MCP-Link Fusion 360 Add-in
Component: Static Loader Stub (NEVER UPDATED)
Author: Christopher Nathan Drake (cnd)
Created: 2025-01-07
SPDX-License-Identifier: Proprietary
Copyright: (c) 2025 Aura Friday. All rights reserved.

IMPORTANT: This file is the STATIC LOADER STUB.
It should NEVER be updated via the auto-update system.

This file's sole purpose is to:
1. Check for pending update files (fusion360_mcp_update.zip)
2. Verify signatures and apply updates BEFORE loading any other code
3. Chain-load the actual add-in logic from mcp_main.py

By doing the update check BEFORE importing other modules, we ensure that
file overwrites are safe (no modules have been loaded yet).
"""

import os

# Get the add-in directory (where this file lives)
_ADDIN_DIR = os.path.dirname(os.path.abspath(__file__))


def _safe_print(message):
  """Print safely even if stdout is unavailable."""
  try:
    print(message)
  except:
    pass


def _check_and_apply_updates():
  """
  Check for and apply any pending updates.
  
  This runs BEFORE any other add-in modules are imported,
  making it safe to overwrite files that will be loaded next.
  
  Returns:
    True if an update was applied, False otherwise
  """
  try:
    # Import update loader (also static, never updated)
    from .lib.update_loader import check_and_apply_update
    
    # Check for and apply pending updates
    update_applied = check_and_apply_update(_ADDIN_DIR)
    
    if update_applied:
      _safe_print("[MCP-Link] Update applied successfully")
    
    return update_applied
    
  except Exception as e:
    # Log error but continue - don't break the add-in
    _safe_print(f"[MCP-Link] Update check error (continuing anyway): {e}")
    return False


def run(context):
  """
  Main entry point - Fusion calls this when the add-in starts.
  
  Flow:
  1. Check for pending updates (before importing anything else)
  2. Apply updates if found (safe because no modules loaded yet)
  3. Import and run the actual add-in logic
  """
  # Step 1: Check for and apply any pending updates FIRST
  # This happens BEFORE importing mcp_main, so file overwrites are safe
  _check_and_apply_updates()
  
  # Step 2: Now import and run the actual add-in
  # If an update was applied, we load the NEW code
  try:
    from . import mcp_main
    mcp_main.run(context)
  except Exception as e:
    _safe_print(f"[MCP-Link] Failed to start add-in: {e}")
    import traceback
    _safe_print(traceback.format_exc())


def stop(context):
  """
  Shutdown handler - Fusion calls this when the add-in stops.
  """
  try:
    from . import mcp_main
    mcp_main.stop(context)
  except Exception as e:
    _safe_print(f"[MCP-Link] Error during shutdown: {e}")
