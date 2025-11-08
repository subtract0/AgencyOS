# Claude Code Hooks Analysis for Agency OS
**Date**: 2025-10-09
**Source**: https://github.com/disler/claude-code-hooks-mastery
**Analyzed By**: Claude Code (Sonnet 4.5)

---

## Executive Summary

Claude Code hooks provide **deterministic, programmatic control** over AI interaction lifecycle through 8 hook types. The `claude-code-hooks-mastery` repository demonstrates production-ready patterns for security, logging, context injection, and intelligent TTS feedback.

**Key Insight**: Hooks enable **constitutional enforcement** without relying on LLM decisions - perfect for Agency OS's autonomous development requirements.

---

## What Are Claude Code Hooks?

### Definition
Hooks are **executable scripts** that fire at specific points in Claude Code's lifecycle, providing interception and modification capabilities before/after key events.

### Architecture
- **Location**: `.claude/hooks/*.py` (project-level) or `~/.claude/hooks/` (user-level)
- **Format**: UV single-file Python scripts with embedded dependencies
- **Input**: JSON via stdin (tool data, session info, prompts)
- **Output**: stdout/stderr + exit codes for control flow
- **Timeout**: 60 seconds per hook execution
- **Parallelization**: All matching hooks run in parallel

### Hook Lifecycle
```
User Input → UserPromptSubmit → Claude Processing → PreToolUse →
Tool Execution → PostToolUse → Response Generation → Stop →
Notification (if needed) → SubagentStop (if subagent used)
```

---

## Available Hook Types (8 Total)

### 1. **UserPromptSubmit Hook** ⭐
**Fires**: Immediately when user submits a prompt
**Can Block**: ✅ Yes (exit code 2 prevents Claude from seeing prompt)
**Payload**: `prompt` text, `session_id`, timestamp

**Capabilities**:
- Prompt validation and security filtering
- Context injection (stdout adds text before prompt)
- Audit logging
- Secret detection (API keys, credentials)

**Example Use Cases**:
```python
# Block dangerous prompts
if "rm -rf /" in prompt:
    print("BLOCKED: Dangerous command detected", file=sys.stderr)
    sys.exit(2)

# Add project context
print("Project: Agency OS | Standards: Constitutional Articles I-V")
sys.exit(0)  # Claude sees context + original prompt
```

**Agency Value**: 🔥🔥🔥 **CRITICAL**
- Enforce constitutional compliance BEFORE Claude acts
- Block prompts violating Articles (e.g., "skip tests", "disable checks")
- Inject memory/backlog context automatically

---

### 2. **PreToolUse Hook** ⭐
**Fires**: Before any tool execution
**Can Block**: ✅ Yes (exit code 2 prevents tool from running)
**Payload**: `tool_name`, `tool_input` parameters

**Capabilities**:
- Block dangerous commands (`rm -rf`, `.env` access, `sudo`)
- Parameter validation
- Tool permission enforcement
- Logging with decision control via JSON

**Example Use Cases**:
```python
# Block .env file access
if tool_name == "Read" and ".env" in file_path:
    print("BLOCKED: .env access prohibited", file=sys.stderr)
    sys.exit(2)

# JSON decision control
output = {
    "decision": "block",
    "reason": "Test suite must be green before Write operations"
}
print(json.dumps(output))
sys.exit(0)
```

**Agency Value**: 🔥🔥🔥 **CRITICAL**
- Enforce Article III (no manual overrides) - block bypass attempts
- Validate test results before git operations
- Prevent secrets exposure

---

### 3. **PostToolUse Hook**
**Fires**: After successful tool completion
**Can Block**: ❌ No (tool already executed)
**Payload**: `tool_name`, `tool_input`, `tool_response` with results

**Capabilities**:
- Result validation
- Logging and audit trails
- Transcript conversion (JSONL → JSON)
- Feedback to Claude via JSON decision control

**Example Use Cases**:
```python
# Validate test results
if tool_name == "Bash" and "pytest" in command:
    if "FAILED" in tool_response:
        output = {
            "decision": "block",
            "reason": "Tests failing - fix before continuing (Article II)"
        }
        print(json.dumps(output))
```

**Agency Value**: 🔥🔥 **HIGH**
- Validate Article II compliance (100% test success)
- Log all autonomous actions for learning
- Extract patterns for VectorStore

---

### 4. **Stop Hook** ⭐
**Fires**: When Claude finishes responding
**Can Block**: ✅ Yes (exit code 2 forces continuation)
**Payload**: `stop_hook_active` boolean flag

**Capabilities**:
- Ensure task completion
- Validate deliverables exist
- AI-generated completion messages with TTS
- Force continuation if incomplete

**Example Use Cases**:
```python
# Ensure PR created
if not pr_created():
    output = {
        "decision": "block",
        "reason": "PR not created - run gh pr create before stopping"
    }
    print(json.dumps(output))
    sys.exit(0)

# Generate completion message
completion_msg = call_llm("Generate task summary")
play_tts(completion_msg)
```

**Agency Value**: 🔥🔥🔥 **CRITICAL**
- Enforce Article II (Definition of Done: Code + Tests + Pass + Review + CI)
- Validate constitutional checklist before stopping
- Prevent incomplete work

---

### 5. **Notification Hook**
**Fires**: When Claude sends notifications
**Can Block**: ❌ No
**Payload**: `message` content

**Capabilities**:
- Logging notifications
- Optional TTS alerts ("Your agent needs input")
- Custom notification handling

**Agency Value**: 🔥 **MEDIUM**
- Audio feedback for autonomous agents
- Alert on critical events (test failures, merge conflicts)

---

### 6. **SubagentStop Hook**
**Fires**: When subagents finish responding
**Can Block**: ✅ Yes (exit code 2 blocks subagent stoppage)
**Payload**: `stop_hook_active` boolean flag

**Capabilities**:
- Logging subagent completions
- TTS announcements
- Validation of subagent deliverables

**Agency Value**: 🔥🔥 **HIGH**
- Validate PrimeCCC agent outputs before returning to orchestrator
- Ensure subagent constitutional compliance

---

### 7. **PreCompact Hook**
**Fires**: Before context compaction
**Can Block**: ❌ No
**Payload**: `trigger` (manual/auto), `custom_instructions`, session info

**Capabilities**:
- Transcript backup
- Learning extraction before compaction
- Context preservation

**Agency Value**: 🔥🔥 **HIGH**
- Extract VectorStore patterns BEFORE context loss
- Backup session for Article IV learning

---

### 8. **SessionStart Hook**
**Fires**: When Claude starts/resumes session
**Can Block**: ❌ No
**Payload**: `source` (startup/resume/clear), session info

**Capabilities**:
- Development context loading (git status, recent issues)
- Session initialization
- Memory/backlog injection

**Agency Value**: 🔥🔥🔥 **CRITICAL**
- Auto-load constitution on session start
- Inject memory backlog (Priority Queue)
- Restore PrimeCCC state after `/clear`

---

## Hook Control Flow Mechanisms

### Exit Codes
| Code | Behavior | Description |
|------|----------|-------------|
| **0** | Success | stdout shown to user in transcript mode (Ctrl-R) |
| **2** | Blocking | stderr fed back to Claude (hook-specific behavior) |
| **Other** | Non-blocking Error | stderr shown to user, execution continues |

### JSON Decision Control (Advanced)
```python
# Common fields (all hooks)
output = {
    "continue": False,  # Stop Claude execution
    "stopReason": "Reason shown to user",
    "suppressOutput": True  # Hide stdout from transcript
}

# PreToolUse specific
output = {
    "decision": "approve" | "block" | undefined,
    "reason": "Explanation for decision"
}

# PostToolUse specific
output = {
    "decision": "block" | undefined,
    "reason": "Automatically prompts Claude with reason"
}

# Stop hook specific
output = {
    "decision": "block" | undefined,
    "reason": "Tells Claude how to proceed (forces continuation)"
}
```

---

## Key Implementation Patterns from Repository

### 1. UV Single-File Scripts Architecture
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import json
import sys

def main():
    input_data = json.load(sys.stdin)
    # Hook logic here
    sys.exit(0)

if __name__ == '__main__':
    main()
```

**Benefits**:
- Isolation from project dependencies
- Portable (dependencies declared inline)
- No venv management (UV handles it)
- Fast execution

### 2. Security Validation Pattern (PreToolUse)
```python
# Dangerous command detection
dangerous_patterns = [
    r'rm\s+.*-[rf]',           # rm -rf variants
    r'sudo\s+rm',              # sudo rm
    r'chmod\s+777',            # Dangerous permissions
    r'>\s*/etc/',              # Writing to system dirs
]

for pattern in dangerous_patterns:
    if re.search(pattern, command, re.IGNORECASE):
        print(f"BLOCKED: {pattern} detected", file=sys.stderr)
        sys.exit(2)

# .env file protection
if '.env' in file_path and not file_path.endswith('.env.sample'):
    print("BLOCKED: .env access prohibited", file=sys.stderr)
    sys.exit(2)
```

### 3. Logging Pattern (All Hooks)
```python
log_dir = Path.cwd() / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / 'hook_name.json'

# Append new data
if log_path.exists():
    log_data = json.load(open(log_path))
else:
    log_data = []

log_data.append(input_data)
json.dump(log_data, open(log_path, 'w'), indent=2)
```

### 4. Context Injection Pattern (UserPromptSubmit)
```python
# Add development context that Claude will see
git_branch = subprocess.run(['git', 'branch', '--show-current'],
                           capture_output=True, text=True).stdout.strip()
git_status = subprocess.run(['git', 'status', '--short'],
                           capture_output=True, text=True).stdout

context = f"""
Development Context:
- Branch: {git_branch}
- Changes: {git_status}
- Constitution: Articles I-V must be followed
- Memory Backlog: {load_backlog_summary()}
"""

print(context)  # Claude sees this + user prompt
sys.exit(0)
```

### 5. LLM-Enhanced Completion Messages (Stop Hook)
```python
# Priority order: OpenAI > Anthropic > Ollama > Random
def get_llm_completion_message():
    if os.getenv('OPENAI_API_KEY'):
        return call_openai("Generate task completion message")
    elif os.getenv('ANTHROPIC_API_KEY'):
        return call_anthropic("Generate task completion message")
    elif ollama_available():
        return call_ollama("Generate task completion message")
    else:
        return random.choice(["Work complete!", "All done!", "Task finished!"])

# Play via TTS (ElevenLabs > OpenAI > pyttsx3)
completion_msg = get_llm_completion_message()
play_tts(completion_msg)
```

---

## Recommended Implementations for Agency OS

### Phase 1: Constitutional Enforcement (CRITICAL - Week 1)

#### 1.1 UserPromptSubmit: Constitutional Gatekeeper
**Purpose**: Enforce Articles I-V BEFORE Claude processes prompts

```python
# .claude/hooks/constitutional_prompt_filter.py
def validate_prompt_constitutional(prompt: str) -> tuple[bool, str]:
    """
    Validate prompt against constitutional articles.
    Returns: (is_valid, reason)
    """
    violations = []

    # Article I: Complete Context
    if re.search(r'skip.*test|partial.*result|timeout.*acceptable', prompt, re.I):
        violations.append("Article I: Cannot skip tests or accept partial results")

    # Article II: 100% Verification
    if re.search(r'merge.*without.*test|bypass.*ci|skip.*verification', prompt, re.I):
        violations.append("Article II: Cannot bypass verification or CI checks")

    # Article III: Automated Enforcement
    if re.search(r'manual.*override|disable.*check|force.*push', prompt, re.I):
        violations.append("Article III: No manual overrides permitted")

    # Article IV: Continuous Learning
    if re.search(r'disable.*memory|skip.*learning|no.*vectorstore', prompt, re.I):
        violations.append("Article IV: VectorStore integration is mandatory")

    if violations:
        return False, "\n".join(violations)

    return True, ""

# Main hook
input_data = json.load(sys.stdin)
prompt = input_data.get('prompt', '')

is_valid, reason = validate_prompt_constitutional(prompt)
if not is_valid:
    print(f"CONSTITUTIONAL VIOLATION BLOCKED:\n{reason}", file=sys.stderr)
    sys.exit(2)  # Block prompt

# Inject constitution context
print("Constitution Active: Articles I-V enforced")
sys.exit(0)
```

**Value**: 🔥🔥🔥 Prevents constitutional violations at the source

---

#### 1.2 PreToolUse: Test Verification Gate
**Purpose**: Block git operations if tests failing

```python
# .claude/hooks/test_verification_gate.py
def are_tests_passing() -> bool:
    """Check if all tests are passing."""
    result = subprocess.run(['python', 'run_tests.py', '--run-all'],
                          capture_output=True, text=True, timeout=600)
    return result.returncode == 0 and 'FAILED' not in result.stdout

tool_name = input_data.get('tool_name', '')
tool_input = input_data.get('tool_input', {})

# Block git push/commit if tests failing
if tool_name == 'Bash':
    command = tool_input.get('command', '')

    if re.search(r'git\s+(push|commit)', command):
        if not are_tests_passing():
            output = {
                "decision": "block",
                "reason": "Article II: All tests must pass before git operations. Run: python run_tests.py --run-all"
            }
            print(json.dumps(output))
            sys.exit(0)

# Block dangerous operations
dangerous_patterns = [
    r'git\s+push\s+--force',  # Force push
    r'rm\s+-rf\s+\.git',      # Delete git repo
    r'--no-verify',            # Bypass pre-commit
]

for pattern in dangerous_patterns:
    if re.search(pattern, command):
        print(f"BLOCKED: Dangerous git operation (Article III)", file=sys.stderr)
        sys.exit(2)
```

**Value**: 🔥🔥🔥 Enforces Article II (100% test success) automatically

---

#### 1.3 Stop: Definition of Done Validator
**Purpose**: Ensure tasks complete with all deliverables

```python
# .claude/hooks/definition_of_done_validator.py
def validate_definition_of_done() -> tuple[bool, list[str]]:
    """
    Validate Definition of Done: Code + Tests + Pass + Review + CI
    Returns: (is_complete, missing_items)
    """
    missing = []

    # 1. Tests exist and passing?
    result = subprocess.run(['python', 'run_tests.py', '--run-all'],
                          capture_output=True, timeout=600)
    if result.returncode != 0:
        missing.append("Tests not passing (Article II)")

    # 2. Changes committed?
    result = subprocess.run(['git', 'status', '--porcelain'],
                          capture_output=True, text=True)
    if result.stdout.strip():
        missing.append("Uncommitted changes exist")

    # 3. PR created? (if on feature branch)
    branch = subprocess.run(['git', 'branch', '--show-current'],
                          capture_output=True, text=True).stdout.strip()
    if branch.startswith('feat/') or branch.startswith('fix/'):
        result = subprocess.run(['gh', 'pr', 'view', '--json', 'number'],
                              capture_output=True)
        if result.returncode != 0:
            missing.append("PR not created")

    # 4. Constitutional checklist?
    checklist_file = Path('.claude/constitutional_checklist.json')
    if not checklist_file.exists():
        missing.append("Constitutional checklist not completed")

    return len(missing) == 0, missing

is_complete, missing_items = validate_definition_of_done()

if not is_complete:
    output = {
        "decision": "block",
        "reason": f"""Definition of Done not met (Article II):

Missing:
{chr(10).join(f"- {item}" for item in missing_items)}

Complete these before stopping.
"""
    }
    print(json.dumps(output))
    sys.exit(0)

# Generate completion message
print("✅ Definition of Done validated - all deliverables complete")
```

**Value**: 🔥🔥🔥 Ensures no incomplete work (Article II compliance)

---

### Phase 2: Memory & Learning Integration (HIGH - Week 2)

#### 2.1 SessionStart: Auto-Load Memory Context
**Purpose**: Load constitution + backlog + VectorStore patterns on session start

```python
# .claude/hooks/session_memory_loader.py
from shared.agent_context import create_agent_context

def load_session_context(source: str) -> str:
    """Load memory context for new session."""
    context_parts = []

    # 1. Constitution (always)
    with open('constitution.md', 'r') as f:
        constitution = f.read()
    context_parts.append(f"### Constitution Loaded\n{constitution[:500]}...")

    # 2. Memory backlog
    context = create_agent_context(session_id=f"session_{timestamp}")
    context.enable_anthropic_memory()
    tool = context.get_anthropic_memory_tool()

    try:
        backlog = tool.view('/memories/agency_backlog/primeccc_priorities.md')
        context_parts.append(f"### Backlog Priorities\n{backlog[:500]}...")
    except:
        pass

    # 3. VectorStore patterns
    learnings = context.search_memories(['pattern', 'success'], include_session=False)
    if learnings:
        context_parts.append(f"### Recent Learnings\n{len(learnings)} patterns available")

    # 4. Git context
    branch = subprocess.run(['git', 'branch', '--show-current'],
                          capture_output=True, text=True).stdout.strip()
    status = subprocess.run(['git', 'status', '--short'],
                          capture_output=True, text=True).stdout
    context_parts.append(f"### Git Status\nBranch: {branch}\n{status}")

    return "\n\n".join(context_parts)

input_data = json.load(sys.stdin)
source = input_data.get('source', 'startup')

context = load_session_context(source)
print(f"Session initialized ({source}):\n{context}")
```

**Value**: 🔥🔥🔥 Restores full context after `/clear` (Article IV)

---

#### 2.2 PreCompact: Learning Extraction
**Purpose**: Extract VectorStore patterns before context loss

```python
# .claude/hooks/learning_extractor.py
from shared.agent_context import create_agent_context

def extract_learnings_before_compact(session_id: str):
    """Extract patterns from current session before compaction."""
    context = create_agent_context(session_id=session_id)

    # Read transcript
    transcript_file = Path(f'.claude/data/conversations/{session_id}.jsonl')
    if not transcript_file.exists():
        return

    # Parse for patterns
    patterns = []
    with open(transcript_file, 'r') as f:
        for line in f:
            msg = json.loads(line)
            # Extract successful tool uses
            if msg.get('type') == 'tool_result' and msg.get('success'):
                patterns.append({
                    'tool': msg.get('tool_name'),
                    'context': msg.get('tool_input'),
                    'outcome': 'success'
                })

    # Store in VectorStore
    for pattern in patterns:
        context.store_memory(
            key=f"pattern_{timestamp}",
            content=pattern,
            tags=['pre_compact', 'auto_extracted']
        )

    print(f"✅ Extracted {len(patterns)} patterns to VectorStore before compaction")

input_data = json.load(sys.stdin)
extract_learnings_before_compact(input_data['session_id'])
```

**Value**: 🔥🔥 Prevents learning loss during compaction (Article IV)

---

### Phase 3: Autonomous Development Support (MEDIUM - Week 3)

#### 3.1 PostToolUse: Telemetry & Learning Logger
**Purpose**: Log all autonomous actions for Article IV learning

```python
# .claude/hooks/autonomous_telemetry.py
from core.telemetry import log_event, TelemetryEvent

tool_name = input_data.get('tool_name', '')
tool_input = input_data.get('tool_input', {})
tool_response = input_data.get('tool_response', {})

# Log telemetry event
event = TelemetryEvent(
    event_type=f"tool_use.{tool_name.lower()}",
    metadata={
        'tool': tool_name,
        'input': tool_input,
        'success': tool_response.get('success', False),
        'session_id': input_data.get('session_id')
    }
)
log_event(event)

# Extract patterns for VectorStore
if tool_response.get('success'):
    context = create_agent_context(session_id=input_data['session_id'])
    context.store_memory(
        key=f"tool_use_{tool_name}_{timestamp}",
        content={'tool': tool_name, 'pattern': tool_input},
        tags=['tool_use', 'success', tool_name.lower()]
    )
```

**Value**: 🔥🔥 Full autonomous action audit trail (Article IV)

---

#### 3.2 Notification: Critical Event Alerts
**Purpose**: TTS/audio alerts for autonomous agent events

```python
# .claude/hooks/critical_event_alerts.py
def should_alert(message: str) -> bool:
    """Determine if message warrants audio alert."""
    alert_keywords = [
        'test.*fail', 'error', 'blocked', 'constitutional.*violation',
        'merge.*conflict', 'ci.*fail'
    ]
    return any(re.search(kw, message, re.I) for kw in alert_keywords)

message = input_data.get('message', '')

if should_alert(message):
    # Priority: ElevenLabs > OpenAI > pyttsx3
    tts_script = get_tts_script_path()
    if tts_script:
        subprocess.run(['uv', 'run', tts_script, '--text', message])
```

**Value**: 🔥 Audio feedback for autonomous operations

---

## Configuration Setup

### 1. Enable Hooks in `.claude/settings.json`
```json
{
  "UserPromptSubmit": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "uv run .claude/hooks/constitutional_prompt_filter.py"
        },
        {
          "type": "command",
          "command": "uv run .claude/hooks/session_memory_loader.py"
        }
      ]
    }
  ],
  "PreToolUse": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "uv run .claude/hooks/test_verification_gate.py"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "uv run .claude/hooks/autonomous_telemetry.py"
        }
      ]
    }
  ],
  "Stop": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "uv run .claude/hooks/definition_of_done_validator.py"
        }
      ]
    }
  ],
  "PreCompact": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "uv run .claude/hooks/learning_extractor.py"
        }
      ]
    }
  ],
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "uv run .claude/hooks/session_memory_loader.py"
        }
      ]
    }
  ]
}
```

### 2. Create Hook Directory Structure
```bash
mkdir -p .claude/hooks/utils/{llm,tts}
mkdir -p logs
```

### 3. Install UV (if not already)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

---

## Integration with Existing Agency Infrastructure

### 1. Constitutional Compliance
**Current**: Manual validation in agents
**With Hooks**: Automatic enforcement at prompt/tool level
**Benefit**: Zero reliance on LLM decisions for compliance

### 2. VectorStore Learning (Article IV)
**Current**: Manual store_memory() calls in agents
**With Hooks**: Automatic extraction after every tool use
**Benefit**: No learning is ever missed

### 3. Memory Tool Integration
**Current**: Manual context loading
**With Hooks**: Automatic injection on SessionStart
**Benefit**: Always starts with full context

### 4. PrimeCCC Workflow
**Current**: Manual TodoWrite, manual checks
**With Hooks**: Automatic validation at Stop hook
**Benefit**: Enforces Definition of Done

### 5. Telemetry System
**Current**: Manual log_event() calls
**With Hooks**: Automatic telemetry for all tool uses
**Benefit**: Complete audit trail

---

## Testing Strategy

### Unit Tests
```python
# tests/test_constitutional_prompt_filter.py
def test_blocks_article_i_violations():
    prompt = "skip the failing tests"
    is_valid, reason = validate_prompt_constitutional(prompt)
    assert not is_valid
    assert "Article I" in reason

def test_blocks_article_ii_violations():
    prompt = "merge without running tests"
    is_valid, reason = validate_prompt_constitutional(prompt)
    assert not is_valid
    assert "Article II" in reason

def test_allows_valid_prompts():
    prompt = "implement feature following TDD"
    is_valid, reason = validate_prompt_constitutional(prompt)
    assert is_valid
```

### Integration Tests
```python
# tests/test_hooks_integration.py
def test_hooks_prevent_bad_commits():
    """Test that PreToolUse blocks commits when tests failing."""
    # Setup: Make tests fail
    subprocess.run(['pytest', 'tests/test_failing.py'])

    # Try to commit (should be blocked by hook)
    result = subprocess.run(['git', 'commit', '-m', 'test'],
                          capture_output=True)

    assert result.returncode != 0
    assert "Article II" in result.stderr.decode()
```

---

## Security Considerations

### 1. Secrets Protection
- Block `.env` file access in PreToolUse
- Scan prompts for API keys in UserPromptSubmit
- Prevent accidental secret commits

### 2. Command Validation
- Block `rm -rf`, `sudo rm`, `chmod 777`
- Prevent system directory modifications
- Validate git operations (no force push to main)

### 3. Constitutional Enforcement
- Cannot be bypassed by LLM (deterministic)
- Multiple layers (prompt + tool + stop)
- Audit log of all violations

---

## Performance Impact

### Benchmark Data (from repository)
- **Typical hook execution**: <100ms per hook
- **Parallel execution**: All hooks run simultaneously
- **Timeout**: 60 seconds max (should never hit)
- **Overhead**: Negligible (~2-5% of total request time)

### Optimization Tips
1. Cache expensive checks (test results, git status)
2. Use subprocess with timeouts
3. Keep hook logic simple (complex logic → separate tool)
4. Log asynchronously

---

## Rollout Plan

### Week 1: Constitutional Enforcement (CRITICAL)
- [ ] Implement UserPromptSubmit constitutional filter
- [ ] Implement PreToolUse test verification gate
- [ ] Implement Stop definition of done validator
- [ ] Test with existing workflows
- [ ] Deploy to production

### Week 2: Memory & Learning (HIGH)
- [ ] Implement SessionStart memory loader
- [ ] Implement PreCompact learning extractor
- [ ] Test VectorStore integration
- [ ] Validate context restoration after `/clear`

### Week 3: Autonomous Support (MEDIUM)
- [ ] Implement PostToolUse telemetry logger
- [ ] Implement Notification critical alerts
- [ ] Optional: TTS integration (ElevenLabs/OpenAI)
- [ ] Optional: SubagentStop validation

### Week 4: Refinement & Documentation
- [ ] Collect metrics on hook effectiveness
- [ ] Optimize slow hooks
- [ ] Write internal documentation
- [ ] Train team on hook configuration

---

## Success Metrics

### Constitutional Compliance
- **Target**: 0 manual overrides attempted
- **Measure**: Count of PreToolUse blocks for Article violations
- **Baseline**: Current manual validation rate

### Learning Coverage
- **Target**: 100% of tool uses logged to VectorStore
- **Measure**: PostToolUse logs vs VectorStore entries
- **Baseline**: Current manual store_memory() coverage (~60%)

### Context Restoration
- **Target**: 100% session context restored after `/clear`
- **Measure**: SessionStart success rate
- **Baseline**: Currently 0% (no automatic restoration)

### Test Compliance
- **Target**: 0 commits with failing tests
- **Measure**: PreToolUse blocks for git operations
- **Baseline**: Pre-commit hook catch rate (~80%)

---

## Risks & Mitigation

### Risk 1: Hook Failures Block Work
**Mitigation**:
- Comprehensive testing before deployment
- Graceful error handling (exit 0 on exceptions)
- Override mechanism for emergencies (env var)

### Risk 2: Performance Degradation
**Mitigation**:
- Profile hooks before deployment
- Cache expensive operations
- 60s timeout prevents hangs

### Risk 3: False Positives
**Mitigation**:
- Extensive test coverage
- Pattern refinement based on logs
- User feedback loop

---

## Conclusion

Claude Code hooks provide **deterministic, programmatic control** perfectly suited for Agency OS's autonomous development requirements. The implementation enables:

1. **Constitutional Enforcement** without LLM reliability issues
2. **Automatic Learning** (Article IV) without manual calls
3. **Context Restoration** after `/clear` or `/compact`
4. **Complete Audit Trail** for all autonomous actions
5. **Definition of Done** validation before task completion

**Recommended Priority**: Implement Phase 1 (Constitutional Enforcement) immediately - provides highest ROI and aligns with Agency's core philosophy of automated discipline.

---

**Next Steps**: Review this analysis, prioritize hooks, and create implementation tickets in backlog.
