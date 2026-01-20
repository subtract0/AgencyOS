"""
Empath Enricher - Local Semantic Analysis (Zero Cost)

Uses the local 'empath' model (Llama-3.3-70B) to enrich text content with:
- Suffering indicators
- Psychological analysis (pain points, needs, temporal state)
- Coaching hooks

Intended to run as a batch process on ingested data (e.g., Reddit posts, emails).
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import requests

# Add project root to path for imports
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
else:
    # When imported as module, assume package path is sufficient OR ensure root is in path elsewhere
    pass

from cells.shared.model_profiles import MODELS, ModelProfile

logger = logging.getLogger(__name__)

@dataclass
class EnrichmentResult:
    content: str
    suffering_score: int
    primary_pain: str
    secondary_pains: List[str]
    is_first_person: bool
    temporal: str  # "past", "ongoing", "future"
    seeking: str
    coaching_hooks: List[str]
    raw_analysis: Dict[str, Any]

class EmpathEnricher:
    def __init__(self):
        self.profile: ModelProfile = MODELS.get("empath") or MODELS["deep_coder"]
        self.api_url = f"{self.profile.api_base}/chat/completions"
        logger.info(f"Empath initialized using model: {self.profile.name} at {self.profile.api_base}")

    def enrich(self, content: str) -> Optional[EnrichmentResult]:
        """
        Enrich a single piece of text with semantic analysis.
        """
        if not content or len(content.strip()) < 10:
            return None

        prompt = f"""
You are an expert compassion-focused psychologist and data analyst. 
Analyze the following text for signs of human suffering, emotional needs, and psychological state.

Text: "{content}"

Return a JSON object with this exact schema (no markdown, just JSON):
{{
  "suffering_score": <1-10 integer, where 10 is extreme acute crisis>,
  "primary_pain": "<one or two words describing the core issue, e.g. isolation, failure, grief>",
  "secondary_pains": ["<list>", "<of>", "<secondary>", "<issues>"],
  "is_first_person": <boolean, true if the author is describing their own experience>,
  "temporal": "<'past'|'ongoing'|'future'>",
  "seeking": "<what is the author unconsciously or consciously asking for?>",
  "coaching_hooks": ["<short 3-5 word conceptual hook>", "<another hook>"]
}}
"""
        
        try:
           response = requests.post(
               self.api_url,
               json={
                   "model": self.profile.name,
                   "messages": [
                       {"role": "system", "content": "You are an empathetic analytical engine. Output valid JSON only."},
                       {"role": "user", "content": prompt}
                   ],
                   "temperature": 0.3, # Low temperature for consistent analysis
                   "max_tokens": 1024,
                   "response_format": {"type": "json_object"} 
               },
               timeout=300
           )
           
           if response.status_code != 200:
               logger.error(f"Empath API error: {response.status_code} - {response.text}")
               return None
               
           result_json = response.json()
           content_str = result_json["choices"][0]["message"]["content"]
           
           # Robust JSON parsing
           try:
               # Strip markdown code blocks if present
               clean_content = content_str.strip()
               if clean_content.startswith("```json"):
                   clean_content = clean_content[7:]
               if clean_content.startswith("```"):
                   clean_content = clean_content[3:]
               if clean_content.endswith("```"):
                   clean_content = clean_content[:-3]
               clean_content = clean_content.strip()
               
               data = json.loads(clean_content)
           except json.JSONDecodeError as e:
               logger.error(f"Empath JSON Parse Error: {e}")
               logger.error(f"Raw Output: {content_str[:500]}...") # Log first 500 chars
               return None
           
           return EnrichmentResult(
               content=content,
               suffering_score=data.get("suffering_score", 0),
               primary_pain=data.get("primary_pain", "unknown"),
               secondary_pains=data.get("secondary_pains", []),
               is_first_person=data.get("is_first_person", False),
               temporal=data.get("temporal", "unknown"),
               seeking=data.get("seeking", "unknown"),
               coaching_hooks=data.get("coaching_hooks", []),
               raw_analysis=data
           )

        except Exception as e:
            logger.error(f"Enrichment failed: {e}")
            return None

    def batch_enrich(self, items: List[Dict[str, Any]], content_key: str = "content") -> List[Dict[str, Any]]:
        """
        Process a list of dictionaries, verifying/enriching those that need it.
        Modifies the list in-place or returns a new one (enrichment adds 'llm_analysis' key).
        """
        results = []
        for item in items:
            text = item.get(content_key, "")
            # Skip if already enriched or empty
            if "llm_analysis" in item or not text:
                results.append(item)
                continue
            
            logger.info(f"Enriching item: {text[:30]}...")
            analysis = self.enrich(text)
            
            if analysis:
                item["llm_analysis"] = analysis.raw_analysis
                # Add convenience fields directly to item if desired, or keep nested
                item["suffering_score"] = analysis.suffering_score
            
            results.append(item)
            
        return results

# Helper for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    enricher = EmpathEnricher()
    
    test_text = "I feel so alone... nothing I do seems to matter anymore."
    print(f"Analyzing: {test_text}")
    result = enricher.enrich(test_text)
    
    if result:
        print(json.dumps(result.raw_analysis, indent=2))
    else:
        print("Analysis failed (is the model server running on port 8086?)")
