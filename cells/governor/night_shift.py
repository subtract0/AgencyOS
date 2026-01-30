import logging
import time
import sys
from datetime import datetime
from pathlib import Path

# Fix path to allow imports from root
sys.path.insert(0, str(Path(__file__).parents[2]))

from typing import List, Set

from agency_memory.pattern_memory import get_pattern_memory, Pattern
from cells.shared.memory_consolidator import MemoryConsolidator

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NightShift")

class NightShift:
    """
    Orchestrates the nightly memory consolidation process.
    """
    
    def __init__(self):
        self.memory = get_pattern_memory()
        self.consolidator = MemoryConsolidator()
        self.journal_dir = Path.home() / ".agency" / "memories" / "journals"
        self.journal_dir.mkdir(parents=True, exist_ok=True)

    def run_shift(self, force: bool = False):
        """
        Execute the Night Shift.
        1. Load all memories.
        2. Consolidate.
        3. Apply changes (Diff).
        4. Write Journal.
        """
        logger.info("🌙 Night Shift Starting...")
        
        # 1. Snapshot State
        current_patterns = self.memory.get_all_patterns()
        initial_count = len(current_patterns)
        logger.info(f"Loaded {initial_count} active patterns.")
        
        if initial_count == 0:
            logger.info("Brain is empty. Nothing to consolidate.")
            return

        # 2. Dream (Consolidate)
        logger.info("🧠 Dreaming (Consolidating)...")
        start_time = time.time()
        
        # NOTE: running ALL patterns might be expensive if count > 100.
        # Future optimization: Batch by tags or time. 
        # For now (Class 9), we process all.
        refined_patterns, journal_log = self.consolidator.consolidate(current_patterns)
        
        duration = time.time() - start_time
        logger.info(f"Dreaming complete in {duration:.2f}s.")
        
        # 3. Apply Changes (Diff)
        old_ids = {p.id for p in current_patterns}
        new_ids = {p.id for p in refined_patterns}
        
        ids_to_delete = old_ids - new_ids
        
        # Safety Check: Don't delete everything if something went wrong
        # e.g., if refined_patterns is empty but initial was not.
        if len(refined_patterns) == 0 and initial_count > 0:
             logger.error("❌ CRITICAL: Consolidation returned 0 patterns! Aborting to prevent lobotomy.")
             return
             
        logger.info(f"Applying Memory Changes: +{len(new_ids - old_ids)} new, -{len(ids_to_delete)} obsolete.")
        
        # ACTUALLY APPLY
        self.memory.bulk_store(refined_patterns)  # Update kept, Add new
        self.memory.bulk_delete(list(ids_to_delete)) # Remove merged/obsolete
        
        final_count = self.memory.count()
        compression_ratio = (1 - (final_count / initial_count)) * 100 if initial_count > 0 else 0
        
        # 4. Write Journal
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        journal_file = self.journal_dir / f"DREAM_JOURNAL_{timestamp}.md"
        
        report = f"""# Dream Journal: {timestamp}

**Stats:**
- Duration: {duration:.2f}s
- Patterns Before: {initial_count}
- Patterns After: {final_count}
- Compression: {compression_ratio:.1f}%

## Consolidation Log
{journal_log}
"""
        journal_file.write_text(report)
        logger.info(f"✅ Night Shift Complete. Journal written to {journal_file}")
        print(f"📉 Memory Compressed by {compression_ratio:.1f}%. Saved to {journal_file}")

if __name__ == "__main__":
    import os
    os.environ["OPENAI_API_KEY"] = "mlx" # Dummy key for local model
    shift = NightShift()
    shift.run_shift(force=True)
