# Tool Integration Fix Plan - Claude Code Agent

**Issue**: Agent is not using any of the 15 available tools despite being properly configured  
**Impact**: CRITICAL - Core functionality completely broken  
**Priority**: IMMEDIATE FIX REQUIRED

## Problem Summary

The Claude Code Agent has 15 fully functional tools but completely fails to use them:
- Tools import successfully and work when tested individually
- Agent responds with text guidance instead of executing tools
- Explicit tool requests are ignored ("I can't do that")
- Agent's tools attribute shows as empty despite proper `tools_folder` configuration

## Immediate Fix Actions

### 1. Fix Agent Configuration (CRITICAL)

**Current broken configuration**:
```python
claude_code_agent = Agent(
    name="ClaudeCodeAgent",
    # ... other params
    model="gpt-4o",
    temperature=0.5,  # DEPRECATED
    max_tokens=25000,  # INVALID
)
```

**Fixed configuration**:
```python
from agency_swarm import Agent

claude_code_agent = Agent(
    name="ClaudeCodeAgent",
    description="...",
    instructions="./instructions.md",
    tools_folder="./tools",
    model="gpt-4o"
    # Remove deprecated temperature and max_tokens parameters
)
```

### 2. Verify Tool Loading (HIGH PRIORITY)

**Test script to diagnose tool loading**:
```python
# Add to debug test
print(f"Agent tools: {claude_code_agent.tools}")
print(f"Tools folder: {claude_code_agent.tools_folder}")

# Check if tools are actually loaded
if hasattr(claude_code_agent, '_tools') or hasattr(claude_code_agent, 'tools'):
    print("Tools attribute found")
else:
    print("ERROR: No tools attribute found")
```

### 3. Strengthen Instructions (MEDIUM PRIORITY)

**Add to instructions.md**:
```markdown
# CRITICAL TOOL USAGE DIRECTIVE
- ALWAYS use available tools to complete tasks
- NEVER provide code examples or instructions when tools are available
- When asked to list files, immediately use the LS tool
- When asked to search files, immediately use the Grep tool  
- When asked to create files, immediately use the Write tool
- When asked to run commands, immediately use the Bash tool
- When asked to fetch web content, immediately use WebSearch/WebFetch tools

# Tool Usage Examples
User: "List files in current directory"
Correct: [Use LS tool with current directory path]
Wrong: "Here's a script to list files..."

User: "Search for TODO comments"  
Correct: [Use Grep tool with TODO pattern]
Wrong: "You can use this script to search..."
```

### 4. Test Framework Updates (MEDIUM PRIORITY)

**Enhanced test queries**:
```python
# Force tool usage with explicit commands
test_queries = [
    "EXECUTE the LS tool to list files in /Users/vrsen/Areas/Development/code/agency-swarm/claude_code",
    "RUN the Bash tool to execute 'git status'",
    "USE the Write tool to create a file called test.py with content '# test'",
    "INVOKE the Grep tool to search for 'import' in Python files",
    "CALL the WebSearch tool to search for 'Agency Swarm documentation'"
]
```

## Investigation Steps

### Step 1: Agency Swarm Version Compatibility
```bash
# Check if tools need different format for v1.0.0
pip show agency-swarm
python -c "from agency_swarm.tools import BaseTool; print(BaseTool.__module__)"
```

### Step 2: Tool Registration Debug
```python
# Test if tools can be manually registered
from tools.ls import LS
from agency_swarm import Agent

agent = Agent(
    name="TestAgent",
    tools=[LS],  # Explicit tool list instead of tools_folder
    instructions="Use the LS tool when asked."
)
```

### Step 3: Framework Integration Check
```python
# Check if there's a different way to load tools in v1.0.0
from agency_swarm import Agency
print(dir(Agency))  # Check available methods
print(dir(claude_code_agent))  # Check agent attributes
```

## Quick Fix Implementation Order

1. **Fix agent configuration** (5 minutes)
2. **Test with single tool** (10 minutes)  
3. **Update instructions** (15 minutes)
4. **Run focused test** (10 minutes)
5. **Debug tool loading if still broken** (30 minutes)

## Success Verification

After each fix, test with this simple query:
```
"Use the LS tool right now to show me files in the current directory"
```

**Expected**: Agent executes LS tool and shows actual file listing
**Current**: Agent says "I can't do that" or provides script

## Emergency Workaround

If tool integration cannot be fixed immediately:
1. Create a simple test agent with just 1-2 tools
2. Use explicit tool list instead of `tools_folder`
3. Test basic functionality before expanding

## Next Actions

1. **IMMEDIATE**: Update claude_code_agent.py configuration
2. **15 MINUTES**: Test single tool integration
3. **30 MINUTES**: If still broken, investigate Agency Swarm v1.0.0 compatibility
4. **1 HOUR**: Full tool integration testing and validation

This is a blocking issue that must be resolved before any production deployment.