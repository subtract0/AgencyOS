# Agency Code Features

This document provides a comprehensive inventory of features implemented in Agency Code.

## 🤖 Autonomous Self-Healing (Revolutionary)

### Autonomous Healing System
**Description**: Complete autonomous error detection, fix generation, and application
**Test Coverage**: `tests/test_apply_and_verify_patch.py`, `tests/test_auto_fix_nonetype.py`
**Key Features**:
- Real-time NoneType error detection from logs
- LLM-powered fix generation using GPT-5
- Automatic patch application with test verification
- Safety rollback on failed patches
- Complete autonomous commit cycle

### Error Detection & Analysis
**Description**: Intelligent pattern recognition for common error types
**Test Coverage**: Integrated within autonomous healing tests
**Capabilities**:
- Log parsing and error extraction
- Context-aware error classification
- Automatic severity assessment
- File and line number identification

### Fix Generation & Application
**Description**: LLM-powered code fix generation and safe application
**Key Components**:
- GPT-5 prompt-based intelligent fixes
- ApplyAndVerifyPatch tool for complete cycles
- Automatic test verification before commit
- Rollback mechanisms for failed applications

## Core Multi-Agent Architecture (10 Agents)

### ChiefArchitectAgent
**Description**: Strategic oversight and self-directed task creation
**Test Coverage**: `tests/test_agency.py`

### AgencyCodeAgent
**Description**: Primary coding agent with full Claude Code tool set
**Test Coverage**: `tests/test_agency.py`

### PlannerAgent
**Description**: Planning mode agent for task breakdown and strategy
**Test Coverage**: `tests/test_planner_agent.py`

### QualityEnforcerAgent
**Description**: Constitutional compliance and quality enforcement with autonomous healing
**Test Coverage**: Comprehensive autonomous healing test suite
**Key Features**:
- Constitutional monitoring and enforcement
- Quality analysis and verification
- Autonomous healing integration
- Test validation and safety checks

### AuditorAgent
**Description**: CodeHealer integration and quality analysis
**Test Coverage**: `tests/test_auditor_agent.py`

### TestGeneratorAgent
**Description**: NECESSARY-compliant test generation
**Test Coverage**: `tests/test_test_generator_agent.py`

### LearningAgent
**Description**: Pattern analysis and institutional memory
**Test Coverage**: `tests/test_learning_agent.py`

### ToolsmithAgent
**Description**: Dynamic tool creation and enhancement
**Test Coverage**: `tests/test_toolsmith_agent.py`

### MergerAgent
**Description**: Integration and pull request management
**Test Coverage**: `tests/test_merger_agent.py`

### WorkCompletionSummaryAgent
**Description**: Audio summaries and task completion reporting
**Test Coverage**: `tests/test_work_completion_summary_agent.py`

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

## 🏛️ Constitutional Governance

### Constitutional Enforcement
**Description**: Automated enforcement of 5 constitutional articles
**Key Articles**:
- Article I: Complete Context Before Action
- Article II: 100% Verification (689 tests passing)
- Article III: Automated Enforcement
- Article IV: Continuous Learning
- Article V: Spec-Driven Development

### Quality Gates
**Description**: Technical enforcement of quality standards
**Features**:
- 100% test success rate requirement
- Automatic rollback on violations
- Zero-tolerance policy for constitutional breaches

## Development Tools

### CLI Helper (World-Class UX)
**Description**: Professional command-line interface for all operations
**Script**: `./agency_cli`
**Commands**:
- `setup`: One-command environment configuration
- `test`: Complete test suite execution
- `demo`: Autonomous healing demonstration
- `run`: Agency execution with proper environment
- `health`: System health and constitutional compliance monitoring
- `logs`: Session transcript viewing

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