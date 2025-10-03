---
description: Write a snapshot of current state for future recovery
config:
  mode: code
  auto_tokens: true
---

You are creating a **session snapshot** - a token-efficient recovery document.

## Your Task

Write a comprehensive snapshot to `.snapshots/snap-{timestamp}.md` containing:

### 1. Current State (What Just Happened)
- Last 1-3 sessions summary
- What was accomplished
- Current metrics (CI %, test count, health score)
- Main branch status

### 2. Open Loops (Unfinished Business)
- Active work not yet complete
- Partial implementations
- Decisions pending user input
- PRs waiting for review/merge

### 3. Broken Windows (Still to Fix)
- Critical bugs blocking work
- Minor bugs (prioritized)
- Known tech debt
- Constitutional violations

### 4. Low-Hanging Fruit (10x Value, Low Effort)
- Quick wins (< 30 min each)
- High impact, low complexity
- Obvious improvements
- Enable/configure existing features

### 5. Reduce Complexity (Simplify Without Losing Value)
- Redundant code to remove
- Over-engineered solutions to simplify
- Bloat to eliminate
- Inefficiencies to fix
- Churn to reduce

### 6. Where to Go Next
- Option A: Most important work
- Option B: Alternative path
- Option C: Quick wins
- Recommendation with rationale

### 7. Key Files for Next Session
- Files to read first
- Context files for background
- Implementation files to modify
- Test files to update

### 8. Critical Insights
- Patterns learned
- Gotchas discovered
- Commands that work
- Anti-patterns to avoid

## Output Format

```markdown
# 📸 Snapshot: {timestamp}

## 🎯 Current State: {one-line summary}
{metrics, status, what just happened}

## 🔄 Open Loops to Close
{unfinished work, numbered list}

## 🪟 Broken Windows Still Open
{bugs by priority, with file locations}

## 🍎 Low-Hanging Fruit
{quick wins with time estimates}

## 🔻 Reduce Complexity/Bloat
{simplification opportunities}

## 🎯 Where to Go Next
{options A/B/C with recommendation}

## 📂 Key Files for Next Session
{organized by task}

## 💡 Critical Insights
{lessons, patterns, commands}

## 🏆 Session Achievements
{what was delivered}

## 🚀 Recommended Next Action
{specific first command or file to read}
```

## Optimization Rules

1. **Token Efficiency**: Use bullets, tables, code blocks
2. **Actionable**: Every item has file path + action
3. **Prioritized**: Critical → Important → Nice-to-have
4. **Time Estimates**: Every task has effort estimate
5. **First Command**: End with exact command to run after `/prime_snap`

## Execution

1. Analyze current git status, recent commits, CI status
2. Review open PRs, issues, failing tests
3. Identify incomplete work from session
4. Write snapshot to `.snapshots/snap-{YYYY-MM-DD-HHMM}.md`
5. Create symlink: `.snapshots/snap-latest.md` → current snapshot
6. Confirm: "✅ Snapshot saved: `.snapshots/snap-{timestamp}.md`"

**Goal**: Enable seamless recovery after `/clear` with full context in ~2k tokens.
