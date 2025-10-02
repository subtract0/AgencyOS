# Specification: Unified Command Interface

**Spec ID**: `spec-018-unified-command-interface`
**Status**: `Draft`
**Author**: ChiefArchitectAgent
**Created**: 2025-10-02
**Last Updated**: 2025-10-02
**Related Plan**: `plan-018-unified-command-interface.md`

---

## Executive Summary

Consolidate 9 prime commands into 4-5 hierarchical commands with subcommands, add /help command with interactive guidance and examples, implement command chaining/composition for complex workflows, and add parameter validation with descriptive error messages. This will improve command interface usability from 69/100 to 84/100, reducing cognitive load and enabling more sophisticated autonomous operations through composable commands.

---

## Goals

### Primary Goals
- [ ] **Goal 1**: Consolidate 9 prime commands to 4-5 top-level commands with subcommands (reduce by 50%+)
- [ ] **Goal 2**: Implement hierarchical command structure with logical grouping (prime → develop, audit, heal, learn)
- [ ] **Goal 3**: Add /help command with interactive guidance, examples, and command discovery
- [ ] **Goal 4**: Enable command chaining/composition for multi-step workflows (e.g., `/prime develop --chain audit`)
- [ ] **Goal 5**: Implement parameter validation with descriptive error messages and suggestion recovery

### Success Metrics
- **Command Discoverability**: Users find relevant command within 30 seconds (measured via usability testing)
- **Cognitive Load**: 50%+ reduction in "which command do I use?" questions (measured via user feedback)
- **Chaining Adoption**: 30%+ of users leverage command chaining within first month
- **Error Recovery**: 90%+ of invalid commands provide actionable fix suggestions
- **Help System Usage**: /help accessed 10+ times per week (indicates good discoverability)
- **User Satisfaction**: 85%+ satisfaction score on command interface UX survey

---

## Non-Goals

### Explicit Exclusions
- **Natural Language Commands**: Not implementing NLP-based command parsing (e.g., "create a new feature for authentication")
- **GUI Command Builder**: Not building graphical interface for command construction
- **Command Aliases**: Not implementing short aliases (e.g., /p for /prime) to maintain clarity
- **Custom Command Creation**: Not allowing users to define custom commands (defer to future)

### Future Considerations
- **Command Marketplace**: Shareable command templates or community-contributed commands
- **Voice Commands**: Integration with voice assistants for hands-free Agency control
- **Command Macros**: User-defined sequences of commands with parameter interpolation
- **Auto-Suggest**: Intelligent command completion based on context and history

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: New Developer (First-Time Agency User)
- **Description**: Developer using Agency OS for the first time, unfamiliar with command structure
- **Goals**: Quickly understand available commands, find right command for task, avoid errors
- **Pain Points**: 9 prime commands overwhelming, unclear which to use, no discovery mechanism
- **Technical Proficiency**: Expert in software development, but novice with Agency-specific commands

#### Persona 2: Power User (Experienced Developer)
- **Description**: Experienced Agency user running complex multi-step workflows regularly
- **Goals**: Efficient command execution, chaining for automation, minimal typing overhead
- **Pain Points**: Repetitive multi-command sequences, no chaining support, verbose command syntax
- **Technical Proficiency**: Expert in Agency architecture, wants advanced capabilities

#### Persona 3: Autonomous Agent (System Consumer)
- **Description**: Agent executing commands programmatically during autonomous operations
- **Goals**: Reliable command parsing, clear error messages, structured output for parsing
- **Pain Points**: Inconsistent error handling, unclear parameter requirements, no validation
- **Technical Proficiency**: Expert in command execution, requires machine-readable interfaces

### User Journeys

#### Journey 1: First-Time Command Discovery (Current - Confusing)
```
1. User needs: Start new feature development
2. User sees: 9 prime commands (/prime, /prime_plan_and_execute, /prime_audit_and_refactor, /prime_healing_mode, /prime_create_tool, /prime_create_spec, /prime_type_safety_mission, /prime_web_research, /prime_cc)
3. User confused: "Which command do I use? What's the difference between /prime and /prime_plan_and_execute?"
4. User guesses: Tries /prime, gets generic priming without development workflow
5. User retries: Tries /prime_plan_and_execute, finally gets desired workflow
6. Time wasted: 5-10 minutes of trial and error
```

#### Journey 2: First-Time Command Discovery (Future - Guided)
```
1. User needs: Start new feature development
2. User types: /help
3. Interactive guide: "What would you like to do? [develop, audit, heal, learn, other]"
4. User selects: "develop"
5. Subcommand shown: "/prime develop plan-and-execute" with description and example
6. User executes: Correct command on first try
7. Time saved: Immediate success, no trial and error
```

#### Journey 3: Multi-Step Workflow (Current - Manual Chaining)
```
1. User wants: Full development cycle (spec → plan → implement → audit → heal → merge)
2. User executes: /prime_plan_and_execute (spec + plan + implement)
3. Workflow completes: Implementation done, but quality checks pending
4. User executes: /prime_audit_and_refactor (audit + fixes)
5. User executes: /prime_healing_mode (autonomous healing)
6. Manual overhead: 3 separate commands, context switching, progress tracking
```

#### Journey 4: Multi-Step Workflow (Future - Command Chaining)
```
1. User wants: Full development cycle (spec → plan → implement → audit → heal → merge)
2. User executes: /prime develop full-cycle --chain audit --chain heal
3. Workflow orchestrated: All steps executed sequentially with checkpoints
4. Progress tracked: "Step 2/3: Auditing code quality..."
5. Single completion: Entire workflow completes without manual intervention
6. Time saved: 1 command instead of 3, automatic transitions
```

#### Journey 5: Parameter Validation Error (Current - Cryptic)
```
1. User executes: /prime develop plan-and-execute --spec
2. Error message: "Invalid arguments"
3. User confused: "What's wrong? Is --spec not a valid parameter?"
4. User checks: .claude/commands/prime_plan_and_execute.md to find correct usage
5. Discovers: --spec requires file path argument
6. User retries: /prime develop plan-and-execute --spec specs/spec-001.md
7. Time wasted: 5 minutes debugging parameter error
```

#### Journey 6: Parameter Validation Error (Future - Helpful)
```
1. User executes: /prime develop plan-and-execute --spec
2. Error message: "Missing value for --spec parameter. Expected: file path to specification.
   Example: /prime develop plan-and-execute --spec specs/spec-001.md
   Available specs: specs/spec-001.md, specs/spec-002.md, specs/spec-007.md"
3. User corrects: Copies suggested command with correct parameter
4. Success: Command executes on second attempt
5. Time saved: <30 seconds with clear guidance
```

---

## Acceptance Criteria

### Functional Requirements

#### Command Consolidation & Hierarchy
- [ ] **AC-1.1**: 9 prime commands consolidated to 4-5 top-level commands: `/prime develop`, `/prime audit`, `/prime heal`, `/prime learn`, `/prime utility`
- [ ] **AC-1.2**: Subcommands implemented: e.g., `/prime develop plan-and-execute`, `/prime develop create-spec`, `/prime develop create-tool`
- [ ] **AC-1.3**: Logical grouping: all development commands under `/prime develop`, all quality commands under `/prime audit`, etc.
- [ ] **AC-1.4**: Backward compatibility: old command names redirect to new hierarchy with deprecation warning
- [ ] **AC-1.5**: Command listing: `/prime` without subcommand shows available top-level commands

#### Interactive Help System
- [ ] **AC-2.1**: `/help` command shows interactive command explorer with categories
- [ ] **AC-2.2**: `/help <command>` shows detailed help for specific command with examples
- [ ] **AC-2.3**: `/help --search <keyword>` searches commands by keyword (e.g., `/help --search audit`)
- [ ] **AC-2.4**: Help includes: command description, parameters, examples, related commands
- [ ] **AC-2.5**: Interactive mode: `/help --interactive` provides step-by-step command builder

#### Command Chaining & Composition
- [ ] **AC-3.1**: Chain syntax: `/prime develop full-cycle --chain audit --chain heal` executes sequentially
- [ ] **AC-3.2**: Conditional chaining: `--chain-if-success audit` only runs if previous step succeeds
- [ ] **AC-3.3**: Parallel chaining: `--chain-parallel heal,test` runs multiple commands concurrently (where safe)
- [ ] **AC-3.4**: Chain checkpointing: each chained command creates checkpoint for resumability (spec-015 integration)
- [ ] **AC-3.5**: Chain abort: failure in chain aborts remaining commands unless `--continue-on-error` specified

#### Parameter Validation & Error Handling
- [ ] **AC-4.1**: Parameter types validated: file paths verified to exist, enums validated against allowed values
- [ ] **AC-4.2**: Required parameters: clear error if missing required parameter with example of correct usage
- [ ] **AC-4.3**: Mutually exclusive parameters: error if conflicting parameters provided (e.g., `--spec` and `--no-spec`)
- [ ] **AC-4.4**: Suggestion recovery: error messages suggest corrections (e.g., "Did you mean --spec instead of --specification?")
- [ ] **AC-4.5**: Available options: parameter errors list available values (e.g., "Invalid --format, choose from: json, text, markdown")

#### Command Documentation & Discoverability
- [ ] **AC-5.1**: Command registry: all commands registered with metadata (name, description, parameters, examples)
- [ ] **AC-5.2**: Auto-generated help: command help auto-generated from registry annotations
- [ ] **AC-5.3**: Command completion: tab completion shows available commands and parameters (if terminal supports)
- [ ] **AC-5.4**: Command history: recent commands accessible via `agency history` for re-execution
- [ ] **AC-5.5**: Command templates: frequently used command patterns saved as templates

### Non-Functional Requirements

#### Performance
- [ ] **AC-P.1**: Command parsing: <50ms to parse and validate command
- [ ] **AC-P.2**: Help display: <100ms to render help screen
- [ ] **AC-P.3**: Chain execution: <5% overhead for chaining vs. sequential manual execution
- [ ] **AC-P.4**: Parameter validation: <10ms per parameter

#### Usability
- [ ] **AC-U.1**: Command discoverability: 90%+ of users find correct command within 30 seconds (usability testing)
- [ ] **AC-U.2**: Error clarity: 95%+ of users understand error messages and successfully correct (usability testing)
- [ ] **AC-U.3**: Help effectiveness: 85%+ of users successfully use command after reading help
- [ ] **AC-U.4**: Chaining intuitiveness: 70%+ of users understand chaining syntax without documentation

#### Backward Compatibility
- [ ] **AC-BC.1**: Old commands remain functional with deprecation warnings for 6 months
- [ ] **AC-BC.2**: Deprecation notices: clear migration path provided (e.g., "Use /prime develop plan-and-execute instead")
- [ ] **AC-BC.3**: Agent compatibility: existing agent invocations continue to work during transition period
- [ ] **AC-BC.4**: Incremental migration: old and new commands coexist during migration

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [ ] **AC-CI.1**: Command help provides complete context for informed command selection
- [ ] **AC-CI.2**: Chained commands gather complete context before executing entire chain
- [ ] **AC-CI.3**: Parameter validation ensures complete required parameters before execution

#### Article II: 100% Verification and Stability
- [ ] **AC-CII.1**: 100% test coverage for command parsing, validation, chaining, help system
- [ ] **AC-CII.2**: All commands verified via integration tests before deployment
- [ ] **AC-CII.3**: Command changes do not break existing tests (backward compatibility verified)

#### Article III: Automated Merge Enforcement
- [ ] **AC-CIII.1**: Command interface changes follow git workflow with CI validation
- [ ] **AC-CIII.2**: No command bypasses constitutional enforcement (quality gates intact)

#### Article IV: Continuous Learning and Improvement
- [ ] **AC-CIV.1**: Command usage patterns tracked for learning (which commands used, when, with what parameters)
- [ ] **AC-CIV.2**: Help system learns from common errors and updates suggestions
- [ ] **AC-CIV.3**: Command effectiveness metrics drive interface improvements

#### Article V: Spec-Driven Development
- [ ] **AC-CV.1**: This specification drives all unified command interface implementation
- [ ] **AC-CV.2**: Command structure follows spec-kit patterns (formal definitions, validation)

---

## Dependencies & Constraints

### System Dependencies
- **Command Parser**: Argument parsing library (argparse or Click for Python)
- **Command Registry**: Centralized command metadata storage
- **AgentContext**: Command execution tied to agent context for state management
- **Telemetry**: Command usage tracking for learning and metrics

### External Dependencies
- **Click (Python)**: Command-line interface creation library (recommended for hierarchy support)
- **Rich (Python)**: Terminal UI for interactive help and progress display
- **Prompt Toolkit**: Optional for advanced tab completion and interactive command builder

### Technical Constraints
- **Terminal Compatibility**: Help system must work in all standard terminals (no Unicode-only features)
- **Command Length**: Chained commands limited to ~500 characters for readability
- **Parsing Complexity**: Command parser must handle nested subcommands and parameters
- **State Management**: Chained commands share state via workflow state machine (spec-015)

### Business Constraints
- **Backward Compatibility**: Old commands must remain functional for 6 months during migration
- **User Training**: Comprehensive migration guide and examples required
- **Documentation Updates**: All documentation updated to reflect new command structure

---

## Risk Assessment

### High Risk Items
- **Risk 1**: Users resist new command structure, prefer old familiar commands - *Mitigation*: Gradual migration, deprecation warnings, comprehensive help system, user feedback integration
- **Risk 2**: Command chaining introduces bugs or unexpected behavior - *Mitigation*: Extensive integration testing, checkpoint-based resumability, clear abort conditions

### Medium Risk Items
- **Risk 3**: Help system becomes too verbose or complex, reducing usability - *Mitigation*: Tiered help (summary → detailed), interactive mode for guidance
- **Risk 4**: Tab completion conflicts with terminal features or other tools - *Mitigation*: Optional tab completion, graceful degradation if terminal doesn't support

### Constitutional Risks
- **Constitutional Risk 1**: Article I violation if chained commands lack complete context - *Mitigation*: Context gathering before chain execution, checkpoint validation
- **Constitutional Risk 2**: Article II violation if command changes break existing workflows - *Mitigation*: 100% test coverage, backward compatibility, incremental rollout

---

## Integration Points

### Agent Integration
- **All Agents**: Updated to use new command structure for invoking workflows
- **PlannerAgent**: Uses `/prime develop` commands for development workflows
- **QualityEnforcerAgent**: Uses `/prime audit` and `/prime heal` for quality operations
- **LearningAgent**: Uses `/prime learn` for learning workflows

### System Integration
- **Workflow State (spec-015)**: Chained commands create checkpoints for resumability
- **Telemetry**: Command usage tracked with parameters for learning analytics
- **Documentation (spec-014)**: Help system references consolidated documentation
- **CLI Infrastructure**: Commands integrated with existing agency.py CLI

### External Integration
- **GitHub Actions**: Commands invokable from CI workflows
- **Shell Scripts**: Commands composable in bash/zsh scripts
- **IDE Integration**: Future potential for IDE command palette integration

---

## Testing Strategy

### Test Categories
- **Unit Tests**: Command parsing, parameter validation, error message generation
- **Integration Tests**: End-to-end command execution including chaining
- **Usability Tests**: User testing for discoverability, clarity, error recovery
- **Backward Compatibility Tests**: Old commands function correctly with deprecation warnings
- **Constitutional Compliance Tests**: All 5 articles verified in command execution

### Test Data Requirements
- **Command Fixtures**: Sample commands with various parameter combinations
- **Error Cases**: Invalid commands, missing parameters, conflicting parameters
- **Chaining Scenarios**: Simple chains (2 commands), complex chains (5+ commands), conditional chains

### Test Environment Requirements
- **Terminal Simulation**: Mock terminal for testing interactive features
- **Command History**: Simulated command history for testing recent command access
- **User Feedback**: Alpha testing with 5+ users for usability validation

---

## Implementation Phases

### Phase 1: Command Consolidation (Week 1)
- **Scope**: Consolidate 9 prime commands into 4-5 top-level with subcommands
- **Deliverables**:
  - New command structure: /prime develop, /prime audit, /prime heal, /prime learn, /prime utility
  - Command registry with metadata
  - Backward compatibility layer with deprecation warnings
- **Success Criteria**: All functionality accessible via new command structure

### Phase 2: Parameter Validation & Error Handling (Week 2)
- **Scope**: Implement robust parameter validation with helpful error messages
- **Deliverables**:
  - Type validation (file paths, enums, numbers)
  - Suggestion recovery for typos/mistakes
  - Available options listing in errors
- **Success Criteria**: 90%+ of validation errors provide actionable fix suggestions

### Phase 3: Help System (Week 3)
- **Scope**: Build comprehensive /help command with interactive guidance
- **Deliverables**:
  - /help with category listing
  - /help <command> with detailed documentation
  - /help --search <keyword> for command discovery
  - Optional interactive command builder
- **Success Criteria**: Users find correct command within 30 seconds

### Phase 4: Command Chaining (Week 4)
- **Scope**: Implement command chaining and composition
- **Deliverables**:
  - Chain syntax: --chain, --chain-if-success, --chain-parallel
  - Checkpoint integration with workflow state machine (spec-015)
  - Chain abort on failure with rollback
- **Success Criteria**: Chained workflows execute reliably with proper error handling

### Phase 5: Documentation & Migration (Week 5)
- **Scope**: Update all documentation and provide migration guide
- **Deliverables**:
  - Migration guide: old commands → new commands mapping
  - Updated .claude/commands/ documentation
  - User announcement and training materials
- **Success Criteria**: Users successfully migrate to new command structure

---

## Review & Approval

### Stakeholders
- **Primary Stakeholder**: @am (Project Owner)
- **Secondary Stakeholders**: All Agency users (command consumers)
- **Technical Reviewers**: ChiefArchitectAgent (architecture validation), PlannerAgent (workflow integration)

### Review Criteria
- [ ] **Completeness**: All command interface gaps addressed
- [ ] **Clarity**: New command structure logical and intuitive
- [ ] **Feasibility**: Chaining and validation technically viable
- [ ] **Constitutional Compliance**: All 5 articles supported by implementation
- [ ] **Quality Standards**: Meets Agency's usability and testing requirements

### Approval Status
- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending agent validation
- [ ] **Constitutional Compliance**: Pending article verification
- [ ] **Final Approval**: Pending all above approvals

---

## Appendices

### Appendix A: Glossary
- **Command Hierarchy**: Tree structure of commands with top-level and subcommands
- **Command Chaining**: Sequential or parallel execution of multiple commands
- **Parameter Validation**: Verification that command parameters are correct and complete
- **Suggestion Recovery**: Automatic suggestion of corrections for invalid commands

### Appendix B: References
- **ADR-001**: Complete Context Before Action (drives help system completeness)
- **ADR-002**: 100% Verification and Stability (drives command testing requirements)
- **spec-015**: Workflow State Persistence (provides checkpointing for chained commands)
- **Article I**: Complete context required for command help and chaining

### Appendix C: Related Documents
- **.claude/commands/*.md**: Current command documentation (to be migrated)
- **agency.py**: CLI infrastructure (to be enhanced with new command structure)
- **shared/agent_context.py**: AgentContext integration for command execution

### Appendix D: Command Migration Map

| Old Command | New Command | Status |
|-------------|-------------|--------|
| `/prime` | `/prime utility cc` | Deprecated (migrate by 2025-04-02) |
| `/prime_plan_and_execute` | `/prime develop plan-and-execute` | Deprecated (migrate by 2025-04-02) |
| `/prime_audit_and_refactor` | `/prime audit refactor` | Deprecated (migrate by 2025-04-02) |
| `/prime_healing_mode` | `/prime heal activate` | Deprecated (migrate by 2025-04-02) |
| `/prime_create_tool` | `/prime develop create-tool` | Deprecated (migrate by 2025-04-02) |
| `/prime_create_spec` | `/prime develop create-spec` | Deprecated (migrate by 2025-04-02) |
| `/prime_type_safety_mission` | `/prime audit type-safety` | Deprecated (migrate by 2025-04-02) |
| `/prime_web_research` | `/prime utility research` | Deprecated (migrate by 2025-04-02) |
| `/prime_cc` | `/prime utility cc` | Deprecated (migrate by 2025-04-02) |

### Appendix E: New Command Structure

```
/prime
├── develop
│   ├── plan-and-execute     # Full development cycle (spec → plan → implement)
│   ├── create-spec          # Generate formal specification
│   ├── create-tool          # Build new agent tool
│   └── full-cycle           # Complete development (spec → plan → implement → audit → heal → merge)
├── audit
│   ├── refactor             # Code quality analysis and refactoring
│   ├── type-safety          # Type safety audit and fixing
│   └── security             # Security vulnerability scanning
├── heal
│   ├── activate             # Activate autonomous healing mode
│   ├── scan                 # Run proactive healing scan
│   └── dashboard            # View healing metrics
├── learn
│   ├── extract              # Extract patterns from sessions
│   ├── consolidate          # Consolidate learnings
│   └── dashboard            # View learning metrics
└── utility
    ├── cc                   # Codebase context (former /prime)
    └── research             # Web research mode
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-02 | ChiefArchitectAgent | Initial specification for unified command interface |

---

*"A specification is a contract between intention and implementation."*
