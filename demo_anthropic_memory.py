#!/usr/bin/env python
"""Anthropic Memory Tool Demo

Demonstrates the Anthropic memory tool integration with Agency OS.
Shows how Claude can maintain persistent context across conversations
using file-based memory storage.

Requirements:
    - anthropic>=0.42.0 (installed via requirements.txt)
    - ANTHROPIC_API_KEY environment variable set

Usage:
    python demo_anthropic_memory.py

Features Demonstrated:
    1. Creating memory files
    2. Reading and updating memories
    3. Cross-conversation persistence
    4. Integration with AgentContext
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.agent_context import create_agent_context
from tools.anthropic_agent_with_memory import (
    ANTHROPIC_AVAILABLE,
    create_client_with_memory,
    get_memory_stats,
    run_with_memory,
)


def demo_direct_memory_operations():
    """Demo 1: Direct memory tool operations"""
    print("=" * 70)
    print("DEMO 1: Direct Memory Tool Operations")
    print("=" * 70)
    print()

    # Create context and enable memory
    context = create_agent_context(session_id="demo_session")
    context.enable_anthropic_memory()

    tool = context.get_anthropic_memory_tool()

    # Create a memory file
    print("[1] Creating memory file...")
    result = tool.create(
        "/memories/project_info.txt",
        """
Project: Agency OS
Language: Python
Framework: agency-swarm
Key Feature: Multi-agent orchestration with constitutional governance
""".strip(),
    )
    print(f"    {result}")
    print()

    # View the file
    print("[2] Viewing memory file...")
    content = tool.view("/memories/project_info.txt")
    print(f"    {content}")
    print()

    # Update the file
    print("[3] Updating memory file...")
    result = tool.str_replace(
        "/memories/project_info.txt",
        "Multi-agent orchestration",
        "Multi-agent orchestration with learning system",
    )
    print(f"    {result}")
    print()

    # View updated content
    print("[4] Viewing updated content...")
    content = tool.view("/memories/project_info.txt")
    print(f"    {content}")
    print()

    # Create directory structure
    print("[5] Creating directory structure...")
    tool.create("/memories/agents/planner.txt", "Strategic planning agent")
    tool.create("/memories/agents/coder.txt", "TDD-focused implementation agent")
    tool.create("/memories/agents/auditor.txt", "Quality analysis agent")
    print("    Created 3 agent files")
    print()

    # List directory
    print("[6] Listing agents directory...")
    listing = tool.view("/memories/agents")
    print(f"    {listing}")
    print()

    # Get stats
    print("[7] Memory statistics...")
    stats = get_memory_stats(tool)
    print(f"    Files: {stats['file_count']}")
    print(f"    Directories: {stats['directory_count']}")
    print(f"    Total size: {stats['total_size']} bytes")
    print(f"    Location: {stats['base_dir']}")
    print()


def demo_sdk_integration():
    """Demo 2: SDK integration with Claude"""
    print("=" * 70)
    print("DEMO 2: SDK Integration with Claude")
    print("=" * 70)
    print()

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set - skipping API demo")
        print("   Set ANTHROPIC_API_KEY to run this demo")
        return

    if not ANTHROPIC_AVAILABLE:
        print("❌ Anthropic SDK not available")
        return

    # Create client with memory
    print("[1] Creating Claude client with memory tool...")
    client, memory_tool = create_client_with_memory(session_id="demo_conversation")
    print(f"    Memory location: {memory_tool.base_dir}")
    print()

    # First conversation - teaching Claude something
    print("[2] Teaching Claude about the project...")
    messages = [
        {
            "role": "user",
            "content": (
                "Please remember: This is Agency OS, a multi-agent system "
                "for autonomous code generation with constitutional governance. "
                "The main agents are: Planner, CodeAgent, Auditor, and QualityEnforcer. "
                "Create a memory file to remember this."
            ),
        }
    ]

    try:
        response = run_with_memory(
            client=client,
            memory_tool=memory_tool,
            messages=messages,
            model="claude-sonnet-4-5",
            max_tokens=1024,
        )

        print("    Claude's response:")
        for block in response.content:
            if hasattr(block, "text"):
                print(f"    {block.text}")
        print()

        # Second conversation - testing recall
        print("[3] Testing Claude's memory...")
        messages.append({"role": "assistant", "content": response.content})
        messages.append(
            {"role": "user", "content": "What agents did I tell you about? Read from your memory."}
        )

        response = run_with_memory(
            client=client,
            memory_tool=memory_tool,
            messages=messages,
            model="claude-sonnet-4-5",
            max_tokens=512,
        )

        print("    Claude's response:")
        for block in response.content:
            if hasattr(block, "text"):
                print(f"    {block.text}")
        print()

        # Show memory stats
        print("[4] Memory statistics after conversation...")
        stats = get_memory_stats(memory_tool)
        print(f"    Files created: {stats['file_count']}")
        print(f"    Total size: {stats['total_size']} bytes")
        print()

    except Exception as e:
        print(f"    ❌ API call failed: {e}")
        print()


def demo_agent_context_integration():
    """Demo 3: Integration with AgentContext"""
    print("=" * 70)
    print("DEMO 3: AgentContext Integration")
    print("=" * 70)
    print()

    # Create context
    print("[1] Creating AgentContext...")
    context = create_agent_context(session_id="agent_demo")
    print(f"    Session ID: {context.session_id}")
    print()

    # Check if memory enabled
    print("[2] Checking memory status...")
    print(f"    Memory enabled: {context.is_anthropic_memory_enabled()}")
    print()

    # Enable memory
    print("[3] Enabling Anthropic memory tool...")
    context.enable_anthropic_memory()
    print(f"    Memory enabled: {context.is_anthropic_memory_enabled()}")
    print()

    # Use memory tool
    print("[4] Using memory tool via context...")
    tool = context.get_anthropic_memory_tool()
    tool.create("/memories/session_info.txt", f"Session: {context.session_id}")
    content = tool.view("/memories/session_info.txt")
    print(f"    {content}")
    print()

    # Also use regular memory
    print("[5] Using regular memory storage...")
    context.store_memory(
        key="demo_task",
        content={"task": "Demonstrate memory integration", "status": "complete"},
        tags=["demo", "anthropic"],
    )

    memories = context.search_memories(["demo"])
    print(f"    Found {len(memories)} memories with 'demo' tag")
    print()


def main():
    """Run all demos"""
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         Anthropic Memory Tool Demo - Agency OS Integration        ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()

    try:
        # Demo 1: Direct operations
        demo_direct_memory_operations()

        # Demo 2: SDK integration (requires API key)
        demo_sdk_integration()

        # Demo 3: AgentContext integration
        demo_agent_context_integration()

        print("=" * 70)
        print("✅ All demos completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Check ~/.agency/memories/ for created memory files")
        print("2. Try 'python agency.py memory' for interactive memory management")
        print("3. Enable memory in your agents via context.enable_anthropic_memory()")
        print()

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
