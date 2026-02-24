# Manual UAT: Category List Feature

## Category List Manual Test

### Prerequisites
- HomeBudget Windows app installed with test database
- Wrapper package installed: `pip install -e src/python/`
- Expense categories configured in the database

### Test Procedure

1. **Setup**: Activate main env
   ```powershell
   & env\Scripts\Activate.ps1
   cd c:\Users\taylo\VSCode_yayfalafels\homebudget
   ```

2. **USER ACTION**: Run the command
   ```bash
   hb category list
   ```

3. **VERIFY** - Output displays:
   - [ ] All expense categories appear in the output
   - [ ] Category names are clear and readable
   - [ ] Sequence numbers indicate display order
   - [ ] Output is ordered by sequence number
   - [ ] No errors or exceptions in console

4. **USER FEEDBACK**:
   - Is the output format helpful for selecting categories?
   - Are all categories visible?
   - Would you like any additional information?

### Result
- [ ] PASS - All categories display correctly
- [ ] FAIL - [Note issues]

### Notes
```
[Test notes and observations]
```
