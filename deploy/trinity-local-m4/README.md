# Trinity Local M4 - Self-Contained 3-LLM Autonomous Loop

**Deployable package for M4 MacBook (48GB RAM)**

## What This Is

A **self-contained deployment** of the Trinity Protocol that runs **3 local LLMs** in a continuous autonomous loop:

- **WITNESS** (qwen2.5-coder:1.5b): Pattern detection from telemetry (<200ms latency)
- **ARCHITECT** (qwen2.5-coder:7b): Strategic planning and spec generation
- **EXECUTOR** (codestral:22b): Code execution via 6 specialized sub-agents

**Zero cloud dependency** after installation. 100% offline operation.

## One-Command Installation

### Option 1: Direct from GitHub (when released)

```bash
curl -fsSL https://raw.githubusercontent.com/subtract0/AgencyOS/main/deploy/trinity-local-m4/install.sh | bash
```

### Option 2: From Local Agency Repo

```bash
# If you have Agency cloned locally
cd /path/to/Agency
./deploy/trinity-local-m4/install.sh
```

## What the Installer Does

1. **Verifies System**:
   - macOS 14+
   - Apple Silicon (M4 preferred, M1/M2/M3 works)
   - 48GB+ RAM
   - 50GB+ free disk space

2. **Installs Ollama** (if not present):
   - Downloads Ollama installer
   - Starts Ollama service
   - Pulls 3 models (~19GB download)

3. **Sets Up Python Environment**:
   - Creates virtualenv at `~/.trinity-local/.venv`
   - Installs minimal dependencies (httpx, pydantic, sqlalchemy)

4. **Initializes Trinity**:
   - Copies Trinity Protocol core modules
   - Creates configuration file
   - Initializes SQLite databases
   - Creates launcher scripts

5. **Validates Installation**:
   - Health check on all 3 models
   - Python dependency verification
   - Database connectivity test

**Total Install Time**: 10-20 minutes (mostly model downloads)

## Usage

### Start Trinity Loop

```bash
cd ~/.trinity-local
./start_trinity.sh
```

Or use the alias (after restarting shell):

```bash
trinity
```

### Monitor Status

```bash
cd ~/.trinity-local
./monitor_trinity.sh
```

Or:

```bash
trinity-monitor
```

### Stop Trinity Loop

```bash
cd ~/.trinity-local
./stop_trinity.sh
```

Or:

```bash
trinity-stop
```

### View Logs

```bash
tail -f ~/.trinity-local/logs/trinity_local/trinity.log
```

## Architecture

### 3-Model Hierarchy

```
WITNESS (qwen2.5-coder:1.5b, ~2GB)
  ↓ detects pattern
  ↓ signals ARCHITECT

ARCHITECT (qwen2.5-coder:7b, ~8GB)
  ↓ creates spec/plan
  ↓ queues task

EXECUTOR (codestral:22b, ~24GB)
  ↓ executes task via sub-agents:
  ├─ CODE_WRITER (reuses codestral:22b)
  ├─ TEST_ARCHITECT (reuses codestral:22b)
  ├─ TOOL_DEVELOPER (reuses codestral:22b)
  ├─ IMMUNITY_ENFORCER (reuses qwen2.5-coder:7b)
  ├─ RELEASE_MANAGER (reuses qwen2.5-coder:7b)
  └─ TASK_SUMMARIZER (reuses qwen2.5-coder:1.5b)
```

**Memory Budget**: Peak 34GB (14GB headroom for OS)

### Sequential Execution (Memory Efficient)

Models load/unload sequentially:
1. WITNESS runs → detects → unloads
2. ARCHITECT loads → plans → unloads
3. EXECUTOR loads → executes → unloads

No parallel model loading ensures memory stays under 34GB.

## Configuration

Edit `~/.trinity-local/trinity_config.yaml` to customize:

```yaml
models:
  witness:
    name: "qwen2.5-coder:1.5b"
    temperature: 0.3
    timeout: 30

  architect:
    name: "qwen2.5-coder:7b"
    temperature: 0.5
    timeout: 120

  executor:
    name: "codestral:22b"
    temperature: 0.3
    timeout: 300

memory:
  max_total_mb: 34000
  sequential_execution: true

constitutional:
  enable_learning: true    # VectorStore (Article IV)
  enforce_tests: true      # 100% test compliance (Article II)
  max_autonomous_commits: 10
```

## Troubleshooting

### Ollama Not Running

```bash
# Start Ollama manually
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

### Model Not Found

```bash
# List available models
ollama list

# Pull missing model
ollama pull qwen2.5-coder:1.5b
```

### Out of Memory

- Check peak memory: `./monitor_trinity.sh`
- If >34GB: Reduce `ollama_num_ctx` in config
- Ensure `sequential_execution: true` in config

### Trinity Won't Start

```bash
# Check logs
tail -100 ~/.trinity-local/logs/trinity_local/trinity.log

# Verify Python deps
cd ~/.trinity-local
source .venv/bin/activate
python3 -c "import httpx, pydantic, sqlalchemy; print('OK')"
```

## File Locations

```
~/.trinity-local/
├── .venv/                      # Python virtualenv
├── trinity_protocol/           # Core Trinity modules
├── shared/                     # Shared infrastructure
├── db/                         # SQLite databases
│   ├── message_bus.db
│   └── patterns.db
├── logs/trinity_local/         # Logs and telemetry
├── trinity_config.yaml         # Configuration
├── start_trinity.sh            # Launcher
├── stop_trinity.sh             # Shutdown
├── monitor_trinity.sh          # Status monitor
└── trinity.pid                 # Process ID (when running)
```

## System Requirements

- **OS**: macOS 14+ (Sonoma or later)
- **CPU**: Apple Silicon (M4 preferred, M1/M2/M3 supported)
- **RAM**: 48GB unified memory (minimum)
- **Disk**: 50GB free space (models + logs)
- **Network**: Required for initial setup only

## Performance Benchmarks

- **Pattern Detection**: <200ms per event (WITNESS)
- **Spec Generation**: ~2 minutes (ARCHITECT)
- **Task Execution**: ~10 minutes (EXECUTOR, varies by complexity)
- **Peak Memory**: ~34GB (EXECUTOR loaded)
- **Idle Memory**: ~2GB (WITNESS only)

## Constitutional Compliance

All operations adhere to the 5 Constitutional Articles:

1. **Complete Context**: Retry on timeout (2x, 3x, 10x)
2. **100% Verification**: All tests pass before commit
3. **Automated Enforcement**: No manual overrides
4. **Continuous Learning**: VectorStore integration (MANDATORY)
5. **Spec-Driven Development**: Formal specs for complex features

## Uninstallation

```bash
# Stop Trinity if running
cd ~/.trinity-local && ./stop_trinity.sh

# Remove Trinity directory
rm -rf ~/.trinity-local

# Remove Ollama models (optional)
ollama rm qwen2.5-coder:1.5b
ollama rm qwen2.5-coder:7b
ollama rm codestral:22b

# Uninstall Ollama (optional)
# Manual removal required - delete /usr/local/bin/ollama
```

## Support

- **Documentation**: See `specs/spec-local-trinity-deployment.md`
- **Issues**: GitHub Issues on subtract0/AgencyOS
- **Architecture**: See `docs/A-Strategic-Framework-for-a-Hybrid-Autonomous-Trinity-on-Apple-Silicon.md`

---

**Status**: Ready for deployment
**Version**: 1.0.0
**Last Updated**: 2025-10-04
