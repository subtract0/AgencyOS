#!/usr/bin/env python3
"""
Auto-Supervise Hook - CMP Learning Coach

Mission 2.2 of Metaproductivity 2.0 - Automatic PR outcome tracking.

Triggered by GitHub Actions when PRs are closed/merged. Extracts metadata,
builds CmpEvent, records to CmpStore, and updates memory reinforcement signals.

Usage:
    python tools/auto_supervise_hook.py --signal=approved --pr-id=142
    python tools/auto_supervise_hook.py --signal=rejected --pr-id=143
    python tools/auto_supervise_hook.py --signal=approved --pr-id=144 --reverted=true

Constitutional Compliance:
- Article I: Retry on GitHub API timeout (2x, 3x)
- Article II: Only record events after definitive PR outcome
- Article III: Automated enforcement (no manual CmpEvent editing)
- Article IV: Continuous learning via VectorStore reinforcement updates
- Article V: Traces to docs/cmp_schema.md specification
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Add project root to PYTHONPATH for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from agency_memory.learning import CmpEvent, CmpStore


def parse_pr_body_metadata(pr_body: str) -> dict[str, Any]:
    """
    Extract metadata from PR body HTML comments.

    Expected format:
        <!-- agent_id: self_healer_v1 -->
        <!-- clade_id: self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal -->
        <!-- task_type: self_heal -->
        <!-- memory_ids: ["mem_001", "mem_002"] -->

    Args:
        pr_body: Full PR body text

    Returns:
        dict with agent_id, clade_id, task_type, memory_ids

    Raises:
        ValueError: If required metadata missing
    """
    metadata: dict[str, Any] = {}

    # Extract single-value fields
    for field in ["agent_id", "clade_id", "task_type"]:
        pattern = rf"<!--\s*{field}:\s*(.+?)\s*-->"
        match = re.search(pattern, pr_body)
        if match:
            metadata[field] = match.group(1).strip()

    # Extract memory_ids (JSON array)
    memory_ids_match = re.search(r"<!--\s*memory_ids:\s*(.+?)\s*-->", pr_body)
    if memory_ids_match:
        try:
            memory_ids = json.loads(memory_ids_match.group(1).strip())
            metadata["memory_ids"] = memory_ids if isinstance(memory_ids, list) else []
        except json.JSONDecodeError:
            metadata["memory_ids"] = []
    else:
        metadata["memory_ids"] = []

    # Validate required fields
    required = ["agent_id", "clade_id", "task_type"]
    missing = [f for f in required if f not in metadata]
    if missing:
        raise ValueError(f"Missing required metadata in PR body: {missing}")

    return metadata


def fetch_pr_data_from_github(
    pr_id: int,
    github_token: str,
    repo: str = "subtract0/AgencyOS",
    max_retries: int = 3
) -> dict[str, Any]:
    """
    Fetch PR metadata from GitHub API with retry logic.

    Args:
        pr_id: GitHub PR number
        github_token: GitHub API token (from GITHUB_TOKEN env var)
        repo: Repository in format "owner/repo"
        max_retries: Maximum retry attempts (Article I compliance)

    Returns:
        dict with pr_id, branch_name, body, created_at, closed_at,
        size_loc_delta, files_touched

    Raises:
        Exception: After max_retries failed attempts

    Constitutional Law #8: Focused function <50 lines
    """
    api_url = f"https://api.github.com/repos/{repo}/pulls/{pr_id}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(api_url, headers=headers, timeout=30)

            if response.status_code == 200:
                pr_data = response.json()

                # Fetch files separately
                files_url = f"{api_url}/files"
                files_response = requests.get(files_url, headers=headers, timeout=30)
                files = files_response.json() if files_response.status_code == 200 else []

                # Parse timestamps
                created_dt = datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00"))
                closed_dt = datetime.fromisoformat(pr_data["closed_at"].replace("Z", "+00:00")) if pr_data.get("closed_at") else datetime.now()

                return {
                    "pr_id": pr_data["number"],
                    "branch_name": pr_data["head"]["ref"],
                    "body": pr_data.get("body", ""),
                    "created_at": int(created_dt.timestamp()),
                    "closed_at": int(closed_dt.timestamp()),
                    "size_loc_delta": pr_data.get("additions", 0) + pr_data.get("deletions", 0),
                    "files_touched": [f["filename"] for f in files],
                }

            elif response.status_code in [502, 503, 504]:
                # Retry on server errors
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue

    raise Exception(f"Failed to fetch PR data after {max_retries} retries")


def build_cmp_event(
    pr_data: dict[str, Any],
    metadata: dict[str, Any],
    signal: str,
    reverted: bool = False
) -> CmpEvent:
    """
    Build CmpEvent from PR data and parsed metadata.

    Args:
        pr_data: PR metadata from GitHub API
        metadata: Parsed PR body comments
        signal: "approved" or "rejected"
        reverted: Was PR later reverted? (default: False)

    Returns:
        CmpEvent instance

    Constitutional Law #2: Strict typing with Pydantic (no Dict[Any, Any])
    """
    # Generate event ID (timestamp + short hash of branch name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    branch_hash = pr_data["branch_name"][-6:] if len(pr_data["branch_name"]) >= 6 else "000000"
    event_id = f"cmp_{timestamp}_{branch_hash}"

    return CmpEvent(
        id=event_id,
        pr_id=pr_data["pr_id"],
        branch_name=pr_data["branch_name"],
        agent_id=metadata["agent_id"],
        clade_id=metadata["clade_id"],
        task_type=metadata["task_type"],
        created_at=pr_data["created_at"],
        closed_at=pr_data["closed_at"],
        reinforcement_signal=signal,
        reverted=reverted,
        size_loc_delta=pr_data["size_loc_delta"],
        files_touched=pr_data["files_touched"],
        test_status="unknown",  # Can be enhanced later with CI test data
        test_suites=[],  # Can be enhanced later
    )


def record_cmp_event_and_update_memories(
    event: CmpEvent,
    memory_ids: list[str]
) -> None:
    """
    Record CmpEvent to CmpStore and update memory reinforcement signals.

    Args:
        event: CmpEvent to record
        memory_ids: List of memory IDs to update with reinforcement signal

    Constitutional Compliance:
    - Article III: Automated enforcement (CmpStore is append-only)
    - Article IV: Continuous learning (VectorStore memory updates)
    """
    # Record event to CmpStore
    store = CmpStore()
    store.record_event(event)

    # Update memory reinforcement signals
    if memory_ids:
        memory_store = EnhancedMemoryStore()
        for memory_id in memory_ids:
            try:
                memory_store.set_reinforcement(memory_id, event.reinforcement_signal)
            except Exception as e:
                print(f"Warning: Failed to update memory {memory_id}: {e}")


def main() -> int:
    """
    Main CLI entry point.

    Usage:
        auto_supervise_hook.py --signal=approved --pr-id=142
        auto_supervise_hook.py --signal=rejected --pr-id=143 --reverted=true

    Returns:
        Exit code (0=success, 1=error)
    """
    parser = argparse.ArgumentParser(
        description="Auto-Supervise Hook - Record PR outcomes as CMP events",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--signal",
        required=True,
        choices=["approved", "rejected"],
        help="Reinforcement signal (approved=merged, rejected=closed without merge)"
    )

    parser.add_argument(
        "--pr-id",
        type=int,
        required=True,
        help="GitHub PR number"
    )

    parser.add_argument(
        "--reverted",
        action="store_true",
        help="Flag if PR was later reverted due to smoke test failure"
    )

    args = parser.parse_args()

    # Get GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        return 1

    try:
        # Step 1: Fetch PR data from GitHub
        print(f"Fetching PR #{args.pr_id} metadata from GitHub...")
        pr_data = fetch_pr_data_from_github(args.pr_id, github_token)

        # Step 2: Parse metadata from PR body
        print("Parsing PR body metadata...")
        metadata = parse_pr_body_metadata(pr_data["body"])

        # Step 3: Build CmpEvent
        print(f"Building CmpEvent (signal={args.signal}, reverted={args.reverted})...")
        event = build_cmp_event(
            pr_data=pr_data,
            metadata=metadata,
            signal=args.signal,
            reverted=args.reverted
        )

        # Step 4: Record event and update memories
        print(f"Recording event {event.id}...")
        record_cmp_event_and_update_memories(event, metadata["memory_ids"])

        print(f"✅ CmpEvent recorded successfully")
        print(f"   Event ID: {event.id}")
        print(f"   Clade: {event.clade_id}")
        print(f"   Signal: {event.reinforcement_signal}")
        print(f"   Memories updated: {len(metadata['memory_ids'])}")

        return 0

    except ValueError as e:
        print(f"Error: Invalid PR metadata - {e}")
        return 1
    except Exception as e:
        print(f"Error: Failed to process PR - {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
