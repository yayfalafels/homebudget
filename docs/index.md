# HomeBudget Python wrapper

- [Overview](#overview)
- [Situation](#situation)
- [Aims](#aims)
- [Reference resources](#reference-resources)

## Overview

The HomeBudget Python wrapper is a Python library and CLI that provides programmatic access to HomeBudget data. It enables full CRUD operations for expenses, income, and transfers with automatic sync to mobile devices. The wrapper is designed to be easy to use and integrate into automation scripts and workflows.

## Situation

The HomeBudget application is a legacy application with a UI and a sqlite database backend. It is time consuming and tedious to perform routine operations such as adding, updating, deleting transactions through the Desktop UI. A proof-of-concept Python wrapper module (homebudget.py) was developed with limited functionality for adding expenses via direct calls to the sqlite database.

## Aims

The aim of the wrapper is to

1. expand the wrapper's functionality to cover more operations and features of the HomeBudget application with full CRUD operations for income, expenses, transfers and operations in foreign currencies.
2. package the wrapper as a Python library that can be easily installed and used by other developers.
3. provide a command-line interface (CLI) for interacting with the wrapper.

## Reference resources

- [HomeBudget application](https://www.anishu.com/homebudget/)
- POC Python wrapper module (homebudget.py, local reference)
- hb-finances reference implementation (local reference)
- sample HB sqlite database (local reference)