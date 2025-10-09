#!/usr/bin/env python3
"""Release task locks - for manual cleanup or automatic session cleanup."""

import os
import sys
from pathlib import Path

LOCK_DIR = Path.home() / ".agency" / "memories" / ".locks"


def release_all_locks_for_session(session_id: str) -> int:
    """Release all locks held by a specific session."""
    if not LOCK_DIR.exists():
        return 0

    released_count = 0
    for lock_file in LOCK_DIR.glob("*.lock"):
        try:
            with lock_file.open() as f:
                holder = f.readline().strip()

            if holder == session_id:
                lock_file.unlink()
                print(f"🔓 Released lock: {lock_file.stem}")
                released_count += 1
        except Exception as e:
            print(f"⚠️ Error releasing {lock_file}: {e}")

    return released_count


def release_specific_lock(task_id: str, session_id: str = None) -> bool:
    """Release a specific task lock (optionally verify session ownership)."""
    lock_file = LOCK_DIR / f"{task_id}.lock"

    if not lock_file.exists():
        print(f"❌ No lock found for: {task_id}")
        return False

    if session_id:
        # Verify ownership before releasing
        with lock_file.open() as f:
            holder = f.readline().strip()

        if holder != session_id:
            print(f"❌ Lock owned by: {holder}, cannot release")
            return False

    lock_file.unlink()
    print(f"🔓 Released lock: {task_id}")
    return True


def list_active_locks() -> None:
    """List all currently active locks with rich metadata."""
    if not LOCK_DIR.exists():
        print("No locks directory found")
        return

    locks = list(LOCK_DIR.glob("*.lock"))

    if not locks:
        print("✅ No active locks")
        return

    print(f"🔒 Active locks ({len(locks)}):")
    for lock_file in sorted(locks):
        with lock_file.open() as f:
            lines = [line.strip() for line in f.readlines()]

        # Parse metadata (6-line format)
        session_id = lines[0] if len(lines) > 0 else "unknown"
        timestamp = lines[1] if len(lines) > 1 else "unknown"
        heartbeat = lines[2] if len(lines) > 2 else "unknown"
        terminal = lines[3] if len(lines) > 3 else "unknown"
        user = lines[4] if len(lines) > 4 else "unknown"
        task_desc = lines[5] if len(lines) > 5 else "unknown"

        print(f"\n  📋 {lock_file.stem}")
        print(f"    Session:     {session_id}")
        print(f"    User:        {user}@{terminal}")
        print(f"    Task:        {task_desc}")
        print(f"    Since:       {timestamp}")
        print(f"    Heartbeat:   {heartbeat}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  release_task_lock.py list                    # List all locks")
        print("  release_task_lock.py release-all <session>   # Release all locks for session")
        print("  release_task_lock.py release <task_id>       # Force release specific lock")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_active_locks()

    elif command == "release-all":
        if len(sys.argv) < 3:
            print("Error: session_id required")
            sys.exit(1)

        session_id = sys.argv[2]
        count = release_all_locks_for_session(session_id)
        print(f"✅ Released {count} lock(s)")

    elif command == "release":
        if len(sys.argv) < 3:
            print("Error: task_id required")
            sys.exit(1)

        task_id = sys.argv[2]
        session_id = sys.argv[3] if len(sys.argv) > 3 else None
        release_specific_lock(task_id, session_id)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
