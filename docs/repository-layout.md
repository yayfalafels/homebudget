# Repository layout

## Overview

This repository contains the HomeBudget Python wrapper for SQLite database access, with CLI and library interfaces.

## Directory structure

```
homebudget/
├── .dev/                    # Development environment (git ignored)
│   ├── env/                 # Python virtual environment
│   ├── logs/                # Development logs and diagnostics
│   ├── .scripts/            # Helper scripts
│   │   ├── python/          # Python helper scripts
│   │   ├── bash/            # Bash scripts
│   │   └── cmd/             # Windows batch scripts
│   └── requirements.txt     # Development dependencies
├── .github/                 # GitHub configuration
│   ├── prompts/             # AI agent prompts
│   └── workflows/           # CI/CD workflows (future)
├── docs/                    # Design and reference documentation
│   ├── index.md
│   ├── cli-guide.md
│   ├── configuration.md
│   ├── dependencies.md
│   ├── design.md
│   ├── developer-guide.md
│   ├── forex-rates.md
│   ├── methods.md
│   ├── repository-layout.md
│   ├── sqlite-schema.md
│   ├── sync-update.md
│   ├── test-cases.md
│   ├── test-guide.md
│   ├── test-strategy.md
│   ├── transfer-currency-normalization.md
│   ├── user-guide.md
│   ├── workflow.md
│   └── tests/               # Test documentation
│       ├── feature_5.1_expense_crud.md
│       ├── feature_5.3_transfer_crud.md
│       ├── sync_validation_procedure.md
│       ├── TRANSFER_TEST_CASES.md
│       └── BATCH_TRANSFER_TEST_CASES.md
├── reference/               # Reference source code used during development
├── src/                     # Source code
│   └── python/              # Python package
│       └── homebudget/      # Main package
│           ├── __init__.py
│           ├── __version__.py
│           ├── client.py
│           ├── models.py
│           ├── sync.py
│           ├── repository.py
│           ├── schema.py
│           ├── exceptions.py
│           ├── cli/         # Command line interface
│           │   ├── __init__.py
│           │   ├── main.py
│           │   ├── commands/
│           │   ├── formatters.py
│           │   └── validators.py
│           └── utils/       # Helper utilities
│               ├── __init__.py
│               ├── currency.py
│               ├── dates.py
│               ├── validation.py
│               └── logging.py
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── fixtures/            # Test fixtures and databases
│   └── conftest.py          # Pytest configuration
├── .gitignore
├── AGENTS.md                # AI agent instructions
├── LICENSE
├── pyproject.toml           # Package configuration
├── README.md                # Project overview and quickstart
├── requirements.txt         # Production dependencies
```

## Key directories

- **src/python/homebudget/** - Main Python package with library and CLI
- **tests/** - Pytest test suite with unit and integration tests
- **docs/** - Complete design documentation and reference materials
- **reference/** - Original implementation for reference only
- **.dev/** - Local development environment (git ignored)