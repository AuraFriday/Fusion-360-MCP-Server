# -*- coding: utf-8 -*-
"""
File: update_loader.py
Project: MCP-Link Fusion 360 Add-in
Component: Auto-Update Loader Module (STATIC - never updated via zip)
Author: Christopher Nathan Drake (cnd)
Created: 2025-01-07
SPDX-License-Identifier: Proprietary
Copyright: (c) 2025 Aura Friday. All rights reserved.

This module handles checking for and applying updates to the add-in.
It runs BEFORE any other add-in code is loaded, allowing safe in-place updates.

IMPORTANT: This file should NEVER be updated via the auto-update system.
It is part of the static loader that verifies and applies updates.

Update file naming convention:
  fusion360_mcp_v{version}-{platform}.zip
  
Where platform is: windows, mac-intel, or mac-arm
"""

import os
import platform
import shutil
import zipfile
from datetime import datetime, timezone
from typing import Optional


def get_platform_suffix() -> str:
  """Get platform suffix for update filename."""
  system = platform.system().lower()
  if system == "windows":
    return "windows"
  elif system == "darwin":  # macOS
    machine = platform.machine().lower()
    if machine in ["arm64", "aarch64"]:
      return "mac-arm"
    else:
      return "mac-intel"
  else:
    # Fallback for unknown systems
    return "windows"


def get_current_version(addin_dir: str) -> str:
  """
  Read current version from VERSION.txt.
  
  Args:
    addin_dir: Path to add-in directory
    
  Returns:
    Version string (e.g., "1.2.73") or "0.0.0" if not found
  """
  version_file = os.path.join(addin_dir, "VERSION.txt")
  try:
    if os.path.exists(version_file):
      with open(version_file, 'r', encoding='utf-8') as f:
        return f.read().strip()
  except Exception:
    pass
  return "0.0.0"


def safe_log(addin_dir: str, message: str, level: str = "info"):
  """
  Log message safely to update.log file.
  Used during update process when Fusion logging may not be available.
  
  Args:
    addin_dir: Path to add-in directory
    message: Message to log
    level: Log level (info, warning, error)
  """
  try:
    log_file = os.path.join(addin_dir, "update.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
      f.write(f"{timestamp} [{level.upper()}] {message}\n")
  except Exception:
    pass  # Silent failure - can't do anything if logging fails


def check_for_pending_update(addin_dir: str) -> Optional[str]:
  """
  Check if there's a pending update zip file waiting to be applied.
  
  Looks for: fusion360_mcp_update.zip in the add-in directory.
  
  Args:
    addin_dir: Path to add-in directory
    
  Returns:
    Path to update zip file if found and valid, None otherwise
  """
  update_zip = os.path.join(addin_dir, "fusion360_mcp_update.zip")
  
  if os.path.exists(update_zip):
    safe_log(addin_dir, f"Found pending update: {update_zip}")
    return update_zip
  
  return None


def verify_update_signature(zip_path: str, addin_dir: str) -> bool:
  """
  Verify the cryptographic signature on an update zip file.
  
  Args:
    zip_path: Path to the update zip file
    addin_dir: Path to add-in directory (for logging)
    
  Returns:
    True if signature is valid, False otherwise
  """
  try:
    # Import signature verification (also static, never updated)
    from .signature_verify import verify_signature_file
    
    safe_log(addin_dir, "Verifying update signature...")
    
    if verify_signature_file(zip_path):
      safe_log(addin_dir, "Signature verification PASSED - update is authentic")
      return True
    else:
      safe_log(addin_dir, "Signature verification FAILED - refusing update", "error")
      return False
      
  except Exception as e:
    safe_log(addin_dir, f"Signature verification error: {e}", "error")
    return False


def apply_update(zip_path: str, addin_dir: str) -> bool:
  """
  Apply an update by extracting the verified zip file.
  
  This function:
  1. Verifies the signature
  2. Extracts files to the add-in directory (overwriting existing)
  3. Deletes the zip file after successful extraction
  
  Args:
    zip_path: Path to the update zip file
    addin_dir: Path to add-in directory
    
  Returns:
    True if update was applied successfully, False otherwise
  """
  try:
    safe_log(addin_dir, f"Applying update from: {zip_path}")
    
    # Step 1: Verify signature
    if not verify_update_signature(zip_path, addin_dir):
      safe_log(addin_dir, "Update rejected: invalid signature", "error")
      # Don't delete - leave for inspection
      return False
    
    # Step 2: Get old version for logging
    old_version = get_current_version(addin_dir)
    
    # Step 3: Extract the zip file
    safe_log(addin_dir, "Extracting update files...")
    
    try:
      with zipfile.ZipFile(zip_path, 'r') as zf:
        # Extract all files, overwriting existing
        zf.extractall(addin_dir)
      safe_log(addin_dir, "Extraction completed successfully")
    except zipfile.BadZipFile:
      safe_log(addin_dir, "Update rejected: corrupted zip file", "error")
      return False
    except Exception as e:
      safe_log(addin_dir, f"Extraction failed: {e}", "error")
      return False
    
    # Step 4: Get new version
    new_version = get_current_version(addin_dir)
    
    # Step 5: Delete the zip file
    try:
      os.remove(zip_path)
      safe_log(addin_dir, f"Deleted update zip: {zip_path}")
    except Exception as e:
      safe_log(addin_dir, f"Warning: Could not delete update zip: {e}", "warning")
      # Not a fatal error - update was still applied
    
    safe_log(addin_dir, f"Update applied successfully: {old_version} -> {new_version}")
    return True
    
  except Exception as e:
    safe_log(addin_dir, f"Update failed with unexpected error: {e}", "error")
    return False


def check_and_apply_update(addin_dir: str) -> bool:
  """
  Main entry point: Check for pending update and apply if found.
  
  This should be called at the very start of add-in loading,
  BEFORE any other modules are imported.
  
  Args:
    addin_dir: Path to add-in directory
    
  Returns:
    True if an update was applied, False otherwise
  """
  try:
    # Check for pending update
    update_zip = check_for_pending_update(addin_dir)
    
    if update_zip:
      # Apply the update
      return apply_update(update_zip, addin_dir)
    
    return False
    
  except Exception as e:
    safe_log(addin_dir, f"Update check failed: {e}", "error")
    return False


def download_update_if_available(addin_dir: str, check_interval_hours: int = 24) -> Optional[str]:
  """
  Check for and download updates from the update server.
  
  This function is called AFTER the add-in has started (not in the loader).
  Downloaded updates will be applied on next startup.
  
  Args:
    addin_dir: Path to add-in directory
    check_interval_hours: Hours between update checks (default 24)
    
  Returns:
    Path to downloaded update zip if found, None otherwise
  """
  import urllib.request
  import urllib.error
  import json
  
  # Update URLs
  primary_url_template = "https://update.aurafriday.com/mcplink/update.asp/fusion360_mcp_v{version}-{platform}.zip"
  backup_url_template = "https://aurafriday.github.io/mcp-link-server/updates/fusion360_mcp_v{version}-{platform}.zip"
  
  # State file for tracking update checks
  state_file = os.path.join(addin_dir, "update_state.json")
  
  try:
    # Check if we should check for updates (rate limiting)
    should_check = True
    try:
      if os.path.exists(state_file):
        with open(state_file, 'r', encoding='utf-8') as f:
          state = json.load(f)
        last_check = state.get("lastUpdateCheck")
        if last_check:
          last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
          now = datetime.now(timezone.utc)
          hours_since = (now - last_check_dt).total_seconds() / 3600
          should_check = hours_since >= check_interval_hours
    except Exception:
      pass  # If state file is corrupt, check anyway
    
    if not should_check:
      return None
    
    # Get current version and platform
    version = get_current_version(addin_dir)
    platform_suffix = get_platform_suffix()
    
    safe_log(addin_dir, f"Checking for updates: version {version}, platform {platform_suffix}")
    
    # Update last check time
    try:
      state = {"lastUpdateCheck": datetime.now(timezone.utc).isoformat()}
      with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f)
    except Exception:
      pass
    
    # Try primary URL first
    primary_url = primary_url_template.format(version=version, platform=platform_suffix)
    result = _try_download_update(primary_url, addin_dir)
    
    if result == "downloaded":
      return os.path.join(addin_dir, "fusion360_mcp_update.zip")
    elif result == "no_update":
      safe_log(addin_dir, "No update available - current version is up to date")
      return None
    else:
      # Try backup URL
      backup_url = backup_url_template.format(version=version, platform=platform_suffix)
      backup_result = _try_download_update(backup_url, addin_dir)
      
      if backup_result == "downloaded":
        return os.path.join(addin_dir, "fusion360_mcp_update.zip")
      elif backup_result == "no_update":
        safe_log(addin_dir, "No update available - current version is up to date")
      else:
        safe_log(addin_dir, "Update check failed - servers unavailable", "warning")
      
      return None
      
  except Exception as e:
    safe_log(addin_dir, f"Update download failed: {e}", "error")
    return None


def _try_download_update(url: str, addin_dir: str) -> str:
  """
  Try to download an update from a specific URL.
  
  Args:
    url: URL to download from
    addin_dir: Path to add-in directory
    
  Returns:
    "downloaded" - Update was downloaded successfully
    "no_update" - No update available (404)
    "error" - Network/server error occurred
  """
  import urllib.request
  import urllib.error
  
  try:
    safe_log(addin_dir, f"Trying: {url}")
    
    with urllib.request.urlopen(url, timeout=30) as response:
      if response.status == 200:
        update_zip = os.path.join(addin_dir, "fusion360_mcp_update.zip")
        with open(update_zip, 'wb') as f:
          f.write(response.read())
        safe_log(addin_dir, f"Update downloaded: {update_zip}")
        return "downloaded"
      else:
        return "error"
        
  except urllib.error.HTTPError as e:
    if e.code == 404:
      return "no_update"
    else:
      safe_log(addin_dir, f"HTTP error: {e.code}", "warning")
      return "error"
  except Exception as e:
    safe_log(addin_dir, f"Download error: {e}", "warning")
    return "error"
