# CI Access Provisioning Guide

## Overview

V5 Test Value Auditor requires CI failure history to identify proven bug detectors (tests that caught real bugs).

## Required Permissions

### GitHub Actions Access

**Minimum scopes:**
- `repo:read` - Read repository metadata
- `actions:read` - Read workflow runs and logs

**Token generation:**
```bash
# Via GitHub CLI
gh auth token

# Or: Personal Access Token (PAT)
# Settings → Developer settings → Personal access tokens → Generate new token (classic)
# Select: repo (all), actions:read
```

**Environment variable:**
```bash
export GITHUB_TOKEN="ghp_..."
```

**Security:**
- ✅ Store in environment variable (never commit)
- ✅ Use GitHub CLI token when possible (automatic refresh)
- ✅ Rotate tokens every 90 days
- ❌ Never commit to `.env` files in git

## CI Log Access Methods

### Method 1: GitHub Actions API (Recommended)

**Advantages:**
- Structured JSON data
- Built-in pagination
- Filter by date, status, conclusion

**API endpoints:**
```bash
# List workflow runs
GET /repos/{owner}/{repo}/actions/runs?created=>2024-07-01

# Get workflow run logs
GET /repos/{owner}/{repo}/actions/runs/{run_id}/logs

# Get job logs
GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs
```

**Rate limits:**
- 5,000 requests/hour (authenticated)
- Logs available for 90 days

### Method 2: Manual Log Download (Fallback)

If API unavailable:
```bash
# Download logs via GitHub CLI
gh run list --limit 100 --json databaseId,conclusion,createdAt
gh run view {run_id} --log > run_{run_id}.log
```

## Failure History Data Model

### SQLite Schema (.audit/failure_history.sqlite)

```sql
CREATE TABLE test_failures (
    id INTEGER PRIMARY KEY,
    test_id TEXT NOT NULL,
    failure_date TEXT NOT NULL,  -- ISO 8601
    ci_run_id TEXT,
    failure_reason TEXT,
    traceback TEXT,
    fixed_date TEXT,  -- NULL if not fixed
    is_flaky BOOLEAN DEFAULT 0,  -- Fails 2-9/10 runs
    UNIQUE(test_id, failure_date)
);

CREATE INDEX idx_test_id ON test_failures(test_id);
CREATE INDEX idx_failure_date ON test_failures(failure_date);
CREATE INDEX idx_fixed_date ON test_failures(fixed_date);
```

### Performance Requirements

- **Query time:** <100ms for 5,000 tests
- **Database size:** <50MB for 90 days history
- **Indexes:** test_id, failure_date, fixed_date

## Failure Classification

### Fixed Definition

Test is "fixed" when:
1. Previously failed in CI (1+ failures in history)
2. Passed in 3 consecutive CI runs after last failure
3. Time window: 90 days

**Query:**
```sql
SELECT test_id, COUNT(*) as failure_count
FROM test_failures
WHERE failure_date > date('now', '-90 days')
  AND fixed_date IS NOT NULL
GROUP BY test_id
```

### Flaky Definition

Test is "flaky" when:
1. Failed 2-9 out of 10 recent runs
2. Never achieved 3 consecutive passes (not fixed)
3. Time window: Last 30 days

**Detection:**
```python
def is_flaky(test_id, runs):
    failures = sum(1 for r in runs if r.failed)
    if 2 <= failures <= 9:
        # Check for 3 consecutive passes
        consecutive_passes = 0
        for run in reversed(runs):  # Most recent first
            if run.passed:
                consecutive_passes += 1
                if consecutive_passes >= 3:
                    return False  # Fixed, not flaky
            else:
                consecutive_passes = 0
        return True  # Never fixed = flaky
    return False
```

## Usage in Test Value Auditor

### Bonus Scoring

```python
# Failure bonus weight (configurable in weights.yaml)
FAILURE_BONUS_WEIGHT = 5.0

recent_failures = count_fixed_failures(test_id, days=90)
failure_bonus = recent_failures * FAILURE_BONUS_WEIGHT

# Integration
test_score += failure_bonus

# Examples:
# 0 failures: +0 bonus
# 1-2 failures (fixed): +5-10 bonus (proven bug detector)
# 3+ failures (fixed): +15 bonus (critical regression test)
# Flaky (2-9 fails, never fixed): -5 penalty (unreliable)
```

## Fallback Strategy

If CI access fails:
1. **Use local pytest cache** (`.pytest_cache/v/cache/lastfailed`)
2. **Heuristic estimation** (assume 0 failures for all tests)
3. **Log warning** but continue audit

**Constitutional requirement:** Idempotency - safe to re-run without corrupting data.

## Troubleshooting

### Token Authentication Failed
```bash
# Verify token
gh auth status

# Re-authenticate
gh auth login
```

### Rate Limit Exceeded
```bash
# Check current rate limit
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Solution: Wait for reset or use GitHub App (higher limits)
```

### No Logs Available (>90 days)
```bash
# GitHub Actions logs expire after 90 days
# Solution: Set up log archiving to S3/GCS before expiration
```

## References

- [GitHub Actions API](https://docs.github.com/en/rest/actions)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [SQLite Performance](https://www.sqlite.org/optoverview.html)
