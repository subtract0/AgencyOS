import sys
import os
import shutil
from pathlib import Path

# Ensure we can import cells
sys.path.append(os.getcwd())

from agency_memory.pattern_memory import PatternMemory, Pattern

def test_knowledge_graph_integration():
    print("🚀 Starting Class 11 Verification: Knowledge Graph")
    
    # Use a temp dir for safety
    test_dir = Path("./test_memories/patterns")
    if test_dir.exists():
        shutil.rmtree(test_dir.parent)
    test_dir.mkdir(parents=True)
    
    print(f"📂 Using test directory: {test_dir}")
    memory = PatternMemory(base_dir=test_dir)
    
    # Create a pattern
    p1 = Pattern(
        id="test_pattern_1",
        content={"solution": "Use Docker"},
        tags=["Docker", "Containerization"],
        confidence=0.9
    )
    
    print("💾 Storing pattern...")
    memory.store(p1)
    
    # Verify File
    json_path = test_dir / "test_pattern_1.json"
    if json_path.exists():
        print("✅ Pattern JSON file created.")
    else:
        print("❌ Pattern JSON file MISSING.")
        
    # Verify Graph File
    graph_path = test_dir / "knowledge_graph.json"
    if graph_path.exists():
        print("✅ Knowledge Graph JSON file created.")
        print(f"   Size: {graph_path.stat().st_size} bytes")
    else:
        print("❌ Knowledge Graph JSON file MISSING.")
        
    # Verify internal graph state
    stats = memory.stats()
    print(f"📊 Stats: {stats}")
    
    if stats.get("graph_nodes", 0) >= 3: # Pattern + 2 Tags
        print("✅ Graph nodes populated correctly.")
    else:
        print(f"❌ Graph node count incorrect. Expected >=3, got {stats.get('graph_nodes')}")

    # Cleanup
    shutil.rmtree(test_dir.parent)
    print("🧹 Cleanup complete.")

if __name__ == "__main__":
    test_knowledge_graph_integration()
