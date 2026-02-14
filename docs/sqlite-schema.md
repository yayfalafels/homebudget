# SQLite schema reference
Database: reference/hb-sqlite-db/homebudget.db

## Table of contents
- [Account](#account)
- [AccountLog](#accountlog)
- [AccountTrans](#accounttrans)
- [Bill](#bill)
- [Budget](#budget)
- [BudgetFuture](#budgetfuture)
- [BudgetHistory](#budgethistory)
- [BudgetSettings](#budgetsettings)
- [Category](#category)
- [Currency](#currency)
- [DeviceInfo](#deviceinfo)
- [Expense](#expense)
- [FIHints](#fihints)
- [FITrans](#fitrans)
- [Income](#income)
- [Payee](#payee)
- [RecurringBill](#recurringbill)
- [RecurringExpense](#recurringexpense)
- [RecurringIncome](#recurringincome)
- [RecurringTransfer](#recurringtransfer)
- [Settings](#settings)
- [SubCategory](#subcategory)
- [SyncInfo](#syncinfo)
- [SyncUpdate](#syncupdate)
- [Transfer](#transfer)

## Account

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| name | TEXT | 0 |  | 0 |
| icon | TEXT | 0 |  | 0 |
| accountType | TEXT | 0 |  | 0 |
| balance | REAL | 0 | 0.00 | 0 |
| deleteOK | CHAR(1) | 0 | 'Y' | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| balanceDate | DATE | 0 |  | 0 |
| includeAccount | CHAR(1) | 0 | 'Y' | 0 |
| seqNum | INTEGER | 0 | 0 | 0 |
| currency | TEXT | 0 |  | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| AccountDeviceIdDeviceKeyIndex | 0 | deviceIdKey, deviceKey | c | 0 |

## AccountLog

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| accountKey | INTEGER | 0 |  | 0 |
| timeStamp | DATETIME | 0 |  | 0 |
| transType | INTEGER | 0 |  | 0 |
| transKey | INTEGER | 0 |  | 0 |
| transAmount | REAL | 0 |  | 0 |
| newBalance | REAL | 0 |  | 0 |
| checked | CHAR(1) | 0 | 'N' | 0 |
| transDate | DATE | 0 |  | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| AccountLogTimeStampIndex | 0 | timeStamp | c | 0 |
| AccountLogAccountKeyIndex | 0 | accountKey | c | 0 |

## AccountTrans

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| accountKey | INTEGER | 0 |  | 0 |
| timeStamp | DATETIME | 0 |  | 0 |
| transType | INTEGER | 0 |  | 0 |
| transKey | INTEGER | 0 |  | 0 |
| transDate | DATE | 0 |  | 0 |
| transAmount | REAL | 0 |  | 0 |
| checked | CHAR(1) | 0 | 'N' | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| AccountTransTransKeyIndex | 0 | transType, transKey | c | 0 |
| AccountTransTransDateIndex | 0 | transDate | c | 0 |

## Bill

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| payeeKey | INTEGER | 0 |  | 0 |
| amount | REAL | 0 |  | 0 |
| dueDate | DATE | 0 |  | 0 |
| paid | CHAR(1) | 0 | 'Y' | 0 |
| expenseKey | INTEGER | 0 |  | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| timeStamp | DATETIME | 0 |  | 0 |
| billType | INTEGER | 0 | 0 | 0 |
| currency | TEXT | 0 |  | 0 |
| currencyAmount | TEXT | 0 |  | 0 |
| recurringKey | INTEGER | 0 | 0 | 0 |
| catKey | INTEGER | 0 | 0 | 0 |
| subCatKey | INTEGER | 0 | 0 | 0 |
| fromAccountKey | INTEGER | 0 | 0 | 0 |
| notes | TEXT | 0 |  | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| BillDeviceIdDeviceKeyIndex | 0 | deviceIdKey, deviceKey | c | 0 |
| BillsDueDateIndex | 0 | dueDate | c | 0 |

## Budget

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| catKey | INTEGER | 0 |  | 0 |
| subCatKey | INTEGER | 0 |  | 0 |
| month | INTEGER | 0 |  | 0 |
| year | INTEGER | 0 |  | 0 |
| amount | TEXT | 0 |  | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| BudgetCatKeySubCatKeyMonthYearIndex | 0 | catKey, subCatKey, month, year | c | 0 |

## BudgetFuture

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| catKey | INTEGER | 0 |  | 0 |
| subCatKey | INTEGER | 0 |  | 0 |
| cycle | INTEGER | 0 |  | 0 |
| startDate | DATE | 0 |  | 0 |
| endDate | DATE | 0 |  | 0 |
| amount | TEXT | 0 |  | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| BudgetFutureSubCatStartDateEndDateIndex | 0 | subCatKey, startDate, endDate | c | 0 |

## BudgetHistory

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| budgetType | CHAR(1) | 0 | 'E' | 0 |
| catKey | INTEGER | 0 |  | 0 |
| subCatKey | INTEGER | 0 |  | 0 |
| startDate | DATE | 0 |  | 0 |
| endDate | DATE | 0 |  | 0 |
| amount | TEXT | 0 |  | 0 |
| rolloverBalance | TEXT | 0 |  | 0 |
| rolloverOnOff | CHAR(1) | 0 |  | 0 |

### Foreign keys
None

### Indexes
None

## BudgetSettings

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| budgetType | CHAR(1) | 0 | 'E' | 0 |
| catKey | INTEGER | 0 |  | 0 |
| subCatKey | INTEGER | 0 |  | 0 |
| cycle | INTEGER | 0 |  | 0 |
| startDate | DATE | 0 |  | 0 |
| endDate | DATE | 0 |  | 0 |
| amount | TEXT | 0 |  | 0 |
| rolloverOnOff | CHAR(1) | 0 | 'N' | 0 |
| rolloverBalance | TEXT | 0 |  | 0 |
| modulus | INTEGER | 0 |  | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |

### Foreign keys
None

### Indexes
None

## Category

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| name | TEXT | 0 |  | 0 |
| icon | TEXT | 0 |  | 0 |
| deleteOK | CHAR(1) | 0 | 'N' | 0 |
| seqNum | INTEGER | 0 | 0 | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |

### Foreign keys
None

### Indexes
None

## Currency

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| name | TEXT | 0 |  | 0 |
| code | TEXT | 0 |  | 0 |
| locale | TEXT | 0 |  | 0 |
| exchangeRate | TEXT | 0 |  | 0 |

### Foreign keys
None

### Indexes
None

## DeviceInfo

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| deviceId | TEXT | 0 |  | 0 |
| deviceName | TEXT | 0 |  | 0 |
| isActive | CHAR(1) | 0 |  | 0 |
| isPrimary | CHAR(1) | 0 |  | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| DeviceInfoDeviceIdIndex | 0 | deviceId | c | 0 |

## Expense

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| date | DATE | 0 |  | 0 |
| catKey | INTEGER | 0 |  | 0 |
| subCatKey | INTEGER | 0 |  | 0 |
| amount | REAL | 0 |  | 0 |
| periods | INTEGER | 0 |  | 0 |
| notes | TEXT | 0 |  | 0 |
| isDetailEntry | CHAR(1) | 0 |  | 0 |
| masterKey | INTEGER | 0 |  | 0 |
| includesReceipt | CHAR(1) | 0 | 'N' | 0 |
| payFrom | INTEGER | 0 | 0 | 0 |
| payeeKey | INTEGER | 0 | 0 | 0 |
| billKey | INTEGER | 0 | 0 | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| timeStamp | DATETIME | 0 |  | 0 |
| currency | TEXT | 0 |  | 0 |
| currencyAmount | TEXT | 0 |  | 0 |
| recurringKey | INTEGER | 0 | 0 | 0 |
| isCategorySplit | CHAR(1) | 0 | 'N' | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| ExpenseDeviceIdDeviceKeyIndex | 0 | deviceIdKey, deviceKey | c | 0 |
| ExpenseDateIndex | 0 | date | c | 0 |

## FIHints

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| accountKey | INTEGER | 0 |  | 0 |
| name | TEXT | 0 |  | 0 |
| trnType | INTEGER | 0 |  | 0 |
| processAs | INTEGER | 0 |  | 0 |
| catKey | INTEGER | 0 |  | 0 |
| subCatKey | INTEGER | 0 |  | 0 |
| payeeKey | INTEGER | 0 |  | 0 |
| account2Key | INTEGER | 0 |  | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| FIHintsNameIndex | 0 | accountKey, name, trnType | c | 0 |

## FITrans

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| accountKey | INTEGER | 0 |  | 0 |
| fiTID | TEXT | 0 |  | 0 |
| trnType | TEXT | 0 |  | 0 |
| datePosted | TEXT | 0 |  | 0 |
| trnAmount | TEXT | 0 |  | 0 |
| sic | TEXT | 0 |  | 0 |
| name | TEXT | 0 |  | 0 |
| processState | CHAR(1) | 0 | 'U' | 0 |
| processAs | INTEGER | 0 |  | 0 |
| catKey | INTEGER | 0 |  | 0 |
| subCatKey | INTEGER | 0 |  | 0 |
| payeeKey | INTEGER | 0 |  | 0 |
| account2Key | INTEGER | 0 |  | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| FITransFiTIDIndex | 0 | accountKey, fiTID | c | 0 |

## Income

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| date | DATE | 0 |  | 0 |
| name | TEXT | 0 |  | 0 |
| amount | REAL | 0 | 0.00 | 0 |
| notes | TEXT | 0 |  | 0 |
| masterKey | INTEGER | 0 |  | 0 |
| addIncomeTo | INTEGER | 0 | 0 | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| timeStamp | DATETIME | 0 |  | 0 |
| currency | TEXT | 0 |  | 0 |
| currencyAmount | TEXT | 0 |  | 0 |
| recurringKey | INTEGER | 0 | 0 | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| IncomeDeviceIdDeviceKeyIndex | 0 | deviceIdKey, deviceKey | c | 0 |
| IncomeDate | 0 | date | c | 0 |

## Payee

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| name | TEXT | 0 |  | 0 |
| accountNum | TEXT | 0 |  | 0 |
| phoneNum | TEXT | 0 |  | 0 |
| webURL | TEXT | 0 |  | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| notes | TEXT | 0 |  | 0 |

### Foreign keys
None

### Indexes
| Name | Unique | Columns | Origin | Partial |
| --- | --- | --- | --- | --- |
| PayeeDeviceIdDeviceKeyIndex | 0 | deviceIdKey, deviceKey | c | 0 |

## RecurringBill

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| billType | INTEGER | 0 | 0 | 0 |
| payeeOrAccountKey | INTEGER | 0 |  | 0 |
| amount | TEXT | 0 |  | 0 |
| nextGenDate | DATE | 0 |  | 0 |
| recurringIndex | INTEGER | 0 |  | 0 |
| modulus | INTEGER | 0 |  | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| currency | TEXT | 0 |  | 0 |
| currencyAmount | TEXT | 0 |  | 0 |
| endDate | DATE | 0 |  | 0 |
| generateNow | CHAR(1) | 0 | 'N' | 0 |
| catKey | INTEGER | 0 | 0 | 0 |
| subCatKey | INTEGER | 0 | 0 | 0 |
| fromAccountKey | INTEGER | 0 | 0 | 0 |
| notes | TEXT | 0 |  | 0 |

### Foreign keys
None

### Indexes
None

## RecurringExpense

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| subCatKey | INTEGER | 0 |  | 0 |
| catKey | INTEGER | 0 |  | 0 |
| amount | TEXT | 0 |  | 0 |
| timesAYear | INTEGER | 0 |  | 0 |
| nextGenDate | DATE | 0 |  | 0 |
| modulus | INTEGER | 0 |  | 0 |
| payFrom | INTEGER | 0 |  | 0 |
| payee | INTEGER | 0 |  | 0 |
| notes | TEXT | 0 |  | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| currency | TEXT | 0 |  | 0 |
| currencyAmount | TEXT | 0 |  | 0 |
| endDate | DATE | 0 |  | 0 |
| generateNow | CHAR(1) | 0 | 'N' | 0 |

### Foreign keys
None

### Indexes
None

## RecurringIncome

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| name | TEXT | 0 |  | 0 |
| amount | REAL | 0 | 0.00 | 0 |
| startDate | DATE | 0 |  | 0 |
| timesAYear | INTEGER | 0 |  | 0 |
| notes | TEXT | 0 |  | 0 |
| nextGenDate | DATE | 0 |  | 0 |
| modulus | INTEGER | 0 |  | 0 |
| addIncomeTo | INTEGER | 0 | 0 | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| currency | TEXT | 0 |  | 0 |
| currencyAmount | TEXT | 0 |  | 0 |
| endDate | DATE | 0 |  | 0 |
| generateNow | CHAR(1) | 0 | 'N' | 0 |

### Foreign keys
None

### Indexes
None

## RecurringTransfer

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| name | TEXT | 0 |  | 0 |
| fromAccount | INTEGER | 0 |  | 0 |
| toAccount | INTEGER | 0 |  | 0 |
| amount | REAL | 0 | 0.00 | 0 |
| timesAYear | INTEGER | 0 |  | 0 |
| nextGenDate | DATE | 0 |  | 0 |
| modulus | INTEGER | 0 |  | 0 |
| notes | TEXT | 0 |  | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| currency | TEXT | 0 |  | 0 |
| currencyAmount | TEXT | 0 |  | 0 |
| endDate | DATE | 0 |  | 0 |
| generateNow | CHAR(1) | 0 | 'N' | 0 |

### Foreign keys
None

### Indexes
None

## Settings

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| cyclestart | INTEGER | 0 |  | 0 |
| lastRun | DATETIME | 0 |  | 0 |
| currency | TEXT | 0 |  | 0 |
| initialBudget | REAL | 0 |  | 0 |
| email | TEXT | 0 |  | 0 |
| locale | TEXT | 0 |  | 0 |
| dateFormat | TEXT | 0 |  | 0 |
| imageResolution | INTEGER | 0 |  | 0 |
| deleteExpenseAfter | INTEGER | 0 |  | 0 |
| deleteReceiptAfter | INTEGER | 0 |  | 0 |
| debugFlag | INTEGER | 0 |  | 0 |
| screenMajor | INTEGER | 0 |  | 0 |
| screenMinor |  | 0 |  | 0 |
| screenMini | INTEGER | 0 |  | 0 |
| screenMicro | INTEGER | 0 |  | 0 |
| passwordOnOff | INTEGER | 0 |  | 0 |
| password | TEXT | 0 |  | 0 |
| passwordEmail | TEXT | 0 |  | 0 |
| future1 | TEXT | 0 |  | 0 |
| future2 | TEXT | 0 |  | 0 |
| future3 | TEXT | 0 |  | 0 |
| future4 | TEXT | 0 |  | 0 |
| future5 | TEXT | 0 |  | 0 |
| future6 | TEXT | 0 |  | 0 |
| future7 | TEXT | 0 |  | 0 |
| future8 | TEXT | 0 |  | 0 |
| future9 | TEXT | 0 |  | 0 |
| future10 | TEXT | 0 |  | 0 |
| lastUsedAccount | INTEGER | 0 | 0 | 0 |
| colorScheme | INTEGER | 0 | 2 | 0 |
| lastUsedPayee | INTEGER | 0 | 0 | 0 |
| monthlyCycleStart | INTEGER | 0 | 1 | 0 |
| rolloverStart | TEXT | 0 | '' | 0 |
| showBillReminders | CHAR(1) | 0 | 'N' | 0 |
| showBillBadge | CHAR(1) | 0 | 'N' | 0 |
| startPage | INTEGER | 0 | 0 | 0 |
| includeFutureTrans | CHAR(1) | 0 | 'Y' | 0 |
| showMonthlyBudgetView | CHAR(1) | 0 | 'N' | 0 |
| keyBoardClicks | CHAR(1) | 0 | 'Y' | 0 |
| billLookForward | INTEGER | 0 | 6 | 0 |
| billNotifyHour | INTEGER | 0 | 2 | 0 |
| showAmountInNumbers | CHAR(1) | 0 | 'N' | 0 |
| importMatchLength | INTEGER | 0 | 16 | 0 |
| homeScreenStyle | INTEGER | 0 | 1 | 0 |

### Foreign keys
None

### Indexes
None

## SubCategory

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| catKey | INTEGER | 0 |  | 0 |
| name | TEXT | 0 |  | 0 |
| icon | TEXT | 0 |  | 0 |
| deleteOK | CHAR(1) | 0 | 'Y' | 0 |
| amount | REAL | 0 | 0.00 | 0 |
| forPeriod | INTEGER | 0 | 1 | 0 |
| autoGenExpEntry | CHAR(1) | 0 | 'N' | 0 |
| autoGenDay | INTEGER | 0 | 1 | 0 |
| recurExpAmount | TEXT | 0 |  | 0 |
| nextGenDate | DATE | 0 |  | 0 |
| timesAYear | INTEGER | 0 |  | 0 |
| modulus | INTEGER | 0 |  | 0 |
| payFrom | INTEGER | 0 | 0 | 0 |
| expenseType | INTEGER | 0 | 1 | 0 |
| seqNum | INTEGER | 0 | 0 | 0 |
| payee | INTEGER | 0 | 0 | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |

### Foreign keys
None

### Indexes
None

## SyncInfo

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| inAGroup | CHAR(1) | 0 |  | 0 |
| groupName | TEXT | 0 |  | 0 |
| password | TEXT | 0 |  | 0 |
| passwordEmail | TEXT | 0 |  | 0 |
| lastUpdateSeq | INTEGER | 0 |  | 0 |
| enforceRestrictions | CHAR(1) | 0 |  | 0 |
| lastSync | DATETIME | 0 |  | 0 |

### Foreign keys
None

### Indexes
None

## SyncUpdate

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| updateType | TEXT | 0 |  | 0 |
| uuid | TEXT | 0 |  | 0 |
| payload | TEXT | 0 |  | 0 |

### Foreign keys
None

### Indexes
None

## Transfer

### Columns
| Name | Type | Not null | Default | PK |
| --- | --- | --- | --- | --- |
| key | INTEGER | 0 |  | 1 |
| transferDate | DATE | 0 |  | 0 |
| fromAccount | INTEGER | 0 |  | 0 |
| toAccount | INTEGER | 0 |  | 0 |
| amount | REAL | 0 | 0.00 | 0 |
| notes | TEXT | 0 |  | 0 |
| billKey | INTEGER | 0 | 0 | 0 |
| deviceIdKey | INTEGER | 0 |  | 0 |
| deviceKey | INTEGER | 0 |  | 0 |
| currency | TEXT | 0 |  | 0 |
| currencyAmount | TEXT | 0 |  | 0 |
| recurringKey | INTEGER | 0 | 0 | 0 |

### Foreign keys
None

### Indexes
None
