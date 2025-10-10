"""
TF-IDF vocabulary builder for task classification.

Extracts top 100 keywords from historical task descriptions using TF-IDF
to create a fixed vocabulary for feature extraction.

Constitutional Compliance:
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling
- Law #7: Clear, readable code
- Law #8: Functions <50 lines
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Removed deprecated typing.List import (use builtin list instead)
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer

from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class TfidfVocabulary(BaseModel):
    """
    TF-IDF vocabulary model.

    Attributes:
        terms: Top 100 keywords extracted from task descriptions
        idf_scores: IDF score per term (higher = more discriminative)
        version: Vocabulary version identifier
        created_at: Timestamp of vocabulary creation
    """

    terms: list[str] = Field(description="Top 100 keywords by IDF score")
    idf_scores: dict[str, float] = Field(
        description="IDF score per term (inverse document frequency)"
    )
    version: str = Field(default="v1.0", description="Vocabulary version")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(), description="Creation timestamp"
    )


class TfidfVocabularyBuilder:
    """
    TF-IDF vocabulary builder for task classification.

    Builds a fixed vocabulary of top 100 keywords from historical task
    descriptions using scikit-learn's TfidfVectorizer.
    """

    def __init__(self, stop_words: str = "english", min_df: int = 2):
        """
        Initialize vocabulary builder.

        Args:
            stop_words: Stopwords to filter out (default: 'english')
            min_df: Minimum document frequency for term inclusion
        """
        self.stop_words = stop_words
        self.min_df = min_df

    def build_vocabulary(
        self, task_descriptions: list[str], top_n: int = 100
    ) -> Result[TfidfVocabulary, str]:
        """
        Build vocabulary from task descriptions using TF-IDF.

        Args:
            task_descriptions: List of task description strings
            top_n: Number of top terms to extract (default: 100)

        Returns:
            Result containing TfidfVocabulary or error message
        """
        if not task_descriptions:
            return Err("Cannot build vocabulary from empty task list")

        if len(task_descriptions) < self.min_df:
            return Err(f"Need at least {self.min_df} tasks, got {len(task_descriptions)}")

        # Build TF-IDF vectorizer
        vectorizer_result = self._create_vectorizer(top_n)
        if vectorizer_result.is_err():
            return Err(vectorizer_result.unwrap_err())

        vectorizer = vectorizer_result.unwrap()

        # Fit vectorizer to task descriptions
        fit_result = self._fit_vectorizer(vectorizer, task_descriptions)
        if fit_result.is_err():
            return Err(fit_result.unwrap_err())

        # Extract terms and IDF scores
        terms = vectorizer.get_feature_names_out().tolist()
        idf_scores = {
            term: float(score) for term, score in zip(terms, vectorizer.idf_, strict=True)
        }

        logger.info(f"Built vocabulary with {len(terms)} terms from {len(task_descriptions)} tasks")
        logger.info(
            f"Top 5 terms by IDF: {sorted(idf_scores.items(), key=lambda x: x[1], reverse=True)[:5]}"
        )

        return Ok(
            TfidfVocabulary(
                terms=terms, idf_scores=idf_scores, version="v1.0", created_at=datetime.now()
            )
        )

    def _create_vectorizer(self, top_n: int) -> Result[TfidfVectorizer, str]:
        """
        Create TfidfVectorizer with configuration.

        Args:
            top_n: Maximum number of features to extract

        Returns:
            Result containing configured TfidfVectorizer or error
        """
        try:
            vectorizer = TfidfVectorizer(
                stop_words=self.stop_words,
                max_features=top_n,
                min_df=self.min_df,
                lowercase=True,
                token_pattern=r"\b[a-z]{2,}\b",  # Filter single chars
            )
            return Ok(vectorizer)
        except Exception as e:
            return Err(f"Failed to create vectorizer: {e}")

    def _fit_vectorizer(
        self, vectorizer: TfidfVectorizer, task_descriptions: list[str]
    ) -> Result[None, str]:
        """
        Fit vectorizer to task descriptions.

        Args:
            vectorizer: TfidfVectorizer instance
            task_descriptions: List of task description strings

        Returns:
            Result containing None or error message
        """
        try:
            vectorizer.fit(task_descriptions)
            return Ok(None)
        except Exception as e:
            return Err(f"Failed to fit vectorizer: {e}")

    def save_vocabulary(
        self,
        vocab: TfidfVocabulary,
        path: Path = Path("~/.agency/models/tfidf_vocabulary_v1.json"),
    ) -> Result[Path, str]:
        """
        Save vocabulary to JSON file.

        Creates parent directory if it doesn't exist.

        Args:
            vocab: TfidfVocabulary to save
            path: File path for vocabulary JSON

        Returns:
            Result containing saved file path or error message
        """
        expanded_path = path.expanduser()

        # Create parent directory if missing
        dir_result = self._ensure_directory(expanded_path.parent)
        if dir_result.is_err():
            return Err(dir_result.unwrap_err())

        # Write vocabulary JSON
        write_result = self._write_json(expanded_path, vocab)
        if write_result.is_err():
            return Err(write_result.unwrap_err())

        logger.info(f"Saved vocabulary to {expanded_path}")
        return Ok(expanded_path)

    def _ensure_directory(self, directory: Path) -> Result[None, str]:
        """
        Ensure directory exists, create if missing.

        Args:
            directory: Directory path to ensure exists

        Returns:
            Result containing None or error message
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return Ok(None)
        except Exception as e:
            return Err(f"Failed to create directory {directory}: {e}")

    def _write_json(self, path: Path, vocab: TfidfVocabulary) -> Result[None, str]:
        """
        Write vocabulary to JSON file.

        Args:
            path: File path to write to
            vocab: TfidfVocabulary to serialize

        Returns:
            Result containing None or error message
        """
        try:
            with open(path, "w") as f:
                # Convert datetime to ISO format for JSON serialization
                vocab_dict = vocab.model_dump()
                vocab_dict["created_at"] = vocab_dict["created_at"].isoformat()
                json.dump(vocab_dict, f, indent=2)
            return Ok(None)
        except Exception as e:
            return Err(f"Failed to write vocabulary to {path}: {e}")

    def load_vocabulary(
        self, path: Path = Path("~/.agency/models/tfidf_vocabulary_v1.json")
    ) -> Result[TfidfVocabulary, str]:
        """
        Load vocabulary from JSON file.

        Args:
            path: File path to load vocabulary from

        Returns:
            Result containing TfidfVocabulary or error message
        """
        expanded_path = path.expanduser()

        if not expanded_path.exists():
            return Err(f"Vocabulary file not found: {expanded_path}")

        read_result = self._read_json(expanded_path)
        if read_result.is_err():
            return Err(read_result.unwrap_err())

        vocab_dict = read_result.unwrap()

        # Parse vocabulary with Pydantic
        parse_result = self._parse_vocabulary(vocab_dict)
        if parse_result.is_err():
            return Err(parse_result.unwrap_err())

        logger.info(f"Loaded vocabulary from {expanded_path}")
        return Ok(parse_result.unwrap())

    def _read_json(self, path: Path) -> Result[dict, str]:
        """
        Read JSON file and return dictionary.

        Args:
            path: File path to read from

        Returns:
            Result containing parsed dictionary or error message
        """
        try:
            with open(path) as f:
                vocab_dict = json.load(f)
            return Ok(vocab_dict)
        except Exception as e:
            return Err(f"Failed to read vocabulary from {path}: {e}")

    def _parse_vocabulary(self, vocab_dict: dict) -> Result[TfidfVocabulary, str]:
        """
        Parse vocabulary dictionary into Pydantic model.

        Args:
            vocab_dict: Dictionary from JSON deserialization

        Returns:
            Result containing TfidfVocabulary or error message
        """
        try:
            # Convert ISO string back to datetime
            if "created_at" in vocab_dict:
                vocab_dict["created_at"] = datetime.fromisoformat(vocab_dict["created_at"])
            vocab = TfidfVocabulary(**vocab_dict)
            return Ok(vocab)
        except Exception as e:
            return Err(f"Failed to parse vocabulary: {e}")
