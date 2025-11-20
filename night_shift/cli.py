import argparse
from night_shift.tui import run_dashboard

def main() -> None:
    parser = argparse.ArgumentParser(prog="nightshift")
    subparsers = parser.add_subparsers(dest="command")
    parser_echo = subparsers.add_parser("echo", help="Echo a message")
    parser_echo.add_argument("message")
    subparsers.add_parser("dashboard", help="Launch Night Shift status TUI dashboard")
    args = parser.parse_args()
    if args.command == "echo":
        print(args.message)
    elif args.command == "dashboard":
        run_dashboard()
    else:
        parser.print_help()
