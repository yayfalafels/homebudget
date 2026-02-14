# Step 3 SQLite schema and data model mapping

## Table of contents

- [Scope and sources](#scope-and-sources)
- [Schema map core tables](#schema-map-core-tables)
- [Schema map supporting tables](#schema-map-supporting-tables)
- [Inferred relationships](#inferred-relationships)
- [Domain model mapping](#domain-model-mapping)
- [UI to schema mapping notes](#ui-to-schema-mapping-notes)
- [Data type notes](#data-type-notes)

## Scope and sources

This step maps the SQLite schema to the wrapper domain model. Core scope is expenses, income, transfers, recurring entries, and currency handling. Statements ingestion is out of scope.

Sources
- [docs/sqlite-schema.md](docs/sqlite-schema.md#L1)
- [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L1262)
- [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L43)

## Schema map core tables

| Table | Primary key | Required fields | Notes | Source |
| --- | --- | --- | --- | --- |
| Expense | key | date, catKey, subCatKey, amount, payFrom, currency, currencyAmount, timeStamp | Includes splits, receipts, and recurring references | [docs/sqlite-schema.md](docs/sqlite-schema.md#L186) |
| Income | key | date, name, amount, addIncomeTo, currency, currencyAmount, timeStamp | Name acts as income description | [docs/sqlite-schema.md](docs/sqlite-schema.md#L300) |
| Transfer | key | transferDate, fromAccount, toAccount, amount, currency, currencyAmount | Tracks account to account movement | [docs/sqlite-schema.md](docs/sqlite-schema.md#L613) |
| AccountTrans | key | accountKey, timeStamp, transType, transKey, transDate, transAmount | Ledger link for Expense, Income, Transfer | [docs/sqlite-schema.md](docs/sqlite-schema.md#L45) |
| Account | key | name, accountType, balance, balanceDate, currency | Account base currency is stored here | [docs/sqlite-schema.md](docs/sqlite-schema.md#L15) |
| Category | key | name | Expense category | [docs/sqlite-schema.md](docs/sqlite-schema.md#L148) |
| SubCategory | key | catKey, name | Expense subcategory | [docs/sqlite-schema.md](docs/sqlite-schema.md#L514) |
| Currency | key | name, code, exchangeRate | Exchange rate stored as text | [docs/sqlite-schema.md](docs/sqlite-schema.md#L161) |
| RecurringExpense | key | catKey, subCatKey, amount, nextGenDate, modulus | Recurring expense settings | [docs/sqlite-schema.md](docs/sqlite-schema.md#L355) |
| RecurringIncome | key | name, amount, startDate, nextGenDate, modulus | Recurring income settings | [docs/sqlite-schema.md](docs/sqlite-schema.md#L387) |
| RecurringTransfer | key | name, fromAccount, toAccount, amount, nextGenDate, modulus | Recurring transfer settings | [docs/sqlite-schema.md](docs/sqlite-schema.md#L417) |

## Schema map supporting tables

These tables are relevant to sync detection and system settings, but are not part of the CRUD surface in the first pass.

| Table | Purpose | Notes | Source |
| --- | --- | --- | --- |
| SyncInfo | Sync group and last sync metadata | Used for sync state detection | [docs/sqlite-schema.md](docs/sqlite-schema.md#L564) |
| SyncUpdate | Sync update payloads | Used for update tracking | [docs/sqlite-schema.md](docs/sqlite-schema.md#L579) |
| DeviceInfo | Device identity and primary flags | Sync context | [docs/sqlite-schema.md](docs/sqlite-schema.md#L173) |
| Settings | Global app settings | Includes home currency | [docs/sqlite-schema.md](docs/sqlite-schema.md#L450) |

## Inferred relationships

SQLite does not enforce foreign key constraints in this database, so the wrapper must treat these as logical links only.

- Expense.catKey to Category.key
- Expense.subCatKey to SubCategory.key
- Expense.payFrom to Account.key
- Expense.payeeKey to Payee.key
- Expense.recurringKey to RecurringExpense.key
- Income.addIncomeTo to Account.key
- Income.recurringKey to RecurringIncome.key
- Transfer.fromAccount to Account.key
- Transfer.toAccount to Account.key
- Transfer.recurringKey to RecurringTransfer.key
- AccountTrans.transKey to Expense.key, Income.key, or Transfer.key based on transType

## Domain model mapping

| Domain model | Primary table | Related tables | Fields and mapping notes |
| --- | --- | --- | --- |
| Expense | Expense | Account, Category, SubCategory, AccountTrans, Currency, Payee | Uses catKey and subCatKey to map to category and subcategory names. payFrom maps to account. currency and currencyAmount capture foreign currency. AccountTrans uses transType expense and transKey to link. |
| Income | Income | Account, AccountTrans, Currency | name is the income description. addIncomeTo maps to account. AccountTrans uses transType income and transKey to link. |
| Transfer | Transfer | Account, AccountTrans, Currency | fromAccount and toAccount map to account keys. AccountTrans uses transType transfer in and transfer out to link. |
| RecurringExpense | RecurringExpense | Category, SubCategory, Account, Currency | nextGenDate and modulus model recurrence. generateNow indicates immediate generation. |
| RecurringIncome | RecurringIncome | Account, Currency | nextGenDate and modulus model recurrence. generateNow indicates immediate generation. |
| RecurringTransfer | RecurringTransfer | Account, Currency | nextGenDate and modulus model recurrence. generateNow indicates immediate generation. |
| Currency | Currency | Settings | code is the currency code. exchangeRate is text and should be parsed. |
| Account | Account | Currency | currency is the base currency for the account. |

## UI to schema mapping notes

- Expense entry fields from the guide map to Expense.date, Expense.catKey, Expense.subCatKey, Expense.amount, Expense.currency, Expense.currencyAmount, Expense.payFrom, Expense.payeeKey, and Expense.notes. Source [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L51)
- Income entry fields map to Income.date, Income.name, Income.amount, Income.notes, and Income.addIncomeTo. Source [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L68)
- Transfers map to Transfer.transferDate, Transfer.fromAccount, Transfer.toAccount, Transfer.amount, and Transfer.notes. Source [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L80)
- Recurring settings map to RecurringExpense, RecurringIncome, and RecurringTransfer tables with nextGenDate, endDate, and generateNow fields. Source [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L61)
- Account base currency maps to Account.currency and is required when associating transactions. Source [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L43)

## Data type notes

- currencyAmount fields are stored as TEXT across Expense, Income, and Transfer. The wrapper should parse these to decimal for validation and store as string for persistence.
- exchangeRate is stored as TEXT in Currency and should be parsed to decimal for calculations.
- date and timeStamp fields are stored as DATE and DATETIME but must be handled as local time based on the guide.
