# Type Checking Guide for Agency OS

## Understanding mypy Output

### The [annotation-unchecked] Notes

When running `mypy`, you'll see many lines like:
```
note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs
```

**What it means:** These are notes, not errors. mypy is pointing out functions in your code that don't have type hints. By default, it doesn't analyze the code inside those functions.

**Why it's useful:** It's a reminder that there are still parts of your codebase that are not being fully type-checked. Adding type hints to these functions would improve your type coverage and potentially catch more bugs.

### How to Improve Type Coverage

1. **Add type hints to function signatures:**
   ```python
   # Before (unchecked)
   def process_data(data):
       return data.strip().lower()

   # After (type-checked)
   def process_data(data: str) -> str:
       return data.strip().lower()
   ```

2. **Use the Result<T,E> pattern for error handling:**
   ```python
   from shared.type_definitions.result import Result, Ok, Err

   def safe_divide(a: float, b: float) -> Result[float, str]:
       if b == 0:
           return Err("Division by zero")
       return Ok(a / b)
   ```

3. **Enable stricter checking for specific modules:**
   - Edit `mypy.ini` to enable `check_untyped_defs = true` for modules you're working on
   - This will check the bodies of functions even without type hints

### Common mypy Configuration Issues

#### Duplicate Section Headers
If you see an error like:
```
While reading from 'mypy.ini': section 'mypy-module.name' already exists
```

**Fix:** Open `mypy.ini` and find the duplicate section. Either:
- Merge the configurations into a single section
- Delete the redundant section

#### Boolean Case Sensitivity
In `mypy.ini`, use lowercase booleans:
- ✅ Correct: `strict = false`, `check_untyped_defs = true`
- ❌ Wrong: `strict = False`, `check_untyped_defs = True`

### Gradual Type Adoption Strategy

The Agency OS uses a gradual typing approach:

1. **Phase 1 (Current):** Core modules have `ignore_errors = true` to allow development
2. **Phase 2:** Add type hints to new code and critical paths
3. **Phase 3:** Progressively enable stricter checking per module
4. **Phase 4:** Achieve full type safety compliance

### Running Type Checks

```bash
# Basic type checking
mypy .

# Check untyped function bodies (more thorough)
mypy --check-untyped-defs .

# Check specific module
mypy agency_memory/

# Ignore notes (focus on errors only)
mypy . 2>&1 | grep -v "note:"
```

### Type Safety Best Practices

1. **Always use type hints for new code**
2. **Prefer Result<T,E> over try/except for control flow**
3. **Use Pydantic models instead of plain dicts**
4. **Enable strict mode gradually per module**
5. **Run mypy in CI/CD pipelines**

### Resources

- [mypy documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [Agency OS Result Pattern](../shared/type_definitions/result.py)