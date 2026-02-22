# HomeBudget Python Wrapper

A Python library and CLI for managing HomeBudget transactions with full CRUD operations for expenses, income, and transfers.

## Quick Links

- **[About](docs/index.md)** - Project overview and goals
- **[User Guide](docs/user-guide.md)** - Getting started and usage
- **[Developer Guide](docs/developer-guide.md)** - Development and testing
- **[Configuration](docs/configuration.md)** - Setup and configuration
- **[API Examples](docs/api-examples.md)** - Python API examples
- **[CLI Examples](docs/cli-examples.md)** - Command-line examples

## Features

- **Full CRUD Operations**: Create, read, update, delete for expenses, income, and transfers
- **Mixed Currency Support**: Handle transactions across accounts with different currencies
- **Automatic Sync**: Changes propagate to HomeBudget mobile apps
- **Batch Operations**: Import multiple transactions from CSV/JSON
- **Forex Rates**: Automatic foreign exchange rate fetching and caching
- **UI Control**: Automatic HomeBudget app management during database operations

## Quick Start

### Installation

```bash
# Setup environment
.\scripts\cmd\setup-env.cmd
.\env\Scripts\activate

# Install package
pip install -e src/python
```

### Configuration

Create `%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json`:

```json
{
  "db_path": "C:\\Users\\USERNAME\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db",
  "sync_enabled": true,
  "base_currency": "SGD"
}
```

See [Configuration Guide](docs/configuration.md) for details.

### Usage

**CLI:**
```bash
homebudget expense add --date 2026-02-20 --category "Food" --amount 25.50 --account "Wallet"
```

**API:**
```python
from homebudget import HomeBudgetClient, ExpenseDTO
from decimal import Decimal
import datetime

with HomeBudgetClient() as client:
    expense = ExpenseDTO(
        date=datetime.date(2026, 2, 20),
        category="Food",
        subcategory="Restaurant",
        amount=Decimal("25.50"),
        account="Wallet"
    )
    saved = client.add_expense(expense)
    print(f"Added expense {saved.key}")
```

## Documentation

Complete documentation is available in the `docs/` directory:

- [About](docs/index.md) - Project background and aims
- [User Guide](docs/user-guide.md) - Complete user documentation
- [Developer Guide](docs/developer-guide.md) - Development workflow
- [Configuration](docs/configuration.md) - Configuration reference
- [Design](docs/design.md) - Architecture and design decisions
- [Test Guide](docs/test-guide.md) - Testing strategy and procedures
- [API Examples](docs/api-examples.md) - Python API usage examples
- [CLI Examples](docs/cli-examples.md) - Command-line usage examples

## License

See [LICENSE](LICENSE) file for details.

