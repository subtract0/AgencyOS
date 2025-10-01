# Trinity Cost Dashboard - Quick Start Card

**🚀 Get Started in 60 Seconds**

---

## 1. Generate Test Data (Optional)

```bash
python trinity_protocol/test_dashboard_demo.py --calls 50
```

---

## 2. Choose Your Dashboard

### 🖥️ Terminal (Live Updates)
```bash
python trinity_protocol/dashboard_cli.py terminal --live
```
**Best for**: SSH sessions, lightweight monitoring

### 🌐 Web (Browser)
```bash
pip install flask  # First time only
python trinity_protocol/dashboard_cli.py web --port 8080
# Open http://localhost:8080
```
**Best for**: Visual monitoring, multiple users

### 🔔 Alerts (Automated)
```bash
python trinity_protocol/dashboard_cli.py alerts --continuous --budget 10.0
```
**Best for**: Background monitoring, budget management

---

## 3. Common Commands

### Quick Snapshot
```bash
python trinity_protocol/dashboard_cli.py snapshot
```

### Export Data
```bash
python trinity_protocol/dashboard_cli.py export
```

### With Budget
```bash
python trinity_protocol/dashboard_cli.py terminal --live --budget 10.0
```

---

## Keyboard Controls (Terminal)

| Key | Action |
|-----|--------|
| `Q` | Quit |
| `E` | Export data |
| `R` | Force refresh |

---

## Configuration

### Database
```bash
--db trinity_costs.db
```

### Budget
```bash
--budget 10.0
```

### Refresh Rate
```bash
--interval 5  # seconds
```

---

## During Trinity Operation

```bash
# Terminal 1: Run Trinity
python trinity_protocol/demo_complete_trinity.py

# Terminal 2: Monitor costs
python trinity_protocol/dashboard_cli.py terminal --live

# Terminal 3 (optional): Web dashboard
python trinity_protocol/dashboard_cli.py web
```

---

## Email Alerts

```bash
python trinity_protocol/dashboard_cli.py alerts \
  --continuous \
  --budget 10.0 \
  --email-enabled \
  --email-smtp-host smtp.gmail.com \
  --email-from alerts@example.com \
  --email-to admin@example.com \
  --email-password "app-password"
```

---

## Slack Alerts

```bash
python trinity_protocol/dashboard_cli.py alerts \
  --continuous \
  --budget 10.0 \
  --slack-enabled \
  --slack-webhook "https://hooks.slack.com/services/XXX"
```

---

## Troubleshooting

### No Data?
```bash
# Verify CostTracker wiring
python trinity_protocol/verify_cost_tracking.py
```

### Web Dashboard Not Loading?
```bash
# Check Flask installed
pip install flask

# Check port available
lsof -i :8080
```

### Terminal Too Small?
Minimum 80x24 required. Resize terminal window.

---

## Full Documentation

📖 **[Complete Guide](docs/COST_DASHBOARD_GUIDE.md)** - Everything you need to know

📊 **[README](DASHBOARD_README.md)** - Quick reference

🎯 **[Trinity Docs](docs/README.md)** - Main documentation

---

## Files

```
trinity_protocol/
├── cost_dashboard.py           # Terminal dashboard
├── cost_dashboard_web.py       # Web dashboard
├── cost_alerts.py              # Alert system
├── dashboard_cli.py            # Unified CLI (START HERE)
├── test_dashboard_demo.py      # Demo/testing
└── docs/
    ├── COST_DASHBOARD_GUIDE.md # Complete guide
    └── README.md               # Trinity docs
```

---

## Next Steps

1. Try demo: `python trinity_protocol/test_dashboard_demo.py --terminal`
2. Read full guide: `docs/COST_DASHBOARD_GUIDE.md`
3. Integrate with Trinity: Pass `cost_tracker` to agents

---

**Need Help?** See `docs/COST_DASHBOARD_GUIDE.md` for complete documentation
