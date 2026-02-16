# Configuration files

## hb-config.json.sample

Sample configuration file for the homebudget wrapper.

### Setup for UAT tests

To run user acceptance tests (UAT), you need a live HomeBudget database connected to your HomeBudget apps.

**Option 1: Use the config file (recommended)**

Copy the sample config to your HomeBudget directory:

```powershell
# Windows PowerShell
$configDir = "$env:USERPROFILE\OneDrive\Documents\HomeBudgetData"
New-Item -ItemType Directory -Force -Path $configDir
Copy-Item config\hb-config.json.sample "$configDir\hb-config.json"
```

Edit `%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json` to set the correct path to your operational homebudget.db file.

**Option 2: Use the --db flag**

Specify the database path directly when running UAT commands:

```bash
homebudget --db "C:\path\to\your\homebudget.db" expense list
```

### SIT tests

System integration tests (SIT) do not require hb-config.json. They use headless test fixtures from `tests/fixtures/`.

### Config file format

```json
{
  "db_path": "C:\\Users\\taylo\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db",
  "sync_enabled": true
}
```

- `db_path`: Absolute path to your operational HomeBudget database (typically in `%USERPROFILE%\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db`)
- `sync_enabled`: Enable sync payload creation (set to `true` for UAT)
