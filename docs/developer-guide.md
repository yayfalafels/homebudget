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
- [Troubleshooting](#troubleshooting)
- [Reference documents](#reference-documents)

## Overview

This guide supports implementation work for the wrapper. It focuses on local setup, test workflow, and support considerations for development.

## Environments

Use env for all wrapper work. Use .dev env only for helper scripts and diagnostics.

## Setup

Run the setup script to create or update env and install dependencies.

Windows

```bash
\.\scripts\cmd\setup-env.cmd
.\env\Scripts\activate
pip install -e .[dev]
```

Bash

```bash
./.scripts/bash/setup-env.sh
source env/bin/activate
pip install -e .[dev]
```

This installs both runtime and development dependencies from `pyproject.toml`.

use a separate python interpreter environment for development work to avoid conflicts with the HomeBudget app. 
use scripts in `.dev/.scripts/*` and interpreter at `.dev/env` and requirements in `.dev/requirements.txt` for development utilities and diagnostics to keep them separate from the main wrapper code and dependencies. This prevents conflicts with the HomeBudget app's Python environment and allows for safe experimentation with helper tools without risking stability of the wrapper or the app.

## Development workflow

Follow the TDD cycle for each feature.

- Document the feature in user guide and example docs
- Write tests and confirm they fail
- Implement the feature and pass tests
- Validate with manual steps when sync is involved
- Refactor and update documentation
- Keep validation logic in shared utilities for single add and batch operations

## Configuration

The wrapper uses a configuration file for database path and settings. See the [Configuration Guide](configuration.md) for complete setup instructions and all configuration options.

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

**Key manual test artifacts:**

- `tests/manual/manual_tests.json`: Comprehensive UAT test suite definitions
- `tests/manual/manual_test_runner.py`: Test runner for executing UAT tests
- `tests/manual/run_uat_tests.py`: Batch UAT test execution
- `tests/manual/TRANSFER_TEST_CASES.md`: 6 transfer test cases covering valid and invalid scenarios
- `tests/manual/BATCH_TRANSFER_TEST_CASES.md`: Batch transfer tests with currency normalization
- `tests/manual/sync_validation_procedure.md`: Sync validation workflow

**Running UAT tests:**

```bash
# Run a specific UAT test
python tests/manual/manual_test_runner.py --test-id uat_expense_crud
```

**Focus areas for UAT:**

- Sync behavior: Verify SyncUpdate creation and propagation to mobile devices
- Mixed currency transfers: Test currency normalization layer with all input modes
- Batch operations: Test CSV/JSON import and mixed-operation batches with sync optimization
- Forex handling: Verify automatic rate fetching and caching

## Fixtures and test data

System integration tests use headless test databases stored in tests/fixtures (test_database.db, sync_test.db, empty_database.db). SIT tests must copy fixtures into a temporary working directory before writing data.

User acceptance tests use the live operational HomeBudget database configured in the user's environment and connected to the HomeBudget Windows and mobile apps.

## Troubleshooting

- Setup script fails. Confirm Python 3.10 or later is in PATH and rerun the script.
- Tests fail with database locked. Close the HomeBudget app and rerun the tests.
- Sync validation fails. Confirm DeviceInfo is present and sync is enabled for the command.

## Reference documents

- [design](design.md)
- [user guide](user-guide.md)
- [methods](methods.md)
- [sync update](sync-update.md)
- [workflow](workflow.md)
