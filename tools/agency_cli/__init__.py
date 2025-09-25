"""
Agency CLI Tools - Command-line interfaces for telemetry and navigation.

This module provides command-line tools extracted from enterprise infrastructure:

- dashboard: Live agent performance dashboard with real-time telemetry
- tail: Tail telemetry events with filtering and formatting options
- nav: Code navigation utilities for exploring project structure

Usage:
    from tools.agency_cli.dashboard import main as dashboard_main
    from tools.agency_cli.tail import main as tail_main
    from tools.agency_cli.nav import (
        list_dir, print_tree, grep_search,
        find_files, extract_symbols, find_references
    )

    # Dashboard
    dashboard_main()  # Interactive dashboard

    # Tail telemetry
    tail_main()  # Filtered event stream

    # Navigation
    files = find_files(".", "**/*.py")
    symbols = extract_symbols("tools/")
    refs = find_references(".", "TaskSpec")
"""

from .dashboard import main as dashboard_main
from .tail import main as tail_main
from .nav import (
    list_dir, print_tree, grep_search,
    find_files, extract_symbols, find_references,
    open_file_segment
)

__all__ = [
    "dashboard_main",
    "tail_main",
    "list_dir",
    "print_tree",
    "grep_search",
    "find_files",
    "extract_symbols",
    "find_references",
    "open_file_segment"
]