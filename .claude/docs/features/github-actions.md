# Claude Code GitHub Actions

You can use Claude Code in GitHub Actions to automate code reviews, testing, and other development workflows.

## Setup

1. Add your Anthropic API key to your repository secrets:
   - Go to your repository Settings → Secrets and variables → Actions
   - Add a new secret named `ANTHROPIC_API_KEY`

2. Create a workflow file (e.g., `.github/workflows/claude-code.yml`):

```yaml
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code

      - name: Run Code Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          claude-code --non-interactive "Review the changes in this PR for potential issues"
```

## Use Cases

### Automated Code Review

```yaml
- name: Review PR
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    claude-code --non-interactive "Review this PR for:
    - Code quality issues
    - Security vulnerabilities
    - Performance concerns
    - Best practice violations"
```

### Test Generation

```yaml
- name: Generate Tests
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    claude-code --non-interactive "Generate unit tests for any new functions that lack test coverage"
```

### Documentation Updates

```yaml
- name: Update Documentation
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    claude-code --non-interactive "Review and update documentation to reflect code changes in this PR"
```

## Configuration

### Non-Interactive Mode

GitHub Actions requires non-interactive mode:

```bash
claude-code --non-interactive "your prompt here"
```

### Custom Instructions

You can provide custom instructions via a file:

```yaml
- name: Run with Custom Instructions
  run: |
    claude-code --non-interactive --claude-md .github/claude-instructions.md "Review this code"
```

### Output Artifacts

Save Claude Code output as artifacts:

```yaml
- name: Save Review Output
  uses: actions/upload-artifact@v4
  with:
    name: claude-review
    path: .claude/logs/
```

## Best Practices

1. **Limit Scope**: Focus on specific tasks to avoid hitting token limits
2. **Cache Dependencies**: Use GitHub Actions caching for faster runs
3. **Set Timeouts**: Add timeouts to prevent long-running jobs
4. **Handle Failures**: Use `continue-on-error` for non-critical tasks

```yaml
- name: Optional Review
  continue-on-error: true
  timeout-minutes: 10
  run: claude-code --non-interactive "Review code"
```

## Security Considerations

- Never commit API keys to your repository
- Use repository secrets for sensitive data
- Limit workflow permissions:

```yaml
permissions:
  contents: read
  pull-requests: write # Only if commenting on PRs
```

## Troubleshooting

### Rate Limits

If you hit rate limits, consider:

- Running reviews only on specific file types
- Using conditional workflows
- Implementing retry logic

### Large Repositories

For large repos:

- Focus on changed files only
- Use git diff to limit scope
- Split tasks across multiple jobs

```yaml
- name: Review Changed Files Only
  run: |
    CHANGED_FILES=$(git diff --name-only origin/main...HEAD)
    claude-code --non-interactive "Review these files: $CHANGED_FILES"
```
