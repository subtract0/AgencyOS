#!/usr/bin/env python3
"""
Trinity Local M4 - Visual Dashboard
Real-time TUI for monitoring autonomous 3-LLM loop
"""

import json
import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class DashboardState:
    def __init__(self, trinity_dir: str = "~/.trinity-local"):
        self.trinity_dir = Path(trinity_dir).expanduser()
        self.events_file = self.trinity_dir / "events.jsonl"
        self.logs_dir = self.trinity_dir / "logs" / "trinity_local"
        self.pid_file = self.trinity_dir / "trinity.pid"

        # State tracking
        self.activities = deque(maxlen=15)
        self.agent_states = {
            "witness": {"status": "idle", "last_action": "Initializing...", "confidence": 0.0, "events": 0},
            "architect": {"status": "idle", "last_action": "Idle - waiting for patterns", "events": 0},
            "executor": {"status": "idle", "last_action": "Queue: 0 tasks", "next_task": None, "events": 0}
        }

        # Fun facts rotation
        self.show_fun_facts = True
        self.show_learning_log = True
        self.fun_fact_index = 0
        self.last_fact_rotate = time.time()
        self.fun_facts = [
            "🧠 WITNESS analyzes patterns at 2048 token context",
            "🏗️  ARCHITECT plans strategies with 4096 token context",
            "⚡ EXECUTOR generates code at 8192 token context",
            "💾 Total memory budget: 34GB (~70% of 48GB RAM)",
            "🔄 Sequential loading: Models load one at a time",
            "🎯 100% offline operation after initial setup",
            "📊 Article IV: Continuous learning from all sessions",
            "⚖️  Constitutional governance: 5 unbreakable articles",
            "🚀 Zero external API calls during execution",
            "🧪 TDD-first: Tests written before implementation",
            "🔒 Article III: Automated merge enforcement",
            "📈 Article II: 100% verification and stability",
            "🎓 VectorStore: Cross-session institutional memory",
            "🛡️  Quality enforcement with autonomous healing",
            "⚡ M4 Pro optimized: Metal acceleration enabled"
        ]

        # Start time
        self.start_time = datetime.now()

    def rotate_fun_fact(self):
        """Rotate fun fact every 10 seconds"""
        now = time.time()
        if now - self.last_fact_rotate >= 10:
            self.fun_fact_index = (self.fun_fact_index + 1) % len(self.fun_facts)
            self.last_fact_rotate = now

    def get_current_fun_fact(self) -> str:
        return self.fun_facts[self.fun_fact_index]

    def is_running(self) -> bool:
        """Check if Trinity is running"""
        if not self.pid_file.exists():
            return False
        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, 0)  # Check if process exists
            return True
        except (ValueError, ProcessLookupError):
            return False

    def get_uptime(self) -> str:
        """Get Trinity uptime"""
        if not self.is_running():
            return "Not running"
        delta = datetime.now() - self.start_time
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def get_memory_usage(self) -> str:
        """Estimate current memory usage"""
        if not self.is_running():
            return "0 MB"

        # Rough estimate based on active agents
        base_memory = 2000  # Base Python/Trinity overhead
        active_models = sum(1 for agent in self.agent_states.values() if agent["status"] != "idle")

        model_memory = {
            0: 0,
            1: 2000,   # 1 model loaded (~2GB)
            2: 7000,   # 2 models loaded (~7GB)
            3: 15000   # All 3 loaded (~15GB)
        }

        total_mb = base_memory + model_memory.get(active_models, 0)
        return f"{total_mb} MB"


class TrinityDashboard:
    def __init__(self, state: DashboardState):
        self.state = state

    def render_header(self) -> Panel:
        """Render header with status"""
        status = "🟢 LIVE" if self.state.is_running() else "🔴 STOPPED"
        uptime = self.state.get_uptime()
        memory = self.state.get_memory_usage()

        header_text = Text()
        header_text.append("TRINITY LOCAL M4 - AUTONOMOUS LOOP  ", style="bold cyan")
        header_text.append(f"[{status}]", style="bold green" if self.state.is_running() else "bold red")
        header_text.append(f"\n⏱️  Uptime: {uptime}  |  ", style="white")
        header_text.append(f"💾 Memory: {memory}  |  ", style="white")
        header_text.append("🔧 Models: 3/3", style="white")

        return Panel(header_text, box=box.DOUBLE, border_style="cyan")

    def render_pipeline(self) -> Panel:
        """Render agent pipeline status"""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Agent", style="cyan", width=30)
        table.add_column("Status", width=80)

        # WITNESS
        witness = self.state.agent_states["witness"]
        status_icon = "⚙️" if witness["status"] == "active" else "○"
        witness_text = f"{status_icon}  WITNESS (qwen2.5-coder:1.5b)"
        witness_status = f"[{'green' if witness['status'] == 'active' else 'dim'}]{witness['last_action']}[/]\n"
        witness_status += f"Confidence: {witness['confidence']:.2f}  |  Events: {witness['events']}"
        table.add_row(witness_text, witness_status)

        # ARCHITECT
        architect = self.state.agent_states["architect"]
        status_icon = "⚙️" if architect["status"] == "active" else "○"
        architect_text = f"{status_icon}  ARCHITECT (qwen2.5-coder:7b)"
        architect_status = f"[{'green' if architect['status'] == 'active' else 'dim'}]{architect['last_action']}[/]\n"
        architect_status += f"Events: {architect['events']}"
        table.add_row(architect_text, architect_status)

        # EXECUTOR
        executor = self.state.agent_states["executor"]
        status_icon = "⚙️" if executor["status"] == "active" else "○"
        executor_text = f"{status_icon}  EXECUTOR (codestral:22b)"
        executor_status = f"[{'green' if executor['status'] == 'active' else 'dim'}]{executor['last_action']}[/]\n"
        next_task = executor.get("next_task", "None")
        executor_status += f"Next: {next_task}"
        table.add_row(executor_text, executor_status)

        return Panel(table, title="AGENT PIPELINE", border_style="yellow", box=box.ROUNDED)

    def render_fun_facts(self) -> Panel:
        """Render rotating fun facts"""
        if not self.state.show_fun_facts:
            return Panel("", title="fun_facts (hidden - press F)", border_style="dim", box=box.ROUNDED, height=8)

        self.state.rotate_fun_fact()
        fact = self.state.get_current_fun_fact()

        content = Text(fact, style="italic yellow", justify="center")
        return Panel(content, title="fun_facts", border_style="blue", box=box.ROUNDED, height=8)

    def render_learning_log(self) -> Panel:
        """Render latest learning patterns"""
        if not self.state.show_learning_log:
            return Panel("", title="learning_log (hidden - press J)", border_style="dim", box=box.ROUNDED, height=8)

        # Read latest learning entries
        learning_entries = []
        sessions_dir = self.state.logs_dir.parent.parent / "logs" / "sessions"
        if sessions_dir.exists():
            session_files = sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            for file in session_files[:3]:
                try:
                    data = json.loads(file.read_text())
                    if "patterns" in data:
                        for pattern in data["patterns"][:2]:
                            learning_entries.append(f"• {pattern.get('description', 'Pattern detected')}")
                except Exception:
                    pass

        if not learning_entries:
            learning_entries = ["(no patterns learned yet - waiting for Trinity activity)"]

        content = "\n".join(learning_entries[:5])
        return Panel(content, title="learning_log", border_style="magenta", box=box.ROUNDED, height=8)

    def render_activity(self) -> Panel:
        """Render recent activity stream"""
        if not self.state.activities:
            content = "[dim](waiting for Trinity activity...)[/]"
        else:
            lines = []
            for activity in self.state.activities:
                timestamp = activity.get("timestamp", "")
                agent = activity.get("agent", "system")
                message = activity.get("message", "")
                lines.append(f"[dim]{timestamp}[/] [{agent}] {message}")
            content = "\n".join(lines)

        return Panel(content, title="activity", border_style="green", box=box.ROUNDED, height=15)

    def render_help(self) -> Text:
        """Render help footer"""
        help_text = Text()
        help_text.append("Controls: ", style="bold white")
        help_text.append("Q", style="bold cyan")
        help_text.append("=Quit  ", style="white")
        help_text.append("F", style="bold cyan")
        help_text.append("=Toggle Fun Facts  ", style="white")
        help_text.append("J", style="bold cyan")
        help_text.append("=Toggle Learning  ", style="white")
        help_text.append("L", style="bold cyan")
        help_text.append("=View Logs  ", style="white")
        help_text.append("H", style="bold cyan")
        help_text.append("=Help", style="white")
        return help_text

    def build_layout(self) -> Layout:
        """Build complete dashboard layout"""
        layout = Layout()

        # Top-level split
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body"),
            Layout(name="footer", size=1)
        )

        # Body split
        layout["body"].split_column(
            Layout(name="pipeline", size=12),
            Layout(name="boxes"),
            Layout(name="activity", size=17)
        )

        # Optional boxes side by side
        layout["boxes"].split_row(
            Layout(name="fun_facts"),
            Layout(name="learning_log")
        )

        # Populate
        layout["header"].update(self.render_header())
        layout["pipeline"].update(self.render_pipeline())
        layout["fun_facts"].update(self.render_fun_facts())
        layout["learning_log"].update(self.render_learning_log())
        layout["activity"].update(self.render_activity())
        layout["footer"].update(self.render_help())

        return layout


def main():
    state = DashboardState()
    dashboard = TrinityDashboard(state)

    console.clear()
    console.print("[bold cyan]Trinity Local M4 Dashboard Starting...[/]")
    console.print(f"Trinity Directory: {state.trinity_dir}")
    console.print(f"Status: {'🟢 Running' if state.is_running() else '🔴 Stopped'}")
    console.print("\nPress Ctrl+C to exit\n")

    time.sleep(1)

    try:
        with Live(dashboard.build_layout(), refresh_per_second=2, console=console) as live:
            while True:
                live.update(dashboard.build_layout())
                time.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/]")


if __name__ == "__main__":
    main()
