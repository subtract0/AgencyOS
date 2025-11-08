# CI Autonomy Upgrades - Self-Diagnosis Automation

**Generated**: 2025-11-07 (Overnight Session)
**Purpose**: Enable future agents to self-diagnose CI failures faster
**Status**: Design proposals ready for implementation

---

## Executive Summary

**Problem**: When CI fails, agents must manually:
1. Parse GitHub Actions logs to find root cause
2. Correlate timeout patterns across multiple runs
3. Detect when manual verification docs are stale
4. Guess which suite timed out based on incomplete logs

**Solution**: Three automation proposals to enable autonomous self-diagnosis:

1. **Auto-Attach Failing Shard Logs** (HIGH PRIORITY) - Instant root cause in PR comments
2. **Timeout Heatmap Generator** (MEDIUM PRIORITY) - Visual pattern detection for optimization
3. **Stale Verification Detector** (LOW PRIORITY) - Auto-flag outdated manual verification docs

**Total Impact**: Save 5-15 minutes per CI failure, enable autonomous healing

---

## Proposal 1: Auto-Attach Failing Shard Logs 🔴 HIGH PRIORITY

### Problem
When a test shard fails in CI, agents must:
1. Click into GitHub Actions UI
2. Navigate to failed job
3. Scroll through 1000+ lines of logs
4. Find the actual error message (buried in output)
5. Copy error to context for analysis

**Time Cost**: 3-5 minutes per failure
**Frequency**: 10-20 failures per week = 30-100 min/week wasted

### Solution
Automatically extract and attach failing test logs to PR comments.

#### Implementation

**Create `.github/scripts/extract_failure_logs.py`**:
```python
#!/usr/bin/env python3
"""Extract failure logs from pytest output and format for PR comment."""

import re
import sys
from pathlib import Path


def extract_failures(pytest_output: str) -> list[dict]:
    """
    Extract failed test details from pytest output.

    Returns:
        list: [{"test": "test_name", "error": "error_msg", "traceback": "..."}]
    """
    failures = []

    # Regex pattern for pytest failure sections
    # FAILED tests/path/test_file.py::test_name - Error message
    failure_pattern = r"FAILED (.*?) - (.*?)(?=\n(?:FAILED|PASSED|$))"

    for match in re.finditer(failure_pattern, pytest_output, re.DOTALL):
        test_path = match.group(1)
        error_context = match.group(2)

        # Extract short error (first 200 chars)
        short_error = error_context[:200].strip()

        # Extract full traceback (up to 1000 chars)
        full_traceback = error_context[:1000].strip()

        failures.append({
            "test": test_path,
            "short_error": short_error,
            "full_traceback": full_traceback,
        })

    return failures


def format_pr_comment(failures: list[dict], shard_name: str) -> str:
    """Format failures as GitHub PR comment markdown."""

    if not failures:
        return f"✅ **{shard_name}**: All tests passed!"

    md = f"""## ❌ {shard_name} - {len(failures)} Failure(s)

<details>
<summary>Click to see failure details</summary>

"""

    for i, failure in enumerate(failures, 1):
        md += f"""### {i}. `{failure['test']}`

**Error**: {failure['short_error']}

<details>
<summary>Full traceback</summary>

```
{failure['full_traceback']}
```

</details>

---

"""

    md += "</details>\n"
    return md


def main():
    if len(sys.argv) != 3:
        print("Usage: extract_failure_logs.py <pytest_output.txt> <shard_name>")
        sys.exit(1)

    output_file = Path(sys.argv[1])
    shard_name = sys.argv[2]

    if not output_file.exists():
        print(f"Error: {output_file} not found")
        sys.exit(1)

    pytest_output = output_file.read_text()
    failures = extract_failures(pytest_output)
    comment = format_pr_comment(failures, shard_name)

    print(comment)


if __name__ == "__main__":
    main()
```

**Update `.github/workflows/merge-guardian.yml`**:
```yaml
jobs:
  test-unit:
    runs-on: ubuntu-latest
    steps:
      - name: "Run unit tests"
        id: pytest
        run: |
          pytest tests/unit -n 6 --maxfail=5 -v | tee pytest_output.txt
        continue-on-error: true  # Don't fail job immediately

      - name: "Extract failure logs"
        if: steps.pytest.outcome == 'failure'
        run: |
          python .github/scripts/extract_failure_logs.py pytest_output.txt "test-unit" > failure_report.md

      - name: "Post failure report"
        if: steps.pytest.outcome == 'failure'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('failure_report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });

      - name: "Fail job if tests failed"
        if: steps.pytest.outcome == 'failure'
        run: exit 1
```

### Expected Impact
- ✅ Instant root cause visibility (no log diving)
- ✅ Agents can read failure from PR comment (no GitHub UI navigation)
- ✅ 3-5 min saved per failure
- ✅ Better for async collaboration (team sees failures without clicking)

### Effort
**2-3 hours** (script + CI integration + testing)

### Risk
**LOW** - Non-critical addition, won't break existing CI

---

## Proposal 2: Timeout Heatmap Generator 🟡 MEDIUM PRIORITY

### Problem
CI timeout optimization requires analyzing patterns across many runs:
- Which suites consistently approach their timeout?
- Which suites have high variance (unpredictable)?
- Which suites could have tighter timeouts?

**Current Process**: Manual analysis of CI logs (30-60 min)

### Solution
Automatically generate timeout heatmaps from CI run history.

#### Implementation

**Create `.github/scripts/generate_timeout_heatmap.py`**:
```python
#!/usr/bin/env python3
"""
Generate timeout heatmap from GitHub Actions run history.

Usage:
    gh run list --workflow=merge-guardian --json durationMs,conclusion,name --limit 50 > runs.json
    python generate_timeout_heatmap.py runs.json > heatmap.md
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def parse_runs(runs_json: Path) -> dict:
    """
    Parse GitHub Actions run history.

    Returns:
        dict: {suite_name: [duration1, duration2, ...]}
    """
    with open(runs_json) as f:
        runs = json.load(f)

    suite_durations = defaultdict(list)

    for run in runs:
        # Extract suite name from job name
        # e.g., "test-unit / ubuntu-latest" -> "test-unit"
        suite_name = run.get("name", "unknown").split(" /")[0]

        # Convert milliseconds to minutes
        duration_min = run.get("durationMs", 0) / 1000 / 60

        suite_durations[suite_name].append(duration_min)

    return suite_durations


def calculate_stats(durations: list[float]) -> dict:
    """Calculate statistical metrics for suite durations."""
    if not durations:
        return {"min": 0, "max": 0, "avg": 0, "p50": 0, "p90": 0, "p99": 0}

    sorted_durations = sorted(durations)
    n = len(sorted_durations)

    return {
        "min": sorted_durations[0],
        "max": sorted_durations[-1],
        "avg": sum(durations) / n,
        "p50": sorted_durations[int(n * 0.5)],
        "p90": sorted_durations[int(n * 0.9)] if n > 10 else sorted_durations[-1],
        "p99": sorted_durations[int(n * 0.99)] if n > 100 else sorted_durations[-1],
    }


def generate_heatmap(suite_durations: dict) -> str:
    """Generate markdown heatmap with visual indicators."""

    md = """# CI Timeout Heatmap

**Generated**: Auto-generated from last 50 runs
**Purpose**: Identify timeout optimization opportunities

## Suite Performance Statistics

| Suite | Min | Avg | P50 | P90 | Max | Status |
|-------|-----|-----|-----|-----|-----|--------|
"""

    for suite_name, durations in sorted(suite_durations.items()):
        stats = calculate_stats(durations)

        # Determine status emoji based on P90 utilization
        # Assume 5 min timeout for most suites (adjust based on actual)
        timeout_min = 5.0  # Default
        if "foundation" in suite_name:
            timeout_min = 45.0
        elif "adr-agents" in suite_name:
            timeout_min = 18.0
        elif "toplevel" in suite_name:
            timeout_min = 25.0

        utilization = (stats["p90"] / timeout_min) * 100 if timeout_min > 0 else 0

        if utilization > 80:
            status = "🔴 High"
        elif utilization > 60:
            status = "🟡 Medium"
        else:
            status = "🟢 Healthy"

        md += f"| {suite_name} | {stats['min']:.1f}m | {stats['avg']:.1f}m | {stats['p50']:.1f}m | {stats['p90']:.1f}m | {stats['max']:.1f}m | {status} |\n"

    md += """
## Status Legend
- 🟢 **Healthy**: P90 < 60% of timeout (room for optimization)
- 🟡 **Medium**: P90 60-80% of timeout (monitor closely)
- 🔴 **High**: P90 > 80% of timeout (risk of timeouts, needs optimization)

## Recommendations
1. **🔴 High status**: Increase timeout or split suite
2. **🟢 Healthy with low utilization**: Consider tightening timeout
3. **High variance (max >> p90)**: Investigate flaky tests or resource contention
"""

    return md


def main():
    if len(sys.argv) != 2:
        print("Usage: generate_timeout_heatmap.py <runs.json>")
        sys.exit(1)

    runs_json = Path(sys.argv[1])

    if not runs_json.exists():
        print(f"Error: {runs_json} not found")
        sys.exit(1)

    suite_durations = parse_runs(runs_json)
    heatmap = generate_heatmap(suite_durations)

    print(heatmap)


if __name__ == "__main__":
    main()
```

**Add to `.github/workflows/` as scheduled job**:
```yaml
name: "Generate Timeout Heatmap"

on:
  schedule:
    - cron: "0 0 * * 0"  # Weekly on Sunday midnight
  workflow_dispatch:

jobs:
  generate-heatmap:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: "Fetch run history"
        run: |
          gh run list --workflow=merge-guardian --json durationMs,conclusion,name --limit 50 > runs.json
        env:
          GH_TOKEN: ${{ github.token }}

      - name: "Generate heatmap"
        run: |
          python .github/scripts/generate_timeout_heatmap.py runs.json > docs/ci/TIMEOUT_HEATMAP.md

      - name: "Commit heatmap"
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/ci/TIMEOUT_HEATMAP.md
          git commit -m "chore(ci): update timeout heatmap [skip ci]" || echo "No changes"
          git push
```

### Expected Impact
- ✅ Weekly automated timeout analysis (was: 30-60 min manual)
- ✅ Visual identification of optimization opportunities
- ✅ Historical tracking (git history shows trends)
- ✅ Agents can query heatmap before proposing timeout changes

### Effort
**3-4 hours** (script + workflow + testing)

### Risk
**LOW** - Runs independently, won't affect CI stability

---

## Proposal 3: Stale Verification Detector 🟢 LOW PRIORITY

### Problem
Manual verification docs (e.g., `TOP_LEVEL_MANUAL_VERIFICATION.md`) can become stale:
- Last verification date > 7 days ago
- Tests added/removed but doc not updated
- No automated reminder to re-verify

**Risk**: Merge expensive suites assuming they pass, but doc is outdated

### Solution
Automated staleness detection with PR warnings.

#### Implementation

**Create `.github/scripts/detect_stale_verification.py`**:
```python
#!/usr/bin/env python3
"""Detect stale manual verification documents."""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def check_verification_freshness(doc_path: Path, max_age_days: int = 7) -> dict:
    """
    Check if manual verification doc is stale.

    Returns:
        dict: {"is_stale": bool, "last_verified": str, "days_old": int}
    """
    if not doc_path.exists():
        return {
            "is_stale": True,
            "last_verified": "NEVER",
            "days_old": 9999,
            "reason": "Document does not exist",
        }

    content = doc_path.read_text()

    # Extract last verification date
    # Format: **Last Verification**: 2025-11-06
    date_pattern = r"\*\*Last Verification\*\*:\s*(\d{4}-\d{2}-\d{2})"
    match = re.search(date_pattern, content)

    if not match:
        return {
            "is_stale": True,
            "last_verified": "UNKNOWN",
            "days_old": 9999,
            "reason": "No verification date found in document",
        }

    last_verified_str = match.group(1)
    last_verified = datetime.strptime(last_verified_str, "%Y-%m-%d")
    days_old = (datetime.now() - last_verified).days

    return {
        "is_stale": days_old > max_age_days,
        "last_verified": last_verified_str,
        "days_old": days_old,
        "reason": f"Last verified {days_old} days ago (threshold: {max_age_days} days)",
    }


def generate_warning_comment(staleness: dict) -> str:
    """Generate GitHub PR warning comment."""

    if not staleness["is_stale"]:
        return ""

    return f"""## ⚠️ Stale Manual Verification Detected

**Document**: `docs/ci/TOP_LEVEL_MANUAL_VERIFICATION.md`
**Last Verified**: {staleness['last_verified']}
**Age**: {staleness['days_old']} days
**Threshold**: 7 days

### Recommendation
Before merging changes to memory, tools, or CI config, please:

1. Run manual verification suite:
   ```bash
   PYTHONMALLOC=malloc pytest tests/test_leap* -m "not slow" --maxfail=1 -v
   ```

2. Update `docs/ci/TOP_LEVEL_MANUAL_VERIFICATION.md` with results

3. Or skip if changes are low-risk (formatting, docs only)

See: `docs/ci/CI_MANUAL_VERIFICATION_SOP.md` for full procedure
"""


def main():
    doc_path = Path("docs/ci/TOP_LEVEL_MANUAL_VERIFICATION.md")
    staleness = check_verification_freshness(doc_path, max_age_days=7)
    warning = generate_warning_comment(staleness)

    if warning:
        print(warning)
    else:
        print("✅ Manual verification is fresh (< 7 days old)")


if __name__ == "__main__":
    main()
```

**Add to `.github/workflows/merge-guardian.yml`**:
```yaml
jobs:
  check-staleness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: "Check verification staleness"
        id: staleness
        run: |
          python .github/scripts/detect_stale_verification.py > staleness_warning.md

      - name: "Post staleness warning"
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const warning = fs.readFileSync('staleness_warning.md', 'utf8');
            if (warning.includes('⚠️')) {
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: warning
              });
            }
```

### Expected Impact
- ✅ Automated reminder to refresh verification docs
- ✅ Prevents merging with stale validation
- ✅ Saves 5-10 min debugging issues from outdated assumptions

### Effort
**1-2 hours** (simple script + workflow integration)

### Risk
**VERY LOW** - Just adds informational comments

---

## Implementation Priority

### Phase 1: High Value, Low Risk (Week 1)
1. **Proposal 1**: Auto-attach failing shard logs
   - Effort: 2-3 hours
   - Impact: 3-5 min saved per failure × 10-20 failures/week = 30-100 min/week

### Phase 2: Optimization Insights (Week 2)
2. **Proposal 2**: Timeout heatmap generator
   - Effort: 3-4 hours
   - Impact: 30-60 min saved weekly on manual analysis

### Phase 3: Quality Assurance (Week 3)
3. **Proposal 3**: Stale verification detector
   - Effort: 1-2 hours
   - Impact: Prevents stale doc issues (rare but critical)

---

## Success Metrics

### Before Autonomy Upgrades
- **Failure diagnosis time**: 3-5 minutes (manual log diving)
- **Timeout analysis**: 30-60 minutes (manual, weekly)
- **Stale doc detection**: Manual/never (reactive only)

### After Autonomy Upgrades
- **Failure diagnosis time**: <30 seconds (read PR comment)
- **Timeout analysis**: <5 minutes (read auto-generated heatmap)
- **Stale doc detection**: <1 minute (automated warning)

**Total Time Savings**: 5-15 minutes per CI failure, 30-60 minutes per week on analysis

---

## Constitutional Compliance

### Article I: Complete Context
- ✅ Auto-attached logs provide complete error context
- ✅ Heatmaps provide historical trend context
- ✅ Staleness warnings provide verification freshness context

### Article II: 100% Verification
- ✅ Agents can verify failures without manual log diving
- ✅ Timeout patterns verified with statistical analysis
- ✅ Verification staleness explicitly checked

### Article IV: Continuous Learning
- ✅ Heatmaps stored in git → institutional memory
- ✅ Failure patterns visible → learning opportunities
- ✅ Agents query artifacts → informed decisions

---

## Next Steps

**Immediate** (This Session):
- [x] Create design document (this file)
- [ ] Prototype Proposal 1 script (if time allows)

**Week 1** (After Approval):
- [ ] Implement Proposal 1 (auto-attach logs)
- [ ] Test on failing PR
- [ ] Deploy to merge-guardian.yml

**Week 2** (After Proposal 1 Success):
- [ ] Implement Proposal 2 (timeout heatmap)
- [ ] Run first weekly heatmap
- [ ] Review results with team

**Week 3** (Polish):
- [ ] Implement Proposal 3 (staleness detector)
- [ ] Monitor for false positives
- [ ] Document best practices

---

**Autonomy Upgrade Version**: 1.0
**Next Review**: After Proposal 1 implementation
**Owner**: CI/CD Autonomy Team

---

*"Self-diagnosing systems heal faster. Agents with instant context make better decisions."*
