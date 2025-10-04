# Getting Started with Agency

**Quick start guide for developers and autonomous agents**

## For Human Developers

### Prerequisites
- Python 3.12 or 3.13
- Git
- OpenAI API key (or compatible LLM provider)

### Quick Setup
```bash
# Clone and initialize
git clone <repository-url>
cd Agency

# Install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Verify installation
python run_tests.py --run-all  # Should show 100% pass rate
```

### Essential Configuration
```bash
# .env file - Core settings
OPENAI_API_KEY=your_key_here
AGENCY_MODEL=gpt-5                    # Primary model
USE_ENHANCED_MEMORY=true              # VectorStore integration (mandatory)
FRESH_USE_FIRESTORE=false             # Optional Firestore backend
FORCE_RUN_ALL_TESTS=1                 # Enable full test suite
```

## For Autonomous Agents

### First Session
1. **Prime the context**: Use `/primecc` command
2. **Load city-map**: Read `.claude/quick-ref/city-map.md`
3. **Check constitution**: Read `.claude/quick-ref/constitution-checklist.md`
4. **Start working**: Use tier-based loading (10k tokens vs 140k)

### Quick References
- **Agent Map**: `.claude/quick-ref/agent-map.md` → Which agent to use
- **Tool Index**: `.claude/quick-ref/tool-index.md` → Which tool to use
- **Code Patterns**: `.claude/quick-ref/common-patterns.md` → Copy-paste examples
- **Constitution**: `.claude/quick-ref/constitution-checklist.md` → Validate before action

## Core Concepts

### The Five Articles (Constitutional Law)
1. **Article I**: Complete context before action (no timeouts)
2. **Article II**: 100% verification (all tests must pass)
3. **Article III**: Automated enforcement (no manual overrides)
4. **Article IV**: Continuous learning (VectorStore mandatory)
5. **Article V**: Spec-driven development (complex features)

### Development Workflow
```
Feature Request
    ↓
Planner (creates spec.md) → User Approval
    ↓
Planner (creates plan.md) → User Approval
    ↓
TodoWrite (task breakdown)
    ↓
AgencyCodeAgent (TDD implementation)
    ↓
TestGenerator + QualityEnforcer → Tests Pass?
    ↓
MergerAgent (branch → commit → PR)
```

## Next Steps

### Tutorials
- **Basic Usage**: See `docs/examples/`
- **Agent Development**: See `docs/architecture/agents.md`
- **Tool Creation**: See `docs/guides/toolsmith.md`
- **Testing**: See `docs/guides/testing.md`

### Resources
- **Architecture**: `docs/architecture/`
- **ADRs**: `docs/adr/ADR-INDEX.md`
- **API Docs**: `docs/api/`
- **Troubleshooting**: `docs/guides/troubleshooting.md`

## Common Commands

### Development
```bash
python agency.py run              # Interactive demo
python run_tests.py --run-all     # Full test suite
python demo_unified.py            # Core capabilities demo
```

### Quality Checks
```bash
python -m pytest tests/           # Run tests
python -m mypy agency.py          # Type checking
python scripts/constitutional_check.py  # Compliance validation
```

### Autonomous Operations
```bash
/primecc                    # Load codebase context
/prime plan_and_execute     # Full dev cycle
/prime audit_and_refactor   # Code quality
/prime healing_mode         # Self-healing
```

---

**Need Help?**
- **Documentation**: Check `docs/` directory
- **Issues**: See GitHub issues
- **Constitution**: Read `constitution.md` (mandatory)

**Version**: 0.9.5
**Last Updated**: 2025-10-03
