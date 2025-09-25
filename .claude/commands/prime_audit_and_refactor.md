## Mission: Code Audit & Refactoring

Your context is now focused on conducting a complete code analysis and subsequent fixing of identified issues.

### Workflow
1. **Conduct Audit:** Call `/agent auditor` to scan the entire codebase (`agency/`, `tools/`, etc.).
2. **Analyze Report:** Wait for the auditor's JSON report. Analyze results and identify the most critical issues.
3. **Plan Refactoring:** Create a detailed plan to fix the 3 most important issues.
4. **Delegate Implementation:** For each item in the plan, call `/agent code_agent` to perform the refactoring.
5. **Verify:** Run relevant tests to confirm successful implementation.

### Start Context
- `/read constitution.md`
- `/read docs/adr/ADR-INDEX.md`