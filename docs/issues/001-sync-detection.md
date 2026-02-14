# Issue 001: Sync Detection

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
