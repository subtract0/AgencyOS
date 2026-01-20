"""
Batch Enricher (Backfill) - Fast & Concurrent

Iterates over goldminer exports and enriches them with semantic analysis
using the local Empath model.

Optimizations:
- ThreadPoolExecutor for concurrent model requests (Targeting M4 Max throughput).
- Robust error handling and checkpointing.
- Skips active files (safety).

Usage:
    python tools/life/batch_enrich.py
"""

import json
import logging
import sys
import time
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.life.empath import EmpathEnricher, EnrichmentResult

# Configuration
DATA_DIR = Path("logs/knowledge_ingest/exports")
FILE_PATTERN = "goldminer_*.json"
ACTIVE_THRESHOLD_SECONDS = 300  # 5 minutes
BATCH_SIZE = 20  # Save every N items
MAX_WORKERS = 5  # Concurrency level for M4 Max

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_file_active(file_path: Path) -> bool:
    """Check if file was modified recently."""
    mtime = file_path.stat().st_mtime
    age = time.time() - mtime
    return age < ACTIVE_THRESHOLD_SECONDS

def atomic_write(file_path: Path, data: List[Dict[str, Any]]):
    """Write data to temp file then rename to target."""
    tmp_path = file_path.with_suffix(".tmp")
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        shutil.move(str(tmp_path), str(file_path))
    except Exception as e:
        logger.error(f"Failed to write {file_path}: {e}")
        if tmp_path.exists():
            tmp_path.unlink()

def process_file(file_path: Path, enricher: EmpathEnricher):
    logger.info(f"Processing: {file_path.name}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.warning(f"Skipping {file_path.name}: Root is not a list")
            return
            
    except Exception as e:
        logger.error(f"Error reading {file_path.name}: {e}")
        return

    # Identify items needing enrichment
    # We store (index, content) tuples
    to_enrich: List[tuple[int, str]] = []
    
    for i, item in enumerate(data):
        if "llm_analysis" in item:
            continue
        
        content = item.get("content", "")
        # Fallback to 'body' or 'selftext' if 'content' is missing/empty
        if not content:
            content = item.get("selftext", "") or item.get("body", "")
            
        if not content or len(content) < 50: 
            continue
            
        to_enrich.append((i, content))
        
    if not to_enrich:
        logger.info(f"No unenriched items in {file_path.name}")
        return

    logger.info(f"Enriching {len(to_enrich)} items in {file_path.name} with {MAX_WORKERS} workers...")
    
    modified = False
    completed_count = 0
    
    # Define a helper for the executor
    def _enrich_task(idx_content):
        idx, text = idx_content
        return idx, enricher.enrich(text)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        futures = {executor.submit(_enrich_task, item): item for item in to_enrich}
        
        for future in as_completed(futures):
            try:
                idx, result = future.result()
                if result:
                    # Update data in memory
                    item = data[idx]
                    item["llm_analysis"] = result.raw_analysis
                    item["suffering_score"] = result.suffering_score
                    modified = True
                    completed_count += 1
                    
                    if completed_count % BATCH_SIZE == 0:
                        logger.info(f"  -> {file_path.name}: {completed_count}/{len(to_enrich)} enriched. Saving checkpoint...")
                        atomic_write(file_path, data)
                else:
                    # Log implicit failure (rate limit, model refusal, etc)
                    # logger.warning(f"Failed to enrich item {idx}")
                    pass
            except Exception as e:
                logger.error(f"Worker task failed: {e}")

    # Final save
    if modified:
        atomic_write(file_path, data)
        logger.info(f"Completed {file_path.name}: Enriched {completed_count} items total.")
    else:
        logger.info(f"No successful enrichments for {file_path.name}.")



def main():
    parser = argparse.ArgumentParser(description="Batch enrich goldminer exports.")
    parser.add_argument("--force", action="store_true", help="Process files even if they are active (modified < 5 mins ago).")
    parser.add_argument("--dir", type=str, default=str(DATA_DIR), help="Directory containing exports.")
    parser.add_argument("--pattern", type=str, default=FILE_PATTERN, help="File pattern to match.")
    args = parser.parse_args()

    data_path = Path(args.dir)
    file_pattern = args.pattern

    logger.info("Starting Batch Enrichment Backfill (Concurrent Mode)...")
    logger.info(f"Target Directory: {data_path}")
    logger.info(f"File Pattern: {file_pattern}")

    if args.force:
        logger.info("FORCE MODE: Ignoring file activity checks.")

    if not data_path.exists():
        logger.error(f"Directory not found: {data_path}")
        return

    enricher = EmpathEnricher()
    
    # 1. FIND FILES
    files = list(data_path.glob(file_pattern))
    files.sort(key=lambda f: f.stat().st_mtime)
    
    logger.info(f"Found {len(files)} export files.")

    for file_path in files:
        if not args.force and is_file_active(file_path):
            logger.info(f"Skipping active file: {file_path.name}")
            continue
        
        process_file(file_path, enricher)

    logger.info("Backfill complete.")

if __name__ == "__main__":
    main()
