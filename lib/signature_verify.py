# -*- coding: utf-8 -*-
"""
File: signature_verify.py
Project: MCP-Link Fusion 360 Add-in
Component: Signature Verification Module (STATIC - never updated via zip)
Author: Christopher Nathan Drake (cnd)
Created: 2025-01-07
SPDX-License-Identifier: Proprietary
Copyright: (c) 2025 Aura Friday. All rights reserved.

This module provides cryptographic signature verification for update files.
It uses RSA signatures with a custom base-256 encoding and rolling digest.

IMPORTANT: This file should NEVER be updated via the auto-update system.
It is part of the static loader that verifies updates before applying them.
"""

import re
from typing import Optional, Tuple

# Public key for verifying Aura Friday signatures
# Format: exponent|modulus (both base-256 encoded)
PUBLIC_KEY = "j|𝟥ȣоSȜƐꓦᏴԝԛƊᴛꞇyᒿƽEkꙄÞⲞꓳFᎬȣƟτⲟƻƛꓠꓖⅠΝZϨIƋᎠᗷ𝟫ᒿƨⴹⲦꞇhƨϜeЈZƐƱ𝟦Ꮾһßх𝟧4ΗȜΒFɋĵµBոRꓳgPɌЗꓟ𝟧wƟƘⲘPȣznŧВeꞇƻƐ𝕌оDᑕВԛÞΗ𝖠ᒿɌоⲢıΡυꞇ"

# Salt used in rolling digest calculation
DIGEST_SALT = "The×second×most×intelligent×dolphins×encrypted×their×squeaks×just×to×confuse×the×mice×monitoring×human×dreams"


class BaseNCodec:
  """Base-256 codec for signature encoding/decoding."""
  
  # Default collation alphabet from base_n_codec.js
  DEFAULT_ALPHABET = (
      "0123456789abcdef"  # 1 .. 15
      "ghijklmnopqrstuv"  # 16 .. 31
      "wxyzABCDEFGHIJKL"  # 32 .. 47
      "MNOPQRSTUVWXYZɅƱ"  # 48 .. 63
      "ΗꓑοƶƳᖴʋꓟ𐓒ԝꓦʈՕЅΒЈ"  # 64 .. 79
      "ѡΟеƿⅠυµıΕꞇ𝟩ⴹꓐꓪǝᴠ"  # 80 .. 95
      "𝟤ꓔÞųƟⲔВᏂ×ƧωƘꓠƏСЕ"  # 96 .. 111
      "ƐᴡꙄᛕꓧꜱ𝛢𝟟ƬƲᴛОƛɊȜр"  # 112 .. 127
      "Ϝ𝟧ƤƊɯᏴօĐսΡᎬꓚ𝟥у𝘈ꓬ"  # 128 .. 143
      "τÐɌɗΑΥƵⲘ𝐴ᎪРᴅᏮᴜνЗ"  # 144 .. 159
      "ѵⅼһƦƽМ𝕌ꓮꙅƴƖⲟⲦꓴᏟᗷ"  # 160 .. 175
      "ҮĸⲢꓗΤƼᗞƎꓰȣʌԛКΝƋո"  # 176 .. 191
      "৭ƙĵҳꓖоАᏎⲞхģᎻ𝟦𝖠Ƞȷ"  # 192 .. 207
      "ďȢӠϹ𝟨ᗅ𝟙ɪց𝟫Ϩꓓ𐐕Ꭰԁ𝟑"  # 208 .. 223
      "μƨ𝟪ꓝɋƌƻⅮΜɡΚ𝟢Нᒿþꓜ"  # 224 .. 239
      "ꓳ𝟣ꓣᴍᗪ𝙰бТŪī𝟛ŧß𝟚ᑕƍ"  # 240 .. 255
      "𐌣øĳƚƾ"  # spares
  )


  def __init__(self, base: int = 256, alphabet: Optional[str] = None):
    """Initialize codec with given base and optional alphabet."""
    if base < 2:
      raise ValueError("Base must be >= 2")
    
    self.base = base
    self.alphabet = alphabet or self.DEFAULT_ALPHABET
    
    # Create lookup maps
    self.char_to_value = {}
    self.value_to_char = []
    
    # Split alphabet into Unicode code points
    chars = list(self.alphabet)
    if len(chars) < base:
      raise ValueError(f"Alphabet too short: needs {base} chars but only has {len(chars)}")
    
    # Build lookup tables
    seen_chars = set()
    for i in range(base):
      char = chars[i]
      if char in seen_chars:
        raise ValueError(f"Duplicate character in alphabet: {char}")
      seen_chars.add(char)
      self.char_to_value[char] = i
      self.value_to_char.append(char)

  def decode(self, s: str) -> int:
    """Convert a base-N string back to an integer."""
    result = 0
    for char in s:
      val = self.char_to_value.get(char)
      if val is None:
        raise ValueError(f"Invalid character '{char}' in input")
      result = result * self.base + val
    return result

  def encode(self, n: int) -> str:
    """Convert an integer to a base-N string."""
    if n < 0:
      raise ValueError("Negative values not supported")
    if n == 0:
      return self.value_to_char[0]
    
    result = []
    while n > 0:
      n, rem = divmod(n, self.base)
      result.append(self.value_to_char[rem])
    return ''.join(reversed(result))


def _process_data_for_signature(data: bytes, modulus: int) -> Tuple[int, Optional[int]]:
  """
  Calculate rolling digest and extract signature from file data.
  
  Args:
    data: Raw file bytes
    modulus: RSA modulus for digest calculation
    
  Returns:
    Tuple of (calculated_digest, extracted_signature_value)
    extracted_signature_value is None if no signature found
  """
  codec = BaseNCodec(256)
  
  # Initialize digest with salt
  rolling_digest = codec.decode(DIGEST_SALT)
  
  # Find signature in data
  sig_match = re.search(rb'"signature"\s*:\s*"([^"]+)"', data)
  if sig_match:
    sig_start = sig_match.start(1)
    sig_end = sig_match.end(1)
    signature = sig_match.group(1).decode('utf-8')
  else:
    sig_start = sig_end = -1
    signature = None
  
  # Calculate rolling digest, skipping signature bytes
  virtual_index = 0
  for i, b in enumerate(data):
    # Skip signature bytes (they change when signing)
    if sig_start >= 0 and sig_end >= 0 and sig_start <= i < sig_end:
      continue
    
    # Process this byte into digest
    remainder = rolling_digest % 256
    xor_result = b ^ remainder
    with_index = xor_result + virtual_index
    multiplied = with_index * 281
    
    # Update rolling digest
    rolling_digest = (rolling_digest * 256 + multiplied) % modulus
    virtual_index += 1
  
  # Decode signature if found
  extracted_sig = None
  if signature:
    try:
      extracted_sig = codec.decode(signature)
    except ValueError:
      pass  # Invalid signature encoding
  
  return rolling_digest, extracted_sig


def verify_signature_bytes(data: bytes) -> bool:
  """
  Verify the signature on raw file data.
  
  Args:
    data: Raw file bytes containing embedded signature
    
  Returns:
    True if signature is valid, False otherwise
  """
  try:
    codec = BaseNCodec(256)
    
    # Parse public key
    key_parts = PUBLIC_KEY.split('|')
    if len(key_parts) != 2:
      return False
    
    exponent = codec.decode(key_parts[0])
    modulus = codec.decode(key_parts[1])
    
    # Process file and extract signature
    calculated_digest, extracted_sig = _process_data_for_signature(data, modulus)
    
    if not extracted_sig:
      return False
    
    # RSA verify: decrypt signature with public key
    # Python's pow(base, exp, mod) does modular exponentiation efficiently
    decrypted_digest = pow(extracted_sig, exponent, modulus)
    
    return decrypted_digest == calculated_digest
    
  except Exception:
    return False


def verify_signature_file(filepath: str) -> bool:
  """
  Verify the signature on a file.
  
  Args:
    filepath: Path to file containing embedded signature
    
  Returns:
    True if signature is valid, False otherwise
  """
  try:
    with open(filepath, 'rb') as f:
      data = f.read()
    return verify_signature_bytes(data)
  except Exception:
    return False
