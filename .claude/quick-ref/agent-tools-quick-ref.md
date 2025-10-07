# Agent Tools Quick Reference

**5 Essential Tools for Constitutional Compliance**

## 1. `/agent-memory-query` - Query VectorStore (Article IV)

**Purpose**: Query institutional memory BEFORE action

**Usage**:
```bash
/agent-memory-query [task-type] [confidence-threshold]

# Examples
/agent-memory-query implementation 0.6
/agent-memory-query fix 0.7
/agent-memory-query test 0.6
/agent-memory-query refactor 0.6
/agent-memory-query audit 0.6
```

**Returns**:
- High confidence patterns (≥0.9) - apply automatically
- Medium confidence patterns (0.7-0.89) - consider carefully
- Errors to avoid - historical failures
- Code samples - reusable implementations

**When to Use**:
- ✅ MANDATORY before implementation (Article IV)
- ✅ Before healing violations
- ✅ Before writing tests
- ✅ Before refactoring
- ✅ Before auditing

## 2. `/agent-memory-store` - Store Patterns (Article IV)

**Purpose**: Store successful patterns AFTER completion

**Usage**:
```bash
/agent-memory-store [task-type] [outcome]

# Examples
/agent-memory-store implementation success
/agent-memory-store fix success
/agent-memory-store test success
/agent-memory-store refactor success
```

**Stores**:
- Pattern description
- Code samples
- Success metrics
- Confidence score
- Evidence count

**When to Use**:
- ✅ MANDATORY after successful implementation (Article IV)
- ✅ After successful healing
- ✅ After comprehensive tests
- ✅ After validated refactoring

## 3. `/agent-test-verify` - Run Tests with Retry (Articles I & II)

**Purpose**: Execute tests with constitutional retry logic

**Usage**:
```bash
/agent-test-verify [scope] [timeout-multiplier]

# Examples
/agent-test-verify all          # Full test suite
/agent-test-verify unit         # Unit tests only
/agent-test-verify integration  # Integration tests
/agent-test-verify file:tests/test_feature.py  # Specific file
```

**Features**:
- Automatic retry on timeout (2x, 3x, 10x)
- 100% pass rate enforcement (Article II)
- Throws ConstitutionalViolation if exhausted
- Detailed test metrics

**When to Use**:
- ✅ After writing tests (confirm failures)
- ✅ After implementation (verify 100% pass)
- ✅ Before commit (final verification)
- ✅ During healing (validate fixes)

## 4. `/agent-diff-review` - Review Diff (Article III)

**Purpose**: Validate git diff against all 10 constitutional laws

**Usage**:
```bash
/agent-diff-review [scope] [strict]

# Examples
/agent-diff-review staged true   # Block on violations
/agent-diff-review staged false  # Warn only
/agent-diff-review unstaged true
/agent-diff-review branch true
```

**Validates**:
- All 10 constitutional laws
- Type safety (no Dict[Any, Any])
- Function complexity (<50 lines)
- Code duplication
- Security vulnerabilities
- TODOs without issues

**When to Use**:
- ✅ MANDATORY before commit (Article III)
- ✅ Before PR creation
- ✅ After healing completion
- ✅ Pre-commit hook integration

## 5. `/agent-adr-query` - Query ADRs (Architectural Guidance)

**Purpose**: Access institutional architectural wisdom

**Usage**:
```bash
/agent-adr-query [topic] [format]

# Examples
/agent-adr-query typing summary
/agent-adr-query testing detailed
/agent-adr-query patterns summary
/agent-adr-query architecture detailed
/agent-adr-query all reference
```

**Returns**:
- ADR decisions
- Context and rationale
- Code examples
- Enforcement mechanisms
- Cross-references

**When to Use**:
- ✅ Before architectural decisions
- ✅ When unsure about coding standards
- ✅ To ensure consistency with precedent
- ✅ Before creating new patterns

---

## Agent Integration Matrix

| Agent | Query Memory | Store Memory | Test Verify | Diff Review | ADR Query |
|-------|-------------|--------------|-------------|-------------|-----------|
| **code_agent** | ✅ Step 1 | ✅ Step 9 | ✅ Step 3 | ✅ Step 7 | ✅ Step 2 |
| **quality_enforcer** | ✅ Step 1 | ✅ Step 8 | ✅ Step 6 | ✅ Step 7 | ✅ Step 2 |
| **test_generator** | ✅ Step 2 | ✅ Step 9 | ✅ Step 6,8 | Optional | ✅ Step 3 |
| **auditor** | ✅ Step 2 | ✅ Step 11 | N/A | N/A | ✅ Step 3 |
| **planner** | ✅ Optional | ✅ Optional | N/A | N/A | ✅ Always |
| **merger** | ✅ Optional | ✅ Optional | ✅ Pre-merge | ✅ Always | ✅ Optional |

---

## Workflow Examples

### Code Agent Full Workflow

```bash
# 1. Query institutional memory (MANDATORY)
/agent-memory-query implementation 0.6

# 2. Query ADR guidance
/agent-adr-query typing summary

# 3. Write tests first, verify failures
/agent-test-verify file:tests/test_feature.py

# 4-5. Implement + refactor (manual)

# 6. Verify quality
/agent-test-verify all

# 7. Review diff (MANDATORY)
/agent-diff-review staged true

# 8. Commit (if diff review passes)
git commit -m "feat: implement feature"

# 9. Store learnings (MANDATORY)
/agent-memory-store implementation success
```

### Quality Enforcer Healing Workflow

```bash
# 1. Query known fixes (MANDATORY)
/agent-memory-query fix 0.7

# 2. Query ADR standards
/agent-adr-query patterns summary

# 3-5. Detect + diagnose + heal (autonomous)

# 6. Verify with tests (MANDATORY)
/agent-test-verify all

# 7. Review changes (MANDATORY)
/agent-diff-review staged strict

# 8. Store healing pattern (MANDATORY)
/agent-memory-store fix success
```

### Pre-Commit Hook Integration

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Review staged changes
/agent-diff-review staged true

if [ $? -ne 0 ]; then
    echo "❌ Pre-commit blocked by constitutional violations"
    exit 1
fi

# Verify all tests pass
/agent-test-verify all

if [ $? -ne 0 ]; then
    echo "❌ Pre-commit blocked - tests must pass 100%"
    exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
```

---

## Constitutional Enforcement

| Article | Tool | Enforcement |
|---------|------|-------------|
| **Article I** | `/agent-test-verify` | Complete context via retry (2x, 3x, 10x) |
| **Article II** | `/agent-test-verify` | 100% pass rate (no exceptions) |
| **Article III** | `/agent-diff-review` | Pre-commit blocking on violations |
| **Article IV** | `/agent-memory-query` + `/agent-memory-store` | Mandatory query before + store after |
| **Article V** | `/agent-adr-query` | Spec-driven decisions aligned with ADRs |

---

## Success Metrics

- **Learning Reuse**: >80% of tasks apply VectorStore patterns
- **Error Avoidance**: >90% reduction in known errors
- **Test Reliability**: 100% pass rate enforced (zero timeouts accepted)
- **Commit Quality**: >95% violation detection before commit
- **Architectural Alignment**: >95% consistency with ADRs

---

**Quick Reference Version 1.0** - Agent Tools Integration
**Last Updated**: 2025-10-07
