# Issue 003: Sync Fail Expense Update Amount

## Problem description

Sync fails for the operation Expense update for field amount but not for other fields, such as description.

The payload is generated, and cleared, but results do not update in other mobile device

The problem only applies to Expense update amount, and not to Income update amount, or Expense update description.

## Diagnostics

| id | status | result  | task |
| -- | --     | --      | --   |
| 01 | closed | --      | generate test payloads from ui |
| 02 | closed | see below | inspect test payloads and compare to program generated payloads |

_01 (closed) generate test payloads from ui_

4x operations generated

1. income add
2. income update amount
3. expense add
4. expense update amount

_02 (closed) inspect test payloads and compare to program generated payloads_

create additional test sync payloads programmatically and compare to the ui generated payloads

## Findings

- SyncUpdate has 4 rows for the target operations, add income, update income, add expense, update expense.
- UpdateExpense payload uses `amount` as a float and `currencyAmount` as a string with two decimals.
- UpdateIncome payload uses `amount` as a string and `currencyAmount` as a string. It syncs to mobile as expected.
- Expense update description syncs, so the payload is accepted, but the amount change does not propagate.

## Hypothesis to test

UpdateExpense sync is sensitive to currency metadata. When amount updates are sent without aligning `currencyAmount`, the sync service accepts the update but does not apply the amount change on mobile.

## Proposed test

1. Generate a programmatic update that sets amount only.
2. Verify the payload sets `currencyAmount` equal to amount.
3. Confirm the amount change appears on mobile.

## Resolution

Update operations now default the base currency path by setting `currencyAmount` to match amount when amount is provided without a foreign currency. CLI update commands no longer inject `currencyAmount` for amount only updates, and the repository update logic aligns `currencyAmount` with the amount change.

## Validation

- Expense amount update syncs to mobile after the currencyAmount alignment change.
