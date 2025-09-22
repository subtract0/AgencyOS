# ADR-003: Automated Merge Enforcement System

## Status
**Accepted** - 2025-09-21

## Context
Building on ADR-002's 100% verification requirement, manual enforcement proved insufficient. Human oversight introduces error potential and inconsistent application of quality standards. The "No Broken Windows" principle requires automated, zero-tolerance enforcement to prevent any compromise of code quality standards.

Despite clear rules from ADR-002, the following risks remained:
- Manual merge decisions could skip verification steps
- Time pressure might lead to "emergency" bypasses
- Human error in interpreting test results
- Inconsistent application of quality gates

## Decision
**Implement a multi-layered automated merge enforcement system that makes it technically impossible to merge code that violates ADR-002.**

### Core Components:

1. **MergerAgent**: Automated gatekeeper agent with exclusive merge authority
2. **Git Hooks**: Local enforcement preventing bad commits
3. **GitHub Actions**: Remote verification and enforcement
4. **Branch Protection**: Repository-level safeguards

### Zero-Tolerance Policy:
- No manual override capabilities
- No "emergency bypass" mechanisms
- 100% test success rate required at ALL enforcement layers
- Automatic rejection of any merge violating ADR-002

## Implementation Details

### 1. MergerAgent Architecture
```
.claude/agents/merger/
├── __init__.py
├── merger_agent.py           # Core agent logic
├── instructions.md           # Merge verification rules
├── instructions-gpt-5.md     # Model-specific instructions
└── tools/
    ├── test_runner.py        # Execute full test suite
    ├── merge_validator.py    # ADR-002 compliance check
    └── git_operations.py     # Safe merge operations
```

### 2. Pre-commit Hook Implementation
```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "🔍 ADR-003: Running automated merge enforcement..."

# Run full test suite
python run_tests.py
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "❌ MERGE BLOCKED by ADR-003"
    echo "📋 ADR-002 Violation: Tests must pass 100%"
    echo "🔧 Fix all failing tests before commit"
    exit 1
fi

# Run code quality checks
ruff check . --quiet
RUFF_EXIT_CODE=$?

if [ $RUFF_EXIT_CODE -ne 0 ]; then
    echo "❌ MERGE BLOCKED by ADR-003"
    echo "📋 Code quality violations detected"
    echo "🔧 Run: ruff check . --fix"
    exit 1
fi

echo "✅ ADR-003: All enforcement checks passed"
exit 0
```

### 3. GitHub Actions Workflow
```yaml
# .github/workflows/merge-guardian.yml
name: ADR-003 Merge Guardian

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main]

jobs:
  enforce-adr-002:
    runs-on: ubuntu-latest
    name: "ADR-003: Automated Merge Enforcement"

    steps:
    - uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt

    - name: ADR-002 Verification - 100% Test Success
      run: |
        echo "🔍 ADR-003: Enforcing 100% test success rate..."
        python run_tests.py
        if [ $? -ne 0 ]; then
          echo "::error title=ADR-003 Violation::ADR-002 requires 100% test success"
          echo "::error::Merge BLOCKED - Fix all failing tests"
          exit 1
        fi
        echo "✅ ADR-002 Compliance: 100% tests passing"

    - name: Code Quality Enforcement
      run: |
        ruff check .
        if [ $? -ne 0 ]; then
          echo "::error title=ADR-003 Violation::Code quality violations detected"
          exit 1
        fi

    - name: Merge Authorization
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      run: |
        echo "✅ ADR-003: Merge authorized - all quality gates passed"
```

### 4. Branch Protection Configuration
```bash
# GitHub CLI setup for branch protection
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ADR-003: Automated Merge Enforcement"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

## Enforcement Layers

### Layer 1: Pre-commit Hook (Local)
- **Scope**: Individual developer machines
- **Trigger**: Before each commit
- **Action**: Block commit if tests fail
- **Bypass**: Technically impossible (hook must be manually disabled)

### Layer 2: MergerAgent (Agent-Level)
- **Scope**: Agency multi-agent system
- **Trigger**: Before any merge operation
- **Action**: Automated test execution and validation
- **Bypass**: None - agent programmed for zero-tolerance

### Layer 3: GitHub Actions (CI/CD)
- **Scope**: All pull requests and pushes
- **Trigger**: Code push to repository
- **Action**: Full test suite + quality checks
- **Bypass**: None - required for merge

### Layer 4: Branch Protection (GitHub)
- **Scope**: Repository level
- **Trigger**: Merge attempt to main branch
- **Action**: Require passing CI checks
- **Bypass**: Admin override (disabled per ADR-003)

## Consequences

### Positive
- **Guaranteed Code Quality**: Technical impossibility of merging broken code
- **No Broken Windows**: Zero tolerance automatically enforced
- **Consistent Standards**: No human judgment variations
- **Fast Feedback**: Immediate notification of quality violations
- **Developer Confidence**: Absolute trust in main branch stability
- **Reduced Debugging**: Problems caught before merge

### Negative
- **Slower Merge Process**: Additional verification time required
- **No Emergency Bypass**: Cannot override for urgent fixes
- **Development Friction**: Must fix ALL issues before progress
- **Learning Curve**: Developers must adapt to strict enforcement
- **Tool Dependency**: System failure could block all merges

### Mitigation Strategies
- **Fast Test Suite**: Optimize test execution time (<2 minutes)
- **Clear Error Messages**: Specific guidance on fixing violations
- **Local Pre-validation**: Run enforcement checks before push
- **Progressive Fixes**: Break down large changes into smaller, testable units
- **Test Infrastructure**: Maintain robust, reliable test environment

## Metrics and Monitoring

### Compliance Metrics
- **ADR-002 Compliance Rate**: Must maintain 100%
- **Merge Success Rate**: Track first-attempt vs. retry merges
- **Test Failure Frequency**: Monitor patterns in test failures
- **Time to Resolution**: Average time from failure to fix

### Performance Metrics
- **Enforcement Latency**: Time from push to verdict
- **False Positive Rate**: Incorrect blocks (target: 0%)
- **System Availability**: Uptime of enforcement infrastructure

### Quality Metrics
- **Bug Escape Rate**: Post-merge defects (target: 0%)
- **Rollback Frequency**: Merges requiring reversion
- **Code Coverage**: Maintain >80% as per ADR-002

## Configuration Examples

### MergerAgent Integration
```python
# agency.py integration
from .claude.agents.merger import create_merger_agent

# Create merger agent with enforcement capabilities
merger_agent = create_merger_agent(
    model="gpt-5",
    reasoning_effort="high",
    agent_context=shared_context,
    enforcement_mode="strict",
    adr_compliance=["ADR-002", "ADR-003"]
)

# Add to agency communication flow
agency.add_agent(merger_agent)
agency.set_merge_authority(merger_agent)  # Exclusive merge rights
```

### Local Development Workflow
```bash
# Developer workflow with ADR-003 enforcement
git add .
git commit -m "feature: implement new functionality"
# → Pre-commit hook runs automatically
# → If tests fail: commit blocked, fix required
# → If tests pass: commit proceeds

git push origin feature-branch
# → GitHub Actions triggered
# → Full enforcement suite runs
# → PR status updated automatically

# Only after ALL enforcement layers pass:
# → Merge button becomes available
# → MergerAgent can authorize merge
```

## Emergency Procedures

### System Failure Response
If enforcement system fails:
1. **Immediate Action**: Stop all merge operations
2. **Manual Verification**: Run full test suite locally
3. **Temporary Measures**: Require additional reviewer approval
4. **System Restoration**: Priority repair of enforcement infrastructure
5. **Post-Incident**: Review and strengthen failure prevention

### Test Infrastructure Issues
If test system is compromised:
1. **Isolation**: Identify scope of test reliability issues
2. **Verification**: Manual execution of critical test subsets
3. **Communication**: Clear status to all developers
4. **Resolution**: Fix test infrastructure before resuming merges

## References
- **ADR-001**: Complete Context Before Action
- **ADR-002**: 100% Verification and Stability (foundational requirement)
- **Agency Swarm Framework**: Multi-agent coordination patterns
- **GitHub Branch Protection**: Repository security documentation
- **"No Broken Windows"**: The Pragmatic Programmer principle

## Review
- **Author**: AgencyCodeAgent
- **Mandated by**: @am
- **Date**: 2025-09-21
- **Dependencies**: ADR-002 (strict requirement)
- **Next Review**: 2025-12-21 (quarterly assessment)

---

*"Automation is the highest form of discipline. When humans cannot be trusted to maintain standards, machines must enforce them."*