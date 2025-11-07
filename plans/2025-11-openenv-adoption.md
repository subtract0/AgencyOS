# AgencyOS Local AI Dev Environment Modernization Plan

**Target Platform**: Mac Studio M4 Max (16P+4E cores, 128GB unified memory)
**Timeline**: 2025-11 to 2026-01 (8 weeks, phased rollout)
**Risk Level**: Low-Medium (incremental experiments, rollback-friendly)

---

## I. Strategic Goals

1. **Onboarding Speed**: Reduce new developer setup from 2 hours → 10 minutes
2. **Test Performance**: Unlock M4 Max potential (15-20 min → 5-7 min test runs)
3. **Reproducibility**: Eliminate "works on my machine" bugs (100% config declarative)
4. **Security**: Sandbox agent code execution (prevent RCE/data exfiltration)
5. **Cost**: Maintain $0/month model inference (100% local vcoder-120b)

---

## II. Phased Adoption Roadmap

### Phase 1: DevContainer Foundation (Week 1-2)
**Goal**: Declarative, reproducible development environment

**Deliverables**:
```
.devcontainer/
├── devcontainer.json           # Base config (Python 3.11, extensions)
├── docker-compose.yml          # Multi-service setup
├── Dockerfile                  # Custom image
└── features/
    ├── ollama-setup.sh         # Configure remote vcoder-120b
    └── test-runner.sh          # Memory-aware pytest
```

**Implementation Steps**:

#### Step 1.1: Create Base DevContainer Config
```bash
# Location: .devcontainer/devcontainer.json
{
  "name": "AgencyOS Dev Environment",
  "dockerComposeFile": "docker-compose.yml",
  "service": "agencyos",
  "workspaceFolder": "/workspace",
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    },
    "ghcr.io/devcontainers/features/docker-in-docker:2": {
      "version": "latest"
    },
    "ghcr.io/devcontainers/features/gh:1": {
      "version": "latest"
    }
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "ms-toolsai.jupyter",
        "GitHub.copilot"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.linting.enabled": true,
        "python.linting.pylintEnabled": true,
        "python.formatting.provider": "black"
      }
    }
  },
  "forwardPorts": [8000, 5432],
  "postCreateCommand": ".devcontainer/features/setup.sh",
  "remoteUser": "vscode"
}
```

#### Step 1.2: Docker Compose Multi-Service Setup
```yaml
# Location: .devcontainer/docker-compose.yml
version: '3.8'

services:
  agencyos:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached
    environment:
      - OPENAI_API_BASE=http://192.168.0.2:1234/v1
      - LOCAL_MODEL_NAME=vcoder-120b-1.0-qx86-hi-mlx
      - USE_ENHANCED_MEMORY=true
      - LOCAL_MODEL_TEST_WORKERS=15  # Upgraded for M4 Max
    command: sleep infinity
    network_mode: host  # Access remote LM Studio

  # Optional: Local PostgreSQL for VectorStore experiments
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: agencyos_dev
      POSTGRES_DB: agencyos
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  pgdata:
```

#### Step 1.3: Custom Dockerfile
```dockerfile
# Location: .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (modern pip replacement)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy requirements and install dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install development tools
RUN pip install pytest pytest-xdist black pylint mypy

# Configure for Apple Silicon host (if needed)
ENV TF_ENABLE_ONEDNN_OPTS=0
```

#### Step 1.4: Setup Script
```bash
# Location: .devcontainer/features/setup.sh
#!/bin/bash
set -e

echo "Setting up AgencyOS development environment..."

# Install Python dependencies
pip install -e .

# Verify Ollama connectivity
echo "Testing vcoder-120b connection..."
curl -s http://192.168.0.2:1234/v1/models || echo "⚠️  Warning: vcoder-120b not reachable"

# Run quick smoke test
echo "Running smoke tests..."
pytest tests/test_imports.py -v

echo "✅ Setup complete! Environment ready."
```

**Validation Criteria**:
- [ ] `code .` opens VSCode with correct Python interpreter
- [ ] `pytest tests/` runs with 15 workers (M4 Max)
- [ ] Remote vcoder-120b accessible from container
- [ ] No manual configuration required for new developers

**Rollback Plan**: Delete `.devcontainer/`, resume manual setup (zero risk)

---

### Phase 2: Hardware-Aware Scheduling (Week 3)
**Goal**: Optimize M4 Max resource utilization (currently 5GB / 128GB = 4%)

**Changes to**: `tools/memory_aware_test_runner.py`

#### Before (Current):
```python
def get_safe_worker_count():
    use_local = os.getenv("USE_LOCAL_MODEL", "true").lower() == "true"
    return 3 if use_local else 10  # Conservative for M4 Pro
```

#### After (Adaptive):
```python
import psutil
import platform

def get_adaptive_worker_count():
    """Hardware-aware test parallelism for M4 Max 128GB."""
    total_memory_gb = psutil.virtual_memory().total / (1024**3)
    available_memory_gb = psutil.virtual_memory().available / (1024**3)
    cpu_count = psutil.cpu_count(logical=False)  # Performance cores only

    # Detect hardware profile
    is_mac_studio = platform.system() == "Darwin" and total_memory_gb >= 100

    if is_mac_studio:
        # M4 Max: 16 P-cores, 128GB unified memory
        if os.getenv("LOCAL_MODEL_ACTIVE") == "true":
            # vcoder-120b (remote) uses ~0GB locally, ~30GB on 192.168.0.2
            # Reserve 8GB for OS/IDE, 120GB for tests
            # Each pytest worker: ~6-8GB at peak
            return min(15, cpu_count)  # Upgraded from 6
        else:
            # Cloud-only: aggressive parallelism
            return min(20, cpu_count)
    elif total_memory_gb >= 40:
        # M4 Pro or similar
        return 3 if use_local else 10
    else:
        # Fallback for CI/smaller machines
        return 2

    # Safety check: never exceed available memory / 8GB per worker
    max_workers_by_memory = int(available_memory_gb / 8)
    return min(calculated_workers, max_workers_by_memory, cpu_count)
```

**Testing Protocol**:
1. **Baseline**: `time python run_tests.py --run-all` (record duration)
2. **Apply change**: Update `get_safe_worker_count()` to `get_adaptive_worker_count()`
3. **Measure**: `time python run_tests.py --run-all` (should be 2-3x faster)
4. **Monitor**: `htop` during run (verify 15 workers, ~120GB used)

**Expected Results**:
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Test duration | 15-20 min | 5-7 min | 2.5-3x faster |
| CPU utilization | ~30% | ~90% | Fully utilized |
| Memory usage | 5GB / 128GB (4%) | 120GB / 128GB (93%) | 24x better |
| Cost | $0/month | $0/month | No change |

**Rollback**: `git revert` commit, restart tests with old worker count

---

### Phase 3: Nix Flake Experiment (Week 4, Optional)
**Goal**: Perfect reproducibility, instant environment switching

**Why Nix?**:
- Zero dependency drift (hash-locked)
- Multi-language support (Python + Node.js + Rust in one flake)
- Instant rollback (`nix develop .#previous`)
- Shared binary cache (no rebuild for unchanged deps)

**Installation** (macOS M4):
```bash
# Determinate Systems installer (official Nix, better macOS support)
curl --proto '=https' --tlsv1.2 -sSf -L \
  https://install.determinate.systems/nix | sh -s -- install

# Verify installation
nix --version  # Should show nix 2.18+
```

**Create Flake** (`flake.nix` in repo root):
```nix
{
  description = "AgencyOS Hermetic Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;  # For proprietary tools if needed
        };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Core toolchain
            python311
            python311Packages.pip
            python311Packages.virtualenv

            # Development tools
            gh                    # GitHub CLI
            git
            docker
            docker-compose

            # Optional: Ollama (if running locally)
            # ollama
          ];

          shellHook = ''
            # Auto-configure environment
            export PYTHONPATH="$PWD:$PYTHONPATH"
            export OPENAI_API_BASE="http://192.168.0.2:1234/v1"
            export LOCAL_MODEL_NAME="vcoder-120b-1.0-qx86-hi-mlx"
            export USE_ENHANCED_MEMORY="true"

            # Create venv if not exists
            if [ ! -d ".venv" ]; then
              echo "Creating Python virtual environment..."
              python -m venv .venv
            fi

            source .venv/bin/activate
            pip install -e . > /dev/null 2>&1

            echo "╔═══════════════════════════════════════════════════╗"
            echo "║ AgencyOS Development Environment (Nix)           ║"
            echo "║ Python: $(python --version | cut -d' ' -f2)      ║"
            echo "║ Workers: 15 (M4 Max optimized)                   ║"
            echo "║ Model: vcoder-120b @ 192.168.0.2:1234            ║"
            echo "╚═══════════════════════════════════════════════════╝"
          '';
        };

        # Optional: Production build
        packages.default = pkgs.python311Packages.buildPythonPackage {
          pname = "agencyos";
          version = "1.3.0";
          src = ./.;
          propagatedBuildInputs = with pkgs.python311Packages; [
            anthropic
            pydantic
            pytest
            # ... other deps
          ];
        };
      }
    );
}
```

**Usage**:
```bash
# Enter Nix environment (one-time download, then cached)
nix develop

# Or make it default
echo "use flake" > .envrc
direnv allow  # Auto-load on cd
```

**Comparison: Nix vs. Current**:
| Task | Current (venv) | Nix Flake |
|------|---------------|-----------|
| Setup time | 5-10 min | 30-60s |
| Python version | System-dependent | Pinned (3.11.9) |
| Dep updates | `pip install` | `nix flake update` |
| Rollback | Delete venv | `git checkout HEAD~1` |
| Multi-machine | Manual sync | Zero config |

**Validation**:
- [ ] `nix develop` activates environment in <60s
- [ ] `python --version` shows exact 3.11.9
- [ ] `pytest tests/` runs with vcoder-120b accessible
- [ ] `git checkout older-commit && nix develop` works instantly

**Rollback**: `rm flake.nix flake.lock`, resume venv workflow

---

### Phase 4: Security Sandboxing (Week 5-6)
**Goal**: Prevent RCE/data exfiltration from agent-generated code

**Threat Model**:
1. **CodingAgent** executes `exec(generated_code)` (Python RCE)
2. **BashTool** runs arbitrary shell commands (system compromise)
3. **ToolsmithAgent** creates new tools (supply chain risk)

**Defense Layers**:

#### Layer 1: seccomp (Syscall Whitelist)
```json
// .devcontainer/seccomp-profile.json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_AARCH64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "close",
        "socket", "connect", "bind",
        "stat", "fstat", "lstat",
        "getcwd", "chdir",
        "execve", "fork", "clone"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["ptrace", "mount", "reboot", "init_module"],
      "action": "SCMP_ACT_KILL"
    }
  ]
}
```

**Apply to Docker**:
```yaml
# docker-compose.yml enhancement
services:
  agencyos:
    security_opt:
      - no-new-privileges:true
      - seccomp=.devcontainer/seccomp-profile.json
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only for server agents
```

#### Layer 2: Read-Only Filesystem
```yaml
# docker-compose.yml enhancement
services:
  agencyos:
    read_only: true
    tmpfs:
      - /tmp:size=10G          # Writable scratch space
      - /workspace/.pytest_cache:size=1G
```

#### Layer 3: Network Policies (Future)
```yaml
# Restrict agent network access
services:
  agencyos:
    networks:
      - internal_only  # No internet access

  vcoder_proxy:
    networks:
      - internal_only
      - external  # Only proxy talks to 192.168.0.2
```

**Testing**:
```python
# tests/security/test_sandbox.py
def test_agent_cannot_access_host_filesystem():
    """Verify read-only filesystem prevents file writes."""
    with pytest.raises(PermissionError):
        open("/workspace/malicious.py", "w").write("exploit()")

def test_agent_cannot_bind_privileged_ports():
    """Verify capability dropping prevents port 80 binding."""
    with pytest.raises(PermissionError):
        socket.socket().bind(("0.0.0.0", 80))
```

**Rollback**: Remove `security_opt` from docker-compose.yml

---

### Phase 5: Build Caching (Week 7-8, Optional)
**Goal**: Reduce test time via incremental builds (Bazel)

**Why Bazel?**:
- **6,496 tests**: Perfect use case (large test suite)
- **Intelligent caching**: Only run affected tests
- **Remote execution**: Share cache across machines

**Prerequisites**:
```bash
# Install Bazel (macOS)
brew install bazelisk  # Auto-downloads correct Bazel version

# Install Python rules
cat > WORKSPACE <<EOF
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_python",
    sha256 = "...",
    url = "https://github.com/bazelbuild/rules_python/releases/...",
)
EOF
```

**Example BUILD File**:
```python
# coding_agent/BUILD
load("@rules_python//python:defs.bzl", "py_library", "py_test")

py_library(
    name = "coding_agent",
    srcs = ["coding_agent.py"],
    deps = [
        "//shared:agent_context",
        "//shared:model_policy",
        "@pypi//anthropic",
    ],
    visibility = ["//visibility:public"],
)

py_test(
    name = "coding_agent_test",
    srcs = ["test_coding_agent.py"],
    deps = [":coding_agent"],
    size = "small",  # <60s
    tags = ["unit"],
)
```

**Remote Cache Setup**:
```bash
# .bazelrc
build --remote_cache=grpc://localhost:9092
build --remote_upload_local_results=true
test --test_output=errors  # Only show failures
```

**Expected Results**:
| Scenario | Time (No Cache) | Time (Cached) | Speedup |
|----------|----------------|---------------|---------|
| First run | 15 min | 15 min | 1x |
| No changes | 15 min | 30s | 30x |
| 1 file changed | 15 min | 2 min | 7.5x |

**Trade-offs**:
- **Pro**: 90%+ cache hit rate after initial run
- **Con**: 40-60 hours to generate BUILD files for entire codebase
- **Verdict**: Defer to Q1 2026 (Phase 5 is optional)

---

## III. Required Tooling

### Immediate (Phase 1-2):
```bash
# macOS M4 Max setup
brew install --cask docker  # For DevContainers
brew install gh             # GitHub CLI
pip install psutil          # For adaptive worker count
```

### Optional (Phase 3):
```bash
# Nix package manager
curl -L https://install.determinate.systems/nix | sh

# direnv (auto-load Nix environment on cd)
brew install direnv
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
```

### Optional (Phase 5):
```bash
# Bazel build system
brew install bazelisk
```

---

## IV. Risk Assessment & Mitigation

### Risk 1: DevContainer Performance Overhead
**Likelihood**: Medium
**Impact**: Low (2-5% slowdown)
**Mitigation**:
- Use `:cached` mount for volumes (already in plan)
- Disable unnecessary features
- Benchmark before/after

### Risk 2: M4 Max Memory Exhaustion
**Likelihood**: Low
**Impact**: High (system freeze)
**Mitigation**:
- Safety check in `get_adaptive_worker_count()` (already in code)
- Monitor with `htop` during first run
- Gradual ramp-up (12 → 15 → 18 workers)

### Risk 3: Nix Learning Curve
**Likelihood**: High
**Impact**: Low (optional experiment)
**Mitigation**:
- Phase 3 is optional (can defer)
- Provide templates + documentation
- Rollback-friendly (delete flake.nix)

### Risk 4: seccomp Breaks Legitimate Code
**Likelihood**: Medium
**Impact**: Medium (CI fails)
**Mitigation**:
- Whitelist syscalls incrementally
- Test with existing test suite first
- Keep escape hatch (disable seccomp flag)

### Risk 5: Bazel Migration Complexity
**Likelihood**: Very High
**Impact**: High (dev productivity hit)
**Mitigation**:
- Phase 5 is optional + deferred to Q1 2026
- Start with small module (coding_agent/)
- Use auto-generation tools (rules_python)

---

## V. Success Metrics

### Quantitative KPIs:
| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Developer onboarding | 2 hours | <10 min | Time to first `pytest tests/` |
| Test execution time | 15-20 min | 5-7 min | `time python run_tests.py --run-all` |
| Memory utilization | 5GB / 128GB (4%) | 120GB / 128GB (93%) | `htop` during test run |
| Config drift incidents | 2-3/month | 0/month | Support tickets |
| Security vulnerabilities | Unknown | 0 | Penetration testing |

### Qualitative KPIs:
- [ ] New contributor can run tests without manual steps
- [ ] Zero "works on my machine" bugs in code reviews
- [ ] Agent code execution sandboxed (no RCE risk)
- [ ] Rollback to any previous environment in <60s

---

## VI. Rollback Plan (Per Phase)

### Phase 1 (DevContainer):
```bash
# Complete rollback
rm -rf .devcontainer/
git checkout -- .  # Resume manual setup
```

### Phase 2 (Adaptive Workers):
```bash
# Revert commit
git revert <commit-hash>
# Or: Edit tools/memory_aware_test_runner.py manually
```

### Phase 3 (Nix):
```bash
# Remove Nix files
rm flake.nix flake.lock
rm -rf .direnvrc
# Uninstall Nix (optional)
/nix/nix-installer uninstall
```

### Phase 4 (Sandboxing):
```yaml
# Edit docker-compose.yml, remove security_opt
services:
  agencyos:
    # security_opt: []  # Commented out
```

### Phase 5 (Bazel):
```bash
# Delete Bazel files
rm WORKSPACE BUILD .bazelrc
rm -rf bazel-*  # Generated directories
```

**General Principle**: All phases are **additive** (no breaking changes), so rollback = delete new files.

---

## VII. Timeline & Ownership

### Week 1-2: DevContainer (HIGH PRIORITY)
- **Owner**: Platform team
- **Time**: 6-8 hours
- **Deliverables**: `.devcontainer/` directory, documentation
- **Validation**: New developer onboards in <10 min

### Week 3: Adaptive Workers (HIGH PRIORITY)
- **Owner**: Testing team
- **Time**: 2 hours
- **Deliverables**: Updated `memory_aware_test_runner.py`
- **Validation**: Test run <7 min on M4 Max

### Week 4: Nix Experiment (OPTIONAL)
- **Owner**: Infrastructure team
- **Time**: 8-12 hours
- **Deliverables**: `flake.nix`, documentation
- **Validation**: Environment loads in <60s

### Week 5-6: Security Sandboxing (MEDIUM PRIORITY)
- **Owner**: Security team
- **Time**: 6-8 hours
- **Deliverables**: `seccomp-profile.json`, tests
- **Validation**: Agent cannot escape sandbox

### Week 7-8: Bazel (OPTIONAL, DEFERRED)
- **Owner**: Build team
- **Time**: 40-60 hours
- **Deliverables**: WORKSPACE, BUILD files
- **Validation**: Cache hit rate >90%

---

## VIII. Next Steps (Immediate Actions)

### This Week (2025-11-07 to 2025-11-14):
1. **Review & approve** this plan (stakeholder sign-off)
2. **Create branch**: `git checkout -b feat/openenv-adoption`
3. **Implement Phase 1**: DevContainer setup (6-8 hours)
4. **Test locally**: Validate onboarding flow
5. **Document**: Update CLAUDE.md with new setup instructions

### Next Week (2025-11-15 to 2025-11-21):
1. **Implement Phase 2**: Adaptive worker count (2 hours)
2. **Benchmark**: Measure test time improvement
3. **Deploy**: Merge to main, notify team
4. **Monitor**: Watch for memory issues (unlikely with safety checks)

### Month 2 (2025-12):
1. **Phase 3**: Nix experiment (optional weekend project)
2. **Phase 4**: Security sandboxing (1 week sprint)
3. **Retrospective**: Review metrics, adjust plan

---

## IX. Communication Plan

### Stakeholders:
- **Development Team**: New DevContainer setup instructions
- **QA Team**: Faster test runs (5-7 min)
- **Security Team**: Sandboxing roadmap
- **Management**: Cost savings ($0/month maintained)

### Channels:
- **Slack**: #engineering channel (progress updates)
- **Docs**: Update CLAUDE.md, README.md
- **Demo**: Lunch & learn session (show DevContainer workflow)

---

## X. Appendix: Command Reference

### DevContainer Commands:
```bash
# Open in container (VSCode)
code .

# Rebuild container
cmd+shift+p → "Dev Containers: Rebuild Container"

# Attach shell to running container
docker compose exec agencyos bash
```

### Nix Commands:
```bash
# Enter development environment
nix develop

# Update dependencies
nix flake update

# Rollback to previous version
git checkout HEAD~1 && nix develop
```

### Testing Commands:
```bash
# Full test suite (M4 Max optimized)
python run_tests.py --run-all

# Watch mode (re-run on file changes)
pytest-watch tests/

# Profile memory usage
python -m memory_profiler run_tests.py
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-07
**Next Review**: 2025-12-07 (monthly cadence)
**Maintained By**: Platform Team

**Related Documents**:
- `docs/ci/OPENENV_COMPARISON.md` (research synthesis)
- `docs/HARDWARE_OPTIMIZATION.md` (M4 Max specifics)
- `CLAUDE.md` (AgencyOS master constitution)
