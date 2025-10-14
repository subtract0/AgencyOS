# GitHub Pro Setup for Constitutional Compliance

**Cost**: $4/month
**Benefit**: Full Article III compliance (automated merge enforcement)

---

## Setup Instructions

### 1. Upgrade to GitHub Pro

**Manual Step** (you must do this):
1. Visit: https://github.com/settings/billing/summary
2. Click "Upgrade to Pro"
3. Enter payment info ($4/month)
4. Confirm upgrade

### 2. Enable Branch Protection

**After upgrading to Pro**, run this script:

```bash
chmod +x scripts/setup_branch_protection.sh
./scripts/setup_branch_protection.sh
```

This configures:
- ✅ Required CI checks before merge
- ✅ No force pushes to main
- ✅ No branch deletion
- ✅ Enforce for all (even admins)
- ✅ Require conversation resolution

### 3. Test the Setup

Create a test PR:

```bash
# Create feature branch
git checkout -b test/ci-validation

# Make a small change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "test: Validate CI pipeline"
git push -u origin test/ci-validation

# Create PR
gh pr create --title "test: CI validation" --body "Testing branch protection"
```

**Expected behavior:**
- ✅ CI workflow runs automatically
- ✅ 3 jobs execute: test-suite, code-quality, constitutional-compliance
- ✅ PR cannot merge until all checks pass
- ✅ Merge button disabled until CI green

### 4. Verify Constitutional Compliance

Check that these protections work:

**Test 1: Cannot push directly to main**
```bash
git checkout main
echo "test" >> test.txt
git add test.txt
git commit -m "test: Direct main commit"
git push  # Should fail with branch protection error
```

**Test 2: PR requires CI pass**
```bash
# Create PR with failing test
git checkout -b test/fail-ci
# (add code that breaks tests)
git push -u origin test/fail-ci
gh pr create --title "test: Failing CI"
# Try to merge → Should be blocked by failed CI
```

**Test 3: Cannot force push**
```bash
git checkout -b test/force-push
git commit --amend
git push --force  # Should fail with protection error
```

---

## CI Workflow Details

**File**: `.github/workflows/ci.yml`

**Jobs**:
1. **test-suite** (Article II - 100% Verification)
   - Runs full test suite: `python run_tests.py --run-all`
   - Timeout: 20 minutes (3x multiplier)
   - Must pass: 1,762/1,762 tests

2. **code-quality** (Article III - Quality Gates)
   - Ruff linting (fast)
   - Black formatting check
   - isort import sorting
   - mypy type checking (advisory)

3. **constitutional-compliance** (Articles I-V)
   - Check for `Dict[Any, Any]` violations
   - Verify ADR index exists
   - Verify constitution.md exists

4. **ci-summary** (Required Check)
   - Aggregates all job results
   - **This is the required status check** for branch protection
   - Must pass for PR merge

---

## Cost Optimization

### Current Usage (3 PRs/day):
- **Estimated minutes**: 1,440/month (under 2,000 free tier)
- **Cost**: $4/month (GitHub Pro only)

### If you exceed free tier:
- **Overage**: $0.008/minute
- **Example**: 2,700 min/month = $5.60 overage = $9.60 total

### Optimization strategies:
1. **Run affected tests only** on PR (full suite on merge)
2. **Cache dependencies** (already configured in workflow)
3. **Use self-hosted runner** on M4 Pro (free unlimited minutes)

---

## Troubleshooting

### "Branch protection not available"
- **Cause**: GitHub Free account
- **Fix**: Upgrade to GitHub Pro ($4/month)

### "CI workflow not running"
- **Cause**: Workflow not on main branch
- **Fix**: Merge CI workflow to main first
  ```bash
  git checkout main
  git add .github/workflows/ci.yml
  git commit -m "ci: Add constitutional compliance workflow"
  git push
  ```

### "CI checks taking too long"
- **Current**: ~4 minutes for full test suite
- **Optimization**: Run affected tests only (~30s)
- **See**: `docs/TEST_OPTIMIZATION.md` (TODO)

### "Cannot merge PR even though CI passed"
- **Cause**: Conversation threads not resolved
- **Fix**: Resolve all review comments before merge

---

## Constitutional Alignment

| Article | Enforcement Mechanism | CI Job |
|---------|----------------------|---------|
| **Article I** | Complete context (all tests run) | `test-suite` |
| **Article II** | 100% verification (tests must pass) | `test-suite` (required) |
| **Article III** | Automated enforcement (no bypass) | Branch protection + `ci-summary` |
| **Article IV** | VectorStore patterns | `test-suite` (validates patterns) |
| **Article V** | Spec-driven | `constitutional-compliance` (ADR checks) |

---

## Next Steps

1. ✅ Upgrade to GitHub Pro
2. ✅ Run `scripts/setup_branch_protection.sh`
3. ✅ Create test PR to verify setup
4. ✅ Update `CLAUDE.md` to document mandatory PR workflow
5. ✅ Add pre-commit hooks for local enforcement (optional)

---

**Status**: Ready for setup after GitHub Pro upgrade

**Last Updated**: 2025-10-14

---

## 🚀 AgencyOS Workflow: /primeA Integration

**IMPORTANT**: After `/clear`, you use `/primeA` for all development tasks!

### Standard Post-/clear Workflow

```bash
# After /clear, execute your task via /primeA
/primeA "implement rate limiting middleware"
```

### PrimeA Task Graph (Automatic Branch Protection Compliance)

When you run `/primeA "your task"`, the Planner agent automatically generates a task graph that includes:

**Phase 1: Setup** (Automatic)
1. ✅ `create_feature_branch` (Code) - Creates `feat/task-name` automatically
2. ✅ `checkout_feature_branch` (Code) - Switches to feature branch

**Phase 2: Implementation** (Your Task)
3. Spec/Code/Test tasks based on your request

**Phase 3: PR Creation** (Automatic if `--auto-pr`)
4. ✅ `commit_changes` (Code) - Commits all work
5. ✅ `push_feature_branch` (Code) - Pushes to origin
6. ✅ `create_pull_request` (Code) - Creates PR via `gh pr create`
7. ✅ CI runs automatically (~4-5 min)

### Example: Full Cycle

```bash
# 1. After /clear
/clear

# 2. New task via /primeA with auto-PR
/primeA "add JWT authentication" --auto-pr

# PrimeA executes:
#   ✅ Creates feat/jwt-auth branch
#   ✅ Generates spec
#   ✅ Writes tests
#   ✅ Implements code
#   ✅ Runs tests locally (100% pass required)
#   ✅ Commits changes
#   ✅ Pushes to feat/jwt-auth
#   ✅ Creates PR automatically
#   ✅ CI triggered (GitHub Actions)

# 3. Monitor CI
gh pr checks  # Watch status

# 4. Merge when green
gh pr merge --squash

# 5. Pull latest main
git checkout main
git pull
```

### /primeA Flags for Branch Protection

```bash
# Plan-only: Review task graph before execution
/primeA "your task" --plan-only

# Execute reviewed graph
/primeA --graph /tmp/task_graph_*.json

# Auto-create PR after completion
/primeA "your task" --auto-pr

# Two-stage: Spec approval checkpoint
/primeA "your task" --two-stage --auto-pr
```

### What PrimeA Handles Automatically

✅ **Branch Creation**: Always creates feature branch (never commits to main)
✅ **Branch Naming**: Uses semantic naming (`feat/`, `fix/`, `docs/`)  
✅ **Local Testing**: Runs tests before commit (Article II compliance)
✅ **PR Creation**: Generates comprehensive PR description
✅ **CI Compliance**: Waits for CI checks (if monitoring enabled)

### Manual Override (If Needed)

If `/primeA` is not available or you need manual control:

```bash
# 1. Create feature branch manually
git checkout -b feat/your-feature

# 2. Make changes
# ... your work ...

# 3. Commit and push
git add .
git commit -m "feat: your changes"
git push -u origin feat/your-feature

# 4. Create PR
gh pr create --title "feat: Your feature" --body "Description"
```

### Key Reminders

1. **Never push to main directly** (branch protection will block you)
2. **Always use feature branches** (PrimeA does this automatically)
3. **CI must pass** before merge (required status check)
4. **Use `/primeA --auto-pr`** for full automation

---

**Updated**: 2025-10-14 (Added /primeA workflow integration)
