"""
Persistent Pattern Store for Trinity Protocol

Provides SQLite-backed storage with FAISS semantic search for pattern persistence
across agent restarts. This is the "second brain" memory layer.

Architecture:
- SQLite: Structured storage for pattern metadata, timestamps, success rates
- FAISS: Vector embeddings for semantic similarity search
- Sentence-Transformers: Embedding generation

Constitutional Compliance:
- Article I: Complete context - patterns persist across sessions
- Article IV: Continuous learning - success tracking and confidence scoring
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
import json

try:
    import numpy as np  # type: ignore
    import faiss  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    np = None  # type: ignore


class PersistentStore:
    """
    Persistent storage layer for Trinity Protocol patterns.

    Combines SQLite for structured data with FAISS for semantic search.
    Designed for 24/7 operation with graceful degradation.
    """

    def __init__(
        self,
        db_path: str = "trinity_patterns.db",
        embedding_model: str = "all-MiniLM-L6-v2",
        dimension: int = 384
    ):
        """
        Initialize persistent store.

        Args:
            db_path: Path to SQLite database
            embedding_model: Model name for sentence-transformers
            dimension: Embedding vector dimension (384 for MiniLM-L6-v2)
        """
        self.db_path = Path(db_path)
        self.dimension = dimension
        self.conn: Optional[sqlite3.Connection] = None
        self.index: Optional[Any] = None
        self.encoder: Optional[Any] = None

        # Initialize storage
        self._init_db()
        if FAISS_AVAILABLE:
            self._init_faiss()
            self._init_encoder(embedding_model)

    def _init_db(self) -> None:
        """Initialize SQLite database with schema."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence_count INTEGER DEFAULT 1,
                times_seen INTEGER DEFAULT 1,
                times_successful INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                metadata TEXT,
                embedding_id INTEGER
            )
        """)

        # Index for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pattern_type
            ON patterns(pattern_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pattern_name
            ON patterns(pattern_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_confidence
            ON patterns(confidence DESC)
        """)

        self.conn.commit()

    def _init_faiss(self) -> None:
        """Initialize FAISS index for semantic search."""
        if not FAISS_AVAILABLE:
            return

        # Use IndexFlatL2 for exact search (good for <1M vectors)
        self.index = faiss.IndexFlatL2(self.dimension)

    def _init_encoder(self, model_name: str) -> None:
        """Initialize sentence-transformers encoder."""
        if not FAISS_AVAILABLE:
            return

        self.encoder = SentenceTransformer(model_name)

    def store_pattern(
        self,
        pattern_type: str,
        pattern_name: str,
        content: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
        evidence_count: int = 1
    ) -> int:
        """
        Store a pattern with semantic embedding.

        Args:
            pattern_type: One of "failure", "opportunity", "user_intent"
            pattern_name: Specific pattern name (e.g., "critical_error")
            content: Pattern description/summary
            confidence: Confidence score (0.0-1.0)
            metadata: Optional metadata dict
            evidence_count: Number of evidence samples

        Returns:
            Pattern ID
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        now = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None

        # Check if pattern already exists
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, times_seen, evidence_count
            FROM patterns
            WHERE pattern_type = ? AND pattern_name = ? AND content = ?
        """, (pattern_type, pattern_name, content))

        existing = cursor.fetchone()

        if existing:
            # Update existing pattern
            pattern_id = existing['id']
            new_times_seen = existing['times_seen'] + 1
            new_evidence_count = existing['evidence_count'] + evidence_count

            cursor.execute("""
                UPDATE patterns
                SET times_seen = ?,
                    evidence_count = ?,
                    confidence = ?,
                    last_seen = ?,
                    metadata = ?
                WHERE id = ?
            """, (new_times_seen, new_evidence_count, confidence, now, metadata_json, pattern_id))
        else:
            # Insert new pattern
            embedding_id = None
            if FAISS_AVAILABLE and self.encoder and self.index:
                # Generate embedding
                embedding = self.encoder.encode([content])[0]
                embedding_id = self.index.ntotal
                self.index.add(np.array([embedding], dtype=np.float32))

            cursor.execute("""
                INSERT INTO patterns (
                    pattern_type, pattern_name, content, confidence,
                    evidence_count, times_seen, created_at, last_seen,
                    metadata, embedding_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_type, pattern_name, content, confidence,
                evidence_count, 1, now, now, metadata_json, embedding_id
            ))
            pattern_id = cursor.lastrowid

        self.conn.commit()
        return pattern_id

    def search_patterns(
        self,
        query: Optional[str] = None,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.7,
        limit: int = 10,
        semantic_search: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search patterns by query and filters.

        Args:
            query: Text query for semantic search (if FAISS available)
            pattern_type: Filter by pattern type
            min_confidence: Minimum confidence threshold
            limit: Maximum results to return
            semantic_search: Use semantic search if available

        Returns:
            List of pattern dicts sorted by relevance
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        cursor = self.conn.cursor()

        # Build SQL query
        sql = "SELECT * FROM patterns WHERE confidence >= ?"
        params: List[Any] = [min_confidence]

        if pattern_type:
            sql += " AND pattern_type = ?"
            params.append(pattern_type)

        # Semantic search with FAISS
        relevant_ids: Optional[List[int]] = None
        if query and semantic_search and FAISS_AVAILABLE and self.encoder and self.index:
            query_embedding = self.encoder.encode([query])[0]
            k = min(limit * 2, self.index.ntotal)  # Get more candidates

            if k > 0:
                distances, indices = self.index.search(
                    np.array([query_embedding], dtype=np.float32),
                    k
                )
                relevant_ids = [int(i) for i in indices[0] if i >= 0]

        if relevant_ids:
            sql += f" AND embedding_id IN ({','.join('?' * len(relevant_ids))})"
            params.extend(relevant_ids)

        sql += " ORDER BY confidence DESC, times_seen DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Convert to dicts
        results = []
        for row in rows:
            pattern = dict(row)
            if pattern['metadata']:
                pattern['metadata'] = json.loads(pattern['metadata'])
            results.append(pattern)

        return results

    def update_success(self, pattern_id: int, success: bool) -> None:
        """
        Update pattern success tracking.

        Args:
            pattern_id: Pattern ID to update
            success: Whether pattern application was successful
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT times_successful, times_seen
            FROM patterns
            WHERE id = ?
        """, (pattern_id,))

        row = cursor.fetchone()
        if not row:
            return

        new_successful = row['times_successful'] + (1 if success else 0)
        times_seen = row['times_seen']
        success_rate = new_successful / times_seen if times_seen > 0 else 0.0

        cursor.execute("""
            UPDATE patterns
            SET times_successful = ?,
                success_rate = ?
            WHERE id = ?
        """, (new_successful, success_rate, pattern_id))

        self.conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dict with pattern counts, average confidence, etc.
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        cursor = self.conn.cursor()

        # Total patterns
        cursor.execute("SELECT COUNT(*) as count FROM patterns")
        total = cursor.fetchone()['count']

        # By type
        cursor.execute("""
            SELECT pattern_type, COUNT(*) as count
            FROM patterns
            GROUP BY pattern_type
        """)
        by_type = {row['pattern_type']: row['count'] for row in cursor.fetchall()}

        # Average confidence
        cursor.execute("SELECT AVG(confidence) as avg_conf FROM patterns")
        avg_confidence = cursor.fetchone()['avg_conf'] or 0.0

        # Top patterns
        cursor.execute("""
            SELECT pattern_name, times_seen, success_rate
            FROM patterns
            ORDER BY times_seen DESC
            LIMIT 5
        """)
        top_patterns = [dict(row) for row in cursor.fetchall()]

        return {
            "total_patterns": total,
            "by_type": by_type,
            "average_confidence": round(avg_confidence, 3),
            "top_patterns": top_patterns,
            "faiss_available": FAISS_AVAILABLE,
            "index_size": self.index.ntotal if self.index else 0
        }

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
