# Tool Quick Reference Index

**Fast lookup of 45 available tools**

## File Operations
- `read.py` - Read files with line ranges
- `write.py` - Write files (prefer Edit for existing)
- `edit.py` - Edit existing files (exact string replacement)
- `multi_edit.py` - Multiple edits in one operation
- `glob.py` - Find files by pattern
- `grep.py` - Search file contents (ripgrep)
- `ls.py` - List directory contents

## Git Workflow
- `git.py` - Basic git operations
- `git_workflow.py` - Professional workflow automation
- `git_workflow_tool.py` - Branch → commit → PR
- `git_unified.py` - Unified git interface

## Code Quality
- `constitution_check.py` - Validate Article I-V compliance
- `analyze_type_patterns.py` - Type safety analysis
- `quality/no_dict_any_check.py` - Zero Dict[Any] validation
- `auto_fix_nonetype.py` - Autonomous NoneType healing
- `apply_and_verify_patch.py` - Safe patch application

## Execution & Monitoring
- `bash.py` - Shell command execution
- `todo_write.py` - Task list management
- `telemetry/aggregator.py` - Metrics aggregation
- `agency_cli/dashboard.py` - System dashboard
- `agency_cli/tail.py` - Log tailing
- `agency_cli/self_healing.py` - Healing status

## Code Generation
- `codegen/scaffold.py` - Generate boilerplate
- `codegen/test_gen.py` - Auto-generate tests
- `codegen/analyzer.py` - Code analysis

## Advanced Tools
- `learning_dashboard.py` - Learning metrics
- `document_generator.py` - Doc generation
- `spec_traceability.py` - Spec → code tracing
- `feature_inventory.py` - Feature catalog
- `anthropic_agent.py` - Claude Agent SDK wrapper

## Orchestration
- `orchestrator/api.py` - Orchestration API
- `orchestrator/scheduler.py` - Task scheduling
- `orchestrator/graph.py` - Dependency graphs

## Kanban & Observability
- `kanban/server.py` - Minimal Kanban UI
- `kanban/adapters.py` - TodoWrite → Kanban
- `kanban/hints.py` - Runtime hints
- `kanban/untracked.py` - Untracked file detection

## Context Management
- `context_handoff.py` - Inter-agent context
- `handoff_context_read.py` - Read handoff state
- `exit_plan_mode.py` - Exit planning mode
- `undo_snapshot.py` - Rollback snapshots

## Web & Research
- `claude_web_search.py` - Web search capability

## Notebook Support
- `notebook_read.py` - Read Jupyter notebooks
- `notebook_edit.py` - Edit notebook cells

---

**Total Tools**: 45 production tools
**Constitutional Requirement**: All tools use Result<T,E> pattern
