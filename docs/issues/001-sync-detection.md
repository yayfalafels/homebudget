# Issue 001: Sync Detection

## Status: RESOLVED

**Resolution date**: 2026-02-17

**Root cause**: Wrapper failed to create SyncUpdate entries with correctly formatted payloads

**Solution**: Implemented SyncUpdate payload generation matching native app format:
- Full zlib compression with header (wbits=15)
- URL-safe base64 encoding
- Fixed 660-byte padding before base64 encoding (produces 880-char strings)

**Validation**: Mobile sync confirmed working with corrected payload format

## Situation

After adding new expenses via the HB Wrapper v1.0, the changes are not synced to all devices.

## Steps to reproduce

1. add expenses via the HB Wrapper v1.0 on desktop
2. verify expenses added on desktop
3. observe changes not synced to mobile app
4. verify changes reflected via manual restore

## Diagnostics

**diagnostic questions**

1. is the sync detection logic represented in the sqlite database, or a process in the HomeBudget application?
2. if the sync is represented in the sqlite database, which tables and columns indicate a new change pending sync?

**Answers**:

1. Sync detection is driven by the SyncUpdate table in the SQLite database
2. Each transaction requires a SyncUpdate entry with a base64-encoded, zlib-compressed JSON payload containing the operation details and device identifiers
