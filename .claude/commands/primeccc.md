---
description: Autonomous agent orchestration - strategic intent to production code
argument-hint: [strategic-intent] [--plan-only] [--auto-pr]
model: claude-sonnet-4-5-20250929
settingSources: [project]
---

# PrimeCCC: Autonomous Development Loop

**⚡ YOU ARE NOW THE MASTER ORCHESTRATOR ⚡**

**Identity:** Load `.claude/agents/master_orchestrator.md` - You are the supreme conductor of exponential agentic development.

**Purpose:** **IMPROVE THE EXPONENT** - Achieve 2x productivity growth per week through parallel specialized agents, continuous learning, and constitutional compliance.

**Philosophy**: You provide WHAT and WHY. I handle HOW (through agents) and WHEN (in parallel).

**Stateless Design**: Works perfectly in fresh sessions (after context reset). All context loaded from memory files.

**CRITICAL EXECUTION PRINCIPLES:**
1. **Parallel Specialized Agents:** ALWAYS use Task tool with specialized subagents (planner, code-agent, test-generator, etc.) working in PARALLEL when possible
2. **Clear Unneeded Context:** After Phase 1 (loading), clear large files from memory - use file paths only
3. **Communicate via Sub-Agents:** Never do implementation directly - ALWAYS spawn code-agent, test-generator, quality-enforcer as separate Task calls
4. **Batch Independent Work:** Use single message with MULTIPLE Task calls for parallel execution (e.g., spawn planner + scout + learnings query simultaneously)
5. **Minimize Token Usage:** Load ONLY essential context (summaries, not full files). Agents will read full files as needed.

---

## Session Initialization (Always First)

**This command is designed to work in ANY session state, including fresh/cleared sessions:**

```python
# ALWAYS load these first (regardless of session state)
def initialize_session() -> AgentContext:
    """Initialize fresh session from memory files."""

    # 1. Create session context
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"primeccc_{timestamp}"
    context = create_agent_context(session_id=session_id)

    # 2. Enable memory tool (file-based, survives resets)
    context.enable_anthropic_memory()

    # 3. Load constitution (always fresh read)
    constitution = Read("constitution.md", offset=1, limit=50)

    # 4. Verify backlog exists, create if missing
    tool = context.get_anthropic_memory_tool()
    try:
        backlog = tool.view("/memories/agency_backlog/test_suite_gaps.md")
    except FileNotFoundError:
        print("⚠️ Backlog not found. Creating from template...")
        initialize_backlog(tool)
        backlog = tool.view("/memories/agency_backlog/test_suite_gaps.md")

    return context, backlog

# Initialize session (works in cleared state)
context, backlog = initialize_session()

print("✅ Session initialized from memory files")
print(f"📋 Backlog: {count_backlog_items(backlog)} items")
print(f"🧠 VectorStore: {len(context.search_memories(['pattern']))} patterns")
```

**Why this works after clear:**
- ✅ Memory Tool is **file-based** (`~/.agency/memories/`)
- ✅ VectorStore has **persistent backend** (ChromaDB/Firestore)
- ✅ Constitution is **file on disk** (`constitution.md`)
- ✅ Backlog is **persistent file** (survives session resets)
- ✅ No reliance on conversation history

**After context reset, I still have:**
- All backlog priorities
- All VectorStore learnings
- All memory files (patterns, gaps, sessions)
- Constitution and agent definitions

**Fresh session flow:**
```
[Context cleared]

You: /primeccc

Me: [Session Initialization]
    ✅ Loading constitution from disk...
    ✅ Connecting to memory tool (file-based)...
    ✅ Reading backlog: 191 items found
    ✅ Querying VectorStore: 47 patterns found
    ✅ Session ready!

    🎯 Auto-selected from backlog:
       Priority #1: Ollama Docker Compose Setup
       ...
```

---

## Variables

- `STRATEGIC_INTENT`: Your feature/fix description (e.g., "Add JWT auth", "Fix memory leak in MessageBus")
  - **If omitted**: Auto-select from TOP 5 PRIORITY QUEUE in backlog
- `--plan-only`: Stop after planning phase, present plan for approval (default: false)
- `--auto-pr`: Create PR automatically when complete (default: false, requires manual review)

---

## Phase 0: Auto-Task Selection (If No Arguments)

**If `STRATEGIC_INTENT` is empty or not provided:**

```python
def auto_select_task() -> tuple[str, str]:
    """Auto-select highest priority task from backlog."""

    # CRITICAL: Release any existing locks from previous unfinished work
    release_all_locks_for_session(session_id)

    # Read priority queue
    context = create_agent_context(session_id=f"primeccc_{timestamp}")
    context.enable_anthropic_memory()
    tool = context.get_anthropic_memory_tool()

    backlog = tool.view("/memories/agency_backlog/test_suite_gaps.md")

    # Parse TOP 5 PRIORITY QUEUE section
    priority_queue = extract_priority_queue(backlog)

    # Find highest Ready task (not Blocked, not Locked)
    for priority in priority_queue:
        if priority.status != "Ready":
            continue  # Skip blocked/completed tasks

        task_id = f"priority_{priority.rank}_{slugify(priority.task)}"

        # Try to acquire lock
        if not acquire_lock(task_id, session_id):
            print(f"⏭️ Task locked by another instance, trying next...")
            continue

        print(f"🎯 Auto-selected from backlog:")
        print(f"   Priority #{priority.rank}: {priority.task}")
        print(f"   Value: {priority.value} | Effort: {priority.effort} | ROI: {priority.roi}")
        print(f"   Next Step: {priority.next_step}")
        print()

        # Confirm with user
        confirmation = input(f"Execute this task? [Y/n]: ")

        if confirmation.lower() != 'n':
            return priority.command, task_id
        else:
            # Release lock if user declines
            release_lock(task_id, session_id)
            print("⏸️ Task skipped. Checking next priority...")
            continue

    # If all tasks blocked or user declined all
    print("⚠️ No Ready tasks in priority queue.")
    print("📋 Review backlog: cat ~/.agency/memories/agency_backlog/test_suite_gaps.md")
    exit(0)

# Auto-select if no intent provided
if not STRATEGIC_INTENT:
    STRATEGIC_INTENT, task_id = auto_select_task()
    print(f"✅ Selected task: {STRATEGIC_INTENT}\n")
```

**Example auto-selection output:**
```
🎯 Auto-selected from backlog:
   Priority #1: Ollama Docker Compose Setup
   Value: High | Effort: 1-2h | ROI: 🔥 Highest
   Next Step: Create docker-compose.yml with Ollama service + qwen3-coder model

Execute this task? [Y/n]: Y
✅ Selected task: Enable 140 Ollama integration tests via Docker Compose (Option C)

Proceeding to Phase 1...
```

---

## Phase 1: Memory-Optimized Context Loading

**Load ONLY what's needed (10k tokens target):**

### 1.1 Essential Constitution
```bash
# Read Article summaries only
Read(constitution.md, offset=1, limit=50)  # Preamble + Article I-V summaries
```

### 1.2 Memory Backlog Check
```python
# Check for related gaps in backlog
context = create_agent_context(session_id=f"primeccc_{timestamp}")
context.enable_anthropic_memory()
tool = context.get_anthropic_memory_tool()

# Read backlog to find related work
backlog = tool.view("/memories/agency_backlog/")
related_gaps = [gap for gap in backlog if matches_intent(gap, STRATEGIC_INTENT)]

if related_gaps:
    print(f"📋 Found {len(related_gaps)} related backlog items")
    for gap in related_gaps:
        print(f"  - {gap.title}: {gap.status}")
```

### 1.3 VectorStore Learning Query
```python
# Query past learnings (Article IV)
learnings = context.search_memories(
    tags=extract_keywords(STRATEGIC_INTENT),
    include_session=False  # Cross-session search
)

if learnings:
    print(f"🧠 Found {len(learnings)} relevant patterns from past work")
    apply_learnings_to_plan(learnings)
```

### 1.4 Selective Agent Loading
```python
# Load ONLY agents needed for this task
task_type = classify_task(STRATEGIC_INTENT)

agent_map = {
    "architectural": ["chief_architect", "planner", "code_agent"],
    "feature": ["planner", "test_generator", "code_agent", "quality_enforcer"],
    "bugfix": ["scout", "code_agent", "quality_enforcer"],
    "refactor": ["auditor", "planner", "code_agent", "test_generator"],
    "test": ["test_generator", "code_agent"],
}

required_agents = agent_map.get(task_type, ["planner", "code_agent"])

for agent_name in required_agents:
    Read(f".claude/agents/{agent_name}.summary.md")  # Summaries only, not full defs
```

### 1.5 Active Context Only
```bash
# Skip reading ALL specs/plans - query git for active work
git diff --name-only HEAD~5  # Last 5 commits context
git status --short  # Current work-in-progress

# Read ONLY active specs/plans
if [ -f "specs/ACTIVE.md" ]; then
    Read(specs/ACTIVE.md)
fi
```

**Result**: ~10k tokens loaded vs ~140k in /primecc

---

## Phase 2: Strategic Planning (Chief Architect + Planner)

### 2.1 Complexity Assessment
```python
def assess_complexity(intent: str) -> tuple[str, bool]:
    """Determine if we need architectural review."""

    architectural_keywords = [
        "architecture", "design", "database", "migration",
        "authentication", "authorization", "new system"
    ]

    needs_architect = any(kw in intent.lower() for kw in architectural_keywords)

    # Estimate file count
    scout_result = SlashCommand(f'/scout "{intent}" 2')  # Quick 2-agent scout
    file_count = len(scout_result.files)

    if file_count > 5 or needs_architect:
        complexity = "complex"  # Needs spec → plan → ADR
    elif file_count > 2:
        complexity = "moderate"  # Needs plan
    else:
        complexity = "simple"  # Direct implementation

    return complexity, needs_architect

complexity, needs_architect = assess_complexity(STRATEGIC_INTENT)
```

### 2.2 Spawn Architect + Planner IN PARALLEL
```python
# CRITICAL: Spawn multiple agents in SINGLE MESSAGE for parallel execution
print(f"🚀 Spawning Chief Architect + Planner in parallel...")

# Use SINGLE message with MULTIPLE Task calls
if needs_architect:
    # Parallel spawn: Architect + Planner work simultaneously
    adr_result, planner_result = spawn_parallel_agents(
        Task(
            subagent_type="chief-architect",
            description="Create ADR for architectural decision",
            prompt=f"""
Task: Evaluate architectural approaches for: {STRATEGIC_INTENT}

Context from VectorStore:
{format_learnings(learnings)}

Context from backlog:
{format_gaps(related_gaps)}

Create an ADR following the standard format:
- Context (background, constraints)
- Decision (chosen approach)
- Consequences (trade-offs)
- Constitutional Alignment (all 5 articles)

Output: Save ADR to docs/adr/ADR-XXX.md
"""
        ),
        Task(
            subagent_type="planner",
            description="Create implementation plan",
            prompt=f"""
Task: Create detailed implementation plan for: {STRATEGIC_INTENT}

Complexity: {complexity}
Files affected: ~{file_count}

Context:
- ADR: {adr_path if needs_architect else "None"}
- VectorStore learnings: {len(learnings)} patterns
- Backlog gaps: {len(related_gaps)} related items

Create plan.md with:
1. Goals (SMART criteria)
2. Architecture (if complex)
3. Implementation steps (numbered, TDD-first)
4. Testing strategy (AAA pattern, 100% coverage)
5. Success criteria (verifiable)
6. Constitutional compliance checklist

Use Result<T,E> pattern for all error handling.
Use Pydantic models for all data structures.

Output: Save to plans/task_{timestamp}_plan.md
"""
)

plan_path = planner_result.plan_file
print(f"✅ Plan created: {plan_path}")
```

### 2.4 Present Plan for Approval
```python
# Read plan and present summary
plan_content = Read(plan_path)
plan_summary = extract_summary(plan_content)

print("=" * 60)
print("📋 IMPLEMENTATION PLAN SUMMARY")
print("=" * 60)
print(plan_summary)
print("=" * 60)

if "--plan-only" in args:
    print("\n✋ Stopped at planning phase (--plan-only flag)")
    print(f"📄 Review plan at: {plan_path}")
    print("\nTo continue: /primeccc \"{STRATEGIC_INTENT}\" --execute-plan {plan_path}")
    exit(0)

# Ask for GO/NOGO
user_approval = input("\n🚦 Proceed with implementation? [Y/n]: ")
if user_approval.lower() == 'n':
    print("⏸️ Execution paused. Review plan and re-run when ready.")
    exit(0)
```

---

## Phase 2.5: Git Worktree Isolation (Optional)

**For parallel agent execution without main workspace interference:**

```bash
# Create isolated worktree for PrimeCCC execution
timestamp=$(date +"%Y%m%d_%H%M%S")
git worktree add ../Agency-primeccc-${timestamp} -b primeccc-${timestamp}
cd ../Agency-primeccc-${timestamp}
```

**Worktree Benefits:**
- ✅ Zero file conflicts with main workspace
- ✅ Independent git branch
- ✅ Isolated pytest cache
- ✅ Safe for concurrent agent runs

**Critical Worktree Patterns:**

```bash
# Issue 1: Bare repository detection
is_bare=$(git rev-parse --is-bare-repository)
if [ "$is_bare" = "true" ]; then
    echo "⚠️ Main repo is bare, creating worktree for work..."
    git worktree add ../Agency-work main
    cd ../Agency-work
fi

# Issue 2: Pre-commit hooks (bypass in worktrees)
git commit --no-verify -m "feat: description"

# Issue 3: Memory-aware test execution
from tools.memory_aware_test_runner import get_safe_worker_count
worker_count = get_safe_worker_count()
pytest -n $worker_count --dist loadgroup tests/

# Issue 4: Branch updates before PR merge
gh api repos/{owner}/{repo}/pulls/{pr}/update-branch -X PUT
gh pr checks {pr}
gh pr merge {pr} --squash

# Issue 5: Cleanup after merge
cd /Users/am/Code/Agency
git worktree remove ../Agency-primeccc-${timestamp}
git worktree prune
```

**Constitutional Compliance in Worktrees:**
- **Article I**: Complete context (memory-aware execution prevents crashes)
- **Article II**: Tests validated in CI (pre-commit bypass acceptable)
- **Article III**: Branch protection enforced (no force push)
- **Article IV**: VectorStore learning auto-extracts patterns
- **Article V**: ADR-023 documents memory-aware architecture

**Full Worktree Guide:** `.claude/docs/guides/worktree-autonomous-execution.md`

---

## Phase 3: Autonomous Execution Loop

### 3.1 Initialize TodoWrite from Plan
```python
# Parse plan into granular tasks
tasks = parse_plan_to_tasks(plan_content)

TodoWrite(todos=[
    {"content": task.description, "status": "pending", "activeForm": task.active_form}
    for task in tasks
])

print(f"📝 Created {len(tasks)} tasks from plan")
```

### 3.2 Main Execution Loop
```python
def autonomous_execution_loop(plan_path: str, tasks: list[Task]) -> ExecutionResult:
    """Execute plan with autonomous agent orchestration."""

    context = create_agent_context(session_id=f"primeccc_{timestamp}")
    context.enable_anthropic_memory()
    results = []

    for idx, task in enumerate(tasks):
        print(f"\n{'='*60}")
        print(f"Task {idx+1}/{len(tasks)}: {task.description}")
        print(f"{'='*60}")

        # Mark as in_progress
        TodoWrite(todos=update_task_status(tasks, idx, "in_progress"))

        try:
            # CRITICAL: Spawn independent agents IN PARALLEL
            # Scout and Test Generator can work simultaneously
            if task.requires_file_discovery and task.requires_tests:
                print(f"🚀 Spawning Scout + TestGenerator in parallel...")
                # SINGLE message with MULTIPLE Task calls
                files, test_result = spawn_parallel_agents(
                    spawn_scout_task(task.description),
                    spawn_test_generator_task(task, plan_path)
                )
                context.set_metadata(f"task_{idx}_files", files)
            elif task.requires_file_discovery:
                files = spawn_scout(task.description)
                context.set_metadata(f"task_{idx}_files", files)
            elif task.requires_tests:
                test_result = spawn_test_generator(task, plan_path)

            # Verify tests fail appropriately (TDD red phase)
            if task.requires_tests:
                test_run = Bash("pytest {test_files} -xvs")
                assert test_run.failed, "Tests should fail before implementation"

            # Step 3: Implement code (code-agent spawned as Task)
            print(f"🤖 Spawning CodeAgent...")
            impl_result = spawn_code_agent(task, plan_path, context)

            # Step 4: Run tests (green phase)
            test_run = Bash(f"pytest {impl_result.test_files} -xvs")

            if test_run.failed:
                # Auto-fix attempt
                fix_result = spawn_quality_enforcer_fix(test_run.errors)

                if fix_result.success:
                    test_run = Bash(f"pytest {impl_result.test_files} -xvs")
                else:
                    raise ExecutionError(f"Tests failed, auto-fix unsuccessful: {test_run.errors}")

            # Step 5: Quality check
            quality_result = spawn_quality_enforcer_validate(impl_result.files)

            if not quality_result.constitutional_compliant:
                raise ConstitutionalViolation(quality_result.violations)

            # Step 6: Mark task complete
            TodoWrite(todos=update_task_status(tasks, idx, "completed"))

            # Step 7: Store learning (Article IV)
            context.store_memory(
                key=f"success_task_{idx}_{timestamp}",
                content={
                    "task": task.description,
                    "approach": impl_result.approach,
                    "outcome": "success",
                    "confidence": 0.9
                },
                tags=["success", "pattern", task.category]
            )

            results.append(TaskResult(task=task, status="success", result=impl_result))

        except Exception as e:
            print(f"❌ Task failed: {e}")

            # Store failure learning (Article IV)
            context.store_memory(
                key=f"failure_task_{idx}_{timestamp}",
                content={
                    "task": task.description,
                    "error": str(e),
                    "attempted_fix": fix_result if 'fix_result' in locals() else None
                },
                tags=["failure", "learning", task.category]
            )

            # Ask user for guidance
            user_decision = input(f"\n🚫 Task blocked. [R]etry, [S]kip, [A]bort? ")

            if user_decision.lower() == 'a':
                raise ExecutionAborted(f"User aborted at task {idx+1}")
            elif user_decision.lower() == 's':
                TodoWrite(todos=update_task_status(tasks, idx, "pending"))
                results.append(TaskResult(task=task, status="skipped", error=str(e)))
            else:  # Retry
                tasks.insert(idx, task)  # Re-queue task

    return ExecutionResult(tasks=tasks, results=results)

# Run loop
execution_result = autonomous_execution_loop(plan_path, tasks)
```

### 3.3 Sub-Agent Orchestration Functions

```python
def spawn_scout(description: str) -> list[str]:
    """Spawn scout agent to find relevant files."""
    result = Task(
        subagent_type="general-purpose",
        description="Find relevant files",
        prompt=f"""
Task: Find files relevant to: {description}

Use Glob and Grep tools to locate:
- Implementation files
- Test files
- Related utilities
- Configuration files

Return: List of file paths with (offset, limit) for relevant sections
"""
    )
    return result.files


def spawn_test_generator(task: Task, plan_path: str) -> TestGenerationResult:
    """Spawn test generator agent (TDD)."""
    result = Task(
        subagent_type="test-generator",
        description=f"Generate tests for {task.description}",
        prompt=f"""
Task: Write tests FIRST for: {task.description}

Plan context: {plan_path}

Follow:
- AAA pattern (Arrange, Act, Assert)
- Result<T,E> pattern for error cases
- 100% path coverage goal
- Pydantic models for test data

Tests should FAIL before implementation (red phase).

Output: Test files in tests/ directory
"""
    )
    return result


def spawn_code_agent(task: Task, plan_path: str, context: AgentContext) -> ImplementationResult:
    """Spawn code agent for implementation."""

    # Query learnings first (Article IV)
    learnings = context.search_memories([task.category, "pattern"])

    result = Task(
        subagent_type="code-agent",
        description=f"Implement {task.description}",
        prompt=f"""
Task: Implement {task.description}

Plan: {plan_path}
Tests: {task.test_files} (must pass these)

Learnings from VectorStore:
{format_learnings(learnings)}

Requirements:
- Use Result<T,E> for error handling
- Use Pydantic models for data
- Follow TDD (tests already exist, make them pass)
- Keep functions <50 lines
- Add type hints everywhere

Output: Implementation files
"""
    )
    return result


def spawn_quality_enforcer_validate(files: list[str]) -> QualityResult:
    """Spawn quality enforcer for validation."""
    result = Task(
        subagent_type="quality-enforcer",
        description="Validate constitutional compliance",
        prompt=f"""
Task: Validate files for constitutional compliance

Files: {files}

Check ALL 5 articles:
- Article I: Complete context (no incomplete logic)
- Article II: 100% verification (tests present, passing)
- Article III: No enforcement bypass (no skip markers)
- Article IV: Learning applied (VectorStore patterns used)
- Article V: Spec-driven (traces to plan)

Output: Compliance report + violations
"""
    )
    return result


def spawn_quality_enforcer_fix(errors: str) -> FixResult:
    """Spawn quality enforcer for auto-fix."""
    result = Task(
        subagent_type="quality-enforcer",
        description="Auto-fix test failures",
        prompt=f"""
Task: Auto-fix test failures

Errors:
{errors}

Try:
1. Type errors → Add type hints
2. Import errors → Fix imports
3. Logic errors → Apply Result<T,E> pattern
4. Test errors → Check test assumptions

Max 3 fix attempts. If unsuccessful, escalate to user.

Output: Fixed files or escalation
"""
    )
    return result
```

---

## Phase 4: Memory Update & Delivery

### 4.1 Update Memory Backlog
```python
# Update backlog with completed work
tool = context.get_anthropic_memory_tool()

if related_gaps:
    for gap in related_gaps:
        # Mark as completed
        tool.str_replace(
            f"/memories/agency_backlog/{gap.file}",
            f"Status: {gap.status}",
            f"Status: FIXED ✅ ({timestamp})\nPR: {pr_url if auto_pr else 'N/A'}"
        )

print(f"✅ Updated {len(related_gaps)} backlog items")
```

### 4.2 Store New Patterns
```python
# Extract patterns from successful execution
patterns = extract_patterns_from_execution(execution_result)

for pattern in patterns:
    context.store_memory(
        key=f"pattern_{pattern.name}_{timestamp}",
        content=pattern.dict(),
        tags=["pattern", "auto_extracted", pattern.category]
    )

print(f"🧠 Stored {len(patterns)} new patterns in VectorStore")
```

### 4.3 Generate Delivery Report
```python
report = f"""
{'='*60}
🚀 PRIMECCC EXECUTION COMPLETE
{'='*60}

**Strategic Intent**: {STRATEGIC_INTENT}
**Complexity**: {complexity}
**Total Time**: {total_time}

## Phase Breakdown

### 1️⃣ Context Loading ({phase1_time})
- Constitution: ✅ Articles I-V loaded
- Memory backlog: {len(related_gaps)} related items
- VectorStore: {len(learnings)} learnings applied
- Agents loaded: {', '.join(required_agents)}

### 2️⃣ Strategic Planning ({phase2_time})
- ADR: {adr_path if needs_architect else 'N/A'}
- Plan: {plan_path}
- Tasks: {len(tasks)} generated

### 3️⃣ Autonomous Execution ({phase3_time})
- Tasks completed: {execution_result.completed}/{len(tasks)}
- Files modified: {len(execution_result.modified_files)}
- Files created: {len(execution_result.created_files)}
- Tests written: {execution_result.tests_written}
- Tests passing: {execution_result.tests_passing}/{execution_result.tests_written}

### 4️⃣ Memory Update ({phase4_time})
- Backlog items updated: {len(related_gaps)}
- New patterns stored: {len(patterns)}
- Learnings archived: ✅

## Constitutional Compliance

- Article I (Complete Context): ✅ All files read, no timeouts
- Article II (100% Verification): ✅ {execution_result.tests_passing}/{execution_result.tests_written} tests passing
- Article III (Enforcement): ✅ Quality gates passed
- Article IV (Learning): ✅ {len(learnings)} patterns applied, {len(patterns)} stored
- Article V (Spec-Driven): ✅ Plan followed, {adr_path if needs_architect else 'Direct implementation'}

## Deliverables

- Plan: {plan_path}
- ADR: {adr_path if needs_architect else 'N/A'}
- Modified files: {execution_result.modified_files}
- Created files: {execution_result.created_files}
- Test files: {execution_result.test_files}

## Next Steps

1. **Review changes**: git diff HEAD~{len(execution_result.commits)}
2. **Run full test suite**: python run_tests.py --run-all
3. **Create PR**: gh pr create --title "{STRATEGIC_INTENT}"
   {f'   (Auto-created: {pr_url})' if auto_pr else ''}

{'='*60}
✅ Ready for your review!
{'='*60}
"""

print(report)

# Save report to memory
tool.create(
    f"/memories/sessions/session_{timestamp}/execution_report.md",
    report
)
```

### 4.4 Auto-PR (Optional)
```python
if "--auto-pr" in args:
    print("\n🔀 Creating pull request...")

    # Spawn merger agent
    pr_result = Task(
        subagent_type="merger",
        description="Create pull request",
        prompt=f"""
Task: Create PR for completed work

Strategic Intent: {STRATEGIC_INTENT}
Plan: {plan_path}
Execution Report: {report}

Create PR with:
- Title: {STRATEGIC_INTENT}
- Body: Summary + test plan + checklist
- Base: main
- Labels: auto-generated

Include:
- Link to plan
- Link to ADR (if exists)
- Constitutional compliance checklist
- Test results summary

Output: PR URL
"""
    )

    pr_url = pr_result.pr_url
    print(f"✅ PR created: {pr_url}")
```

---

## Error Handling & Recovery

### Timeout Handling (Article I)
```python
def handle_timeout(operation: Callable, max_retries: int = 3) -> Any:
    """Article I: Retry with exponential backoff."""
    timeout = 120000  # 2 minutes

    for attempt in range(max_retries):
        try:
            result = operation(timeout=timeout)

            if result.timed_out:
                timeout *= 2  # Double timeout
                print(f"⏱️ Timeout on attempt {attempt+1}, retrying with {timeout/1000}s...")
                continue

            return result

        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"❌ Error on attempt {attempt+1}: {e}")

    raise TimeoutError(f"Operation failed after {max_retries} attempts")
```

### Constitutional Violation Handling
```python
class ConstitutionalViolation(Exception):
    """Raised when code violates constitutional articles."""
    pass

def handle_constitutional_violation(violation: ConstitutionalViolation) -> None:
    """Halt execution and report violation."""
    print(f"\n🚨 CONSTITUTIONAL VIOLATION DETECTED")
    print(f"Article: {violation.article}")
    print(f"Description: {violation.description}")
    print(f"\n⛔ Execution HALTED (Article III: Zero tolerance)")

    # Store violation for learning
    context.store_memory(
        key=f"violation_{timestamp}",
        content={
            "article": violation.article,
            "description": violation.description,
            "context": violation.context
        },
        tags=["violation", "constitutional", "blocker"]
    )

    raise violation
```

### Memory-Safe Execution (Article II, Section 2.4)
```python
import psutil

def verify_memory_safe(required_gb: int = 10) -> bool:
    """Check if enough memory available."""
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)

    if available_gb < required_gb + 5:  # 5GB safety margin
        print(f"⚠️ Low memory: {available_gb:.1f}GB available, {required_gb}GB required")
        return False

    return True

# Before spawning agents
if not verify_memory_safe():
    print("🌩️ Falling back to cloud API (insufficient local memory)")
    os.environ["USE_LOCAL_MODEL"] = "false"
```

---

## Performance Optimization

### Prompt Caching
```python
# Automatically cached by SDK:
# - System prompts (agents)
# - CLAUDE.md content
# - Constitution content
# - Large plan files

# No manual cache management needed
```

### Parallel Agent Execution
```python
# When tasks are independent, spawn in parallel
if tasks_are_independent(tasks[:3]):
    results = await asyncio.gather(
        spawn_code_agent(tasks[0]),
        spawn_code_agent(tasks[1]),
        spawn_code_agent(tasks[2]),
    )
```

---

## Usage Examples

### Example 1: Simple Feature
```bash
/primeccc "Add rate limiting to API endpoints"

# Output:
# 📋 Plan: 3 tasks (simple complexity)
# 🚦 Proceed? Y
# ✅ Task 1/3: Add rate limit decorator... DONE
# ✅ Task 2/3: Update API middleware... DONE
# ✅ Task 3/3: Write integration tests... DONE
# 🚀 Complete! 3/3 tasks, 12/12 tests passing
```

### Example 2: Complex Architecture
```bash
/primeccc "Migrate authentication to OAuth2" --plan-only

# Output:
# 🏛️ Spawning Chief Architect...
# ✅ ADR created: docs/adr/ADR-024-oauth2-migration.md
# 📝 Plan created: plans/oauth2_migration_plan.md
#
# Summary: 15 tasks, 8 files to modify, 20+ tests needed
# ⏸️ Stopped at planning (--plan-only)
#
# Review plan, then run:
# /primeccc "Migrate authentication to OAuth2" --execute-plan plans/oauth2_migration_plan.md
```

### Example 3: Backlog Item Fix
```bash
/primeccc "Fix Ollama integration tests (140 skipped)"

# Output:
# 📋 Found 1 related backlog item: test_suite_gaps.md
# 🧠 Found 2 learnings: docker-compose pattern, ollama setup
# 📝 Plan: 4 tasks (moderate complexity)
# ✅ Task 1/4: Create docker-compose.yml... DONE
# ✅ Task 2/4: Update test configuration... DONE
# ✅ Task 3/4: Remove skip markers... DONE
# ✅ Task 4/4: Run tests... 140/140 PASSING
# 🚀 Complete! Backlog updated: Status FIXED ✅
```

---

## Report

After completion, provide:

```markdown
# PrimeCCC Execution Report

**Strategic Intent**: [INTENT]
**Status**: ✅ COMPLETE
**Time**: [TOTAL_TIME]

## Autonomous Agent Orchestration

**Agents Used**:
- Chief Architect: [YES/NO]
- Planner: ✅
- Scout: [YES/NO]
- Test Generator: ✅
- Code Agent: ✅
- Quality Enforcer: ✅
- Auditor: [YES/NO]
- Learning Agent: ✅ (auto-triggered)
- Merger: [YES if --auto-pr]

## Memory Integration

**VectorStore (Article IV)**:
- Learnings queried: [N]
- Patterns applied: [N]
- New patterns stored: [N]

**Memory Tool**:
- Backlog items updated: [N]
- Session progress saved: ✅
- Execution report: /memories/sessions/session_[ID]/

## Constitutional Compliance

- Article I: ✅ Complete context
- Article II: ✅ 100% tests passing
- Article III: ✅ Quality gates passed
- Article IV: ✅ Learning integrated
- Article V: ✅ Spec-driven process

## Deliverables

- Plan: [PATH]
- ADR: [PATH or N/A]
- Modified: [N] files
- Created: [N] files
- Tests: [PASSING]/[TOTAL]
- PR: [URL if --auto-pr]

**Ready for review** 🚀
```

---

## Notes

**This command implements:**
- ✅ Memory-optimized context loading (10k tokens vs 140k)
- ✅ Strategic planning with Chief Architect + Planner
- ✅ Autonomous execution loop with sub-agent orchestration
- ✅ TDD-first development (Article II)
- ✅ Constitutional compliance checking (all 5 articles)
- ✅ VectorStore integration (Article IV - MANDATORY)
- ✅ Memory Tool backlog updates
- ✅ Error handling with retry logic (Article I)
- ✅ Quality gates with auto-fix (Quality Enforcer)
- ✅ Optional auto-PR creation (Merger agent)

**You stay strategic, I handle tactical.**
