# Agency OS Documentation Hub

**Comprehensive documentation for Claude Code integration with Agency OS**

## Overview

This directory contains detailed documentation for Agency OS's Claude Code integration, organized into three main categories:

- **Features**: Deep dives into specific capabilities and systems
- **Guides**: Step-by-step tutorials and workflows
- **SDK**: Claude Agent SDK integration patterns and examples

This documentation complements the token-optimized quick references in `.claude/quick-ref/` and provides comprehensive context when deeper understanding is needed.

---

## Directory Structure

```
.claude/
├── docs/                          # Comprehensive documentation (this directory)
│   ├── README.md                  # This file - documentation index
│   ├── features/                  # Feature-specific deep dives
│   ├── guides/                    # How-to tutorials and workflows
│   └── sdk/                       # Claude Agent SDK integration
│
├── quick-ref/                     # Token-optimized quick references
│   ├── city-map.md               # Tier-based codebase navigation (213 lines)
│   ├── constitution-checklist.md  # Fast Article I-V validation (50 lines)
│   ├── agent-map.md              # Agent capabilities + flows (100 lines)
│   ├── tool-index.md             # All 45 tools indexed (150 lines)
│   └── common-patterns.md        # Result, Pydantic, TDD patterns (100 lines)
│
├── agents/                        # Agent role definitions (12 files)
│   ├── code_agent.md             # Primary development agent
│   ├── planner.md                # Spec-kit methodology
│   ├── auditor.md                # Quality analysis (READ-ONLY)
│   ├── quality_enforcer.md       # Constitutional compliance
│   └── ...                       # + 8 more agents
│
├── commands/                      # Prime commands (17 files)
│   ├── primecc.md                # General codebase understanding
│   ├── plan_and_execute.md       # Full dev cycle (Spec → Code)
│   ├── audit_and_refactor.md     # Quality improvement
│   └── ...                       # + 14 more commands
│
└── settings.local.json            # Permissions configuration
```

---

## Quick Links

### Features (Deep Dives)

> Detailed documentation on specific Agency OS capabilities

_Coming soon - this directory will contain:_

- Autonomous Healing System
- VectorStore & Learning Architecture
- Constitutional Governance Framework
- Multi-Agent Coordination (Trinity Protocol)
- Spec-Driven Development Workflow
- Test-Driven Development (TDD) Enforcement

### Guides (How-To)

> Step-by-step tutorials for common workflows

_Coming soon - this directory will contain:_

- Getting Started with Agency OS
- Creating Your First Agent
- Writing Constitutional-Compliant Code
- Using the Spec-Kit Methodology
- Debugging with Telemetry & Logs
- Contributing to Agency OS

### SDK Integration

> Claude Agent SDK patterns and examples

_Coming soon - this directory will contain:_

- SDK Quick Start Guide
- Custom Tool Development with `@tool`
- Session Management Patterns
- MCP Server Integration
- Streaming Input/Output Examples

---

## Documentation Philosophy

### Quick References vs Comprehensive Docs

**Use `.claude/quick-ref/` when:**

- You need fast lookup of capabilities (agents, tools, patterns)
- You're in an active session and need context quickly
- Token efficiency is critical (Tier 1-2 loading: ~1,700 lines)
- You need constitutional validation checklist
- You're navigating the codebase structure

**Use `.claude/docs/` when:**

- You need deep understanding of a feature or system
- You're learning a new workflow or methodology
- You need step-by-step tutorials
- You're integrating with Claude Agent SDK
- You need comprehensive examples and edge cases

### Documentation Layers

```
Layer 1: CLAUDE.md (408 lines)
         ↓ Quick overview + Constitution summary

Layer 2: .claude/quick-ref/ (613 lines total)
         ↓ Token-optimized lookups

Layer 3: .claude/docs/ (this directory)
         ↓ Comprehensive guides + examples

Layer 4: Source code + ADRs
         ↓ Implementation details
```

---

## Integration with Agency OS

### For AI Agents

**Session Initialization:**

1. **Load Tier 1**: `CLAUDE.md` + `constitution.md` (1,266 lines)
2. **Load Tier 2**: `.claude/quick-ref/` as needed (613 lines)
3. **Deep Dive**: `.claude/docs/` when specific feature understanding required

**Workflow:**

```python
# Example: Agent needs to understand autonomous healing
1. Quick lookup: .claude/quick-ref/tool-index.md → Find auto_fix_nonetype.py
2. Deep dive: .claude/docs/features/autonomous-healing.md → System architecture
3. Implementation: tools/auto_fix_nonetype.py → Source code
```

**Constitutional Compliance:**

- All documentation adheres to Articles I-V (see `constitution.md`)
- Quick validation: `.claude/quick-ref/constitution-checklist.md`
- Deep understanding: `.claude/docs/features/constitutional-governance.md` (coming soon)

### For Human Developers

**Getting Started:**

1. Read `README.md` (root) for project overview
2. Review `CLAUDE.md` for master constitution
3. Browse `.claude/quick-ref/city-map.md` for codebase navigation
4. Use `.claude/docs/guides/` for step-by-step workflows

**Contributing:**

- Follow TDD principles (Constitutional Law #1)
- Validate against Articles I-V before submitting
- Use `python run_tests.py --run-all` (must show 100% pass rate)
- See `.claude/docs/guides/contributing.md` (coming soon)

---

## Content Roadmap

### Phase 1: Core Features (Planned)

- [ ] `features/autonomous-healing.md` - Self-healing system architecture
- [ ] `features/vectorstore-learning.md` - Learning & memory subsystem
- [ ] `features/constitutional-governance.md` - Articles I-V deep dive
- [ ] `features/spec-driven-development.md` - Spec-kit methodology

### Phase 2: Developer Guides (Planned)

- [ ] `guides/getting-started.md` - Onboarding tutorial
- [ ] `guides/agent-development.md` - Creating custom agents
- [ ] `guides/tool-development.md` - Writing new tools with TDD
- [ ] `guides/debugging-workflows.md` - Telemetry & logging

### Phase 3: SDK Integration (Planned)

- [ ] `sdk/quickstart.md` - Claude Agent SDK basics
- [ ] `sdk/custom-tools.md` - `@tool` decorator patterns
- [ ] `sdk/mcp-servers.md` - MCP integration guide
- [ ] `sdk/advanced-patterns.md` - Streaming, permissions, options

---

## Key Architectural Documents

### Must-Read for All Agents

1. **`/constitution.md`** (366 lines) - 5 Articles, MANDATORY compliance
2. **`/CLAUDE.md`** (408 lines) - Master constitution + quick reference
3. **`.claude/quick-ref/constitution-checklist.md`** - Pre-action validation

### Agent-Specific Context

- **Development**: `.claude/agents/code_agent.md` + `quick-ref/common-patterns.md`
- **Planning**: `.claude/agents/planner.md` + `specs/` directory
- **Quality**: `.claude/agents/auditor.md` + `quality_enforcer.md`
- **Git Operations**: `.claude/agents/merger.md` + `tools/git.py`

### Architecture Decision Records (ADRs)

Located in `/docs/adr/` (18 ADRs total):

- **ADR-001**: Complete Context Before Action (Article I)
- **ADR-002**: 100% Verification and Stability (Article II)
- **ADR-003**: Automated Merge Enforcement (Article III)
- **ADR-004**: Continuous Learning and Improvement (Article IV)
- **ADR-007**: Spec-Driven Development (Article V)
- Full index: `/docs/adr/ADR-INDEX.md`

---

## Documentation Standards

### Writing Guidelines

**For Feature Documentation:**

- Start with "Why this exists" (problem statement)
- Include architecture diagrams (ASCII art acceptable)
- Provide code examples with explanations
- Link to source files and tests
- Show constitutional compliance

**For How-To Guides:**

- Begin with prerequisites and assumptions
- Use numbered steps with clear outcomes
- Include error handling and troubleshooting
- Show complete working examples
- Reference related documentation

**For SDK Documentation:**

- Start with minimal working example
- Build complexity incrementally
- Show both sync and async patterns
- Include type annotations
- Link to official SDK docs

### Code Examples

All code examples must follow Agency OS constitutional laws:

```python
# ✅ Correct: Typed Pydantic model
from pydantic import BaseModel

class UserRequest(BaseModel):
    email: str
    name: str
    age: int

# ❌ Wrong: Dict[Any, Any] (Constitutional violation)
from typing import Dict, Any
user_data: Dict[Any, Any] = {}
```

```python
# ✅ Correct: Result pattern for error handling
from shared.type_definitions.result import Result, Ok, Err

def validate_email(email: str) -> Result[str, str]:
    if "@" not in email:
        return Err("Invalid email format")
    return Ok(email)

# ❌ Wrong: Exception-based control flow
def validate_email(email: str) -> str:
    if "@" not in email:
        raise ValueError("Invalid email")
    return email
```

---

## Token Efficiency Metrics

### Documentation Size Comparison

**Quick References** (Token-Optimized):

- `city-map.md`: 213 lines (~1.5k tokens)
- `agent-map.md`: 100 lines (~700 tokens)
- `tool-index.md`: 150 lines (~1k tokens)
- `common-patterns.md`: 100 lines (~700 tokens)
- `constitution-checklist.md`: 50 lines (~350 tokens)
- **Total**: 613 lines (~4.2k tokens)

**Comprehensive Docs** (Deep Dives):

- Features: ~500-1000 lines each (~3-7k tokens)
- Guides: ~300-800 lines each (~2-5k tokens)
- SDK: ~400-1000 lines each (~2.5-7k tokens)

**Loading Strategy**:

1. **Session Start**: Tier 1 + Quick Refs = ~10k tokens (vs 140k previously = 93% reduction)
2. **Deep Dive**: Load specific `.claude/docs/` file as needed
3. **Source Code**: Only when implementation details required

---

## Contributing to Documentation

### Adding New Documentation

1. **Determine Type**:
   - Feature deep dive → `features/`
   - Step-by-step tutorial → `guides/`
   - SDK integration → `sdk/`

2. **Follow Template**:
   - Features: Problem → Architecture → Examples → Tests
   - Guides: Prerequisites → Steps → Troubleshooting → References
   - SDK: Minimal Example → Advanced → Integration → Best Practices

3. **Update This Index**:
   - Add entry to appropriate section
   - Update quick links
   - Increment content roadmap

4. **Validate**:
   - Run `python run_tests.py --run-all` (must pass)
   - Check constitutional compliance
   - Link to related docs

### Documentation Quality Checklist

Before submitting documentation:

- [ ] Constitutional compliance validated (Articles I-V)
- [ ] Code examples follow Agency OS patterns
- [ ] Links to source files verified
- [ ] Cross-references to related docs added
- [ ] Token efficiency considered (quick-ref vs comprehensive)
- [ ] Examples tested and working
- [ ] Markdown formatting clean

---

## Related Resources

### Internal Documentation

- **Root README**: `/README.md` - Public-facing project overview
- **Constitution**: `/constitution.md` - 5 Articles (MANDATORY)
- **Master Guide**: `/CLAUDE.md` - Command & control interface
- **ADR Index**: `/docs/adr/ADR-INDEX.md` - Architecture decisions

### External Links

- **Claude Agent SDK**: `docs/reference/claude-agent-sdk-python.md`
- **Anthropic Docs**: [Claude API Documentation](https://docs.anthropic.com/)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)

### Agent Resources

- **Tool Implementations**: `/tools/` (45 production tools)
- **Agent Modules**: `/agency_code_agent/`, `/planner_agent/`, etc.
- **Shared Infrastructure**: `/shared/` (types, models, context)
- **Memory System**: `/agency_memory/` (VectorStore, learning)

---

## Quick Navigation Commands

### For AI Agents (Prime Commands)

```bash
/primecc                    # Load codebase understanding + improvements
/prime plan_and_execute     # Full dev cycle (Spec → Plan → Code)
/prime audit_and_refactor   # Code quality improvement
/prime healing_mode         # Autonomous self-healing
/prime_snap <file>          # Resume from snapshot
/write_snap                 # Create snapshot for next session
```

### For Humans (CLI)

```bash
# Development
python agency.py run                    # Interactive demo
python agency.py health                 # System health check

# Testing (MUST be 100% pass rate)
python run_tests.py --run-all           # Full validation (1,568+ tests)
python run_tests.py                     # Unit tests only
python run_tests.py --integration-only  # Integration tests

# Documentation
ls .claude/quick-ref/                   # Quick references
ls .claude/docs/                        # Comprehensive docs
cat docs/adr/ADR-INDEX.md              # Architecture decisions
```

---

## Version History

**v0.9.5** (2025-10-03)

- Initial `.claude/docs/` structure created
- README index established
- Integration with existing `.claude/quick-ref/` documented
- Content roadmap defined (Phases 1-3)

---

## Contact & Support

**For Questions:**

- Review constitutional checklist: `.claude/quick-ref/constitution-checklist.md`
- Check ADR index: `docs/adr/ADR-INDEX.md`
- Browse quick references: `.claude/quick-ref/`

**For Issues:**

- Constitutional violations → QualityEnforcerAgent
- Documentation gaps → Submit to `.claude/docs/` with template
- Tool/feature requests → ToolsmithAgent via `/prime create_tool`

---

_"In automation we trust, in discipline we excel, in learning we evolve."_

**Last Updated**: 2025-10-03
**Version**: 0.9.5 (Documentation Hub Establishment)
**Maintainer**: Agency OS Core Team
