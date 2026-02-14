# Financial statements workflow

## Table of contents

- [Overview](#overview)
- [Sequential steps and time estimates](#sequential-steps-and-time-estimates)
- [Workflows](#workflows)
    - [Pre-flight checks](#pre-flight-checks)
    - [Forex](#forex)
    - [Account update](#account-update)
    - [Report update](#report-update)

## Overview

This document describes the financial statements workflow, beginning with the sequential steps with time estimates, then the account update flowchart, and finally the report generation flowchart.

## Sequential steps and time estimates

| id | workflow       | account    | duration min  | description                         |
| -- | -------------- | ---------- | ------------- | ----------------------------------- |
| 01 | forex          |            | 3 min         | fetch USD.SGD forex rates           |
| 02 | account update | wallets    | 20 to 40 min  | direct read from HB app             |
| 03 | account update | IBKR       | 50 to 110 min | brokerage with helper workbook      |
| 04 | account update | CPF        | 20 to 80 min  | Singapore retirement CPF            |
| 07 | report update  | reconcile  | 30 to 140 min | review and close reconcile gaps     |
| 08 | report update  | statements | 45 to 90 min  | review and update statements        |
| 09 | report update  | print-out  | 20 min        | print-out statements to PDF report  |
| 10 | refresh        |            |5 min          | refresh the workspace logging sheet |

## Workflows

- [Pre-flight checks](#pre-flight-checks)
- [Forex](#forex)
- [Account update](#account-update)
- [Report update](#report-update)

### Pre-flight checks

### Forex

download USD.SGD forex rates from yahoo finance
load monthly month-end rates since last update into sheet `forex_rates`

USD.SGD forex rates url: [USD.SGD](https://sg.finance.yahoo.com/quote/SGD%3DX/)

### Account update

The account update flow starts from statement download and moves through worksheets and balances, with reviews at several points.

- authenticate to website either password or MFA
- statement download from website
- statement backup to S3
- use worksheet as intermediate calculator to determine balances and transactions
- human review of balances and transactions for errors
- update HomeBudget with transactions - income, expenses, transfers
- update balances sheet in financial statements workbook

### Report update

The final report generation flow starts after reconcile and splits into income statement and balance sheet, then merges into the financial statements file and produces a PDF print-out stored in Drive.

- Reconcile review
- Update and review income statement and balance sheet
- safe reports as PDF
- upload to S3

### Workspace close-out and refresh
