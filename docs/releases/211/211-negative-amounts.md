# Release 2.1.1 - Negative Amounts Support

In this release

1. **Negative Amounts Support**: Updated validation rules to allow negative amounts for income and expenses, while still enforcing non-zero amounts. 

## 01 Negative amounts

Previous version 2.1.0 did not allow negative amounts for income and expenses, which does not accurately reflect the usage of HomeBudget.

Updated validation rules to allow negative amounts for income and expenses, while still enforcing non-zero amounts. 

### Locations affected

- **src/python/homebudget/models.py**: Updated `_ensure_decimal()` function to validate that amounts are non-zero (instead of positive), allowing negative values for expenses and incomes

