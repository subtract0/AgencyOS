# CMP Schema: Clade Metaproductivity Events and Scores

**Purpose**: Define the data structures for tracking autonomous PR experiments and computing clade performance scores.

**Context**: Metaproductivity 2.0 tracks every autonomous PR as an experiment. When merged or rejected, we log a CmpEvent. Clades (agent+model+prompt+strategy combinations) compete via epsilon-greedy bandit selection based on CmpScore metrics.

---

## Core Concepts

### Clade
A **clade** is a specific configuration of:
- Agent implementation (e.g., `self_healer_v1`, `backlog_v1`)
- Model used (e.g., `qwen-32b`, `vcoder-120b`, `gpt-5`)
- Prompt profile (e.g., `prompt_small_diff_v1`)
- Strategy tag (e.g., `strategy_minimal`)

**Format**: `<agent_id>::<model_name>::<prompt_profile>::<strategy>`

**Example**: `self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal`

### CMP (Clade Metaproductivity)
The process of:
1. Tracking PR experiments via CmpEvent
2. Computing performance metrics via CmpScore
3. Selecting clades via epsilon-greedy bandit (CladeSelector)
4. Evolving agent configurations based on real performance

---

## CmpEvent Schema

Records a single autonomous PR experiment.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | Yes | Unique event ID (UUID or timestamp-based) |
| `pr_id` | int | Yes | GitHub PR number |
| `branch_name` | str | Yes | Git branch name (format: `autogen/{agent}-{model}-{prompt}-{strategy}-{short_id}`) |
| `agent_id` | str | Yes | Agent that created the PR (e.g., `self_healer_v1`, `backlog_v1`) |
| `clade_id` | str | Yes | Full clade identifier (format: `agent::model::prompt::strategy`) |
| `task_type` | str | Yes | Type of task (e.g., `self_heal`, `backlog`, `refactor`) |
| `created_at` | int | Yes | PR creation timestamp (Unix epoch seconds) |
| `closed_at` | int | Yes | PR close/merge timestamp (Unix epoch seconds) |
| `reinforcement_signal` | str | Yes | Outcome: `"approved"` (merged) or `"rejected"` (closed without merge) |
| `reverted` | bool | Yes | Was this PR later reverted due to smoke test failure? |
| `size_loc_delta` | int | Yes | Lines of code changed (additions + deletions) |
| `files_touched` | List[str] | Yes | List of file paths modified |
| `test_status` | str | Yes | Test outcome: `"pass"`, `"fail"`, `"skip"`, `"timeout"` |
| `test_suites` | List[str] | No | Test suites run (e.g., `["unit", "integration"]`) |
| `human_review_time_sec` | int | No | Time from creation to human approval (seconds) |
| `extra_metadata` | Dict[str, Any] | No | Flexible field for additional context |

### Example JSON

```json
{
  "id": "cmp_20251112_143052_abc123",
  "pr_id": 142,
  "branch_name": "autogen/selfheal-v1-qwen32b-prompt_small_diff-v1-minimal-9f2a",
  "agent_id": "self_healer_v1",
  "clade_id": "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
  "task_type": "self_heal",
  "created_at": 1731423052,
  "closed_at": 1731425280,
  "reinforcement_signal": "approved",
  "reverted": false,
  "size_loc_delta": 47,
  "files_touched": ["tests/test_validation.py", "shared/validation.py"],
  "test_status": "pass",
  "test_suites": ["unit"],
  "human_review_time_sec": 2228,
  "extra_metadata": {
    "fix_type": "NoneType_AttributeError",
    "test_failures_fixed": 3
  }
}
```

---

## CmpScore Schema

Aggregates performance metrics for a single clade.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `clade_id` | str | Clade identifier |
| `total_events` | int | Total number of CmpEvents for this clade |
| `approvals` | int | Number of merged PRs (`reinforcement_signal == "approved"`) |
| `rejections` | int | Number of rejected PRs (`reinforcement_signal == "rejected"`) |
| `reverts` | int | Number of merged PRs later reverted (`reverted == True`) |
| `approval_rate` | float | `approvals / total_events` (0.0 to 1.0) |
| `revert_rate` | float | `reverts / approvals` (0.0 to 1.0, or 0.0 if no approvals) |
| `avg_loc_delta_rejected` | float | Average LOC changed for rejected PRs |
| `score` | float | Composite score (see formula below) |

### Score Formula

```python
score = approval_rate - 2 * revert_rate - 0.5 * (avg_loc_delta_rejected / 500)
```

**Rationale**:
- **High approval_rate**: Clade's PRs get merged frequently (good)
- **Low revert_rate**: Merged PRs rarely break things (very good)
- **Low avg_loc_delta_rejected**: Rejections are small, targeted fixes (acceptable)

**Score Range**: Approximately -2.0 to 1.0
- **> 0.8**: Excellent (most PRs approved, few reverts, small rejection deltas)
- **0.5 to 0.8**: Good
- **0.0 to 0.5**: Acceptable
- **< 0.0**: Poor (high rejection or revert rate)

### Example JSON

```json
{
  "clade_id": "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
  "total_events": 15,
  "approvals": 12,
  "rejections": 3,
  "reverts": 1,
  "approval_rate": 0.8,
  "revert_rate": 0.083,
  "avg_loc_delta_rejected": 234.67,
  "score": 0.633
}
```

**Calculation**:
```
score = 0.8 - 2*(0.083) - 0.5*(234.67/500)
      = 0.8 - 0.166 - 0.234
      = 0.633
```

---

## CmpStore Schema (JSONL File)

Events are stored in `data/cmp_events.jsonl` (newline-delimited JSON).

### Format
Each line is a complete CmpEvent JSON object:

```jsonl
{"id": "cmp_001", "pr_id": 140, "clade_id": "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal", ...}
{"id": "cmp_002", "pr_id": 141, "clade_id": "backlog_v1::gpt-5::prompt_full_context::strategy_careful", ...}
{"id": "cmp_003", "pr_id": 142, "clade_id": "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal", ...}
```

### Operations

**Write (append-only)**:
```python
with open("data/cmp_events.jsonl", "a") as f:
    f.write(json.dumps(event_dict) + "\n")
```

**Read (load all)**:
```python
events = []
with open("data/cmp_events.jsonl", "r") as f:
    for line in f:
        events.append(json.loads(line))
```

---

## CladeSelector Schema (Epsilon-Greedy Bandit)

Selects which clade to use for the next agent run.

### Algorithm

```python
def select_clade(
    task_type: str,
    available_clades: List[str],
    epsilon: float = 0.1
) -> str:
    """
    Epsilon-greedy selection:
    - With probability ε: explore (choose random clade)
    - With probability 1-ε: exploit (choose highest-scoring clade)

    Args:
        task_type: Filter events by task type (e.g., "self_heal")
        available_clades: List of clade_ids to choose from
        epsilon: Exploration probability (default 0.1)

    Returns:
        Selected clade_id
    """
    if random.random() < epsilon:
        # Explore: random selection
        return random.choice(available_clades)
    else:
        # Exploit: choose best clade by score
        scores = {clade: compute_clade_score(clade, task_type) for clade in available_clades}
        return max(scores, key=scores.get)
```

### Example

**Available clades for self-healing**:
```python
available = [
    "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
    "self_healer_v1::gpt-5::prompt_full_context::strategy_careful",
    "self_healer_v2::vcoder-120b::prompt_context_aware::strategy_balanced"
]
```

**Selection (ε=0.1)**:
- 10% chance: Pick random clade (explore new configurations)
- 90% chance: Pick clade with highest CmpScore (exploit proven winners)

**Evolution**: Over time, successful clades dominate, but exploration ensures we don't miss better configurations.

---

## Integration with AgentContext and EnhancedMemoryStore

### AgentContext Extensions

**New fields**:
```python
class AgentContext:
    agent_id: str  # e.g., "self_healer_v1"
    clade_id: str  # e.g., "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal"
    task_type: str  # e.g., "self_heal"
    provenance_id: str  # UUID linking to CmpEvent.id

    def build_clade_id(model_name: str, prompt_profile: str, strategy: str) -> str:
        return f"{self.agent_id}::{model_name}::{prompt_profile}::{strategy}"
```

### EnhancedMemoryStore Extensions

**New memory schema fields**:
```python
memory = {
    "content": "...",
    "agent_id": "self_healer_v1",
    "clade_id": "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
    "task_type": "self_heal",
    "reinforcement_signal": "approved",  # Set by supervise() after PR merge
    "provenance_id": "cmp_20251112_143052_abc123",  # Links to CmpEvent
    "tags": ["self_heal", "test_fix", "NoneType"],
    "created_at": 1731423052
}
```

**New method**:
```python
def set_reinforcement(memory_id: str, signal: str) -> None:
    """
    Update memory's reinforcement_signal field.
    Called by auto_supervise_hook.py after PR is merged/rejected.

    Args:
        memory_id: ID of memory to update
        signal: "approved" or "rejected"
    """
```

---

## Workflow: From PR to CMP Event

```
1. AGENT RUN (e.g., self_healer.py)
   - CladeSelector chooses clade (epsilon-greedy)
   - AgentContext initialized with agent_id, clade_id, task_type
   - Agent creates PR on autogen/* branch
   - PR body includes metadata comments:
     <!-- agent_id: self_healer_v1 -->
     <!-- clade_id: self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal -->
     <!-- task_type: self_heal -->
     <!-- memory_ids: ["mem_001", "mem_002"] -->

2. PR MERGED/CLOSED (Human or auto-merge)
   - GitHub workflow triggers: .github/workflows/learning_coach.yml
   - Calls: tools/auto_supervise_hook.py --signal=approved --pr-id=142

3. AUTO_SUPERVISE_HOOK
   - Parses PR metadata from body
   - Builds CmpEvent:
     - pr_id, branch_name, agent_id, clade_id, task_type
     - reinforcement_signal = "approved"
     - reverted = false (initially)
     - size_loc_delta, files_touched (from GitHub API)
   - Records event: CmpStore.record_event(event)
   - Updates memories: supervise(memory_id, signal) for each memory_id

4. CMP CONSOLE (Optional inspection)
   - python tools/cmp_console.py list-clades
   - Shows: clade_id, approvals, rejections, score
   - Helps monitor which clades are winning

5. REVERT HOOK (If smoke tests fail)
   - scripts/revert_on_smoke_failure.sh
   - Calls: auto_supervise_hook.py --signal=rejected --reverted=true --pr-id=142
   - Updates original CmpEvent: reverted = true
   - Lowers clade score significantly
```

---

## Constitutional Compliance

CMP schema aligns with AgencyOS constitutional requirements:

### Article I: Complete Context
- All CmpEvents tracked to completion (no partial data)
- Retry on GitHub API timeouts

### Article II: 100% Verification
- Events only recorded after definitive PR outcome (merged/closed)
- Revert detection via smoke tests

### Article III: Automated Enforcement
- CmpStore is append-only (no manual editing)
- Scoring formula is deterministic
- CladeSelector enforces epsilon-greedy (no manual clade selection)

### Article IV: Continuous Learning
- Every PR experiment contributes to institutional knowledge
- VectorStore integration via enhanced_memory_store.py
- supervise() updates memories with reinforcement signals

### Article V: Spec-Driven
- This schema doc is the source of truth
- Implementation in `learning.py` traces to this spec

---

## Implementation Notes

### Data Directory
```
data/
├── cmp_events.jsonl (CmpEvent log)
└── cmp_checkpoints/ (optional: periodic backups)
```

### Error Handling
- **Missing PR metadata**: Log warning, skip CmpEvent creation
- **GitHub API failures**: Retry 3x with exponential backoff
- **Malformed JSONL**: Log error, continue processing

### Performance
- **CmpStore.load_events()**: O(n) where n = number of events
- **Optimization**: If >10k events, consider SQLite or time-based filtering
- **Current scale**: <1000 events expected in first month

---

## Future Extensions

### Advanced Scoring
- Add time-to-merge penalty (faster is better)
- Add test coverage delta (more coverage is better)
- Weight by task_type (self_heal vs backlog have different success criteria)

### Multi-Armed Bandit Variants
- Thompson Sampling (Bayesian approach)
- Upper Confidence Bound (UCB1)
- Contextual bandits (select clade based on task features)

### Federated CMP
- Share anonymized CmpEvents across AgencyOS installations
- Learn from global clade performance

---

**Last Updated**: 2025-11-12
**Version**: 1.0
**Status**: Approved (ADR-037)
