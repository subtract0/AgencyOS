# MacBook Air (M4) → MacBook Pro (M4 Pro) Sync Guide

**Generated**: 2025-10-22 @ 20:00 UTC

---

## Current Machine: MacBook Air (M4)

**Specs**:
- Model: MacBook Air (M4, 16GB RAM)
- Location: `/Users/am/Code/Agency`

**Repository State**:
- **HEAD**: `5753b3f` (main)
- **Latest commit**: feat(tests): Leap 9 - Test Performance Optimization (86.4% faster) (#103)
- **Uncommitted changes**: 1 file (missions/autonomous-parallel-dev-phase-2.json)

**Worktrees**:
```
/Users/am/Code/Agency                    (bare)
/Users/am/Code/Agency-distributed-locks  9333c5a [feat/distributed-locks-edge-cases] ← CAN DELETE
/Users/am/Code/Agency-hooks-analysis     5b0496b [feat/constitutional-hooks-phase-1] ← CAN DELETE
/Users/am/Code/Agency-main               5753b3f [main] ← ACTIVE
```

**Mission Files**: 16 total (including new autonomous-parallel-dev-phase-2.json)

---

## Target Machine: MacBook Pro (M4 Pro)

**Specs**:
- Model: MacBook Pro (M4 Pro, 14-core CPU, 20-core GPU, 48GB RAM)
- Expected Location: `/Users/am/Code/Agency` (TBD)

**State**: Unknown - needs verification

---

## Sync Strategy

### Phase 1: Verify M4 Pro State (ON M4 PRO)

Run these commands on the M4 Pro to understand its state:

```bash
# 1. Check if repository exists
cd ~/Code/Agency
pwd
ls -la

# 2. Check git status
git status
git log --oneline -5

# 3. Check worktrees
git worktree list

# 4. Check for uncommitted changes
git status --short

# 5. Check remote
git remote -v

# 6. Compare with GitHub main
git fetch origin
git log --oneline main..origin/main  # Behind commits
git log --oneline origin/main..main  # Ahead commits
```

### Phase 2: Decision Tree

**Scenario A: M4 Pro is BEHIND MBA/GitHub**
```bash
# On M4 Pro
cd ~/Code/Agency-main  # or appropriate worktree
git pull origin main
```

**Scenario B: M4 Pro has UNCOMMITTED work**
```bash
# On M4 Pro - stash or commit first
git stash push -m "WIP: Before MBA sync"
git pull origin main
git stash pop  # Review conflicts if any
```

**Scenario C: M4 Pro has UNPUSHED commits**
```bash
# On M4 Pro - check what's unique
git log origin/main..HEAD

# Option 1: Push to new branch
git checkout -b feat/m4pro-work
git push -u origin feat/m4pro-work

# Option 2: Cherry-pick to MBA
# (Run on MBA after M4 Pro pushes)
git fetch origin
git cherry-pick <commit-hash>
```

**Scenario D: M4 Pro is AHEAD (has newer work)**
```bash
# This is the current session's work from M4 Pro
# Push it to GitHub first (on M4 Pro)
git push origin main  # or create feature branch

# Then pull on MBA
git pull origin main
```

### Phase 3: Commit MBA Changes First

**Before syncing, commit the MBA's new mission file**:

```bash
# On MBA (this machine)
cd /Users/am/Code/Agency-main

# Add the new mission file
git add missions/autonomous-parallel-dev-phase-2.json

# Commit
git commit -m "feat: Add Autonomous Parallel Dev Phase 2 mission spec

- Complete task graph with 12 tasks
- Trinity pattern (WATCHER → FIXER → LEARNER)
- BLOCKED until main is green (Article II)
- Ready for /primeA execution

Mission ID: autonomous-parallel-dev-phase-2
Estimated: 5.5 days (3 days with 2 agents)
Constitutional: Articles I-V compliant"

# Push to GitHub
git push origin main
```

### Phase 4: Sync M4 Pro

**After MBA pushes, on M4 Pro**:

```bash
cd ~/Code/Agency-main  # or appropriate worktree
git pull origin main

# Verify sync
git log --oneline -5
# Should show: missions/autonomous-parallel-dev-phase-2.json commit
```

### Phase 5: Clean Up Obsolete Worktrees

**On MBA** (after confirming M4 Pro is synced):

```bash
# Remove obsolete worktrees
git worktree remove /Users/am/Code/Agency-distributed-locks
git worktree remove /Users/am/Code/Agency-hooks-analysis
git worktree prune

# Verify
git worktree list
# Should show only: Agency (bare) and Agency-main
```

**On M4 Pro** (match MBA state):

```bash
git worktree list
# Remove any obsolete worktrees if needed
```

---

## Conflict Resolution

### If M4 Pro has conflicting changes:

1. **Identify conflicts**:
   ```bash
   git fetch origin
   git diff origin/main
   ```

2. **Merge strategy**:
   ```bash
   # Option A: Favor GitHub/MBA changes
   git pull origin main --strategy-option theirs

   # Option B: Favor M4 Pro changes
   git pull origin main --strategy-option ours

   # Option C: Manual merge
   git pull origin main
   # Resolve conflicts manually
   git add .
   git commit
   ```

3. **Run tests** (Article II):
   ```bash
   python run_tests.py --run-all
   ```

---

## Verification Checklist

After sync, verify both machines match:

### On Both Machines:

- [ ] Same HEAD commit (`git log --oneline -1`)
- [ ] Same worktree count (`git worktree list`)
- [ ] No uncommitted changes (`git status --short`)
- [ ] Same remote (`git remote -v`)
- [ ] Tests pass (`python run_tests.py --run-all`)

### MBA-Specific:
- [ ] Mission file committed and pushed
- [ ] Obsolete worktrees removed

### M4 Pro-Specific:
- [ ] Pulled latest from GitHub
- [ ] Mission file present (`ls missions/autonomous-parallel-dev-phase-2.json`)

---

## Quick Commands Summary

### On MBA (Now):
```bash
cd /Users/am/Code/Agency-main
git add missions/autonomous-parallel-dev-phase-2.json
git commit -m "feat: Add Autonomous Parallel Dev Phase 2 mission spec"
git push origin main
```

### On M4 Pro (Next):
```bash
cd ~/Code/Agency-main  # or wherever your main worktree is
git fetch origin
git log origin/main..HEAD  # Check if ahead
git log main..origin/main  # Check if behind
git pull origin main  # If behind, pull latest
```

### Clean Up (Both):
```bash
git worktree remove <path>  # Remove obsolete worktrees
git worktree prune
```

---

## Notes

- **Bare repo pattern**: Both machines use bare repo at `/Users/am/Code/Agency`
- **Main worktree**: Should be at `Agency-main` on both
- **Mission file**: New autonomous-parallel-dev-phase-2.json needs to be on both
- **Test status**: MBA shows Leap 3 Pydantic errors (needs fixing before Phase 2)

---

## Next Steps After Sync

1. **Fix test failures** on whichever machine you're using (Article II)
2. **Unblock** autonomous-parallel-dev-phase-2 mission
3. **Execute** via `/primeA missions/autonomous-parallel-dev-phase-2.json`

---

**Status**: ⏳ Awaiting M4 Pro state verification
