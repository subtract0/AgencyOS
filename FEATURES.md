# Agency Code Features

This document provides a comprehensive inventory of features implemented in Agency Code.

## Core Agent Features

### Developer Agent
**Description**: Primary coding agent with full Claude Code tool set
**Test Coverage**: `tests/test_agency.py`

### Planner Agent
**Description**: Planning mode agent for task breakdown and strategy
**Test Coverage**: `tests/test_planner_agent.py`

### Subagent System
**Description**: Template-based creation of specialized agents
**Test Coverage**: `tests/test_handoffs_minimal.py`

## Memory API & Learning

### Memory API
**Description**: Core memory storage and retrieval system with pluggable backends
**Test Coverage**: `tests/test_memory_api.py`
**Key Components**:
- In-memory store (default)
- Firestore backend (optional)
- Memory search and tagging
- Session transcript generation

### Learning Consolidation
**Description**: Automated analysis and summarization of memory patterns
**Test Coverage**: `tests/test_learning_consolidation.py`
**Features**:
- Tag frequency analysis
- Content type categorization
- Time pattern detection
- Usage insights generation

### Session Transcripts
**Description**: Automatic logging of agent interactions and memory records
**Location**: `logs/sessions/`
**Format**: Markdown with timestamps and structured content

### Memory Integration Hooks
**Description**: System hooks for seamless memory integration across agent lifecycle
**Test Coverage**: `tests/test_hooks_memory_logging.py`

## Development Tools

### Bash Tool
**Description**: Execute shell commands with proper security handling
**Test Coverage**: `tests/test_bash_tool.py`

### File Operations
**Description**: File reading, writing, and editing capabilities
**Test Coverage**:
- `tests/test_read_tool.py`
- `tests/test_write_tool.py`
- `tests/test_edit_tool.py`

### Multi-Edit Tool
**Description**: Batch file editing with atomic operations
**Test Coverage**: `tests/test_multi_edit_tool.py`

### Search & Navigation
**Description**: Code search and file discovery tools
**Test Coverage**:
- `tests/test_grep_tool.py`
- `tests/test_glob_tool.py`
- `tests/test_ls_tool.py`

### Git Integration
**Description**: Version control operations and repository management
**Test Coverage**: `tests/test_git_tool.py`

### Notebook Support
**Description**: Jupyter notebook reading and editing capabilities
**Test Coverage**:
- `tests/test_notebook_read_tool.py`
- `tests/test_notebook_edit_tool.py`

## Planning & Organization

### Todo Management
**Description**: Task tracking and progress management
**Test Coverage**: `tests/test_todo_write_tool.py`

### Instruction Selection
**Description**: Dynamic instruction template selection based on model capabilities
**Test Coverage**: `tests/test_instructions_selection.py`

## System Features

### System Hooks
**Description**: Extensible hook system for agent lifecycle events
**Test Coverage**: `tests/test_system_reminder_hook.py`

### Agent Context
**Description**: Shared context and memory injection for agents
**Implementation**: `shared/agent_context.py`

### Tool Integration
**Description**: Seamless integration of all tools within agent workflows
**Test Coverage**: `tests/test_tool_integration.py`

## Configuration & Environment

### Environment Variables
- `FRESH_USE_FIRESTORE`: Enable Firestore backend for persistent memory
- `FIRESTORE_EMULATOR_HOST`: Local Firestore emulator configuration
- Standard LLM provider keys (OpenAI, Anthropic, etc.)

### Model Support
- GPT-5 with reasoning effort configuration
- Claude Sonnet 4 with advanced reasoning
- Flexible model switching via environment

## Testing Infrastructure

### Test Framework
- Pytest with async support
- Comprehensive fixture system
- Integration and unit test coverage

### Test Categories
- Tool functionality tests
- Agent behavior tests
- Memory system tests
- Integration workflow tests
- Hook system tests

---

*This feature inventory is maintained automatically. For feature coverage analysis, run the feature inventory script.*