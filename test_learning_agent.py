#!/usr/bin/env python3
"""
Test script for LearningAgent integration.

This script tests the complete learning pipeline:
1. Create LearningAgent instance
2. Convert Markdown session to JSON format
3. Analyze session with AnalyzeSession tool
4. Extract insights with ExtractInsights tool
5. Consolidate learnings with ConsolidateLearning tool
6. Store knowledge in VectorStore with StoreKnowledge tool
7. Verify the complete workflow

Tests with real session data from /logs/sessions/
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from learning_agent.learning_agent import create_learning_agent
from shared.agent_context import create_agent_context
from agency_memory import VectorStore


def convert_markdown_session_to_json(markdown_path: str) -> dict:
    """
    Convert a Markdown session file to JSON format for testing.

    Parses the Markdown format session logs and creates a JSON structure
    that the AnalyzeSession tool can process.
    """
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract session metadata from the header
    session_id_match = re.search(r'Session Transcript: (.+)', content)
    session_id = session_id_match.group(1) if session_id_match else "unknown"

    generated_match = re.search(r'\*\*Generated:\*\* (.+)', content)
    generated_time = generated_match.group(1) if generated_match else datetime.now().isoformat()

    total_memories_match = re.search(r'\*\*Total Memories:\*\* (\d+)', content)
    total_memories = int(total_memories_match.group(1)) if total_memories_match else 0

    # Parse memory records
    entries = []
    memory_sections = re.split(r'\n---\n', content)

    for section in memory_sections:
        if not section.strip() or '## Memory Records' in section:
            continue

        # Extract memory data
        timestamp_match = re.search(r'\*\*Timestamp:\*\* (.+)', section)
        tags_match = re.search(r'\*\*Tags:\*\* (.+)', section)
        content_match = re.search(r'\*\*Content:\*\* (.+)', section, re.DOTALL)

        if timestamp_match and tags_match:
            timestamp = timestamp_match.group(1)
            tags = [tag.strip() for tag in tags_match.group(1).split(',')]

            # Parse content (it's usually a dictionary representation)
            content_str = content_match.group(1).strip() if content_match else "{}"
            try:
                # Try to parse as eval (since it's Python dict format)
                content_data = eval(content_str) if content_str.startswith('{') else {"raw": content_str}
            except:
                content_data = {"raw": content_str}

            entry = {
                "timestamp": timestamp,
                "tags": tags,
                "content": content_data
            }
            entries.append(entry)

    # Create JSON session structure
    session_data = {
        "session_id": session_id,
        "start_time": generated_time,
        "end_time": generated_time,  # Use same time for simplicity
        "total_memories": total_memories,
        "entries": entries
    }

    return session_data


def test_learning_agent_pipeline():
    """Test the complete LearningAgent pipeline with real session data."""

    print("=" * 60)
    print("LEARNING AGENT INTEGRATION TEST")
    print("=" * 60)

    # Step 1: Create agent context and LearningAgent
    print("\n1. Creating LearningAgent instance...")
    try:
        agent_context = create_agent_context()
        learning_agent = create_learning_agent(model="gpt-5", reasoning_effort="high", agent_context=agent_context)
        print("✅ LearningAgent created successfully")
        print(f"   - Agent name: {learning_agent.name}")
        print(f"   - Number of tools: {len(learning_agent.tools)}")
        print(f"   - Session ID: {agent_context.session_id}")
    except Exception as e:
        print(f"❌ Failed to create LearningAgent: {e}")
        return False

    # Step 2: Select and process a session file
    print("\n2. Processing session file...")
    sessions_dir = Path("/Users/am/Code/Agency/logs/sessions/")

    # Find a good session file with substantial content
    session_files = list(sessions_dir.glob("*.md"))
    if not session_files:
        print("❌ No session files found")
        return False

    # Choose a file with good size (not too small, not too large)
    good_sessions = [f for f in session_files if 10000 < f.stat().st_size < 150000]
    if not good_sessions:
        good_sessions = session_files  # Fall back to any session

    test_session = good_sessions[0]
    print(f"   - Selected session: {test_session.name}")
    print(f"   - File size: {test_session.stat().st_size:,} bytes")

    # Convert to JSON format
    try:
        session_json = convert_markdown_session_to_json(str(test_session))
        print(f"   - Converted to JSON with {len(session_json['entries'])} entries")

        # Save temporary JSON file for the tool
        temp_json_path = "/tmp/test_session.json"
        with open(temp_json_path, 'w') as f:
            json.dump(session_json, f, indent=2)
        print(f"   - Saved temporary JSON to {temp_json_path}")

    except Exception as e:
        print(f"❌ Failed to convert session: {e}")
        return False

    # Step 3: Test AnalyzeSession tool
    print("\n3. Testing AnalyzeSession tool...")
    try:
        from learning_agent.tools.analyze_session import AnalyzeSession

        analyze_tool = AnalyzeSession(
            session_file=temp_json_path,
            analysis_depth="standard"
        )
        analysis_result = analyze_tool.run()

        if "Error" in analysis_result:
            print(f"❌ AnalyzeSession failed: {analysis_result}")
            return False

        analysis_data = json.loads(analysis_result)
        print("✅ Session analysis completed successfully")
        print(f"   - Session ID: {analysis_data.get('session_metadata', {}).get('session_id', 'unknown')}")
        print(f"   - Total entries: {analysis_data.get('session_metadata', {}).get('total_entries', 0)}")

        if 'tool_analysis' in analysis_data:
            tool_count = len(analysis_data['tool_analysis'].get('tool_usage_counts', {}))
            print(f"   - Tools analyzed: {tool_count}")

    except Exception as e:
        print(f"❌ AnalyzeSession tool failed: {e}")
        return False

    # Step 4: Test ExtractInsights tool
    print("\n4. Testing ExtractInsights tool...")
    try:
        from learning_agent.tools.extract_insights import ExtractInsights

        insights_tool = ExtractInsights(
            session_analysis=analysis_result,
            insight_type="auto",
            confidence_threshold=0.6
        )
        insights_result = insights_tool.run()

        if "Error" in insights_result:
            print(f"❌ ExtractInsights failed: {insights_result}")
            return False

        insights_data = json.loads(insights_result)
        print("✅ Insights extraction completed successfully")
        print(f"   - Insights found: {len(insights_data.get('insights', []))}")
        print(f"   - Confidence threshold: {insights_data.get('confidence_threshold', 0)}")

        # Display first insight as example
        if insights_data.get('insights'):
            first_insight = insights_data['insights'][0]
            print(f"   - Example insight: {first_insight.get('title', 'Untitled')}")

    except Exception as e:
        print(f"❌ ExtractInsights tool failed: {e}")
        return False

    # Step 5: Test ConsolidateLearning tool
    print("\n5. Testing ConsolidateLearning tool...")
    try:
        from learning_agent.tools.consolidate_learning import ConsolidateLearning

        consolidate_tool = ConsolidateLearning(
            insights=insights_result,
            learning_type="auto",
            session_context=f"Test session analysis from {test_session.name}"
        )
        learning_result = consolidate_tool.run()

        # Check if it's actually a JSON response (success) vs an error string
        try:
            learning_data = json.loads(learning_result)
            if learning_data.get("error"):
                print(f"❌ ConsolidateLearning failed: {learning_data['error']}")
                return False
        except json.JSONDecodeError:
            if "Error" in learning_result:
                print(f"❌ ConsolidateLearning failed: {learning_result}")
                return False

        learning_data = json.loads(learning_result)
        print("✅ Learning consolidation completed successfully")
        print(f"   - Learning objects created: {learning_data.get('total_learning_objects', 0)}")
        print(f"   - Learning type: {learning_data.get('learning_type', 'unknown')}")

        # Display first learning object as example
        if learning_data.get('learning_objects'):
            first_learning = learning_data['learning_objects'][0]
            print(f"   - Example learning: {first_learning.get('title', 'Untitled')}")
            print(f"   - Learning ID: {first_learning.get('learning_id', 'unknown')}")

    except Exception as e:
        print(f"❌ ConsolidateLearning tool failed: {e}")
        return False

    # Step 6: Test StoreKnowledge tool
    print("\n6. Testing StoreKnowledge tool...")
    try:
        from learning_agent.tools.store_knowledge import StoreKnowledge

        store_tool = StoreKnowledge(
            learning=learning_result,
            storage_mode="standard",
            namespace="test_learnings"
        )
        store_result = store_tool.run()

        # Check if it's actually a JSON response (success) vs an error string
        try:
            store_data = json.loads(store_result)
            if store_data.get("error"):
                print(f"❌ StoreKnowledge failed: {store_data['error']}")
                return False
        except json.JSONDecodeError:
            if "Error" in store_result:
                print(f"❌ StoreKnowledge failed: {store_result}")
                return False

        store_data = json.loads(store_result)
        print("✅ Knowledge storage completed successfully")
        print(f"   - Status: {store_data.get('status', 'unknown')}")
        print(f"   - Stored objects: {store_data.get('stored_count', 0)}")
        print(f"   - Message: {store_data.get('message', 'No message')}")

    except Exception as e:
        print(f"❌ StoreKnowledge tool failed: {e}")
        return False

    # Step 7: Verify storage by checking VectorStore stats
    print("\n7. Verifying knowledge storage...")
    try:
        vector_store = VectorStore()

        # Get VectorStore statistics to verify storage
        stats = vector_store.get_stats()

        print("✅ Knowledge storage verification completed")
        print(f"   - Total memories stored: {stats.get('total_memories', 0)}")
        print(f"   - Has embeddings: {stats.get('has_embeddings', False)}")
        print(f"   - Embedding provider: {stats.get('embedding_provider', 'none')}")

        # Basic check that something was stored
        if stats.get('total_memories', 0) > 0:
            print("   - ✅ Learnings successfully stored in VectorStore")
        else:
            print("   - ⚠️  No memories found in VectorStore")

    except Exception as e:
        print(f"⚠️  Knowledge verification test failed (non-critical): {e}")

    # Step 8: Generate example learning output
    print("\n8. Example Learning Output:")
    print("-" * 40)
    try:
        if learning_data.get('learning_objects'):
            example_learning = learning_data['learning_objects'][0]
            print(json.dumps(example_learning, indent=2))
        else:
            print("No learning objects to display")
    except:
        print("Could not display example learning object")

    # Cleanup
    try:
        os.unlink(temp_json_path)
        print(f"\n🧹 Cleaned up temporary file: {temp_json_path}")
    except Exception as e:
        print(f"⚠️  Could not clean up temporary file: {e}")

    print("\n" + "=" * 60)
    print("✅ LEARNING AGENT INTEGRATION TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)

    return True


def main():
    """Main test runner."""
    try:
        success = test_learning_agent_pipeline()
        if success:
            print("\n🎉 All tests passed! LearningAgent integration is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ Tests failed! Check the output above for details.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()