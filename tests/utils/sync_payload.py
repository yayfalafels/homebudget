from __future__ import annotations

import base64
import json
import zlib


def decode_sync_payload(payload: str) -> dict:
    padding = "=" * (-len(payload) % 4)
    raw = base64.b64decode(payload + padding)
    inflated = zlib.decompress(raw, wbits=-zlib.MAX_WBITS)
    return json.loads(inflated.decode("utf-8"))
