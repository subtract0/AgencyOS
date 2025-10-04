# 🔒 Offline Mode - Zero Network Dependency

**Stricter than `--local-only`**: Works even when disconnected from internet

---

## Comparison: Local-Only vs Offline

| Feature | Local-Only | **Offline** |
|---------|-----------|-----------|
| **LLM Inference** | ✅ Ollama (local) | ✅ Ollama (local) |
| **Embeddings** | sentence-transformers (downloads models first) | ✅ Pre-downloaded models |
| **Model Updates** | Can pull new models | ❌ Uses only local cache |
| **Ollama Service** | Can download models on-demand | ✅ Uses only pre-pulled models |
| **Internet Required** | Only for pip install | ❌ Never (after setup) |

---

## How Offline Mode Works

### 1. Setup Phase (Internet Required, One-Time)
```bash
bash setup_consciousness.sh --offline
```

**What it does**:
- Downloads all models to local cache
- Downloads sentence-transformer weights
- Pre-caches all Python dependencies
- Creates offline package bundle
- **After this, internet not needed**

### 2. Runtime (No Internet Required)
```bash
# Disconnect from WiFi completely
# Constitutional Consciousness still works:
bash start_night_run.sh --offline
```

**What happens**:
- ✅ Ollama uses local models only (no pull attempts)
- ✅ sentence-transformers uses cached weights
- ✅ VectorStore operates entirely in RAM/disk
- ✅ No DNS lookups, no HTTP requests

---

## Implementation

### Changes to Feedback Loop

```python
# tools/constitutional_consciousness/feedback_loop.py

class ConstitutionalFeedbackLoop:
    def __init__(
        self,
        log_path: str = "logs/autonomous_healing/constitutional_violations.jsonl",
        enable_vectorstore: bool = True,
        offline_mode: bool = False,  # NEW
    ):
        self.offline_mode = offline_mode

        if self.enable_vectorstore:
            if self.offline_mode:
                # Use local sentence-transformers with cached models
                self.vector_store = create_enhanced_memory_store(
                    embedding_provider="sentence-transformers",
                    model_cache_dir=".cache/sentence_transformers"  # Local cache
                )
            else:
                # Can download models if needed
                self.vector_store = create_enhanced_memory_store(
                    embedding_provider="sentence-transformers"
                )
```

### Changes to VectorStore

```python
# agency_memory/vector_store.py

def _init_sentence_transformers(self, cache_dir: str = None) -> None:
    """Initialize sentence-transformers with optional cache."""
    from sentence_transformers import SentenceTransformer

    model_name = "all-MiniLM-L6-v2"  # 80MB model

    if cache_dir:
        # Offline mode: Use pre-downloaded cache
        self._embedding_model = SentenceTransformer(
            model_name,
            cache_folder=cache_dir,
            device="cpu"  # Works on any hardware
        )
    else:
        # Online mode: Can download if needed
        self._embedding_model = SentenceTransformer(model_name)
```

---

## Offline Setup Script

### `setup_consciousness.sh --offline`

**Additional steps**:

1. **Download sentence-transformer models**:
```bash
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('.cache/sentence_transformers/all-MiniLM-L6-v2')
print('✓ Embeddings cached locally')
"
```

2. **Verify all Ollama models are local**:
```bash
# Pull all models if not present
ollama pull codestral:22b-v0.1-q4_K_M
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
ollama pull qwen2.5-coder:1.5b-instruct-q4_K_M

# Verify no network needed
OFFLINE_TEST=$(ollama list 2>/dev/null | wc -l)
if [ "$OFFLINE_TEST" -lt 3 ]; then
    echo "❌ Models not fully cached"
    exit 1
fi
```

3. **Create offline Python package**:
```bash
# Download all dependencies to local vendor directory
pip download -r requirements.txt -d .vendor/

# Create offline installer
cat > install_offline.sh <<'EOF'
#!/bin/bash
pip install --no-index --find-links=.vendor/ -r requirements.txt
EOF
chmod +x install_offline.sh
```

4. **Test offline operation**:
```bash
# Disable network
sudo ifconfig en0 down

# Verify Constitutional Consciousness works
python -m tools.constitutional_consciousness.feedback_loop --days 7 --offline

# Re-enable network
sudo ifconfig en0 up
```

---

## Offline Mode Features

### What Works Offline

✅ **Constitutional Consciousness**:
- Pattern detection (rule-based, no LLM)
- VectorStore storage (local embeddings)
- Prediction engine (mathematical calculations)
- Agent evolution proposals (template-based)

✅ **Ollama Models**:
- All 3 models run from local cache
- No model updates attempted
- No registry checks

✅ **Python Dependencies**:
- All packages in `.vendor/` directory
- No PyPI access needed

### What Doesn't Work Offline

❌ **Model Updates**: Can't pull new Ollama models
❌ **pip install**: Can't install new Python packages
❌ **Git Push**: Can't push changes to remote (local commits only)
❌ **External APIs**: Obviously no OpenAI, Anthropic, etc.

---

## Use Cases for Offline Mode

### 1. Air-Gapped Environments
- High-security deployments
- Classified networks
- Compliance requirements (HIPAA, SOC2, etc.)

### 2. Field Deployments
- Remote locations with no internet
- Mobile development (airplane mode)
- Bandwidth-constrained environments

### 3. Privacy-Critical Work
- Sensitive code analysis
- Proprietary algorithms
- Trade secret development

### 4. Cost Optimization
- No accidental API calls
- No bandwidth usage
- Guaranteed $0 runtime cost

---

## Offline Setup Commands

### Full Offline Package Creation

```bash
# On a machine with internet (one-time setup):
bash setup_consciousness.sh --offline-bundle

# This creates: agency_offline_v1.0.0.tar.gz
# Contains:
#   - All Ollama models (20GB)
#   - All Python dependencies
#   - sentence-transformer weights (80MB)
#   - Constitutional Consciousness source
```

### Offline Deployment (No Internet)

```bash
# Transfer agency_offline_v1.0.0.tar.gz to offline machine via USB/etc.
tar -xzf agency_offline_v1.0.0.tar.gz
cd agency_offline_v1.0.0

# Install (no internet needed)
bash install_offline.sh

# Run
bash start_night_run.sh --offline
```

---

## Offline Validation Tests

### Test 1: Network Disabled
```bash
sudo ifconfig en0 down  # Disable WiFi
python -m tools.constitutional_consciousness.feedback_loop --offline
# Should complete successfully
sudo ifconfig en0 up
```

### Test 2: DNS Failure Simulation
```bash
# Point DNS to localhost (breaks resolution)
sudo networksetup -setdnsservers Wi-Fi 127.0.0.1

python -m tools.constitutional_consciousness.feedback_loop --offline
# Should complete successfully

# Restore DNS
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8
```

### Test 3: Firewall Block
```bash
# Block all outgoing connections (macOS)
sudo pfctl -e
sudo pfctl -f /etc/pf.conf

python -m tools.constitutional_consciousness.feedback_loop --offline
# Should complete successfully

sudo pfctl -d  # Disable firewall
```

---

## Offline Mode Configuration

### `.env.offline`

```bash
# Offline Mode Configuration
AGENCY_MODE=offline
OFFLINE_MODE=true

# No external services
ENABLE_GPT5_ESCALATION=false
USE_OPENAI_FALLBACK=false
OLLAMA_AUTO_PULL=false  # Don't attempt model downloads

# Local-only paths
OLLAMA_MODELS_DIR=.cache/ollama
SENTENCE_TRANSFORMERS_CACHE=.cache/sentence_transformers
VECTORSTORE_PATH=.cache/vectorstore

# Ollama models (pre-downloaded)
PLANNER_MODEL=codestral:22b-v0.1-q4_K_M
CODER_MODEL=qwen2.5-coder:7b-instruct-q4_K_M
SCANNER_MODEL=qwen2.5-coder:1.5b-instruct-q4_K_M

# Constitutional Consciousness
ENABLE_CONSCIOUSNESS=true
AUTONOMOUS_NIGHT_RUN=true
```

---

## Performance Impact

### Offline vs Local-Only

| Metric | Local-Only | Offline | Difference |
|--------|-----------|---------|------------|
| **Setup Time** | 15 min | 20 min | +5 min (pre-caching) |
| **Disk Usage** | 20GB | 21GB | +1GB (vendor packages) |
| **Runtime Speed** | Same | Same | No difference |
| **Network Usage** | 0 MB | 0 MB | Guaranteed |

### Benefits of Offline Mode

✅ **Guaranteed isolation**: No accidental network calls
✅ **Compliance**: Meet air-gap requirements
✅ **Portability**: USB-transferable bundle
✅ **Resilience**: Works anywhere, anytime

---

## Offline Bundle Contents

### `agency_offline_v1.0.0.tar.gz` Structure

```
agency_offline_v1.0.0/
├── ollama_models/
│   ├── codestral-22b-q4_k_m.gguf       (13.4GB)
│   ├── qwen2.5-coder-7b-q4_k_m.gguf    (4.7GB)
│   └── qwen2.5-coder-1.5b-q4_k_m.gguf  (1.5GB)
├── .vendor/                             (Python packages)
│   ├── sentence-transformers-*.whl
│   ├── pydantic-*.whl
│   ├── litellm-*.whl
│   └── ...
├── .cache/
│   └── sentence_transformers/
│       └── all-MiniLM-L6-v2/           (80MB)
├── install_offline.sh                   (Offline installer)
├── start_night_run.sh --offline         (Offline runner)
└── [Constitutional Consciousness source]
```

**Total Size**: ~21GB

---

## Security Benefits

### Attack Surface Reduction

**Local-Only Mode**:
- No OpenAI API (prevents API key leakage)
- No cloud services
- BUT: Can still reach PyPI, Ollama registry

**Offline Mode** (Stricter):
- ✅ No OpenAI API
- ✅ No cloud services
- ✅ No PyPI access
- ✅ No Ollama registry access
- ✅ Zero network activity

### Compliance Advantages

| Requirement | Local-Only | Offline |
|------------|-----------|---------|
| **HIPAA** | ✅ | ✅✅ (stronger) |
| **SOC2** | ✅ | ✅✅ (auditable) |
| **Air-Gap** | ❌ (needs internet for setup) | ✅ (transferable bundle) |
| **Zero Trust** | Partial | ✅ Full |

---

## Creating Offline Release

### For v1.0.0 Release:

```bash
# Create offline bundle (on machine with internet)
bash create_offline_bundle.sh

# Outputs:
# - agency_offline_v1.0.0.tar.gz (21GB)
# - agency_offline_v1.0.0.sha256 (checksum)
```

### Upload to GitHub Release:

```bash
gh release upload v1.0.0 agency_offline_v1.0.0.tar.gz
gh release upload v1.0.0 agency_offline_v1.0.0.sha256
```

### User Downloads (Air-Gap Transfer):

```bash
# Download on internet-connected machine
curl -L https://github.com/subtract0/Agency/releases/download/v1.0.0/agency_offline_v1.0.0.tar.gz -o agency_offline.tar.gz

# Transfer via USB to offline machine
# Extract and install (no internet)
tar -xzf agency_offline.tar.gz
cd agency_offline_v1.0.0
bash install_offline.sh
bash start_night_run.sh --offline
```

---

## Summary

**Offline Mode = Local-Only + Stricter Isolation**

| Capability | Local-Only | **Offline** |
|-----------|-----------|-----------|
| LLM Inference | ✅ Local | ✅ Local |
| Embeddings | ✅ Local (can download) | ✅ **Pre-cached** |
| Python Packages | ✅ pip install works | ✅ **Vendored** |
| Ollama Models | ✅ Can pull updates | ✅ **Locked to cache** |
| Internet Needed | Setup only | ✅ **Never** (after bundle) |
| Air-Gap Compatible | ❌ | ✅ **Yes** |
| Bundle Size | N/A | **21GB** |

**Use Offline Mode When**:
- Air-gap compliance required
- Zero network tolerance
- Field deployment without internet
- Maximum privacy/security needed

---

**Status**: Ready to implement
**Impact**: Enables truly isolated, portable AI deployment
**User Value**: Run Constitutional Consciousness anywhere, even in submarine/bunker/airplane 🚀
