# Contributing to Agency OS

Welcome! This guide will get you up and running in **5 minutes**.

## 🚀 Quick Start

### 1. Clone and Setup (2 minutes)
```bash
git clone https://github.com/subtract0/AgencyOS.git
cd Agency
./agency setup
```

### 2. Verify Health (30 seconds)
```bash
./scripts/health_check.sh
# Should show all ✅ green checkmarks
```

### 3. Create Feature Branch (REQUIRED)
```bash
# ⚠️ NEVER commit directly to main
git checkout -b feat/your-feature-name

# The pre-commit hook will block main commits (Article III)
```

### 4. Make Your Changes
```bash
# Edit files, write code
# Run fast tests during development:
pytest -m fast  # <30s feedback loop
```

### 5. Test Everything (2 minutes)
```bash
# Before committing, run full suite:
python run_tests.py --run-all
# Must be 100% passing (Article II)
```

### 6. Create PR (Constitutional Workflow)
```bash
git add .
git commit -m "feat: Your clear commit message"
git push -u origin feat/your-feature-name

# Create PR:
gh pr create --fill

# CI will run automatically - wait for ✅ green
```

---

## 📋 Constitutional Requirements

### Article II: 100% Test Success
- **ALL tests must pass** before merge
- No exceptions, no bypass
- Green CI pipeline required

### Article III: Automated Enforcement
- Feature branch workflow mandatory
- No direct commits to main
- Pre-commit hook enforces this

### Article V: Spec-Driven (for complex features)
- Complex features need `specs/feature.md`
- Simple fixes can skip formal spec

---

## 🧪 Testing Strategy

### Fast Tests (Development)
```bash
pytest -m fast
# Run continuously while coding
```

### Full Validation (Pre-Commit)
```bash
python run_tests.py --run-all
# 1,725+ tests, ~3 minutes
```

### Test Categories
- `fast`: Unit tests (<1s)
- `slow`: Integration tests (>5s)
- `constitutional`: Compliance tests
- `benchmark`: Performance tests

---

## 🏗️ Code Standards

### 1. Type Safety (Mandatory)
```python
# ❌ NO
def process(data: Dict[Any, Any]) -> any:
    pass

# ✅ YES
from pydantic import BaseModel

class Data(BaseModel):
    field: str

def process(data: Data) -> Result[Output, Error]:
    pass
```

### 2. TDD (Test-Driven Development)
```python
# Write test FIRST:
def test_feature():
    result = my_feature()
    assert result.is_ok()

# Then implement:
def my_feature() -> Result[str, Error]:
    return Ok("works!")
```

### 3. Result Pattern (Error Handling)
```python
from shared.type_definitions.result import Result, Ok, Err

def risky_operation() -> Result[Data, str]:
    if success:
        return Ok(data)
    return Err("reason for failure")
```

### 4. Keep Functions Small
- Maximum 50 lines per function
- One function, one purpose
- Clear, descriptive names

---

## 🔧 Development Workflow

### Daily Development Loop
```bash
1. git checkout main
2. git pull origin main
3. git checkout -b feat/my-feature
4. [Make changes]
5. pytest -m fast  # Quick validation
6. git add . && git commit -m "feat: description"
7. python run_tests.py --run-all  # Full validation
8. git push -u origin feat/my-feature
9. gh pr create
10. Wait for CI ✅
11. Merge via GitHub
```

### Commit Message Format
```bash
feat: Add new feature
fix: Bug fix
docs: Documentation only
test: Add or update tests
refactor: Code refactoring
perf: Performance improvement
chore: Maintenance task
```

---

## 🏥 Autonomous Healing

If tests fail, the system can often auto-heal:

```bash
# View autonomous healing logs
tail -f logs/autonomous_healing/constitutional_violations.jsonl

# Healing success rate: >95%
```

---

## 📊 Health Monitoring

### Check System Health
```bash
./scripts/health_check.sh
# Shows: Constitutional compliance, git status, logs, technical debt
```

### View Health Report
```bash
cat SYSTEM_HEALTH_REPORT.md
# Current score: 92/100 (A-)
```

---

## 🐛 Troubleshooting

### Tests Failing?
```bash
# 1. Check if it's a real failure
pytest tests/test_failing.py -v

# 2. Fix the code (not the test)
# 3. Re-run full suite
python run_tests.py --run-all
```

### Pre-commit Hook Blocking?
```bash
# You're on main - create feature branch:
git checkout -b feat/your-feature
git add .
git commit -m "your message"  # Now allowed
```

### CI Pipeline Red?
```bash
# Check CI logs
gh pr checks

# Fix issues
# Push again - CI re-runs automatically
```

---

## 🎯 Definition of Done

A task is complete when:
1. ✅ Code written
2. ✅ Tests written (TDD)
3. ✅ All tests pass (100%)
4. ✅ PR created
5. ✅ CI pipeline green
6. ✅ Merged to main

**Not before all 6 are complete.**

---

## 📚 Key Resources

- **Constitution**: `constitution.md` - The law
- **Health Report**: `SYSTEM_HEALTH_REPORT.md` - Current status
- **ADRs**: `docs/adr/` - Architecture decisions
- **Agents**: `.claude/agents/` - Agent capabilities
- **Tools**: `tools/` - Available tools

---

## 🆘 Getting Help

1. **Documentation**: Read `CLAUDE.md` for overview
2. **Health Check**: Run `./scripts/health_check.sh`
3. **Ask**: Open an issue on GitHub
4. **Constitution**: When in doubt, check `constitution.md`

---

## 🎉 Your First Contribution

### Beginner-Friendly Tasks
1. Add pytest markers to existing tests
2. Improve documentation
3. Fix TODOs in test files
4. Add type hints

### Where to Start
```bash
# Find good first issues:
grep -r "# TODO" --include="*.py" tests/

# Or check GitHub issues labeled "good-first-issue"
```

---

**Welcome to the team! Let's build something amazing together.** 🚀

*Questions? Check `CLAUDE.md` or ask in discussions.*
