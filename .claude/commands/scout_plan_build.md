---
description: Three-step engineering workflow - Scout files, plan implementation, build solution
argument-hint: [user-prompt] [documentation-urls] [scale]
model: claude-sonnet-4-5-20250929
settingSources: ['project']
---

# Purpose

Run a three-step engineering workflow to deliver on the `USER_PROMPT`:

1. **Scout** - Find relevant files in codebase (parallel agents)
2. **Plan** - Create implementation plan based on discovered files
3. **Build** - Execute the plan and deliver working code

This command uses the Claude Agent SDK's full capabilities including subagents, context management, and tool permissions.

# Variables

- `USER_PROMPT`: The task to complete (e.g., "Add JWT authentication to API endpoints")
- `DOCUMENTATION_URLS`: Optional comma-separated URLs to documentation (e.g., "https://docs.example.com/auth,https://jwt.io")
- `SCALE`: Number of parallel scout agents (1-5, default: 4)

# Workflow

> Run the workflow in order, top to bottom. Do not stop in between steps. Complete every step in the workflow before stopping.

## 1. Scout Phase - Find Relevant Files

**Using Claude Agent SDK with parallel subagents:**

```typescript
// TypeScript SDK Pattern
import { ClaudeAgentSDK } from '@anthropic-ai/claude-agent-sdk';

const sdk = new ClaudeAgentSDK({
  apiKey: process.env.ANTHROPIC_API_KEY,
  settingSources: ['project'], // Loads .claude/agents/, CLAUDE.md, etc.
});

// Spawn parallel scout agents
const scoutPromises = Array.from({ length: SCALE }, (_, i) => {
  const agentType = ['gemini-flash', 'cerebras-qwen', 'gemini-lite', 'gpt-codex', 'haiku'][i];

  return sdk.createAgent({
    name: `scout-${agentType}`,
    systemPrompt: `You are a code search specialist using ${agentType}.

Task: Find files relevant to "${USER_PROMPT}"
Strategy: Use Bash tool to call CLI: ${getAgentCommand(agentType, USER_PROMPT)}
Timeout: 180 seconds
Output: List files with (offset, limit) for relevant sections`,

    allowedTools: ['Bash'],
    permissionMode: 'acceptAll',
    model: 'claude-sonnet-4-5',
    maxTurns: 1, // Single search pass
  }).run();
});

// Race to get fastest results
const scoutResults = await Promise.allSettled(scoutPromises);
```

**Actual Implementation (Use SlashCommand tool):**

Run SlashCommand(`/scout "${USER_PROMPT}" "${SCALE}"`) and capture the `relevant_files_collection_path`.

**Expected Output:**
```
## Scout Results
Files found: 12
Most relevant:
1. src/auth/middleware.py (offset: 15, limit: 80) - Auth middleware base
2. src/models/user.py (offset: 42, limit: 120) - User model with password hash
3. tests/test_auth.py (offset: 0, limit: 200) - Existing auth tests
...

Collection saved to: .output/scout_collections/task_abc123.json
```

## 2. Plan Phase - Create Implementation Plan

**Using Agent SDK with MCP and documentation fetching:**

```python
# Python SDK Pattern
from claude_agent_sdk import ClaudeAgentSDK, MCPServer

# Setup MCP server for documentation fetching
class DocFetchServer(MCPServer):
    @tool("fetch_docs")
    async def fetch_docs(self, url: str) -> str:
        """Fetch and parse documentation from URL."""
        # Implementation fetches and converts to markdown
        return markdown_content

sdk = ClaudeAgentSDK(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    setting_sources=["project"],  # Loads .claude/* configs
)

# Create planner agent with documentation access
planner = sdk.create_agent(
    name="implementation_planner",
    system_prompt=f"""You are an expert implementation planner.

Task: Create detailed plan for "{USER_PROMPT}"
Context: {len(scout_files)} files found via scout
Documentation: {"Available" if DOCUMENTATION_URLS else "None"}

Create a plan.md following the spec-kit methodology:
- Goals section
- Architecture decisions
- Implementation steps (numbered, detailed)
- Testing strategy
- Success criteria
""",

    allowed_tools=["Read", "Write", "Glob", "Grep", "WebFetch"],
    mcp_servers={"docs": DocFetchServer()} if DOCUMENTATION_URLS else None,
    permission_mode="acceptEdits",
    model="claude-sonnet-4-5",
)

plan_result = await planner.run()
```

**Actual Implementation:**

1. If `DOCUMENTATION_URLS` provided:
   ```bash
   # Fetch documentation using WebFetch
   for url in DOCUMENTATION_URLS.split(','):
     WebFetch(url, "Extract key concepts and API patterns")
   ```

2. Run SlashCommand(`/plan_w_docs "${USER_PROMPT}" "${DOCUMENTATION_URLS}" "${relevant_files_collection_path}"`)

**Expected Output:**
```
Plan created: .output/plans/task_abc123_plan.md

## Plan Summary
- Architecture: JWT tokens with refresh mechanism
- Files to modify: 5
- Files to create: 3
- Tests to write: 12
- Estimated time: 4 hours

Next: Build phase
```

## 3. Build Phase - Execute Implementation

**Using Agent SDK with full tool permissions and hooks:**

```typescript
// TypeScript SDK with custom hooks
import { ClaudeAgentSDK } from '@anthropic-ai/claude-agent-sdk';

const sdk = new ClaudeAgentSDK({
  apiKey: process.env.ANTHROPIC_API_KEY,
  settingSources: ['project'], // Enables .claude/settings.json hooks
});

// Hooks from .claude/settings.json will fire automatically:
// - tool-start: Log when Write/Edit tools are called
// - tool-end: Run linters after file changes
// - prompt-submit: Inject constitutional compliance reminders

const builder = sdk.createAgent({
  name: "implementation_builder",
  systemPrompt: `You are an expert software engineer.

Task: Implement "${USER_PROMPT}" following plan.md
Plan: ${plan_path}
Files to modify: ${scout_results.files.join(', ')}

IMPORTANT:
- Follow TDD: Write tests FIRST
- Use Result<T,E> pattern for error handling
- Run tests after each change
- Commit atomically (one feature = one commit)
- Follow constitutional compliance (all 5 articles)
`,

  allowedTools: [
    "Read", "Write", "Edit", "MultiEdit",
    "Bash",  // For running tests
    "Glob", "Grep",  // For finding related code
  ],
  disallowedTools: ["WebSearch"],  // No external lookups during build
  permissionMode: "acceptEdits",  // Auto-approve file edits
  model: "claude-sonnet-4-5",

  // Context management (automatic)
  maxPromptTokens: 128000,  // SDK auto-compacts when near limit
  maxCompletionTokens: 16384,
});

// Run with streaming for real-time progress
const stream = builder.stream();

for await (const event of stream) {
  if (event.type === "tool_use") {
    console.log(`🔧 ${event.tool_name}: ${event.tool_input}`);
  }
  if (event.type === "content_block_delta") {
    process.stdout.write(event.delta);
  }
}

const buildResult = await stream.finalMessage();
```

**Actual Implementation:**

Run SlashCommand(`/build "${path_to_plan}"`)

The `/build` command will:
1. Read plan.md
2. For each implementation step:
   - Read relevant files
   - Write tests first (TDD)
   - Implement changes
   - Run tests
   - Commit if passing
3. Generate build report

**Expected Output:**
```
## Build Complete ✅

Implemented: 8/8 tasks from plan
Files modified: 5
Files created: 3
Tests written: 12
Tests passing: 12/12 (100%)

Commits:
- abc123: test: Add JWT authentication test suite
- def456: feat: Implement JWT token generation
- ghi789: feat: Add refresh token rotation
- jkl012: feat: Integrate JWT middleware with API routes

All tests passing. Ready for PR.
```

## 4. Final Report - Summarize Completed Work

Generate structured summary of the entire workflow:

```markdown
# Scout → Plan → Build Report

**Task**: ${USER_PROMPT}
**Status**: ✅ Complete
**Total Time**: ${total_time}

## Phase 1: Scout (${scout_time})
- Agents spawned: ${SCALE}
- Files found: ${scout_files.length}
- Fastest agent: ${fastest_agent} (${fastest_time}s)

## Phase 2: Plan (${plan_time})
- Documentation URLs fetched: ${DOCUMENTATION_URLS ? 'Yes' : 'No'}
- Plan file: ${plan_path}
- Implementation steps: ${plan_steps}
- Estimated effort: ${estimated_hours}h

## Phase 3: Build (${build_time})
- Files modified: ${modified_files.length}
- Files created: ${created_files.length}
- Tests written: ${tests_written}
- Tests passing: ${tests_passing}/${tests_written}
- Commits: ${commits.length}

## Success Metrics
- ✅ All tests passing
- ✅ Constitutional compliance (Articles I-V)
- ✅ Code coverage: ${coverage}%
- ✅ No linting errors
- ✅ Build time under estimate

## Next Steps
1. Review commits: git log --oneline -${commits.length}
2. Run full test suite: python run_tests.py --run-all
3. Create PR: gh pr create
4. Deploy to staging

**Ready for review** 🚀
```

# Instructions

## Agent SDK Best Practices (Apply Throughout)

### 1. Context Management
```python
# SDK handles context automatically
agent = sdk.create_agent(
    max_prompt_tokens=128000,  # Auto-compacts when approaching limit
    # No manual context tracking needed
)
```

### 2. Tool Permissions (Fine-Grained Control)
```typescript
// Restrictive for scout (read-only)
allowedTools: ['Bash'],
permissionMode: 'acceptAll',

// Permissive for build (write allowed)
allowedTools: ['Read', 'Write', 'Edit', 'Bash'],
permissionMode: 'acceptEdits',

// Block dangerous operations
disallowedTools: ['WebSearch', 'KillShell'],
```

### 3. MCP Integration
```python
# Load MCP servers from .claude/settings.json
sdk = ClaudeAgentSDK(
    setting_sources=["project"],  # Auto-discovers MCP configs
)

# Or define inline
from claude_agent_sdk import MCPServer

class CustomToolServer(MCPServer):
    @tool("my_tool")
    async def my_tool(self, arg: str) -> str:
        return f"Result: {arg}"

agent = sdk.create_agent(
    mcp_servers={"custom": CustomToolServer()}
)
```

### 4. Hooks Integration
```json
// .claude/settings.json (loaded automatically with settingSources: ['project'])
{
  "hooks": {
    "tool-start": {
      "Write": "echo 'Writing file: {file_path}' >> .output/build.log"
    },
    "tool-end": {
      "Edit": "ruff check {file_path} --fix"
    },
    "prompt-submit": "echo 'Remember: Constitutional compliance!' | cat"
  }
}
```

### 5. Streaming vs Single Mode
```python
# Streaming (for long-running builds)
stream = agent.stream()
for event in stream:
    if event.type == "content_block_delta":
        print(event.delta, end="", flush=True)

# Single (for quick operations)
result = await agent.run()
```

## Error Handling

```python
from claude_agent_sdk import AgentError, ContextLengthExceeded

try:
    result = await agent.run()
except ContextLengthExceeded:
    # SDK auto-compacts, but if still over limit:
    print("Task too large, breaking into subtasks")
except AgentError as e:
    print(f"Agent failed: {e}")
    # Retry with different model or reduced scope
```

## Performance Optimization

### Prompt Caching (Automatic)
SDK automatically caches:
- System prompts
- CLAUDE.md contents
- Large file contexts

No manual cache management needed.

### Parallel Execution
```typescript
// Scout phase - race multiple agents
const results = await Promise.race([
  scoutAgent1.run(),
  scoutAgent2.run(),
  scoutAgent3.run(),
]);

// Plan phase - sequential (needs scout results)
const plan = await planAgent.run();

// Build phase - parallel file edits (if independent)
await Promise.all([
  editFile1(),
  editFile2(),
  editFile3(),
]);
```

# Report

After completing all 3 phases, report:

```markdown
# Scout → Plan → Build Complete

## Summary
**Task**: [USER_PROMPT]
**Total Time**: [scout_time + plan_time + build_time]
**Status**: ✅ COMPLETE

## Phase Breakdown

### 1️⃣ Scout ([scout_time])
- Agents: [SCALE] parallel
- Files found: [N]
- Collection: [path_to_collection]

### 2️⃣ Plan ([plan_time])
- Documentation: [DOCUMENTATION_URLS or "None"]
- Plan: [path_to_plan]
- Steps: [N]

### 3️⃣ Build ([build_time])
- Files modified: [N]
- Files created: [N]
- Tests: [passing/total]
- Commits: [N]

## Agent SDK Features Used
- ✅ Subagents (Scout phase)
- ✅ Context management (Auto-compaction)
- ✅ MCP servers (Documentation fetching)
- ✅ Hooks (.claude/settings.json)
- ✅ Tool permissions (Fine-grained control)
- ✅ Streaming (Build phase)

## Constitutional Compliance
- Article I: ✅ Complete context (all relevant files read)
- Article II: ✅ 100% tests passing
- Article III: ✅ Automated validation (hooks)
- Article IV: ✅ Learning stored (VectorStore)
- Article V: ✅ Spec-driven (plan.md)

## Next Steps
1. Review: git diff HEAD~[N]
2. Test: python run_tests.py --run-all
3. PR: gh pr create --title "[USER_PROMPT]"

**Ready for deployment** 🚀
```

---

## Implementation Notes

**This command uses the Claude Agent SDK pattern:**
- **TypeScript**: `@anthropic-ai/claude-agent-sdk`
- **Python**: `claude-agent-sdk`

**SDK handles automatically:**
- Context window management (auto-compaction)
- Prompt caching (system prompts, large contexts)
- Tool permission enforcement
- MCP server integration
- Hook execution (.claude/settings.json)

**Manual orchestration:**
- Phase sequencing (Scout → Plan → Build)
- Parallel agent spawning (Scout phase)
- Result aggregation and ranking

**Performance:**
- Scout: 2-5 seconds (parallel agents, fastest wins)
- Plan: 30-60 seconds (sequential, needs scout context)
- Build: 5-30 minutes (depends on task complexity)

**Total**: Under 35 minutes for most tasks.
