---
description: Search the codebase for files needed to complete the task using fast, parallel agents
argument-hint: [user-prompt] [scale]
model: claude-sonnet-4-5-20250929
---

# Purpose

Search the codebase for files needed to complete the task using a fast, token efficient agent. Spawns multiple parallel search agents (CLI tools via Bash) to quickly find relevant files.

# Variables

- `user_prompt`: Description of what you're looking for (e.g., "authentication middleware", "database models")
- `scale`: Number of parallel agents to spawn (1-5, default: 3)

# Workflow

Write a prompt for `SCALE` number of agents to the Task tool that will immediately call the Bash tool to run these commands to kick off your agents to conduct the search:
- `gemini -p "[prompt]" --model gemini-2.5-flash-preview-09-2025`
- `opencode run [prompt] --model cerebras/qwen-3-coder-480b` (if count >= 2)
- `gemini -p "[prompt]" --model gemini-2.5-flash-lite-preview-09-2025` (if count >= 3)
- `codex exec -m gpt-5-codex -s read-only -c model_reasoning_effort="low" "[prompt]"` (if count >= 4)
- `opencode run [prompt] --model haiku` (if count >= 5)

## How to prompt the agents:

- IMPORTANT: Kick these agents off in parallel using the Task tool.
- IMPORTANT: These agents are calling OTHER agentic coding tools to search the codebase. DO NOT call any search tools yourself.
- IMPORTANT: That means with the Task tool, you'll immediately call the Bash tool to run the respective agentic coding tool (gemini, opencode, claude, etc.)
- IMPORTANT: Instruct the agents to quickly search the codebase for files needed to complete the task. This isn't about a full blown search, just a quick search to find the files needed to complete the task.
- Instruct the subagent to use a timeout of 3 minutes for each agent's bash call. Skip any agents that don't return within the timeout, don't restart them.
- Make it absolutely clear that the Task tool is ONLY going to call the Bash tool and pass in the appropriate prompt, replacing the [prompt] with the actual prompt you want to run.
- Make it absolutely clear the agent is NOT implementing the task, the agent is ONLY searching the codebase for files needed to complete the task.
- Prompt the agent to return a structured list of files with specific line ranges in this format:
  - `<path to file> (offset: N, limit: M)` where offset is the starting line number and limit is the number read
- If there are multiple relevant sections in the same file, repeat the entry with different offset/limit values.
- Execute additional agent calls in round robin fashion.
- Give them the relevant information needed to complete the task.

# Report

Return structured results ranked by relevance:

```
## Scout Search Results

**Query**: [user_prompt]
**Agents Spawned**: [scale]
**Agent Responses**: [N successful / M timeout]

### Results (Ranked by Relevance)
1. `path/to/file.py` (offset: 42, limit: 100) - score: 0.96
   Context: [Agent's description of what's in this section]

2. `path/to/file.py` (offset: 200, limit: 75) - score: 0.92
   Context: [Different section of same file]

3. `another/file.py` (offset: 15, limit: 50) - score: 0.89
   Context: [Relevant code section]

### Agent Performance
- Agent 1 (gemini-flash): 1.2s ✅
- Agent 2 (cerebras): 2.5s ✅
- Agent 3 (gemini-lite): timeout ⏭️
- Agent 4 (codex): skipped (scale=3)
- Agent 5 (haiku): skipped (scale=3)

**Total Time**: 2.5s (fastest agent wins)
```

---

**Remember**: You are orchestrating search agents via CLI tools. DO NOT search yourself - delegate to parallel Bash calls.
