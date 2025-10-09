# Multi-Machine Autonomous Agent Setup Guide

**Autonomous coordination across M4 Pro + MacBook Air via iCloud Drive**

---

## ✅ M4 Pro (Primary Machine) - COMPLETE

The M4 Pro is already configured and ready!

**Status:**
- ✅ iCloud shared workspace created
- ✅ TaskQueue auto-configured
- ✅ Configuration file created
- ✅ Ready to run agents

---

## 🔧 MacBook Air Setup (5 Minutes)

### Step 1: Clone the Repository

```bash
# On MacBook Air
cd ~/Code
git clone <repository-url> Agency
cd Agency
```

**Or sync via iCloud:**
```bash
# If you want to share the entire codebase via iCloud
cd "/Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared"
```

### Step 2: Copy Configuration File

**Option A: Via iCloud (Recommended)**
```bash
# The config file is already in iCloud!
cp "/Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared/.agency_config.json" ~/Code/Agency/
```

**Option B: Manual Creation**

Create `~/Code/Agency/.agency_config.json`:

```json
{
  "shared_workspace": {
    "enabled": true,
    "type": "icloud",
    "path": "/Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared",
    "task_queue_file": "/Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared/meta_learning/task_queue.json",
    "sync_status": "active"
  },
  "machines": {
    "m4_pro": {
      "hostname": "M4-Pro.local",
      "agent_ids": ["m4pro-agent1", "m4pro-agent2"],
      "max_workers": 2
    },
    "macbook_air": {
      "hostname": "MacBook-Air.local",
      "agent_ids": ["mba-agent1", "mba-agent2"],
      "max_workers": 2
    }
  },
  "coordination": {
    "poll_interval": 5,
    "lock_timeout": 30,
    "heartbeat_interval": 10
  }
}
```

### Step 3: Verify iCloud Access

```bash
# Check iCloud is accessible
ls -la "/Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared/"

# Should see:
# drwxr-xr-x  meta_learning
```

### Step 4: Test Queue Access

```bash
# On MacBook Air
cd ~/Code/Agency

python -c "from meta_learning.task_queue import TaskQueue; q = TaskQueue(); print('✅ Connected to shared queue!')"

# Should output:
# ✅ Using iCloud shared workspace: /Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared/meta_learning/task_queue.json
# ✅ Connected to shared queue!
```

### Step 5: Start Agents

```bash
# Terminal 1 (MacBook Air)
python scripts/autonomous_worker.py --agent-id mba-agent1

# Terminal 2 (MacBook Air)
python scripts/autonomous_worker.py --agent-id mba-agent2
```

---

## 🚀 Complete 4-Agent Setup

### On M4 Pro

**Terminal 1:**
```bash
cd ~/Code/Agency
python scripts/autonomous_worker.py --agent-id m4pro-agent1
```

**Terminal 2:**
```bash
cd ~/Code/Agency
python scripts/autonomous_worker.py --agent-id m4pro-agent2
```

### On MacBook Air

**Terminal 3:**
```bash
cd ~/Code/Agency
python scripts/autonomous_worker.py --agent-id mba-agent1
```

**Terminal 4:**
```bash
cd ~/Code/Agency
python scripts/autonomous_worker.py --agent-id mba-agent2
```

### Monitor (Either Machine)

```bash
watch -n 5 'python meta_learning/task_queue.py status'
```

---

## 🔍 Verification Checklist

### On M4 Pro:
- [x] iCloud directory created
- [x] Config file exists
- [x] TaskQueue uses iCloud path
- [x] Can run orchestrator
- [x] Can start agents

### On MacBook Air:
- [ ] Repository cloned/synced
- [ ] Config file copied
- [ ] iCloud accessible
- [ ] TaskQueue connects
- [ ] Can start agents

---

## 🛡️ How It Works: Zero-Conflict Coordination

### File Locking (fcntl)
- **Atomic operations** prevent race conditions
- **Shared locks** for reading (multiple readers OK)
- **Exclusive locks** for writing (blocks everyone)
- **Works over iCloud** (macOS kernel handles it)

### Task Claiming Process

```
Agent (M4 Pro):                    Agent (MacBook Air):
     |                                     |
     v                                     v
1. Read queue (fcntl LOCK_SH)      1. Read queue (fcntl LOCK_SH)
2. Find available task             2. Find available task
3. Acquire exclusive lock          3. Try exclusive lock
4. Update task status              4. BLOCKED (M4 has lock)
5. Release lock                    5. Wait...
6. Execute task                    6. Lock available!
     |                             7. Update different task
     v                             8. Execute in parallel!
   Done                                    |
                                          Done
```

### File Conflict Prevention

```python
# M4 Pro agent claims:
Task A: files_to_modify = ["file1.py", "file2.py"]

# MacBook Air agent tries:
Task B: files_to_modify = ["file2.py", "file3.py"]
        # file2.py overlaps!
        # → BLOCKED until Task A completes

Task C: files_to_modify = ["file4.py"]
        # No overlap!
        # → CLAIMED immediately, runs in parallel
```

---

## 📊 Expected Behavior

### Orchestration (M4 Pro)

```bash
python scripts/orchestrate_epic4.py --phase epic4.2-complete

# Output:
# ✅ Task queue populated with 12 tasks
# Dependency Graph:
# PHASE 1: Specifications (Parallel)
#   ├─ epic4.2-spec-proposal-generator
#   ├─ epic4.2-spec-adr-template
#   └─ epic4.2-spec-integration-workflow
# ...
```

### Agent Execution (Both Machines)

**M4 Pro Agent 1:**
```
🤖 Autonomous Agent Started
Agent ID: m4pro-agent1
...
🎯 Executing: epic4.2-spec-proposal-generator
✅ Task completed!
```

**MacBook Air Agent 1:**
```
🤖 Autonomous Agent Started
Agent ID: mba-agent1
...
🎯 Executing: epic4.2-spec-adr-template
   (Different file, runs in parallel!)
✅ Task completed!
```

**M4 Pro Agent 2:**
```
⏳ No tasks available (dependencies not met), waiting...
🎯 Executing: epic4.2-code-proposal-models
   (Dependencies met, continues)
```

---

## 🐛 Troubleshooting

### Issue: "iCloud path not accessible"

**Solution:**
1. Check iCloud Drive is enabled: System Settings → Apple ID → iCloud → iCloud Drive
2. Verify sync status: `ls "/Users/am/Library/Mobile Documents/com~apple~CloudDocs/"`
3. Wait for sync (check status bar for cloud icon)

### Issue: "File locking not working"

**Solution:**
1. Ensure both machines use same iCloud account
2. Check network connectivity (same Wi-Fi)
3. Verify iCloud sync is active (not paused)
4. Try: `sudo fs_usage | grep task_queue.json` to see lock operations

### Issue: "Agents claiming same task"

**Solution:**
- This should NEVER happen with fcntl locks
- If it does, check:
  1. Both agents using same queue file path
  2. iCloud sync is working
  3. File system supports locking (HFS+/APFS do, some network FS don't)

### Issue: "iCloud sync lag"

**Symptoms:** Changes take 5-10 seconds to appear on other machine

**Solution:**
- This is normal for iCloud
- Agents poll every 5 seconds, so they'll see changes
- For faster sync, consider Dropbox or direct NFS mount

---

## 🎯 Alternative Sync Options

### Option B: Dropbox (Faster Sync)

1. Install Dropbox on both machines
2. Create `~/Dropbox/Agency-Shared/`
3. Update `.agency_config.json`:
   ```json
   "path": "/Users/am/Dropbox/Agency-Shared"
   ```

### Option C: Direct Network Share (Fastest)

**M4 Pro (Server):**
```bash
# Enable file sharing in System Settings
# Share ~/Code/Agency as "Agency"
```

**MacBook Air (Client):**
```bash
# Connect to M4 Pro
# Mount share at /Volumes/Agency
# Update config to use /Volumes/Agency path
```

### Option D: Git-Based (Most Robust)

Each agent:
```python
# Before claiming task:
subprocess.run(["git", "pull"])

# After completing task:
subprocess.run(["git", "add", "meta_learning/task_queue.json"])
subprocess.run(["git", "commit", "-m", "Update queue"])
subprocess.run(["git", "push"])
```

---

## ✅ Success Criteria

Your multi-machine setup is working when:

1. ✅ Both machines see same task queue file
2. ✅ Agents on M4 Pro can claim tasks
3. ✅ Agents on MacBook Air can claim tasks
4. ✅ No two agents claim same task
5. ✅ Tasks with dependencies wait correctly
6. ✅ File conflicts are detected
7. ✅ All agents complete work autonomously

---

## 📞 Next Steps

1. **On MacBook Air:**
   - Complete Steps 1-4 above
   - Start 2 agents

2. **On M4 Pro:**
   - Start 2 agents
   - Orchestrate tasks

3. **Monitor:**
   - Watch agents coordinate
   - Verify zero conflicts
   - Celebrate autonomous coordination! 🎉

---

**Status:** M4 Pro READY ✅ | MacBook Air TODO ⏳

Once MacBook Air is set up, you'll have **4 autonomous agents** working across **2 machines** with **perfect coordination**!
