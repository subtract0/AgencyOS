# 📍 AgencyOS Codebase Map - M4 Max Edition

## 🏗️ Directory Structure

```
/Users/am/Code/AgencyOS/
├── .claude/                    # Agent configuration & instructions
│   ├── agents/                 # 10 agent definitions
│   ├── commands/               # Slash commands
│   ├── quick-ref/              # Fast lookup docs (city-map.md)
│   └── docs/                   # Deep documentation
│
├── docs/                       # Full documentation
│   ├── architecture/           # System design
│   ├── adr/                    # Architecture Decision Records
│   ├── setup/                  # Setup guides (includes Apple Silicon)
│   └── getting-started/        # Getting started guide
│
├── src/agency/                 # Core agency framework
├── shared/                     # Shared utilities & types
│   ├── type_definitions/       # Type safety (Result, JSONValue)
│   ├── models/                 # Pydantic models
│   └── *.py                    # Utilities (memory, routing, etc.)
│
├── tools/                      # 60+ production tools
│   ├── ci_monitor/             # CI/CD monitoring
│   ├── ml_routing/             # ML model routing
│   ├── orchestrator/           # Task orchestration
│   ├── kanban/                 # Kanban board
│   └── *.py                    # Individual tools
│
├── agents/                     # 10 core agents
│   ├── coding_agent/           # Code generation
│   ├── planner_agent/          # Planning
│   ├── auditor_agent/          # Quality audit
│   ├── quality_enforcer_agent/ # Constitutional compliance
│   └── ...                     # 6 more agents
│
├── trinity_protocol/           # Multi-agent orchestration
│   ├── core/                   # Production core
│   ├── experimental/           # R&D code
│   └── demos/                  # Working examples
│
├── tests/                      # 1700+ tests (100% pass)
│   ├── unit/                   # Fast unit tests
│   ├── integration/            # Service integration tests
│   ├── e2e/                    # End-to-end tests
│   └── fixtures/               # Test utilities
│
├── dspy_agents/                # DSPy-enhanced agents
├── learning_agent/             # Pattern learning system
├── pattern_intelligence/       # Learning extraction
├── agency_memory/              # Memory persistence
│
├── scripts/                    # Automation scripts
├── specs/                      # Formal specifications
├── plans/                      # Implementation plans
│
├── pyproject.toml              # Python project config
├── requirements.txt            # Full dependencies
├── poetry.lock                 # Locked dependency versions
├── pytest.ini                  # Test configuration
├── .env                        # Local environment (secrets)
│
├── SETUP_M4_MAX.md             # This session's setup guide
├── AGENTS.md                   # Agent architecture
├── constitution.md             # Constitutional rules
├── README.md                   # Main documentation
└── CODEBASE_MAP.md            # This file
```

## 🎯 Key Entry Points

### For Development
- **Start here**: `docs/getting-started/README.md`
- **Architecture**: `docs/architecture/overview.md`
- **For agents**: `.claude/quick-ref/city-map.md`

### For Running
- **Tests**: `pytest tests/` (via Poetry)
- **Agency**: `poetry run python -m agency`
- **Trinity**: `poetry run python -m trinity_protocol`

### For Learning
- **Constitutional rules**: `constitution.md`
- **Agent system**: `AGENTS.md`
- **Local LLM**: `SETUP_M4_MAX.md`

## 🔧 Development Tools

### Code Quality
- **Ruff**: Linting + formatting (configured in `pyproject.toml`)
- **MyPy**: Type checking
- **Pytest**: Testing (1700+ tests)
- **Hypothesis**: Property-based testing

### Git & Version Control
- **GitWorkflowTool**: Atomic commits + PR automation
- **Pre-commit hooks**: Constitutional enforcement
- **Branch protection**: GitHub rules enforcement

### Monitoring & Observability
- **Cost tracking**: OpenAI API cost monitoring
- **Telemetry**: System health metrics
- **Learning extraction**: Pattern analysis across sessions

## 📦 Python Structure

### Modules (All via Poetry)
```python
import shared              # Utilities
import tools              # Production tools
import agents             # AI agents
import trinity_protocol   # Multi-agent orchestration
import dspy_agents        # DSPy-enhanced agents
import learning_agent     # Pattern learning
import pattern_intelligence  # Learning extraction
```

### Type Safety (Constitutional)
```python
from shared.type_definitions import JSONValue, Result
from pydantic import BaseModel  # Type validation

# ✅ GOOD - Type-safe
class Config(BaseModel):
    model: str
    temperature: float

# ❌ BAD - Never used in main branch
data: Dict[Any, Any]  # Constitutional violation!
```

## 🚀 Common Tasks

### Run All Tests
```bash
/opt/homebrew/bin/poetry run pytest tests/ -v
```

### Type Check Code
```bash
/opt/homebrew/bin/poetry run mypy shared/
```

### Format & Lint
```bash
/opt/homebrew/bin/poetry run ruff format .
/opt/homebrew/bin/poetry run ruff check .
```

### Run Specific Test
```bash
/opt/homebrew/bin/poetry run pytest tests/unit/test_agency.py -v
```

## 💾 Configuration Files

### `.env` - Local Configuration
- OpenAI API keys
- Firestore credentials
- Model settings
- Local LLM configuration

### `pyproject.toml` - Python Config
- Dependencies
- Test configuration
- Ruff rules
- Coverage settings

### `pytest.ini` - Test Runner
- Test discovery patterns
- Markers (unit, integration, e2e)
- Parallel execution settings
- Timeouts

### `.pre-commit-config.yaml` - Git Hooks
- Automatic code formatting
- Type checking
- Constitution checks

## 🎯 Next Steps

1. **Model download** (happening now in background)
   - Check: `tail -f /tmp/ollama_download.log`

2. **Run verification**
   ```bash
   /Users/am/Code/AgencyOS/.start-dev.sh
   ```

3. **Try a test**
   ```bash
   cd /Users/am/Code/AgencyOS
   /opt/homebrew/bin/poetry run pytest tests/unit/ -v -x --tb=short
   ```

## 📖 Documentation Resources

| Topic | Location |
|-------|----------|
| **Getting Started** | `docs/getting-started/README.md` |
| **Architecture** | `docs/architecture/overview.md` |
| **Constitutional Rules** | `constitution.md` |
| **Agent Guide** | `AGENTS.md` |
| **Trinity Protocol** | `trinity_protocol/README.md` |
| **Setup (Local LLM)** | `SETUP_M4_MAX.md` |
| **Apple Silicon** | `docs/setup/APPLE_SILICON_AI_SETUP.md` |

---

**Last Updated**: 2025-10-30
**Status**: ✅ Environment ready
**Next**: Monitor model download in `/tmp/ollama_download.log`
