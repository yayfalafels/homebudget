# Sync validation procedure

## Table of contents

- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Test procedure](#test-procedure)
- [Results](#results)

## Purpose

User acceptance test to validate that SyncUpdate entries created by the wrapper appear in the HomeBudget apps.

## Prerequisites

- HomeBudget Windows app installed and running
- HomeBudget mobile app available for sync checks
- Live HomeBudget database configured and connected to the apps
  - Copy `config/hb-config.json.sample` to `%USERPROFILE%/OneDrive/Documents/HomeBudgetData/hb-config.json`
  - Edit the config file to set `db_path` to your operational homebudget.db
  - Or use `--db` flag to specify your operational database path
- Wrapper environment activated

## Test procedure

1. User action: record the current transaction count in the Windows app
2. Automated: add a test expense with the wrapper
3. Automated: verify a new SyncUpdate entry exists
4. User action: confirm the new expense appears in the Windows app
5. User action: wait for sync and confirm the expense appears in the mobile app
6. Record results and any notes

## Results

- Result status
- Notes
- Timestamp
