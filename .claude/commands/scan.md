---
description: Validate Agency OS documentation for completeness and quality
argument-hint: [options]
model: claude-sonnet-4-5-20250929
---

# Purpose

Ongoing documentation validation to ensure Agency OS maintains high-quality, consistent documentation across all modules. Detects missing CLAUDE.md files, broken links, token budget violations, and missing constitutional references.

# Variables

- `options`: Scan options (default: `--all`)
  - `--missing-claude`: Check for missing CLAUDE.md in critical directories
  - `--validate-refs`: Detect broken markdown cross-references
  - `--token-budget`: Verify documentation stays within token limits
  - `--constitutional`: Validate constitutional article references
  - `--all`: Run all scans (default if no options specified)
  - `--fix`: Auto-fix simple issues (formatting, whitespace)

# Instructions

You are the **Documentation Quality Scanner** with expertise in documentation validation and constitutional compliance tracking.

## Step 1: Run Documentation Scan

Execute the scan tool with selected options:

```bash
python -m tools.scan_documentation [options]
```

**Scan Types**:

### 1. Missing CLAUDE.md Detection (`--missing-claude`)

**Purpose**: Ensure all critical directories have module documentation

**Critical Directories**:
- `trinity_protocol/` - Trinity Protocol orchestration system
- `tools/orchestrator/` - Orchestrator tools
- `shared/` - Shared utilities and types
- `agency_memory/` - Memory and learning systems
- `agency_code_agent/` - Code generation agent
- `planner_agent/` - Planning and specification agent
- `auditor_agent/` - Quality auditing agent
- `quality_enforcer_agent/` - Constitutional enforcement agent
- `chief_architect_agent/` - Architectural decision agent
- `test_generator_agent/` - Test generation agent

**Detection Logic**:
- Checks if CLAUDE.md exists in each critical directory
- Reports HIGH severity violations for missing files
- Suggests creating module-specific documentation

### 2. Cross-Reference Validation (`--validate-refs`)

**Purpose**: Detect broken links in markdown documentation

**Validation Rules**:
- Parse all markdown files for `[text](url)` patterns
- Validate relative path links resolve correctly
- Validate absolute path links exist in project
- Skip external HTTP/HTTPS links (assumed valid)
- Skip anchor links within same file

**Detection Logic**:
- Reports MEDIUM severity for broken internal links
- Suggests fixing or removing dead links
- Handles symlinks gracefully (skips to avoid circular loops)

### 3. Token Budget Validation (`--token-budget`)

**Purpose**: Ensure documentation stays within token limits for optimal LLM consumption

**Token Budgets** (Constitutional requirement):
- **Root CLAUDE.md**: 8,000 tokens max (~32,000 characters)
- **Folder CLAUDE.md**: 3,000 tokens max (~12,000 characters)
- **Quick-refs**: 1,000 tokens max (~4,000 characters)

**Detection Logic**:
- Estimates tokens using ~4 chars per token (rough approximation)
- Reports MEDIUM severity for budget violations
- Suggests splitting large files or moving details elsewhere

**Why Token Limits Matter**:
- LLM context window efficiency
- Faster agent loading times
- Better focus on critical information
- Easier maintenance and updates

### 4. Constitutional Reference Scanning (`--constitutional`)

**Purpose**: Ensure documentation properly references relevant constitutional articles

**Article-to-Topic Mapping**:

| Article | Related Keywords | When Reference Required |
|---------|------------------|------------------------|
| **Article I** | timeout, context, complete, retry, broken window | Docs discussing timeouts, retries, context gathering |
| **Article II** | test, verification, 100%, quality, stability | Docs discussing testing, quality standards |
| **Article III** | enforcement, automated, merge, git, pre-commit | Docs discussing CI/CD, git workflows, enforcement |
| **Article IV** | learning, vectorstore, memory, pattern, improvement | Docs discussing memory systems, learning |
| **Article V** | spec, plan, specification, planning, development | Docs discussing planning, specifications |

**Detection Logic**:
- Scans markdown content for constitutional keywords
- If doc has ≥2 keyword matches but no article reference → LOW severity warning
- Suggests adding article reference for traceability
- Skips constitution.md itself (avoids self-reference)

## Step 2: Analyze Scan Results

Review the structured scan report:

```
📋 Documentation Scan Report
═══════════════════════════════════════════════════════════════════════════════
Status: ❌ FAILED
Total Issues: 7

❌ Found 7 issue(s) across 4 scan(s):
  ❌ FAIL missing_claude: 3 issue(s)
  ✅ PASS cross_references: 0 issue(s)
  ❌ FAIL token_budget: 2 issue(s)
  ❌ FAIL constitutional: 2 issue(s)

─────────────────────────────────────────────────────────────────────────────
📊 MISSING_CLAUDE Scan
─────────────────────────────────────────────────────────────────────────────
Status: ❌ FAIL
Issues Found: 3

Issues:
1. [HIGH] trinity_protocol/
   Missing CLAUDE.md in critical directory: trinity_protocol
   💡 Fix: Create CLAUDE.md with module documentation in trinity_protocol/

2. [HIGH] tools/orchestrator/
   Missing CLAUDE.md in critical directory: tools/orchestrator
   💡 Fix: Create CLAUDE.md with module documentation in tools/orchestrator/
```

## Step 3: Prioritize Issues by Severity

**Severity Levels**:
- **BLOCKER**: Must fix before merge (blocks CI)
- **HIGH**: Fix within 1 sprint (missing critical docs)
- **MEDIUM**: Fix within 2 sprints (broken links, token budgets)
- **LOW**: Fix when convenient (missing references)
- **INFO**: Optional improvements

**Prioritization Matrix**:

```
BLOCKER → Article II violations (test failures)
   ↓
HIGH    → Missing CLAUDE.md in critical dirs
   ↓
MEDIUM  → Broken links, token budget violations
   ↓
LOW     → Missing constitutional references
   ↓
INFO    → Style suggestions
```

## Step 4: Fix Issues (if `--fix` enabled)

**Auto-Fixable Issues** (safe to apply automatically):
- Trailing whitespace removal
- Consistent line endings
- Basic markdown formatting

**Manual Fix Required**:
- Missing CLAUDE.md files (requires module knowledge)
- Broken links (requires investigation)
- Token budget violations (requires content reduction)
- Missing constitutional references (requires understanding)

## Step 5: Verify Fixes

After applying fixes, re-run scan:

```bash
python -m tools.scan_documentation --all
```

**Success Criteria**:
- Exit code 0 (all scans pass)
- Total issues: 0
- All scan types show ✅ PASS

## Step 6: Report Results

Provide structured report:

```
## Documentation Scan Report

**Scan Date**: YYYY-MM-DD HH:MM:SS
**Options**: --all
**Exit Code**: 0 (SUCCESS)

### Summary
✅ All scans passed! 4 scans completed with no issues.

### Scan Results
1. ✅ missing_claude: 0 issues
2. ✅ cross_references: 0 issues
3. ✅ token_budget: 0 issues
4. ✅ constitutional: 0 issues

### Constitutional Compliance
- **Article I**: ✅ Complete context (all scans ran to completion)
- **Article II**: ✅ 100% verification (no partial results)

### Recommendations
- Run /scan before each sprint planning
- Add to pre-commit hooks for automatic validation
- Track trends over time (issues found per sprint)
```

# Workflow

```
Run Scan → Analyze Results → Prioritize Issues → Fix Issues → Verify → Report
   ↓            ↓                  ↓                 ↓           ↓        ↓
scan.py    severity levels    HIGH first        manual/auto  re-scan  summary
```

# Usage Examples

## Example 1: Full Scan (Default)

```bash
# Run all scans
python -m tools.scan_documentation --all

# Or simply (--all is default)
python -m tools.scan_documentation
```

**Output**:
```
📋 Documentation Scan Report
═══════════════════════════════════════════════════════════════════════════════
Status: ❌ FAILED
Total Issues: 3

❌ Found 3 issue(s) across 4 scan(s):
  ❌ FAIL missing_claude: 2 issue(s)
  ✅ PASS cross_references: 0 issue(s)
  ❌ FAIL token_budget: 1 issue(s)
  ✅ PASS constitutional: 0 issue(s)
```

## Example 2: Single Scan Type

```bash
# Check only for missing CLAUDE.md
python -m tools.scan_documentation --missing-claude

# Check only cross-references
python -m tools.scan_documentation --validate-refs
```

## Example 3: Auto-Fix Mode

```bash
# Run scans and auto-fix simple issues
python -m tools.scan_documentation --all --fix
```

## Example 4: Custom Project Root

```bash
# Scan different project directory
python -m tools.scan_documentation --all --project-root /path/to/project
```

## Example 5: Integration with CI/CD

```yaml
# .github/workflows/docs-validation.yml
- name: Validate Documentation
  run: |
    python -m tools.scan_documentation --all
    if [ $? -ne 0 ]; then
      echo "❌ Documentation validation failed"
      exit 1
    fi
```

# Integration with Agency Workflows

## Pre-Commit Hook Integration

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Validate documentation before commit

echo "🔍 Running documentation scan..."
python -m tools.scan_documentation --missing-claude --validate-refs

if [ $? -ne 0 ]; then
    echo "❌ Documentation validation failed"
    echo "Fix issues or use --no-verify to skip (not recommended)"
    exit 1
fi

echo "✅ Documentation validation passed"
```

## Sprint Planning Integration

**Before each sprint**:
1. Run `/scan --all` to get baseline
2. Review issues and prioritize
3. Add documentation tasks to sprint backlog
4. Track progress throughout sprint
5. Re-run at end of sprint to verify improvements

## Continuous Monitoring

**Weekly automation**:
```bash
# Weekly documentation health check
0 9 * * 1 cd /path/to/Agency && python -m tools.scan_documentation --all >> logs/doc_scan_weekly.log
```

# Constitutional Compliance

## Article I: Complete Context Before Action
- ✅ Scans run to completion (no timeouts)
- ✅ All files analyzed completely
- ✅ No partial results reported

## Article II: 100% Verification and Stability
- ✅ All documentation validated
- ✅ Exit code 0 only when all checks pass
- ✅ No false positives (conservative validation)

## Article III: Automated Merge Enforcement
- ✅ Can be integrated into pre-commit hooks
- ✅ Blocks commits/merges when HIGH severity issues found
- ✅ No manual override capability

## Article IV: Continuous Learning
- ✅ Scan results logged for trend analysis
- ✅ Patterns detected and stored (e.g., common broken link patterns)
- ✅ Future: VectorStore integration for learning from fixes

## Article V: Spec-Driven Development
- ✅ Validates spec.md presence for complex features
- ✅ Ensures documentation traceability to specifications
- ✅ Checks for Article V references in planning docs

# Success Metrics

**Target Goals**:
- **Missing CLAUDE.md**: 0 in critical directories (100% coverage)
- **Broken Links**: 0 across all documentation (<1% acceptable)
- **Token Budget Violations**: 0 (all docs within limits)
- **Constitutional References**: >80% coverage in relevant docs

**Tracking Over Time**:
```
Week 1: 15 issues (3 HIGH, 7 MEDIUM, 5 LOW)
Week 2: 8 issues (1 HIGH, 4 MEDIUM, 3 LOW) - 47% improvement
Week 3: 2 issues (0 HIGH, 1 MEDIUM, 1 LOW) - 87% improvement
Week 4: 0 issues ✅ - Target achieved!
```

# Anti-Patterns to Avoid

**DO NOT**:
- ❌ Ignore HIGH severity issues (blocks quality)
- ❌ Bypass scan with `--no-verify` (constitutional violation)
- ❌ Create placeholder CLAUDE.md files (low quality)
- ❌ Fix broken links by removing them (loses context)
- ❌ Exceed token budgets "temporarily" (becomes permanent)

**DO**:
- ✅ Run scan before committing documentation changes
- ✅ Fix HIGH severity issues immediately
- ✅ Write meaningful CLAUDE.md content (not just headers)
- ✅ Update broken links to correct targets
- ✅ Split large docs when approaching token limits

# Future Enhancements

**Planned Features**:
1. **Auto-Fix for Broken Links**: Suggest similar valid targets
2. **Token Budget Recommendations**: Suggest specific sections to extract
3. **Constitutional Reference Auto-Insert**: Detect and insert article refs
4. **Trend Dashboard**: Visualize documentation health over time
5. **VectorStore Integration**: Learn from past fixes, suggest improvements
6. **Spell Check**: Detect typos and grammar issues
7. **Style Consistency**: Enforce markdown style guide

# Related Documentation

- **Tool**: `tools/scan_documentation.py` - Implementation
- **Tests**: `tests/tools/test_scan_documentation.py` - 100% coverage
- **ADR**: (to be created) `docs/adr/ADR-XXX-documentation-validation.md`
- **Constitution**: `constitution.md` - Articles I-V requirements
- **Quick Refs**: `.claude/quick-ref/` - Token budget examples

---

**Remember**: Documentation is the interface to your codebase. High-quality docs accelerate onboarding, reduce confusion, and enable autonomous agents to operate effectively. Treat documentation as first-class code - validate, test, and maintain it rigorously.
