---
name: plan-wrapper-implementation
description: This prompt guides TDD implementation of the Python wrapper, following user guide documentation → test cases → build → validate workflow for each feature.
model: Auto (copilot)
agent: agent
---

## Plan: Python Wrapper Implementation with TDD

This plan implements the wrapper design using Test-Driven Development (TDD) workflow. Each feature follows the cycle: user guide documentation → test cases → implementation → validation. Testing is hybrid: automated scripts plus manual user feedback from HomeBudget UI.

The implementation follows the consolidated design in [docs/design.md](docs/design.md), with support from [docs/developer-guide.md](docs/developer-guide.md) and [docs/user-guide.md](docs/user-guide.md).

## Environment usage

**CRITICAL: Environment management rules**

1. **Development scaffolding** (construction tools, temporary only)
   - `.dev/env` — Python virtual environment for helper scripts ONLY
   - `.dev/.scripts/python` — Helper scripts for diagnostics, analysis, PDF extraction
   - `.dev/.scripts/bash` — Bash helper scripts
   - `.dev/.scripts/cmd` — Windows batch helper scripts
   - **DO NOT CREATE A NEW VIRTUAL ENV** - Reuse existing `.dev/env`
   - **DO NOT USE `.dev/env` FOR MAIN APP** - This is scaffolding only

2. **Main application environment** (production runtime)
   - `env/` — Python virtual environment for wrapper package and tests (root level)
   - Used by: wrapper package, test scripts, CLI commands
   - This is the "finished building" environment

**Metaphor:** `.dev/` is scaffolding and cranes during construction. `env/` is the finished building's electrical and plumbing systems.

## Environment setup scripts

Use setup scripts in `.scripts/cmd` and `.scripts/bash` to create and configure the main virtual environment at `env`. The scripts must follow these rules.

- Read dependencies from `requirements.txt`
- Check if `env` exists before each step and skip when already complete
- Steps include creation, activation, and dependency install
- Catch errors and print clear guidance for users
- Never touch `.dev/env`

**Directory structure**
```
homebudget/
├── .dev/                    # Construction scaffolding (git ignored)
│   ├── env/                 # Helper scripts env only
│   ├── .scripts/            # Helper scripts
│   └── requirements.txt     # Helper script dependencies
├── env/                     # Main application env (git ignored)
│   └── ...                  # Wrapper package + test dependencies
├── src/python/homebudget/   # Wrapper package
├── tests/                   # Test suite (uses env/)
├── requirements.txt         # Main app production dependencies
└── pyproject.toml           # Package configuration
```

## Implementation workflow

**Phases**

0. Prerequisites and environment setup
1. User guide and entry points documentation
2. Test strategy and tooling framework
3. Foundation test cases and implementation
4. Packaging and distribution setup
5. Feature implementation (TDD cycles)
6. Integration and validation

Each feature follows TDD cycle:
1. **Document** - User guide section describing feature
2. **Test** - Write test cases (unit + integration)
3. **Build** - Implement to pass tests
4. **Validate** - Run tests + manual HB UI verification
5. **Refactor** - Clean up and optimize
6. **Commit** - Move to next feature

### Phase 0: Prerequisites and environment setup

**Goal**
Verify development environment and create main application environment.

**Inputs**
- [docs/develop/environment.md](docs/develop/environment.md)
- [docs/design.md](docs/design.md)
- [docs/developer-guide.md](docs/developer-guide.md)
- Existing [.dev/env](.dev/env) virtual environment

**Process**
1. Verify `.dev/env` exists from design phase and do not create new
2. Create setup scripts in `.scripts/cmd` and `.scripts/bash` for `env`
3. Run setup script to create and configure `env`
4. Install package build tools in main `env`
5. Verify Python version 3.10 or higher
6. Verify SQLite version 3.35 or higher
7. Create `.gitignore` entries for both environments

**Expected outputs**
- Main `env/` virtual environment created and activated
- Build tools installed: `pip install build setuptools wheel`
- Environment verification report
- Updated `.gitignore` with `env/` and `.dev/` entries
- Setup scripts for Windows and Bash

**Structured prompt**
```
Set up the main application environment:
1. Verify .dev/env exists from design phase (DO NOT CREATE)
2. Create setup scripts in .scripts/cmd and .scripts/bash
   - Use requirements.txt for dependencies
   - Check if env exists before each step and skip as needed
   - Steps include creation, activation, and dependency install
   - Catch errors and print clear help for users
3. Run the setup script to create and configure env
4. Activate env and install: build, setuptools, wheel
5. Verify Python version 3.10 or higher
6. Verify SQLite version 3.35 or higher by running python -c "import sqlite3; print(sqlite3.sqlite_version)"
7. Add env/ and .dev/ to .gitignore if not present
8. Document environment paths in a verification report

CRITICAL: Use env/ for all wrapper and test work. Reserve .dev/env for helper scripts only.
```

**Validation**
- [ ] `.dev/env` exists and functional
- [ ] `env/` created with Python 3.10+
- [ ] Build tools installed in `env/`
- [ ] SQLite 3.35+ available
- [ ] `.gitignore` updated
- [ ] Setup scripts exist and run without errors

### Phase 1: User guide and entry points documentation

**Goal**
Document user-facing features and workflows based on design and HomeBudget guide.

**Inputs**
- [docs/design.md](docs/design.md)
- [docs/developer-guide.md](docs/developer-guide.md)
- [docs/user-guide.md](docs/user-guide.md)
- [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md)
- [docs/workflow.md](docs/workflow.md)

**Process**
1. Create user guide outline in `docs/user-guide.md`
2. Document API entry points with examples
3. Document CLI commands with usage examples
4. Document workflows from [workflow.md](docs/workflow.md)
5. Map HomeBudget UI features to wrapper operations
6. Create a method list from design step 4
7. Create a developer guide for implementation support
8. Document user config JSON and default db path

**Expected outputs**
- `docs/user-guide.md` - Comprehensive user documentation
- `docs/api-examples.md` - Code examples for library usage
- `docs/cli-examples.md` - CLI usage patterns
- `docs/methods.md` - Method list for API surface
- `docs/developer-guide.md` - Implementation and development support guide
- Feature-to-workflow mapping table

**Structured prompt**
```
Create user-facing documentation for the wrapper:
1. Create docs/user-guide.md with sections:
   - Getting started
   - Installation
   - Basic usage (API and CLI)
   - Common workflows
   - Troubleshooting
2. Create docs/api-examples.md with code examples for:
   - Adding expenses, income, transfers
   - Querying transactions
   - Reference data lookups
3. Create docs/cli-examples.md with command examples for:
   - All CRUD operations
   - Batch imports
   - Output format options
4. Create docs/methods.md with method lists from design step 4
5. Create docs/developer-guide.md for implementation support
6. Document user config JSON and default db path
7. Map HomeBudget UI operations to wrapper methods
   
Use design documents and workflow.md as source material.
```

**Validation**
- [ ] user-guide.md complete and readable
- [ ] API examples are syntactically correct
- [ ] CLI examples align with step 6 design
- [ ] Workflow mapping matches workflow.md
- [ ] methods.md matches step 4 method list
- [ ] developer-guide.md supports implementation workflow
- [ ] config file guidance matches design

### Phase 2: Test strategy and tooling framework

**Goal**
Define hybrid testing approach and build test infrastructure.

**Inputs**
- [docs/design.md](docs/design.md)
- [docs/developer-guide.md](docs/developer-guide.md)
- [docs/user-guide.md](docs/user-guide.md)
- [docs/sync-update.md](docs/sync-update.md)
- [reference/hb-sqlite-db](reference/hb-sqlite-db)

**Process**
1. Create test strategy document
2. Define automated vs manual test boundaries
3. Build test fixture framework
4. Create user feedback test templates
5. Set up pytest configuration

**Expected outputs**
- `docs/test-strategy.md` - Hybrid test approach
- `tests/conftest.py` - Pytest configuration
- `tests/fixtures/` - Test databases
- `tests/manual/` - Manual test procedures with user prompts
- Test utility functions

**Structured prompt**
```
Activate main env/ and create test strategy and infrastructure:

1. Create docs/test-strategy.md covering:
   - Automated test scope (unit, integration)
   - Manual test scope (HB UI sync validation)
   - User feedback integration points
   - Test fixture management
   - Coverage targets (85% automated)

2. Create tests/conftest.py with:
   - Pytest configuration
   - Fixture for isolated test databases
   - Fixture for sample data
   - Cleanup hooks

3. Create test fixtures:
   - tests/fixtures/test_database.db (from reference DB)
   - tests/fixtures/empty_database.db (schema only)
   - tests/fixtures/sync_test.db (with DeviceInfo)

4. Create tests/manual/ with templates:
   - MANUAL_TEST_TEMPLATE.md (user prompt → automation → user verify)
   - sync_validation_procedure.md (Issue 001 verification)

5. Create tests/utils/ helper functions:
   - Database setup/teardown
   - Payload decoder for SyncUpdate validation
   - Assertion helpers

Use main env/ for pytest and test dependencies.
```

**Validation**
- [ ] test-strategy.md defines hybrid approach clearly
- [ ] conftest.py loads and test fixtures work
- [ ] Manual test templates guide user interaction
- [ ] Test utils support automated assertions

### Phase 3: Foundation test cases and implementation

**Goal**
Implement core infrastructure with TDD: models, schema, exceptions, repository foundation.

**TDD Cycle for each component:**

#### 3.1: Models and DTOs

**Document**
- Define ExpenseDTO, IncomeDTO, TransferDTO in user-guide.md

**Test first**
```python
# tests/unit/test_models.py
def test_expense_dto_required_fields():
    """ExpenseDTO accepts required fields only."""
    
def test_expense_dto_validation():
    """ExpenseDTO validates field constraints."""
    
def test_expense_dto_all_fields():
    """ExpenseDTO accepts all optional fields."""
```

**Build**
- Implement `src/python/homebudget/models.py`
- Define dataclasses with validation

**Validate**
- Run: `pytest tests/unit/test_models.py`
- All tests pass

#### 3.2: Schema constants

**Test first**
```python
# tests/unit/test_schema.py
def test_expense_table_fields():
    """Schema defines all Expense table fields."""
    
def test_transaction_types():
    """Schema defines transType constants."""
```

**Build**
- Implement `src/python/homebudget/schema.py`

**Validate**
- Run: `pytest tests/unit/test_schema.py`

#### 3.3: Custom exceptions

**Test first**
```python
# tests/unit/test_exceptions.py
def test_duplicate_error_details():
    """DuplicateError includes matched transaction details."""
```

**Build**
- Implement `src/python/homebudget/exceptions.py`

**Validate**
- Run: `pytest tests/unit/test_exceptions.py`

#### 3.4: Repository foundation

**Test first**
```python
# tests/integration/test_repository_connection.py
def test_repository_connection(test_db_path):
    """Repository connects to SQLite database."""
    
def test_repository_read_accounts(test_db_path):
    """Repository reads Account table."""
```

**Build**
- Implement `src/python/homebudget/repository.py` (connection only)

**Validate**
- Run: `pytest tests/integration/test_repository_connection.py`

**Expected outputs from Phase 3**
- `src/python/homebudget/models.py` - All DTOs
- `src/python/homebudget/schema.py` - Schema constants
- `src/python/homebudget/exceptions.py` - Custom exceptions
- `src/python/homebudget/repository.py` - Connection foundation
- Unit and integration tests passing

**Structured prompt**
```
Using main env/, implement foundation with TDD:

For each component (models, schema, exceptions, repository):
1. Write test cases first in tests/unit/ or tests/integration/
2. Run tests (they should fail initially)
3. Implement component in src/python/homebudget/
4. Run tests until all pass
5. Refactor if needed
6. Commit and move to next component

Follow design documents:
- Models: docs/design.md and docs/methods.md
- Schema: docs/design.md and docs/sqlite-schema.md
- Exceptions: docs/design.md
- Repository: docs/design.md

Track progress: Create checklist in logs and mark each component complete.
```

**Validation checklist**
- [ ] All test files created in tests/
- [ ] All implementation files created in src/python/homebudget/
- [ ] `pytest tests/unit/` passes 100%
- [ ] `pytest tests/integration/test_repository_connection.py` passes
- [ ] Code formatted with black
- [ ] Type checks pass with mypy

### Phase 4: Packaging and distribution setup

**Goal**
Create installable package structure.

**Inputs**
- [docs/design.md](docs/design.md)
- [docs/developer-guide.md](docs/developer-guide.md)

**Process**
1. Create `pyproject.toml`
2. Create `src/python/homebudget/__init__.py`
3. Create `requirements.txt`
4. Test local installation

**Expected outputs**
- `pyproject.toml` - Package configuration
- `src/python/homebudget/__init__.py` - Package exports
- `src/python/homebudget/__version__.py` - Version string
- Installable package

**Structured prompt**
```
Using main env/, set up packaging:

1. Create pyproject.toml following step 7 design:
   - Package metadata
   - Dependencies (click>=8.1.0)
   - Entry points (homebudget, hb)
   - Tool configurations (black, ruff, mypy, pytest)

2. Create src/python/homebudget/__init__.py:
   - Import and export public API
   - Version string

3. Create src/python/homebudget/__version__.py:
   - __version__ = "0.1.0-dev"

4. Create requirements.txt:
   - click>=8.1.0

5. Test installation:
   - Activate main env/
   - pip install -e src/python
   - Verify: python -c "import homebudget; print(homebudget.__version__)"

Follow design: docs/design.md
```

**Validation**
- [ ] `pip install -e src/python` succeeds
- [ ] `import homebudget` works
- [ ] `homebudget.__version__` defined
- [ ] Package structure matches step 7 design

### Phase 5: Feature implementation (TDD cycles)

Each feature follows this workflow:

**Feature workflow template**
1. **Document** - Update user-guide.md with feature description
2. **Test (Manual)** - Create manual test procedure in tests/manual/
3. **Inspect fixtures** - Query test_database.db and sync_test.db to verify available data (accounts, categories, etc.) before writing tests
4. **Test (Auto)** - Write unit and integration tests (failing) using verified fixture data
5. **Build** - Implement feature to pass tests
6. **Validate (Auto)** - Run pytest, achieve 100% pass
7. **Validate (Manual)** - Execute manual procedure, get user feedback
8. **Review Docs** - Update relevant documentation based on implementation and validation results
9. **Refactor** - Clean up based on results
10. **Commit** - Mark feature complete, move to next

#### Feature 5.1: Expense CRUD

**Document**
- Update user-guide.md: "Working with Expenses" section
- Add API examples for expense operations
- Add CLI examples for expense commands

**Test (Manual)**
```markdown
# tests/manual/feature_5.1_expense_crud.md

## Manual Test: Expense CRUD with Sync Validation

### Prerequisites
- [ ] HomeBudget Windows app installed
- [ ] Test database at tests/fixtures/sync_test.db
- [ ] Mobile device with HomeBudget app
- [ ] Wifi enabled for sync

### Test Procedure

1. **USER ACTION**: Note current expense count in HB Windows app

2. **AUTOMATED**: Add expense via wrapper
   ```bash
   homebudget --db tests/fixtures/sync_test.db expense add \
     --date 2026-02-16 --category Dining --subcategory Restaurant \
     --amount 25.50 --account Wallet --notes "TDD Test Expense"
   ```

3. **AUTOMATED**: Verify SyncUpdate entry created
   ```python
   # Script checks SyncUpdate table has new entry
   ```

4. **USER ACTION**: Check expense appears in HB Windows app
   - [ ] Expense visible with correct details
   - [ ] Amount matches

5. **USER ACTION**: Wait 30 seconds for sync, check mobile app
   - [ ] Expense synced to mobile device
   - [ ] No duplicates created
   
6. **RESULT**: PASS / FAIL with notes
```

**Test (Auto)**
```python
# tests/integration/test_expense_crud.py

def test_add_expense_basic(test_db_path):
    """Add expense with required fields only."""
    
def test_add_expense_creates_accounttrans(test_db_path):
    """Adding expense creates AccountTrans entry."""
    
def test_add_expense_creates_syncupdate(sync_test_db_path):
    """Adding expense creates SyncUpdate with valid payload."""
    
def test_add_duplicate_expense_raises_error(test_db_path):
    """Adding duplicate expense raises DuplicateError."""
    
def test_get_expense_by_key(test_db_path):
    """Get expense by key returns correct DTO."""
    
def test_list_expenses_with_filters(test_db_path):
    """List expenses with date range filter."""
    
def test_update_expense_amount(test_db_path):
    """Update expense amount and verify change."""
    
def test_delete_expense_removes_accounttrans(test_db_path):
    """Deleting expense removes AccountTrans entry."""
```

**Build**
- Implement `HomeBudgetClient.add_expense()`
- Implement `Repository.insert_expense()`
- Implement `SyncUpdateManager.create_expense_update()`
- Implement remaining CRUD methods

**Validate (Auto)**
```bash
pytest tests/integration/test_expense_crud.py -v
pytest tests/integration/test_sync_integration.py -k expense -v
```

**Validate (Manual)**
- Execute tests/manual/feature_5.1_expense_crud.md
- Record results
- User confirms sync worked

**Structured prompt for Feature 5.1**
```
Implement Expense CRUD with TDD using main env/:

1. Document:
   - Update docs/user-guide.md with Expense section
   - Add expense examples to docs/api-examples.md
   - Add expense CLI examples to docs/cli-examples.md

2. Manual test:
   - Create tests/manual/feature_5.1_expense_crud.md
   - Include user action prompts and automated steps
   - Design for Issue 001 sync validation

3. Automated tests (write first):
   - tests/integration/test_expense_crud.py (8 test cases)
   - tests/integration/test_sync_integration.py (expense subset)
   - Run tests (should fail - not implemented yet)

4. Build (implement to pass tests):
   - src/python/homebudget/client.py - add_expense() and CRUD methods
   - src/python/homebudget/repository.py - expense operations
   - src/python/homebudget/sync.py - SyncUpdateManager class
   - Follow design: docs/design.md and docs/sync-update.md

5. Validate automated:
   - pytest tests/integration/test_expense_crud.py
   - All tests must pass

6. Validate manual:
   - Execute tests/manual/feature_5.1_expense_crud.md
   - Prompt user to confirm sync results
   - Document PASS/FAIL

7. Review docs:
   - Check docs/user-guide.md reflects actual implementation behavior
   - Update docs/api-examples.md with any new patterns discovered
   - Update docs/cli-examples.md with working command syntax
   - Revise docs/methods.md with accurate signatures and return types

8. Refactor and commit

Reference: docs/design.md and docs/methods.md
```

#### Feature 5.2: Income CRUD

Follow same TDD workflow as 5.1:
1. Document (user-guide.md income section)
2. Manual test (tests/manual/feature_5.2_income_crud.md)
3. Auto tests (tests/integration/test_income_crud.py)
4. Build (client.py, repository.py income methods)
5. Validate auto + manual
6. Review docs (user-guide.md, api-examples.md, cli-examples.md, methods.md)

#### Feature 5.3: Transfer CRUD

Follow same TDD workflow as 5.1:
1. Document (user-guide.md transfer section)
2. Manual test (tests/manual/feature_5.3_transfer_crud.md)
3. Auto tests (tests/integration/test_transfer_crud.py)
4. Build (client.py, repository.py transfer methods with dual AccountTrans)
5. Validate auto + manual
6. Review docs (user-guide.md, api-examples.md, cli-examples.md, methods.md)

#### Feature 5.4: Reference Data

1. Document - Reference data queries in user-guide.md
2. Auto tests - tests/integration/test_reference_data.py
3. Build - Repository queries for accounts, categories, currencies
4. Validate - pytest tests/integration/test_reference_data.py
5. Review docs - Ensure query patterns and return types match implementation

#### Feature 5.5: CLI Commands

1. Document - cli-examples.md complete coverage
2. Auto tests - tests/integration/test_cli.py
3. Build - src/python/homebudget/cli/ structure
4. Validate - Click test runner + manual CLI execution
5. Review docs - Verify all CLI examples work as documented

#### Feature 5.6: Batch Operations

1. Document - Batch import workflow in user-guide.md
2. Manual test - Large CSV import with error handling
3. Auto tests - tests/integration/test_batch_operations.py
4. Build - Batch add commands with CSV and JSON parsing
5. Validate - Import 100 row test file
6. Review docs - Check batch examples, error handling documentation, csv/json format specs

Batch implementation notes
- Batch accepts resource and operation values and a list of records
- Batch runs shared input validation per record
- Batch delegates to lower level add methods with sync disabled
- Batch performs sync once after the batch completes

**Feature summary table**

| Feature | Tests | Implementation | Doc Review | Key Files |
| --- | --- | --- | --- | --- |
| 5.1 Expense CRUD | test_expense_crud.py + manual | client.py, repository.py, sync.py | user-guide, api-examples, cli-examples, methods | Issue 001 resolution |
| 5.2 Income CRUD | test_income_crud.py + manual | client.py, repository.py | user-guide, api-examples, cli-examples, methods | Sync support |
| 5.3 Transfer CRUD | test_transfer_crud.py + manual | client.py, repository.py | user-guide, api-examples, cli-examples, methods | Dual AccountTrans |
| 5.4 Reference Data | test_reference_data.py | repository.py | user-guide, api-examples, methods | Read-only queries |
| 5.5 CLI Commands | test_cli.py | cli/main.py, cli/commands/ | cli-examples, user-guide | Click framework |
| 5.6 Batch Operations | test_batch_operations.py | cli/commands/batch.py | user-guide, api-examples, cli-examples | CSV/JSON import |

### Phase 6: Integration and validation

**Goal**
End-to-end validation with full workflow testing.

**Process**
1. Run complete test suite
2. Check coverage (target 85%)
3. Execute all manual test procedures
4. Perform workflow validation from workflow.md
5. Pre-release checklist from step 8

**Expected outputs**
- Coverage report ≥ 85%
- All manual tests PASS
- Workflow validation complete
- Release candidate ready

**Structured prompt**
```
Using main env/, perform final integration validation:

1. Run full test suite:
   - pytest tests/ --cov=homebudget --cov-report=html --cov-report=term
   - Target: 85% line coverage minimum
   - Fix any failures

2. Execute all manual tests:
   - tests/manual/feature_5.1_expense_crud.md
   - tests/manual/feature_5.2_income_crud.md
   - tests/manual/feature_5.3_transfer_crud.md
   - Record results for each
   - User must confirm sync validation

3. Workflow validation from docs/workflow.md:
   - Account update workflow with batch import
   - Review workflow with list commands
   - Verify sync to mobile device

4. Pre-release checklist from docs/design.md:
   - All checklist items must pass
   - Document any failures or limitations

5. Generate release candidate:
   - Update VERSION to 1.0.0-rc1
   - Build package: python -m build src/python
   - Test install: pip install dist/homebudget-1.0.0rc1-py3-none-any.whl
   - Verify CLI: homebudget --version

6. Documentation check:
   - README.md updated with current features and installation
   - user-guide.md complete and matches implementation
   - api-examples.md validated with actual code execution
   - cli-examples.md validated with actual command execution
   - methods.md signatures match implementation
   - developer-guide.md reflects current workflow
   - All cross-references between docs are valid
```

**Validation criteria**
- [ ] Automated test coverage ≥ 85%
- [ ] All manual sync tests PASS
- [ ] Workflow validation complete
- [ ] Pre-release checklist 100% pass
- [ ] Package builds and installs
- [ ] CLI commands functional
- [ ] Documentation complete and accurate

## Implementation tracking

Create `docs/develop/IMPLEMENTATION_LOG.md` to track progress:

```markdown
# Implementation Log

## Phase 0: Prerequisites ✅ / ⏳ / ❌
- [ ] Setup scripts created
- [ ] Main env/ created
- [ ] Build tools installed
- [ ] Environment verified

## Phase 1: User Guide ✅ / ⏳ / ❌
- [ ] user-guide.md
- [ ] api-examples.md
- [ ] cli-examples.md

## Phase 2: Test Strategy ✅ / ⏳ / ❌
- [ ] TEST_STRATEGY.md
- [ ] conftest.py
- [ ] Test fixtures
- [ ] Manual test templates

## Phase 3: Foundation ✅ / ⏳ / ❌
- [ ] Models (tests + impl)
- [ ] Schema (tests + impl)
- [ ] Exceptions (tests + impl)
- [ ] Repository foundation (tests + impl)

## Phase 4: Packaging ✅ / ⏳ / ❌
- [ ] pyproject.toml
- [ ] Package structure
- [ ] Local install verified

## Phase 5: Features ✅ / ⏳ / ❌
- [ ] 5.1 Expense CRUD (doc + test + build + validate)
- [ ] 5.2 Income CRUD
- [ ] 5.3 Transfer CRUD
- [ ] 5.4 Reference Data
- [ ] 5.5 CLI Commands
- [ ] 5.6 Batch Operations

## Phase 6: Integration ✅ / ⏳ / ❌
- [ ] Full test suite passing
- [ ] Coverage ≥ 85%
- [ ] Manual tests complete
- [ ] Workflow validation
- [ ] Release candidate ready
```

## Test execution examples

**Automated tests**
```bash
# Run setup script if needed
.\.scripts\cmd\setup-env.cmd

# Activate main environment
.\env\Scripts\activate

# Run specific feature tests
pytest tests/integration/test_expense_crud.py -v

# Run all tests with coverage
pytest tests/ --cov=homebudget --cov-report=html

# Run only sync validation tests
pytest tests/integration/test_sync_integration.py -v

# Type checking
mypy src/python/homebudget

# Linting
ruff check src/python/homebudget

# Formatting
black src/python/homebudget tests/
```

**Manual tests**
```bash
# Run setup script if needed
.\.scripts\cmd\setup-env.cmd

# Activate main environment
.\env\Scripts\activate

# Install wrapper in development mode
pip install -e src/python

# Execute manual test procedure
# (Follow tests/manual/feature_5.1_expense_crud.md)

# Step 1: User notes current state in HB app
# Step 2: Run automated portion
homebudget --db tests/fixtures/sync_test.db expense add \
  --date 2026-02-16 --category Dining --subcategory Restaurant \
  --amount 25.50 --account Wallet --notes "TDD Test"

# Step 3: Automated verification script
python tests/manual/verify_syncupdate.py

# Step 4-5: User confirms in HB Windows and mobile apps
# Step 6: Record PASS/FAIL
```

## Decision points

**When to use automated vs manual testing:**

- **Automated:** All code paths, database operations, payload encoding, CLI commands
- **Manual:** Sync confirmation in HomeBudget UI (Windows and mobile), visual validation of transaction details

**Test data management:**
- Test fixtures are static (committed to git)
- Test runs copy fixtures to temp directories
- No modification of fixtures during tests
- Each test gets isolated database copy

**Coverage targets:**
- Automated: 85% line coverage minimum
- Manual: Critical user workflows (sync, CRUD operations visible in UI)
- Combined: 100% of user-facing features validated

## Verification

- All tests run in main `env/` environment
- Helper scripts (if any) run in `.dev/env`
- No creation of new virtual environments
- Package installable and CLI functional
- Manual sync validation confirms Issue 001 resolution
- Pre-release checklist from step 8 complete
