"""Unit tests for VLM integration module.

Tests the VLMClient, SemanticPredictor, and related classes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestVLMConfig:
    """Tests for VLMConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        from tools.vlm_integration import VLMConfig

        config = VLMConfig()

        assert config.model_name == "vcoder-120b-1.0-hi-mlx"
        assert config.api_base == "http://127.0.0.1:1234/v1"
        assert config.embedding_model == "text-embedding-nomic-embed-text-v1.5"
        assert config.embedding_dim == 768
        assert config.temperature == 0.1
        assert config.timeout_seconds == 120

    def test_custom_values(self):
        """Test custom configuration values."""
        from tools.vlm_integration import VLMConfig

        config = VLMConfig(
            model_name="custom-model",
            api_base="http://localhost:8080/v1",
            embedding_dim=512,
        )

        assert config.model_name == "custom-model"
        assert config.api_base == "http://localhost:8080/v1"
        assert config.embedding_dim == 512


class TestSemanticEmbedding:
    """Tests for SemanticEmbedding dataclass."""

    def test_embedding_structure(self):
        """Test SemanticEmbedding dataclass structure."""
        from tools.vlm_integration import SemanticEmbedding

        vector = np.random.randn(768).astype(np.float32)
        embedding = SemanticEmbedding(
            vector=vector,
            source_type="text",
            confidence=0.95,
            metadata={"text_preview": "test"},
        )

        assert embedding.vector.shape == (768,)
        assert embedding.source_type == "text"
        assert embedding.confidence == 0.95
        assert "text_preview" in embedding.metadata


class TestSemanticPredictor:
    """Tests for SemanticPredictor class."""

    def test_predict_embedding_returns_result(self):
        """Test that predict_embedding returns a Result."""
        from tools.vlm_integration import SemanticPredictor

        predictor = SemanticPredictor()

        with patch.object(predictor, "_get_encoder") as mock_encoder:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.random.randn(384)
            mock_encoder.return_value = mock_model

            result = predictor.predict_embedding("test query")

            assert hasattr(result, "is_ok")
            assert hasattr(result, "is_err")

    def test_should_decode_first_time(self):
        """Test that should_decode returns True for first embedding."""
        from tools.vlm_integration import SemanticPredictor, SemanticEmbedding

        predictor = SemanticPredictor()

        current = SemanticEmbedding(
            vector=np.random.randn(384).astype(np.float32),
            source_type="text",
            confidence=0.9,
            metadata={},
        )

        # Should decode on first time (no previous)
        assert predictor.should_decode(current, None) is True

    def test_should_decode_semantic_shift(self):
        """Test that should_decode detects semantic shifts."""
        from tools.vlm_integration import SemanticPredictor, SemanticEmbedding

        predictor = SemanticPredictor()

        # Two very different embeddings (high distance)
        current = SemanticEmbedding(
            vector=np.array([1.0, 0.0, 0.0] + [0.0] * 381, dtype=np.float32),
            source_type="text",
            confidence=0.9,
            metadata={},
        )
        previous = SemanticEmbedding(
            vector=np.array([0.0, 1.0, 0.0] + [0.0] * 381, dtype=np.float32),
            source_type="text",
            confidence=0.9,
            metadata={},
        )

        # Should decode when there's a semantic shift
        assert predictor.should_decode(current, previous, threshold=0.3) == True

    def test_should_not_decode_similar(self):
        """Test that should_decode returns False for similar embeddings."""
        from tools.vlm_integration import SemanticPredictor, SemanticEmbedding

        predictor = SemanticPredictor()

        # Two very similar embeddings
        vector = np.random.randn(384).astype(np.float32)
        current = SemanticEmbedding(
            vector=vector,
            source_type="text",
            confidence=0.9,
            metadata={},
        )
        previous = SemanticEmbedding(
            vector=vector + np.random.randn(384).astype(np.float32) * 0.01,  # Small noise
            source_type="text",
            confidence=0.9,
            metadata={},
        )

        # Should not decode when embeddings are similar
        assert predictor.should_decode(current, previous, threshold=0.3) == False


class TestLMStudioVLMProvider:
    """Tests for LMStudioVLMProvider class."""

    def test_encode_image_file_not_found(self):
        """Test that encode_image returns Err for missing file."""
        from tools.vlm_integration import LMStudioVLMProvider, VLMConfig

        config = VLMConfig()
        provider = LMStudioVLMProvider(config)

        result = provider.encode_image("/nonexistent/path/image.png")

        assert result.is_err()
        assert "not found" in result.unwrap_err()

    def test_encode_text_returns_result(self):
        """Test that encode_text returns a Result."""
        from tools.vlm_integration import LMStudioVLMProvider, VLMConfig

        config = VLMConfig()
        provider = LMStudioVLMProvider(config)

        with patch.object(provider, "_text_to_embedding") as mock_embed:
            mock_embed.return_value = np.random.randn(768).astype(np.float32)

            result = provider.encode_text("test text")

            assert result.is_ok()
            embedding = result.unwrap()
            assert embedding.source_type == "text"
            assert embedding.confidence == 0.95


class TestVLMClient:
    """Tests for VLMClient class."""

    def test_client_initialization(self):
        """Test VLMClient initialization."""
        from tools.vlm_integration import VLMClient

        client = VLMClient()

        assert client.config is not None
        assert client.provider is not None
        assert client.predictor is not None

    def test_client_with_custom_model(self):
        """Test VLMClient with custom model name."""
        from tools.vlm_integration import VLMClient

        client = VLMClient(model="custom-model")

        assert client.config.model_name == "custom-model"

    def test_client_with_custom_api_base(self):
        """Test VLMClient with custom API base."""
        from tools.vlm_integration import VLMClient

        client = VLMClient(api_base="http://custom:8080/v1")

        assert client.config.api_base == "http://custom:8080/v1"

    def test_encode_text_delegates_to_provider(self):
        """Test that encode_text delegates to provider."""
        from tools.vlm_integration import VLMClient

        client = VLMClient()

        with patch.object(client.provider, "encode_text") as mock_encode:
            from shared.type_definitions.result import Ok
            from tools.vlm_integration import SemanticEmbedding

            mock_encode.return_value = Ok(SemanticEmbedding(
                vector=np.random.randn(768).astype(np.float32),
                source_type="text",
                confidence=0.95,
                metadata={},
            ))

            result = client.encode_text("test")

            mock_encode.assert_called_once_with("test")

    def test_health_check_returns_result(self):
        """Test that health_check returns a Result."""
        from tools.vlm_integration import VLMClient

        client = VLMClient()

        with patch.object(client.provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Mock models.list
            mock_models = MagicMock()
            mock_models.data = [{"id": "model1"}]
            mock_client.models.list.return_value = mock_models

            # Mock encode_text
            with patch.object(client, "encode_text") as mock_encode:
                from shared.type_definitions.result import Ok
                from tools.vlm_integration import SemanticEmbedding

                mock_encode.return_value = Ok(SemanticEmbedding(
                    vector=np.random.randn(768).astype(np.float32),
                    source_type="text",
                    confidence=0.95,
                    metadata={},
                ))

                # Mock query
                with patch.object(client, "query") as mock_query:
                    mock_query.return_value = Ok("healthy")

                    result = client.health_check()

                    assert result.is_ok()
                    status = result.unwrap()
                    assert "overall" in status
                    assert "checks" in status


class TestSemanticSimilarity:
    """Tests for semantic similarity functionality."""

    def test_cosine_similarity_identical(self):
        """Test cosine similarity for identical vectors."""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])

        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        assert abs(similarity - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity for orthogonal vectors."""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])

        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        assert abs(similarity) < 1e-6

    def test_cosine_similarity_opposite(self):
        """Test cosine similarity for opposite vectors."""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([-1.0, 0.0, 0.0])

        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        assert abs(similarity - (-1.0)) < 1e-6
