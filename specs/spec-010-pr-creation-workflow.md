# Specification: Git Worktree Isolation Workflow for PR Creation

**Spec ID**: `spec-010-pr-creation-workflow`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-11
**Last Updated**: 2025-10-11
**Related Plan**: `plan-010-pr-creation-workflow.md`

---

## Executive Summary

> This specification defines a standardized Git worktree isolation workflow for autonomous PR creation that ensures zero file conflicts between parallel agent executions, enforces constitutional compliance (100% test pass requirement), and maintains predictable commit/PR patterns with automated cleanup. The workflow enables multiple agents to work simultaneously on different features without interfering with the main workspace or each other.

---

## Goals

### Primary Goals
> What this workflow WILL accomplish - specific, measurable objectives

- [x] **Goal 1**: Enable parallel autonomous agent execution without file conflicts through isolated Git worktrees
- [x] **Goal 2**: Enforce Article II constitutional compliance (100% test pass) before PR creation via automated checks
- [x] **Goal 3**: Standardize commit message format with Claude co-authorship attribution for audit trail
- [x] **Goal 4**: Define deterministic PR body template (Summary, Test Plan, Constitutional Compliance) for consistent quality gate documentation
- [x] **Goal 5**: Automate worktree cleanup after PR merge to prevent disk bloat and abandoned branches

### Success Metrics
> How we will measure success

- **Metric 1**: Zero file conflicts between parallel agent executions (0 conflict-related failures per 100 PRs)
- **Metric 2**: 100% PR creation adherence to constitutional test pass requirement (0 PRs created with failing tests)
- **Metric 3**: 100% commit message compliance with Co-Authored-By format (automated validation)
- **Metric 4**: <30 seconds PR creation time from commit to PR URL (gh pr create latency)
- **Metric 5**: 100% automatic worktree cleanup within 24 hours of PR merge

---

## Non-Goals

### Explicit Exclusions
> What this workflow will NOT do - clear scope boundaries

- **Non-Goal 1**: Support for non-worktree Git workflows (standard clones, submodules) - worktree isolation is mandatory
- **Non-Goal 2**: Manual commit message editing - templates are enforced programmatically
- **Non-Goal 3**: PR creation without CI passing - constitutional enforcement is absolute
- **Non-Goal 4**: Support for bare repository file operations - all file work requires worktree creation

### Future Considerations
> Potential future enhancements that are out of scope for this iteration

- **Future Enhancement 1**: Automatic PR description enhancement via LLM analysis of git diff
- **Future Enhancement 2**: Stacked PR support for dependent feature branches
- **Future Enhancement 3**: Auto-rebase on main branch updates before PR creation
- **Future Enhancement 4**: Cross-repository PR coordination for multi-repo features

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Autonomous Agent (Primary User)
- **Description**: Agency agents (AgencyOSAgent, QualityEnforcer, Auditor) executing tasks in isolation
- **Goals**: Create feature branches, commit changes, open PRs without human intervention or workspace conflicts
- **Pain Points**: File conflicts when multiple agents work simultaneously, pre-commit hook blocking PRs with test failures, forgetting Co-Authored-By attribution
- **Technical Proficiency**: Expert (programmatic Git access via Python subprocess)

#### Persona 2: Human Developer (@am)
- **Description**: Repository owner reviewing PRs created by autonomous agents
- **Goals**: Quickly understand PR intent, verify constitutional compliance, merge with confidence
- **Pain Points**: Inconsistent PR descriptions, missing test coverage info, unclear Claude contribution attribution, orphaned worktree directories
- **Technical Proficiency**: Expert (Git power user, understands worktree mechanics)

### User Journeys

#### Journey 1: Autonomous Feature Implementation
```
1. User starts with: AgencyOSAgent receives task "Implement JWT authentication"
2. User needs to: Isolate work from main workspace to avoid conflicts
3. User performs:
   - Creates worktree: git worktree add ../Agency-{session_id} -b feat/jwt-auth
   - Implements feature in isolated directory
   - Runs tests: pytest (must pass 100%)
   - Commits with template: git commit --no-verify -m "{message}\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
   - Pushes: git push -u origin feat/jwt-auth
   - Creates PR: gh pr create --title "..." --body "{template}"
4. System responds:
   - PR created with URL: https://github.com/org/repo/pull/123
   - CI pipeline triggered automatically
   - Branch protection rules validate constitutional compliance
5. User achieves: Feature PR ready for @am review, zero conflicts with other agents
```

#### Journey 2: PR Merge and Cleanup
```
1. User starts with: @am approves PR #123, merges via GitHub UI
2. User needs to: Cleanup worktree and local branches to prevent disk bloat
3. User performs:
   - Checks merge status: gh pr view 123 --json state
   - Removes worktree: git worktree remove ../Agency-{session_id}
   - Prunes references: git worktree prune
   - Deletes local branch: git branch -d feat/jwt-auth
4. System responds:
   - Worktree directory deleted
   - Git references cleaned
   - Disk space reclaimed
5. User achieves: Clean repository state, ready for next task
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: Worktree Creation
- [x] **AC-1.1**: System creates worktree with naming pattern `../Agency-{session_id}` where session_id is UUID4 or timestamp-based
- [x] **AC-1.2**: Branch naming follows convention: `{type}/{kebab-case-description}` where type is `feat|fix|refactor|docs|test`
- [x] **AC-1.3**: Worktree creation verifies parent directory exists and main .git database is accessible (not bare repo error)
- [x] **AC-1.4**: Multiple worktrees can coexist without file locking conflicts (parallel agent execution)

#### Feature Component 2: Commit Message Templating
- [x] **AC-2.1**: Commit message follows format: `{type}: {imperative title}\n\n{body}\n\nCo-Authored-By: Claude <noreply@anthropic.com>`
- [x] **AC-2.2**: Type is one of: `feat|fix|refactor|docs|test|style|chore`
- [x] **AC-2.3**: Title is imperative mood (e.g., "Add JWT auth", not "Added JWT auth")
- [x] **AC-2.4**: Body explains WHY (context, rationale) not WHAT (visible in diff)
- [x] **AC-2.5**: Co-Authored-By line is mandatory and properly formatted (verified via pre-commit hook or commit-msg hook)

#### Feature Component 3: PR Body Template
- [x] **AC-3.1**: PR body includes three required sections: ## Summary, ## Test Plan, ## Constitutional Compliance
- [x] **AC-3.2**: Summary section: 2-3 sentence overview + bullet points of key changes (auto-generated from commits)
- [x] **AC-3.3**: Test Plan section: Markdown checklist of testing performed (e.g., "- [x] Unit tests pass (47/47)" )
- [x] **AC-3.4**: Constitutional Compliance section: Checklist validating Articles I-V with evidence (e.g., "- [x] Article II: 100% test pass (1,725/1,725)")
- [x] **AC-3.5**: Footer includes: "🤖 Generated with [Claude Code](https://claude.com/claude-code)"

#### Feature Component 4: Mergeability Checks
- [x] **AC-4.1**: System validates 100% test pass via `python run_tests.py --run-all` before allowing PR creation
- [x] **AC-4.2**: System checks for merge conflicts: `git status` shows "nothing to commit, working tree clean" after rebase
- [x] **AC-4.3**: System verifies CI pipeline status: `gh pr checks {pr_number}` returns all checks passing
- [x] **AC-4.4**: System enforces branch protection: no force push, no bypass of required reviews
- [x] **AC-4.5**: Automatic rollback if mergeability checks fail (delete remote branch, cleanup worktree)

#### Feature Component 5: Cleanup Automation
- [x] **AC-5.1**: After PR merge detected (via `gh pr view {pr} --json state`), system triggers cleanup within 5 minutes
- [x] **AC-5.2**: Cleanup removes worktree: `git worktree remove {path} --force` (handles uncommitted changes)
- [x] **AC-5.3**: Cleanup prunes references: `git worktree prune`
- [x] **AC-5.4**: Cleanup deletes merged branch: `git branch -d {branch}` (fails if not merged, uses -D for force delete)
- [x] **AC-5.5**: Cleanup logs success/failure to telemetry for Article IV learning

### Non-Functional Requirements

#### Performance
- [x] **AC-P.1**: Worktree creation completes in <5 seconds (local filesystem operation)
- [x] **AC-P.2**: PR creation (commit + push + gh pr create) completes in <30 seconds
- [x] **AC-P.3**: Cleanup automation completes in <10 seconds per worktree

#### Quality
- [x] **AC-Q.1**: Zero file conflicts in 100% of parallel agent executions (isolated working directories)
- [x] **AC-Q.2**: 100% commit message compliance with template (automated validation)
- [x] **AC-Q.3**: 100% PR body completeness (all three sections required)

#### Security
- [x] **AC-S.1**: Worktree paths do not expose sensitive session IDs in public logs
- [x] **AC-S.2**: Git credentials are never logged in commit messages or PR bodies
- [x] **AC-S.3**: Pre-commit hooks cannot be bypassed for constitutional violations (--no-verify allowed only for worktree-specific test runs)

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [x] **AC-CI.1**: Worktree creation verifies main .git database accessibility before proceeding
- [x] **AC-CI.2**: PR creation retries on transient GitHub API errors (timeout, rate limit) up to 3x
- [x] **AC-CI.3**: Cleanup verifies PR merge status before deleting branches (no premature cleanup)

#### Article II: 100% Verification and Stability
- [x] **AC-CII.1**: 100% test pass required before PR creation (blocking, no exceptions)
- [x] **AC-CII.2**: CI pipeline validates tests again in isolated environment (GitHub Actions)
- [x] **AC-CII.3**: No test deactivation or skip markers allowed in PR commits

#### Article III: Automated Merge Enforcement
- [x] **AC-CIII.1**: Branch protection enforces required reviews and status checks
- [x] **AC-CIII.2**: No manual bypass of quality gates via admin privileges
- [x] **AC-CIII.3**: Pre-commit hooks enforce constitutional compliance locally

#### Article IV: Continuous Learning and Improvement
- [x] **AC-CIV.1**: Successful PR patterns (worktree path, branch name, commit structure) stored in VectorStore
- [x] **AC-CIV.2**: Failed PR attempts analyzed for learning (e.g., test failures, merge conflicts)
- [x] **AC-CIV.3**: Cleanup automation learns optimal timing from PR merge latency patterns

#### Article V: Spec-Driven Development
- [x] **AC-CV.1**: This specification defines the PR workflow standard for all agents
- [x] **AC-CV.2**: Implementation strictly follows this spec (plan-010 references spec-010)
- [x] **AC-CV.3**: Workflow changes require spec amendment before implementation

---

## Dependencies & Constraints

### System Dependencies
- **Git 2.30+**: Worktree support with modern features (prune, list, lock)
- **GitHub CLI (gh)**: PR creation, status checks, merge detection (gh version 2.0+)
- **Python 3.11+**: Subprocess management for git/gh commands
- **pytest**: Test execution for constitutional compliance validation

### External Dependencies
- **GitHub API**: PR creation, CI status checks, merge event webhooks
- **Branch Protection Rules**: Repository settings enforce constitutional compliance

### Technical Constraints
- **Worktree Isolation**: Main repository may be bare (no working directory), all file operations require worktree
- **Disk Space**: Each worktree consumes ~500MB (codebase size), max 10 concurrent worktrees (5GB)
- **Pre-commit Hook**: Blocks commits with test failures, requires --no-verify override in worktrees
- **pytest-xdist**: May not be available in worktree venv, requires PYTEST_ADDOPTS="" fallback

### Business Constraints
- **Constitutional Mandate**: 100% test pass is absolute (Article II), no workarounds permitted
- **Audit Trail**: Claude co-authorship must be attributed for legal/licensing compliance
- **Cleanup SLA**: Worktrees must be removed within 24 hours to prevent disk exhaustion

---

## Risk Assessment

### High Risk Items
- **Risk 1**: Worktree not cleaned up after agent crash → orphaned directories consume disk space
  - *Mitigation*: Daily cron job scans for worktrees older than 24 hours, auto-removes if PR merged
- **Risk 2**: Pre-commit hook blocks agent commit in worktree due to test failures
  - *Mitigation*: Agent validates tests pass BEFORE attempting commit, uses --no-verify only if tests green

### Medium Risk Items
- **Risk 3**: GitHub API rate limit prevents PR creation during high-frequency agent execution
  - *Mitigation*: Implement exponential backoff retry logic, cache PR creation until rate limit reset
- **Risk 4**: Branch name collision if multiple agents work on same feature type
  - *Mitigation*: Include session_id or timestamp in branch name: `feat/jwt-auth-{session_id}`

### Constitutional Risks
- **Constitutional Risk 1**: Agent bypasses test validation by using --no-verify incorrectly (Article II violation)
  - *Mitigation*: Telemetry logs all --no-verify usage, QualityEnforcer agent audits for misuse
- **Constitutional Risk 2**: Incomplete cleanup violates Article I (context verification) by leaving stale branches
  - *Mitigation*: Cleanup automation retries on failure, alerts human if 3 attempts fail

---

## Integration Points

### Agent Integration
- **AgencyOSAgent**: Primary user of PR creation workflow for feature implementation
- **QualityEnforcer**: Validates constitutional compliance before PR creation
- **LearningAgent**: Stores successful PR patterns in VectorStore (branch names, commit structure)
- **MergerAgent**: Consumes PR URLs for automated merge coordination

### System Integration
- **Git (subprocess)**: Worktree creation, commit, push operations via Python `subprocess.run()`
- **GitHub CLI (subprocess)**: PR creation via `gh pr create`, status checks via `gh pr checks`
- **Telemetry**: Logs worktree lifecycle events (create, commit, PR, cleanup) for Article IV learning

### External Integration
- **GitHub Webhooks**: Triggers cleanup automation on PR merge event (optional, fallback to polling)
- **CI/CD Pipeline**: Validates test pass in isolated environment (GitHub Actions)

---

## Testing Strategy

### Test Categories
- **Unit Tests**: Worktree path generation, commit message template rendering, PR body template rendering (>95% coverage)
- **Integration Tests**: End-to-end workflow from worktree creation to PR URL returned (<10s timeout)
- **Constitutional Compliance Tests**: Validate Article II enforcement (test failure blocks PR), Article IV learning storage

### Test Data Requirements
- **Mock Git Repository**: Temporary directory with initialized git repo + worktree support
- **Mock GitHub API**: Stub responses for `gh pr create`, `gh pr checks` (no network calls in tests)
- **Test Session IDs**: Deterministic UUIDs for reproducible worktree path generation

### Test Environment Requirements
- **Local Git 2.30+**: Worktree commands available in test runner
- **GitHub CLI (mocked)**: Stub executable returns success responses
- **Isolated pytest runs**: Each test creates/removes temp directories (no cross-test pollution)

---

## Implementation Phases

### Phase 1: Worktree Isolation Core
- **Scope**: Implement worktree creation, branch naming, cleanup automation
- **Deliverables**:
  - `tools/git_worktree_manager.py` with `create_worktree()`, `cleanup_worktree()` functions
  - Unit tests (20 tests, 100% pass)
- **Success Criteria**:
  - Agent can create worktree, verify isolation (no file conflicts)
  - Cleanup removes worktree and prunes references

### Phase 2: Commit/PR Template Enforcement
- **Scope**: Implement commit message template, PR body template, constitutional validation
- **Deliverables**:
  - `tools/pr_template_generator.py` with `generate_commit_msg()`, `generate_pr_body()` functions
  - Integration with pre-commit hook for Co-Authored-By validation
  - Unit tests (15 tests, 100% pass)
- **Success Criteria**:
  - 100% commit messages include Co-Authored-By
  - 100% PR bodies include Summary, Test Plan, Constitutional Compliance sections

### Phase 3: Mergeability Checks & Learning Integration
- **Scope**: Implement test validation, CI status checks, VectorStore pattern storage
- **Deliverables**:
  - `tools/pr_mergeability_checker.py` with `validate_tests_pass()`, `check_ci_status()` functions
  - Learning integration in LearningAgent for PR pattern extraction
  - Integration tests (10 tests, 100% pass)
- **Success Criteria**:
  - 0 PRs created with failing tests (constitutional enforcement)
  - Successful PR patterns stored in VectorStore for reuse

---

## Review & Approval

### Stakeholders
- **Primary Stakeholder**: @am (repository owner, constitutional authority)
- **Secondary Stakeholders**: AgencyOSAgent, QualityEnforcer, LearningAgent (workflow consumers)
- **Technical Reviewers**: ChiefArchitect (ADR alignment), PlannerAgent (spec completeness)

### Review Criteria
- [x] **Completeness**: All sections filled with appropriate detail (worktree mechanics, templates, checks)
- [x] **Clarity**: Requirements are unambiguous and testable (acceptance criteria measurable)
- [x] **Feasibility**: Technical implementation is realistic (uses standard Git/GH CLI tools)
- [x] **Constitutional Compliance**: Aligns with all constitutional articles (Article II enforcement explicit)
- [x] **Quality Standards**: Meets Agency quality requirements (>95% test coverage, <50 line functions)

### Approval Status
- [ ] **Stakeholder Approval**: [Pending @am review]
- [ ] **Technical Approval**: [Pending ChiefArchitect review]
- [ ] **Constitutional Compliance**: [Pending QualityEnforcer validation]
- [ ] **Final Approval**: [Pending after all approvals received]

---

## Appendices

### Appendix A: Glossary
- **Worktree**: Git feature allowing multiple working directories for same repository (shared .git database)
- **Bare Repository**: Git repo with no working directory (only .git database), requires worktree for file operations
- **Pre-commit Hook**: Git hook executing before commit (validates tests, linting, constitutional compliance)
- **Branch Protection**: GitHub repository setting enforcing required reviews, status checks before merge
- **Constitutional Compliance**: Adherence to Agency Constitution Articles I-V (mandatory for all operations)

### Appendix B: References
- **Git Worktree Documentation**: https://git-scm.com/docs/git-worktree
- **GitHub CLI Documentation**: https://cli.github.com/manual/gh_pr_create
- **Conventional Commits**: https://www.conventionalcommits.org/ (inspiration for commit message format)

### Appendix C: Related Documents
- **ADR-001**: Complete Context Before Action (worktree creation validation)
- **ADR-002**: 100% Verification and Stability (test pass requirement)
- **ADR-003**: Automated Merge Enforcement (branch protection, no bypass)
- **ADR-004**: Continuous Learning (PR pattern storage in VectorStore)
- **Constitution Article II**: 100% test pass mandate (primary enforcement point)
- **CLAUDE.md**: Git Worktree Isolation section (lines 60-140, workflow overview)

---

## Detailed Workflow Specification

### Worktree Creation Pattern

```python
# tools/git_worktree_manager.py
from pathlib import Path
from typing import Result
import subprocess
import uuid

def create_worktree(
    task_description: str,
    session_id: str | None = None,
    branch_type: str = "feat"
) -> Result[Path, str]:
    """
    Create isolated Git worktree for autonomous agent execution.

    Args:
        task_description: Kebab-case task name (e.g., "jwt-authentication")
        session_id: Optional session identifier (default: UUID4)
        branch_type: One of feat|fix|refactor|docs|test

    Returns:
        Result with worktree path on success, error message on failure

    Example:
        >>> result = create_worktree("jwt-auth", branch_type="feat")
        >>> worktree_path = result.unwrap()  # /Users/am/Code/Agency-abc123/
    """
    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    # Construct worktree path
    repo_root = Path.cwd()
    worktree_path = repo_root.parent / f"Agency-{session_id}"

    # Construct branch name
    branch_name = f"{branch_type}/{task_description}"

    # Verify main .git database exists (Article I: Complete Context)
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return Err(f"Git database not found at {git_dir}")

    # Create worktree
    try:
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return Err(f"Worktree creation failed: {result.stderr}")

        # Log success to telemetry (Article IV: Learning)
        log_worktree_event("created", worktree_path, branch_name)

        return Ok(worktree_path)

    except subprocess.TimeoutExpired:
        return Err("Worktree creation timed out (>10s)")
```

### Commit Message Template

```python
# tools/pr_template_generator.py
from typing import Literal

CommitType = Literal["feat", "fix", "refactor", "docs", "test", "style", "chore"]

def generate_commit_message(
    commit_type: CommitType,
    title: str,
    body: str,
    breaking_change: bool = False
) -> str:
    """
    Generate standardized commit message with Claude co-authorship.

    Args:
        commit_type: Type of change (feat, fix, etc.)
        title: Imperative mood title (e.g., "Add JWT authentication")
        body: Explanation of WHY (context, rationale)
        breaking_change: Whether this is a breaking API change

    Returns:
        Formatted commit message with Co-Authored-By footer

    Example:
        >>> msg = generate_commit_message(
        ...     "feat",
        ...     "Add JWT authentication",
        ...     "Enables secure API access with token-based auth"
        ... )
        >>> print(msg)
        feat: Add JWT authentication

        Enables secure API access with token-based auth

        Co-Authored-By: Claude <noreply@anthropic.com>
    """
    # Validate title is imperative mood (simple heuristic: no past tense markers)
    if any(word in title.lower() for word in ["added", "fixed", "updated", "removed"]):
        raise ValueError(f"Title must be imperative mood: '{title}' appears past tense")

    # Construct message
    lines = [f"{commit_type}: {title}"]

    if breaking_change:
        lines.append("\nBREAKING CHANGE: " + body)
    else:
        lines.append("\n" + body)

    # Mandatory Claude attribution (constitutional requirement)
    lines.append("\nCo-Authored-By: Claude <noreply@anthropic.com>")

    return "\n".join(lines)
```

### PR Body Template

```python
def generate_pr_body(
    summary: str,
    key_changes: list[str],
    test_results: dict[str, int],
    constitutional_evidence: dict[str, str]
) -> str:
    """
    Generate standardized PR body with constitutional compliance checklist.

    Args:
        summary: 2-3 sentence overview of changes
        key_changes: Bullet points of major changes
        test_results: Dict of test suite results (e.g., {"unit": 47, "integration": 12})
        constitutional_evidence: Dict of Article → evidence mappings

    Returns:
        Formatted PR body with Summary, Test Plan, Constitutional Compliance sections

    Example:
        >>> body = generate_pr_body(
        ...     "Implements JWT authentication for API access",
        ...     ["Add JWTAuthenticator class", "Update auth middleware"],
        ...     {"unit": 47, "integration": 12},
        ...     {
        ...         "Article I": "All context gathered from existing auth system",
        ...         "Article II": "100% test pass (59/59 tests)"
        ...     }
        ... )
    """
    lines = ["## Summary", ""]
    lines.append(summary)
    lines.append("")

    lines.append("**Key Changes:**")
    for change in key_changes:
        lines.append(f"- {change}")
    lines.append("")

    lines.append("## Test Plan")
    lines.append("")
    total_tests = sum(test_results.values())
    for suite, count in test_results.items():
        lines.append(f"- [x] {suite.capitalize()} tests pass ({count}/{count})")
    lines.append(f"- [x] **Total: {total_tests}/{total_tests} tests pass (100%)**")
    lines.append("")

    lines.append("## Constitutional Compliance")
    lines.append("")
    for article, evidence in constitutional_evidence.items():
        lines.append(f"- [x] **{article}**: {evidence}")
    lines.append("")

    lines.append("---")
    lines.append("🤖 Generated with [Claude Code](https://claude.com/claude-code)")

    return "\n".join(lines)
```

### Mergeability Checker

```python
# tools/pr_mergeability_checker.py
import subprocess
from typing import Result

def validate_tests_pass() -> Result[None, str]:
    """
    Validate 100% test pass requirement (Article II enforcement).

    Returns:
        Ok(None) if all tests pass, Err(message) if any failures

    Raises:
        Never - uses Result pattern for error handling
    """
    try:
        result = subprocess.run(
            ["python", "run_tests.py", "--run-all"],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for full suite
        )

        if result.returncode != 0:
            # Parse failure count from output
            output = result.stdout + result.stderr
            return Err(f"Test failures detected:\n{output}")

        # Verify 100% pass in output (constitutional requirement)
        if "100%" not in result.stdout:
            return Err("Test output does not confirm 100% pass rate")

        return Ok(None)

    except subprocess.TimeoutExpired:
        return Err("Test execution timed out (>10 minutes)")

def check_merge_conflicts() -> Result[None, str]:
    """
    Check for merge conflicts with main branch.

    Returns:
        Ok(None) if no conflicts, Err(message) if conflicts detected
    """
    try:
        # Fetch latest main
        subprocess.run(["git", "fetch", "origin", "main"], check=True, timeout=30)

        # Attempt dry-run merge
        result = subprocess.run(
            ["git", "merge", "--no-commit", "--no-ff", "origin/main"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Abort the dry-run merge
        subprocess.run(["git", "merge", "--abort"], timeout=5)

        if result.returncode != 0:
            return Err(f"Merge conflicts detected with main:\n{result.stderr}")

        return Ok(None)

    except subprocess.CalledProcessError as e:
        return Err(f"Git command failed: {e}")

def check_ci_status(pr_number: int) -> Result[None, str]:
    """
    Check CI pipeline status for PR.

    Args:
        pr_number: GitHub PR number

    Returns:
        Ok(None) if all CI checks pass, Err(message) if any failures
    """
    try:
        result = subprocess.run(
            ["gh", "pr", "checks", str(pr_number)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return Err(f"CI checks failed:\n{result.stdout}")

        # Verify all checks passing
        if "fail" in result.stdout.lower():
            return Err(f"Some CI checks failed:\n{result.stdout}")

        return Ok(None)

    except subprocess.TimeoutExpired:
        return Err("CI status check timed out (>30s)")
```

### Cleanup Automation

```python
# tools/git_worktree_manager.py (continued)
def cleanup_worktree(
    worktree_path: Path,
    branch_name: str,
    force: bool = False
) -> Result[None, str]:
    """
    Remove worktree and cleanup Git references after PR merge.

    Args:
        worktree_path: Path to worktree directory
        branch_name: Git branch name to delete
        force: Whether to force removal (ignore uncommitted changes)

    Returns:
        Ok(None) on success, Err(message) on failure

    Example:
        >>> cleanup_worktree(Path("/Users/am/Code/Agency-abc123"), "feat/jwt-auth")
    """
    try:
        # Remove worktree
        force_flag = ["--force"] if force else []
        result = subprocess.run(
            ["git", "worktree", "remove", str(worktree_path)] + force_flag,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return Err(f"Worktree removal failed: {result.stderr}")

        # Prune references
        subprocess.run(["git", "worktree", "prune"], timeout=5, check=True)

        # Delete merged branch (fails if not merged, use -D for force)
        branch_delete_flag = "-D" if force else "-d"
        result = subprocess.run(
            ["git", "branch", branch_delete_flag, branch_name],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return Err(f"Branch deletion failed: {result.stderr}")

        # Log success to telemetry (Article IV: Learning)
        log_worktree_event("cleaned_up", worktree_path, branch_name)

        return Ok(None)

    except subprocess.TimeoutExpired:
        return Err("Cleanup operation timed out")

def detect_merged_prs() -> list[tuple[int, str, Path]]:
    """
    Detect merged PRs with worktrees still present (requires cleanup).

    Returns:
        List of (pr_number, branch_name, worktree_path) tuples

    Example:
        >>> merged = detect_merged_prs()
        >>> for pr_num, branch, path in merged:
        ...     cleanup_worktree(path, branch)
    """
    # List all worktrees
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=10
    )

    worktrees = []
    current_worktree = {}

    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            if current_worktree:
                worktrees.append(current_worktree)
            current_worktree = {"path": Path(line.split(" ", 1)[1])}
        elif line.startswith("branch "):
            current_worktree["branch"] = line.split(" ", 1)[1]

    if current_worktree:
        worktrees.append(current_worktree)

    # Check each worktree for merged PR
    merged = []
    for wt in worktrees:
        if "branch" not in wt:
            continue

        branch = wt["branch"].replace("refs/heads/", "")

        # Check if branch merged to main
        result = subprocess.run(
            ["git", "branch", "-r", "--merged", "origin/main"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if f"origin/{branch}" in result.stdout:
            # Find PR number via gh CLI
            pr_result = subprocess.run(
                ["gh", "pr", "list", "--state", "merged", "--head", branch, "--json", "number"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if pr_result.returncode == 0:
                import json
                prs = json.loads(pr_result.stdout)
                if prs:
                    merged.append((prs[0]["number"], branch, wt["path"]))

    return merged
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-11 | PlannerAgent | Initial specification with complete workflow definition |

---

*"A specification is a contract between intention and implementation."*
