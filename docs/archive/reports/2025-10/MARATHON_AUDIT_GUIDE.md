# 🏃 Marathon Test Audit Guide - Long-Running Analysis

## What Is This?

A **long-running, READ-ONLY audit** that analyzes ALL 5,889+ tests individually using your M4 Pro + Qwen3-Coder-30b locally. NO code changes - only creates comprehensive reports and healing roadmaps.

**Perfect for:**
- Understanding test quality across entire codebase
- Identifying NECESSARY pattern gaps (9 categories)
- Creating prioritized healing roadmap for autonomous fixes
- Running overnight/weekend while you sleep

---

## Quick Start (For Beginners)

### Option 1: Quick Test (1 hour, 500 tests)

```bash
# Test the system first (1 hour, 500 tests)
python scripts/marathon_test_audit.py --depth quick --max-tests 500
```

**What happens:**
- ✅ Analyzes 500 tests (not all 5,889)
- ✅ Takes ~1 hour
- ✅ Cost: $0 (100% local)
- ✅ Creates 3 reports in `audit_reports/`

**Use this to:**
- Verify local model works
- See sample output
- Decide if you want to run full audit

---

### Option 2: Standard Mode (8 hours, ALL tests)

```bash
# Run overnight (8 hours, all tests)
python scripts/marathon_test_audit.py --depth standard
```

**What happens:**
- ✅ Analyzes ALL 5,889 tests
- ✅ Takes ~8 hours
- ✅ Cost: $0 (100% local)
- ✅ Creates comprehensive reports

**Use this for:**
- Complete test quality assessment
- NECESSARY pattern gap analysis
- Healing roadmap generation

---

### Option 3: Deep Mode (48 hours, ALL tests + suggestions)

```bash
# Run over weekend (48 hours, deep analysis)
python scripts/marathon_test_audit.py --depth deep --suggestions
```

**What happens:**
- ✅ Analyzes ALL 5,889 tests
- ✅ Generates healing suggestions per test
- ✅ Takes ~48 hours
- ✅ Cost: $0 (100% local)
- ✅ Creates actionable healing plan

**Use this for:**
- Maximum detail
- Ready-to-execute healing plan
- Autonomous healing preparation

---

## What Gets Analyzed?

For EVERY test function (all 5,889+), the audit checks:

### 1. NECESSARY Pattern Compliance (9 Categories)

| Category | What It Checks |
|----------|----------------|
| **Normal** | Standard usage paths covered? |
| **Edge** | Boundary conditions tested? |
| **Cascading** | Error propagation verified? |
| **Essential** | Critical business logic validated? |
| **Security** | Auth, injection, XSS tested? |
| **Spec** | Acceptance criteria met? |
| **Accessibility** | Inclusive design considered? |
| **Resilience** | Error recovery tested? |
| **Year-round** | Time-based logic validated? |

### 2. Test Quality Metrics

- **Complexity Score**: 0.0-1.0 (based on lines of code)
- **Quality Issues**: Missing assertions, unclear names, etc.
- **Healing Priority**: P0 (critical) → P3 (low)

### 3. Healing Suggestions (if `--suggestions` flag used)

- Specific code improvements
- NECESSARY gap filling recommendations
- Refactoring opportunities

---

## Understanding the Reports

### Report 1: JSON (Machine-Readable)

**Location**: `audit_reports/marathon_audit_YYYYMMDD_HHMMSS.json`

**Structure**:
```json
[
  {
    "file": "tests/test_model_policy_enhanced.py",
    "name": "test_model_selection_with_override",
    "line_start": 42,
    "line_end": 58,
    "lines_of_code": 12,
    "complexity_score": 0.24,
    "necessary_coverage": ["Normal", "Edge"],
    "necessary_gaps": ["Security", "Resilience"],
    "quality_issues": ["Missing edge case for empty input"],
    "healing_priority": "P1",
    "healing_suggestions": ["Add test for empty string input"],
    "analysis_timestamp": "2025-10-23T15:30:45"
  }
]
```

**Use for**: Programmatic analysis, autonomous healing, metrics tracking

---

### Report 2: Markdown (Human-Readable)

**Location**: `audit_reports/marathon_audit_YYYYMMDD_HHMMSS.md`

**Contents**:
- Summary statistics (NECESSARY coverage %, priority breakdown)
- Top 50 priority tests (P0/P1 with details)
- Quality issues per test
- Healing suggestions

**Use for**: Manual review, understanding patterns, planning fixes

---

### Report 3: Healing Roadmap (Action Plan)

**Location**: `audit_reports/healing_roadmap_YYYYMMDD_HHMMSS.md`

**Structure**:
```markdown
# Healing Roadmap - Prioritized Action Plan

## Phase 1: Critical Fixes (P0)
- [ ] Fix `test_auth_bypass` in `tests/test_security.py:45`
      - Add authentication check before operation
      - Test injection vulnerability

## Phase 2: High Priority (P1)
- [ ] Enhance `test_model_selection` in `tests/test_model_policy.py:42`

## Phase 3: NECESSARY Gap Filling
### Security Gap (347 tests)
- [ ] Add Security tests to `tests/test_model_policy.py:42`
- [ ] Add Security tests to `tests/test_git_validation.py:60`

## Phase 4: Quality Improvements (P2/P3)
- 1,234 P2 issues
- 2,341 P3 issues
```

**Use for**:
- Prioritized fix execution
- Autonomous healing task queue
- Progress tracking (check off boxes as you fix)

---

## Running the Audit

### Step 1: Start Audit

```bash
# Quick test first (recommended)
python scripts/marathon_test_audit.py --depth quick --max-tests 100

# Full audit (run overnight)
python scripts/marathon_test_audit.py --depth standard

# Deep audit with suggestions (run over weekend)
python scripts/marathon_test_audit.py --depth deep --suggestions
```

### Step 2: Monitor Progress

The script shows live progress:

```
[  12.3%] test_model_selection_with_override            (ETA: 7.2h)
```

- **Percentage**: Tests analyzed so far
- **Test name**: Currently analyzing
- **ETA**: Estimated time remaining

### Step 3: Handle Interruptions (Ctrl+C)

If you need to stop:

1. Press **Ctrl+C**
2. Script saves checkpoint automatically
3. Resume later with:

```bash
python scripts/marathon_test_audit.py --resume
```

The script remembers:
- ✅ All tests already analyzed
- ✅ Current position
- ✅ Partial results

### Step 4: Review Reports

After completion:

```bash
# View healing roadmap
cat audit_reports/healing_roadmap_*.md

# View summary
cat audit_reports/marathon_audit_*.md | less

# JSON for programmatic use
jq '.[] | select(.healing_priority == "P0")' audit_reports/marathon_audit_*.json
```

---

## Cost Analysis

| Depth | Tests | Time | Local Cost | Cloud Cost | Savings |
|-------|-------|------|------------|------------|---------|
| Quick | 500 | 1h | $0 | ~$50 | 100% |
| Standard | 5,889 | 8h | $0 | ~$590 | 100% |
| Deep | 5,889 | 48h | $0 | ~$1,180 | 100% |

**Why $0 local?**
- Uses Qwen3-Coder-30b on your M4 Pro
- No API calls to OpenAI/Anthropic
- 100% offline capability

**Cloud equivalent:**
- OpenAI: ~$0.10 per test analysis
- Anthropic: ~$0.12 per test analysis

---

## What To Do With Results

### Immediate Actions (After Quick Mode)

1. **Review P0 issues** in healing roadmap
2. **Check NECESSARY gaps** - which categories are missing?
3. **Identify top 10 worst tests** - start fixing manually or autonomously

### Strategic Planning (After Standard Mode)

1. **Create healing task queue** from roadmap
2. **Prioritize P0/P1 fixes** for next sprint
3. **Use `/heal` command** to auto-fix issues
4. **Track progress** by checking off roadmap items

### Autonomous Healing (After Deep Mode)

1. **Feed healing suggestions to local model**:
   ```bash
   python scripts/bulk_local_fixer.py --from-roadmap audit_reports/healing_roadmap_*.md
   ```

2. **Enable autonomous fixing**:
   ```bash
   # Future feature: autonomous healing loop
   python scripts/autonomous_healer.py --roadmap audit_reports/healing_roadmap_*.md
   ```

3. **Verify fixes with tests**:
   ```bash
   python run_tests.py --run-all
   ```

---

## Advanced Usage

### Resume from Checkpoint

```bash
# If interrupted (Ctrl+C or crash)
python scripts/marathon_test_audit.py --resume
```

### Analyze Specific Test Subset

```bash
# Only analyze first 1000 tests
python scripts/marathon_test_audit.py --max-tests 1000
```

### Custom Depth Settings

Edit `scripts/marathon_test_audit.py` to adjust:
- `time.sleep()` intervals (line ~340)
- Model temperature (line ~75)
- Checkpoint frequency (line ~330)

---

## Troubleshooting

### Issue: "OSError: cannot send"

**Cause**: Ollama connection timeout

**Fix**:
```bash
# Restart Ollama
ollama serve

# Check status
curl http://localhost:11434/api/tags
```

### Issue: Audit runs too slow

**Solution 1**: Use quick mode first
```bash
python scripts/marathon_test_audit.py --depth quick
```

**Solution 2**: Reduce sleep interval
```python
# Edit line ~340 in marathon_test_audit.py
time.sleep(0.5)  # Faster, but M4 Pro may heat up
```

### Issue: Out of memory

**Cause**: M4 Pro using 48GB (Qwen3-Coder + tests)

**Fix**:
```bash
# Use smaller model
# Edit MODEL variable in marathon_test_audit.py
MODEL = "qwen2.5-coder:7b"  # Smaller, faster, less accurate
```

### Issue: Want to stop without checkpoint

```bash
# Kill process
pkill -9 -f marathon_test_audit.py

# Delete checkpoint
rm .marathon_audit_state.json
```

---

## Next Steps After Audit

### Option 1: Manual Fixing

1. Open healing roadmap
2. Pick P0/P1 issues
3. Fix manually
4. Run tests: `python run_tests.py --run-all`

### Option 2: Semi-Automated Fixing

```bash
# Use bulk fixer with roadmap
python scripts/bulk_local_fixer.py --from-roadmap audit_reports/healing_roadmap_*.md
```

### Option 3: Fully Autonomous Healing

```bash
# Store roadmap to VectorStore
python scripts/store_roadmap_to_vectorstore.py audit_reports/healing_roadmap_*.md

# Enable autonomous healing
/heal --auto --priority P0,P1
```

---

## FAQ

**Q: How long does it really take?**

A:
- Quick mode (500 tests): ~1 hour
- Standard mode (5,889 tests): ~8 hours
- Deep mode (5,889 tests + suggestions): ~48 hours

**Q: Can I run it on MacBook Air?**

A: Yes, but:
- Use smaller model: `qwen2.5-coder:7b` (3.8GB)
- Expect 2-3x longer execution time
- Watch memory usage: `docker stats agency-ollama`

**Q: Will it change my code?**

A: **NO!** 100% read-only. Only creates reports.

**Q: Can I use cloud models instead?**

A: Yes, edit `OLLAMA_API` to point to OpenAI/Anthropic, but:
- Cost: ~$590 for full audit (vs $0 local)
- Privacy: Code sent to cloud

**Q: What if I find a bug?**

A: Script is robust with retry logic, but if issues:
1. Check Ollama status: `ollama list`
2. Review logs: `cat .marathon_audit_state.json`
3. Report issue or fix manually

---

## Example Session

```bash
# Terminal 1: Start audit
$ python scripts/marathon_test_audit.py --depth standard

================================================================================
🏃 MARATHON TEST AUDIT - Long-Running Deep Analysis
================================================================================
Model: qwen3-coder:30b
Cost: $0 (100% local)
Depth: standard
Max Tests: ALL
Suggestions: False

🔍 Extracting ALL test functions...
  ✅ Found 5889 test functions across 284 files

🎯 Analyzing 5889 test functions...

[  12.3%] test_model_selection_with_override            (ETA: 7.2h)

# Press Ctrl+C to interrupt
^C

⚠️  Shutdown signal received. Saving checkpoint...
✅ Checkpoint saved. Resume with: --resume

# Resume later
$ python scripts/marathon_test_audit.py --resume

📂 Resuming from checkpoint: 725 tests already analyzed
[  12.3%] test_git_validation_edge_case                 (ETA: 7.0h)

# ... 8 hours later ...

================================================================================
✅ MARATHON AUDIT COMPLETE
================================================================================
Execution Time: 8.2 hours
Tests Analyzed: 5889
Cost: $0.00 (100% local)
Cloud Equivalent: ~$588.90 (AVOIDED!)

📊 Generating Reports...
  ✅ JSON: audit_reports/marathon_audit_20251023_153045.json
  ✅ Markdown: audit_reports/marathon_audit_20251023_153045.md
  ✅ Healing Roadmap: audit_reports/healing_roadmap_20251023_153045.md

# Review results
$ cat audit_reports/healing_roadmap_20251023_153045.md | less
```

---

## Summary

**This script gives you:**

1. ✅ **Complete test quality overview** (all 5,889 tests analyzed)
2. ✅ **NECESSARY pattern gap analysis** (which categories missing?)
3. ✅ **Prioritized healing roadmap** (P0/P1/P2/P3 with file:line references)
4. ✅ **Actionable suggestions** (if `--suggestions` flag used)
5. ✅ **$0 cost** (100% local execution)
6. ✅ **Checkpoint/resume** (handle interruptions gracefully)

**You asked for:**
> "read-only, long-running task (hours/days) that touches ALL 5000+ tests and creates a VERY USEFUL overview"

**This is exactly that!** Ready to run whenever you want. Start with `--depth quick --max-tests 100` to test it first.

---

**Next Step**: Try the quick mode!

```bash
python scripts/marathon_test_audit.py --depth quick --max-tests 100
```

Takes ~10 minutes, costs $0, proves the concept works!
