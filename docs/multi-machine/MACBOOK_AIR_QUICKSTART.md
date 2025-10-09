# MacBook Air Quick Start Guide

**5-Minute Setup for 4-Agent Autonomous Coordination**

---

## 🚀 Option 1: Automated Setup (Recommended)

### On MacBook Air:

```bash
# 1. Get the setup script from iCloud
cd ~
bash "/Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared/setup_macbook_air.sh"

# 2. Start agents
cd ~/Code/Agency
./scripts/start_agents_mba.sh

# Done! ✅
```

---

## 🔧 Option 2: Manual Setup

### Step 1: Clone Repository

```bash
# On MacBook Air
cd ~/Code
git clone <repository-url> Agency
cd Agency
```

### Step 2: Copy Config from iCloud

```bash
cp "/Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared/.agency_config.json" .
```

### Step 3: Test Connection

```bash
python -c "from meta_learning.task_queue import TaskQueue; q = TaskQueue(); print('✅ Connected!')"

# Expected output:
# ✅ Using iCloud shared workspace: .../task_queue.json
# ✅ Connected!
```

### Step 4: Start Agents

**Terminal 1:**
```bash
cd ~/Code/Agency
python scripts/autonomous_worker.py --agent-id mba-agent1
```

**Terminal 2:**
```bash
cd ~/Code/Agency
python scripts/autonomous_worker.py --agent-id mba-agent2
```

---

## 📊 Verify 4-Agent Coordination

### On Either Machine:

```bash
cd ~/Code/Agency
python meta_learning/task_queue.py status
```

**Expected output:**
```json
{
  "total": 12,
  "pending": 0,
  "in_progress": 4,  ← All 4 agents working!
  "completed": 8
}
```

---

## 🧪 Test New Task Orchestration

### On M4 Pro:

```bash
# Create new tasks
python scripts/orchestrate_epic4.py --phase medi-pack-v1

# Watch all 4 agents coordinate!
watch -n 5 'python meta_learning/task_queue.py status'
```

**Expected behavior:**
- M4 Pro agents (m4pro-agent1, m4pro-agent2) claim tasks
- MacBook Air agents (mba-agent1, mba-agent2) claim different tasks
- **Zero conflicts!**
- **Perfect load balancing!**
- **Automatic coordination via iCloud!**

---

## 🎯 What You'll See

### On M4 Pro Terminal 1 (m4pro-agent1):
```
🤖 Autonomous Agent Started
Agent ID: m4pro-agent1
...
🎯 Executing: medi-v1-spec-scout-fleet
✅ Task completed!
⏳ Waiting for tasks...
```

### On MacBook Air Terminal 1 (mba-agent1):
```
🤖 Autonomous Agent Started
Agent ID: mba-agent1
...
🎯 Executing: medi-v1-spec-planner-phase
✅ Task completed!
```

### Status Monitor:
```
{
  "total": 10,
  "pending": 4,
  "in_progress": 4,  ← All 4 agents working simultaneously!
  "completed": 2,
  "tasks": [
    {"task_id": "...", "assigned_to": "m4pro-agent1", "status": "in_progress"},
    {"task_id": "...", "assigned_to": "m4pro-agent2", "status": "in_progress"},
    {"task_id": "...", "assigned_to": "mba-agent1", "status": "in_progress"},
    {"task_id": "...", "assigned_to": "mba-agent2", "status": "in_progress"}
  ]
}
```

---

## 🛡️ Troubleshooting

### "iCloud path not accessible"

**Fix:**
1. Check iCloud Drive enabled: System Settings → Apple ID → iCloud
2. Verify sync: Look for cloud icon in menu bar
3. Wait for sync to complete (may take 1-2 minutes)

### "Config file not found"

**Fix:**
```bash
# Check if iCloud has synced from M4 Pro
ls "/Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared/"

# Should see:
# .agency_config.json
# setup_macbook_air.sh
# meta_learning/
```

### "TaskQueue connection failed"

**Fix:**
1. Ensure same Apple ID on both machines
2. Check network connectivity
3. Verify iCloud sync status
4. Try: `python -c "from meta_learning.task_queue import TaskQueue; TaskQueue()"`

---

## ✅ Success Checklist

- [ ] iCloud Drive accessible on MacBook Air
- [ ] Repository cloned or accessible
- [ ] Config file copied
- [ ] TaskQueue test passes
- [ ] 2 agents started on MacBook Air
- [ ] 2 agents running on M4 Pro
- [ ] Status shows 4 agents coordinating
- [ ] No task conflicts observed

---

## 🎉 Next Steps

Once all 4 agents are running:

1. **Orchestrate new tasks** (M4 Pro):
   ```bash
   python scripts/orchestrate_epic4.py --phase medi-pack-v1
   ```

2. **Watch coordination** (Either machine):
   ```bash
   watch -n 2 'python meta_learning/task_queue.py status'
   ```

3. **Celebrate** 🎊
   - 4 agents
   - 2 machines
   - 1 shared queue
   - 0 conflicts
   - **Fully autonomous!**

---

## 📞 Quick Commands

```bash
# Start agents (MacBook Air)
./scripts/start_agents_mba.sh

# Check status (Either machine)
python meta_learning/task_queue.py status

# Orchestrate tasks (M4 Pro)
python scripts/orchestrate_epic4.py --phase epic4.2-complete

# Stop agent (Ctrl+C in terminal)
^C

# Reset stuck task (if needed)
python meta_learning/task_queue.py reset --id <task-id>
```

---

**Files in iCloud Ready for MacBook Air:**
- ✅ `.agency_config.json` - Configuration
- ✅ `setup_macbook_air.sh` - Automated setup script
- ✅ `meta_learning/task_queue.json` - Shared task queue

**Total setup time:** ~5 minutes
**Result:** 4-agent autonomous coordination across 2 machines! 🚀
