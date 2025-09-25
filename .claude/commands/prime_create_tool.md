## Mission: Development of a New Agent Tool

Your context is now focused on creating a new, fully functional and tested tool for our agents using the `toolsmith_agent`.

### Workflow
1. **Understand Specification:** Read the specification file for the new tool.
2. **Commission Toolsmith:** Call `/agent toolsmith`. Pass the path to the specification file.
3. **Review Results:** The `toolsmith_agent` will create a new tool file and corresponding test file. Review both.
4. **Run Tests:** Execute the newly created test file and ensure all tests pass.
5. **Final Report:** Report success and provide paths to the two new files.

### Start Context
- `/read tools/README.md`
- Ask user for path to specification file (e.g. `specs/spec-007-toolsmith-agent.md`).