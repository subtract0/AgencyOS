# Subagents

Subagents let you delegate specific subtasks to specialized agents. They're isolated—separate conversations with independent context. This keeps main threads focused while letting parallel agents handle detailed work.

## Use cases

- **Parallel subtasks**: Break complex work into isolated chunks that run independently.
- **Role specialization**: Spin up expert agents (e.g., a testing specialist, a documentation writer).
- **Context isolation**: Keep main threads clean—subagents handle noise (research, parsing logs).
- **Sandboxed experiments**: Try risky changes without affecting the main agent's state.

## What are subagents?

Subagents are fully functional Claude Code instances running independently from the main agent. Think of them as coworkers you spin up for specific jobs. Each subagent has:

- **Independent conversation context**: It doesn't share your main thread's memory.
- **Full tool access**: File operations, git commands, bash execution—same capabilities as the main agent.
- **Isolated workspace**: Changes happen in the same filesystem, but decisions are independent.
- **Automatic cleanup**: When done, the subagent's context disappears—work persists, clutter doesn't.

## Key behaviors

### When subagents make sense

- **Clear subtask boundary**: "Write unit tests for auth module" or "Research rate limiting patterns."
- **Independent decisions**: The subtask doesn't need back-and-forth with the main agent.
- **Parallel execution**: Multiple subagents can run at once (each in its own thread).

### When to avoid subagents

- **Tight coupling**: If the subtask requires constant main-agent input, keep it in the main thread.
- **Trivial tasks**: Reading a file or running `ls`? Don't delegate—use tools directly.
- **State synchronization**: If success depends on coordinating with the main agent mid-task, subagents add friction.

## How to use subagents

### Basic syntax

Request a subagent by asking Claude Code to delegate a task:

```
Create a subagent to write integration tests for the API endpoints.
```

Claude Code will:

1. Spin up the subagent in a new thread.
2. Give it clear instructions (you can review and refine).
3. Let it work autonomously.
4. Report results back to you.

### Example workflow

**Main agent context:**

```
You: Refactor the authentication module. Use a subagent to handle test updates.
```

**Claude Code response:**

```
I'll refactor the auth module. Spinning up a subagent to update tests in parallel.

Subagent task: Update all authentication tests to match the new AuthService interface.
```

**Subagent (in separate thread):**

```
[Subagent analyzes AuthService changes]
[Subagent updates test files]
[Subagent runs test suite]
Result: 24 tests updated, all passing.
```

**Main agent:**

```
Refactoring complete. Subagent reports tests are updated and green.
```

### Controlling subagents

You can guide subagent behavior through your instructions:

```
Create a subagent to research best practices for rate limiting.
Give it access to WebSearch and limit the task to 15 minutes.
```

Claude Code will configure the subagent accordingly (tools, constraints, focus).

## Best practices

### 1. Define clear deliverables

Bad:

```
Subagent: Make the code better.
```

Good:

```
Subagent: Refactor UserRepository to use the Builder pattern and update all call sites.
```

### 2. Isolate noisy work

Use subagents for tasks that generate clutter (logs, research notes, experimental code):

```
Main agent: Implement feature X.
Subagent: Parse the 5,000-line API spec and extract endpoint schemas.
```

### 3. Parallelize when possible

Multiple independent subtasks? Spin up multiple subagents:

```
Subagent A: Write unit tests for controllers.
Subagent B: Write integration tests for database layer.
Subagent C: Update API documentation.
```

### 4. Review before merging

Subagents work autonomously, but you're the integrator. Always review their output:

```
Subagent completed tests. Review: [show me the diff]
```

### 5. Don't over-delegate

If the task needs your judgment every 2 minutes, keep it in the main thread.

## Technical details

### Context boundaries

- **Filesystem**: Shared (changes persist).
- **Conversation history**: Isolated (subagent doesn't see main thread messages).
- **Tool state**: Independent (separate bash sessions, git state, etc.).

### Lifecycle

1. **Spawn**: Main agent creates subagent with task definition.
2. **Execute**: Subagent runs autonomously (can use all tools).
3. **Report**: Subagent summarizes results to main agent.
4. **Cleanup**: Subagent context is discarded (work persists).

### Communication

- **One-way**: Main agent → subagent (via task definition).
- **Results-only**: Subagent → main agent (summary at completion).
- **No mid-task sync**: Subagents don't interrupt the main agent for input.

## Limitations

- **No shared memory**: Subagents can't access the main thread's conversation context.
- **No real-time coordination**: If the main agent changes strategy, the subagent won't know unless you cancel it.
- **Resource overhead**: Each subagent is a full Claude Code instance—don't spawn dozens simultaneously.

## Example patterns

### Research assistant

```
Main: Implement OAuth2 flow.
Subagent: Research OAuth2 security best practices and create a checklist.
```

### Test specialist

```
Main: Refactor PaymentService.
Subagent: Generate comprehensive unit tests for the new PaymentService API.
```

### Documentation writer

```
Main: Build new API endpoints.
Subagent: Write OpenAPI specs and usage examples for the new endpoints.
```

### Experiment sandbox

```
Main: Consider migrating to library X.
Subagent: Prototype library X integration in a feature branch and report findings.
```

## FAQ

**Q: Can subagents create their own subagents?**
A: No. Only the main agent can spawn subagents (prevents runaway delegation).

**Q: How do I cancel a subagent?**
A: Ask the main agent: `Cancel the test generation subagent.`

**Q: Can I talk to a subagent directly?**
A: No. Subagents are autonomous. Communicate through the main agent.

**Q: Do subagents cost extra?**
A: They use API calls like any Claude Code operation. Be mindful of parallel subagents.

**Q: Can subagents access secrets/env vars?**
A: Yes—same permissions as the main agent. Don't delegate sensitive tasks to untrusted code.

---

**Next steps:**

- Try delegating a test-writing task to a subagent.
- Use subagents for research tasks that would clutter your main thread.
- Experiment with parallel subagents for independent refactoring work.
