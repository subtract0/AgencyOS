
import json
import logging
import uuid
from typing import List, Dict, Any, Tuple
from datetime import datetime

from agency_memory.pattern_memory import Pattern
from cells.shared.lean_agent import LeanAgent, AgentConfig
from cells.shared.model_profiles import MODELS

logger = logging.getLogger(__name__)

class MemoryConsolidator:
    """
    The 'Sleep' mechanism. 
    Uses a high-intelligence model (Architect) to merge, refine, and archive patterns.
    """
    
    def __init__(self):
        # Use the powerful 70B model for deep thinking
        profile = MODELS["architect"]
        
        self.config = AgentConfig(
            name="MemoryConsolidator",
            model=profile, # Pass the full profile object so LeanAgent can see api_base
            max_tokens=2000, # Large context output
            temperature=0.3, # Low temp for precision
            instructions="""
            You are the Memory Consolidator. Your job is to organize the mind of an AI agent.
            
            You will receive a list of "Learned Patterns" (JSON).
            Your task is to:
            1. GROUP related patterns (e.g., 5 errors about 'login').
            2. MERGE them into single, high-quality truths.
            3. DISCARD useless or redundant noise.
            
            OUTPUT FORMAT:
            You must return a strictly valid JSON list of refined Pattern objects.
            Example:
            [
                {
                    "title": "Login Error Handling",
                    "description": "Auth fails if token is expired. Fix: Refresh token before 401.",
                    "tags": ["auth", "bugfix"],
                    "confidence": 0.95
                }
            ]
            
            RULES:
            - Keep the "evidence_count" high if merging multiple patterns.
            - Write clear, instructive descriptions.
            - Do not lose important technical details.
            """
        )
        self.agent = LeanAgent(self.config)

    def consolidate(self, patterns: List[Pattern]) -> Tuple[List[Pattern], str]:
        """
        Consolidate a list of patterns.
        Returns: (new_patterns, report_log)
        """
        if not patterns:
            return [], "No memories to consolidate."
            
        # 1. Clustering (Simple Tag-based for MVP)
        clusters = self._cluster_by_tags(patterns)
        
        refined_patterns = []
        report_lines = ["# Dream Journal\n"]
        
        for tag, cluster in clusters.items():
            if len(cluster) < 2:
                # If only 1 pattern, keep it as is (no merge needed yet)
                refined_patterns.extend(cluster)
                continue
                
            report_lines.append(f"## Processing Cluster: {tag} ({len(cluster)} items)")
            
            # 2. LLM Merge
            merged = self._merge_cluster(tag, cluster)
            if merged:
                refined_patterns.extend(merged)
                report_lines.append(f"  -> Merged into {len(merged)} patterns.")
            else:
                # Fallback: keep originals if merge failed
                refined_patterns.extend(cluster)
                report_lines.append("  -> Merge failed, kept originals.")
                
        return refined_patterns, "\n".join(report_lines)

    def _cluster_by_tags(self, patterns: List[Pattern]) -> Dict[str, List[Pattern]]:
        """Group patterns by their primary (first) tag."""
        clusters = {}
        for p in patterns:
            # Use first tag as primary cluster key, or 'misc'
            key = p.tags[0] if p.tags else "misc"
            clusters.setdefault(key, []).append(p)
        return clusters

    def _merge_cluster(self, tag: str, cluster: List[Pattern]) -> List[Pattern]:
        """Ask LLM to merge a specific cluster."""
        # Prepare input
        cluster_data = [p.to_dict() for p in cluster]
        prompt = f"Target Tag: {tag}\n\nMemories to Merge:\n{json.dumps(cluster_data, indent=2)}\n\nReturn JSON list of merged patterns."
        
        try:
            response = self.agent.run(prompt)
            # Parse JSON from response
            merged_data = self._extract_json_list(response)
            
            new_patterns = []
            for item in merged_data:
                # Create new Pattern objects
                new_p = Pattern(
                    id=str(uuid.uuid4()), # New ID for new thought
                    content={"description": item.get("description", item.get("content", ""))},
                    tags=item.get("tags", [tag]),
                    confidence=item.get("confidence", 0.9),
                    evidence_count=sum(p.evidence_count for p in cluster), # Access cumulative evidence but limit?
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                new_patterns.append(new_p)
                
            return new_patterns
            
        except Exception as e:
            logger.error(f"Failed to merge cluster {tag}: {e}")
            return None

    def _extract_json_list(self, text: str) -> List[Dict]:
        """Robustly extract JSON list from LLM text."""
        import re
        text = text.strip()
        
        # Try finding [ and ]
        start = text.find("[")
        end = text.rfind("]")
        
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except:
                pass
                
        return []
