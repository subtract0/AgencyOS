"""
Test learning consolidation functionality.

Tests the consolidate_learnings function with various memory sets
and verifies tag frequency analysis and learning report generation.
"""

import pytest
from datetime import datetime, timedelta
from agency_memory.learning import consolidate_learnings, generate_learning_report


def test_consolidate_learnings_empty():
    """Test consolidation with empty memory set."""
    result = consolidate_learnings([])

    assert result['summary'] == 'No memories to analyze'
    assert result['total_memories'] == 0
    assert result['tag_frequencies'] == {}
    assert result['patterns'] == {}
    assert 'generated_at' in result


def test_consolidate_learnings_small_set():
    """Test consolidation with small memory set."""
    # Create test memories with different patterns
    base_time = datetime.now()
    memories = [
        {
            'key': 'test_1',
            'content': 'This is a test message',
            'tags': ['test', 'agency'],
            'timestamp': base_time.isoformat()
        },
        {
            'key': 'test_2',
            'content': 'Error: Something went wrong',
            'tags': ['error', 'agency'],
            'timestamp': (base_time + timedelta(hours=1)).isoformat()
        },
        {
            'key': 'test_3',
            'content': 'Success: Task completed successfully',
            'tags': ['success', 'coder'],
            'timestamp': (base_time + timedelta(hours=2)).isoformat()
        },
        {
            'key': 'test_4',
            'content': 'git commit -m "test"',
            'tags': ['command', 'coder'],
            'timestamp': (base_time + timedelta(hours=3)).isoformat()
        }
    ]

    result = consolidate_learnings(memories)

    # Verify basic statistics
    assert result['total_memories'] == 4
    assert result['unique_tags'] == 6  # test, agency, error, success, coder, command
    assert result['avg_tags_per_memory'] == 2.0

    # Verify tag frequencies
    expected_tags = {'test': 1, 'agency': 2, 'error': 1, 'success': 1, 'coder': 2, 'command': 1}
    assert result['tag_frequencies'] == expected_tags

    # Verify top tags
    assert len(result['top_tags']) >= 2
    top_tag_names = [tag['tag'] for tag in result['top_tags']]
    assert 'agency' in top_tag_names
    assert 'coder' in top_tag_names

    # Verify content type analysis
    content_types = result['patterns']['content_types']
    assert 'text' in content_types
    assert 'error' in content_types
    assert 'success' in content_types
    assert 'command' in content_types

    # Verify insights are generated
    assert isinstance(result['insights'], list)
    assert len(result['insights']) > 0

    # Verify timestamp
    assert 'generated_at' in result


def test_tag_frequency_analysis():
    """Test tag frequency analysis with repeated tags."""
    memories = [
        {
            'key': 'mem_1',
            'content': 'Test 1',
            'tags': ['agency', 'planner'],
            'timestamp': datetime.now().isoformat()
        },
        {
            'key': 'mem_2',
            'content': 'Test 2',
            'tags': ['agency', 'coder'],
            'timestamp': datetime.now().isoformat()
        },
        {
            'key': 'mem_3',
            'content': 'Test 3',
            'tags': ['agency', 'planner', 'success'],
            'timestamp': datetime.now().isoformat()
        }
    ]

    result = consolidate_learnings(memories)

    # Agency should be most frequent (appears 3 times)
    assert result['tag_frequencies']['agency'] == 3
    assert result['tag_frequencies']['planner'] == 2
    assert result['tag_frequencies']['coder'] == 1
    assert result['tag_frequencies']['success'] == 1

    # Top tag should be 'agency'
    assert result['top_tags'][0]['tag'] == 'agency'
    assert result['top_tags'][0]['count'] == 3


def test_content_type_categorization():
    """Test content type categorization."""
    memories = [
        {'key': 'empty', 'content': '', 'tags': ['test'], 'timestamp': datetime.now().isoformat()},
        {'key': 'error', 'content': 'Error: Failed to connect', 'tags': ['test'], 'timestamp': datetime.now().isoformat()},
        {'key': 'success', 'content': 'Success: Operation completed', 'tags': ['test'], 'timestamp': datetime.now().isoformat()},
        {'key': 'command', 'content': 'git push origin main', 'tags': ['test'], 'timestamp': datetime.now().isoformat()},
        {'key': 'url', 'content': 'https://example.com', 'tags': ['test'], 'timestamp': datetime.now().isoformat()},
        {'key': 'long', 'content': 'x' * 300, 'tags': ['test'], 'timestamp': datetime.now().isoformat()},
        {'key': 'structured', 'content': {'key': 'value'}, 'tags': ['test'], 'timestamp': datetime.now().isoformat()},
        {'key': 'numeric', 'content': 42, 'tags': ['test'], 'timestamp': datetime.now().isoformat()},
    ]

    result = consolidate_learnings(memories)

    content_types = result['patterns']['content_types']
    assert content_types['empty'] == 1
    assert content_types['error'] == 1
    assert content_types['success'] == 1
    assert content_types['command'] == 1
    assert content_types['url'] == 1
    assert content_types['long_text'] == 1
    assert content_types['structured'] == 1
    assert content_types['numeric'] == 1


def test_time_pattern_analysis():
    """Test time pattern analysis."""
    # Create memories at different times
    base_time = datetime(2024, 1, 15, 10, 0, 0)  # Monday 10 AM
    memories = [
        {
            'key': 'morning_1',
            'content': 'Morning task',
            'tags': ['work'],
            'timestamp': base_time.isoformat()
        },
        {
            'key': 'morning_2',
            'content': 'Another morning task',
            'tags': ['work'],
            'timestamp': (base_time + timedelta(minutes=30)).isoformat()
        },
        {
            'key': 'afternoon',
            'content': 'Afternoon task',
            'tags': ['work'],
            'timestamp': (base_time + timedelta(hours=4)).isoformat()  # 2 PM
        }
    ]

    result = consolidate_learnings(memories)

    patterns = result['patterns']

    # Check hourly distribution
    assert patterns['hourly_distribution'][10] == 2  # 10 AM
    assert patterns['hourly_distribution'][14] == 1  # 2 PM

    # Check daily distribution
    assert patterns['daily_distribution']['Monday'] == 3

    # Check peak times
    assert patterns['peak_hour'] == 10
    assert patterns['peak_day'] == 'Monday'


def test_learning_report_generation():
    """Test learning report generation."""
    memories = [
        {
            'key': 'task_1',
            'content': 'Completed feature implementation',
            'tags': ['coding', 'success'],
            'timestamp': datetime.now().isoformat()
        },
        {
            'key': 'task_2',
            'content': 'Fixed bug in authentication',
            'tags': ['coding', 'bugfix'],
            'timestamp': datetime.now().isoformat()
        }
    ]

    report = generate_learning_report(memories, session_id="test_session")

    # Verify report structure
    assert "# Learning Consolidation Report" in report
    assert "**Session:** test_session" in report
    assert "## Statistics" in report
    assert "## Most Used Tags" in report
    assert "## Key Insights" in report
    assert "## Content Analysis" in report

    # Verify content
    assert "2" in report  # total memories
    assert "coding" in report  # should appear in top tags


def test_insights_generation():
    """Test insight generation with different scenarios."""
    # High memory activity scenario
    many_memories = []
    for i in range(120):
        many_memories.append({
            'key': f'mem_{i}',
            'content': f'Memory {i}',
            'tags': ['test', f'tag_{i % 5}'],
            'timestamp': datetime.now().isoformat()
        })

    result = consolidate_learnings(many_memories)
    insights = result['insights']

    # Should detect high memory activity
    high_activity_insight = any('High memory activity' in insight for insight in insights)
    assert high_activity_insight

    # Should have insights about most used tag
    most_used_insight = any('Most used tag' in insight for insight in insights)
    assert most_used_insight


def test_invalid_timestamp_handling():
    """Test handling of invalid timestamps."""
    memories = [
        {
            'key': 'valid',
            'content': 'Valid timestamp',
            'tags': ['test'],
            'timestamp': datetime.now().isoformat()
        },
        {
            'key': 'invalid',
            'content': 'Invalid timestamp',
            'tags': ['test'],
            'timestamp': 'not-a-timestamp'
        },
        {
            'key': 'missing',
            'content': 'Missing timestamp',
            'tags': ['test']
            # No timestamp field
        }
    ]

    # Should not crash with invalid timestamps
    result = consolidate_learnings(memories)
    assert result['total_memories'] == 3

    # Time patterns should only include valid timestamp
    patterns = result['patterns']
    total_time_entries = sum(patterns['hourly_distribution'].values())
    assert total_time_entries == 1  # Only one valid timestamp


if __name__ == "__main__":
    # Skip nested pytest execution to prevent recursion
    import os
    if os.environ.get("AGENCY_NESTED_TEST") != "1":
        pytest.main([__file__, "-v"])