---
description: Prime session from latest snapshot for quick recovery
config:
  mode: code
  auto_tokens: true
---

You are **recovering a session** from a snapshot.

## Your Task

1. **Load Latest Snapshot**
   ```bash
   # Read the most recent snapshot
   Read /Users/am/Code/Agency/.snapshots/snap-latest.md
   # OR if symlink broken, find manually:
   Glob .snapshots/snap-*.md
   Read {most_recent_snapshot}
   ```

2. **Load Core Context** (Same as `/prime_cc`)
   ```bash
   Read constitution.md
   Read CLAUDE.md
   Read agency.py
   Read docs/adr/ADR-INDEX.md
   Read shared/model_policy.py
   ```

3. **Load Snapshot-Specific Files**
   - Read "Key Files for Next Session" from snapshot
   - Prioritize files marked "MUST READ"
   - Load context files for background

4. **Check Current State**
   ```bash
   git status
   gh pr list --state open
   gh run list --branch main --limit 1
   ```

5. **Present Recovery Summary**
   ```markdown
   # 📸 Session Recovered from Snapshot

   ## Last Session Summary
   {from snapshot: current state, achievements}

   ## Open Loops
   {numbered list of unfinished work}

   ## Recommended Next Action
   {from snapshot: specific command or task}

   ## Quick Context
   - Main Branch: {status from git/CI}
   - Open PRs: {count and key ones}
   - CI Status: {pass/fail rate}
   - Priority: {from snapshot recommendation}

   ## Loaded Files
   - Core: constitution.md, CLAUDE.md, agency.py, ADR-INDEX.md, model_policy.py
   - Snapshot: {files from "Key Files" section}
   - Status: git status, PR list, CI status

   Ready to continue. First action: {exact command from snapshot}
   ```

## Execution Steps

### Step 1: Load Snapshot
```
Read .snapshots/snap-latest.md
```

### Step 2: Load Core (in parallel)
```
Read constitution.md
Read CLAUDE.md
Read agency.py
Read docs/adr/ADR-INDEX.md
Read shared/model_policy.py
```

### Step 3: Load Snapshot-Specific Files
Parse "Key Files for Next Session" section, read MUST READ files first, then context files.

### Step 4: Check Status (in parallel)
```bash
git status
gh pr list --state open --limit 5
gh run list --branch main --limit 1 --json status,conclusion
```

### Step 5: Present Summary
- Extract "Current State" from snapshot
- Extract "Open Loops" from snapshot
- Extract "Recommended Next Action" from snapshot
- Combine with current git/CI status
- Present as formatted summary

### Step 6: Execute First Action
If snapshot has "Recommended Next Action" with specific command:
- Execute it immediately after presenting summary
- OR ask user: "Ready to: {action}. Proceed? (y/n)"

## Smart Loading

**If snapshot recommends Trinity work**:
```
Read trinity_protocol/README.md
Read TRINITY_ADE_BACKLOG.md
Read trinity_protocol/core/models/*.py
```

**If snapshot recommends test fixes**:
```
Read {failing test files from snapshot}
Read {implementation files from snapshot}
```

**If snapshot recommends quick wins**:
```
Read {files listed in Low-Hanging Fruit section}
```

## Optimization

1. **Parallel Reads**: Batch file reads when possible
2. **Selective Loading**: Only load files for recommended path
3. **Token Budget**: ~5k tokens for priming (core + snapshot + specific files)
4. **Fresh Status**: Always check current git/CI, don't trust snapshot timestamps

## Success Criteria

✅ Snapshot loaded and parsed
✅ Core context loaded (5 files)
✅ Snapshot-specific files loaded (3-5 files)
✅ Current status checked (git, PRs, CI)
✅ Recovery summary presented
✅ First action identified and ready

**Goal**: Full context restoration in <60 seconds, ready to continue work seamlessly.
