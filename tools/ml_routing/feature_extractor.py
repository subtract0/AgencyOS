"""
Feature extractor for ML-based task classification.

Extracts 1644-dimension feature vectors from task descriptions using:
- 1536-dim semantic embeddings (OpenAI text-embedding-3-small)
- 100-dim TF-IDF keyword features
- 8-dim metadata features

Constitutional Compliance:
- Article I: Retry on embedding API timeout (3 attempts, exponential backoff)
- Article II: Result pattern for error handling (no exceptions)
- Article IV: Cache embeddings in memory to reduce API calls (>80% reduction)
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for all fallible operations
- Law #8: Functions <50 lines each

Reference: specs/spec-005-advanced-pattern-recognition.md Section 5.3
Author: AgencyCodeAgent
Date: 2025-10-10
"""

import hashlib
import logging
import re
import time
from typing import Any

import openai
from sklearn.feature_extraction.text import TfidfVectorizer

from shared.models.task_feature_vector import TaskFeatureVector
from shared.type_definitions.result import Err, Ok, Result
from tools.ml_routing.tfidf_vocabulary_builder import TfidfVocabulary

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extract ML features from task descriptions.

    Performance targets:
    - <50ms p99 latency for feature extraction
    - >80% cache hit rate for duplicate tasks
    - <3 API calls per 10 tasks (via caching)

    Constitutional Compliance:
    - Article I: Complete context with retry logic (3 attempts)
    - Article II: Result pattern for error handling
    - Article IV: Cache features to reduce API costs
    """

    def __init__(
        self,
        openai_api_key: str,
        tfidf_vocabulary: TfidfVocabulary,
        cache_size: int = 1000,
    ):
        """
        Initialize feature extractor with OpenAI client and TF-IDF vocabulary.

        Args:
            openai_api_key: OpenAI API key for embeddings
            tfidf_vocabulary: Pre-built TF-IDF vocabulary (100 terms)
            cache_size: Maximum number of embeddings to cache (default: 1000)
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.tfidf_vocabulary = tfidf_vocabulary
        self.cache_size = cache_size

        # Initialize TF-IDF vectorizer with vocabulary
        self.tfidf_vectorizer = TfidfVectorizer(
            vocabulary=tfidf_vocabulary.terms,
            stop_words="english",
            lowercase=True,
            token_pattern=r"\b[a-z]{2,}\b",
        )

        # Embedding cache (task_hash -> embedding)
        self.embedding_cache: dict[str, list[float]] = {}

        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_extractions = 0

        logger.info(
            f"FeatureExtractor initialized with {len(tfidf_vocabulary.terms)} "
            f"TF-IDF terms and cache size {cache_size}"
        )

    def extract_features(
        self,
        task_description: str,
        task_metadata: dict[str, Any] | None = None,
    ) -> Result[TaskFeatureVector, str]:
        """
        Extract 1644-dim feature vector from task description.

        Combines embedding (1536), TF-IDF (100), and metadata (8) features.

        Args:
            task_description: Task description text
            task_metadata: Optional metadata (estimated_time_seconds, etc.)

        Returns:
            Result containing TaskFeatureVector or error message

        Performance Target: <50ms p99 latency
        """
        self.total_extractions += 1

        if not task_description.strip():
            return Err("Task description cannot be empty")

        metadata = task_metadata or {}

        # Extract all features
        embedding_result = self._generate_embedding(task_description)
        if embedding_result.is_err():
            return Err(embedding_result.unwrap_err())

        tfidf_result = self._compute_tfidf(task_description)
        if tfidf_result.is_err():
            return Err(tfidf_result.unwrap_err())

        metadata_result = self._extract_metadata(task_description, metadata)
        if metadata_result.is_err():
            return Err(metadata_result.unwrap_err())

        # Combine into feature vector
        return self._build_feature_vector(
            embedding_result.unwrap(),
            tfidf_result.unwrap(),
            metadata_result.unwrap(),
        )

    def _generate_embedding(self, text: str) -> Result[list[float], str]:
        """
        Generate semantic embedding with retry logic and caching.

        Article I compliance: 3 retry attempts with exponential backoff.
        Article IV compliance: Cache embeddings to reduce API costs.

        Args:
            text: Text to embed

        Returns:
            Result containing 1536-dim embedding or error message
        """
        # Check cache first (Article IV: reduce API calls)
        task_hash = self._hash_task(text)
        cached_result = self._get_cached_embedding(task_hash)
        if cached_result.is_ok():
            return cached_result

        self.cache_misses += 1

        # Generate embedding with retry logic (Article I)
        return self._call_openai_with_retry(text, task_hash)

    def _get_cached_embedding(self, task_hash: str) -> Result[list[float], str]:
        """
        Get embedding from cache if available.

        Args:
            task_hash: Task hash key

        Returns:
            Result containing cached embedding or error if not found
        """
        if task_hash in self.embedding_cache:
            self.cache_hits += 1
            logger.debug(f"Embedding cache hit (rate: {self._cache_hit_rate():.1%})")
            return Ok(self.embedding_cache[task_hash])
        return Err("Not in cache")

    def _call_openai_with_retry(self, text: str, task_hash: str) -> Result[list[float], str]:
        """
        Call OpenAI embeddings API with retry logic.

        Args:
            text: Text to embed
            task_hash: Task hash for caching

        Returns:
            Result containing embedding or error message
        """
        for attempt in range(1, 4):
            result = self._attempt_openai_call(text, task_hash, attempt)
            if result.is_ok():
                return result

            # Handle timeout with retry
            if attempt < 3 and "timeout" in result.unwrap_err().lower():
                wait_seconds = 2**attempt
                logger.warning(
                    f"Embedding API timeout (attempt {attempt}/3), retrying in {wait_seconds}s"
                )
                time.sleep(wait_seconds)
            else:
                return result

        return Err("Embedding generation failed after 3 attempts")

    def _attempt_openai_call(
        self, text: str, task_hash: str, attempt: int
    ) -> Result[list[float], str]:
        """
        Single attempt to call OpenAI embeddings API.

        Args:
            text: Text to embed
            task_hash: Task hash for caching
            attempt: Current attempt number

        Returns:
            Result containing embedding or error message
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small", input=text
            )
            embedding = response.data[0].embedding

            # Validate dimension
            if len(embedding) != 1536:
                return Err(f"Invalid embedding dimension: expected 1536, got {len(embedding)}")

            # Cache embedding
            self._cache_embedding(task_hash, embedding)
            return Ok(embedding)

        except openai.APITimeoutError:
            return Err(f"Embedding API timeout on attempt {attempt}")

        except Exception as e:
            return Err(f"Embedding generation error: {e}")

    def _compute_tfidf(self, task_description: str) -> Result[list[float], str]:
        """
        Compute TF-IDF features using pre-built vocabulary.

        Pads to 100 dimensions if vocabulary < 100 terms (with zeros).

        Args:
            task_description: Task description text

        Returns:
            Result containing 100-dim TF-IDF feature vector or error
        """
        try:
            # Fit vectorizer to single document
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([task_description])

            # Extract feature vector (variable dimensions based on vocabulary)
            tfidf_features = tfidf_matrix.toarray()[0].tolist()

            # Pad to 100 dimensions if vocabulary < 100 (Article II: complete context)
            vocab_size = len(self.tfidf_vocabulary.terms)
            if vocab_size < 100:
                padding = [0.0] * (100 - vocab_size)
                tfidf_features.extend(padding)
                logger.debug(f"Padded TF-IDF from {vocab_size} to 100 dimensions")

            # Validate dimension
            if len(tfidf_features) != 100:
                return Err(f"Invalid TF-IDF dimension: expected 100, got {len(tfidf_features)}")

            return Ok(tfidf_features)

        except Exception as e:
            return Err(f"TF-IDF computation failed: {e}")

    def _extract_metadata(
        self, task_description: str, task_metadata: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Extract 8 metadata features from task description and metadata.

        Features:
        1. description_length: Character count
        2. word_count: Word count
        3. has_refactor_keyword: Binary flag
        4. has_test_keyword: Binary flag
        5. has_async_keyword: Binary flag
        6. has_fix_keyword: Binary flag
        7. estimated_time_seconds: User estimate (default: 0.0)
        8. historical_tier_mode: Most common tier (default: 0)

        Args:
            task_description: Task description text
            task_metadata: Optional metadata dictionary

        Returns:
            Result containing metadata features dictionary or error
        """
        try:
            description_lower = task_description.lower()

            metadata_features = {
                "description_length": len(task_description),
                "word_count": len(task_description.split()),
                "has_refactor_keyword": int("refactor" in description_lower),
                "has_test_keyword": int("test" in description_lower),
                "has_async_keyword": int("async" in description_lower),
                "has_fix_keyword": int("fix" in description_lower),
                "estimated_time_seconds": float(task_metadata.get("estimated_time_seconds", 0.0)),
                "historical_tier_mode": int(task_metadata.get("historical_tier_mode", 0)),
            }

            return Ok(metadata_features)

        except Exception as e:
            return Err(f"Metadata extraction failed: {e}")

    def _build_feature_vector(
        self,
        embedding: list[float],
        tfidf_features: list[float],
        metadata_features: dict[str, Any],
    ) -> Result[TaskFeatureVector, str]:
        """
        Build TaskFeatureVector from extracted features.

        Args:
            embedding: 1536-dim semantic embedding
            tfidf_features: 100-dim TF-IDF features
            metadata_features: 8-dim metadata features dictionary

        Returns:
            Result containing TaskFeatureVector or error message
        """
        try:
            vector = TaskFeatureVector(
                embedding=embedding,
                tfidf_features=tfidf_features,
                description_length=metadata_features["description_length"],
                word_count=metadata_features["word_count"],
                has_refactor_keyword=metadata_features["has_refactor_keyword"],
                has_test_keyword=metadata_features["has_test_keyword"],
                has_async_keyword=metadata_features["has_async_keyword"],
                has_fix_keyword=metadata_features["has_fix_keyword"],
                estimated_time_seconds=metadata_features["estimated_time_seconds"],
                historical_tier_mode=metadata_features["historical_tier_mode"],
            )
            return Ok(vector)
        except Exception as e:
            return Err(f"Failed to create TaskFeatureVector: {e}")

    def _cache_embedding(self, task_hash: str, embedding: list[float]) -> None:
        """
        Cache embedding with LRU eviction.

        Args:
            task_hash: Task hash key
            embedding: 1536-dim embedding vector
        """
        # Evict oldest entry if cache is full
        if len(self.embedding_cache) >= self.cache_size:
            oldest_key = next(iter(self.embedding_cache))
            del self.embedding_cache[oldest_key]
            logger.debug(f"Evicted oldest embedding from cache (size: {self.cache_size})")

        self.embedding_cache[task_hash] = embedding

    def _hash_task(self, task_description: str) -> str:
        """
        Generate hash key for task description.

        Uses SHA-256 for collision resistance.

        Args:
            task_description: Task description text

        Returns:
            Hex digest of task description hash
        """
        return hashlib.sha256(task_description.encode("utf-8")).hexdigest()

    def _cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Cache hit rate (0.0-1.0)
        """
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            return 0.0
        return self.cache_hits / total_requests

    def get_performance_metrics(self) -> dict[str, Any]:
        """
        Get performance metrics for monitoring.

        Returns:
            Dictionary with cache hit rate, total extractions, etc.
        """
        return {
            "total_extractions": self.total_extractions,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self._cache_hit_rate(),
            "cache_size": len(self.embedding_cache),
            "cache_limit": self.cache_size,
        }

    def compute_complexity_score(self, task_description: str) -> float:
        """
        Compute complexity score heuristic (0.0-1.0).

        Heuristic based on:
        - Description length (longer = more complex)
        - Keyword density (architecture, design, refactor)
        - Code snippet presence
        - File path mentions

        Args:
            task_description: Task description text

        Returns:
            Complexity score (0.0 = simple, 1.0 = complex)
        """
        score = 0.0
        description_lower = task_description.lower()

        # Length factor (0.0-0.3)
        length_score = min(len(task_description) / 1000.0, 0.3)
        score += length_score

        # Complexity keywords (0.0-0.4)
        complexity_keywords = [
            "architecture",
            "design",
            "refactor",
            "optimize",
            "performance",
            "scalability",
        ]
        keyword_score = sum(0.1 for keyword in complexity_keywords if keyword in description_lower)
        score += min(keyword_score, 0.4)

        # Code snippets (0.15)
        if self._detect_code_snippets(task_description):
            score += 0.15

        # File paths (0.15)
        if self._detect_file_paths(task_description):
            score += 0.15

        # Cap at 1.0
        return min(score, 1.0)

    def _detect_code_snippets(self, text: str) -> bool:
        """
        Detect code snippets in text.

        Looks for:
        - Backtick code blocks (```python, etc.)
        - Inline code (`code`)
        - Common code patterns (def, class, import)

        Args:
            text: Text to analyze

        Returns:
            True if code snippets detected
        """
        code_patterns = [
            r"```[\w]*",  # Code blocks
            r"`[^`]+`",  # Inline code
            r"\bdef\s+\w+\s*\(",  # Python function definitions
            r"\bclass\s+\w+",  # Class definitions
            r"\bimport\s+\w+",  # Import statements
        ]

        for pattern in code_patterns:
            if re.search(pattern, text):
                return True

        return False

    def _detect_file_paths(self, text: str) -> bool:
        """
        Detect file paths in text.

        Looks for:
        - Absolute paths (/path/to/file)
        - Relative paths (./path/to/file)
        - Common file extensions (.py, .ts, .md)

        Args:
            text: Text to analyze

        Returns:
            True if file paths detected
        """
        file_path_patterns = [
            r"/[\w/]+\.\w+",  # Absolute path with extension
            r"\./[\w/]+\.\w+",  # Relative path with extension
            r"[\w/]+\.(py|ts|js|md|json|yaml|yml)",  # Common extensions
        ]

        for pattern in file_path_patterns:
            if re.search(pattern, text):
                return True

        return False
