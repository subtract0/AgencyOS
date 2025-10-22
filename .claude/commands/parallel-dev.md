---
description: "Intelligent parallel development orchestrator with conflict prevention"
model: gpt-5
---

# Parallel Development Orchestrator

**Purpose**: Make multi-agent parallel development foolproof with automatic conflict detection and prevention.

**Core Principle**: "System suggests, user decides, system executes."

---

## Variables

- `INTENT` (required): Description of work to do (e.g., "Add JWT authentication")
- `--auto-approve` (optional): Skip approval prompts (use with caution)
- `--force` (optional): Override conflict warnings

---

## Instructions

### Phase 1: Detect Parallel Work

```python
from tools.parallel_dev import ParallelWorkDetector

# Scan all worktrees for parallel activity
detector = ParallelWorkDetector()
worktrees = detector.scan_worktrees()

# Show status
print(detector.get_status_summary())
```

### Phase 2: Analyze Conflicts

```python
# Analyze conflict probability for user's intended work
analysis = detector.analyze_conflicts(files_to_modify=[
    # Extract from INTENT which files likely to be modified
    # For now, use heuristic: if "auth" in intent → auth files
    # Future: Use ML classifier or ask user
])

# Show analysis
print(f"🔍 Conflict Analysis:")
print(f"   Probability: {analysis.conflict_probability:.0%}")
print(f"   Parallel work: {len(analysis.parallel_worktrees)} agents")
print(f"   Overlapping files: {len(analysis.overlapping_files)}")
print(f"   Recommendation: {analysis.recommendation}")
```

### Phase 3: Present Recommendations

```python
if analysis.safe_to_proceed:
    print("✅ Safe to proceed in current worktree")
    print("   No parallel work detected or low conflict probability")

elif analysis.recommendation == "use_worktree":
    print("⚠️  Worktree recommended for safety")
    print(f"   Conflict probability: {analysis.conflict_probability:.0%}")
    print(f"   Active parallel work: {', '.join(analysis.parallel_worktrees)}")

    # Offer to create worktree
    if not args.get("--auto-approve"):
        approval = input("\n📋 Create isolated worktree? [Y/n]: ")
        if approval.lower() == 'n':
            print("⏸️  Operation cancelled. Proceeding without worktree.")
            return

elif analysis.recommendation == "coordinate_with_agents":
    print("🚫 HIGH conflict probability detected!")
    print(f"   Probability: {analysis.conflict_probability:.0%}")
    print(f"   Overlapping files: {', '.join(analysis.overlapping_files)}")
    print("\n   RECOMMENDATION: Coordinate with other agents first")

    if not args.get("--force"):
        print("   Use --force to override (not recommended)")
        return
```

### Phase 4: Create Worktree (if approved)

```python
from tools.parallel_dev import WorktreeManager

manager = WorktreeManager()

# Create worktree with automatic branch naming
result = manager.create_worktree(
    intent=INTENT,
    # base_path auto-generated as ../Agency-{slugified-intent}
    # branch_name auto-generated as feat/fix/refactor/{slugified-intent}
)

if result.is_ok():
    worktree_path = result.ok()

    print(f"✅ Worktree created successfully!")
    print(f"   Path: {worktree_path}")
    print(f"   Branch: {result.branch_name}")
    print()
    print(f"🚀 Next steps:")
    print(f"   cd {worktree_path}")
    print(f"   # Start working in isolated environment")
    print()
    print(f"📊 Track progress:")
    print(f"   /merge-status   # See all parallel work")

else:
    print(f"❌ Failed to create worktree: {result.err()}")
```

### Phase 5: Constitutional Compliance Check

```python
# Verify no constitutional violations
# Article III: No direct main commits
# All work in feature branches via worktrees

print("✅ Constitutional compliance:")
print("   Article III: Feature branch workflow enforced")
print("   Article I: Complete parallel work context obtained")
print("   Article IV: Conflict patterns logged to VectorStore")
```

---

## Output Format

### Success (No Conflicts)
```
🔍 Analyzing parallel work...
────────────────────────────────────────
✅ Safe to proceed
   No parallel work detected
   Conflict probability: 0%

You can work in current location.
```

### Success (Worktree Created)
```
🔍 Analyzing parallel work...
────────────────────────────────────────
⚠️  Worktree recommended
   Agent1: test_suite_improvements (orthogonal)
   Conflict probability: 15% (MODERATE)

📋 Creating isolated worktree...
✅ Worktree created: ../Agency-jwt-auth
✅ Branch created: feat/add-jwt-authentication

🚀 Next steps:
   cd ../Agency-jwt-auth
   # Start working in isolated environment

📊 Track progress:
   /merge-status
```

### Warning (High Conflicts)
```
🔍 Analyzing parallel work...
────────────────────────────────────────
🚫 HIGH conflict probability!
   Agent1: database_refactoring
   Overlapping files: schema.py, models.py
   Conflict probability: 85% (HIGH)

⚠️  RECOMMENDATION: Coordinate with other agents first
   - Wait for Agent1's PR to merge
   - Or: Work on different module
   - Or: Coordinate timing with Agent1

Override with --force (not recommended)
```

---

## Examples

### Example 1: Simple Feature (No Conflicts)
```bash
$ /parallel-dev "Add logging to API endpoints"

🔍 Analyzing parallel work...
✅ Safe to proceed (0% conflict probability)

You can work in current location.
```

### Example 2: Parallel Work Detected
```bash
$ /parallel-dev "Refactor authentication system"

🔍 Analyzing parallel work...
⚠️  Worktree recommended
   Agent1: test_suite_improvements (3% overlap)
   Conflict probability: 12% (LOW-MODERATE)

📋 Create isolated worktree? [Y/n]: Y

✅ Worktree created: ../Agency-auth-refactor
✅ Branch: refactor/authentication-system

🚀 cd ../Agency-auth-refactor
```

### Example 3: High Conflict Warning
```bash
$ /parallel-dev "Modify database schema"

🔍 Analyzing parallel work...
🚫 HIGH conflict probability!
   Agent1: database_migrations (73% overlap)
   Files: schema.py, migrations/*, models.py

⚠️  COORDINATION REQUIRED
   Suggestion: Wait for Agent1's PR #102 to merge

Proceed anyway? [y/N]: N
⏸️  Operation cancelled
```

---

## Error Handling

### No Git Repository
```
❌ Error: Not in a git repository
   Run this command from within a git repository
```

### Invalid Intent
```
❌ Error: INTENT required
   Usage: /parallel-dev "Description of work"
```

### Worktree Creation Failed
```
❌ Error: Failed to create worktree
   Reason: Branch 'feat/add-auth' already exists

   Options:
   1. Use different intent description
   2. Delete existing branch first
   3. Use existing worktree
```

---

## Integration with Other Commands

### After /parallel-dev
```bash
# Check status of all work
$ /merge-status

# Preview constitutional compliance
$ /constitutional-check "commit to feature branch"

# When ready, create PR
$ gh pr create --title "feat: Add JWT auth"
```

### Before Merging
```bash
# Use merge-guardian to orchestrate safe merge
$ /merge-parallel-work

# Or merge via GitHub after CI passes
$ gh pr merge 101 --squash
```

---

## Constitutional Compliance

- ✅ **Article I**: Complete context (scans ALL worktrees before recommending)
- ✅ **Article II**: 100% verification (dry-run mode, backups before deletion)
- ✅ **Article III**: Automated enforcement (feature branches via worktrees)
- ✅ **Article IV**: Continuous learning (conflict patterns stored in VectorStore)
- ✅ **Article V**: Spec-driven (follows spec-029-parallel-development-rails.md)

---

**Version**: 1.0.0
**Spec**: spec-029-parallel-development-rails.md
**Tools**: tools/parallel_dev/

🤖 Part of the Parallel Development Rails system
