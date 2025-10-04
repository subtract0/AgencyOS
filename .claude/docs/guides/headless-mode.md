# Headless mode

Headless mode lets Claude Code run without a terminal UI—perfect for automation, CI/CD pipelines, scripts, and server deployments. Instead of interactive conversations, you send instructions programmatically and receive structured responses.

## What is headless mode?

In headless mode, Claude Code:

- Accepts input via **command-line arguments** or **stdin**.
- Executes tasks autonomously (no interactive prompts).
- Returns output as **structured JSON** or **plain text**.
- Exits after task completion (no persistent session).

Think of it as turning Claude Code into a **CLI tool** or **API**.

## Use cases

1. **CI/CD pipelines**: Run tests, generate reports, validate code quality.
2. **Automation scripts**: Trigger Claude Code from cron jobs, webhooks, or orchestration tools.
3. **Batch processing**: Process multiple tasks in sequence without manual input.
4. **Server deployments**: Embed Claude Code in backend services (e.g., code review bots).
5. **Integration testing**: Automate Claude Code workflows in test suites.

## Basic usage

### Command-line mode

Run a single task and exit:

```bash
claude-code --headless "Write unit tests for auth.py"
```

**Output (JSON):**

```json
{
  "status": "success",
  "result": {
    "files_created": ["test_auth.py"],
    "tests_written": 12,
    "summary": "Generated 12 unit tests covering authentication flows"
  }
}
```

### Stdin mode

Pipe instructions to Claude Code:

```bash
echo "Refactor user_service.py to use async/await" | claude-code --headless --stdin
```

### Batch mode

Process multiple tasks from a file:

```bash
# tasks.txt:
# Write tests for auth.py
# Refactor database.py
# Update README with API docs

claude-code --headless --batch tasks.txt
```

## Configuration

### Output format

Choose JSON or plain text:

```bash
# JSON output (default)
claude-code --headless --format json "Fix linting errors"

# Plain text output
claude-code --headless --format text "Fix linting errors"
```

### Timeout

Set maximum execution time (default: 5 minutes):

```bash
claude-code --headless --timeout 600 "Run all tests"  # 10 minutes
```

### Working directory

Run in a specific directory:

```bash
claude-code --headless --cwd /path/to/project "Build the application"
```

### Environment variables

Pass variables to Claude Code:

```bash
GITHUB_TOKEN=xyz claude-code --headless "Create a GitHub issue"
```

## Advanced patterns

### 1. Exit codes

Claude Code uses standard exit codes:

- `0`: Success
- `1`: Task failed (e.g., tests didn't pass)
- `2`: Invalid input (e.g., malformed instruction)
- `3`: Timeout exceeded

**Example (CI/CD):**

```bash
#!/bin/bash
claude-code --headless "Run tests and report coverage"
if [ $? -eq 0 ]; then
  echo "Tests passed"
else
  echo "Tests failed"
  exit 1
fi
```

### 2. Structured output parsing

Parse JSON output in scripts:

```bash
result=$(claude-code --headless --format json "Count files in src/")
file_count=$(echo "$result" | jq -r '.result.count')
echo "Found $file_count files"
```

### 3. Chaining tasks

Run multiple tasks in sequence:

```bash
claude-code --headless "Write tests for auth.py" && \
claude-code --headless "Run tests and fix failures" && \
claude-code --headless "Commit changes"
```

### 4. Parallel execution

Run tasks in parallel (use with caution—can cause file conflicts):

```bash
claude-code --headless "Refactor auth.py" &
claude-code --headless "Update README" &
wait
```

### 5. Logging

Redirect output to a log file:

```bash
claude-code --headless "Build project" > build.log 2>&1
```

## CI/CD integration

### GitHub Actions

```yaml
# .github/workflows/claude-review.yml
name: Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Claude Code
        run: pip install claude-code
      - name: Run review
        run: |
          claude-code --headless "Review changes in this PR and suggest improvements" > review.txt
          cat review.txt >> $GITHUB_STEP_SUMMARY
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test

claude_test:
  stage: test
  script:
    - pip install claude-code
    - claude-code --headless "Run all tests and report results"
```

### Jenkins

```groovy
// Jenkinsfile
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh 'claude-code --headless "Run integration tests"'
            }
        }
    }
}
```

### CircleCI

```yaml
# .circleci/config.yml
version: 2.1
jobs:
  test:
    docker:
      - image: python:3.11
    steps:
      - checkout
      - run: pip install claude-code
      - run: claude-code --headless "Validate code quality"
```

## Server mode

Run Claude Code as a persistent HTTP server:

```bash
claude-code --server --port 8080
```

### API endpoints

**POST /execute**

```bash
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Write tests for auth.py"}'
```

**Response:**

```json
{
  "status": "success",
  "result": {
    "files_created": ["test_auth.py"],
    "summary": "Generated 12 tests"
  }
}
```

**GET /health**

```bash
curl http://localhost:8080/health
# {"status": "ok"}
```

### Authentication

Protect the server with an API key:

```bash
claude-code --server --api-key your-secret-key
```

**Request:**

```bash
curl -X POST http://localhost:8080/execute \
  -H "Authorization: Bearer your-secret-key" \
  -d '{"instruction": "..."}'
```

## Best practices

### 1. Keep instructions specific

Vague instructions lead to unpredictable results:

**Bad:**

```bash
claude-code --headless "Fix the code"
```

**Good:**

```bash
claude-code --headless "Fix linting errors in src/auth.py and src/database.py"
```

### 2. Set timeouts

Long-running tasks can hang in headless mode—always set a timeout:

```bash
claude-code --headless --timeout 300 "Run full test suite"
```

### 3. Validate output

Parse JSON responses to detect failures:

```bash
result=$(claude-code --headless --format json "Run tests")
status=$(echo "$result" | jq -r '.status')
if [ "$status" != "success" ]; then
  echo "Task failed"
  exit 1
fi
```

### 4. Use environment variables for secrets

Never hardcode tokens in scripts:

```bash
export GITHUB_TOKEN=xyz
claude-code --headless "Create GitHub issue"
```

### 5. Log everything

In automated environments, logs are critical for debugging:

```bash
claude-code --headless "Deploy to staging" 2>&1 | tee deploy.log
```

### 6. Test locally first

Before running in CI/CD, test headless commands locally:

```bash
claude-code --headless --dry-run "Deploy to production"
```

## Error handling

### Timeouts

If a task exceeds `--timeout`, Claude Code exits with code `3`:

```bash
claude-code --headless --timeout 10 "Long running task"
# Exit code: 3
```

### Invalid instructions

Malformed or ambiguous instructions exit with code `2`:

```bash
claude-code --headless "asdfghjkl"
# Exit code: 2
# Error: Unable to parse instruction
```

### Task failures

If Claude Code can't complete the task (e.g., tests fail), exit code is `1`:

```bash
claude-code --headless "Run tests"
# Exit code: 1
# Result: {"status": "failure", "errors": ["3 tests failed"]}
```

## Limitations

1. **No interactivity**: Can't ask follow-up questions or clarify instructions.
2. **Context limits**: Each headless invocation is isolated (no session history).
3. **Resource usage**: Spinning up Claude Code repeatedly is slower than persistent sessions.
4. **Debugging**: Harder to troubleshoot without interactive feedback.

## Alternatives to headless mode

| Use case                 | Recommended approach                                  |
| ------------------------ | ----------------------------------------------------- |
| One-off tasks            | Headless mode                                         |
| Long-running workflows   | Server mode                                           |
| Interactive development  | CLI mode                                              |
| Complex multi-step tasks | Use [subagents](../features/subagents.md) in CLI mode |

## Example workflows

### 1. Automated code review

```bash
#!/bin/bash
# review.sh - Run on every commit

git diff HEAD~1 > changes.diff
claude-code --headless "Review changes in changes.diff and suggest improvements" > review.txt

if grep -q "CRITICAL" review.txt; then
  echo "Critical issues found!"
  cat review.txt
  exit 1
fi
```

### 2. Nightly test generation

```bash
#!/bin/bash
# generate_tests.sh - Run daily via cron

for file in src/**/*.py; do
  if [ ! -f "tests/test_$(basename $file)" ]; then
    claude-code --headless "Write unit tests for $file"
  fi
done
```

### 3. PR validation

```bash
#!/bin/bash
# validate_pr.sh - GitHub Actions

claude-code --headless "Check if all files in src/ have corresponding tests" > validation.json
has_tests=$(jq -r '.result.all_tested' validation.json)

if [ "$has_tests" != "true" ]; then
  echo "Some files lack tests"
  exit 1
fi
```

### 4. Release automation

```bash
#!/bin/bash
# release.sh

version=$(cat VERSION)
claude-code --headless "Update CHANGELOG.md with version $version"
claude-code --headless "Run full test suite"
claude-code --headless "Build and tag release $version"
```

## FAQ

**Q: Can headless mode use MCP servers?**
A: Yes. Configure MCP in `.claude/config.json` as usual.

**Q: Can I pass files as input?**
A: Yes, via stdin or by referencing file paths in instructions.

**Q: Does headless mode support hooks?**
A: Yes. Hooks run normally in headless mode.

**Q: Can I run headless mode in Docker?**
A: Yes. Use a minimal base image (e.g., `python:3.11-slim`) and install Claude Code.

**Q: How do I debug headless failures?**
A: Add `--debug` flag: `claude-code --headless --debug "..."` (logs to stderr).

**Q: Can headless mode modify files?**
A: Yes. It has the same permissions as CLI mode.

---

**Next steps:**

- Set up a CI/CD pipeline with headless mode.
- Build a code review bot using server mode.
- Automate test generation with a nightly cron job.
