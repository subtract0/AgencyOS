## Mission: Planning & Execution from Specification

Your context is now focused on a complete development cycle, from planning to implementation, based on an existing specification.

### Workflow
1. **Understand Specification:** Read the specification file provided by the user.
2. **Delegate Planning:** Call `/agent planner` and pass the specification to create a detailed implementation plan.
3. **Design Architecture:** Call `/agent chief_architect` to make necessary ADRs and architecture decisions based on the plan.
4. **Implement Code:** For each task in the plan, call `/agent code_agent` to write and modify code.
5. **Create Tests:** Call `/agent test_generator` to ensure complete test coverage for the new code.
6. **Final Report:** Summarize results, created artifacts (plan, ADR, changed files) and test status.

### Start Context
- `/read constitution.md`
- Ask user for path to specification file (e.g. `specs/spec-XXX.md`).