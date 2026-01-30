
import pytest
import shutil
from pathlib import Path
from cells.action.action_cell import ActionCell, consult_memory, save_pattern
from agency_memory.pattern_memory import get_pattern_memory, Pattern

# Test setup to ensure clean memory for testing
@pytest.fixture
def clean_memory():
    base_dir = Path("/tmp/agency_test_memory")
    if base_dir.exists():
        shutil.rmtree(base_dir)
    base_dir.mkdir(parents=True)
    
    # Patch the global memory instance if possible or just rely on ActionCell picking it up
    # Since get_pattern_memory is a singleton using a default path, we need to be careful.
    # We might need to mock get_pattern_memory or PatternMemory init.
    # For integration testing, using specific test paths is safer.
    
    # HACK: We will patch the singleton _default_memory in pattern_memory module
    import agency_memory.pattern_memory
    original_memory = agency_memory.pattern_memory._default_memory
    
    # Create new memory instance
    test_memory = agency_memory.pattern_memory.PatternMemory(base_dir=base_dir)
    agency_memory.pattern_memory._default_memory = test_memory
    
    yield test_memory
    
    # Cleanup
    agency_memory.pattern_memory._default_memory = original_memory
    if base_dir.exists():
        shutil.rmtree(base_dir)

def test_save_and_retrieve_pattern(clean_memory):
    """Verify that we can save a pattern and retrieve it via tools."""
    
    # 1. Save a pattern
    result = save_pattern.function(
        title="Deployment Fix",
        problem="Deploy failure 500",
        solution="Restart nginx",
        tags=["deploy", "error", "nginx"]
    )
    assert "Pattern saved as" in result
    
    # 2. Consult memory
    # We should find it by tag
    search_result = consult_memory.function(query="How to fix deploy error?", tags=["deploy"])
    
    assert "Deployment Fix" in search_result
    assert "Restart nginx" in search_result
    assert "Confidence" in search_result

def test_consult_memory_no_results(clean_memory):
    """Verify empty search behavior."""
    search_result = consult_memory.function(query="Something random", tags=["unicorn"])
    assert "No relevant memories found" in search_result

def test_consult_memory_no_tags(clean_memory):
    """Verify behavior when no tags provided."""
    search_result = consult_memory.function(query="Help")
    assert "Please provide at least one relevant tag" in search_result
