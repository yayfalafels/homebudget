# Issue 001: Sync Detection

## Status

Resolved on 2026-02-17

## Summary

Wrapper created expenses but mobile devices did not receive updates. Sync detection is driven by SyncUpdate entries, so missing entries and mismatched payload encoding prevented the sync service from accepting wrapper changes.

## Resolution

- Added SyncUpdate creation for each operation
- Aligned payload JSON structure with native app rules per operation
- Corrected encoding to use full zlib format, URL safe base64, and operation specific padding rules
- Confirmed mobile sync success after applying fixes

## Diagnostics findings

- Sync detection is driven by the SyncUpdate table in SQLite
- SyncInfo and DeviceInfo do not trigger sync and remained unchanged during tests
- Payloads must match native app structure for each operation, including key field formats
- Encoding must use full zlib format and URL safe base64 with trailing padding removed
- Update operations emit one sync entry per changed attribute

## References

- [Issue 001 Sync Detection Diagnostics](001-sync-detection-diagnostics.md)
- [Sync Update Mechanism](../sync-update.md)
