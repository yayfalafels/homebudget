# Transfer Currency Normalization Layer

## Table of contents

- [Overview](#overview)
- [Backend storage format](#backend-storage-format)
- [User input modes](#user-input-modes)
- [Design rationale](#design-rationale)
- [Implementation architecture](#implementation-architecture)
- [Normalization calculations](#normalization-calculations)
- [Example transformation](#example-transformation)
- [Error handling](#error-handling)
- [Testing](#testing)
- [Related documentation](#related-documentation)

## Overview

The transfer currency normalization layer lets users specify currency for **either** the from_account **or** the to_account when creating transfers. It normalizes inputs to the backend standard format before validation and persistence.

## Backend Storage Format

The Transfer table stores currency information in this format:

| Field | Description |
|-------|-------------|
| `currency` | **Always** equals from_account currency |
| `currency_amount` | Amount in from_account currency |
| `amount` | Amount in to_account currency |

The backend enforces `currency = from_account` to keep conversion semantics unambiguous.

## User Input Modes

Users can specify transfer amounts in three ways:

### 1. Amount Only, Inference

Specify only the `amount` field. The system infers currency based on account types:

```json
{
  "from_account": "TWH - Personal",  // SGD, base currency
  "to_account": "TWH IB USD",  // USD
  "amount": "200.00"  // Inferred as SGD, base currency present
}
```

**Inference rules:**

- If base currency in either account -> user amount is in base currency
- If base in neither account -> user amount is in from_account currency

### 2. From-Currency Explicit, Pass Through

Specify `currency` + `currency_amount` matching the **from_account**:

```json
{
  "from_account": "TWH IB USD",  // USD
  "to_account": "TWH - Personal",  // SGD
  "currency": "USD",  // Matches from_account
  "currency_amount": "150.00"  // from_amount
}
```

**Behavior:** Already in backend format -> passes through unchanged.

### 3. To-Currency Explicit, Normalized

Specify `currency` + `currency_amount` matching the **to_account**:

```json
{
  "from_account": "TWH - Personal",  // SGD, base currency
  "to_account": "TWH IB USD",  // USD
  "currency": "USD",  // Matches to_account
  "currency_amount": "100.00"  // to_amount
}
```

**Behavior:** Normalized to backend format:

1. Interpret `currency_amount` as `to_amount`, 100.00 USD
2. Calculate `from_amount` using the inverse rate, `from_amount = to_amount / forex_rate`
3. Convert to standard form:
    - `currency` = "SGD", from_account
    - `currency_amount` = calculated from_amount
    - `amount` = 100.00, to_amount

## Design Rationale

### Why Normalize to from_account?

The backend constraint `currency = from_account` provides:

1. **Unambiguous semantics:** Always clear which account's currency is the reference
2. **Consistent querying:** Filtering by currency always uses from_account perspective
3. **Simplified validation:** Single constraint rule instead of multiple cases

### Why Accept Both Specifications?

User convenience:

- **From-account specification:** Natural when user thinks "I'm sending X USD"
- **To-account specification:** Natural when user thinks "Recipient gets Y EUR"
- **Either works:** System handles both transparently

The normalization layer provides user flexibility while maintaining backend consistency.

## Implementation Architecture

### Layer 1: User Input, Flexible

**Location:** JSON parsing in CLI, `cli/transfer.py`

**Accepts:**

- `amount` only, optional
- `currency` + `currency_amount`, optional and can match either account

### Layer 2: Normalization, Conversion

**Location:** `client.py`, `_infer_currency_for_transfer()`

**Logic:**

1. If `currency` + `currency_amount` specified:
    - Validate: `currency` must match **either** from_account or to_account
    - If matches from_account, pass through
    - If matches to_account, calculate inverse and swap to backend format

2. If only `amount` specified:
    - Apply inference rules, base currency priority

3. Return normalized TransferDTO

### Layer 3: Validation, Constraint Enforcement

**Location:** `client.py`, `_validate_transfer_currency_constraint()`

**Enforces:** `currency` **must** equal from_account currency, backend constraint

This validation runs **after** normalization, so it always sees backend-formatted data.

Persistence stores backend-formatted data via repository `insert_transfer`.

## Normalization Calculations

### Same Currency Accounts

```
from_amount = to_amount
```

### Foreign to Base Currency

```
to_amount_base = from_amount_foreign * forex_rate
```

Inverse, when normalizing to_amount to from_amount:
```
from_amount_foreign = to_amount_base / forex_rate
```

### Base to Foreign Currency

```
to_amount_foreign = from_amount_base / forex_rate
```

Inverse, when normalizing to_amount to from_amount:
```
from_amount_base = to_amount_foreign * forex_rate
```

### Foreign to Foreign Currency

```
to_amount = from_amount * from_rate / to_rate
```

Inverse, when normalizing to_amount to from_amount:
```
from_amount = to_amount * to_rate / from_rate
```

## Example Transformation

**User Input, to_account currency:**
```json
{
  "date": "2026-02-22",
  "from_account": "TWH - Personal",  // SGD, base currency, rate = 1.0
  "to_account": "TWH IB USD",  // USD, rate = 0.74
  "currency": "USD",
  "currency_amount": "100.00",
  "notes": "Normalized transfer"
}
```

**Normalization Steps:**

1. **Identify:** `currency` = USD matches `to_account`, not from_account
2. **Interpret:** `currency_amount` 100.00 is the to_amount in USD
3. **Calculate from_amount:**
  - Conversion: foreign USD to base SGD
  - Formula: `from_amount = to_amount / forex_rate`
  - Calculation: `100.00 / 0.74 = 135.14` SGD

4. **Normalize to backend format:**
   ```json
   {
     "currency": "SGD",          // from_account, backend constraint
     "currency_amount": "135.14", // from_amount, calculated
     "amount": "100.00"           // to_amount, preserved
   }
   ```


## Error Handling

### Over-Specification Error

Cannot specify **both** `amount` and `currency_amount`:

```json
{
  "amount": "100.00",
  "currency": "USD",
  "currency_amount": "74.00"  // ERROR: over-specified
}
```

**Error message:**
```
Cannot specify both 'amount' and 'currency_amount'. 
Provide either 'amount' alone for inference or 'currency' with 'currency_amount'.
```

### Invalid Currency Error

Currency must match **one of** the transfer accounts:

```json
{
  "from_account": "TWH - Personal",  // SGD
  "to_account": "TWH IB USD",  // USD
  "currency": "EUR",  // ERROR: matches neither
  "currency_amount": "50.00"
}
```

**Error message:**
```
Transfer currency must match either from_account or to_account currency. 
from_account uses SGD, to_account uses USD, but transfer specifies EUR.
```

## Testing

### Integration Test Coverage

The normalization layer is tested in:

- `tests/integration/test_currency_constraints.py::test_transfer_currency_must_match_from_account`

This test verifies:

1. ✅ To-currency specification is normalized correctly
2. ✅ From-currency specification passes through unchanged
3. ✅ Invalid currencies, matching neither account, are rejected

### UAT Test Cases

Comprehensive batch transfer tests in:

- [transfers_valid_batch.json](https://github.com/yayfalafels/homebudget/blob/main/tests/manual/batch_templates/transfers_valid_batch.json)

Test coverage:

- **Items 1-4:** Amount-only inference, 4 cases
- **Items 5-7:** Explicit from-currency, 3 cases
- **Items 8-10:** Explicit to-currency with normalization, 3 cases
- **Item 11:** Invalid date format, parsing error test

See [Test cases](tests/BATCH_TRANSFER_TEST_CASES.md) for detailed test case documentation.


## Related Documentation

- **[Design](design.md)**, transfer currency semantics
- **[Schema](sqlite-schema.md)**, transfer table structure
- **[Test Strategy](test-strategy.md)**, inference testing approach
- **[Test Cases](tests/BATCH_TRANSFER_TEST_CASES.md)**, UAT coverage
