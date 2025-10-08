---
description: Develop a new agent tool via ToolsmithAgent (TDD, API design, testing)
settingSources: [project]
---

## Mission: Development of a New Agent Tool

Your context is now focused on creating a new, fully functional and tested tool for our agents using the `toolsmith_agent`.

### SDK Tool Development Pattern

When creating MCP tools for Agency, use the Claude Agent SDK's `@tool` decorator:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("analyze_code", "Analyze code for quality issues", {
    "file_path": str,
    "check_type": str  # "quality" | "security" | "performance"
})
async def analyze_code(args):
    """Analyze code file for issues."""
    file_path = args["file_path"]
    check_type = args["check_type"]

    # Implementation using Agency patterns
    from shared.type_definitions.result import Result, Ok, Err
    result = perform_analysis(file_path, check_type)

    if result.is_ok():
        return {
            "content": [{
                "type": "text",
                "text": f"Analysis complete: {result.unwrap()}"
            }]
        }
    return {
        "content": [{
            "type": "text",
            "text": f"Error: {result.unwrap_err()}"
        }],
        "isError": True
    }

# Register tool with Agency
tool_server = create_sdk_mcp_server(
    name="agency_analysis",
    version="1.0.0",
    tools=[analyze_code]
)
```

### Workflow
1. **Understand Specification:** Read the specification file for the new tool.
2. **Commission Toolsmith:** Call `/agent toolsmith`. Pass the path to the specification file.
3. **Review Results:** The `toolsmith_agent` will create a new tool file and corresponding test file. Review both.
4. **Run Tests:** Execute the newly created test file and ensure all tests pass.
5. **Final Report:** Report success and provide paths to the two new files.

### Start Context
- `/read tools/README.md`
- Ask user for path to specification file (e.g. `specs/spec-007-toolsmith-agent.md`).