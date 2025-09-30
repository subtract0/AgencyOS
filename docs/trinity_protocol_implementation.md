# Trinity Protocol: Complete Implementation Guide

## 🎯 Mission Statement

Transform Agency into a continuously running autonomous system with persistent learning capabilities. The system operates 24/7 with three core agents (AUDITLEARN, PLAN, EXECUTE) that monitor, learn, plan, and improve the codebase without manual intervention.

**Hardware Target**: 48GB M4 Mac with local open-source models (Qwen 2.5-Coder variants)

**Core Value Proposition**: Build a "second brain" that persists knowledge across sessions, enabling true autonomous self-improvement.

---

## 🏗️ Architecture Overview

### The Trinity Agents

```
┌─────────────────────────────────────────────────────────────┐
│                     TRINITY PROTOCOL                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │ AUDITLEARN   │─────>│    PLAN      │─────>│ EXECUTE  │  │
│  │              │      │              │      │          │  │
│  │ • Monitor    │      │ • Strategize │      │ • Route  │  │
│  │ • Detect     │      │ • Prioritize │      │ • Run    │  │
│  │ • Learn      │      │ • Create     │      │ • Verify │  │
│  └──────┬───────┘      └──────────────┘      └────┬─────┘  │
│         │                                           │        │
│         │          ┌──────────────────┐            │        │
│         └─────────>│  Message Bus     │<───────────┘        │
│                    │  (Telemetry)     │                     │
│                    └──────────────────┘                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Existing Specialized Agents (Unchanged)        │ │
│  │  AgencyCodeAgent, PlannerAgent, AuditorAgent, etc.    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Hybrid Cloud/Local Models**: Use local models for pattern detection, cloud for strategic reasoning
2. **Orchestrate, Don't Replace**: Trinity coordinates existing agents, doesn't rebuild them
3. **Persistent Learning**: All patterns, learnings, and history stored locally (SQLite + FAISS)
4. **Message-Driven**: Async message bus decouples agents, enables observability
5. **Incremental Value**: Each phase delivers immediate benefits

---

## 📅 6-Week Implementation Timeline

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Build the persistent "second brain" and message infrastructure

### Phase 2: AUDITLEARN Agent (Weeks 3-4)
**Goal**: Continuous monitoring and pattern detection with local models

### Phase 3: Orchestration (Weeks 5-6)
**Goal**: PLAN and EXECUTE agents as meta-orchestrators

---

## 🔨 Detailed Implementation Plan

## Week 1: Persistent Storage + Message Bus

### 1.1 Persistent Learning Store

**File**: `trinity_protocol/persistent_store.py`

**Purpose**: Local, persistent storage for patterns, learnings, and embeddings

**Technology Stack**:
- SQLite: Metadata, pattern success rates, timestamps, relationships
- FAISS: Fast similarity search for semantic pattern matching (50k+ vectors)
- sentence-transformers: Local embeddings (`all-MiniLM-L6-v2` model)

**Schema Design**:

```python
# SQLite Tables
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT NOT NULL,  -- 'failure', 'opportunity', 'user_intent'
    content TEXT NOT NULL,
    confidence FLOAT,
    success_rate FLOAT DEFAULT 0.5,
    times_seen INTEGER DEFAULT 1,
    times_successful INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    last_seen TIMESTAMP,
    embedding_id INTEGER  -- Reference to FAISS index
);

CREATE TABLE pattern_applications (
    id INTEGER PRIMARY KEY,
    pattern_id INTEGER,
    task_description TEXT,
    outcome TEXT,  -- 'success', 'failure', 'partial'
    details JSON,
    applied_at TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES patterns(id)
);

CREATE TABLE learning_sessions (
    id INTEGER PRIMARY KEY,
    session_type TEXT,  -- 'audit', 'plan', 'execute', 'manual'
    patterns_extracted INTEGER,
    improvements_made INTEGER,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    metadata JSON
);
```

**Implementation**:

```python
"""
Trinity Protocol: Persistent Learning Store

Provides local, persistent storage for patterns, learnings, and embeddings.
Combines SQLite for structured data with FAISS for semantic similarity search.
"""

import sqlite3
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer


class TrinityStore:
    """
    Persistent storage for Trinity Protocol learning and patterns.
    
    Features:
    - SQLite for metadata and relationships
    - FAISS for fast similarity search (50k+ vectors in ms)
    - Local embeddings (no API calls)
    - Automatic pattern lifecycle management
    """
    
    def __init__(
        self, 
        db_path: str = "trinity.db",
        faiss_index_path: str = "trinity_embeddings.faiss",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """Initialize Trinity persistent store."""
        self.db_path = Path(db_path)
        self.faiss_path = Path(faiss_index_path)
        
        # Initialize SQLite
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        
        # Initialize FAISS index
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        if self.faiss_path.exists():
            self.faiss_index = faiss.read_index(str(self.faiss_path))
        else:
            self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Initialize local embedding model
        self.embedder = SentenceTransformer(embedding_model)
        
    def _create_tables(self):
        """Create SQLite schema."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence FLOAT NOT NULL,
                success_rate FLOAT DEFAULT 0.5,
                times_seen INTEGER DEFAULT 1,
                times_successful INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                embedding_id INTEGER UNIQUE,
                metadata JSON
            );
            
            CREATE TABLE IF NOT EXISTS pattern_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER NOT NULL,
                task_description TEXT NOT NULL,
                outcome TEXT NOT NULL,
                details JSON,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pattern_id) REFERENCES patterns(id)
            );
            
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                patterns_extracted INTEGER DEFAULT 0,
                improvements_made INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                metadata JSON
            );
            
            CREATE INDEX IF NOT EXISTS idx_pattern_type ON patterns(pattern_type);
            CREATE INDEX IF NOT EXISTS idx_confidence ON patterns(confidence);
            CREATE INDEX IF NOT EXISTS idx_success_rate ON patterns(success_rate);
        """)
        self.conn.commit()
    
    def store_pattern(
        self, 
        pattern_type: str,
        content: str,
        confidence: float,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Store a new pattern with semantic embedding.
        
        Args:
            pattern_type: Type of pattern (failure, opportunity, user_intent)
            content: Pattern description/signature
            confidence: Detection confidence (0-1)
            metadata: Additional context
            
        Returns:
            Pattern ID
        """
        # Generate embedding
        embedding = self.embedder.encode(content, convert_to_numpy=True)
        
        # Check for similar existing patterns
        similar = self.find_similar_patterns(content, threshold=0.9, limit=1)
        if similar:
            # Update existing pattern instead of creating duplicate
            return self._update_pattern_seen(similar[0]['id'])
        
        # Add to FAISS index
        embedding_id = self.faiss_index.ntotal
        self.faiss_index.add(np.array([embedding], dtype=np.float32))
        
        # Store in SQLite
        cursor = self.conn.execute("""
            INSERT INTO patterns 
            (pattern_type, content, confidence, embedding_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            pattern_type,
            content,
            confidence,
            embedding_id,
            json.dumps(metadata or {})
        ))
        self.conn.commit()
        
        # Save FAISS index
        faiss.write_index(self.faiss_index, str(self.faiss_path))
        
        return cursor.lastrowid
    
    def find_similar_patterns(
        self, 
        query: str, 
        threshold: float = 0.8,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar patterns using semantic search.
        
        Args:
            query: Query text to match against
            threshold: Similarity threshold (0-1, higher = more similar)
            limit: Max results to return
            
        Returns:
            List of similar patterns with metadata
        """
        if self.faiss_index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedder.encode(query, convert_to_numpy=True)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        # Search FAISS
        distances, indices = self.faiss_index.search(query_embedding, limit)
        
        # Convert distances to similarity scores (L2 distance -> similarity)
        # Lower distance = higher similarity
        max_distance = 2.0  # Normalized embeddings have max distance ~2
        similarities = 1.0 - (distances[0] / max_distance)
        
        # Fetch matching patterns from SQLite
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if similarity >= threshold and idx >= 0:
                row = self.conn.execute(
                    "SELECT * FROM patterns WHERE embedding_id = ?",
                    (int(idx),)
                ).fetchone()
                if row:
                    pattern = dict(row)
                    pattern['similarity'] = float(similarity)
                    pattern['metadata'] = json.loads(pattern.get('metadata', '{}'))
                    results.append(pattern)
        
        return results
    
    def _update_pattern_seen(self, pattern_id: int) -> int:
        """Update pattern last_seen and times_seen counters."""
        self.conn.execute("""
            UPDATE patterns 
            SET times_seen = times_seen + 1,
                last_seen = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (pattern_id,))
        self.conn.commit()
        return pattern_id
    
    def record_pattern_application(
        self,
        pattern_id: int,
        task_description: str,
        outcome: str,
        details: Optional[Dict] = None
    ):
        """Record when a pattern was applied and the outcome."""
        self.conn.execute("""
            INSERT INTO pattern_applications
            (pattern_id, task_description, outcome, details)
            VALUES (?, ?, ?, ?)
        """, (
            pattern_id,
            task_description,
            outcome,
            json.dumps(details or {})
        ))
        
        # Update pattern success rate
        if outcome == "success":
            self.conn.execute("""
                UPDATE patterns 
                SET times_successful = times_successful + 1,
                    success_rate = CAST(times_successful + 1 AS FLOAT) / times_seen
                WHERE id = ?
            """, (pattern_id,))
        else:
            # Recalculate success rate
            self.conn.execute("""
                UPDATE patterns 
                SET success_rate = CAST(times_successful AS FLOAT) / times_seen
                WHERE id = ?
            """, (pattern_id,))
        
        self.conn.commit()
    
    def prune_low_performing_patterns(self, min_success_rate: float = 0.3):
        """Remove patterns with low success rates after sufficient trials."""
        self.conn.execute("""
            DELETE FROM patterns
            WHERE success_rate < ?
            AND times_seen >= 5
        """, (min_success_rate,))
        self.conn.commit()
    
    def get_top_patterns(
        self, 
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.7,
        limit: int = 20
    ) -> List[Dict]:
        """Get highest confidence patterns."""
        query = """
            SELECT * FROM patterns
            WHERE confidence >= ?
        """
        params = [min_confidence]
        
        if pattern_type:
            query += " AND pattern_type = ?"
            params.append(pattern_type)
        
        query += " ORDER BY confidence DESC, success_rate DESC LIMIT ?"
        params.append(limit)
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def get_pattern_stats(self) -> Dict:
        """Get overall pattern statistics."""
        stats = self.conn.execute("""
            SELECT 
                COUNT(*) as total_patterns,
                AVG(confidence) as avg_confidence,
                AVG(success_rate) as avg_success_rate,
                SUM(times_seen) as total_applications
            FROM patterns
        """).fetchone()
        
        by_type = self.conn.execute("""
            SELECT pattern_type, COUNT(*) as count
            FROM patterns
            GROUP BY pattern_type
        """).fetchall()
        
        return {
            **dict(stats),
            'patterns_by_type': {row['pattern_type']: row['count'] for row in by_type}
        }
    
    def close(self):
        """Close connections and save state."""
        self.conn.close()
        faiss.write_index(self.faiss_index, str(self.faiss_path))
```

**Tests**: `tests/trinity_protocol/test_persistent_store.py`

```python
import pytest
from trinity_protocol.persistent_store import TrinityStore
import tempfile
from pathlib import Path


@pytest.fixture
def store():
    """Create temporary store for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_trinity.db"
        faiss_path = Path(tmpdir) / "test_faiss.idx"
        store = TrinityStore(str(db_path), str(faiss_path))
        yield store
        store.close()


def test_store_and_retrieve_pattern(store):
    """Test basic pattern storage and retrieval."""
    pattern_id = store.store_pattern(
        pattern_type="failure",
        content="Test timeout in test_planner_agent.py",
        confidence=0.9,
        metadata={"file": "test_planner_agent.py", "error_type": "timeout"}
    )
    
    assert pattern_id > 0
    
    # Find similar pattern
    results = store.find_similar_patterns("timeout in planner test", threshold=0.7)
    assert len(results) > 0
    assert results[0]['pattern_type'] == "failure"


def test_duplicate_pattern_handling(store):
    """Test that similar patterns are merged, not duplicated."""
    id1 = store.store_pattern("failure", "Import error in module X", 0.8)
    id2 = store.store_pattern("failure", "Import error in module X", 0.85)
    
    # Should be same ID (merged)
    assert id1 == id2


def test_pattern_application_tracking(store):
    """Test success rate tracking."""
    pattern_id = store.store_pattern("opportunity", "Refactor duplicated code", 0.8)
    
    # Record successful application
    store.record_pattern_application(pattern_id, "Refactor auth module", "success")
    
    # Check success rate updated
    pattern = store.conn.execute(
        "SELECT success_rate FROM patterns WHERE id = ?", (pattern_id,)
    ).fetchone()
    assert pattern['success_rate'] > 0.5


def test_semantic_similarity_search(store):
    """Test FAISS semantic search."""
    # Store related patterns
    store.store_pattern("failure", "NoneType error in database connection", 0.9)
    store.store_pattern("failure", "Null pointer in DB query", 0.85)
    store.store_pattern("opportunity", "Add logging to API endpoints", 0.7)
    
    # Search for related pattern
    results = store.find_similar_patterns("database null error", threshold=0.6)
    
    # Should find database-related failures, not logging opportunity
    assert len(results) >= 2
    assert all(r['pattern_type'] == 'failure' for r in results[:2])
```

---

### 1.2 Message Bus

**File**: `trinity_protocol/message_bus.py`

**Purpose**: Async message queue for inter-agent communication with persistence

**Technology**: SQLite-backed async queue (persistent across restarts)

**Channels**:
- `improvement_queue`: AUDITLEARN → PLAN
- `execution_queue`: PLAN → EXECUTE  
- `telemetry_stream`: EXECUTE → AUDITLEARN (closes the loop)
- `error_alerts`: Any agent → AUDITLEARN (for immediate attention)

**Implementation**:

```python
"""
Trinity Protocol: Message Bus

Persistent, async message queue for inter-agent communication.
Uses SQLite for persistence (survives restarts) with async polling.
"""

import asyncio
import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional, AsyncIterator, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Message:
    """Message structure for Trinity bus."""
    channel: str
    data: Dict
    priority: MessagePriority = MessagePriority.NORMAL
    source_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            **asdict(self),
            'priority': self.priority.value
        }


class TrinityMessageBus:
    """
    Persistent async message bus for Trinity Protocol.
    
    Features:
    - SQLite persistence (survives restarts)
    - Priority queues
    - Async pub/sub
    - Message correlation (track request → response)
    - Queryable history for debugging
    """
    
    def __init__(self, db_path: str = "trinity_messages.db"):
        """Initialize message bus."""
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        
        # In-memory subscribers for async delivery
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._running = False
    
    def _create_tables(self):
        """Create message queue schema."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                data JSON NOT NULL,
                priority INTEGER DEFAULT 1,
                source_agent TEXT,
                correlation_id TEXT,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                processed_by TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_channel_unprocessed 
            ON messages(channel, processed_at) 
            WHERE processed_at IS NULL;
            
            CREATE INDEX IF NOT EXISTS idx_priority 
            ON messages(priority DESC, created_at ASC);
            
            CREATE INDEX IF NOT EXISTS idx_correlation 
            ON messages(correlation_id);
        """)
        self.conn.commit()
    
    async def publish(self, message: Message):
        """
        Publish message to a channel.
        
        Args:
            message: Message to publish
        """
        # Store in SQLite
        cursor = self.conn.execute("""
            INSERT INTO messages 
            (channel, data, priority, source_agent, correlation_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message.channel,
            json.dumps(message.data),
            message.priority.value,
            message.source_agent,
            message.correlation_id,
            json.dumps(message.metadata or {})
        ))
        self.conn.commit()
        message_id = cursor.lastrowid
        
        # Deliver to in-memory subscribers (fast path)
        if message.channel in self._subscribers:
            msg_dict = {**message.to_dict(), 'id': message_id}
            for queue in self._subscribers[message.channel]:
                try:
                    queue.put_nowait(msg_dict)
                except asyncio.QueueFull:
                    pass  # Subscriber too slow, will catch up from DB
    
    async def subscribe(
        self, 
        channel: str,
        batch_size: int = 10,
        poll_interval: float = 1.0
    ) -> AsyncIterator[Dict]:
        """
        Subscribe to a channel (async generator).
        
        Args:
            channel: Channel name to subscribe to
            batch_size: Max messages per poll
            poll_interval: Seconds between polls
            
        Yields:
            Message dictionaries
        """
        # Register in-memory queue for fast delivery
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        queue = asyncio.Queue(maxsize=100)
        self._subscribers[channel].append(queue)
        
        try:
            while self._running:
                # Try in-memory queue first (fast path)
                try:
                    msg = queue.get_nowait()
                    yield msg
                    continue
                except asyncio.QueueEmpty:
                    pass
                
                # Fall back to polling SQLite (slow path for catch-up)
                messages = self.conn.execute("""
                    SELECT * FROM messages
                    WHERE channel = ? AND processed_at IS NULL
                    ORDER BY priority DESC, created_at ASC
                    LIMIT ?
                """, (channel, batch_size)).fetchall()
                
                for row in messages:
                    msg = dict(row)
                    msg['data'] = json.loads(msg['data'])
                    msg['metadata'] = json.loads(msg.get('metadata', '{}'))
                    yield msg
                    
                    # Mark as processed
                    self.conn.execute("""
                        UPDATE messages 
                        SET processed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (msg['id'],))
                    self.conn.commit()
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                
        finally:
            # Cleanup
            self._subscribers[channel].remove(queue)
    
    def get_unprocessed_count(self, channel: str) -> int:
        """Get count of unprocessed messages in a channel."""
        row = self.conn.execute("""
            SELECT COUNT(*) as count FROM messages
            WHERE channel = ? AND processed_at IS NULL
        """, (channel,)).fetchone()
        return row['count']
    
    def get_recent_messages(
        self, 
        channel: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get recent messages (for debugging/monitoring)."""
        query = "SELECT * FROM messages"
        params = []
        
        if channel:
            query += " WHERE channel = ?"
            params.append(channel)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def purge_old_messages(self, days: int = 7):
        """Delete processed messages older than N days."""
        self.conn.execute("""
            DELETE FROM messages
            WHERE processed_at IS NOT NULL
            AND processed_at < datetime('now', ? || ' days')
        """, (f'-{days}',))
        self.conn.commit()
    
    async def start(self):
        """Start the message bus."""
        self._running = True
    
    async def stop(self):
        """Stop the message bus."""
        self._running = False
        # Wait for subscribers to finish
        await asyncio.sleep(0.1)
    
    def close(self):
        """Close database connection."""
        self.conn.close()
```

**Tests**: `tests/trinity_protocol/test_message_bus.py`

```python
import pytest
import asyncio
from trinity_protocol.message_bus import (
    TrinityMessageBus, Message, MessagePriority
)
import tempfile
from pathlib import Path


@pytest.fixture
async def bus():
    """Create temporary message bus for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_messages.db"
        bus = TrinityMessageBus(str(db_path))
        await bus.start()
        yield bus
        await bus.stop()
        bus.close()


@pytest.mark.asyncio
async def test_publish_and_subscribe(bus):
    """Test basic pub/sub functionality."""
    # Publish message
    msg = Message(
        channel="test_channel",
        data={"event": "test_event", "value": 42},
        source_agent="test_agent"
    )
    await bus.publish(msg)
    
    # Subscribe and receive
    received = []
    async def subscriber():
        async for message in bus.subscribe("test_channel"):
            received.append(message)
            if len(received) >= 1:
                break
    
    task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.5)
    task.cancel()
    
    assert len(received) == 1
    assert received[0]['data']['value'] == 42


@pytest.mark.asyncio
async def test_persistence_across_restart(bus):
    """Test messages persist across bus restart."""
    # Publish message
    await bus.publish(Message(
        channel="persistent_test",
        data={"important": "data"}
    ))
    
    # Stop and restart bus
    await bus.stop()
    bus.close()
    
    # Create new bus instance with same DB
    new_bus = TrinityMessageBus(bus.db_path)
    await new_bus.start()
    
    # Should still have unprocessed message
    count = new_bus.get_unprocessed_count("persistent_test")
    assert count == 1
    
    await new_bus.stop()
    new_bus.close()


@pytest.mark.asyncio
async def test_priority_ordering(bus):
    """Test messages are delivered by priority."""
    # Publish messages with different priorities
    await bus.publish(Message("priority_test", {"order": 1}, MessagePriority.LOW))
    await bus.publish(Message("priority_test", {"order": 2}, MessagePriority.CRITICAL))
    await bus.publish(Message("priority_test", {"order": 3}, MessagePriority.HIGH))
    
    # Subscribe and collect
    received = []
    async def subscriber():
        async for msg in bus.subscribe("priority_test"):
            received.append(msg['data']['order'])
            if len(received) >= 3:
                break
    
    task = asyncio.create_task(subscriber())
    await asyncio.sleep(1.0)
    task.cancel()
    
    # Should receive in priority order: CRITICAL, HIGH, LOW
    assert received == [2, 3, 1]
```

---

## Week 2: Local Model Integration

### 2.1 Local Model Server

**File**: `shared/local_model_server.py`

**Purpose**: Adapter for local model serving (Ollama, llama.cpp, vLLM)

**Implementation**:

```python
"""
Local Model Server for Trinity Protocol

Provides unified interface to local LLM serving backends:
- Ollama (primary): Easy setup, good performance
- llama.cpp: Lightweight fallback
- vLLM: High-throughput batching (future)
"""

import os
from typing import Optional, Dict, List
from enum import Enum
import httpx
from dataclasses import dataclass


class ModelProvider(Enum):
    """Supported local model providers."""
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"
    VLLM = "vllm"


@dataclass
class ModelConfig:
    """Configuration for a local model."""
    name: str
    provider: ModelProvider
    context_length: int = 8192
    temperature: float = 0.7
    max_tokens: int = 2048


# Trinity model registry
TRINITY_MODELS = {
    "auditlearn": ModelConfig(
        name="qwen2.5-coder:7b-q3",
        provider=ModelProvider.OLLAMA,
        context_length=8192,
        temperature=0.3,  # Lower for deterministic pattern detection
        max_tokens=512    # Short outputs for pattern detection
    ),
    "plan_simple": ModelConfig(
        name="qwen2.5-coder:14b-q4",
        provider=ModelProvider.OLLAMA,
        context_length=16384,
        temperature=0.7,
        max_tokens=2048
    ),
    "execute": ModelConfig(
        name="qwen2.5-coder:14b-q4",
        provider=ModelProvider.OLLAMA,
        context_length=8192,
        temperature=0.5,
        max_tokens=2048
    ),
}


class LocalModelServer:
    """
    Unified interface to local model serving.
    
    Supports fallback chain:
    1. Try local model
    2. On error, try alternative local model
    3. On critical failure, can escalate to cloud (if fallback enabled)
    """
    
    def __init__(
        self,
        provider: ModelProvider = ModelProvider.OLLAMA,
        base_url: str = "http://localhost:11434",
        enable_cloud_fallback: bool = True
    ):
        """Initialize local model server."""
        self.provider = provider
        self.base_url = base_url
        self.enable_cloud_fallback = enable_cloud_fallback
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)
    
    async def generate(
        self,
        model_key: str,
        prompt: str,
        **kwargs
    ) -> str:
        """
        Generate text using local model.
        
        Args:
            model_key: Key in TRINITY_MODELS registry
            prompt: Input prompt
            **kwargs: Override model config params
            
        Returns:
            Generated text
        """
        config = TRINITY_MODELS.get(model_key)
        if not config:
            raise ValueError(f"Unknown model key: {model_key}")
        
        if self.provider == ModelProvider.OLLAMA:
            return await self._generate_ollama(config, prompt, **kwargs)
        else:
            raise NotImplementedError(f"Provider {self.provider} not yet supported")
    
    async def _generate_ollama(
        self,
        config: ModelConfig,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate using Ollama."""
        payload = {
            "model": config.name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", config.temperature),
                "num_predict": kwargs.get("max_tokens", config.max_tokens),
            }
        }
        
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            return result["response"]
        except Exception as e:
            if self.enable_cloud_fallback:
                # Log and escalate to cloud
                print(f"Local model failed: {e}, escalating to cloud")
                return await self._fallback_to_cloud(prompt, **kwargs)
            raise
    
    async def _fallback_to_cloud(self, prompt: str, **kwargs) -> str:
        """Fallback to cloud model (if enabled)."""
        # Import cloud client
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective fallback
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048)
        )
        return response.choices[0].message.content
    
    async def health_check(self) -> bool:
        """Check if local model server is responding."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available local models."""
        if self.provider == ModelProvider.OLLAMA:
            response = await self.client.get("/api/tags")
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        return []
```

### 2.2 Enhanced Model Policy

**File**: `shared/model_policy.py` (enhance existing)

**Purpose**: Add hybrid routing logic (local vs cloud)

**Enhancement**:

```python
"""
Enhanced Model Policy with Local/Cloud Hybrid Routing
"""

import os
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class TaskComplexity:
    """Assess task complexity for routing."""
    score: float  # 0-1, higher = more complex
    reasoning_required: bool
    multi_step: bool
    strategic: bool


def assess_task_complexity(task_description: str) -> TaskComplexity:
    """
    Assess task complexity to route local vs cloud.
    
    Local models (Qwen 2.5-Coder 7B-14B): Good for:
    - Pattern detection
    - Code completion
    - Simple refactoring
    - Test generation
    - Documentation
    
    Cloud models (GPT-4/Claude): Required for:
    - Architecture decisions
    - Complex multi-step reasoning
    - Strategic planning
    - Nuanced debugging
    """
    keywords_strategic = [
        "architecture", "design", "refactor plan", "strategy",
        "trade-off", "decision", "approach", "should we"
    ]
    keywords_complex = [
        "debug", "why", "explain", "analyze", "investigate",
        "performance", "optimize"
    ]
    
    text_lower = task_description.lower()
    
    # Strategic tasks → always cloud
    if any(kw in text_lower for kw in keywords_strategic):
        return TaskComplexity(
            score=0.9,
            reasoning_required=True,
            multi_step=True,
            strategic=True
        )
    
    # Complex analysis → cloud
    if any(kw in text_lower for kw in keywords_complex):
        return TaskComplexity(
            score=0.7,
            reasoning_required=True,
            multi_step=True,
            strategic=False
        )
    
    # Simple tasks → local
    return TaskComplexity(
        score=0.3,
        reasoning_required=False,
        multi_step=False,
        strategic=False
    )


def agent_model(
    agent_key: str, 
    task_description: Optional[str] = None,
    force_local: bool = False,
    force_cloud: bool = False
) -> str:
    """
    Select model (local or cloud) based on agent and task.
    
    Args:
        agent_key: Agent identifier
        task_description: Task to perform (for complexity assessment)
        force_local: Force local model
        force_cloud: Force cloud model
        
    Returns:
        Model identifier (with provider prefix if local)
    """
    # Environment overrides
    if os.getenv("ENABLE_LOCAL_MODE") == "true" and not force_cloud:
        from shared.local_model_server import TRINITY_MODELS
        if agent_key in TRINITY_MODELS:
            return f"local:{agent_key}"
    
    # Task complexity routing
    if task_description and not force_local and not force_cloud:
        complexity = assess_task_complexity(task_description)
        
        # High complexity → cloud
        if complexity.score > 0.7 or complexity.strategic:
            return DEFAULTS.get(agent_key, DEFAULT_GLOBAL)
        
        # Medium complexity → try local, allow escalation
        if complexity.score > 0.5:
            if os.getenv("ENABLE_CLOUD_FALLBACK") == "true":
                return f"local:{agent_key}:fallback"
            return DEFAULTS.get(agent_key, DEFAULT_GLOBAL)
        
        # Low complexity → local
        if agent_key in ["auditlearn", "execute"]:
            return f"local:{agent_key}"
    
    # Default routing (existing logic)
    return DEFAULTS.get(agent_key, DEFAULT_GLOBAL)


# Existing code continues...
```

---

## Week 3-4: AUDITLEARN Agent

### 3.1 Pattern Detector

**File**: `trinity_protocol/pattern_detector.py`

**Purpose**: Lightweight pattern detection using local models

**Implementation**:

```python
"""
Trinity Protocol: Pattern Detector

Uses local Qwen 2.5-Coder for fast pattern detection.
Does NOT do complex reasoning - just signal detection.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from shared.local_model_server import LocalModelServer


@dataclass
class DetectedPattern:
    """A detected pattern from telemetry."""
    pattern_type: str  # 'failure', 'opportunity', 'user_intent'
    content: str
    confidence: float
    evidence: List[Dict]
    detected_at: datetime
    metadata: Dict


class PatternDetector:
    """
    Lightweight pattern detection using local models.
    
    Scans telemetry for known failure patterns, improvement opportunities,
    and user intent signals.
    """
    
    def __init__(self):
        """Initialize pattern detector."""
        self.model_server = LocalModelServer()
        self.pattern_library = self._load_pattern_library()
    
    def _load_pattern_library(self) -> Dict:
        """Load known patterns to look for."""
        return {
            "failures": [
                {"name": "flaky_test", "signature": ["test failed", "random", "sometimes"]},
                {"name": "timeout", "signature": ["timeout", "took too long", "exceeded"]},
                {"name": "import_error", "signature": ["import", "no module", "cannot import"]},
                {"name": "none_type", "signature": ["NoneType", "None has no attribute"]},
                {"name": "type_error", "signature": ["TypeError", "expected", "got"]},
            ],
            "opportunities": [
                {"name": "code_duplication", "signature": ["similar code", "repeated", "duplicate"]},
                {"name": "missing_tests", "signature": ["no tests", "untested", "no coverage"]},
                {"name": "type_safety", "signature": ["Dict[Any]", "Any", "untyped"]},
                {"name": "performance", "signature": ["slow", "performance", "optimization"]},
            ],
            "user_intents": [
                {"name": "feature_request", "signature": ["want", "need", "could you", "add"]},
                {"name": "recurring_topic", "signature": ["again", "still", "another"]},
                {"name": "frustration", "signature": ["why", "confusing", "difficult", "hard"]},
            ]
        }
    
    async def detect_patterns(
        self,
        events: List[Dict],
        min_confidence: float = 0.7
    ) -> List[DetectedPattern]:
        """
        Scan events for patterns.
        
        Args:
            events: List of telemetry events
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Group events by type for batch processing
        failures = [e for e in events if e.get('level') == 'error']
        logs = [e for e in events if e.get('type') == 'log']
        user_messages = [e for e in events if e.get('type') == 'user_message']
        
        # Detect failure patterns
        if failures:
            patterns.extend(await self._detect_failure_patterns(failures))
        
        # Detect opportunity patterns
        if logs:
            patterns.extend(await self._detect_opportunity_patterns(logs))
        
        # Detect user intent patterns
        if user_messages:
            patterns.extend(await self._detect_user_intent_patterns(user_messages))
        
        # Filter by confidence
        return [p for p in patterns if p.confidence >= min_confidence]
    
    async def _detect_failure_patterns(self, failures: List[Dict]) -> List[DetectedPattern]:
        """Detect failure patterns in error events."""
        patterns = []
        
        for failure_type in self.pattern_library["failures"]:
            matching_failures = []
            for event in failures:
                message = event.get("message", "").lower()
                if any(sig in message for sig in failure_type["signature"]):
                    matching_failures.append(event)
            
            if matching_failures:
                # Use local model for pattern characterization
                prompt = self._build_failure_prompt(failure_type, matching_failures)
                analysis = await self.model_server.generate("auditlearn", prompt)
                
                patterns.append(DetectedPattern(
                    pattern_type="failure",
                    content=f"{failure_type['name']}: {analysis}",
                    confidence=self._calculate_confidence(matching_failures),
                    evidence=matching_failures,
                    detected_at=datetime.now(),
                    metadata={"failure_type": failure_type["name"]}
                ))
        
        return patterns
    
    async def _detect_opportunity_patterns(self, logs: List[Dict]) -> List[DetectedPattern]:
        """Detect improvement opportunities."""
        patterns = []
        
        # Code duplication detection
        code_events = [e for e in logs if "code" in e.get("context", {})]
        if len(code_events) >= 3:
            # Check for similar code structures
            prompt = self._build_duplication_prompt(code_events)
            analysis = await self.model_server.generate("auditlearn", prompt, max_tokens=256)
            
            if "similar" in analysis.lower() or "duplicate" in analysis.lower():
                patterns.append(DetectedPattern(
                    pattern_type="opportunity",
                    content=f"Code duplication detected: {analysis}",
                    confidence=0.75,
                    evidence=code_events[:5],
                    detected_at=datetime.now(),
                    metadata={"opportunity_type": "code_duplication"}
                ))
        
        return patterns
    
    async def _detect_user_intent_patterns(self, messages: List[Dict]) -> List[DetectedPattern]:
        """Detect recurring user intents."""
        patterns = []
        
        # Group messages by topic using simple keyword extraction
        topics = {}
        for msg in messages:
            text = msg.get("content", "").lower()
            # Extract key phrases (nouns, verbs)
            phrases = self._extract_key_phrases(text)
            for phrase in phrases:
                if phrase not in topics:
                    topics[phrase] = []
                topics[phrase].append(msg)
        
        # Detect recurring topics (mentioned 3+ times)
        for topic, msgs in topics.items():
            if len(msgs) >= 3:
                prompt = f"""
                The user mentioned "{topic}" {len(msgs)} times recently.
                Messages: {[m['content'][:100] for m in msgs[:3]]}
                
                Is this a recurring intent or just coincidence? (one sentence)
                """
                analysis = await self.model_server.generate("auditlearn", prompt, max_tokens=100)
                
                patterns.append(DetectedPattern(
                    pattern_type="user_intent",
                    content=f"Recurring topic '{topic}': {analysis}",
                    confidence=min(0.95, 0.6 + len(msgs) * 0.1),
                    evidence=msgs,
                    detected_at=datetime.now(),
                    metadata={"topic": topic, "occurrences": len(msgs)}
                ))
        
        return patterns
    
    def _build_failure_prompt(self, failure_type: Dict, failures: List[Dict]) -> str:
        """Build prompt for failure pattern analysis."""
        return f"""
        Analyze these {failure_type['name']} errors:
        
        {[f['message'][:200] for f in failures[:3]]}
        
        In 1 sentence, describe the root cause pattern:
        """
    
    def _build_duplication_prompt(self, code_events: List[Dict]) -> str:
        """Build prompt for code duplication detection."""
        return f"""
        Check if these code snippets are similar/duplicated:
        
        {[e.get('context', {}).get('code', '')[:100] for e in code_events[:3]]}
        
        Answer in 1 sentence: Are these similar? Where?
        """
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text (simple heuristic)."""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        words = re.findall(r'\b\w{4,}\b', text.lower())
        return [w for w in words if w not in stop_words][:5]
    
    def _calculate_confidence(self, evidence: List[Dict]) -> float:
        """Calculate confidence score based on evidence."""
        base_confidence = 0.6
        # More occurrences = higher confidence
        confidence = min(0.95, base_confidence + len(evidence) * 0.05)
        return confidence
```

### 3.2 AUDITLEARN Agent

**File**: `trinity_protocol/auditlearn_agent.py`

**Purpose**: Continuous monitoring and pattern detection

**Implementation**:

```python
"""
Trinity Protocol: AUDITLEARN Agent

Continuously monitors telemetry, detects patterns, learns, and publishes
findings to the message bus for PLAN agent to act on.

This agent does NOT take action - it only observes and learns.
"""

import asyncio
from typing import List, Dict
from datetime import datetime, timedelta
from trinity_protocol.persistent_store import TrinityStore
from trinity_protocol.message_bus import TrinityMessageBus, Message, MessagePriority
from trinity_protocol.pattern_detector import PatternDetector, DetectedPattern
from core.telemetry import get_telemetry_events


class AuditLearnAgent:
    """
    AUDITLEARN: The Observer and Learner
    
    Responsibilities:
    1. Monitor telemetry continuously (30s cycle)
    2. Detect patterns using local model
    3. Store patterns in persistent store
    4. Publish findings to improvement_queue
    5. Learn from execution outcomes
    
    Does NOT:
    - Take direct action on findings
    - Make strategic decisions
    - Execute fixes
    """
    
    def __init__(
        self,
        store: TrinityStore,
        message_bus: TrinityMessageBus,
        scan_interval: float = 30.0
    ):
        """Initialize AUDITLEARN agent."""
        self.store = store
        self.message_bus = message_bus
        self.scan_interval = scan_interval
        self.pattern_detector = PatternDetector()
        self.running = False
        self.last_scan_time = datetime.now()
    
    async def run_forever(self):
        """Main event loop - runs indefinitely."""
        self.running = True
        print("🔍 AUDITLEARN: Starting continuous monitoring...")
        
        # Start parallel tasks
        tasks = [
            self.monitoring_loop(),
            self.learning_loop(),
            self.feedback_loop()
        ]
        await asyncio.gather(*tasks)
    
    async def monitoring_loop(self):
        """
        Continuous monitoring cycle (30s).
        
        Flow:
        1. Read telemetry from last 30s
        2. Detect patterns using local model
        3. Store high-confidence patterns
        4. Publish improvements to message bus
        """
        while self.running:
            try:
                # Fetch recent telemetry
                events = self._fetch_recent_telemetry()
                
                if events:
                    # Detect patterns
                    patterns = await self.pattern_detector.detect_patterns(
                        events,
                        min_confidence=0.7
                    )
                    
                    # Process detected patterns
                    for pattern in patterns:
                        await self._process_pattern(pattern)
                
                self.last_scan_time = datetime.now()
                
            except Exception as e:
                print(f"❌ AUDITLEARN: Error in monitoring loop: {e}")
            
            # Wait for next cycle
            await asyncio.sleep(self.scan_interval)
    
    async def learning_loop(self):
        """
        Continuous learning from stored patterns (5 min cycle).
        
        Flow:
        1. Analyze pattern success rates
        2. Prune low-performing patterns
        3. Identify high-value patterns
        4. Update pattern confidence scores
        """
        while self.running:
            try:
                # Prune low-performing patterns
                self.store.prune_low_performing_patterns(min_success_rate=0.3)
                
                # Get statistics
                stats = self.store.get_pattern_stats()
                print(f"📊 AUDITLEARN: {stats['total_patterns']} patterns, "
                      f"avg confidence: {stats['avg_confidence']:.2f}")
                
            except Exception as e:
                print(f"❌ AUDITLEARN: Error in learning loop: {e}")
            
            # Wait 5 minutes between learning cycles
            await asyncio.sleep(300)
    
    async def feedback_loop(self):
        """
        Listen to execution outcomes via telemetry_stream.
        
        Flow:
        1. Subscribe to telemetry_stream (EXECUTE → AUDITLEARN)
        2. Update pattern success rates based on outcomes
        3. Learn from successes and failures
        """
        async for message in self.message_bus.subscribe("telemetry_stream"):
            try:
                outcome = message['data']
                
                # If execution referenced a pattern, update it
                if 'pattern_id' in outcome:
                    self.store.record_pattern_application(
                        pattern_id=outcome['pattern_id'],
                        task_description=outcome['task'],
                        outcome=outcome['result'],  # 'success' or 'failure'
                        details=outcome.get('details')
                    )
                    print(f"📝 AUDITLEARN: Learned from pattern {outcome['pattern_id']} "
                          f"→ {outcome['result']}")
                
            except Exception as e:
                print(f"❌ AUDITLEARN: Error in feedback loop: {e}")
    
    async def _process_pattern(self, pattern: DetectedPattern):
        """Process a detected pattern."""
        # Store in persistent store
        pattern_id = self.store.store_pattern(
            pattern_type=pattern.pattern_type,
            content=pattern.content,
            confidence=pattern.confidence,
            metadata=pattern.metadata
        )
        
        print(f"🔍 AUDITLEARN: Detected {pattern.pattern_type} pattern "
              f"(confidence: {pattern.confidence:.2f})")
        
        # Publish to improvement queue if high confidence
        if pattern.confidence >= 0.8:
            await self._publish_improvement(pattern_id, pattern)
    
    async def _publish_improvement(self, pattern_id: int, pattern: DetectedPattern):
        """Publish improvement opportunity to message bus."""
        priority = MessagePriority.CRITICAL if pattern.pattern_type == "failure" else MessagePriority.NORMAL
        
        message = Message(
            channel="improvement_queue",
            data={
                "pattern_id": pattern_id,
                "pattern_type": pattern.pattern_type,
                "content": pattern.content,
                "confidence": pattern.confidence,
                "evidence_count": len(pattern.evidence),
                "detected_at": pattern.detected_at.isoformat()
            },
            priority=priority,
            source_agent="auditlearn"
        )
        
        await self.message_bus.publish(message)
        print(f"📤 AUDITLEARN: Published improvement to queue (pattern_id: {pattern_id})")
    
    def _fetch_recent_telemetry(self) -> List[Dict]:
        """Fetch telemetry events since last scan."""
        try:
            # Get events from last scan_interval seconds
            cutoff = self.last_scan_time - timedelta(seconds=self.scan_interval)
            events = get_telemetry_events(since=cutoff)
            return events
        except Exception as e:
            print(f"⚠️  AUDITLEARN: Could not fetch telemetry: {e}")
            return []
    
    async def stop(self):
        """Stop the agent gracefully."""
        print("🛑 AUDITLEARN: Stopping...")
        self.running = False
```

---

## Week 4: Dashboard & CLI

### 4.1 CLI Interface

**File**: `trinity_protocol/cli.py`

**Purpose**: Command-line interface for Trinity control

**Implementation**:

```python
"""
Trinity Protocol: CLI Interface

Command-line tool for monitoring and controlling Trinity Protocol.
"""

import click
import asyncio
from pathlib import Path
from trinity_protocol.persistent_store import TrinityStore
from trinity_protocol.message_bus import TrinityMessageBus
from rich.console import Console
from rich.table import Table
from rich import print as rprint


console = Console()


@click.group()
def cli():
    """Trinity Protocol CLI - Control your autonomous agents."""
    pass


@cli.command()
def status():
    """Show Trinity Protocol status."""
    store = TrinityStore()
    bus = TrinityMessageBus()
    
    # Get statistics
    stats = store.get_pattern_stats()
    
    # Create status table
    table = Table(title="Trinity Protocol Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    table.add_row(
        "AUDITLEARN",
        "✅ Running",
        f"Scanned: last 30s"
    )
    table.add_row(
        "Patterns",
        f"{stats['total_patterns']} stored",
        f"Avg confidence: {stats.get('avg_confidence', 0):.2f}"
    )
    table.add_row(
        "Message Bus",
        "✅ Connected",
        f"{bus.get_unprocessed_count('improvement_queue')} in queue"
    )
    
    console.print(table)
    
    store.close()
    bus.close()


@cli.command()
@click.option('--type', '-t', help='Filter by pattern type')
@click.option('--limit', '-l', default=20, help='Max patterns to show')
def patterns(type, limit):
    """List detected patterns."""
    store = TrinityStore()
    
    patterns = store.get_top_patterns(
        pattern_type=type,
        min_confidence=0.6,
        limit=limit
    )
    
    # Create patterns table
    table = Table(title=f"Top {limit} Patterns")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Content", style="white", max_width=60)
    table.add_column("Confidence", style="green")
    table.add_column("Success Rate", style="yellow")
    table.add_column("Times Seen", style="magenta")
    
    for p in patterns:
        table.add_row(
            str(p['id']),
            p['pattern_type'],
            p['content'][:57] + "..." if len(p['content']) > 60 else p['content'],
            f"{p['confidence']:.2f}",
            f"{p['success_rate']:.2f}",
            str(p['times_seen'])
        )
    
    console.print(table)
    store.close()


@cli.command()
@click.argument('pattern_id', type=int)
def trace(pattern_id):
    """Trace pattern history and applications."""
    store = TrinityStore()
    
    # Get pattern details
    pattern = store.conn.execute(
        "SELECT * FROM patterns WHERE id = ?",
        (pattern_id,)
    ).fetchone()
    
    if not pattern:
        console.print(f"[red]Pattern {pattern_id} not found[/red]")
        return
    
    # Show pattern details
    rprint(f"\n[bold cyan]Pattern {pattern_id}:[/bold cyan]")
    rprint(f"  Type: {pattern['pattern_type']}")
    rprint(f"  Content: {pattern['content']}")
    rprint(f"  Confidence: {pattern['confidence']:.2f}")
    rprint(f"  Success Rate: {pattern['success_rate']:.2f}")
    rprint(f"  Times Seen: {pattern['times_seen']}")
    
    # Show applications
    applications = store.conn.execute(
        "SELECT * FROM pattern_applications WHERE pattern_id = ? ORDER BY applied_at DESC",
        (pattern_id,)
    ).fetchall()
    
    if applications:
        rprint(f"\n[bold]Applications ({len(applications)}):[/bold]")
        for app in applications:
            outcome_color = "green" if app['outcome'] == 'success' else "red"
            rprint(f"  [{outcome_color}]{app['outcome']}[/{outcome_color}] - {app['task_description']}")
            rprint(f"    Applied: {app['applied_at']}")
    
    store.close()


@cli.command()
@click.option('--channel', '-c', help='Filter by channel')
@click.option('--limit', '-l', default=50, help='Max messages to show')
def messages(channel, limit):
    """Show recent messages in message bus."""
    bus = TrinityMessageBus()
    
    recent = bus.get_recent_messages(channel=channel, limit=limit)
    
    table = Table(title=f"Recent Messages ({len(recent)})")
    table.add_column("ID", style="cyan")
    table.add_column("Channel", style="blue")
    table.add_column("Priority", style="yellow")
    table.add_column("Source", style="green")
    table.add_column("Created", style="white")
    table.add_column("Processed", style="magenta")
    
    for msg in recent:
        table.add_row(
            str(msg['id']),
            msg['channel'],
            str(msg['priority']),
            msg['source_agent'] or "-",
            msg['created_at'][:19],
            msg['processed_at'][:19] if msg['processed_at'] else "⏳ Pending"
        )
    
    console.print(table)
    bus.close()


@cli.command()
def init():
    """Initialize Trinity Protocol (create databases, setup models)."""
    console.print("[bold cyan]Initializing Trinity Protocol...[/bold cyan]")
    
    # Create persistent store
    console.print("  Creating persistent store...")
    store = TrinityStore()
    store.close()
    console.print("  ✅ Persistent store created")
    
    # Create message bus
    console.print("  Creating message bus...")
    bus = TrinityMessageBus()
    bus.close()
    console.print("  ✅ Message bus created")
    
    # Check local models
    console.print("  Checking local models...")
    from shared.local_model_server import LocalModelServer
    server = LocalModelServer()
    
    async def check_models():
        is_healthy = await server.health_check()
        if is_healthy:
            models = await server.list_models()
            console.print(f"  ✅ Found {len(models)} local models")
            for model in models:
                console.print(f"    - {model}")
        else:
            console.print("  ⚠️  Local model server not responding")
            console.print("     Run: ollama serve")
    
    asyncio.run(check_models())
    
    console.print("\n[bold green]✨ Trinity Protocol initialized![/bold green]")


if __name__ == '__main__':
    cli()
```

### 4.2 Dashboard (Optional but Recommended)

**File**: `trinity_protocol/dashboard/server.py`

**(This is Week 4, can be deprioritized if needed)**

Simple FastAPI + WebSocket dashboard for real-time monitoring:

```python
"""
Trinity Protocol: Web Dashboard

Real-time monitoring dashboard using FastAPI + WebSockets.
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
from trinity_protocol.persistent_store import TrinityStore
from trinity_protocol.message_bus import TrinityMessageBus


app = FastAPI(title="Trinity Protocol Dashboard")

store = TrinityStore()
bus = TrinityMessageBus()


@app.get("/")
async def dashboard():
    """Serve dashboard HTML."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trinity Protocol Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white">
        <div class="container mx-auto p-8">
            <h1 class="text-4xl font-bold mb-8">Trinity Protocol Dashboard</h1>
            
            <div class="grid grid-cols-3 gap-4 mb-8">
                <div class="bg-gray-800 p-6 rounded">
                    <h2 class="text-xl mb-2">AUDITLEARN</h2>
                    <p class="text-green-400">● Running</p>
                    <p id="patterns-count" class="text-3xl mt-4">--</p>
                    <p class="text-sm text-gray-400">Patterns Detected</p>
                </div>
                
                <div class="bg-gray-800 p-6 rounded">
                    <h2 class="text-xl mb-2">Message Queue</h2>
                    <p id="queue-count" class="text-3xl mt-4">--</p>
                    <p class="text-sm text-gray-400">Pending Messages</p>
                </div>
                
                <div class="bg-gray-800 p-6 rounded">
                    <h2 class="text-xl mb-2">Success Rate</h2>
                    <p id="success-rate" class="text-3xl mt-4">--</p>
                    <p class="text-sm text-gray-400">Pattern Applications</p>
                </div>
            </div>
            
            <div class="bg-gray-800 p-6 rounded">
                <h2 class="text-xl mb-4">Recent Events</h2>
                <div id="events" class="space-y-2 max-h-96 overflow-y-auto">
                    <!-- Events will be inserted here -->
                </div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                // Update stats
                document.getElementById('patterns-count').innerText = data.total_patterns;
                document.getElementById('queue-count').innerText = data.queue_count;
                document.getElementById('success-rate').innerText = 
                    (data.avg_success_rate * 100).toFixed(1) + '%';
                
                // Add event to stream
                if (data.event) {
                    const eventDiv = document.createElement('div');
                    eventDiv.className = 'bg-gray-700 p-3 rounded';
                    eventDiv.innerHTML = `
                        <span class="text-gray-400">${data.event.timestamp}</span> - 
                        <span class="text-blue-400">${data.event.type}</span>: 
                        ${data.event.message}
                    `;
                    document.getElementById('events').prepend(eventDiv);
                }
            };
        </script>
    </body>
    </html>
    """)


@app.websocket("/ws/telemetry")
async def telemetry_stream(websocket: WebSocket):
    """Stream telemetry data to dashboard."""
    await websocket.accept()
    
    while True:
        try:
            # Get current stats
            stats = store.get_pattern_stats()
            queue_count = bus.get_unprocessed_count("improvement_queue")
            
            await websocket.send_json({
                "total_patterns": stats.get('total_patterns', 0),
                "queue_count": queue_count,
                "avg_success_rate": stats.get('avg_success_rate', 0.0),
                "event": None  # TODO: stream actual events
            })
            
            await asyncio.sleep(2)
        except:
            break


@app.get("/api/stats")
async def get_stats():
    """Get Trinity Protocol statistics."""
    stats = store.get_pattern_stats()
    return {
        "patterns": stats,
        "queue": {
            "improvement_queue": bus.get_unprocessed_count("improvement_queue"),
            "execution_queue": bus.get_unprocessed_count("execution_queue"),
        }
    }
```

Run with: `uvicorn trinity_protocol.dashboard.server:app --reload`

---

## Week 5-6: PLAN & EXECUTE Agents (Overview)

**Note**: Weeks 5-6 depend on successful completion of Weeks 1-4. The foundation must be solid before adding orchestration.

### High-Level Architecture

```python
# trinity_protocol/plan_agent.py
class PlanAgent:
    """
    PLAN: Strategic Orchestrator
    
    - Subscribes to improvement_queue
    - Uses HYBRID models (cloud for strategic, local for simple)
    - Calls existing PlannerAgent, ChiefArchitectAgent for specs
    - Creates task list → publishes to execution_queue
    """
    async def planning_loop(self):
        async for improvement in self.message_bus.subscribe("improvement_queue"):
            # Assess complexity
            if complexity.strategic:
                model = "gpt-4"  # Cloud for strategy
            else:
                model = "local:plan_simple"
            
            # Generate plan using existing agents
            spec = await self.planner_agent.create_spec(improvement)
            tasks = await self.break_down_tasks(spec)
            
            # Publish to execution queue
            for task in tasks:
                await self.message_bus.publish(
                    Message("execution_queue", task)
                )


# trinity_protocol/execute_agent.py
class ExecuteAgent:
    """
    EXECUTE: Task Runner
    
    - Subscribes to execution_queue
    - Routes to existing specialized agents (NO rewrite!)
    - Verifies results with tests
    - Publishes outcome to telemetry_stream (closes loop)
    """
    async def execution_loop(self):
        async for task in self.message_bus.subscribe("execution_queue"):
            # Route to appropriate agent
            agent = self.agent_registry.get_agent(task.agent_type)
            
            # Execute with timeout
            result = await agent.execute(task)
            
            # Verify
            if await self.verify_result(result):
                await self.merge_changes(result)
            
            # Publish outcome (AUDITLEARN sees this)
            await self.message_bus.publish(
                Message("telemetry_stream", {
                    "pattern_id": task.pattern_id,
                    "result": "success" if result.passed else "failure",
                    "details": result.details
                })
            )
```

**Key Points for Weeks 5-6:**
- PLAN and EXECUTE are thin orchestration layers
- They use existing agents (AgencyCodeAgent, PlannerAgent, etc.)
- Hybrid cloud/local routing for optimal quality/cost
- Close the feedback loop: EXECUTE → telemetry_stream → AUDITLEARN

---

## 🎯 Success Criteria

### Week 4 Go/No-Go Decision

Before proceeding to Weeks 5-6, must demonstrate:

1. ✅ **AUDITLEARN detects real patterns** from actual usage
2. ✅ **Patterns persist** across restarts (check trinity.db)
3. ✅ **Dashboard shows** live pattern detection
4. ✅ **At least 3 high-confidence patterns** stored with evidence
5. ✅ **Local model inference** < 5s per scan cycle

If these criteria pass → Proceed to PLAN/EXECUTE
If not → Iterate on foundation

### Week 6 Final Validation

1. ✅ **Full loop working**: AUDITLEARN → PLAN → EXECUTE → telemetry → AUDITLEARN
2. ✅ **At least 1 autonomous improvement** completed without human intervention
3. ✅ **Pattern success rate tracking** showing learning over time
4. ✅ **Constitutional compliance** maintained (all tests passing)
5. ✅ **System stability** (24+ hours continuous operation)

---

## 🚀 Getting Started

### Prerequisites

1. **Install Ollama**:
```bash
# macOS
brew install ollama

# Start server
ollama serve
```

2. **Pull Qwen Models**:
```bash
ollama pull qwen2.5-coder:7b-q3   # For AUDITLEARN
ollama pull qwen2.5-coder:14b-q4  # For EXECUTE
ollama pull qwen2.5-coder:32b-q4  # For PLAN (optional)
```

3. **Install Dependencies**:
```bash
cd Agency
poetry install

# Additional Trinity dependencies
poetry add faiss-cpu sentence-transformers fastapi uvicorn websockets
```

4. **Environment Setup**:
```bash
# Add to .env.local
ENABLE_LOCAL_MODE=true
LOCAL_MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
ENABLE_CLOUD_FALLBACK=true  # Keep cloud as safety net
```

### Week 1 Kickoff Commands

```bash
# Initialize Trinity Protocol
python -m trinity_protocol.cli init

# Check status
python -m trinity_protocol.cli status

# Run tests
pytest tests/trinity_protocol/

# (Later) Start AUDITLEARN
python -m trinity_protocol.auditlearn_agent
```

---

## 📋 File Structure

```
Agency/
├── trinity_protocol/
│   ├── __init__.py
│   ├── persistent_store.py       # Week 1 ✅
│   ├── message_bus.py             # Week 1 ✅
│   ├── cli.py                     # Week 1-4 ✅
│   ├── pattern_detector.py        # Week 3 ⏳
│   ├── auditlearn_agent.py        # Week 3-4 ⏳
│   ├── plan_agent.py              # Week 5 📋
│   ├── execute_agent.py           # Week 6 📋
│   ├── dashboard/
│   │   └── server.py              # Week 4 (optional) ⏳
│   └── config/
│       └── trinity_config.yaml
├── shared/
│   ├── local_model_server.py      # Week 2 ⏳
│   └── model_policy.py (enhanced) # Week 2 ⏳
├── tests/trinity_protocol/
│   ├── test_persistent_store.py   # Week 1 ✅
│   ├── test_message_bus.py        # Week 1 ✅
│   └── test_pattern_detector.py   # Week 3 ⏳
├── .env.local                      # Configuration
├── trinity.db                      # Persistent learning store
└── trinity_messages.db             # Message bus queue
```

---

## 🎓 Key Concepts

### Pattern Detection vs Reasoning

**AUDITLEARN uses local models for DETECTION, not REASONING:**

✅ Good use of local models:
- "Is this error message similar to pattern X?"
- "Count occurrences of 'timeout' in these events"
- "Extract key phrases from this log"
- "Is this code duplicated elsewhere?"

❌ Bad use of local models:
- "Design an architecture for this feature"
- "Debug this complex race condition"
- "Should we refactor or rewrite?"
- "What's the best database for this use case?"

### Hybrid Cloud/Local Strategy

```
Task Complexity Assessment:
  Low (0.0-0.5): Local model (fast, cheap)
    Examples: pattern matching, simple refactoring, test generation
  
  Medium (0.5-0.7): Local with cloud fallback
    Examples: code completion, documentation, simple debugging
  
  High (0.7-1.0): Cloud model (quality critical)
    Examples: architecture, strategy, complex debugging
```

### Message Bus as Integration Layer

The message bus decouples agents:
- AUDITLEARN doesn't know about PLAN
- PLAN doesn't know about EXECUTE
- EXECUTE doesn't know about AUDITLEARN

This enables:
- Independent testing of each agent
- Swapping implementations without breaking others
- Observability (every message logged)
- Replay debugging (can replay message sequence)

---

## 🔧 Troubleshooting

### Ollama Not Starting
```bash
# Check if running
ps aux | grep ollama

# Start manually
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

### Models Too Slow
```bash
# Use smaller quantization
ollama pull qwen2.5-coder:7b-q2  # Faster but lower quality

# Or use CPU-optimized models
export OLLAMA_NUM_GPU=0  # Force CPU (more predictable latency)
```

### FAISS Index Errors
```bash
# Rebuild index
rm trinity_embeddings.faiss
python -m trinity_protocol.cli init
```

---

## 📚 References

### Trinity Protocol Inspiration
- Based on "Trinity Protocol" concept: 3 persistent agents (monitor, plan, execute)
- Adapted for Agency's multi-agent architecture
- Enhanced with hybrid cloud/local models

### Local Model Resources
- Qwen 2.5-Coder: https://qwenlm.github.io/blog/qwen2.5-coder/
- Ollama: https://ollama.ai/
- FAISS: https://github.com/facebookresearch/faiss

### Agency Architecture
- See: `constitution.md` - Constitutional principles
- See: `CLAUDE.md` - Codebase map and best practices
- See: `docs/ADR/` - Architecture decision records

---

## 🎯 Next Steps

1. **Review this plan** with team/stakeholders
2. **Set up Ollama** and pull Qwen models
3. **Start Week 1** implementation:
   - Create `trinity_protocol/` directory
   - Implement `persistent_store.py`
   - Implement `message_bus.py`
   - Write tests
4. **Daily check-ins** to track progress
5. **Week 4 decision point**: Go/no-go for PLAN/EXECUTE

---

**Ready to build the second brain? Let's begin with Week 1!** 🚀