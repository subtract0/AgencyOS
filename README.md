# AgencyOS - Autonomous Multi-Agent Development Platform

**Status**: Active Development | **Test Suite**: 5,822 tests passing | **Focus**: Claude API Orchestration + Local Model Integration

---

## **What is AgencyOS?**

AgencyOS is an experimental platform for orchestrating multiple AI agents to perform software development tasks. Think of it as a framework for building AI-powered development workflows with:

- **10 Specialized Agents** - Each handling specific aspects of development (planning, coding, testing, quality enforcement)
- **Constitutional Governance** - A formal "constitution" defining quality standards and workflows
- **Memory & Learning Systems** - VectorStore-based institutional memory for pattern recognition
- **Extensive Tooling** - 56+ tools for file operations, git, testing, and code quality

---

## **Quick Start**

### Prerequisites
- Python 3.12 or 3.13
- An Anthropic API key (agents currently require Claude)
- Git

### Setup (5 minutes)
```bash
# Clone the repository
git clone https://github.com/subtract0/AgencyOS.git
cd AgencyOS

# Create environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Configure your API key
export OPENAI_API_KEY=your_key_here
# OR create a .env file with: OPENAI_API_KEY=your_key_here

# Run tests to verify setup
python run_tests.py --run-all
```

**Expected**: Tests should run successfully. Note: Current test runner may require `uv` for optimal execution.

---

## **Current Capabilities**

### What Works Well ✅
1. **Agent Infrastructure** - 10 agents with defined roles and communication flows
2. **Memory Systems** - VectorStore and EnhancedMemoryStore for pattern storage
3. **Constitutional Framework** - 7 Articles defining governance (see [`constitution.md`](constitution.md))
4. **Tool Ecosystem** - 56 production tools for file ops, git, testing
5. **Test Infrastructure** - Comprehensive test suite (5,822 tests)

### What's In Progress 🚧
1. **Local Model Integration** - Ollama integration documented but partially implemented
2. **Autonomous Workflows** - Prime commands exist but orchestration is experimental
3. **Agent-to-Agent Communication** - Infrastructure present, full implementation ongoing

### What's Aspirational 🎯
1. **True Local-First Execution** - Currently requires Claude API for all agent operations
2. **100% Autonomous Healing** - Self-healing framework present, production use limited
3. **Cost Optimization Claims** - "96% cost reduction" refers to theoretical local model usage

---

## **Understanding the Architecture**

### The 10 Core Agents

1. **Planner Agent** - Converts specs into technical plans
2. **Coding Agent** - Implements features with TDD approach
3. **Test Generator** - Creates tests following NECESSARY pattern
4. **Quality Enforcer** - Ensures constitutional compliance
5. **Auditor Agent** - Analyzes code quality via AST parsing
6. **Chief Architect** - Creates ADRs and strategic decisions
7. **Learning Agent** - Extracts patterns from sessions
8. **Merger Agent** - Handles git operations and PRs
9. **Toolsmith Agent** - Develops new tools
10. **Work Completion Summary** - Creates task summaries

**Key Insight**: These are currently factory functions that wrap the `agency_swarm` framework, which calls Claude API. They're not fully autonomous local agents (yet).

### The Constitutional Framework

AgencyOS operates under a formal "constitution" ([`constitution.md`](constitution.md)) with 7 Articles:

- **Article I**: Complete Context Before Action
- **Article II**: 100% Verification and Stability
- **Article III**: Automated Local Enforcement
- **Article IV**: Continuous Learning and Improvement
- **Article V**: Spec-Driven Development
- **Article VI**: Red-Green-Refactor TDD Workflow
- **Article VII**: Value-First Testing Philosophy

These aren't just guidelines—they're enforced through code and tests.

### Memory Architecture

**Three-Tier System**:
1. **Anthropic Memory Tool** - Cross-conversation file-based persistence
2. **VectorStore** - Institutional learning with semantic search
3. **Session Context** - Temporary working memory

---

## **Key Documentation**

### For Users
- **[QUICK_START.md](QUICK_START.md)** - 5-minute setup guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[docs/USER_MANUAL.md](docs/USER_MANUAL.md)** - Complete user guide

### For Developers
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical architecture overview
- **[docs/ROADMAP.md](docs/ROADMAP.md)** - Current state → future vision
- **[docs/testing/](docs/testing/)** - Test infrastructure documentation
- **[docs/development/](docs/development/)** - Development guides

### For Understanding the System
- **[constitution.md](constitution.md)** - The governance framework
- **[CLAUDE.md](CLAUDE.md)** - Agent operating instructions
- **[docs/adr/](docs/adr/)** - Architectural Decision Records (47 ADRs)

---

## **Testing**

### Run Tests

```bash
# Full test suite (recommended test runner)
python run_tests.py --run-all

# Fast unit tests only
python run_tests.py --unit

# With Docker (enables Ollama integration tests)
python run_tests.py --with-docker --run-all
```

**Current Status**: Test suite is comprehensive with 5,822 tests. Some test infrastructure quirks exist (see `docs/testing/KNOWN_TEST_ISSUES.md` for details).

---

## **Project Status & Honesty**

### Where We Are Now

**Strengths**:
- Solid infrastructure (memory, tools, governance framework)
- Well-designed agent architecture
- Extensive documentation (744 markdown files)
- Comprehensive test coverage

**Gaps**:
- **Cloud Dependency**: All agents currently require Claude API
- **Test Infrastructure**: Some quirks with test runner (requires `uv` or specific setup)
- **Documentation Overload**: Previously 101 files in root directory (now organized)
- **Claims vs Reality**: Some documentation overstated capabilities

### Honest Assessment

This is a **sophisticated research platform** exploring autonomous agent coordination. It's:
- ✅ Great for **learning about** multi-agent systems
- ✅ Good **infrastructure** for agent orchestration
- 🚧 **Not yet** fully local-first (despite claims)
- 🚧 **Not yet** production-ready for autonomous development

We've reorganized documentation to be honest about current state vs. aspirational goals.

---

## **Roadmap**

See **[docs/ROADMAP.md](docs/ROADMAP.md)** for detailed roadmap, but key goals:

### Near-Term (1-3 Months)
1. Fix test infrastructure quirks
2. Improve local model integration
3. Simplify agent orchestration
4. Better documentation accuracy

### Medium-Term (3-6 Months)
1. True local-first agent execution
2. Reduced dependency on Claude API
3. Production-ready autonomous workflows
4. Proven cost optimization

### Long-Term (6-12 Months)
1. Fully autonomous development cycles
2. Self-improving agent systems
3. Production deployments at scale

---

## **Contributing**

We welcome contributions! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for:
- Development setup
- Code standards
- Testing requirements
- Pull request process

**Key Requirement**: All changes must pass 100% of tests and follow the constitutional framework.

---

## **Community & Support**

- **Issues**: [GitHub Issues](https://github.com/subtract0/AgencyOS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/subtract0/AgencyOS/discussions)
- **Documentation**: Start with [QUICK_START.md](QUICK_START.md)

---

## **License**

[License information to be added]

---

## **Acknowledgments**

This project builds on extensive research in:
- Multi-agent systems
- Constitutional AI governance
- Test-driven development methodologies
- Autonomous software engineering

Special thanks to all contributors and the broader AI research community.

---

**Last Updated**: 2025-01-30
**Status**: Active Development
**Next Major Milestone**: True local-first agent execution
