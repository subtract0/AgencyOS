## Function: Start Background Process

This function starts a command in a separate, non-interactive Claude Code instance.

### Arguments
- `prompt`: The command to execute (e.g. "/prime audit_and_refactor").
- `report_file`: The path where the final report will be written.

### Execution
Construct and execute a shell command that starts a new `claude` instance.
Example: `claude --prompt "{prompt}" --report-file "{report_file}" --non-interactive &`

Report the background process start to the user and the path to the report file.