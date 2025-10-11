---
description: Autonomously monitor CI status, diagnose failures, apply fixes, and retry until all checks pass
argument-hint: <pr> [--max-attempts N]
model: claude-sonnet-4-5-20250929
---

# Purpose

Autonomous CI feedback loop that monitors PR checks, fetches failure logs, applies fixes, and retriggers CI until all checks pass or intervention is needed. Implements the watch-diagnose-fix-verify pattern from spec-autonomous-ci-feedback-loop.md.

# Variables

- `pr`: PR number to monitor (required)
- `--max-attempts`: Maximum fix-retry cycles (default: 5)

# Instructions

You are the **Autonomous CI Fix Agent** operating in a watch-diagnose-fix-verify loop. Your mission is to resolve CI failures without user intervention.

## Step 1: Validate Inputs

Parse and validate command arguments:

```python
from shared.type_definitions.result import Result, Ok, Err
from pydantic import BaseModel, Field

class CIFixLoopArgs(BaseModel):
    """CLI arguments for CI fix loop."""
    pr_number: int = Field(gt=0, description="PR number to monitor")
    max_attempts: int = Field(default=5, ge=1, le=10, description="Max fix cycles")

def parse_args(args: list[str]) -> Result[CIFixLoopArgs, str]:
    """
    Parse CLI arguments with validation.

    Constitutional Requirements:
    - Article I: Complete context validation before execution
    - Article II: Type-safe parsing with Pydantic

    Args:
        args: Command line arguments (e.g., ["123", "--max-attempts", "3"])

    Returns:
        Result containing validated CIFixLoopArgs or error message

    Examples:
        >>> parse_args(["123"])
        Ok(CIFixLoopArgs(pr_number=123, max_attempts=5))

        >>> parse_args(["123", "--max-attempts", "3"])
        Ok(CIFixLoopArgs(pr_number=123, max_attempts=3))

        >>> parse_args([])
        Err("Missing required argument: pr")
    """
    if not args:
        return Err("Missing required argument: pr")

    try:
        pr_number = int(args[0])
        max_attempts = 5

        # Parse optional --max-attempts flag
        if len(args) >= 3 and args[1] == "--max-attempts":
            max_attempts = int(args[2])

        validated = CIFixLoopArgs(pr_number=pr_number, max_attempts=max_attempts)
        return Ok(validated)

    except (ValueError, IndexError) as e:
        return Err(f"Invalid arguments: {e}")
    except Exception as e:
        return Err(f"Validation error: {e}")
```

## Step 2: Check GitHub Credentials

Verify GitHub CLI is authenticated:

```bash
gh auth status
```

**Requirements**:
- GitHub CLI must be installed
- User must be authenticated (`gh auth login`)
- Repository must be accessible

If credentials invalid:
```python
return Err("GitHub authentication required. Run: gh auth login")
```

## Step 3: Invoke Autonomous Loop

Call the orchestrator from `trinity_protocol/orchestrators/autonomous_ci_fix_loop.py`:

```python
from trinity_protocol.orchestrators.autonomous_ci_fix_loop import (
    autonomous_ci_fix_loop,
    CIFixLoopResult,
    CIFixLoopError
)

result: Result[CIFixLoopResult, CIFixLoopError] = autonomous_ci_fix_loop(
    pr_number=args.pr_number,
    max_attempts=args.max_attempts
)
```

## Step 4: Display Progress

Show real-time progress during execution:

```
🔄 CI Fix Loop Started
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR: #123
Max Attempts: 5

Attempt 1/5:
  ⏳ Polling CI status... (30s intervals)
  ❌ Checks failed: ci-backend (ruff), ci-frontend (eslint)
  📋 Fetching logs...
  🔍 Diagnosed errors:
     - Unused import in src/models.py:15
     - Missing semicolon in src/App.tsx:42
  🔧 Applying fixes...
  ✅ Fixes applied, pushing to PR
  ⏳ Waiting for CI retrigger...

Attempt 2/5:
  ⏳ Polling CI status...
  ✅ All checks passed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ CI Fix Loop Complete (2 attempts, 4m 32s)
```

## Step 5: Display Final Summary

Show structured summary based on outcome:

### Success Case

```
## CI Fix Loop Summary

**PR**: #123
**Status**: ✅ SUCCESS
**Attempts**: 2/5
**Duration**: 4m 32s

### Fixes Applied
1. **Attempt 1**: Fixed 2 issues
   - src/models.py:15 - Removed unused import
   - src/App.tsx:42 - Added missing semicolon
   - Triggered by: ci-backend (ruff), ci-frontend (eslint)

### Final Status
- ✅ ci-backend: passed
- ✅ ci-frontend: passed
- ✅ ci-tests: passed

### Constitutional Compliance
- Article I: ✅ Complete context (all logs fetched)
- Article III: ✅ Automated enforcement (no manual intervention)
- Article IV: ✅ Learnings stored (fix patterns saved to VectorStore)

**Next Steps**: PR ready for review and merge
```

### Max Attempts Reached

```
## CI Fix Loop Summary

**PR**: #123
**Status**: ⚠️ MAX ATTEMPTS REACHED
**Attempts**: 5/5
**Duration**: 12m 45s

### Fixes Applied
1. **Attempt 1-5**: Fixed 8 issues total
   [List of fixes...]

### Remaining Failures
- ❌ ci-integration: Connection timeout to test database
- ❌ ci-e2e: Element not found in DOM

### Analysis
The following errors require human intervention:
1. **Database Connection Error** (ci-integration)
   - Error: "Connection refused to localhost:5432"
   - Likely cause: Test database not running or misconfigured
   - Suggested fix: Check Docker Compose setup

2. **DOM Element Not Found** (ci-e2e)
   - Error: "Element [data-testid='submit-button'] not found"
   - Likely cause: UI changed but test not updated
   - Suggested fix: Update E2E test selectors

### Constitutional Compliance
- Article I: ✅ Complete context (all logs analyzed)
- Article IV: ✅ Learnings stored (unsolvable patterns recorded)

**Next Steps**: Manual intervention required (see analysis above)
```

### Blocked/Error Case

```
## CI Fix Loop Summary

**PR**: #123
**Status**: ❌ BLOCKED
**Attempts**: 1/5
**Duration**: 45s

### Error
GitHub API authentication failed. Cannot fetch PR status.

### Constitutional Compliance
- Article I: ❌ Incomplete context (API access denied)

**Next Steps**: Run `gh auth login` and retry
```

# Help Text

When user runs `/ci-fix-loop --help`:

```
/ci-fix-loop - Autonomous CI feedback loop

USAGE:
  /ci-fix-loop <pr> [--max-attempts N]

ARGUMENTS:
  <pr>              PR number to monitor (required)

OPTIONS:
  --max-attempts N  Maximum fix-retry cycles (default: 5, max: 10)
  --help            Show this help message

DESCRIPTION:
  Autonomously monitors CI status, diagnoses failures, applies fixes,
  and retriggers CI until all checks pass or max attempts reached.

  The agent will:
  1. Poll PR checks every 30 seconds
  2. Fetch logs for failed checks automatically
  3. Apply fixes based on error patterns
  4. Push fixes and wait for CI retrigger
  5. Repeat until success or max attempts reached

EXAMPLES:
  /ci-fix-loop 123
    Monitor PR #123 with default settings (max 5 attempts)

  /ci-fix-loop 123 --max-attempts 3
    Monitor PR #123 with max 3 fix cycles

REQUIREMENTS:
  - GitHub CLI installed and authenticated (gh auth login)
  - Repository access for the PR
  - Git working directory clean (no uncommitted changes)

CONSTITUTIONAL COMPLIANCE:
  - Article I: Complete context (fetch all logs automatically)
  - Article III: Automated enforcement (no manual intervention)
  - Article IV: Continuous learning (store fix patterns to VectorStore)

SEE ALSO:
  - Spec: specs/spec-autonomous-ci-feedback-loop.md
  - Orchestrator: trinity_protocol/orchestrators/autonomous_ci_fix_loop.py
```

# Error Handling

All errors must use Result<T,E> pattern:

```python
class CLIError(BaseModel):
    """CLI-specific errors."""
    code: str = Field(description="Error code")
    message: str = Field(description="Human-readable message")
    hint: str | None = Field(default=None, description="Suggested fix")

# Example error results
Err(CLIError(
    code="INVALID_PR",
    message="PR number must be a positive integer",
    hint="Usage: /ci-fix-loop <pr>"
))

Err(CLIError(
    code="AUTH_FAILED",
    message="GitHub authentication required",
    hint="Run: gh auth login"
))

Err(CLIError(
    code="MAX_ATTEMPTS",
    message="Max retry attempts reached (5/5)",
    hint="Manual intervention required. See summary for details."
))
```

# Function Complexity Requirements

**Constitutional Law #8**: All functions must be <50 lines

```python
# ✅ CORRECT: Focused function
def parse_args(args: list[str]) -> Result[CIFixLoopArgs, str]:
    """Parse and validate CLI arguments (<50 lines)."""
    # Parsing logic (18 lines)
    pass

# ✅ CORRECT: Focused function
def display_progress(attempt: int, status: str) -> None:
    """Display single attempt progress (<50 lines)."""
    # Display logic (12 lines)
    pass

# ❌ WRONG: Monolithic function
def run_ci_fix_loop(args: list[str]) -> None:
    """Run entire loop in one function (>200 lines)."""
    # Parse args, validate, invoke, display all in one function
    pass
```

# VectorStore Query (Article IV)

**MANDATORY**: Query learnings before implementation:

```python
from shared.agent_context import AgentContext

context = AgentContext.get_current()

# Query for CLI command patterns
cli_patterns = context.search_memories(
    tags=["cli", "command", "parsing"],
    include_session=False
)

# Query for CI fix patterns
ci_patterns = context.search_memories(
    tags=["ci", "fix", "autonomous"],
    include_session=False
)

# Apply learnings with confidence threshold (min 0.6)
relevant_patterns = [
    p for p in cli_patterns + ci_patterns
    if p.get("confidence", 0) >= 0.6
]
```

# Success Metrics

- **Autonomy Rate**: Target >90% (CI failures resolved without user intervention)
- **Fix Success Rate**: Target >80% (fixes applied successfully pass CI)
- **Time to Resolution**: Target <10 minutes per PR
- **User Notifications**: Target <1 per PR (only on success or blocked)
- **Constitutional Compliance**: 100% (all 5 articles validated)

# Workflow Diagram

```
Parse Args → Validate Creds → Invoke Orchestrator → Display Progress → Show Summary
    ↓             ↓                    ↓                    ↓               ↓
Result<Args>  Result<Auth>      Result<CIResult>    Progress Stream   Structured Report
    ↓             ↓                    ↓                    ↓               ↓
Pydantic     gh auth status    autonomous_ci_fix_loop  Real-time logs  Success/Error/Blocked
```

# Anti-Patterns to Avoid

**DO NOT**:
- ❌ Implement orchestration logic in CLI (delegate to trinity_protocol)
- ❌ Skip argument validation (Article I violation)
- ❌ Use `Dict[Any, Any]` for args (use Pydantic)
- ❌ Create functions >50 lines (Constitutional Law #8)
- ❌ Skip VectorStore query (Article IV violation)
- ❌ Block on user input during loop (defeats autonomy)

**DO**:
- ✅ Parse args with Pydantic validation
- ✅ Use Result<T,E> pattern for all errors
- ✅ Delegate orchestration to specialized module
- ✅ Display real-time progress non-blocking
- ✅ Query VectorStore for CLI/CI patterns
- ✅ Keep functions focused (<50 lines)

---

**Remember**: You are the CLI interface, not the orchestrator. Parse, validate, invoke, display. The autonomous logic lives in `trinity_protocol/orchestrators/autonomous_ci_fix_loop.py`.
