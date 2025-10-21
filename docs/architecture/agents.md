# 🤖 Agency Agent Architecture

## 🚨 WARP RULES (CONSTITUTIONAL ENFORCEMENT)

### ARTICLE I: COMPLETE CONTEXT BEFORE ACTION - NO HANGING COMMANDS
**THIS IS FORBIDDEN AND VIOLATES THE CONSTITUTION:**
- NEVER leave hanging commands running (e.g., `gh pr checks --watch`)
- NEVER leave open interactive windows that require user input (e.g., "press :qa")
- NEVER leave processes in an incomplete state
- ALL operations must be FULLY COMPLETED before response ends
- If a command hangs or requires interaction: TERMINATE IT and find alternative approach
- Use non-interactive flags: `--no-pager`, `--non-interactive`, `--batch`, etc.
- Constitutional violation: Article I - Complete Context Before Action

### FULL CONSTITUTION INTEGRATION
All agents must operate under the complete Agency Constitution:

**Article I: Complete Context Before Action**
- No action without complete contextual understanding
- At timeouts: halt and retry with 2x, 3x, up to 10x extended timeouts  
- ALL tests must run to completion
- NEVER proceed with incomplete data
- No broken windows tolerance

**Article II: 100% Verification and Stability**
- Main branch MUST maintain 100% test success
- No merge without green CI pipeline
- Tests verify REAL functionality, not simulated behavior
- "Delete the Fire First" priority always

**Article III: Automated Merge Enforcement** 
- Quality standards technically enforced, not manually governed
- No manual override capabilities
- No bypass authority for anyone
- Quality gates are absolute barriers

**Article IV: Continuous Learning and Improvement**
- Agency continuously improves through experiential learning
- VectorStore integration mandatory (USE_ENHANCED_MEMORY=true)
- All agents query learnings before decisions
- Store successful patterns after operations

**Article V: Spec-Driven Development**
- All development follows formal specification processes
- New features begin with formal spec.md
- Plans decompose into verifiable tasks
- Progress tracking required throughout

**Article VI: Red-Green-Refactor TDD Workflow**
- Tests written FIRST (must fail initially)
- Implementation ONLY after failing tests exist
- 100% pass rate required before completion
- No "pragmatic shortcuts" that skip RED phase

---

Comprehensive documentation of the Agency's 10-agent architecture, their roles, responsibilities, and communication patterns.

## 🏗️ Architecture Overview

The Agency uses a **simplified, focused multi-agent architecture** with clear responsibilities and streamlined communication flows. Each agent is specialized for specific tasks while maintaining constitutional compliance and autonomous healing capabilities.

### Design Principles
- **Constitutional Compliance**: All agents operate under the six constitutional articles
- **LLM-First Design**: Complex analysis delegated to GPT-5 rather than custom Python systems
- **Focused Responsibilities**: Each agent has clear, non-overlapping duties
- **Autonomous Healing**: Quality and error recovery capabilities built into the system
- **Cross-Agent Learning**: Shared memory and knowledge across all agents

## 🎯 Core Agents

### 1. ChiefArchitectAgent
**Role**: Strategic oversight and self-directed task creation

**Key Responsibilities**:
- Provides high-level architectural guidance and strategic direction
- Creates `[SELF-DIRECTED TASK]` entries for system improvements
- Reviews audit findings and VectorStore knowledge for optimization opportunities
- Coordinates between all other agents for complex multi-agent workflows
- Monitors overall system health and performance

**Communication Patterns**:
- **Outbound**: All agents (strategic oversight)
- **Decision Authority**: High-level architectural decisions
- **Trigger Conditions**: System health issues, audit findings, performance concerns

---

### 2. CodingAgent (Coder)
**Role**: Primary development agent with comprehensive toolset

**Key Responsibilities**:
- Core software development and implementation
- File operations (read, write, edit, multi-edit)
- Code execution and testing
- Git operations and version control
- Direct implementation of plans and fixes

**Tools & Capabilities**:
- Complete file management suite (Read, Write, Edit, MultiEdit)
- Version control operations (Git integration)
- Code execution and testing (Bash, Python)
- Search and navigation (Grep, Glob, Find)
- Notebook and documentation handling

**Communication Patterns**:
- **Inbound**: PlannerAgent, AuditorAgent, QualityEnforcerAgent
- **Outbound**: MergerAgent, WorkCompletionSummaryAgent
- **Bidirectional**: PlannerAgent (collaborative development)

---

### 3. PlannerAgent
**Role**: Strategic planning using spec-kit methodology

**Key Responsibilities**:
- Creates formal specifications in `specs/` directory
- Develops implementation plans in `plans/` directory
- Breaks down complex tasks into manageable components
- Coordinates multi-step development workflows
- Ensures spec-driven development compliance (Constitutional Article V)

**Communication Patterns**:
- **Inbound**: ChiefArchitectAgent, User (planning mode)
- **Outbound**: AuditorAgent, CodingAgent
- **Bidirectional**: CodingAgent (collaborative planning)

---

### 4. AuditorAgent
**Role**: Quality analysis using NECESSARY pattern

**Key Responsibilities**:
- Analyzes code quality using the 9-point NECESSARY pattern
- Calculates Q(T) scores for test quality assessment
- Identifies quality violations with severity levels
- Generates actionable improvement recommendations
- Ensures constitutional compliance across the codebase

**Tools & Capabilities**:
- NECESSARY pattern analysis (N-E-C-E-S-S-A-R-Y)
- Q(T) scoring: `Q(T) = Π(p_i) × (|B_c| / |B|)`
- Code quality assessment and violation detection

**Communication Patterns**:
- **Inbound**: ChiefArchitectAgent, PlannerAgent
- **Outbound**: CodingAgent, TestGeneratorAgent, QualityEnforcerAgent

---

### 5. TestGeneratorAgent
**Role**: NECESSARY-compliant test generation

**Key Responsibilities**:
- Generates comprehensive tests based on audit reports
- Creates property-specific test templates for violation types
- Prioritizes high-impact test improvements
- Ensures tests maximize Q(T) scores and quality metrics
- Maintains 100% test success rate (Constitutional Article II)

**Communication Patterns**:
- **Inbound**: AuditorAgent, QualityEnforcerAgent
- **Outbound**: CodingAgent
- **Bidirectional**: QualityEnforcerAgent (quality collaboration)

---

### 6. LearningAgent
**Role**: Pattern analysis and institutional memory

**Key Responsibilities**:
- Analyzes session transcripts for successful patterns
- Extracts insights and consolidates learning
- Stores knowledge in VectorStore for cross-session application
- Identifies optimization opportunities from historical data
- Maintains institutional memory across agency operations

**Communication Patterns**:
- **Inbound**: ChiefArchitectAgent, System (automatic analysis)
- **Knowledge Sharing**: All agents benefit from stored patterns

---

### 7. MergerAgent
**Role**: Integration and pull request management

**Key Responsibilities**:
- Handles code integration and merge operations
- Manages pull request creation and review processes
- Ensures integration compliance with constitutional standards
- Coordinates final deployment and release activities

**Communication Patterns**:
- **Inbound**: CodingAgent, ToolsmithAgent
- **Outbound**: WorkCompletionSummaryAgent

---

### 8. QualityEnforcerAgent ⭐ **Autonomous Healing Core**
**Role**: Constitutional compliance and autonomous healing

**Key Responsibilities**:
- Maintains constitutional compliance across all operations
- Performs autonomous healing for NoneType errors
- Enforces quality standards and prevents violations
- Provides complete error detection, fix generation, and application
- Maintains audit trails for all quality enforcement actions

**Autonomous Healing Tools**:
- `NoneTypeErrorDetector`: Automatic error detection from logs
- `LLMNoneTypeFixer`: GPT-5 powered fix generation
- `AutoNoneTypeFixer`: Complete error-to-fix workflow
- `ApplyAndVerifyPatch`: Autonomous patch application with test verification
- `AutonomousHealingOrchestrator`: End-to-end healing coordination

**Autonomous Healing Workflow**:
1. **Detection**: Monitors logs and system events for NoneType errors
2. **Analysis**: Uses LLM intelligence to understand context and generate fixes
3. **Application**: Applies fixes with automatic safety verification
4. **Testing**: Runs complete test suite to ensure no regressions
5. **Commitment**: Commits successful fixes with detailed audit trails
6. **Rollback**: Automatically reverts failed fixes to maintain system integrity

**Communication Patterns**:
- **Inbound**: ChiefArchitectAgent, AuditorAgent
- **Outbound**: CodingAgent, TestGeneratorAgent
- **Bidirectional**: TestGeneratorAgent
- **Autonomous**: Self-initiated healing workflows

---

### 9. ToolsmithAgent
**Role**: Tool development and enhancement

**Key Responsibilities**:
- Develops and maintains agency tools
- Enhances existing tool capabilities
- Creates new tools based on identified needs
- Ensures tool compatibility across model types (OpenAI, Claude, Grok)

**Communication Patterns**:
- **Inbound**: ChiefArchitectAgent
- **Outbound**: MergerAgent

---

### 10. WorkCompletionSummaryAgent
**Role**: Intelligent task summaries and completion reporting

**Key Responsibilities**:
- Generates intelligent summaries of completed work
- Provides task completion reports and status updates
- Creates audio summaries when requested (TTS integration)
- Tracks project progress and milestone achievements

**Communication Patterns**:
- **Inbound**: CodingAgent, PlannerAgent, MergerAgent
- **Route-Aware**: Activated via "tts" or "audio summary" intents
- **Outbound**: User (completion summaries)

## 🔄 Primary Workflows

### Development Workflow
```
User Request → PlannerAgent → CodingAgent → MergerAgent → Completion
                     ↓              ↓
              AuditorAgent  →  TestGeneratorAgent
```

### Quality Assurance Workflow
```
AuditorAgent → QualityEnforcerAgent → TestGeneratorAgent → CodingAgent
       ↓                    ↓                     ↓
   Violations         Autonomous          Test Implementation
   Detected            Healing
```

### Autonomous Healing Workflow
```
Error Detection → QualityEnforcerAgent → LLM Analysis → Fix Application → Test Verification → Auto-Commit
      ↓                    ↓                    ↓              ↓              ↓
  Log Monitoring     Constitutional     GPT-5 Fix        Safety         Version
   & Alerts          Compliance        Generation       Checks          Control
```

## 🛡️ Constitutional Compliance

All agents operate under the **Six Constitutional Articles**:

1. **Complete Context Before Action**: Agents gather full context before taking action
2. **100% Verification**: All agents maintain 100% test success rate
3. **Automated Enforcement**: Quality standards technically enforced
4. **Continuous Learning**: All agents participate in learning and improvement
5. **Spec-Driven Development**: All features require formal specifications
6. **Red-Green-Refactor TDD**: Tests written first, must fail initially

## 🎯 Key Benefits

### Autonomous Capabilities
- **Self-Healing**: Automatic error detection and fixing
- **Constitutional Governance**: Unbreakable quality standards
- **Cross-Agent Learning**: Collective intelligence and pattern sharing
- **Real-Time Adaptation**: Dynamic behavior based on system conditions

### Developer Experience
- **Focused Architecture**: Clear responsibilities and clean communication
- **LLM-First Design**: Leverages AI strengths over complex systems
- **Complete Automation**: From error detection to commit with safety
- **Rich Observability**: Comprehensive logging and monitoring

---

*This architecture represents the pinnacle of autonomous software engineering - a system that maintains, improves, and heals itself while adhering to the highest quality standards.*
