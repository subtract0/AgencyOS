#!/usr/bin/env python3
"""
Trinity Local M4 - Real-Time Visual Dashboard

Beautiful TUI showing autonomous agent activity with fun facts and learning logs.
"""

import json
import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Literal

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

# Dashboard state
class DashboardState:
    """Global dashboard state."""
    def __init__(self, trinity_dir: str = "~/.trinity-local"):
        self.trinity_dir = Path(trinity_dir).expanduser()
        self.events_file = self.trinity_dir / "events.jsonl"
        self.log_file = self.trinity_dir / "logs/trinity_local/trinity.log"
        self.learning_file = self.trinity_dir / "../logs/sessions"  # Agency learnings

        # State
        self.activities = deque(maxlen=15)
        self.agent_states = {
            "witness": {"status": "IDLE", "last_action": "Initializing...", "confidence": 0.0, "events": 0},
            "architect": {"status": "IDLE", "task": "", "progress": 0.0, "tokens": [0, 0]},
            "executor": {"status": "IDLE", "queue": 0, "next_task": ""}
        }
        self.code_view = {"mode": "idle", "file": "", "before": "", "after": "", "tests": ""}
        self.memory_usage = 0
        self.uptime_start = datetime.now()

        # Toggle states
        self.show_fun_facts = True
        self.show_learning_log = True

        # Fun facts rotation
        self.fun_facts = [
            "💡 Trinity uses 3 local LLMs - zero cloud dependency after setup",
            "🧠 VectorStore learning is constitutional law (Article IV)",
            "⚡ WITNESS detects patterns in <200ms",
            "🎯 100% test compliance is enforced (Article II - no exceptions)",
            "🔄 Models load sequentially to stay under 34GB memory",
            "📊 Constitutional Consciousness learns from its own violations",
            "🎸 This isn't an AI assistant - it's a Digital Muse",
            "⚖️ Software development is a legal problem requiring AI jurists",
            "🌙 Trinity learns YOUR coding DNA from git history",
            "🚀 Codestral:22B generates production-quality code autonomously",
            "🧬 Precedent-based decisions: what YOU chose in similar cases",
            "💎 Not 'AI assistant' - AI Jurist with jurisprudence",
            "🔥 Offline mode: Gets wiser without internet (local VectorStore)",
            "📜 Living Constitution: Evolves through case law, not just rules",
            "🎭 Multi-agent debate protocol coming: Agents argue constitutional interpretations"
        ]
        self.current_fact_index = 0
        self.last_fact_rotation = time.time()

        # Learning log
        self.recent_learnings = []

    def rotate_fun_fact(self):
        """Rotate fun fact every 10 seconds."""
        if time.time() - self.last_fact_rotation > 10:
            self.current_fact_index = (self.current_fact_index + 1) % len(self.fun_facts)
            self.last_fact_rotation = time.time()

    def get_uptime(self) -> str:
        """Get formatted uptime."""
        delta = datetime.now() - self.uptime_start
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def parse_events(self):
        """Parse new events from events.jsonl."""
        if not self.events_file.exists():
            return

        try:
            with open(self.events_file, 'r') as f:
                lines = f.readlines()

            # Process last 20 events (performance)
            for line in lines[-20:]:
                if not line.strip():
                    continue

                event = json.loads(line)
                self.process_event(event)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    def process_event(self, event: dict):
        """Process a single Trinity event."""
        agent = event.get("agent", "unknown")
        event_type = event.get("event_type", "")
        data = event.get("data", {})

        # Update agent state
        if agent == "witness":
            if event_type == "pattern_detected":
                self.agent_states["witness"]["last_action"] = f"Pattern: {data.get('pattern', 'Unknown')}"
                self.agent_states["witness"]["confidence"] = data.get("confidence", 0.0)
                self.agent_states["witness"]["events"] += 1
                self.agent_states["witness"]["status"] = "ACTIVE"

                # Add to activity stream
                self.activities.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "agent": "WITNESS",
                    "action": "Pattern detected",
                    "details": [
                        {"icon": "📊", "message": data.get("pattern", "Unknown pattern")},
                        {"icon": "→", "message": "Signaling ARCHITECT"}
                    ]
                })

        elif agent == "architect":
            if event_type == "model_loaded":
                self.agent_states["architect"]["status"] = "GENERATING"
                self.memory_usage = data.get("memory_mb", 0) / 1024  # Convert to GB

                self.activities.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "agent": "ARCHITECT",
                    "action": "Loading model...",
                    "details": [
                        {"icon": "🧠", "message": f"qwen2.5-coder:7b ({data.get('memory_mb', 0) / 1024:.1f}GB)"},
                        {"icon": "→", "message": f"Memory: {self.memory_usage:.1f}GB"}
                    ]
                })

            elif event_type == "spec_created":
                self.agent_states["architect"]["status"] = "IDLE"
                self.agent_states["architect"]["task"] = data.get("spec_file", "")

                self.activities.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "agent": "ARCHITECT",
                    "action": "Spec created",
                    "details": [
                        {"icon": "✅", "message": data.get("spec_file", "")},
                        {"icon": "→", "message": "Creating implementation plan"}
                    ]
                })

        elif agent == "executor":
            if event_type == "task_executing":
                self.agent_states["executor"]["status"] = "EXECUTING"
                self.agent_states["executor"]["next_task"] = data.get("task", "")

                self.activities.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "agent": "EXECUTOR",
                    "action": "Executing task",
                    "details": [
                        {"icon": "⚡", "message": data.get("task", "")},
                        {"icon": "→", "message": "Using codestral:22b"}
                    ]
                })

    def load_recent_learnings(self):
        """Load recent learning logs."""
        learning_dir = Path(self.trinity_dir).parent / "logs/sessions"
        if not learning_dir.exists():
            return

        try:
            # Get most recent session file
            session_files = sorted(learning_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not session_files:
                return

            recent_file = session_files[0]
            with open(recent_file, 'r') as f:
                lines = f.readlines()

            # Parse last 5 learnings
            self.recent_learnings = []
            for line in lines[-5:]:
                if not line.strip():
                    continue
                try:
                    learning = json.loads(line)
                    if learning.get("type") == "pattern":
                        self.recent_learnings.append({
                            "pattern": learning.get("description", "Unknown"),
                            "confidence": learning.get("confidence", 0.0),
                            "timestamp": learning.get("timestamp", "")
                        })
                except json.JSONDecodeError:
                    pass
        except (FileNotFoundError, PermissionError):
            pass


class TrinityDashboard:
    """Real-time Trinity activity dashboard."""

    def __init__(self, trinity_dir: str = "~/.trinity-local"):
        self.console = Console()
        self.state = DashboardState(trinity_dir)
        self.layout = Layout()

        # Setup dynamic layout
        self.update_layout()

    def update_layout(self):
        """Update layout based on toggle states."""
        # Base layout (always visible)
        sections = [
            Layout(name="header", size=3),
            Layout(name="pipeline", size=12),
            Layout(name="activity", size=15),
            Layout(name="code", size=18),
        ]

        # Add optional boxes
        if self.state.show_fun_facts and self.state.show_learning_log:
            # Side-by-side optional boxes
            optional_row = Layout()
            optional_row.split_row(
                Layout(name="fun_facts"),
                Layout(name="learning_log")
            )
            sections.insert(2, Layout(optional_row, size=8))
        elif self.state.show_fun_facts:
            sections.insert(2, Layout(name="fun_facts", size=5))
        elif self.state.show_learning_log:
            sections.insert(2, Layout(name="learning_log", size=8))

        # Footer always at bottom
        sections.append(Layout(name="footer", size=1))

        self.layout.split_column(*sections)

    def render_header(self) -> Panel:
        """Top status bar."""
        memory = self.state.memory_usage
        uptime = self.state.get_uptime()
        models = "3/3"  # All 3 models available

        header = Text()
        header.append("TRINITY LOCAL M4 - AUTONOMOUS LOOP", style="bold cyan")
        header.append("  ", style="white")
        header.append("[LIVE]", style="bold green blink")
        header.append(f"\nMemory: {memory:.1f}GB / 34GB  |  ", style="white")
        header.append(f"Models: {models}  |  ", style="white")
        header.append(f"Uptime: {uptime}", style="white")

        return Panel(header, border_style="cyan")

    def render_pipeline(self) -> Panel:
        """Agent pipeline status."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Status", width=3, justify="center")
        table.add_column("Agent", style="white")

        # WITNESS
        witness = self.state.agent_states["witness"]
        witness_icon = "●" if witness["status"] == "ACTIVE" else "○"
        witness_style = "green" if witness["status"] == "ACTIVE" else "dim"

        witness_text = Text()
        witness_text.append(f"WITNESS (qwen2.5-coder:1.5b)", style="cyan")
        witness_text.append(f"          [{witness['status']}]\n", style=witness_style)
        witness_text.append(f"Last: {witness['last_action']}\n", style="white")
        witness_text.append(f"Confidence: {witness['confidence']:.2f}  |  ", style="white")
        witness_text.append(f"Events: {witness['events']}", style="white")

        table.add_row(
            Text(witness_icon, style=witness_style),
            witness_text
        )

        # ARCHITECT
        architect = self.state.agent_states["architect"]
        architect_icon = "⚡" if architect["status"] == "GENERATING" else "○"
        architect_style = "yellow" if architect["status"] == "GENERATING" else "dim"

        architect_text = Text()
        architect_text.append(f"ARCHITECT (qwen2.5-coder:7b)", style="cyan")
        architect_text.append(f"         [{architect['status']}]\n", style=architect_style)

        if architect["status"] == "GENERATING":
            # Progress bar
            progress = architect["progress"]
            filled = int(progress * 30)
            bar = "█" * filled + "░" * (30 - filled)
            architect_text.append(f"{bar}  {progress * 100:.0f}%\n", style="yellow")
            architect_text.append(f"Creating: {architect['task']}\n", style="white")
            architect_text.append(f"Token: {architect['tokens'][0]} / {architect['tokens'][1]}", style="white")
        else:
            architect_text.append(f"Idle - waiting for patterns", style="dim")

        table.add_row(
            Text(architect_icon, style=architect_style),
            architect_text
        )

        # EXECUTOR
        executor = self.state.agent_states["executor"]
        executor_icon = "●" if executor["status"] == "EXECUTING" else "○"
        executor_style = "green" if executor["status"] == "EXECUTING" else "dim"

        executor_text = Text()
        executor_text.append(f"EXECUTOR (codestral:22b)", style="cyan")
        executor_text.append(f"              [{executor['status']}]\n", style=executor_style)
        executor_text.append(f"Queue: {executor['queue']} tasks  |  ", style="white")
        executor_text.append(f"Next: {executor['next_task'] or 'None'}", style="white")

        table.add_row(
            Text(executor_icon, style=executor_style),
            executor_text
        )

        return Panel(table, title="AGENT PIPELINE", border_style="yellow")

    def render_activity_stream(self) -> Panel:
        """Scrolling activity log."""
        if not self.state.activities:
            text = Text("Waiting for Trinity activity...", style="dim italic")
            return Panel(text, title="ACTIVITY STREAM", border_style="blue")

        text = Text()
        for activity in self.state.activities:
            timestamp = activity["timestamp"]
            agent = activity["agent"]
            action = activity["action"]
            details = activity.get("details", [])

            # Main line
            text.append(f"{timestamp}  ", style="dim")
            text.append(f"[{agent}]", style=self._get_agent_color(agent))
            text.append(f"  {action}\n", style="white")

            # Detail lines
            for detail in details:
                icon = detail.get("icon", "→")
                msg = detail["message"]
                text.append(f"           {icon} {msg}\n", style="cyan")

        return Panel(text, title="ACTIVITY STREAM", border_style="blue")

    def render_fun_facts(self) -> Panel:
        """Fun fact rotation."""
        fact = self.state.fun_facts[self.state.current_fact_index]

        text = Text()
        text.append(fact, style="italic yellow")

        return Panel(text, title="💡 FUN FACT", border_style="magenta", padding=(1, 2))

    def render_learning_log(self) -> Panel:
        """Recent learning patterns."""
        if not self.state.recent_learnings:
            text = Text("No recent learnings captured yet...", style="dim italic")
            return Panel(text, title="🧠 LEARNING LOG", border_style="green", padding=(1, 2))

        text = Text()
        for i, learning in enumerate(self.state.recent_learnings[-3:], 1):  # Last 3
            confidence = learning["confidence"]
            pattern = learning["pattern"]

            # Confidence bar
            filled = int(confidence * 10)
            bar = "█" * filled + "░" * (10 - filled)

            text.append(f"{i}. ", style="white")
            text.append(f"[{bar}] {confidence:.0%}\n", style="green")
            text.append(f"   {pattern}\n", style="white")

            if i < len(self.state.recent_learnings[-3:]):
                text.append("\n")

        return Panel(text, title="🧠 LEARNING LOG", border_style="green", padding=(1, 2))

    def render_code_view(self) -> Panel:
        """Live code diff or test output."""
        mode = self.state.code_view["mode"]

        if mode == "idle":
            text = Text("Waiting for code changes...", style="dim italic")
            return Panel(text, title="LIVE CODE VIEW", border_style="green")

        elif mode == "diff":
            return self._render_diff_view()

        elif mode == "test":
            return self._render_test_view()

        return Panel(Text("Unknown mode", style="red"), title="LIVE CODE VIEW", border_style="red")

    def _render_diff_view(self) -> Panel:
        """Before/After code comparison."""
        file_path = self.state.code_view["file"]
        before = self.state.code_view["before"]
        after = self.state.code_view["after"]

        text = Text()
        text.append(f"File: {file_path}\n\n", style="bold cyan")

        # Before code
        text.append("# BEFORE (VIOLATION)\n", style="red bold")
        if before:
            syntax = Syntax(before, "python", theme="monokai", line_numbers=False)
            text.append(syntax)
        text.append("\n")

        # After code
        text.append("# AFTER (FIXED)\n", style="green bold")
        if after:
            syntax = Syntax(after, "python", theme="monokai", line_numbers=False)
            text.append(syntax)
        text.append("\n")

        # Test results
        tests = self.state.code_view.get("tests", "")
        if tests:
            text.append(tests, style="green")

        return Panel(text, title="LIVE CODE VIEW", border_style="green")

    def _render_test_view(self) -> Panel:
        """Test execution output."""
        tests_output = self.state.code_view.get("tests", "Running tests...")

        text = Text()
        text.append(tests_output, style="white")

        return Panel(text, title="TEST EXECUTION", border_style="yellow")

    def render_footer(self) -> Panel:
        """Help text."""
        footer = Text()
        footer.append("Q: Quit  |  ", style="dim")
        footer.append("L: Logs  |  ", style="dim")
        footer.append("F: Toggle Fun Facts  |  ", style="dim")
        footer.append("J: Toggle Learning Log  |  ", style="dim")
        footer.append("H: Help", style="dim")

        return Panel(footer, border_style="dim")

    def _get_agent_color(self, agent: str) -> str:
        """Get color for agent name."""
        colors = {
            "WITNESS": "cyan",
            "ARCHITECT": "yellow",
            "EXECUTOR": "green"
        }
        return colors.get(agent, "white")

    def update_display(self):
        """Update all dashboard zones."""
        try:
            # Update header
            self.layout["header"].update(self.render_header())

            # Update pipeline
            self.layout["pipeline"].update(self.render_pipeline())

            # Update optional boxes if visible
            if self.state.show_fun_facts:
                if "fun_facts" in self.layout:
                    self.layout["fun_facts"].update(self.render_fun_facts())

            if self.state.show_learning_log:
                if "learning_log" in self.layout:
                    self.layout["learning_log"].update(self.render_learning_log())

            # Update activity stream
            self.layout["activity"].update(self.render_activity_stream())

            # Update code view
            self.layout["code"].update(self.render_code_view())

            # Update footer
            self.layout["footer"].update(self.render_footer())
        except KeyError:
            # Layout key doesn't exist (during toggle) - safe to ignore
            pass

    def run(self):
        """Main dashboard loop."""
        self.console.print("[bold green]Starting Trinity Dashboard...[/]")
        time.sleep(1)

        with Live(self.layout, console=self.console, refresh_per_second=2, screen=True) as live:
            iteration = 0
            while True:
                # Parse new events
                self.state.parse_events()

                # Rotate fun fact every 10 seconds
                self.state.rotate_fun_fact()

                # Load learnings every 30 iterations (~15 seconds)
                if iteration % 30 == 0:
                    self.state.load_recent_learnings()

                # Update display
                self.update_display()

                # Handle keyboard input (non-blocking)
                # TODO: Implement keyboard handler for Q/L/F/J/H

                time.sleep(0.5)  # 500ms refresh
                iteration += 1


def main():
    """Launch Trinity dashboard."""
    import sys

    trinity_dir = sys.argv[1] if len(sys.argv) > 1 else "~/.trinity-local"

    try:
        dashboard = TrinityDashboard(trinity_dir)
        dashboard.run()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped. Trinity continues running.")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
