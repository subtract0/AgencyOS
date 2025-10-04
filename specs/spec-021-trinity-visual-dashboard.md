# Specification: Trinity Visual Dashboard - Real-Time Agent Activity Monitor

**Date**: 2025-10-04
**Status**: Draft
**Author**: Digital Muse Team
**Context**: Make Trinity visually engaging for humans observing the M4 MacBook

---

## Goals

1. **Visual Engagement**: Beautiful TUI (Terminal UI) showing what Trinity is doing in real-time
2. **Agent Status**: Live view of WITNESS → ARCHITECT → EXECUTOR flow with progress indicators
3. **Model Activity**: Show which local LLM is currently loaded and generating tokens
4. **Pattern Detection**: Stream detected patterns as they happen
5. **Code Generation**: Live view of code being written, tests running, commits happening

## Non-Goals

- Web-based GUI (terminal-only for simplicity)
- Historical analytics (focus on real-time)
- User interaction (read-only dashboard, `trinity-stop` to control)
- Audio notifications (visual only)

## Personas

### Primary: Human Observer
- **Need**: See what Trinity is doing autonomously without reading logs
- **Context**: M4 MacBook running 24/7 in corner of room
- **Interaction**: Glance at screen to see current activity

### Secondary: Developer Debugging
- **Need**: Understand Trinity's decision-making in real-time
- **Context**: Troubleshooting why Trinity chose certain patterns
- **Interaction**: Watch detailed agent reasoning and model outputs

---

## Architecture

### Tech Stack: Rich TUI (Terminal User Interface)

**Library**: `rich` (Python TUI framework)
- Live updating panels
- Syntax highlighting
- Progress bars
- Tree views
- Tables

**Why Rich over alternatives**:
- Pure Python (already in dependencies)
- Beautiful rendering
- Live refresh support
- No external server needed

---

## Visual Layout

### Full-Screen TUI (3 Zones)

```
┌────────────────────────────────────────────────────────────────┐
│ TRINITY LOCAL M4 - AUTONOMOUS LOOP                      [LIVE] │
│ Memory: 24GB / 34GB  |  Models: 3/3  |  Uptime: 2h 14m        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌──────────────────── AGENT PIPELINE ─────────────────────┐   │
│ │                                                          │   │
│ │  ● WITNESS (qwen2.5-coder:1.5b)          [IDLE]        │   │
│ │    Last: Pattern detected - "Dict[Any] usage spike"     │   │
│ │    Confidence: 0.87  |  Events: 142                     │   │
│ │                                                          │   │
│ │  ⚡ ARCHITECT (qwen2.5-coder:7b)         [GENERATING]   │   │
│ │    ████████████████░░░░░░░░░░  65%                      │   │
│ │    Creating: spec-022-type-safety-enforcement.md        │   │
│ │    Token: 1,247 / 2,000  |  ETA: 42s                    │   │
│ │                                                          │   │
│ │  ○ EXECUTOR (codestral:22b)              [WAITING]      │   │
│ │    Queue: 2 tasks  |  Next: Implement Pydantic models   │   │
│ │                                                          │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌──────────────────── ACTIVITY STREAM ────────────────────┐   │
│ │                                                          │   │
│ │ 14:23:47  [WITNESS]    Pattern detected                 │   │
│ │           📊 Dict[Any] usage in 3 files                  │   │
│ │           → Signaling ARCHITECT                         │   │
│ │                                                          │   │
│ │ 14:23:52  [ARCHITECT]  Loading model...                 │   │
│ │           🧠 qwen2.5-coder:7b (8GB)                     │   │
│ │           → Memory: 8GB → 16GB                          │   │
│ │                                                          │   │
│ │ 14:24:10  [ARCHITECT]  Generating spec...               │   │
│ │           📝 Goals: Enforce type safety                  │   │
│ │           📝 Criteria: Zero Dict[Any] violations         │   │
│ │           → Querying VectorStore for patterns           │   │
│ │                                                          │   │
│ │ 14:24:35  [ARCHITECT]  Spec approved (auto)             │   │
│ │           ✅ spec-022-type-safety-enforcement.md         │   │
│ │           → Creating implementation plan                │   │
│ │                                                          │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌─────────────────── LIVE CODE VIEW ──────────────────────┐   │
│ │                                                          │   │
│ │ File: src/utils.py:42                                    │   │
│ │                                                          │   │
│ │  # BEFORE (VIOLATION)                                    │   │
│ │  def process_data(data: Dict[Any, Any]) -> None:        │   │
│ │      pass                                                │   │
│ │                                                          │   │
│ │  # AFTER (FIXED)                                         │   │
│ │  class DataInput(BaseModel):                             │   │
│ │      field_1: str                                        │   │
│ │      field_2: int                                        │   │
│ │                                                          │   │
│ │  def process_data(data: DataInput) -> None:             │   │
│ │      pass                                                │   │
│ │                                                          │   │
│ │  ✅ Tests: 12/12 passing  |  Mypy: ✓  |  Ruff: ✓        │   │
│ │                                                          │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
  Press Q to quit  |  Press L for full logs  |  Press H for help
```

---

## Dashboard Components

### Zone 1: Agent Pipeline (Top)

**Shows**: Current state of 3-agent Trinity loop

**Elements**:
- **Status Indicators**:
  - `●` Active (green)
  - `⚡` Generating (yellow, animated)
  - `○` Idle (gray)
  - `✓` Complete (green)
  - `✗` Error (red)

- **Progress Bars**:
  - Token generation progress (for ARCHITECT/EXECUTOR)
  - Task execution progress
  - ETA based on past performance

- **Model Info**:
  - Model name + size
  - Memory usage
  - Token count / context length

**Real-Time Updates**: Every 500ms

---

### Zone 2: Activity Stream (Middle)

**Shows**: Live log of Trinity decisions and actions

**Format**:
```
[HH:MM:SS] [AGENT_NAME]  Action description
           📊 Detail line 1
           📝 Detail line 2
           → Next action
```

**Icons**:
- 📊 Pattern detection
- 🧠 Model loading
- 📝 Spec/plan generation
- ✅ Success
- ❌ Error
- 🔄 Retry
- 💾 Memory storage
- 🧪 Test execution
- 📦 Git commit

**Colors**:
- Green: Success actions
- Yellow: In-progress
- Red: Errors
- Blue: Info
- Cyan: VectorStore queries

**Auto-Scroll**: Latest at bottom, max 20 lines visible

---

### Zone 3: Live Code View (Bottom)

**Shows**: Real-time code changes as they happen

**Modes**:
1. **Diff View** (default):
   - Before/After code side-by-side
   - Syntax highlighted (Pygments)
   - Line numbers

2. **Test View** (when tests running):
   - Test output streaming
   - Pass/fail indicators
   - Coverage metrics

3. **Commit View** (when committing):
   - Git diff summary
   - Commit message
   - Files changed count

**Syntax Highlighting**: Python, TypeScript, YAML, Markdown

---

## Implementation Plan

### Component 1: Dashboard Core

**File**: `deploy/trinity-local-m4/dashboard.py`

```python
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
import time
from datetime import datetime

class TrinityDashboard:
    """Real-time Trinity activity dashboard."""

    def __init__(self, trinity_dir: str = "~/.trinity-local"):
        self.trinity_dir = trinity_dir
        self.console = Console()
        self.layout = Layout()

        # Setup 3-zone layout
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="pipeline", size=12),
            Layout(name="activity", size=15),
            Layout(name="code", size=18),
            Layout(name="footer", size=1)
        )

    def render_header(self) -> Panel:
        """Top status bar."""
        memory_used = self.get_memory_usage()
        uptime = self.get_uptime()
        models_loaded = self.get_models_status()

        header = Text()
        header.append("TRINITY LOCAL M4 - AUTONOMOUS LOOP", style="bold cyan")
        header.append("  [LIVE]", style="bold green blink")
        header.append(f"\nMemory: {memory_used}GB / 34GB  |  ", style="white")
        header.append(f"Models: {models_loaded}  |  ", style="white")
        header.append(f"Uptime: {uptime}", style="white")

        return Panel(header, border_style="cyan")

    def render_pipeline(self) -> Panel:
        """Agent pipeline status."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Status", width=3)
        table.add_column("Agent", width=50)

        # WITNESS
        witness_status = self.get_agent_status("witness")
        witness_icon = self.get_status_icon(witness_status)
        witness_info = (
            f"WITNESS (qwen2.5-coder:1.5b)          [{witness_status}]\n"
            f"Last: {self.get_last_action('witness')}\n"
            f"Confidence: {self.get_confidence('witness')}  |  Events: {self.get_event_count('witness')}"
        )
        table.add_row(witness_icon, witness_info)

        # ARCHITECT
        architect_status = self.get_agent_status("architect")
        architect_icon = self.get_status_icon(architect_status)
        architect_info = self.render_architect_status()
        table.add_row(architect_icon, architect_info)

        # EXECUTOR
        executor_status = self.get_agent_status("executor")
        executor_icon = self.get_status_icon(executor_status)
        executor_info = self.render_executor_status()
        table.add_row(executor_icon, executor_info)

        return Panel(table, title="AGENT PIPELINE", border_style="yellow")

    def render_architect_status(self) -> str:
        """ARCHITECT with progress bar if generating."""
        status = self.get_agent_status("architect")
        if status == "GENERATING":
            progress = self.get_generation_progress("architect")
            tokens = self.get_token_count("architect")
            eta = self.estimate_eta("architect")
            return (
                f"ARCHITECT (qwen2.5-coder:7b)         [{status}]\n"
                f"{'█' * int(progress * 30)}{'░' * (30 - int(progress * 30))}  {progress * 100:.0f}%\n"
                f"Creating: {self.get_current_task('architect')}\n"
                f"Token: {tokens[0]} / {tokens[1]}  |  ETA: {eta}s"
            )
        else:
            return f"ARCHITECT (qwen2.5-coder:7b)         [{status}]"

    def render_activity_stream(self) -> Panel:
        """Scrolling activity log."""
        activities = self.get_recent_activities(limit=15)

        text = Text()
        for activity in activities:
            timestamp = activity["timestamp"]
            agent = activity["agent"]
            action = activity["action"]
            details = activity.get("details", [])

            # Main line
            text.append(f"{timestamp}  ", style="dim")
            text.append(f"[{agent}]", style=self.get_agent_color(agent))
            text.append(f"  {action}\n", style="white")

            # Detail lines
            for detail in details:
                icon = detail.get("icon", "→")
                msg = detail["message"]
                text.append(f"           {icon} {msg}\n", style="cyan")

        return Panel(text, title="ACTIVITY STREAM", border_style="blue")

    def render_code_view(self) -> Panel:
        """Live code diff or test output."""
        mode = self.get_code_view_mode()

        if mode == "diff":
            return self.render_diff_view()
        elif mode == "test":
            return self.render_test_view()
        elif mode == "commit":
            return self.render_commit_view()

    def render_diff_view(self) -> Panel:
        """Before/After code comparison."""
        file_path = self.get_current_file()
        before_code = self.get_code_before()
        after_code = self.get_code_after()

        # Syntax highlighted diff
        syntax_before = Syntax(before_code, "python", theme="monokai", line_numbers=True)
        syntax_after = Syntax(after_code, "python", theme="monokai", line_numbers=True)

        diff_text = Text()
        diff_text.append(f"File: {file_path}\n\n", style="bold cyan")
        diff_text.append("# BEFORE (VIOLATION)\n", style="red")
        # ... render before/after with syntax highlighting

        return Panel(diff_text, title="LIVE CODE VIEW", border_style="green")

    def render_footer(self) -> Panel:
        """Help text."""
        footer = Text("Press Q to quit  |  Press L for full logs  |  Press H for help", style="dim")
        return Panel(footer, border_style="dim")

    def run(self):
        """Main dashboard loop."""
        with Live(self.layout, console=self.console, refresh_per_second=2) as live:
            while True:
                # Update all zones
                self.layout["header"].update(self.render_header())
                self.layout["pipeline"].update(self.render_pipeline())
                self.layout["activity"].update(self.render_activity_stream())
                self.layout["code"].update(self.render_code_view())
                self.layout["footer"].update(self.render_footer())

                time.sleep(0.5)  # 500ms refresh

if __name__ == "__main__":
    dashboard = TrinityDashboard()
    dashboard.run()
```

---

### Component 2: Data Sources

**Trinity needs to emit structured events for the dashboard to consume**

**File**: `trinity_protocol/core/events.py`

```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class AgentStatus(str, Enum):
    IDLE = "IDLE"
    LOADING = "LOADING"
    GENERATING = "GENERATING"
    EXECUTING = "EXECUTING"
    WAITING = "WAITING"
    ERROR = "ERROR"

class TrinityEvent(BaseModel):
    """Event emitted by Trinity agents."""
    timestamp: datetime
    agent: str  # "witness", "architect", "executor"
    event_type: str  # "pattern_detected", "model_loaded", "spec_created", etc.
    status: AgentStatus
    data: dict

    def to_dashboard_format(self) -> dict:
        """Convert to dashboard-readable format."""
        return {
            "timestamp": self.timestamp.strftime("%H:%M:%S"),
            "agent": self.agent.upper(),
            "action": self.event_type.replace("_", " ").title(),
            "details": self._extract_details()
        }

# Event emitter
class EventEmitter:
    """Emit Trinity events to dashboard."""

    def __init__(self, events_file: str = "~/.trinity-local/events.jsonl"):
        self.events_file = events_file

    def emit(self, event: TrinityEvent):
        """Write event to JSONL file for dashboard consumption."""
        with open(self.events_file, 'a') as f:
            f.write(event.json() + "\n")
```

**Trinity agents emit events**:
```python
# In trinity_protocol/core/witness.py
emitter = EventEmitter()

# When pattern detected
emitter.emit(TrinityEvent(
    timestamp=datetime.now(),
    agent="witness",
    event_type="pattern_detected",
    status=AgentStatus.IDLE,
    data={
        "pattern": "Dict[Any] usage spike",
        "confidence": 0.87,
        "file_count": 3
    }
))
```

---

### Component 3: Launcher Integration

**Update `start_trinity.sh`** to launch dashboard alongside Trinity:

```bash
#!/bin/bash
# Start Trinity with visual dashboard

# Start Trinity loop in background
python -m trinity_protocol.core.orchestrator --config trinity_config.yaml &
TRINITY_PID=$!

# Wait for Trinity to initialize
sleep 3

# Launch dashboard in foreground (user sees this)
python deploy/trinity-local-m4/dashboard.py

# Cleanup on exit
kill $TRINITY_PID
```

---

## Acceptance Criteria

### AC-1: Real-Time Agent Status
- **Given**: Trinity running with all 3 agents
- **When**: User views dashboard
- **Then**:
  - Agent pipeline shows correct status (IDLE/GENERATING/WAITING)
  - Status updates within 1 second of actual change
  - Progress bars animate smoothly during generation

### AC-2: Activity Stream Readability
- **Given**: Trinity processing patterns and generating code
- **When**: User watches activity stream
- **Then**:
  - Events appear in chronological order (newest at bottom)
  - Icons and colors make events scannable
  - Details are concise (1-3 lines per event)
  - Auto-scrolls without user intervention

### AC-3: Live Code Diff
- **Given**: EXECUTOR writing code changes
- **When**: Dashboard shows live code view
- **Then**:
  - Before/After diff is syntax highlighted
  - File path clearly shown
  - Test results update when tests run
  - Git commit info shows when committing

### AC-4: Performance
- **Given**: Dashboard running 24/7
- **When**: Monitoring resource usage
- **Then**:
  - Dashboard uses <100MB RAM
  - CPU usage <5% (not blocking Trinity)
  - Refresh rate maintains 2 FPS
  - No memory leaks over 24 hours

---

## Visual Enhancements

### Animations

1. **Loading Spinner** (when model loading):
   ```
   ⠋ Loading qwen2.5-coder:7b...
   ⠙ Loading qwen2.5-coder:7b...
   ⠹ Loading qwen2.5-coder:7b...
   ```

2. **Progress Bar** (when generating):
   ```
   ████████████████░░░░░░░░░░  65%
   ```

3. **Blinking "LIVE" Indicator**:
   ```
   [LIVE]  ← Blinks green
   ```

### Color Scheme

- **Cyan**: Headers, agent names
- **Green**: Success, active agents
- **Yellow**: In-progress, warnings
- **Red**: Errors
- **Blue**: Info, metadata
- **White**: Default text
- **Dim**: Timestamps, footer

---

## User Controls

**Keyboard Shortcuts**:
- `Q`: Quit dashboard (Trinity keeps running)
- `L`: Open full logs in `less`
- `H`: Help overlay
- `P`: Pause auto-scroll (activity stream)
- `R`: Resume auto-scroll
- `C`: Clear activity stream

---

## Future Enhancements

### Phase 2: Interactive Mode
- Click on agent to see detailed logs
- Pause/resume Trinity from dashboard
- Manual trigger for specific patterns

### Phase 3: Multi-Session View
- Show multiple Trinity instances (if running on cluster)
- Aggregate metrics across sessions

### Phase 4: Web Dashboard
- Convert TUI to web UI (FastAPI + WebSockets)
- Accessible from any device on network
- Historical graphs and analytics

---

**Status**: Draft
**Next Step**: Build dashboard.py with Rich TUI framework
**Dependencies**: `rich>=13.0.0`, `pygments>=2.0.0` (already in requirements)

---

**This gives the human observer a beautiful, information-dense view of Trinity's autonomous work - like watching a talented developer code in real-time, but it's 3 AI agents orchestrating together.**
