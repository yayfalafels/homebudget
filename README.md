# HomeBudget Python Wrapper

A Python library and CLI for managing HomeBudget transactions with full CRUD operations for expenses, income, and transfers.

see [HomeBudget Python Wrapper](https://yayfalafels.github.io/homebudget/) for complete documentation and usage guides.

## Release 2.1.1

for full release notes, see [211-negative-amounts.md](docs/releases/211/211-negative-amounts.md)

In this release

1. **Negative Amounts Support**: Updated validation rules to allow negative amounts for income and expenses, while still enforcing non-zero amounts. 

## Features

- **Full CRUD Operations**: Create, read, update, delete for expenses, income, and transfers
- **Mixed Currency Support**: Handle transactions across accounts with different currencies
- **Automatic Sync**: Changes propagate to HomeBudget mobile apps
- **Batch Operations**: Import multiple transactions from CSV/JSON
- **Forex Rates**: Automatic foreign exchange rate fetching and caching
- **UI Control**: Automatic HomeBudget app management during database operations

## Installation

```bash
# Create and activate virtual environment
python -m venv env
source env/Scripts/activate

# install dependencies
pip install -r requirements.txt

# Install package
pip install -e homebudget-*.whl
```

## Configuration

Create `%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json`:

```json
{
  "db_path": "C:\\Users\\<USERNAME>\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db",
  "sync_enabled": true,
  "base_currency": "SGD"
}
```

## Usage: Add an expense

**CLI:**
```bash
homebudget expense add --date 2026-02-20 --category "Food (Basic)" --subcategory "Cheap restaurant" --amount 25.50 --account "Wallet" --notes "Lunch with friends"
```

**Public interface:**
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
