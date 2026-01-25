#!/usr/bin/env python3
"""
Librarian Agent - 24/7 Data Quality Guardian

Continuously works to improve the pain points database:
- Deduplication (find and merge similar entries)
- Quality scoring (rate each entry's value)
- Pruning (mark/remove low-value entries)
- Clustering (group similar stories into archetypes)
- Metadata enrichment (fill gaps)
- Index optimization

Philosophy: A librarian who works through the night,
quietly making the collection more valuable, more organized,
more accessible. Never resting, always improving.

Storage: /Volumes/Satechi4TB/pain_points/
Runs: 24/7 continuous
"""

import json
import time
import logging
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


@dataclass
class QualityReport:
    """Report on data quality improvements"""
    timestamp: str
    duplicates_found: int
    duplicates_merged: int
    low_quality_flagged: int
    metadata_enriched: int
    clusters_updated: int
    total_documents: int
    quality_score_avg: float


class LibrarianAgent:
    """
    24/7 Data Quality Guardian.

    Works continuously to improve the database:
    - More valuable (higher signal-to-noise)
    - More organized (better clustering)
    - More complete (enriched metadata)
    - More efficient (deduplicated)
    """

    # Quality thresholds
    MIN_CONTENT_LENGTH = 100
    MIN_AUTHENTICITY_SCORE = 0.1
    SIMILARITY_THRESHOLD = 0.85  # For deduplication
    LOW_QUALITY_THRESHOLD = 0.2

    def __init__(
        self,
        storage_path: str = "/Volumes/Satechi4TB/pain_points",
        model_base_url: str = "http://localhost:1234/v1",
    ):
        self.storage_path = Path(storage_path)
        self.librarian_path = self.storage_path / "librarian"
        self.model_base_url = model_base_url

        # Create directories
        self.librarian_path.mkdir(parents=True, exist_ok=True)
        (self.librarian_path / "reports").mkdir(exist_ok=True)
        (self.librarian_path / "clusters").mkdir(exist_ok=True)
        (self.librarian_path / "quarantine").mkdir(exist_ok=True)

        # Setup logging
        log_file = self.librarian_path / f"librarian_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Stats
        self.stats = {
            "duplicates_found": 0,
            "duplicates_merged": 0,
            "low_quality_flagged": 0,
            "metadata_enriched": 0,
            "clusters_updated": 0,
        }

        self.logger.info("=" * 60)
        self.logger.info("LIBRARIAN AGENT - Data Quality Guardian")
        self.logger.info("=" * 60)

    def _get_llm_client(self) -> Optional[OpenAI]:
        """Get LLM client"""
        if not OpenAI:
            return None
        try:
            return OpenAI(
                api_key="not-needed",
                base_url=self.model_base_url,
                timeout=120.0
            )
        except Exception:
            return None

    def _clean_llm_response(self, text: str) -> str:
        """Remove thinking tags from LLM response"""
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        return text

    def _get_collection(self):
        """Get ChromaDB collection"""
        if not CHROMADB_AVAILABLE:
            return None
        try:
            client = chromadb.PersistentClient(
                path=str(self.storage_path / "chromadb_index"),
                settings=Settings(anonymized_telemetry=False)
            )
            return client.get_collection("pain_points")
        except Exception as e:
            self.logger.error(f"ChromaDB error: {e}")
            return None

    def _content_hash(self, text: str) -> str:
        """Create hash for content comparison"""
        # Normalize text
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()

    def find_duplicates(self, batch_size: int = 100) -> List[Tuple[str, str, float]]:
        """
        Find duplicate or near-duplicate entries.
        Returns list of (id1, id2, similarity_score) tuples.
        """
        collection = self._get_collection()
        if not collection:
            return []

        duplicates = []

        try:
            # Get all documents
            total = collection.count()
            self.logger.info(f"Scanning {total} documents for duplicates...")

            # Process in batches
            all_docs = collection.get(
                include=["documents", "metadatas"],
                limit=min(total, 5000)
            )

            # Build content hash map
            hash_to_ids = defaultdict(list)
            for doc_id, doc, meta in zip(all_docs["ids"], all_docs["documents"], all_docs["metadatas"]):
                if doc:
                    content_hash = self._content_hash(doc[:500])  # Hash first 500 chars
                    hash_to_ids[content_hash].append((doc_id, meta.get("source_url", "")))

            # Find exact/near duplicates (same hash)
            for content_hash, id_list in hash_to_ids.items():
                if len(id_list) > 1:
                    # Multiple docs with same hash = duplicates
                    for i in range(len(id_list)):
                        for j in range(i + 1, len(id_list)):
                            duplicates.append((id_list[i][0], id_list[j][0], 1.0))
                            self.stats["duplicates_found"] += 1

            self.logger.info(f"Found {len(duplicates)} duplicate pairs")

        except Exception as e:
            self.logger.error(f"Error finding duplicates: {e}")

        return duplicates

    def merge_duplicates(self, duplicates: List[Tuple[str, str, float]], dry_run: bool = False) -> int:
        """
        Merge duplicate entries, keeping the higher quality one.
        Returns count of merged entries.
        """
        if not duplicates:
            return 0

        collection = self._get_collection()
        if not collection:
            return 0

        merged = 0
        ids_to_delete = set()

        for id1, id2, similarity in duplicates:
            if id1 in ids_to_delete or id2 in ids_to_delete:
                continue

            try:
                # Get both documents
                doc1 = collection.get(ids=[id1], include=["documents", "metadatas"])
                doc2 = collection.get(ids=[id2], include=["documents", "metadatas"])

                if not doc1["documents"] or not doc2["documents"]:
                    continue

                # Decide which to keep (longer content, higher authenticity)
                meta1 = doc1["metadatas"][0] if doc1["metadatas"] else {}
                meta2 = doc2["metadatas"][0] if doc2["metadatas"] else {}

                score1 = len(doc1["documents"][0]) + meta1.get("authenticity_score", 0) * 1000
                score2 = len(doc2["documents"][0]) + meta2.get("authenticity_score", 0) * 1000

                # Mark lower quality for deletion
                if score1 >= score2:
                    ids_to_delete.add(id2)
                else:
                    ids_to_delete.add(id1)

                merged += 1

            except Exception as e:
                self.logger.debug(f"Error comparing {id1} and {id2}: {e}")

        # Delete duplicates
        if not dry_run and ids_to_delete:
            try:
                collection.delete(ids=list(ids_to_delete))
                self.stats["duplicates_merged"] += len(ids_to_delete)
                self.logger.info(f"Deleted {len(ids_to_delete)} duplicate entries")
            except Exception as e:
                self.logger.error(f"Error deleting duplicates: {e}")

        return merged

    def score_quality(self, doc: str, meta: Dict) -> float:
        """
        Calculate quality score for a document.
        Returns 0.0 - 1.0
        """
        score = 0.0

        # Length score (0-0.2)
        length = len(doc)
        if length > 500:
            score += 0.2
        elif length > 200:
            score += 0.1
        elif length > 100:
            score += 0.05

        # Authenticity score from metadata (0-0.3)
        auth = meta.get("authenticity_score", 0) or 0
        score += min(0.3, auth * 0.3)

        # Has suffering indicators (0-0.2)
        indicators = meta.get("suffering_indicators", "")
        if indicators and len(indicators) > 10:
            score += 0.2

        # First person narrative (0-0.15)
        doc_lower = doc.lower()
        first_person = doc_lower.count(" i ") + doc_lower.count("i'm") + doc_lower.count("i've")
        if first_person > 5:
            score += 0.15
        elif first_person > 2:
            score += 0.08

        # Has meaningful content (not just links/short) (0-0.15)
        word_count = len(doc.split())
        if word_count > 100:
            score += 0.15
        elif word_count > 50:
            score += 0.08

        return min(1.0, score)

    def flag_low_quality(self, batch_size: int = 500) -> int:
        """
        Identify and flag low-quality entries.
        Returns count of flagged entries.
        """
        collection = self._get_collection()
        if not collection:
            return 0

        flagged = 0
        quarantine_data = []

        try:
            total = collection.count()
            self.logger.info(f"Scanning {total} documents for quality...")

            results = collection.get(
                include=["documents", "metadatas"],
                limit=min(total, 5000)
            )

            for doc_id, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
                if not doc:
                    continue

                quality = self.score_quality(doc, meta)

                if quality < self.LOW_QUALITY_THRESHOLD:
                    flagged += 1
                    quarantine_data.append({
                        "id": doc_id,
                        "quality_score": quality,
                        "reason": "Below quality threshold",
                        "content_preview": doc[:200],
                        "flagged_at": datetime.now().isoformat()
                    })

            # Save quarantine list (don't delete, just flag)
            if quarantine_data:
                quarantine_file = self.librarian_path / "quarantine" / f"flagged_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                with open(quarantine_file, 'w') as f:
                    json.dump(quarantine_data, f, indent=2)

                self.stats["low_quality_flagged"] += flagged
                self.logger.info(f"Flagged {flagged} low-quality entries")

        except Exception as e:
            self.logger.error(f"Error flagging low quality: {e}")

        return flagged

    def enrich_metadata(self, batch_size: int = 50) -> int:
        """
        Enrich metadata for entries that are missing key fields.
        Uses LLM to extract: archetype, emotional_state, life_stage
        """
        collection = self._get_collection()
        client = self._get_llm_client()
        if not collection or not client:
            return 0

        enriched = 0

        try:
            # Find entries without enrichment
            results = collection.get(
                include=["documents", "metadatas"],
                limit=2000
            )

            to_enrich = []
            for doc_id, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
                if not doc:
                    continue
                # Check if already enriched
                if not meta.get("archetype") and not meta.get("life_stage"):
                    quality = self.score_quality(doc, meta)
                    if quality > 0.4:  # Only enrich decent quality
                        to_enrich.append((doc_id, doc, meta))

            self.logger.info(f"Found {len(to_enrich)} entries to enrich")

            # Enrich in batches
            for doc_id, doc, meta in to_enrich[:batch_size]:
                try:
                    prompt = f"""Analyze this post and extract structured metadata.

POST:
"{doc[:1000]}"

Respond in JSON:
{{
    "archetype": "One of: seeker, venter, crisis, transformer, stuck, helper",
    "life_stage": "One of: student, early_career, midlife, late_career, retired, unknown",
    "primary_emotion": "The dominant emotion",
    "seeking_clarity": true/false (are they open to new perspectives?)
}}

Be concise. JSON only."""

                    response = client.chat.completions.create(
                        model="vcoder-120b-1.0-hi-mlx",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=200
                    )

                    result = self._clean_llm_response(response.choices[0].message.content)

                    # Parse JSON
                    start = result.find('{')
                    end = result.rfind('}') + 1
                    if start >= 0 and end > start:
                        enrichment = json.loads(result[start:end])

                        # Update metadata
                        new_meta = dict(meta)
                        new_meta["archetype"] = enrichment.get("archetype", "unknown")
                        new_meta["life_stage"] = enrichment.get("life_stage", "unknown")
                        new_meta["primary_emotion"] = enrichment.get("primary_emotion", "")
                        new_meta["seeking_clarity"] = enrichment.get("seeking_clarity", False)
                        new_meta["enriched_at"] = datetime.now().isoformat()

                        # Update in ChromaDB
                        collection.update(
                            ids=[doc_id],
                            metadatas=[new_meta]
                        )

                        enriched += 1

                    time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    self.logger.debug(f"Error enriching {doc_id}: {e}")

            self.stats["metadata_enriched"] += enriched
            self.logger.info(f"Enriched {enriched} entries with metadata")

        except Exception as e:
            self.logger.error(f"Error in enrichment: {e}")

        return enriched

    def build_clusters(self) -> int:
        """
        Group similar stories into clusters/archetypes.
        Saves cluster definitions for later analysis.
        """
        collection = self._get_collection()
        if not collection:
            return 0

        clusters = defaultdict(list)

        try:
            # Get enriched documents
            results = collection.get(
                include=["documents", "metadatas"],
                limit=5000
            )

            # Group by archetype + topic
            for doc_id, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
                if not doc or not meta:
                    continue

                archetype = meta.get("archetype", "unknown")
                topic = meta.get("topic", "unknown")
                cluster_key = f"{archetype}_{topic}"

                clusters[cluster_key].append({
                    "id": doc_id,
                    "preview": doc[:200],
                    "quality": self.score_quality(doc, meta),
                    "seeking_clarity": meta.get("seeking_clarity", False)
                })

            # Save cluster summary
            cluster_summary = {}
            for key, members in clusters.items():
                if len(members) >= 3:  # Only meaningful clusters
                    cluster_summary[key] = {
                        "count": len(members),
                        "avg_quality": sum(m["quality"] for m in members) / len(members),
                        "clarity_seekers": sum(1 for m in members if m.get("seeking_clarity")),
                        "top_examples": sorted(members, key=lambda x: x["quality"], reverse=True)[:3]
                    }

            # Save
            cluster_file = self.librarian_path / "clusters" / f"clusters_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(cluster_file, 'w') as f:
                json.dump(cluster_summary, f, indent=2)

            self.stats["clusters_updated"] = len(cluster_summary)
            self.logger.info(f"Built {len(cluster_summary)} clusters")

            return len(cluster_summary)

        except Exception as e:
            self.logger.error(f"Error building clusters: {e}")
            return 0

    def generate_report(self) -> QualityReport:
        """Generate quality report"""
        collection = self._get_collection()
        total = collection.count() if collection else 0

        # Calculate average quality
        avg_quality = 0.5  # Default
        if collection:
            try:
                results = collection.get(
                    include=["documents", "metadatas"],
                    limit=1000
                )
                qualities = []
                for doc, meta in zip(results["documents"], results["metadatas"]):
                    if doc:
                        qualities.append(self.score_quality(doc, meta))
                if qualities:
                    avg_quality = sum(qualities) / len(qualities)
            except:
                pass

        report = QualityReport(
            timestamp=datetime.now().isoformat(),
            duplicates_found=self.stats["duplicates_found"],
            duplicates_merged=self.stats["duplicates_merged"],
            low_quality_flagged=self.stats["low_quality_flagged"],
            metadata_enriched=self.stats["metadata_enriched"],
            clusters_updated=self.stats["clusters_updated"],
            total_documents=total,
            quality_score_avg=round(avg_quality, 3)
        )

        # Save report
        report_file = self.librarian_path / "reports" / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2)

        return report

    def run_cycle(self) -> QualityReport:
        """Run one complete quality improvement cycle"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("LIBRARIAN CYCLE START")
        self.logger.info("=" * 60)

        # 1. Find and merge duplicates
        self.logger.info("\n[1/4] Deduplication...")
        duplicates = self.find_duplicates()
        if duplicates:
            self.merge_duplicates(duplicates)

        # 2. Flag low quality
        self.logger.info("\n[2/4] Quality assessment...")
        self.flag_low_quality()

        # 3. Enrich metadata
        self.logger.info("\n[3/4] Metadata enrichment...")
        self.enrich_metadata(batch_size=30)

        # 4. Build clusters
        self.logger.info("\n[4/4] Clustering...")
        self.build_clusters()

        # Generate report
        report = self.generate_report()

        self.logger.info("\n" + "=" * 60)
        self.logger.info("CYCLE COMPLETE")
        self.logger.info(f"  Documents: {report.total_documents}")
        self.logger.info(f"  Avg Quality: {report.quality_score_avg:.1%}")
        self.logger.info(f"  Duplicates merged: {report.duplicates_merged}")
        self.logger.info(f"  Enriched: {report.metadata_enriched}")
        self.logger.info(f"  Clusters: {report.clusters_updated}")
        self.logger.info("=" * 60)

        return report

    def run_continuous(self, interval_hours: int = 2):
        """Run continuously"""
        self.logger.info(f"Starting continuous mode (interval: {interval_hours}h)")

        cycle = 0
        while True:
            try:
                cycle += 1
                self.logger.info(f"\n{'#'*60}")
                self.logger.info(f"CYCLE {cycle}")
                self.logger.info(f"{'#'*60}")

                report = self.run_cycle()

                self.logger.info(f"\nSleeping {interval_hours} hours...")
                time.sleep(interval_hours * 3600)

            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Error in cycle: {e}")
                time.sleep(300)  # Wait 5 min on error


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Librarian Agent - Data Quality Guardian")
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=2, help='Hours between cycles (default: 2)')
    parser.add_argument('--storage', type=str, default="/Volumes/Satechi4TB/pain_points")

    args = parser.parse_args()

    librarian = LibrarianAgent(storage_path=args.storage)

    if args.once:
        librarian.run_cycle()
    else:
        librarian.run_continuous(interval_hours=args.interval)


if __name__ == "__main__":
    main()
