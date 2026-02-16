# Test strategy

## Table of contents

- [Overview](#overview)
- [System integration tests](#system-integration-tests)
- [User acceptance tests](#user-acceptance-tests)
- [User feedback integration points](#user-feedback-integration-points)
- [Test fixture management](#test-fixture-management)
- [Coverage targets](#coverage-targets)
- [Tooling and execution](#tooling-and-execution)
- [References](#references)

## Overview

This strategy separates system integration tests from user acceptance tests. System integration tests cover data integrity, database operations, and payload encoding. User acceptance tests validate sync behavior and UI verification in the HomeBudget apps.

## System integration tests

System integration tests cover automated database behavior without HomeBudget UI or sync services.

- Unit tests for models, schema constants, exceptions, and utility helpers
- Integration tests for CRUD operations and SyncUpdate payload creation
- CLI tests for command parsing, output formats, and error handling

## User acceptance tests

User acceptance tests require HomeBudget Windows and mobile apps and verify sync and UI behavior.

- Sync confirmation in HomeBudget desktop and mobile apps
- Visual validation of transaction details after wrapper operations
- User confirmation for duplicate prevention behavior

## User feedback integration points

- User acceptance test procedures prompt the user to confirm UI results
- Results are recorded in manual test files with pass or fail notes
- Follow up tasks record issues discovered during manual validation

## Test fixture management

- System integration tests use headless test databases in tests/fixtures (test_database.db, sync_test.db, empty_database.db)
- Each SIT test copies a fixture to a temporary path before modifications
- No test writes directly to a fixture file
- User acceptance tests use the live operational HomeBudget database connected to Windows and mobile apps

## Coverage targets

- System integration tests target at least 85 percent line coverage
- User acceptance tests target all user facing sync workflows

## Tooling and execution

- Use pytest for unit and integration tests
- Use temporary directories for isolated database tests
- Use helper utilities in tests utils for shared assertions and payload decoding

## References

- docs/design.md
- docs/sync-update.md
- docs/test-cases.md
