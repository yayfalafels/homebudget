# Manual UAT: Account List Feature

## Account List Manual Test

### Prerequisites
- HomeBudget Windows app installed with test database
- Wrapper package installed: `pip install -e src/python/`
- At least 3 accounts in the test database

### Test Procedure

1. **Setup**: Activate main env and navigate to workspace directory
   ```powershell
   & env\Scripts\Activate.ps1
   cd c:\Users\taylo\VSCode_yayfalafels\homebudget
   ```

2. **USER ACTION**: Run the command
   ```bash
   hb account list
   ```

3. **VERIFY** - Output displays:
   - [ ] All accounts from the database appear in the output
   - [ ] Account names are properly formatted and readable
   - [ ] Account balances show correctly with 2 decimal places
   - [ ] Account types are displayed (Checking, Savings, Credit Card, etc.)
   - [ ] Accounts are ordered alphabetically by name
   - [ ] No errors or exceptions in console

4. **USER FEEDBACK**:
   - Is the output format clear and easy to read?
   - Are all accounts visible?
   - Would you like any additional information (e.g., currency)?

### Result
- [ ] PASS - All accounts display correctly
- [ ] FAIL - [Note issues]

### Notes
```
[Test notes and observations]
```
