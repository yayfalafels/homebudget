# Currency Matching Rules

This document details the constraints on adding and updating transactions with foreign currencies.

## Overview

HomeBudget supports multi-currency accounts with explicit exchange rate handling. The system enforces currency matching rules to maintain data consistency and prevent invalid transactions.

**System base currency**: SGD (configured in Settings.currency)

## Rules by Transaction Type

### Expenses and Income

#### Rule 1: Cannot add base currency to non-base currency accounts

You cannot add a transaction in the system's base currency (SGD) to an account that has a non-base currency.

**Examples:**
- ✗ INVALID: Add SGD expense to "TWH IB USD" (USD account)
- ✗ INVALID: Add SGD income to any account where account.currency != SGD

#### Rule 2: Can add foreign currencies to base currency accounts

You can add a transaction in any foreign currency to an account whose currency is the system base.

**Examples:**
- ✓ VALID: Add USD expense to "TWH - Personal" (SGD account)
- ✓ VALID: Add EUR income to "DBS Multi" (SGD account)
- ✓ VALID: Add GEL expense to any base currency account

#### Requirements for foreign currency transactions

When adding a transaction in a foreign currency, you must provide:
1. `--currency`: The foreign currency code (USD, EUR, GEL, etc.)
2. `--currency-amount`: The amount in the foreign currency
3. `--exchange-rate`: The exchange rate to convert foreign currency to base currency

Formula: `amount = currency_amount × exchange_rate`

**Example - Add USD expense to SGD account:**
```bash
hb expense add \
  --date 2026-02-17 \
  --category Dining \
  --subcategory Restaurant \
  --currency USD \
  --currency-amount 27.50 \
  --exchange-rate 0.9273 \
  --account "TWH - Personal" \
  --notes "Lunch in USD"
```
Calculates: amount = 27.50 × 0.9273 = 25.50 SGD

### Transfers

#### Rule 3: Specify currency for only one account in mixed-currency transfers

When transferring between accounts with different currencies, you can specify the currency amount and exchange rate for **only one** of the two account currencies, not both.

#### Rule 4: Use only account currencies in transfers

When specifying a currency for a transfer, it must match either:
1. The source account's currency, OR
2. The destination account's currency

You cannot introduce a third currency (e.g., EUR) unless it matches one of the accounts.

**Examples:**
- ✓ VALID: Transfer from "TWH - Personal" (SGD) to "TWH IB USD" (USD) specifying USD:
  ```bash
  hb transfer add \
    --date 2026-02-17 \
    --from-account "TWH - Personal" \
    --to-account "TWH IB USD" \
    --currency USD \
    --currency-amount 110.00 \
    --exchange-rate 0.9091 \
    --notes "Transfer"
  ```
  Converts 110 USD at 0.9091 rate = 100 SGD from TWH - Personal to TWH IB USD

- ✓ VALID: Same transfer specifying SGD (source currency):
  ```bash
  hb transfer add \
    --date 2026-02-17 \
    --from-account "TWH - Personal" \
    --to-account "TWH IB USD" \
    --currency SGD \
    --currency-amount 100.00 \
    --exchange-rate 1.10 \
    --notes "Transfer"
  ```
  100 SGD at rate 1.10 = 110 USD to TWH IB USD

- ✗ INVALID: Transferring between SGD and USD accounts but specifying EUR currency
- ✗ INVALID: Specifying both USD and SGD currencies in a single transfer

## Implementation Status

### Documentation
- ✓ User guide updated with currency matching constraints
- ✓ CLI examples include proper currency usage
- ✓ Manual tests updated to comply with constraints

### Source Code Validation
- ⚠ Constraint documentation is complete
- ⏳ Runtime validation enforcement is a future enhancement

**Next steps for enforcement:**
1. Add `_validate_currency_compatibility()` method to HomeBudgetClient
2. Call validation in `add_expense()`, `add_income()`, `add_transfer()` before insertion
3. Call validation in update methods when currency is being modified
4. Raise `ValueError` with clear message when constraint is violated

Example validation invocation:
```python
def add_expense(self, expense: ExpenseDTO) -> ExpenseRecord:
    """Add an expense and return the created record."""
    if expense.currency:
        self._validate_currency_compatibility(
            account_name=expense.account,
            transaction_currency=expense.currency,
            transaction_type="expense"
        )
    # ... rest of method
```

## Testing

Manual tests verify proper currency handling:

- **uat_expense_currency_usd**: Add USD expense to SGD account (TWH - Personal)
- **uat_income_currency_usd**: Add USD income to SGD account (DBS Multi)
- **uat_transfer_currency_usd**: Transfer USD between mixed-currency accounts

All tests include verification that:
1. Transactions are created with correct currency and amount fields
2. SyncUpdate records are generated for sync to other devices
3. Currency and currencyAmount values are preserved in the record

Run tests with:
```bash
python tests/manual/manual_test_runner.py --test-id uat_expense_currency_usd
python tests/manual/manual_test_runner.py --test-id uat_income_currency_usd
python tests/manual/manual_test_runner.py --test-id uat_transfer_currency_usd
```

## References

- User guide: [docs/user-guide.md](user-guide.md#currency-matching-constraints)
- CLI examples: [docs/cli-examples.md](cli-examples.md)
- Manual tests: [tests/manual/manual_tests.json](../tests/manual/manual_tests.json)
- Database schema: [docs/sqlite-schema.md](sqlite-schema.md#account)
