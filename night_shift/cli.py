import argparse
import sys
from threading import Event

from night_shift.tui import run_dashboard

def _main() -> None:
    parser = argparse.ArgumentParser(prog="nightshift")
    subparsers = parser.add_subparsers(dest="command")

    # Existing sub‑commands would be added here by the original project.
    # New TUI dashboard command:
    dash_parser = subparsers.add_parser(
        "dashboard", help="Launch the Night Shift status dashboard"
    )
    dash_parser.add_argument(
        "--refresh", type=int, default=5, help="Refresh interval in seconds"
    )

    args = parser.parse_args()

    if args.command == "dashboard":
        # Allow graceful termination from tests.
        stop_evt = Event()
        try:
            run_dashboard(stop_event=stop_evt)
        except KeyboardInterrupt:
            stop_evt.set()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    _main()
