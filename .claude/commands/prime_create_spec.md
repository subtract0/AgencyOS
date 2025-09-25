## Mission: Guided Specification Generation

Your primary objective is to collaborate with the user to create a comprehensive, well-defined specification for a new task. You will guide them through a structured process to ensure all necessary details are captured before any planning or implementation begins.

This interactive process ensures that the resulting specification is clear, actionable, and ready for the plan_and_execute workflow.

### Workflow
1. **Initiate Spec Creation:** Immediately call the `/create_spec` command to begin the interactive session with the user.
2. **Follow the Script:** Adhere strictly to the conversational flow defined in the `/create_spec` command.
3. **Produce Artifact:** The final output of this session will be a new markdown file in the `specs/` directory.

### Start Command
`/create_spec`