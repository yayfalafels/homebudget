# HomeBudget wrapper developer guide

## Table of contents

- [Overview](#overview)
- [Environments](#environments)
- [Setup](#setup)
- [Development workflow](#development-workflow)
- [Configuration](#configuration)
- [Testing](#testing)
- [Manual validation](#manual-validation)
- [Fixtures and test data](#fixtures-and-test-data)
- [Quality checks](#quality-checks)
- [Troubleshooting](#troubleshooting)
- [Reference documents](#reference-documents)

## Overview

This guide supports implementation work for the wrapper. It focuses on local setup, test workflow, and support considerations for development.

## Environments

Use env for all wrapper work. Use .dev env only for helper scripts and diagnostics.

## Setup

Run the setup script to create or update env and install requirements.

Windows

```bash
.\.scripts\cmd\setup-env.cmd
.\env\Scripts\activate
```

Bash

```bash
./.scripts/bash/setup-env.sh
source env/bin/activate
```

## Development workflow

Follow the TDD cycle for each feature.

- Document the feature in user guide and example docs
- Write tests and confirm they fail
- Implement the feature and pass tests
- Validate with manual steps when sync is involved
- Refactor and update documentation
- Keep validation logic in shared utilities for single add and batch operations

## Configuration

The wrapper uses a user config JSON file for HomeBudget settings such as the database path. A sample config is provided in `config/hb-config.json.sample`.

Config file path
- %USER_PROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json

Default database path
- %USER_PROFILE%\OneDrive\Documents\HomeBudgetData\Data\homebudget.db

See [config/README.md](../config/README.md) for setup instructions.

## Testing

Run unit and integration tests using pytest.

```bash
pytest tests/unit -v
pytest tests/integration -v
```

Run tests for a single feature when needed.

```bash
pytest tests/integration/test_expense_crud.py -v
```

## Manual validation

Manual validation is required for sync confirmation in the HomeBudget apps. Use the manual test procedures in tests/manual and record results.

## Fixtures and test data

System integration tests use headless test databases stored in tests/fixtures (test_database.db, sync_test.db, empty_database.db). SIT tests must copy fixtures into a temporary working directory before writing data.

User acceptance tests use the live operational HomeBudget database configured in the user's environment and connected to the HomeBudget Windows and mobile apps.

## Quality checks

Run these checks before committing.

```bash
black src/python/homebudget tests
ruff check src/python/homebudget
mypy src/python/homebudget
```

## Troubleshooting

- Setup script fails. Confirm Python 3.10 or later is in PATH and rerun the script.
- Tests fail with database locked. Close the HomeBudget app and rerun the tests.
- Sync validation fails. Confirm DeviceInfo is present and sync is enabled for the command.

## Reference documents

- docs/design.md
- docs/user-guide.md
- docs/methods.md
- docs/sync-update.md
- docs/workflow.md
