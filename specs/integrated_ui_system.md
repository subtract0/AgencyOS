# Integrated UI System - Apple-Inspired Design

**Version**: 1.0.0
**Created**: October 1, 2025
**Status**: SPECIFICATION
**Priority**: HIGH

---

## Vision

Create a **fully integrated user interface** for Agency OS that combines the best of:
- **Text-based interfaces** (terminal efficiency, keyboard-driven)
- **Visual interfaces** (charts, graphs, real-time updates)
- **Interactive elements** (click, drag, gestures)
- **Apple design philosophy** (simplicity, beauty, functionality)

**Not just text, not just GUI, but seamlessly integrated** - like Apple's ecosystem where everything works together naturally.

---

## Goals

1. **Unified Experience**: Single interface that adapts to context (development, monitoring, planning)
2. **Real-time Updates**: Live cost tracking, agent status, task progress, system metrics
3. **Keyboard-First**: Power users can do everything without mouse
4. **Visual Enhancement**: Charts and visualizations where they add value
5. **Cross-Platform**: macOS, Linux, Windows (with progressive enhancement)
6. **Agent Integration**: All 10 agents visible and controllable from UI
7. **Cost Transparency**: Always-visible cost tracking with budget awareness

---

## Non-Goals

- Web-only interface (must work in terminal + browser)
- Complex 3D visualizations (keep it clean and fast)
- Mobile-first design (desktop/laptop is primary target)
- Social features (this is a developer tool)

---

## Design Principles (Apple-Inspired)

### 1. **Simplicity**
- Hide complexity, reveal progressively
- Default to essential information only
- Advanced features accessible but not prominent

### 2. **Clarity**
- Typography matters (use SF Mono, Inter, or similar)
- Color with purpose (not decoration)
- Information hierarchy clear at a glance

### 3. **Consistency**
- Same patterns everywhere
- Predictable interactions
- Unified visual language

### 4. **Feedback**
- Immediate response to actions
- Progress indicators for long operations
- Success/error states visually distinct

### 5. **Beauty**
- Attention to detail
- Smooth animations (60fps)
- Delightful micro-interactions

---

## User Personas

### 1. **The Developer** (Primary)
- Working on code in one window
- Wants quick glance at agent status, costs, test results
- Keyboard-driven workflow
- Needs: Split-screen support, hotkeys, minimal context switching

### 2. **The Architect** (Secondary)
- Planning system design
- Needs overview of agent activities
- Reviews ADRs, specs, plans
- Needs: Big picture view, relationship diagrams, timeline

### 3. **The Monitor** (Tertiary)
- Watching autonomous operation
- Concerned about costs, errors, performance
- May not be coding actively
- Needs: Dashboard view, alerts, real-time metrics

---

## Acceptance Criteria

### Must Have (P0)
- [ ] Single command to launch integrated UI
- [ ] Terminal mode with rich TUI (curses/textual)
- [ ] Web mode with real-time updates (WebSocket/SSE)
- [ ] Cost tracking visible in both modes
- [ ] Agent status visible (what each agent is doing)
- [ ] Task list visible (current TodoWrite tasks)
- [ ] Keyboard shortcuts for common actions
- [ ] Works on macOS, Linux, Windows

### Should Have (P1)
- [ ] Chart.js or similar for cost trends
- [ ] Agent activity timeline (last 1 hour)
- [ ] File tree view with git status
- [ ] Quick access to recent logs
- [ ] Settings panel for configuration
- [ ] Dark/light mode toggle
- [ ] Responsive layout (window resize)

### Nice to Have (P2)
- [ ] Vim-style keyboard navigation
- [ ] Customizable dashboard layout
- [ ] Notification system (desktop alerts)
- [ ] Command palette (Cmd+K style)
- [ ] Export reports (PDF/HTML)
- [ ] Integration with system notification center

---

## Technical Architecture

### Option A: Textual + FastAPI (Recommended)

**Terminal Mode**:
```python
from textual.app import App
from textual.widgets import Header, Footer, DataTable, Sparkline

class AgencyUI(App):
    """Apple-inspired TUI for Agency OS."""

    def compose(self):
        yield Header()
        yield CostTracker()  # Live cost updates
        yield AgentStatus()  # 10 agents, current activities
        yield TaskList()     # TodoWrite integration
        yield SystemMetrics() # CPU, memory, disk
        yield Footer()
```

**Web Mode**:
```python
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Stream updates to browser
    await websocket.accept()
    while True:
        updates = get_agency_updates()
        await websocket.send_json(updates)
```

**Shared State**:
- SQLite for persistence (existing trinity_*.db)
- Redis for real-time updates (optional)
- Shared Python API for both interfaces

### Option B: Electron + Python Backend

**Benefits**:
- Native desktop app feel
- Better performance for complex UIs
- System tray integration
- Native notifications

**Drawbacks**:
- Larger bundle size
- More complex deployment
- Node.js dependency

**Recommendation**: Start with Option A, migrate to B if needed.

---

## UI Components

### 1. **Global Header**
```
┌─────────────────────────────────────────────────────────────────────┐
│ Agency OS │ 🟢 Running │ $2.34/$5.00 (47%) │ 3h 24m remaining │ ⚙️  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. **Agent Status Grid** (3x4 for 10 agents + 2 system)
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 🤖 Coder     │ 📋 Planner   │ 🧪 TestGen   │ 🛡️ Quality   │
│ ⚡ Writing... │ 💤 Idle      │ 🔄 Testing...│ ✅ Verified  │
│ $0.23        │ $0.00        │ $0.15        │ $0.08        │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 🔍 Auditor   │ 🔀 Merger    │ 📝 Summary   │ 🔨 Toolsmith │
│ 🔄 Analyzing │ ⏸️ Waiting   │ 💤 Idle      │ 💤 Idle      │
│ $0.12        │ $0.00        │ $0.00        │ $0.00        │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 📚 Learning  │ 🏗️ Architect │ 🤖 WITNESS   │ 🧠 ARCHITECT │
│ 💤 Idle      │ 💤 Idle      │ 👀 Watching  │ 🤔 Planning  │
│ $0.00        │ $0.00        │ $0.00 (local)│ $0.18        │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### 3. **Task List** (TodoWrite integration)
```
┌─ Current Tasks ────────────────────────────────────────────────┐
│ ⏳ [1/5] Wire EXECUTOR to real sub-agents                      │
│ ✅ [2/5] Enable real test verification                         │
│ ✅ [3/5] Clean up Dict[Any, Any] violations                    │
│ ⏳ [4/5] Integrate CostTracker                                 │
│ ⏸️ [5/5] Run 24-hour autonomous test                           │
└────────────────────────────────────────────────────────────────┘
```

### 4. **Cost Tracker** (Sparkline + numbers)
```
┌─ Cost Tracking ────────────────────────────────────────────────┐
│                                                                 │
│  Hourly Rate: $0.42/hr     ▁▂▃▄▅▆█▆▅▄▃▂▁▂▃▄▅                   │
│  Total Spent: $2.34        Budget: $5.00 (47% used)            │
│  Remaining:   $2.66        Est. Runtime: 3h 24m                │
│                                                                 │
│  Top Spenders: Coder ($0.45) • TestGen ($0.38) • Auditor ($..) │
└────────────────────────────────────────────────────────────────┘
```

### 5. **System Metrics**
```
┌─ System ───────────────────────────────────────────────────────┐
│ CPU:  ████████░░░░░░░░░░ 42%    Memory: ██████░░░░░░░░░░ 31%  │
│ Disk: ████░░░░░░░░░░░░░░ 23%    Queue:  ██░░░░░░░░░░░░░░  8   │
└────────────────────────────────────────────────────────────────┘
```

### 6. **Recent Activity Log** (scrollable)
```
┌─ Activity Log ─────────────────────────────────────────────────┐
│ 03:15:23 │ Coder       │ ✅ Completed test_user_auth.py        │
│ 03:15:20 │ TestGen     │ ⚡ Generated 12 test cases            │
│ 03:15:18 │ Quality     │ ✅ Verified constitutional compliance │
│ 03:15:12 │ Auditor     │ 📊 Q(T) score: 0.87 (GOOD)           │
│ 03:15:08 │ ARCHITECT   │ 📋 Created task graph (3 tasks)      │
│ 03:15:02 │ WITNESS     │ 👀 Detected: feature_request         │
└────────────────────────────────────────────────────────────────┘
```

### 7. **Footer** (context-sensitive help)
```
┌─────────────────────────────────────────────────────────────────┐
│ [q]uit │ [p]ause │ [r]esume │ [c]osts │ [a]gents │ [?]help     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Color Palette (Apple-Inspired)

### Light Mode
- Background: #FFFFFF (white)
- Text: #1D1D1F (near black)
- Accent: #007AFF (blue)
- Success: #34C759 (green)
- Warning: #FF9500 (orange)
- Error: #FF3B30 (red)
- Secondary: #8E8E93 (gray)

### Dark Mode
- Background: #000000 (true black)
- Text: #F5F5F7 (off-white)
- Accent: #0A84FF (bright blue)
- Success: #30D158 (bright green)
- Warning: #FF9F0A (bright orange)
- Error: #FF453A (bright red)
- Secondary: #98989D (light gray)

---

## Typography

### Terminal
- Monospace: SF Mono, Fira Code, JetBrains Mono
- Size: 12-14pt
- Line height: 1.4

### Web
- Headings: SF Pro Display, -apple-system
- Body: SF Pro Text, -apple-system
- Code: SF Mono, Monaco, Consolas

---

## Animations

### Principles
- Duration: 200-300ms for most transitions
- Easing: ease-in-out or cubic-bezier(0.4, 0.0, 0.2, 1)
- Avoid animation for critical data (costs, errors)
- Use motion to guide attention

### Examples
- Agent status change: Fade in/out (200ms)
- Cost counter: Count-up animation (500ms)
- Task completion: Slide + fade (300ms)
- Error appearance: Shake + fade in (250ms)

---

## Keyboard Shortcuts

### Global
- `Cmd/Ctrl + Q`: Quit
- `Cmd/Ctrl + ,`: Settings
- `Cmd/Ctrl + K`: Command palette
- `Cmd/Ctrl + R`: Refresh
- `Cmd/Ctrl + D`: Toggle dark mode

### Navigation
- `Tab`: Next section
- `Shift + Tab`: Previous section
- `↑↓`: Scroll in active section
- `1-9`: Jump to specific agent

### Actions
- `P`: Pause autonomous operation
- `R`: Resume autonomous operation
- `C`: Show cost details
- `A`: Show agent details
- `T`: Show task list
- `L`: Show logs
- `?`: Help

---

## Implementation Plan

### Phase 1: Core TUI (Week 1)
1. Install Textual framework
2. Create basic layout (header, 3 sections, footer)
3. Integrate CostTracker data
4. Show agent status from shared memory
5. Display TodoWrite tasks
6. Test on macOS, Linux, Windows

### Phase 2: Rich Features (Week 2)
1. Add sparklines for cost trends
2. Implement activity log with colors
3. Add keyboard shortcuts
4. Create settings panel
5. Add dark/light mode toggle
6. Polish animations and transitions

### Phase 3: Web Interface (Week 3)
1. Create FastAPI backend
2. Build HTML/CSS/JS frontend
3. Implement WebSocket updates
4. Add Chart.js visualizations
5. Make responsive layout
6. Deploy alongside terminal version

### Phase 4: Advanced Features (Week 4)
1. Command palette (fuzzy search)
2. Export reports functionality
3. Desktop notifications
4. Vim-style navigation
5. Customizable layouts
6. Integration with system tray

---

## Success Metrics

### User Experience
- [ ] Launch time <2 seconds
- [ ] UI responds in <100ms to input
- [ ] Zero UI freezes during agent operations
- [ ] 60fps animations in web mode
- [ ] Works flawlessly on all 3 platforms

### Functionality
- [ ] All agent statuses accurate
- [ ] Cost tracking matches dashboard
- [ ] Task list syncs with TodoWrite
- [ ] Keyboard shortcuts 100% working
- [ ] No data loss on restart

### Adoption
- [ ] 80%+ of users prefer integrated UI over separate tools
- [ ] <5 minutes to learn basics
- [ ] <1 hour to master keyboard shortcuts
- [ ] Positive feedback on aesthetics

---

## References

- Apple Human Interface Guidelines
- Textual Documentation: https://textual.textualize.io/
- Chart.js: https://www.chartjs.org/
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/

---

## Notes

This specification draws inspiration from:
- Apple's design philosophy (simplicity, beauty, function)
- Terminal multiplexers (tmux, screen)
- Modern dashboards (Grafana, K9s, lazygit)
- Developer tools (VS Code, Cursor, Warp)

The goal is **not to copy** but to **learn from the best** and create something uniquely suited for Agency OS.

---

**Status**: READY FOR IMPLEMENTATION
**Next Step**: Enhance agent with UI development capabilities
**Assigned To**: ToolsmithAgent + AgencyCodeAgent (TDD pair)
