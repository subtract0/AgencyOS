Operational Upgrade package
Files included:
- ai-dev-tasks/create-prd.md
- ai-dev-tasks/generate-tasks.md
- ai-dev-tasks/process-task-list.md
- .claude/commands/create_prd.md
- .claude/commands/generate_tasks.md
- .claude/commands/process_tasks.md
- claude.md.unified (replaced content)

Suggested branch name: feature/ai-dev-tasks-operational-upgrade
Suggested commit message: feat: add ai-dev-tasks framework & claude commands; update constitution (Development Protocol)

Suggested steps to apply to your repository (run from repo root):

1. Unpack the archive into your repo root:
   unzip agency_ai_dev_upgrade.zip -d .

2. Create and switch to a branch:
   git checkout -b feature/ai-dev-tasks-operational-upgrade

3. Review files, run tests, then add & commit:
   git add ai-dev-tasks .claude/claude.md.unified claude.md.unified
   git commit -m "feat: add ai-dev-tasks framework & claude commands; update constitution (Development Protocol)"

4. Push branch and open a PR:
   git push origin feature/ai-dev-tasks-operational-upgrade
   # Use GitHub UI or gh CLI to create the PR with title:
   # "Operational Upgrade: AI Dev Tasks + Development Protocol"

IMPORTANT: Replacing claude.md.unified is a significant governance change — review carefully before committing.
