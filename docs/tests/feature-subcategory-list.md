# Manual UAT: Subcategory List Feature

## Subcategory List Manual Test

### Prerequisites
- HomeBudget Windows app installed with test database
- At least one category with subcategories
- Wrapper package installed: `pip install -e src/python/`

### Test Procedure

1. **Setup**: Activate main env, note a category name from `hb category list`
   ```powershell
   & env\Scripts\Activate.ps1
   cd c:\Users\taylo\VSCode_yayfalafels\homebudget
   hb category list
   # Note a category name, e.g., "Groceries" or "Utilities"
   ```

2. **USER ACTION**: Run the command with a real category
   ```bash
   hb category subcategories --category "Groceries"
   ```

3. **VERIFY** - Output displays:

   - [ ] Parent category name is shown
   - [ ] All subcategories for that category appear
   - [ ] Subcategory names are clear and readable
   - [ ] Subcategories are ordered by sequence number
   - [ ] No errors or exceptions in console

4. **USER ACTION**: Test with non-existent category
   ```bash
   hb category subcategories --category "NonExistentCategory"
   ```

5. **VERIFY** - Error handling:

   - [ ] Clear error message displayed (not a stack trace)
   - [ ] Message indicates category was not found
   - [ ] Command exits cleanly

6. **USER FEEDBACK**:

   - Is the output helpful for viewing subcategories?
   - Is the format clear?
   - Would you like filtering or additional information?

### Result

- [ ] PASS - Subcategories display and errors handled correctly
- [ ] FAIL - [Note issues]

### Notes
```
[Test notes and observations]
```
