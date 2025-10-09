# Claude Code Pre-Tool-Use Quality Gate Hook

**Strategic Goal**: Eliminate 50% of merge time waste by catching lint/format errors BEFORE files are written to disk.

## Overview

The `pre_tool_use.py` hook validates Python code quality **before** Claude Code writes files. This prevents low-quality code from ever reaching the filesystem, eliminating the expensive fix-after-write cycle.

## Quality Gates Enforced

### 1. Ruff Lint (Exit 0 Required)
- Unused imports
- Undefined names
- Style violations
- **Block**: Any lint error prevents file write

### 2. Ruff Format (Exit 0 Required)
- Consistent spacing
- Line length compliance
- Import sorting
- **Block**: Unformatted code prevents file write

### 3. Dict[str, Any] Ban (Constitutional Law #2)
- No `dict[str, Any]` types
- No `Dict[str, Any]` types
- **Rationale**: Use Pydantic models with typed fields
- **Block**: Any Dict[Any] usage prevents file write

### 4. Function Length <50 Lines (Constitutional Law #8)
- All functions must be under 50 lines
- **Rationale**: Focused, single-purpose functions
- **Block**: Long functions prevent file write

## Installation

### 1. Copy Hook to Your Project

```bash
cp /Users/am/Code/Agency-hooks-analysis/.claude/hooks/pre_tool_use.py \
   /path/to/your/project/.claude/hooks/
chmod +x /path/to/your/project/.claude/hooks/pre_tool_use.py
```

### 2. Configure Claude Code

Edit your `.claude/config.json` (or global config):

```json
{
  "hooks": {
    "pre_tool_use": ".claude/hooks/pre_tool_use.py"
  }
}
```

### 3. Verify Installation

```bash
python .claude/hooks/test_pre_tool_use.py
```

Expected output:
```
Running pre_tool_use.py quality gate tests...

✅ Test 1 passed: Valid code allowed
✅ Test 2 passed: Lint violations blocked
✅ Test 3 passed: Format violations blocked
✅ Test 4 passed: Dict[Any] violations blocked
✅ Test 5 passed: Long functions blocked
✅ Test 6 passed: Edit tool allowed (surgical edits)
✅ Test 7 passed: Non-Python files ignored
✅ Test 8 passed: Non-file tools ignored

============================================================
Results: 8/8 tests passed
✅ All tests passed!
```

## How It Works

### Input Format (JSON via stdin)

```json
{
  "tool_name": "Write",
  "args": {
    "file_path": "src/user_service.py",
    "content": "def create_user():\n    pass"
  }
}
```

### Validation Flow

```
Claude Code → Write Tool Request
    ↓
pre_tool_use.py hook
    ↓
┌─────────────────────┐
│ Quality Gates       │
│ 1. Ruff lint        │
│ 2. Ruff format      │
│ 3. Dict[Any] ban    │
│ 4. Function <50L    │
└─────────────────────┘
    ↓
Exit Code Decision
    ↓
├─ 0: Allow write (quality OK)
├─ 2: Block write (violations found)
└─ 1: Script error
```

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Quality OK | Allow file write |
| 2 | Quality violations | Block file write, show errors |
| 1 | Script error | Allow write (fail open for safety) |

## Tools Validated

- ✅ **Write**: Full validation (new files)
- ✅ **NotebookEdit**: Full validation (notebook cells)
- ❌ **Edit**: Bypassed (surgical edits to existing files)
- ❌ **MultiEdit**: Bypassed (complex reconstruction)
- ❌ **Non-Python**: Bypassed (only .py files validated)

## Example Error Messages

### Lint Violation

```
❌ Quality Gate Failed for src/user_service.py:

Ruff lint errors:
src/user_service.py:3:8: F401 `os` imported but unused

🔧 Fix these issues before writing the file.
```

### Format Violation

```
❌ Quality Gate Failed for src/user_service.py:

Ruff format required (run: ruff format src/user_service.py)

🔧 Fix these issues before writing the file.
```

### Dict[Any] Violation

```
❌ Quality Gate Failed for src/user_service.py:

Dict[str, Any] violation - use Pydantic models with typed fields (Constitutional Law #2)

🔧 Fix these issues before writing the file.
```

### Long Function Violation

```
❌ Quality Gate Failed for src/user_service.py:

Function 'process_user_data' exceeds 50 lines (72 lines at line 15) - Constitutional Law #8

🔧 Fix these issues before writing the file.
```

## Constitutional Compliance

This hook enforces:

- **Article I**: Complete Context Before Action
  - Validates code BEFORE writing (complete quality context)

- **Article II**: 100% Verification and Stability
  - Deterministic quality gates (no subjective judgment)
  - All validations must pass (100% enforcement)

- **Constitutional Law #2**: Strict Typing Always
  - No `Dict[Any, Any]` types allowed
  - Forces use of Pydantic models

- **Constitutional Law #8**: Focused Functions
  - Functions must be under 50 lines
  - Enforces single-purpose design

## Performance Impact

### Time Added Per Write

- **Ruff lint**: ~50ms
- **Ruff format**: ~30ms
- **Dict[Any] check**: ~5ms (regex)
- **Function length**: ~10ms (parsing)
- **Total**: ~95ms per Python file write

### Merge Time Saved

**Before Hook** (fix-after-write cycle):
1. Write file (0ms)
2. Run tests (30s)
3. Tests fail due to lint errors
4. Fix lint errors (2 min manual)
5. Re-run tests (30s)
6. **Total**: ~3 minutes

**After Hook** (prevent-bad-writes):
1. Validate before write (95ms)
2. Fix violations in Claude prompt
3. Write correct file (0ms)
4. Run tests (30s)
5. Tests pass
6. **Total**: ~30 seconds

**Savings**: 2.5 minutes per file = 50% reduction in merge time

## Testing

### Run Full Test Suite

```bash
python .claude/hooks/test_pre_tool_use.py
```

### Manual Testing

```bash
# Test valid code (should allow)
echo '{"tool_name":"Write","args":{"file_path":"test.py","content":"def test():\n    pass\n"}}' | \
  python .claude/hooks/pre_tool_use.py
echo $?  # Expected: 0

# Test lint violation (should block)
echo '{"tool_name":"Write","args":{"file_path":"test.py","content":"import os\ndef test():\n    pass\n"}}' | \
  python .claude/hooks/pre_tool_use.py
echo $?  # Expected: 2
```

## Limitations

### 1. Edit Tool Not Validated
- **Rationale**: Edit makes surgical changes to existing files
- **Risk**: Could introduce violations in already-passing files
- **Mitigation**: Pre-commit hooks catch violations before merge

### 2. MultiEdit Not Validated
- **Rationale**: Complex reconstruction of full file state
- **Risk**: Could introduce violations
- **Mitigation**: Pre-commit hooks catch violations before merge

### 3. Temporary Files Used
- **Rationale**: Ruff requires files on disk
- **Risk**: ~10 file creates/deletes per validation
- **Mitigation**: Fast (tmpfs on most systems)

### 4. No Type Checking
- **Rationale**: Mypy/Pyright too slow for pre-write hook (>1s)
- **Risk**: Type errors only caught at test time
- **Mitigation**: Pre-commit hooks run mypy before merge

## Future Enhancements

### Phase 2: TypeScript Support
- Add TSC type checking
- Add ESLint validation
- Add Prettier format validation

### Phase 3: Edit Tool Validation
- Reconstruct full file state (read existing + apply edit)
- Validate reconstructed file
- Block if violations introduced

### Phase 4: Incremental Validation
- Cache validation results per file hash
- Skip validation if file unchanged
- 10x speedup for repeated writes

## Troubleshooting

### Hook Not Running

**Symptom**: Files written without validation

**Diagnosis**:
```bash
# Check hook is executable
ls -la .claude/hooks/pre_tool_use.py

# Should show: -rwxr-xr-x (executable bit set)
```

**Fix**:
```bash
chmod +x .claude/hooks/pre_tool_use.py
```

### False Positives

**Symptom**: Valid code blocked

**Diagnosis**:
```bash
# Run hook manually to see errors
echo '{"tool_name":"Write","args":{"file_path":"test.py","content":"YOUR_CODE_HERE"}}' | \
  python .claude/hooks/pre_tool_use.py
```

**Fix**:
- Address the specific error shown (likely legitimate issue)
- If truly false positive, open issue with example

### Ruff Not Found

**Symptom**: Hook fails with "ruff: command not found"

**Fix**:
```bash
# Install ruff
pip install ruff

# Or via uv
uv pip install ruff
```

## License

MIT License - Same as Agency OS

## Author

Created for Agency OS autonomous agent framework.

## References

- **Agency Constitution**: `/Users/am/Code/Agency/constitution.md`
- **ADR-001**: Complete Context Before Action
- **ADR-002**: 100% Verification and Stability
- **Constitutional Laws**: 10 unbreakable rules for code quality
