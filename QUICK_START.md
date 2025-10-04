# 🚀 Constitutional Consciousness - 5-Minute Setup

**For**: MacBook Pro M4 (48GB RAM)
**Goal**: Run Constitutional Consciousness overnight with zero manual work
**Difficulty**: ⭐ Beginner-friendly

---

## Step 1: Download Release

### Option A: Online Mode (Requires Internet for Setup)

Open **Terminal** on your MacBook Pro and run:

```bash
cd ~/Downloads
curl -L https://github.com/subtract0/Agency/archive/refs/tags/v1.0.0.tar.gz -o agency-1.0.0.tar.gz
tar -xzf agency-1.0.0.tar.gz
cd Agency-1.0.0
```

**What this does**: Downloads Agency v1.0.0 and extracts it

### Option B: Offline Mode (No Internet After Setup)

For air-gapped/high-security deployments:

```bash
# Download offline bundle (21GB, includes all models)
curl -L https://github.com/subtract0/Agency/releases/download/v1.0.0/agency_offline_v1.0.0.tar.gz -o agency_offline.tar.gz

# Transfer to offline machine via USB (if needed)
# Then extract:
tar -xzf agency_offline.tar.gz
cd agency_offline_v1.0.0
```

**What this does**: Downloads pre-packaged bundle with all models and dependencies

---

## Step 2: Run Automatic Setup

### Online Mode Setup:

Copy and paste this **ONE command**:

```bash
bash setup_consciousness.sh
```

**What this does** (automatically):
- ✅ Installs Ollama (AI model engine)
- ✅ Downloads 3 AI models (Codestral, Qwen2.5-Coder)
- ✅ Installs Python dependencies
- ✅ Configures everything for local-only mode
- ✅ Tests that everything works

**Time**: ~15 minutes (downloads ~20GB of models)

### Offline Mode Setup:

For offline bundle (no internet needed):

```bash
bash install_offline.sh
```

**What this does**:
- ✅ Installs Python dependencies from `.vendor/` (no PyPI)
- ✅ Copies Ollama models from bundle (no downloads)
- ✅ Configures offline mode
- ✅ **No internet required**

**Time**: ~5 minutes (everything pre-packaged)

---

## Step 3: Start Night Run

When setup is done, run:

### Online/Local-Only Mode:
```bash
bash start_night_run.sh
```

### Offline Mode (Stricter - No Network):
```bash
bash start_night_run.sh --offline
```

**What happens**:
- 🌙 Constitutional Consciousness runs every hour
- 🧠 Analyzes code violations and learns patterns
- 🔮 Predicts future issues
- 🧬 Suggests agent improvements
- 📊 Saves reports to `reports/` folder

**Cost**: $0 (100% local, no API calls)
**Offline Mode**: Works even without WiFi/internet connection

---

## Step 4: Check Results (Tomorrow Morning)

```bash
cat reports/latest.txt
```

**You'll see**:
- How many violations were found
- What patterns were detected
- Predictions for next week
- Agent improvement suggestions

---

## 🛑 Stop Night Run

Press `Ctrl+C` or run:

```bash
bash stop_night_run.sh
```

---

## 🆘 Troubleshooting

### "Command not found: bash"
You're in the wrong folder. Run:
```bash
cd ~/Downloads/Agency-1.0.0
```

### "Setup failed"
Check if you have ~25GB free space:
```bash
df -h ~
```

### "Models not downloading"
Check internet connection, then retry:
```bash
bash setup_consciousness.sh
```

---

## 📊 What You Get

After one night (~8 hours):
- ✅ 12 analysis cycles completed
- ✅ Violation patterns identified
- ✅ Predictions for next 7 days
- ✅ Agent evolution proposals
- ✅ Full reports in `reports/` folder

**All running locally on your MacBook Pro. No cloud. No costs.**

---

## 🎯 Next Steps

1. Review reports: `cat reports/latest.txt`
2. See detailed logs: `ls -lh logs/`
3. Check evolution proposals: `cat reports/evolution_proposals.txt`

---

**That's it! 3 commands, 15 minutes setup, autonomous operation overnight.**

*Constitutional Consciousness v1.0.0 - Making AI self-improvement accessible*
