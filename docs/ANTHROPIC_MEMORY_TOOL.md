# Anthropic Memory Tool Integration

**Last Updated:** 2025-10-08
**Beta Version:** `context-management-2025-06-27`
**Status:** Production-Ready

## Overview

The Anthropic Memory Tool enables Claude to store and retrieve information across conversations through a persistent file-based memory directory. This is **client-side** storage—you control where and how data is stored through your own infrastructure.

### Key Benefits
- **Cross-conversation persistence** without context window bloat
- **Client-side control** over storage location and security
- **Automatic memory management** by Claude
- **Session isolation** for independent memory spaces

---

## Use Cases

1. **Maintain project context** across multiple agent executions
2. **Learn from past interactions**, decisions, and feedback
3. **Build knowledge bases** over time
4. **Enable cross-conversation learning** where Claude improves at recurring workflows
5. **Track technical debt and backlogs** (Agency-specific)

---

## How It Works

When enabled, Claude automatically checks its memory directory before starting tasks. Claude can perform 6 memory operations:

| Command | Purpose | Example |
|---------|---------|---------|
| `view` | Read directory/file contents | Check existing notes |
| `create` | Create or overwrite files | Save new insights |
| `str_replace` | Replace text in files | Update outdated info |
| `insert` | Insert text at specific line | Add to lists |
| `delete` | Remove files/directories | Clean up old data |
| `rename` | Move or rename files | Reorganize memory |

### Typical Interaction Flow

1. **User request:** "Help me respond to this customer service ticket."
2. **Claude checks memory:** Calls `view` command on `/memories` directory
3. **App returns contents:** Lists available memory files
4. **Claude reads relevant files:** Calls `view` on specific files
5. **Claude uses memory:** Applies stored guidelines/context to task

---

## Supported Models

- Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) ✅
- Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- Claude Opus 4.1 (`claude-opus-4-1-20250805`)
- Claude Opus 4 (`claude-opus-4-20250514`)

---

## Getting Started

### 1. Include Beta Header

```bash
# cURL
--header "anthropic-beta: context-management-2025-06-27"
```

```python
# Python SDK
client.beta.messages.create(
    betas=["context-management-2025-06-27"],
    tools=[{"type": "memory_20250818", "name": "memory"}],
    ...
)
```

### 2. Add Memory Tool to Request

```python
tools=[{
    "type": "memory_20250818",
    "name": "memory"
}]
```

### 3. Implement Client-Side Handlers

Our SDKs provide memory tool helpers:
- **Python:** Subclass `BetaAbstractMemoryTool`
- **TypeScript:** Use `betaMemoryTool`

You can implement **any backend**:
- File-based (default in Agency)
- Database
- Cloud storage (S3, GCS)
- Encrypted files
- In-memory caches

---

## Tool Commands Reference

### view

Read directory contents or file contents with optional line ranges:

```json
{
  "command": "view",
  "path": "/memories",
  "view_range": [1, 10]  // Optional: specific lines
}
```

**Agency Example:**
```python
tool.view("/memories/agency_backlog/test_suite_gaps.md")
```

---

### create

Create or overwrite a file:

```json
{
  "command": "create",
  "path": "/memories/notes.txt",
  "file_text": "Meeting notes:\n- Discussed project timeline\n- Next steps defined\n"
}
```

**Agency Example:**
```python
tool.create(
    "/memories/patterns/result_pattern.md",
    "# Result<T,E> Pattern\n\nUse for all error handling..."
)
```

---

### str_replace

Replace text in a file:

```json
{
  "command": "str_replace",
  "path": "/memories/preferences.txt",
  "old_str": "Favorite color: blue",
  "new_str": "Favorite color: green"
}
```

**Agency Example:**
```python
tool.str_replace(
    "/memories/agency_backlog/test_suite_gaps.md",
    "Status: Ready to fix",
    "Status: FIXED ✅"
)
```

---

### insert

Insert text at a specific line:

```json
{
  "command": "insert",
  "path": "/memories/todo.txt",
  "insert_line": 2,
  "insert_text": "- Review memory tool documentation\n"
}
```

---

### delete

Delete a file or directory:

```json
{
  "command": "delete",
  "path": "/memories/old_file.txt"
}
```

---

### rename

Rename or move a file/directory:

```json
{
  "command": "rename",
  "old_path": "/memories/draft.txt",
  "new_path": "/memories/final.txt"
}
```

---

## Security Considerations

### 1. Path Traversal Protection ⚠️

**CRITICAL:** Malicious path inputs could access files outside `/memories`.

**Required Safeguards:**
```python
def validate_path(self, path: str) -> Path:
    """Validate and normalize path to prevent directory traversal."""
    # 1. Must start with /memories
    if not path.startswith("/memories"):
        raise ValueError("Path must start with /memories")

    # 2. Resolve to canonical form
    full_path = (self.base_dir / path.lstrip("/")).resolve()

    # 3. Verify within base directory
    try:
        full_path.relative_to(self.base_dir)
    except ValueError:
        raise ValueError("Path escapes memory directory")

    return full_path
```

**Watch for:**
- `../`, `..\\` sequences
- URL-encoded traversal: `%2e%2e%2f`
- Symlink attacks
- Absolute paths that escape base

---

### 2. Sensitive Information

Claude **usually refuses** to write sensitive data, but implement additional validation:

```python
SENSITIVE_PATTERNS = [
    r"password\s*[:=]",
    r"api[_-]?key\s*[:=]",
    r"secret\s*[:=]",
    r"\b[A-Za-z0-9+/]{32,}={0,2}\b",  # Base64 keys
]

def check_sensitive_content(content: str) -> bool:
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False
```

---

### 3. File Storage Size

Prevent unbounded memory growth:

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TOTAL_SIZE = 100 * 1024 * 1024  # 100MB

def check_file_size(self, path: Path, content: str) -> None:
    new_size = len(content.encode('utf-8'))

    if new_size > MAX_FILE_SIZE:
        raise ValueError(f"File exceeds {MAX_FILE_SIZE} bytes")

    total_size = sum(f.stat().st_size for f in self.base_dir.rglob("*") if f.is_file())
    if total_size + new_size > MAX_TOTAL_SIZE:
        raise ValueError(f"Memory directory exceeds {MAX_TOTAL_SIZE} bytes")
```

---

### 4. Memory Expiration

Clear stale memories periodically:

```python
from datetime import datetime, timedelta

def cleanup_old_memories(self, days: int = 90) -> None:
    """Remove memories not accessed in N days."""
    cutoff = datetime.now() - timedelta(days=days)

    for file in self.base_dir.rglob("*.md"):
        if datetime.fromtimestamp(file.stat().st_atime) < cutoff:
            file.unlink()
            logger.info(f"Removed stale memory: {file}")
```

---

## Prompting Guidance

### Default System Prompt

When memory tool is enabled, Claude receives:

```
IMPORTANT: ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE.

MEMORY PROTOCOL:
1. Use the `view` command of your `memory` tool to check for earlier progress.
2. ... (work on the task) ...
   - As you make progress, record status/progress/thoughts in your memory.

ASSUME INTERRUPTION: Your context window might be reset at any moment,
so you risk losing any progress that is not recorded in your memory directory.
```

### Custom Guidance

**Keep memory organized:**
> When editing your memory folder, always try to keep its content up-to-date, coherent and organized. You can rename or delete files that are no longer relevant. Do not create new files unless necessary.

**Limit memory scope:**
> Only write down information relevant to \<topic> in your memory system.

**Agency-specific:**
> Store technical debt, architectural decisions, and backlog items in /memories/agency_backlog/. Follow the existing file structure.

---

## Error Handling

Memory tool uses same patterns as [text editor tool](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/text-editor-tool#handle-errors).

### Common Errors

| Error | Cause | Handling |
|-------|-------|----------|
| File not found | Path doesn't exist | Return error, suggest `view` on parent |
| Permission denied | Insufficient file permissions | Check base_dir permissions |
| Invalid path | Path traversal attempt | Reject and log security event |
| File too large | Exceeds size limits | Suggest splitting into multiple files |

```python
def handle_memory_error(self, error: Exception) -> dict:
    if isinstance(error, FileNotFoundError):
        return {"error": f"File not found: {error.filename}"}
    elif isinstance(error, PermissionError):
        return {"error": "Permission denied"}
    elif isinstance(error, ValueError):
        return {"error": str(error)}  # Path validation errors
    else:
        logger.exception("Unexpected memory tool error")
        return {"error": "Internal memory error"}
```

---

## Agency Integration

### Current Implementation

**File:** `tools/anthropic_memory_tool.py`
**Class:** `AgencyMemoryTool(BetaAbstractMemoryTool)`

**Features:**
- ✅ All 6 memory commands implemented
- ✅ Path traversal protection with `pathlib.Path.resolve()`
- ✅ File size limits (10MB per file, 100MB total)
- ✅ Session isolation via `base_dir` parameter
- ✅ Comprehensive security tests (30 tests, 100% pass)

### Usage in AgentContext

```python
from shared.agent_context import create_agent_context

# Enable memory for session
context = create_agent_context(session_id="feature_x_dev")
context.enable_anthropic_memory()

# Access memory tool
tool = context.get_anthropic_memory_tool()

# Use memory operations
tool.create("/memories/backlog/feature_x.md", "Feature X requirements...")
tool.view("/memories/backlog/feature_x.md")
```

### Integration with Claude SDK

```python
from tools.anthropic_agent_with_memory import create_client_with_memory

client, memory_tool = create_client_with_memory(session_id="architecture_review")

response = client.messages.create(
    model="claude-sonnet-4-5",
    messages=[{"role": "user", "content": "Review the Trinity Protocol architecture"}],
    betas=["context-management-2025-06-27"]
)
```

---

## Best Practices

### 1. Memory Organization

```
~/.agency/memories/
├── agency_backlog/          # Technical debt, TODO lists
│   ├── test_suite_gaps.md
│   ├── architecture_decisions.md
│   └── feature_requests.md
├── patterns/                # Reusable code patterns
│   ├── result_pattern.md
│   ├── pydantic_models.md
│   └── tdd_workflow.md
├── sessions/                # Session-specific context
│   ├── session_123/
│   └── session_456/
└── institutional/           # Cross-session knowledge
    ├── coding_standards.md
    ├── git_workflow.md
    └── testing_guidelines.md
```

### 2. Constitutional Compliance (Article IV)

Memory Tool **complements** (not replaces) VectorStore:

| Feature | Memory Tool | VectorStore | Use Case |
|---------|-------------|-------------|----------|
| **Persistence** | Cross-conversation | Session-scoped | Long-term vs temporary |
| **Structure** | Files/directories | Tagged records | Organized docs vs data |
| **Search** | File paths | Semantic search | Known structure vs discovery |
| **Learning** | Manual curation | Auto-extraction | Deliberate vs continuous |

**Best Practice:** Use both together!
- **Memory Tool:** Store curated knowledge, backlogs, decisions
- **VectorStore:** Learn patterns from sessions, search history

### 3. Proactive Memory Updates

```python
# After completing task
tool.str_replace(
    "/memories/agency_backlog/test_suite_gaps.md",
    "Status: Ready to fix",
    "Status: FIXED ✅ (2025-10-08)"
)

# Document new learnings
tool.create(
    "/memories/patterns/cost_tracker_api_v2.md",
    "# CostTracker API v2\n\n"
    "Changed from task_id/correlation_id params to metadata dict..."
)
```

---

## Examples

### Example 1: Tracking Technical Debt

```python
# Initial backlog creation
tool.create(
    "/memories/agency_backlog/test_suite_gaps.md",
    """# Test Suite Gaps

## Ollama Integration Tests (140 skipped)
Status: Ready to fix
Effort: 4-8 hours
Priority: Medium
"""
)

# Update after fix
tool.str_replace(
    "/memories/agency_backlog/test_suite_gaps.md",
    "Status: Ready to fix",
    "Status: FIXED ✅ (2025-10-15)"
)
```

### Example 2: Institutional Knowledge

```python
# Store coding standards
tool.create(
    "/memories/institutional/result_pattern_usage.md",
    """# Result<T,E> Pattern Usage

## Rule
ALWAYS use Result<T,E> for error handling. Never use try/catch for control flow.

## Example
```python
def fetch_data() -> Result[Data, FetchError]:
    if success:
        return Ok(data)
    return Err(FetchError("Connection failed"))
```

## Constitutional Mandate
Article II: 100% Verification - use typed errors for better testing.
"""
)
```

### Example 3: Session Progress

```python
# Track multi-step task progress
tool.create(
    "/memories/sessions/feature_auth/progress.md",
    """# Authentication Feature Progress

## Completed
- [x] Design OAuth2 flow
- [x] Implement token generation
- [x] Add refresh token logic

## In Progress
- [ ] Add rate limiting
- [ ] Write integration tests

## Next Steps
- [ ] Deploy to staging
- [ ] Security audit
"""
)
```

---

## References

- [Official Anthropic Docs](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/memory-tool)
- [Python SDK Examples](https://github.com/anthropics/anthropic-sdk-python/blob/main/examples/memory/basic.py)
- [TypeScript SDK Examples](https://github.com/anthropics/anthropic-sdk-typescript/blob/main/examples/tools-helpers-memory.ts)
- [Agency Implementation](../tools/anthropic_memory_tool.py)
- [Agency Integration Tests](../tests/test_anthropic_memory_security.py)

---

## Feedback

Memory Tool is in **beta**. Share feedback via:
- [Anthropic Feedback Form](https://forms.gle/YXC2EKGMhjN1c4L88)
- Agency GitHub Issues (for integration-specific feedback)

---

**Next:** See [MEMORY_ARCHITECTURE.md](./MEMORY_ARCHITECTURE.md) for unified memory system design.
