"""End-to-end tests for self-healing infrastructure.

Tests the full self-healing cycle:
1. Health monitoring
2. Issue detection
3. Auto-healing
4. VLM integration
5. Daemon mode

These tests verify AgencyOS can maintain itself autonomously.
"""

import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestSelfHealingE2E:
    """End-to-end tests for self-healing infrastructure."""

    @pytest.mark.skip(reason="Runs full pytest suite - too slow for integration tests")
    def test_health_check_reports_passing_tests(self):
        """Test that health check correctly reports test pass rate."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()
        result = monitor.check_health()

        assert result.is_ok(), f"Health check failed: {result.unwrap_err()}"

        report = result.unwrap()
        assert report.test_pass_rate >= 0.95, f"Pass rate too low: {report.test_pass_rate}"
        assert report.tests_passed > 0, "No tests passed"
        assert report.collection_errors == 0, f"Collection errors: {report.collection_errors}"

    @pytest.mark.skip(reason="Runs full pytest suite - too slow for integration tests")
    def test_generate_report_is_readable(self):
        """Test that generated report is human-readable."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()
        report = monitor.generate_report()

        assert "AgencyOS Health Report" in report
        assert "Test Pass Rate" in report
        assert "Passed" in report

    def test_vlm_health_check_works(self):
        """Test VLM health check with real LM Studio if available."""
        from tools.self_healing_monitor import check_vlm_health

        status = check_vlm_health()

        assert "overall" in status
        assert "checks" in status
        assert "timestamp" in status

        # If VLM is available, verify it's healthy
        if status.get("overall") == "healthy":
            assert status["checks"]["api"]["status"] == "ok"
            assert status["checks"]["embedding"]["status"] == "ok"
            assert status["checks"]["embedding"]["dimension"] == 768

    def test_import_fixes_mapping_comprehensive(self):
        """Test that IMPORT_FIXES covers common packages."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()
        fixes = monitor.IMPORT_FIXES

        # Essential packages should be mapped
        essential = ["agents", "sklearn", "psutil", "watchdog", "faiss"]
        for pkg in essential:
            assert pkg in fixes, f"Missing fix for {pkg}"

    @pytest.mark.skip(reason="Runs full pytest suite - too slow for integration tests")
    def test_auto_heal_dry_run_safe(self):
        """Test that auto_heal dry run doesn't modify anything."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()

        # Dry run should be safe
        result = monitor.auto_heal(dry_run=True)

        assert result.is_ok(), f"Dry run failed: {result.unwrap_err()}"

        fixes = result.unwrap()
        for fix in fixes:
            # Dry run fixes should not actually run
            assert "Would run" in fix.description


class TestVLMIntegrationE2E:
    """End-to-end tests for VLM integration."""

    def test_vlm_client_initialization(self):
        """Test VLMClient initializes correctly."""
        from tools.vlm_integration import VLMClient

        client = VLMClient()

        assert client.config is not None
        assert "1234/v1" in client.config.api_base  # Works with localhost or remote
        assert client.provider is not None
        assert client.predictor is not None

    @pytest.mark.skip(reason="May hang loading sentence-transformers models")
    def test_semantic_embedding_with_fallback(self):
        """Test that semantic embedding works with sentence-transformers fallback."""
        from tools.vlm_integration import VLMClient

        client = VLMClient()

        # This should work even if LM Studio is not available
        # (falls back to sentence-transformers)
        result = client.encode_text("Test embedding for authentication bug fix")

        assert result.is_ok(), f"Encode failed: {result.unwrap_err()}"

        embedding = result.unwrap()
        assert embedding.vector.shape[0] in [384, 768], f"Unexpected dim: {embedding.vector.shape}"
        assert embedding.source_type == "text"
        assert embedding.confidence > 0

    def test_semantic_predictor_embedding(self):
        """Test SemanticPredictor generates embeddings."""
        from tools.vlm_integration import SemanticPredictor

        predictor = SemanticPredictor()

        result = predictor.predict_embedding(
            query="How to fix NoneType error?",
            context="File: auth.py, Line 42",
        )

        assert result.is_ok(), f"Prediction failed: {result.unwrap_err()}"

        embedding = result.unwrap()
        assert embedding.source_type == "predicted"
        assert embedding.metadata.get("method") == "semantic_predictor"

    def test_should_decode_logic(self):
        """Test selective decoding logic (VLJA concept)."""
        from tools.vlm_integration import SemanticPredictor, SemanticEmbedding
        import numpy as np

        predictor = SemanticPredictor()

        # Same embedding should not trigger decode
        vector = np.random.randn(384).astype(np.float32)
        same = SemanticEmbedding(
            vector=vector,
            source_type="text",
            confidence=0.9,
            metadata={},
        )

        # First time should always decode
        assert predictor.should_decode(same, None) == True

        # Same embedding should not decode
        assert predictor.should_decode(same, same, threshold=0.3) == False


class TestDaemonModeE2E:
    """End-to-end tests for daemon mode."""

    def test_daemon_single_cycle(self):
        """Test daemon runs single cycle successfully."""
        from tools.self_healing_monitor import run_daemon, SelfHealingMonitor
        from tools.self_healing_monitor import HealthReport, check_vlm_health
        from shared.type_definitions.result import Ok
        from datetime import datetime

        # Mock the health checks to avoid long test times
        with patch.object(SelfHealingMonitor, "check_health") as mock_check:
            with patch("tools.self_healing_monitor.check_vlm_health") as mock_vlm:
                with patch("time.sleep"):
                    mock_check.return_value = Ok(HealthReport(
                        timestamp=datetime.now(),
                        test_pass_rate=1.0,
                        tests_passed=400,
                        tests_failed=0,
                        tests_skipped=0,
                        tests_error=0,
                        collection_errors=0,
                        issues_detected=[],
                        recommendations=[],
                        auto_fixable=[],
                    ))

                    mock_vlm.return_value = {"overall": "healthy", "checks": {}}

                    # Run single cycle - should complete without error
                    run_daemon(interval_seconds=1, max_cycles=1)

                    assert mock_check.call_count == 1
                    assert mock_vlm.call_count == 1


class TestSemanticSimilarityE2E:
    """End-to-end tests for semantic similarity (VLJA validation)."""

    @pytest.mark.skipif(
        not Path("/Users/am/Code/AgencyOS").exists(),
        reason="Only run on development machine"
    )
    def test_similar_errors_cluster_together(self):
        """Test that similar error descriptions have higher similarity."""
        try:
            from openai import OpenAI
            import numpy as np

            client = OpenAI(
                api_key="lm-studio",
                base_url="http://127.0.0.1:1234/v1",
                timeout=10.0,
            )

            # Test connectivity first
            try:
                client.models.list()
            except Exception:
                pytest.skip("LM Studio not available")

            texts = [
                "Fix NoneType error in authentication",
                "Resolve None attribute access in auth module",
                "Add new button to dashboard UI",
            ]

            embeddings = []
            for text in texts:
                response = client.embeddings.create(
                    model="text-embedding-nomic-embed-text-v1.5",
                    input=text,
                )
                embeddings.append(np.array(response.data[0].embedding))

            def cosine_sim(a, b):
                return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

            similar = cosine_sim(embeddings[0], embeddings[1])
            different = cosine_sim(embeddings[0], embeddings[2])

            # Similar errors should have higher similarity
            assert similar > different, f"VLJA failed: {similar} <= {different}"

        except ImportError:
            pytest.skip("OpenAI client not available")
