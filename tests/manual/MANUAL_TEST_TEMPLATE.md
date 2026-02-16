# Manual test template

## Table of contents

- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Automation runner](#automation-runner)
- [Test procedure](#test-procedure)
- [Results](#results)

## Purpose

Use this template for user acceptance testing that requires the HomeBudget apps. Record the user feedback in the results section.

## Prerequisites

- HomeBudget Windows app installed and running
- HomeBudget mobile app available for sync checks
- Live HomeBudget database configured and connected to the apps
  - Copy `config/hb-config.json.sample` to `%USERPROFILE%/OneDrive/Documents/HomeBudgetData/hb-config.json`
  - Edit the config file to set `db_path` to your operational homebudget.db
  - Or use `--db` flag to specify your operational database path
- Wrapper environment activated

## Automation runner

Use the manual test runner to capture user input and store results.

Run the runner

```bash
python tests/manual/manual_test_runner.py
```

Run a specific test by id

```bash
python tests/manual/manual_test_runner.py --test-id sync_validation
```

## Test procedure

1. User action: capture the current state in the HomeBudget Windows app
2. Automated: run the wrapper command for the target operation
3. Automated: verify SyncUpdate entry in the database
4. User action: confirm the change appears in the Windows app
5. User action: confirm the change appears in the mobile app
6. Record results and any notes

## Results

- Result status
- Notes
- Timestamp
