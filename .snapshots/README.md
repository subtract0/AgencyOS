# Session Snapshots

**Purpose**: Token-efficient recovery documents for resuming work after `/clear`.

## How It Works

### 1. Save Snapshot
```
/write_snap
```
Creates: `.snapshots/snap-{timestamp}.md` with:
- Current state & metrics
- Open loops (unfinished work)
- Broken windows (bugs to fix)
- Low-hanging fruit (quick wins)
- Next recommended actions
- Key files to load
- Critical insights

### 2. Recover Session
```
/prime_snap
```
Loads:
- Latest snapshot (`snap-latest.md`)
- Core context (constitution, CLAUDE.md, agency.py, ADRs)
- Snapshot-specific files (from "Key Files" section)
- Current status (git, PRs, CI)

Presents:
- Recovery summary
- Open loops
- Recommended next action
- First command to execute

## Snapshot Structure

```markdown
# 📸 Snapshot: {timestamp}

## 🎯 Current State
What just happened, metrics, status

## 🔄 Open Loops
Unfinished business

## 🪟 Broken Windows
Bugs by priority

## 🍎 Low-Hanging Fruit
Quick wins (<30 min each)

## 🔻 Reduce Complexity
Simplification opportunities

## 🎯 Where to Go Next
Options A/B/C + recommendation

## 📂 Key Files for Next Session
Organized by task

## 💡 Critical Insights
Lessons, patterns, gotchas

## 🚀 Recommended Next Action
Specific first command
```

## Token Budget

- **Snapshot**: ~2k tokens (optimized for quick loading)
- **Prime**: ~5k tokens total (core + snapshot + specific files)
- **Recovery**: <60 seconds to full context

## File Naming

```
snap-{YYYY-MM-DD-HHMM}.md    # Timestamped snapshot
snap-latest.md                # Symlink to most recent
```

## Best Practices

### When to `/write_snap`
- ✅ Before `/clear` (save current state)
- ✅ After major milestone (preserve achievements)
- ✅ Before switching epics (capture context)
- ✅ End of session (document progress)

### When to `/prime_snap`
- ✅ After `/clear` (restore context)
- ✅ Start of new session (quick recovery)
- ✅ Switching between tasks (reload context)

### Snapshot Content
- ✅ **Actionable**: Every item has file path + next step
- ✅ **Prioritized**: Critical → Important → Nice-to-have
- ✅ **Time-estimated**: Every task has effort estimate
- ✅ **Specific**: Exact commands, not vague suggestions
- ❌ **Not history**: Focus on future, not past details

## Example Workflow

```bash
# End of session
/write_snap
# ✅ Snapshot saved: .snapshots/snap-2025-10-03-1745.md

# Start of next session (after /clear)
/prime_snap
# Loads snapshot, core files, specific context
# Presents recovery summary
# Executes first recommended action
```

## Directory Structure

```
.snapshots/
├── README.md                 # This file
├── snap-latest.md           # Symlink to most recent
├── snap-2025-10-03-1745.md  # Session snapshot
├── snap-2025-10-04-0930.md  # Next session
└── snap-2025-10-04-1500.md  # And so on...
```

## Current Snapshot

**Latest**: `snap-2025-10-03-1745.md` (2025-10-03 17:45 UTC)

**Summary**:
- Status: 99.6% CI green (3245 passing, 11 failing)
- Achievement: Restored from 0% via PR #13 + #15
- Open Loops: 11 test failures (impl bugs), Trinity Trust Imperative ready
- Recommendation: Start Trinity Trust Imperative epic
- First Action: `Read TRINITY_ADE_BACKLOG.md`

---

**Version**: 1.0
**Created**: 2025-10-03
**Commands**: `/write_snap`, `/prime_snap`
