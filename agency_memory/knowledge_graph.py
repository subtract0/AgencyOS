"""
agency_memory/knowledge_graph.py

The Antibodies: A NetworkX-based knowledge graph for AgencyOS.
Links Patterns, Errors, and Concepts to enable semantic reasoning.
"""

import json
import logging
import networkx as nx
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class NodeType(str, Enum):
    PATTERN = "pattern"
    ERROR = "error"
    CONCEPT = "concept"

class EdgeType(str, Enum):
    FIXES = "fixes"
    RELATES_TO = "relates_to"
    TAGGED_AS = "tagged_as"
    CAUSED_BY = "caused_by"

class AgencyGraph:
    """
    In-memory knowledge graph backed by NetworkX.
    Persists to knowledge_graph.json.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.graph = nx.DiGraph()
        self.base_dir = base_dir
        
        if self.base_dir:
            self.graph_path = self.base_dir / "knowledge_graph.json"
            self.load()

    def add_node(self, node_id: str, node_type: NodeType, **attrs):
        """Add a node to the graph."""
        self.graph.add_node(node_id, type=node_type.value, **attrs)

    def add_edge(self, source: str, target: str, relation: EdgeType, **attrs):
        """Add a directed edge between nodes."""
        # Ensure nodes exist to avoid orphan edges
        if not self.graph.has_node(source):
            logger.warning(f"Source node {source} does not exist. Creating generic Concept.")
            self.add_node(source, NodeType.CONCEPT)
        if not self.graph.has_node(target):
            logger.warning(f"Target node {target} does not exist. Creating generic Concept.")
            self.add_node(target, NodeType.CONCEPT)
            
        self.graph.add_edge(source, target, relation=relation.value, **attrs)

    def add_pattern(self, pattern_id: str, tags: List[str]):
        """
        High-level method to ingest a pattern.
        1. Creates PatternNode.
        2. Creates ConceptNodes for tags.
        3. Links them.
        """
        self.add_node(pattern_id, NodeType.PATTERN)
        
        for tag in tags:
            tag_id = tag.lower().strip()
            self.add_node(tag_id, NodeType.CONCEPT)
            self.add_edge(pattern_id, tag_id, EdgeType.TAGGED_AS)

    def find_related(self, node_id: str, max_hops: int = 1) -> List[str]:
        """Find related nodes within N hops."""
        if node_id not in self.graph:
            return []
        
        # Simple neighbor traversal for now
        # TODO: Implement PageRank or localized BFS
        if max_hops == 1:
            return list(self.graph.neighbors(node_id))
            
        # BFS for N hops
        related = set()
        for _, neighbor in nx.bfs_edges(self.graph, node_id, depth_limit=max_hops):
            related.add(neighbor)
        return list(related)

    def search_by_concept(self, concept: str) -> List[str]:
        """Find patterns tagged with a concept (reverse lookup)."""
        concept_id = concept.lower().strip()
        if concept_id not in self.graph:
            return []
        
        # Find predecessors (Patterns that point to this Concept via TAGGED_AS)
        patterns = [
            n for n in self.graph.predecessors(concept_id)
            if self.graph.nodes[n].get("type") == NodeType.PATTERN.value
        ]
        return patterns

    def save(self):
        """Serialize graph to JSON link-node format."""
        if not self.base_dir:
            return
            
        data = nx.node_link_data(self.graph)
        self.graph_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Saved Knowledge Graph: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges.")

    def load(self):
        """Load graph from JSON."""
        if not self.base_dir or not self.graph_path.exists():
            return

        try:
            data = json.loads(self.graph_path.read_text())
            self.graph = nx.node_link_graph(data)
            logger.info(f"Loaded Knowledge Graph: {len(self.graph.nodes)} nodes.")
        except Exception as e:
            logger.error(f"Failed to load Knowledge Graph: {e}")

if __name__ == "__main__":
    # Self-test
    kg = AgencyGraph()
    kg.add_pattern("fix_docker_network", ["Docker", "Networking", "Linux"])
    kg.add_pattern("fix_ssh_timeout", ["SSH", "Networking"])
    
    print("Related to 'Networking':", kg.search_by_concept("Networking"))
    print("Related to 'fix_docker_network':", kg.find_related("fix_docker_network"))
