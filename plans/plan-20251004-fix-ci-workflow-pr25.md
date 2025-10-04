# Tactical Plan: Fix CI Workflow Issues in PR #25

**Plan ID**: plan-20251004-fix-ci-workflow-pr25
**Status**: Ready for Execution
**Estimated Duration**: 15 minutes
**Constitutional Compliance**: Articles I, II, III

---

## Overview

### Problem Statement
PR #25 is failing in the "Analyze PR Changes" step due to GitHub Actions multiline output format violation when handling deleted files with special characters in paths (e.g., `.test_bloat_backup_20251003_230743/trinity_protocol/test_witness_agent.py`).

**Error**: `##[error]Invalid format '.test_bloat_backup_20251003_230743/archived/trinity_legacy/test_daily_checkin.py'`

### Root Cause
The workflow uses:
```bash
echo "files=$CHANGED_FILES" >> $GITHUB_OUTPUT
```

This fails when `$CHANGED_FILES` contains:
1. Multiple lines (40 deleted Python files)
2. Special characters (dots, underscores, slashes in backup directory paths)
3. GitHub Actions multiline output requires special EOF delimiter syntax

### Success Criteria
- [ ] PR #25 "Analyze PR Changes" step passes
- [ ] Workflow handles deleted files correctly
- [ ] Workflow handles files with special characters in paths
- [ ] All other workflows continue working (no regressions)
- [ ] Constitutional compliance maintained (Articles I-III)

---

## Architecture

### Affected Files
- `/Users/am/Code/Agency/.github/workflows/pr_checks.yml` (PRIMARY)

### Dependencies
- GitHub Actions multiline output syntax (EOF delimiters)
- Git diff command behavior with deleted files
- JSON serialization for safe multiline output transfer

### Technical Approach
**Option A**: Use GitHub Actions multiline output syntax with EOF delimiters (RECOMMENDED)
**Option B**: Use JSON array serialization for file list transfer
**Option C**: Skip analysis step if all files are deletions

We will use **Option A** (multiline EOF delimiters) as the primary fix with **Option B** (JSON array) as the output format, providing both safety and compatibility.

---

## Task Breakdown

### TASK-001: Fix multiline output format in pr_checks.yml
**Priority**: CRITICAL
**Estimated Time**: 5 minutes
**Dependencies**: None

#### TASK-001.1: Update "Detect changed files" step
**Acceptance Criteria**:
- Use GitHub Actions EOF delimiter syntax for multiline output
- Handle special characters in file paths safely
- Convert newline-separated list to JSON array for reliable transfer
- Preserve existing file count logic

**Implementation**:
1. Locate step at lines 34-45 in `/Users/am/Code/Agency/.github/workflows/pr_checks.yml`
2. Replace the output generation block with EOF delimiter syntax
3. Add null-byte safety for paths with spaces/special chars
4. Convert to JSON array for reliable cross-step transfer

**Code Change**:
```yaml
# OLD (BROKEN):
- name: Detect changed files
  id: changes
  run: |
    # Get all changed Python files
    CHANGED_FILES=$(git diff --name-only ${{ github.event.pull_request.base.sha }}...${{ github.sha }} | grep '\.py$' || echo "")
    FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l)

    echo "files=$CHANGED_FILES" >> $GITHUB_OUTPUT
    echo "count=$FILE_COUNT" >> $GITHUB_OUTPUT

    echo "Changed Python files ($FILE_COUNT):"
    echo "$CHANGED_FILES"

# NEW (FIXED):
- name: Detect changed files
  id: changes
  run: |
    # Get all changed Python files (handles deletions and special chars)
    CHANGED_FILES=$(git diff --name-only ${{ github.event.pull_request.base.sha }}...${{ github.sha }} | grep '\.py$' || echo "")

    # Count files (handle empty result)
    if [ -z "$CHANGED_FILES" ]; then
      FILE_COUNT=0
    else
      FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l)
    fi

    # Use multiline EOF delimiter for GitHub Actions output (handles special chars)
    {
      echo 'files<<EOF'
      echo "$CHANGED_FILES"
      echo 'EOF'
    } >> $GITHUB_OUTPUT

    echo "count=$FILE_COUNT" >> $GITHUB_OUTPUT

    echo "Changed Python files ($FILE_COUNT):"
    echo "$CHANGED_FILES"
```

**Why This Works**:
- GitHub Actions multiline output syntax uses heredoc-style EOF delimiters
- Syntax: `echo 'key<<EOF' ... echo 'EOF'` wrapped in `{ }` block
- Handles any special characters (dots, slashes, underscores, spaces)
- Preserves empty lines and multiline values safely
- Standard GitHub Actions best practice for multiline outputs

---

### TASK-002: Validate downstream step compatibility
**Priority**: HIGH
**Estimated Time**: 3 minutes
**Dependencies**: TASK-001

#### TASK-002.1: Verify "Determine test mode" step compatibility
**Acceptance Criteria**:
- Step correctly reads `${{ steps.changes.outputs.files }}` with new format
- File iteration logic handles multiline string correctly
- Empty file list case handled gracefully

**Validation Points**:
1. Line 51: `CHANGED_FILES="${{ steps.changes.outputs.files }}"` - works with multiline
2. Line 63: `for file in $CHANGED_FILES` - bash loop handles multiline correctly
3. Line 70-82: Empty string case already handled by existing conditions

**Action**: No changes needed - bash handles multiline variables correctly in for-loops

---

### TASK-003: Test validation and verification
**Priority**: CRITICAL
**Estimated Time**: 7 minutes
**Dependencies**: TASK-001, TASK-002

#### TASK-003.1: Local validation (pre-push)
**Steps**:
1. Create test script to simulate GitHub Actions behavior:
```bash
# Test multiline output syntax
TEST_FILES=$(cat <<'EOF'
.test_bloat_backup_20251003_230743/archived/trinity_legacy/test_budget_enforcer.py
.test_bloat_backup_20251003_230743/trinity_protocol/test_witness_agent.py
health_check.py
EOF
)

# Simulate GitHub Actions output processing
{
  echo 'files<<EOF'
  echo "$TEST_FILES"
  echo 'EOF'
} > /tmp/test_output.txt

# Verify format
cat /tmp/test_output.txt
```

2. Verify output contains:
   - `files<<EOF` as first line
   - All file paths as-is (with special chars)
   - `EOF` as last line

**Expected Output**:
```
files<<EOF
.test_bloat_backup_20251003_230743/archived/trinity_legacy/test_budget_enforcer.py
.test_bloat_backup_20251003_230743/trinity_protocol/test_witness_agent.py
health_check.py
EOF
```

#### TASK-003.2: CI validation (post-push)
**Steps**:
1. Push changes to PR #25 branch (`fix/test-infra-clean`)
2. Monitor GitHub Actions workflow execution
3. Verify "Analyze PR Changes" step passes
4. Verify "Determine test mode" step reads files correctly
5. Verify no regression in other workflow steps

**Success Indicators**:
- Green check on "Analyze PR Changes" step
- No `##[error]Invalid format` messages
- Test mode determination succeeds
- Downstream steps execute (even if fail for other reasons)

---

## Implementation Order

### Phase 1: Code Fix (5 minutes)
1. Edit `/Users/am/Code/Agency/.github/workflows/pr_checks.yml`
2. Update lines 34-45 per TASK-001.1 specification
3. Verify YAML syntax validity

### Phase 2: Local Validation (3 minutes)
1. Run local test script (TASK-003.1)
2. Verify multiline output format
3. Confirm no syntax errors

### Phase 3: CI Validation (7 minutes)
1. Commit changes to PR #25 branch
2. Push and monitor workflow execution
3. Verify all checks pass or fail for expected reasons
4. Document any new failures unrelated to this fix

---

## Quality Gates

### Pre-Commit Checklist
- [ ] YAML syntax valid (no tab characters, correct indentation)
- [ ] EOF delimiter syntax correct (`'files<<EOF'` with quotes)
- [ ] Heredoc block properly wrapped in `{ }` braces
- [ ] No unintended changes to other workflow sections
- [ ] Local validation test passes

### Post-Commit Checklist
- [ ] "Analyze PR Changes" step completes successfully
- [ ] No `##[error]Invalid format` errors in logs
- [ ] File count output is correct (40 files for PR #25)
- [ ] "Determine test mode" step executes without errors
- [ ] PR Summary section displays correctly

### Constitutional Compliance Checkpoints

#### Article I: Complete Context Before Action
- [ ] Full git diff retrieved before analysis
- [ ] No truncation of file list due to format errors
- [ ] Deleted files included in analysis correctly

#### Article II: 100% Verification
- [ ] Workflow completes all steps (no premature exit)
- [ ] Test mode determination based on complete file list
- [ ] No broken windows introduced by partial file analysis

#### Article III: Automated Merge Enforcement
- [ ] Fix is minimal and surgical (no workflow logic changes)
- [ ] No bypass of existing quality gates
- [ ] PR gate logic unchanged

---

## Risk Assessment

### Low Risk
- **Multiline output syntax**: Standard GitHub Actions feature, well-documented
- **Backward compatibility**: New format is transparent to downstream steps
- **Empty file list**: Explicitly handled with zero-count case

### Medium Risk
- **Deleted files edge case**: Validated via PR #25 test case (40 deletions)
- **Special characters**: Handled by EOF delimiter syntax (no escaping needed)

### Mitigation Strategies
1. **Test with PR #25**: Real-world test case with problematic file paths
2. **Fallback option**: If fails, can use JSON array serialization as backup
3. **Rollback plan**: Single file change, easy to revert via git

---

## Testing Strategy

### Unit Test (Local)
```bash
# Validate multiline output format
bash -c '
CHANGED_FILES=$(cat <<EOF
.test_bloat_backup_20251003_230743/archived/trinity_legacy/test_budget_enforcer.py
path/with spaces/file.py
special@chars#file.py
EOF
)

{
  echo "files<<EOF"
  echo "$CHANGED_FILES"
  echo "EOF"
} > /tmp/output.txt

# Verify format
grep -q "files<<EOF" /tmp/output.txt && \
grep -q ".test_bloat_backup" /tmp/output.txt && \
grep -q "EOF$" /tmp/output.txt && \
echo "✅ Format validation passed" || \
echo "❌ Format validation failed"
'
```

### Integration Test (CI)
- **Test Case**: PR #25 with 40 deleted Python files
- **Expected**: "Analyze PR Changes" step passes, outputs 40 file paths
- **Validation**: Check workflow logs for successful output generation

### Regression Test
- **Test Case**: Create new PR with normal Python file changes (no deletions)
- **Expected**: Workflow behaves identically to before
- **Validation**: File list transfer and test mode determination work correctly

---

## Rollback Plan

### If Workflow Still Fails
1. **Option A**: Use JSON array serialization instead
```yaml
# Convert to JSON array for robust transfer
FILES_JSON=$(echo "$CHANGED_FILES" | jq -R -s -c 'split("\n") | map(select(length > 0))')
echo "files=$FILES_JSON" >> $GITHUB_OUTPUT

# Downstream usage
CHANGED_FILES=$(echo '${{ steps.changes.outputs.files }}' | jq -r '.[]')
```

2. **Option B**: Skip analysis for deletion-only PRs
```yaml
if [[ "$CHANGED_FILES" =~ ^\.test_bloat_backup ]]; then
  echo "Skipping analysis for backup deletions"
  exit 0
fi
```

3. **Option C**: Revert entire commit
```bash
git revert <commit-hash> --no-edit
git push origin fix/test-infra-clean
```

---

## Documentation Updates

### Required Updates
- None (internal workflow fix, no external API changes)

### Optional Updates
- Add comment in pr_checks.yml explaining EOF delimiter syntax for future maintainers

---

## Execution Summary

### Files to Modify
1. `/Users/am/Code/Agency/.github/workflows/pr_checks.yml` (lines 34-45)

### Commands to Run
```bash
# 1. Make changes (via Edit tool)
# 2. Local validation
bash -c 'CHANGED_FILES=$(cat <<EOF
.test_bloat_backup_20251003_230743/test.py
health_check.py
EOF
); { echo "files<<EOF"; echo "$CHANGED_FILES"; echo "EOF"; } > /tmp/output.txt; cat /tmp/output.txt'

# 3. Commit and push
git add .github/workflows/pr_checks.yml
git commit -m "fix: Use EOF delimiter syntax for multiline GitHub Actions output

Fixes the 'Invalid format' error in PR checks workflow when analyzing
PRs with deleted files containing special characters in paths.

- Replace direct output assignment with EOF heredoc syntax
- Handle empty file list case explicitly
- Maintain backward compatibility with downstream steps

Constitutional Compliance:
- Article I: Complete context (no truncated file lists)
- Article II: 100% verification (all files analyzed)
- Article III: No bypass of quality gates

Fixes workflow failures in PR #25"

git push origin fix/test-infra-clean

# 4. Monitor CI
gh run watch
```

### Expected Timeline
- **Code change**: 2 minutes
- **Local validation**: 3 minutes
- **Commit/push**: 1 minute
- **CI execution**: 5-10 minutes
- **Total**: ~15 minutes

---

## Appendix

### GitHub Actions Multiline Output Reference
**Documentation**: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#multiline-strings

**Syntax**:
```yaml
run: |
  {
    echo 'key_name<<EOF'
    echo "multiline value"
    echo "with special chars: ./@#$"
    echo 'EOF'
  } >> $GITHUB_OUTPUT
```

**Usage**:
```yaml
steps:
  - id: step1
    run: |
      {
        echo 'my_output<<EOF'
        echo "line 1"
        echo "line 2"
        echo 'EOF'
      } >> $GITHUB_OUTPUT

  - run: |
      echo "Output was: ${{ steps.step1.outputs.my_output }}"
```

### Alternative: JSON Array Approach
If EOF delimiters fail, use JSON for robust serialization:

```yaml
- name: Detect changed files
  id: changes
  run: |
    # Get changed files as JSON array (handles all edge cases)
    CHANGED_FILES=$(git diff --name-only ${{ github.event.pull_request.base.sha }}...${{ github.sha }} | grep '\.py$' || echo "")

    if [ -z "$CHANGED_FILES" ]; then
      FILES_JSON="[]"
      FILE_COUNT=0
    else
      FILES_JSON=$(echo "$CHANGED_FILES" | jq -R -s -c 'split("\n") | map(select(length > 0))')
      FILE_COUNT=$(echo "$FILES_JSON" | jq 'length')
    fi

    echo "files=$FILES_JSON" >> $GITHUB_OUTPUT
    echo "count=$FILE_COUNT" >> $GITHUB_OUTPUT

- name: Determine test mode
  run: |
    # Parse JSON array
    CHANGED_FILES=$(echo '${{ steps.changes.outputs.files }}' | jq -r '.[]')
    # Rest of logic unchanged
```

**Pros**: Bulletproof serialization, handles all edge cases
**Cons**: Requires `jq` installed in runner (already available in ubuntu-latest)

---

**Plan Status**: Ready for execution
**Blocker Status**: None
**Next Action**: Execute TASK-001.1 (Edit pr_checks.yml)
