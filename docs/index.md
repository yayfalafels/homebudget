# HomeBudget Python wrapper

- [Overview](#overview)
- [Situation](#situation)
- [Aims](#aims)
- [Reference resources](#reference-resources)

## Overview

The HomeBuget Python wrapper (wrapper) is a Python library that provides an interface to interact with the HomeBudget application. It allows developers to perform similar operations as the HomeBudget application, such as managing accounts, transactions, and budgets, but through a Python interface. The wrapper is designed to be easy to use and integrate into other Python applications or scripts.

## Situation

The HomeBudget application is a legacy application with a UI and a sqlite database backend. It is time consuming and tedious to perform routine operations such as adding, updating, deleting transactions through the Desktop UI. A proof-of-concept Python wrapper module [homebudget.py](../reference/hb-finances/homebudget.py) has already been developed with limited functionality for adding expenses via direct calls to the sqlite database.

## Aims

The aim of the wrapper is to

1. expand the wrapper's functionality to cover more operations and features of the HomeBudget application with full CRUD operations for income, expenses, transfers and operations in foreign currencies.
2. package the wrapper as a Python library that can be easily installed and used by other developers.
3. provide a command-line interface (CLI) for interacting with the wrapper.

## Reference resources

- [HomeBudget application](https://www.anishu.com/homebudget/)
- [POC Python wrapper module](../reference/hb-finances/homebudget.py)
- [hb-finances that implements the wrapper](../reference/hb-finances)
- [sample HB sqlite database](../reference/hb-sqlite-db/homebudget.db)