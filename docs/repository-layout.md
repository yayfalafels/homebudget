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
│   ├── about.md
│   ├── dependencies.md
│   ├── homebudget.md
│   ├── repository-layout.md
│   ├── sqlite-schema.md
│   ├── sync-update.md
│   ├── test-cases.md
│   ├── workflow.md
│   ├── develop/             # Development process docs
│   │   ├── backlog.md
│   │   └── environment.md
│   │   ├── environment-verification.md
│   │   ├── IMPLEMENTATION_LOG.md
│   │   ├── plan-wrapper-design-step2.md
│   │   ├── plan-wrapper-design-step3.md
│   │   ├── plan-wrapper-design-step4.md
│   │   ├── plan-wrapper-design-step5.md
│   │   ├── plan-wrapper-design-step6.md
│   │   ├── plan-wrapper-design-step7.md
│   │   ├── plan-wrapper-design-step8.md
│   │   ├── plan-wrapper-design-step9.md
│   │   └── plan-wrapper-design-summary.md
│   ├── issues/              # Issue tracking and diagnostics
│   │   ├── 001-sync-detection.md
│   │   └── 001-sync-detection-diagnostics.md
├── reference/               # Reference implementation (archived)
│   ├── hb-finances/         # Original Python wrapper
│   ├── hb-sqlite-db/        # Sample HomeBudget database
│   ├── sync-demo/           # Sync diagnostics snapshots
│   └── HomeBudget_Windows_guide.md
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
├── CHANGELOG.md             # Version history
├── LICENSE
├── pyproject.toml           # Package configuration
├── README.md                # Project overview and quickstart
├── requirements.txt         # Production dependencies
└── VERSION                  # Version number
```

## Key directories

- **src/python/homebudget/** - Main Python package with library and CLI
- **tests/** - Pytest test suite with unit and integration tests
- **docs/** - Complete design documentation and reference materials
- **reference/** - Original implementation for reference only
- **.dev/** - Local development environment (git ignored)

## Design documentation

The wrapper design is documented in a series of step documents:

- [plan-wrapper-design-step2.md](develop/plan-wrapper-design-step2.md) - Source inventory and gap log
- [plan-wrapper-design-step3.md](develop/plan-wrapper-design-step3.md) - SQLite schema and data model mapping
- [plan-wrapper-design-step4.md](develop/plan-wrapper-design-step4.md) - Core API surface and module boundaries
- [plan-wrapper-design-step5.md](develop/plan-wrapper-design-step5.md) - Idempotency and conflict strategy
- [plan-wrapper-design-step6.md](develop/plan-wrapper-design-step6.md) - CLI UX and command map
- [plan-wrapper-design-step7.md](develop/plan-wrapper-design-step7.md) - Packaging and repository layout
- [plan-wrapper-design-step8.md](develop/plan-wrapper-design-step8.md) - Testing and validation strategy
- [plan-wrapper-design-step9.md](develop/plan-wrapper-design-step9.md) - Design documentation and rollout

See [plan-wrapper-design-step9.md](develop/plan-wrapper-design-step9.md) for the complete design summary and implementation roadmap.