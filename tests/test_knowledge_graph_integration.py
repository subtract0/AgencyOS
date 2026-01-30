
import pytest
import shutil
from pathlib import Path
from cells.action.action_cell import ActionCell, consult_memory, save_pattern, link_patterns
from agency_memory.pattern_memory import get_pattern_memory, Pattern

@pytest.fixture
def clean_memory_graph():
    base_dir = Path("/tmp/agency_test_graph")
    if base_dir.exists():
        shutil.rmtree(base_dir)
    base_dir.mkdir(parents=True)
    
    # Patch global memory
    import agency_memory.pattern_memory
    original_memory = agency_memory.pattern_memory._default_memory
    
    test_memory = agency_memory.pattern_memory.PatternMemory(base_dir=base_dir)
    agency_memory.pattern_memory._default_memory = test_memory
    
    yield test_memory
    
    # Cleanup
    agency_memory.pattern_memory._default_memory = original_memory
    if base_dir.exists():
        shutil.rmtree(base_dir)

def test_graph_traversal(clean_memory_graph):
    """Verify that consulting memory finds related patterns via graph."""
    
    # 1. Create Pattern A (Cause)
    res_a = save_pattern.function(
        title="OOM Error", problem="Process killed", solution="Increase SWAP", tags=["error", "memory"]
    )
    id_a = res_a.split("saved as ")[1].strip(" .")
    
    # 2. Create Pattern B (Fix) - Not tagged with 'memory' directly maybe? 
    # Let's say it's tagged "swap", but we want to find it when searching "memory" if linked.
    res_b = save_pattern.function(
        title="Configure Swapfile", problem="Need swap", solution="dd if=/dev/zero ...", tags=["swap", "linux"]
    )
    id_b = res_b.split("saved as ")[1].strip(" .")
    
    # 3. Link them: OOM Error --relates_to--> Configure Swapfile
    link_res = link_patterns.function(source_id=id_a, target_id=id_b, relation="relates_to")
    assert "Link created" in link_res
    
    # 4. Search for "OOM Error" (should find Pattern A) and verify B matches via association
    # Query for "memory" -> finds A. A links to B. So B should be in results?
    # Our logic: find matching IDs -> then find neighbors -> include neighbors.
    
    results = consult_memory.function(query="Fix memory crash", tags=["memory"])
    
    assert id_a in results
    assert id_b in results # This confirms Graph Traversal worked!

def test_concept_search(clean_memory_graph):
    """Verify searching by concept node."""
    res = save_pattern.function(title="Test", problem="p", solution="s", tags=["Architecture"])
    pid = res.split("saved as ")[1].strip(" .")
    
    # "Architecture" tag creates a Concept Node.
    # Searching for "Architecture" (concept) should find the pattern.
    
    results = consult_memory.function(query="?", tags=["Architecture"])
    assert pid in results
