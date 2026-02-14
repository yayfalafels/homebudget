# Step 2 Source inventory and gap log

## Table of contents

- [Scope and sources](#scope-and-sources)
- [Inventory summary](#inventory-summary)
- [Entity and table hints](#entity-and-table-hints)
- [Gap log](#gap-log)
- [UI alignment notes](#ui-alignment-notes)

## Scope and sources

This inventory focuses on the reference wrapper, its data sources, and workflow documents. The guide reference is used for UI alignment notes. Statements ingestion is out of scope for the wrapper design.

Sources
- [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L497)
- [reference/hb-finances/database.py](reference/hb-finances/database.py#L21)
- [reference/hb-finances/statements.py](reference/hb-finances/statements.py#L58)
- [docs/workflow.md](docs/workflow.md#L21)
- [docs/issues.md](docs/issues.md#L5)
- [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L43)

## Inventory summary

| Component | Type | Purpose | Notes | Source |
| --- | --- | --- | --- | --- |
| HomeBudgetAgent | Class | Main wrapper interface for SQLite | Handles load, query tables, expense add and delete | [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L497) |
| expenses_add | Method | Insert expense transactions | Writes to Expense and AccountTrans tables | [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L640) |
| expenses_delete | Method | Remove expense transactions | Deletes Expense and AccountTrans rows | [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L704) |
| general_ledger | Method | Create a unified ledger view | Merges AccountTrans with Expense, Income, Transfer | [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L1262) |
| expense_categories | Method | List categories and subcategories | Join Category and SubCategory | [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L1383) |
| transactions_update | Function | Batch update handler | Only expense transactions are processed | [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L369) |
| database module | Module | SQLite and Google Sheets helpers | Includes SQLite connection and gsheet read and write | [reference/hb-finances/database.py](reference/hb-finances/database.py#L21) |
| get_sheet | Function | Read gsheet range into DataFrame | Used by UI and statement flows | [reference/hb-finances/database.py](reference/hb-finances/database.py#L100) |
| post_to_gsheet | Function | Write DataFrame to gsheet | Used for UI and statement updates | [reference/hb-finances/database.py](reference/hb-finances/database.py#L144) |
| CSVDirectory | Class | File system helper for csv and xls | Used in statement workflows | [reference/hb-finances/database.py](reference/hb-finances/database.py#L185) |
| statements module | Module | Statement import and balances | Produces GL and balances tables | [reference/hb-finances/statements.py](reference/hb-finances/statements.py#L189) |
| statement_cleanup | Function | Parse bank statement files | Bank specific parsing logic | [reference/hb-finances/statements.py](reference/hb-finances/statements.py#L218) |
| tsv_cleanup | Function | Parse manual tsv statements | Bank specific parsing logic | [reference/hb-finances/statements.py](reference/hb-finances/statements.py#L246) |
| workflow forex | Doc section | Forex data updates | Uses USD.SGD monthly rates | [docs/workflow.md](docs/workflow.md#L41) |
| workflow account update | Doc section | Data entry flow | Updates HomeBudget with income, expenses, transfers | [docs/workflow.md](docs/workflow.md#L55) |
| issue sync detection | Issue | Open bug | Sync detection risk remains | [docs/issues.md](docs/issues.md#L5) |

## Entity and table hints

The reference wrapper code suggests these domain tables or entities are part of the SQLite model. They appear in query joins and ledger assembly.

- AccountTrans, Account, Expense, Income, Transfer appear in the general ledger assembly and are central to transaction flow. Source [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L1262)
- Category and SubCategory are joined for expense category reporting. Source [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L1383)
- Expense transactions include links to Category, SubCategory, Account, Currency, Payee via foreign key lookup. Source [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L994)

## Gap log

| Gap | Severity | Design impact | Evidence |
| --- | --- | --- | --- |
| Income and transfer transactions are not processed by the batch update path | High | New wrapper must support full CRUD for income and transfers in the core pipeline | [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L369) |
| Expense idempotency relies on a composite match of date, account, amount, currency, subcategory, and notes | Medium | Keep existing composite match for now, revisit after schema mapping | [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L1072) |
| Foreign key constraints are not enforced by the schema in the reference database | Low | Do not enforce in the wrapper for now, document the risk | [reference/hb-finances/homebudget.py](reference/hb-finances/homebudget.py#L760) |
| Reference wrapper writes through Google Sheets UI and a queued transaction model | High | Remove Google Sheets dependency and design a direct SQLite API | [reference/hb-finances/database.py](reference/hb-finances/database.py#L100) |
| Workflow calls for forex rate updates and multi currency handling | Medium | Include USD focused forex handling first, expand later | [docs/workflow.md](docs/workflow.md#L41) and [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L43) |
| Sync detection bug remains open | High | Sync and duplicate detection strategy must be explicit | [docs/issues.md](docs/issues.md#L5) |

## UI alignment notes

The guide reference defines user facing terms and behaviors relevant to the wrapper design.

- Expenses, income, transfers, and recurring entries are primary UI concepts and should map to public API names where possible. Source [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L23)
- Transactions can use foreign currency with exchange rate conversion, and account currency must match when linked to accounts. Source [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L43)
- Transfers are used for credit card payments when the expense already exists, to avoid double counting. Source [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L83)
- Recurring entries are configured as settings that generate future dated entries. Source [reference/HomeBudget_Windows_guide.md](reference/HomeBudget_Windows_guide.md#L63)
