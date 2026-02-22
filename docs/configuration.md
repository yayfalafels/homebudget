# Configuration Guide

## Overview

The HomeBudget wrapper uses a JSON configuration file to manage database paths, sync settings, and forex preferences. This eliminates the need to specify these settings for every command.

## Configuration File Location

**Default path:**
```
%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json
```

**Alternative locations checked (in order):**
1. Path specified by `HB_CONFIG` environment variable
2. Default path shown above

## Configuration File Format

**Complete configuration example:**

```json
{
  "db_path": "C:\\Users\\taylo\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db",
  "sync_enabled": true,
  "base_currency": "SGD",
  "forex": {
    "cache_ttl_hours": 1
  }
}
```

### Configuration Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `db_path` | string | Yes | N/A | Absolute path to HomeBudget database file |
| `sync_enabled` | boolean | No | `true` | Enable/disable SyncUpdate creation |
| `base_currency` | string | No | From DB | Base currency code (e.g., "SGD", "USD") |
| `forex.cache_ttl_hours` | number | No | `1` | Forex rate cache validity in hours |

**Default database path:**
```
%USERPROFILE%\OneDrive\Documents\HomeBudgetData\Data\homebudget.db
```

## Setup Instructions

### First-Time Setup

**Create configuration directory and file:**

```powershell
# Windows PowerShell
$configDir = "$env:USERPROFILE\OneDrive\Documents\HomeBudgetData"
New-Item -ItemType Directory -Force -Path $configDir
Copy-Item config\hb-config.json.sample "$configDir\hb-config.json"
```

**Edit the configuration file:**

Open `%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json` and update:

1. Set `db_path` to your operational HomeBudget database location
2. Verify `base_currency` matches your database
3. Adjust `sync_enabled` if needed (default: `true`)

### UAT (User Acceptance Testing) Setup

For UAT tests with live database and mobile sync:
- Set `db_path` to operational database
- Set `sync_enabled` to `true`
- Ensure HomeBudget apps (Windows and mobile) use the same database

### SIT (System Integration Testing) Setup

For SIT tests with headless fixtures:
- No configuration file needed
- Tests use fixtures from `tests/fixtures/`
- Configuration is ignored during SIT

## Using Configuration

### With API

Configuration is loaded automatically when creating a client:

```python
from homebudget import HomeBudgetClient

# Uses config file automatically
with HomeBudgetClient() as client:
    expenses = client.list_expenses()
```

**Override with explicit path:**

```python
# Ignore config file, use explicit path
with HomeBudgetClient(db_path="C:/path/to/homebudget.db") as client:
    expenses = client.list_expenses()
```

### With CLI

Configuration is loaded automatically for all commands:

```bash
# Uses config file automatically
homebudget expense list --limit 10
```

**Override with `--db` flag:**

```bash
# Ignore config file, use explicit path
homebudget --db "C:\path\to\homebudget.db" expense list
```

## Configuration Behavior

### Loading Priority

The wrapper loads configuration in this order (first found wins):

1. **Explicit parameter**: API `db_path` parameter or CLI `--db` flag
2. **Environment variable**: `HB_CONFIG` pointing to config file
3. **Default location**: `%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json`

### Sync Control

Sync behavior is determined by configuration:

1. **Config file**: `sync_enabled` setting (default: `true`)
2. **Default**: `true` if not specified

Sync is always enabled via CLI and cannot be disabled to ensure consistency between local and remote devices.

### Missing Configuration

**If no configuration file exists:**

- API: Must provide `db_path` parameter, or will raise error
- CLI: Must provide `--db` flag, or will raise error

## Sample Configuration File

A complete sample is provided at `config/hb-config.json.sample`:

```json
{
  "db_path": "C:\\Users\\USERNAME\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db",
  "sync_enabled": true,
  "base_currency": "SGD",
  "forex": {
    "cache_ttl_hours": 1
  }
}
```

**To use:**

1. Copy to the default location
2. Replace `USERNAME` with your actual username
3. Adjust paths and currency as needed

## Troubleshooting

### "Config file not found" Error

**Problem:** CLI or API cannot locate configuration file.

**Solution:**

- Check file exists at default location
- Verify path in error message
- Use `--db` flag or `db_path` parameter as workaround

### "Database path not in config" Error

**Problem:** Config file exists but `db_path` field is missing.

**Solution:**

- Open config file
- Add `"db_path": "C:\\path\\to\\homebudget.db"`
- Ensure path uses double backslashes on Windows

### Sync Not Working

**Problem:** Changes don't appear in mobile app.

**Solution:**

- Verify `sync_enabled: true` in config
- Confirm DeviceInfo exists in database
- Verify mobile app uses same database

## Related Documentation

- [User Guide](user-guide.md) - Getting started and usage examples
- [Developer Guide](developer-guide.md) - Development workflow and testing
- [CLI Examples](cli-examples.md) - Command-line usage examples
- [Sync Update Mechanism](sync-update.md) - How sync works
