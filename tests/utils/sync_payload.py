from __future__ import annotations

import base64
import json
import zlib


def decode_sync_payload(payload: str) -> dict:
    """Decode HomeBudget sync payload using URL-safe base64 and full zlib format.
    
    HomeBudget uses:
    - URL-safe base64 encoding (- and _ instead of + and /)
    - Full zlib format (wbits=15) with header and checksum
    - 512-byte minimum padding with null bytes (smaller payloads only)
    - Variable payload sizes: 683-920 chars typical (Delete/Income/Transfer smaller)
    """
    cleaned = payload.strip()
    
    # Convert from URL-safe base64 to standard base64
    cleaned = cleaned.replace('-', '+').replace('_', '/')
    
    # Add padding if needed
    padding = '=' * (-len(cleaned) % 4)
    cleaned = cleaned + padding
    
    # Decode base64
    raw = base64.b64decode(cleaned)
    
    # Strip trailing null bytes (512-byte minimum padding for smaller payloads)
    raw = raw.rstrip(b'\x00')
    
    # Decompress using full zlib format (wbits=15)
    inflated = zlib.decompress(raw, wbits=15)
    
    # Parse JSON
    return json.loads(inflated.decode('utf-8'))
