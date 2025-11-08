# Quick Start Guide - AgencyOS

Get up and running with AgencyOS in **5 minutes**.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.12 or 3.13** installed
- **Git** installed
- **An Anthropic API key** (get one at [console.anthropic.com](https://console.anthropic.com))
- **15GB+ free disk space** (for dependencies and models)

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/subtract0/AgencyOS.git
cd AgencyOS
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows
```

### Step 3: Install Dependencies

```bash
# Install AgencyOS and all dependencies
pip install -e .
```

**Expected time**: 2-3 minutes

### Step 4: Configure API Key

Choose one of these methods:

**Option A: Environment Variable**
```bash
export OPENAI_API_KEY=your_anthropic_key_here
```

**Option B: .env File** (Recommended)
```bash
# Create .env file in project root
echo "OPENAI_API_KEY=your_anthropic_key_here" > .env
```

**Option C: Set in Shell Profile**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export OPENAI_API_KEY=your_anthropic_key_here' >> ~/.bashrc
source ~/.bashrc
```

---

## Verify Installation

### Run the Test Suite

```bash
# Run unit tests to verify setup
python run_tests.py --unit
```

**Expected**: Tests should start running. You should see output like:
```
============================= test session starts ==============================
...
5,822 passed, 164 skipped in 180.43s
```

**If tests fail with interpreter error**: Your local Codex agent has already identified this. Use the project's test runner as shown above.

---

## Your First Agent Interaction

### Option 1: Interactive Demo

```bash
python demo_unified.py
```

This runs a demonstration of the agent system's capabilities.

### Option 2: Health Check

```bash
python agency.py health
```

Shows system health status including:
- Constitutional compliance
- Test status
- Agent availability
- Memory system status

### Option 3: Use Prime Commands (Advanced)

If you're using Claude Code/Codex:

```
/primecc
```

This loads the essential context for agent operations.

---

## Common Issues & Solutions

### Issue: "No module named 'anthropic'"

**Solution**:
```bash
pip install -e .
```

### Issue: "OPENAI_API_KEY not set"

**Solution**: Follow Step 4 above to configure your API key.

### Issue: Tests won't run

**Solution**: Use the recommended test runner:
```bash
python run_tests.py --run-all
```

**NOT**: Direct pytest (which may have issues with Python 3.13)

### Issue: "ModuleNotFoundError: No module named 'sklearn'"

**Solution**:
```bash
pip install scikit-learn>=1.0.0
```

---

## What's Next?

### Learn the Basics

1. **Read the Constitution**: Understand the governance framework
   ```bash
   cat constitution.md
   ```

2. **Explore the Agents**: See what each agent does
   ```bash
   cat docs/AGENTS.md
   ```

3. **Review the Architecture**: Understand the system design
   ```bash
   cat docs/ARCHITECTURE.md
   ```

### Try Development Workflows

1. **Create a feature branch**:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make changes** to code

3. **Run tests**:
   ```bash
   python run_tests.py --unit
   ```

4. **Create a pull request** (see [CONTRIBUTING.md](CONTRIBUTING.md))

### Explore Prime Commands

If using Claude Code locally:

- `/primecc` - Load context
- `/scout "search term"` - Search codebase
- `/agent-memory-query "topic"` - Query VectorStore
- `/constitutional-audit` - Check compliance

See [CLAUDE.md](CLAUDE.md) for full command reference.

---

## Directory Structure

```
AgencyOS/
├── README.md              # Project overview
├── QUICK_START.md         # This file
├── CONTRIBUTING.md        # Contribution guide
├── constitution.md        # Governance framework
├── CLAUDE.md             # Agent instructions
│
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md    # Technical architecture
│   ├── ROADMAP.md        # Project roadmap
│   ├── USER_MANUAL.md    # Complete user guide
│   ├── testing/          # Test documentation
│   ├── development/      # Dev guides
│   └── adr/              # Architecture decisions
│
├── shared/               # Shared infrastructure
├── tools/                # 56+ agent tools
├── *_agent/              # 10 specialized agents
├── agency_memory/        # Memory systems
├── tests/                # Test suite (5,822 tests)
└── specs/                # Feature specifications
```

---

## Getting Help

- **Documentation**: Start with [README.md](README.md)
- **User Manual**: See [docs/USER_MANUAL.md](docs/USER_MANUAL.md)
- **Issues**: [GitHub Issues](https://github.com/subtract0/AgencyOS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/subtract0/AgencyOS/discussions)

---

## Next Steps

Once you're set up:

1. **Read** [README.md](README.md) for project overview
2. **Review** [constitution.md](constitution.md) for governance
3. **Explore** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical details
4. **Contribute** following [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Questions?** Open an issue or start a discussion on GitHub.

**Ready to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow.
