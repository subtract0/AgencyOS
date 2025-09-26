"""
Vector similarity search for memory systems.

Provides semantic search capabilities alongside tag-based search.
Lightweight implementation with optional embeddings support.
"""

import logging
import json
from typing import Any, Dict, List, Optional
from shared.types.json import JSONValue
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Result from similarity search with score and metadata."""

    memory: Dict[str, JSONValue]
    similarity_score: float
    search_type: str  # 'semantic', 'keyword', or 'hybrid'


class VectorStore:
    """
    Lightweight vector store for semantic memory search.

    Features:
    - Text embeddings for semantic search
    - Keyword-based fallback
    - Hybrid search combining both approaches
    - Optional external embedding provider support
    """

    def __init__(self, embedding_provider: Optional[str] = None):
        """
        Initialize VectorStore.

        Args:
            embedding_provider: Optional embedding provider ('openai', 'sentence-transformers', etc.)
        """
        self._embeddings: Dict[str, List[float]] = {}
        self._memory_texts: Dict[str, str] = {}
        self._memory_records: Dict[str, Dict[str, JSONValue]] = {}
        self._embedding_provider = embedding_provider
        self._embedding_function = None

        # Try to initialize embedding function
        self._initialize_embeddings()

        logger.info(
            f"VectorStore initialized with provider: {embedding_provider or 'keyword-only'}"
        )

    def _initialize_embeddings(self) -> None:
        """Initialize embedding function based on provider."""
        if not self._embedding_provider:
            logger.info("No embedding provider specified - using keyword search only")
            return

        try:
            if self._embedding_provider == "sentence-transformers":
                self._init_sentence_transformers()
            elif self._embedding_provider == "openai":
                self._init_openai_embeddings()
            else:
                logger.warning(
                    f"Unknown embedding provider: {self._embedding_provider}"
                )

        except ImportError as e:
            logger.warning(f"Failed to initialize {self._embedding_provider}: {e}")
            logger.info("Falling back to keyword search only")

    def _init_sentence_transformers(self) -> None:
        """Initialize sentence-transformers embedding model."""
        try:
            from sentence_transformers import SentenceTransformer

            # Use a lightweight model for efficiency
            model_name = "all-MiniLM-L6-v2"  # 22MB, fast, good quality
            self._embedding_model = SentenceTransformer(model_name)

            def embed_texts(texts: List[str]) -> List[List[float]]:
                embeddings = self._embedding_model.encode(
                    texts, convert_to_tensor=False
                )
                return embeddings.tolist()

            self._embedding_function = embed_texts
            logger.info(f"Initialized sentence-transformers with model: {model_name}")

        except ImportError:
            raise ImportError(
                "sentence-transformers not available. Install with: pip install sentence-transformers"
            )

    def _init_openai_embeddings(self) -> None:
        """Initialize OpenAI embeddings."""
        try:
            import openai
            import os

            # Check for API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")

            def embed_texts(texts: List[str]) -> List[List[float]]:
                """Embed texts using OpenAI API."""
                client = openai.OpenAI(api_key=api_key)
                response = client.embeddings.create(
                    model="text-embedding-3-small",  # Efficient and cost-effective
                    input=texts,
                )
                return [embedding.embedding for embedding in response.data]

            self._embedding_function = embed_texts
            logger.info("Initialized OpenAI embeddings")

        except ImportError:
            raise ImportError("openai not available. Install with: pip install openai")

    def add_memory(self, memory_key: str, memory_content: Dict[str, JSONValue]) -> None:
        """
        Add memory to vector store for search.

        Args:
            memory_key: Unique memory identifier
            memory_content: Memory record with content and metadata
        """
        if "key" not in memory_content:
            memory_content["key"] = memory_key
        self._memory_records[memory_key] = memory_content

        searchable_text = self._extract_searchable_text(memory_content)
        self._memory_texts[memory_key] = searchable_text

        # Generate embedding if provider is available
        if self._embedding_function:
            try:
                embeddings = self._embedding_function([searchable_text])
                self._embeddings[memory_key] = embeddings[0]
                logger.debug(f"Generated embedding for memory: {memory_key}")
            except Exception as e:
                logger.warning(f"Failed to generate embedding for {memory_key}: {e}")

    def _extract_searchable_text(self, memory: Dict[str, JSONValue]) -> str:
        """
        Extract searchable text from memory record.

        Args:
            memory: Memory record

        Returns:
            Combined searchable text
        """
        text_parts = []

        # Add key
        if "key" in memory:
            text_parts.append(memory["key"])

        # Add tags
        if "tags" in memory and memory["tags"]:
            text_parts.extend(memory["tags"])

        # Add content (convert to string if needed)
        content = memory.get("content", "")
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, dict):
            # Extract text from structured content
            text_parts.append(json.dumps(content, default=str))
        else:
            text_parts.append(str(content))

        return " ".join(text_parts)

    def semantic_search(
        self, query: str, memories: List[dict[str, JSONValue]], top_k: int = 10
    ) -> List[SimilarityResult]:
        """
        Perform semantic similarity search.

        Args:
            query: Search query
            memories: List of memory records to search
            top_k: Maximum number of results

        Returns:
            List of similarity results ordered by relevance
        """
        if not self._embedding_function:
            logger.warning(
                "No embedding function available - falling back to keyword search"
            )
            return self.keyword_search(query, memories, top_k)

        try:
            # Generate query embedding
            query_embeddings = self._embedding_function([query])
            query_embedding = query_embeddings[0]

            results = []

            for memory in memories:
                memory_key = memory.get("namespaced_key", memory.get("key", ""))

                # Ensure memory is in vector store
                if memory_key not in self._embeddings:
                    self.add_memory(memory_key, memory)

                # Skip if still no embedding
                if memory_key not in self._embeddings:
                    continue

                # Calculate cosine similarity
                memory_embedding = self._embeddings[memory_key]
                similarity = self._cosine_similarity(query_embedding, memory_embedding)

                results.append(
                    SimilarityResult(
                        memory=memory,
                        similarity_score=similarity,
                        search_type="semantic",
                    )
                )

            # Sort by similarity score (descending)
            results.sort(key=lambda x: x.similarity_score, reverse=True)

            return results[:top_k]

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return self.keyword_search(query, memories, top_k)

    def keyword_search(
        self, query: str, memories: List[dict[str, JSONValue]], top_k: int = 10
    ) -> List[SimilarityResult]:
        """
        Perform keyword-based search as fallback.

        Args:
            query: Search query
            memories: List of memory records to search
            top_k: Maximum number of results

        Returns:
            List of similarity results ordered by relevance
        """
        query_words = set(query.lower().split())
        results = []

        for memory in memories:
            # Get searchable text
            memory_key = memory.get("namespaced_key", memory.get("key", ""))

            if memory_key not in self._memory_texts:
                searchable_text = self._extract_searchable_text(memory)
                self._memory_texts[memory_key] = searchable_text
            else:
                searchable_text = self._memory_texts[memory_key]

            # Calculate keyword overlap score
            memory_words = set(searchable_text.lower().split())
            overlap = query_words.intersection(memory_words)

            if overlap:
                # Simple scoring: ratio of overlapping words
                score = len(overlap) / len(query_words) if query_words else 0

                # Boost score for exact phrase matches
                if query.lower() in searchable_text.lower():
                    score *= 1.5

                results.append(
                    SimilarityResult(
                        memory=memory, similarity_score=score, search_type="keyword"
                    )
                )

        # Sort by similarity score (descending)
        results.sort(key=lambda x: x.similarity_score, reverse=True)

        return results[:top_k]

    def hybrid_search(
        self,
        query: str,
        memories: List[dict[str, JSONValue]],
        top_k: int = 10,
        semantic_weight: float = 0.7,
    ) -> List[SimilarityResult]:
        """
        Perform hybrid search combining semantic and keyword approaches.

        Args:
            query: Search query
            memories: List of memory records to search
            top_k: Maximum number of results
            semantic_weight: Weight for semantic scores (0.0 to 1.0)

        Returns:
            List of similarity results ordered by combined relevance
        """
        if not self._embedding_function:
            return self.keyword_search(query, memories, top_k)

        # Get results from both approaches
        semantic_results = self.semantic_search(query, memories, len(memories))
        keyword_results = self.keyword_search(query, memories, len(memories))

        # Create combined score mapping
        combined_scores = {}
        memory_map = {}

        # Process semantic results
        for result in semantic_results:
            memory_key = result.memory.get(
                "namespaced_key", result.memory.get("key", "")
            )
            combined_scores[memory_key] = semantic_weight * result.similarity_score
            memory_map[memory_key] = result.memory

        # Add keyword results
        keyword_weight = 1.0 - semantic_weight
        for result in keyword_results:
            memory_key = result.memory.get(
                "namespaced_key", result.memory.get("key", "")
            )

            if memory_key in combined_scores:
                combined_scores[memory_key] += keyword_weight * result.similarity_score
            else:
                combined_scores[memory_key] = keyword_weight * result.similarity_score
                memory_map[memory_key] = result.memory

        # Create final results
        final_results = []
        for memory_key, score in combined_scores.items():
            if score > 0:  # Only include results with positive scores
                final_results.append(
                    SimilarityResult(
                        memory=memory_map[memory_key],
                        similarity_score=score,
                        search_type="hybrid",
                    )
                )

        # Sort by combined score (descending)
        final_results.sort(key=lambda x: x.similarity_score, reverse=True)

        return final_results[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (-1 to 1)
        """
        if len(vec1) != len(vec2):
            return 0.0

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def search(self, query: str, namespace: Optional[str] = None, limit: int = 10) -> List[Dict[str, JSONValue]]:
        try:
            memories = list(self._memory_records.values())
            if namespace:
                memories = [m for m in memories if m.get("metadata", {}).get("namespace") == namespace]
            results = self.hybrid_search(query, memories, top_k=limit)
            return [
                {
                    **r.memory,
                    "relevance_score": r.similarity_score,
                    "search_type": r.search_type,
                }
                for r in results
            ]
        except Exception:
            return []

    def remove_memory(self, memory_key: str) -> None:
        """
        Remove memory from vector store.

        Args:
            memory_key: Memory key to remove
        """
        self._embeddings.pop(memory_key, None)
        self._memory_texts.pop(memory_key, None)
        self._memory_records.pop(memory_key, None)

    def get_stats(self) -> Dict[str, JSONValue]:
        """
        Get vector store statistics.

        Returns:
            Dictionary with store statistics
        """
        return {
            "total_memories": len(self._memory_texts),
            "memories_with_embeddings": len(self._embeddings),
            "embedding_provider": self._embedding_provider,
            "embedding_available": self._embedding_function is not None,
            "has_embeddings": self._embedding_function is not None,
            "last_updated": datetime.now().isoformat(),
        }


class EnhancedSwarmMemoryStore:
    """
    SwarmMemoryStore enhanced with vector similarity search.

    Combines the swarm features with semantic search capabilities.
    """

    def __init__(self, swarm_store, vector_store: Optional[VectorStore] = None):
        """
        Initialize enhanced store.

        Args:
            swarm_store: SwarmMemoryStore instance
            vector_store: Optional VectorStore for semantic search
        """
        self.swarm_store = swarm_store
        self.vector_store = vector_store or VectorStore()

    def store(self, key: str, content: Any, tags: List[str], **kwargs) -> None:
        """Store memory in both swarm and vector stores."""
        # Store in swarm store
        self.swarm_store.store(key, content, tags, **kwargs)

        # Add to vector store
        agent_id = kwargs.get("agent_id", "default")
        namespaced_key = f"{agent_id}:{key}"

        memory_record = {
            "key": key,
            "namespaced_key": namespaced_key,
            "content": content,
            "tags": tags,
            **kwargs,
        }

        self.vector_store.add_memory(namespaced_key, memory_record)

    def semantic_search(
        self,
        query: str,
        agent_id: str = "default",
        include_shared: bool = True,
        top_k: int = 10,
    ) -> List[SimilarityResult]:
        """
        Perform semantic search across agent memories.

        Args:
            query: Search query
            agent_id: Agent identifier
            include_shared: Include shared memories
            top_k: Maximum results

        Returns:
            List of similarity results
        """
        # Get relevant memories from swarm store
        memories = self.swarm_store.get_all(agent_id)

        if include_shared:
            shared_memories = list(self.swarm_store._shared_knowledge.values())
            # Filter out memories from the same agent
            shared_memories = [m for m in shared_memories if m["agent_id"] != agent_id]
            memories.extend(shared_memories)

        return self.vector_store.hybrid_search(query, memories, top_k)

    def combined_search(
        self,
        tags: List[str] = None,
        query: str = None,
        agent_id: str = "default",
        include_shared: bool = True,
        top_k: int = 10,
    ) -> List[Dict[str, JSONValue]]:
        """
        Combine tag-based and semantic search.

        Args:
            tags: Optional tags to filter by
            query: Optional semantic query
            agent_id: Agent identifier
            include_shared: Include shared memories
            top_k: Maximum results

        Returns:
            Combined search results with relevance scores
        """
        if tags and query:
            # First filter by tags, then semantic search
            tag_filtered = self.swarm_store.search(tags, agent_id, include_shared)
            semantic_results = self.vector_store.hybrid_search(
                query, tag_filtered, top_k
            )

            # Convert to memory records with scores
            return [
                {
                    **result.memory,
                    "relevance_score": result.similarity_score,
                    "search_type": result.search_type,
                }
                for result in semantic_results
            ]

        elif tags:
            # Tag-based search only
            results = self.swarm_store.search(tags, agent_id, include_shared)
            return results[:top_k]

        elif query:
            # Semantic search only
            semantic_results = self.semantic_search(
                query, agent_id, include_shared, top_k
            )
            return [
                {
                    **result.memory,
                    "relevance_score": result.similarity_score,
                    "search_type": result.search_type,
                }
                for result in semantic_results
            ]
        else:
            # Return all memories
            return self.swarm_store.get_all(agent_id)[:top_k]

    def __getattr__(self, name):
        """Delegate unknown methods to swarm_store."""
        return getattr(self.swarm_store, name)
