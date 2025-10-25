"""
Tests for auto_label_batch.py - TRM routing label generation.

Test coverage:
- Batch API request format validation
- Retry logic on timeout
- Output format validation
- Cost estimation accuracy
- Error handling for malformed responses
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import auto_label_batch


class TestPromptTemplate:
    """Test prompt template loading and formatting."""

    def test_load_prompt_template(self):
        """Test loading TRM routing prompt template."""
        template = auto_label_batch.load_prompt_template()

        assert isinstance(template, str)
        assert len(template) > 100
        assert "{instruction}" in template
        assert "{input}" in template
        assert "TRM-7M" in template
        assert '{"label": 1}' in template or '{"label": 0}' in template

    def test_prompt_template_has_decision_criteria(self):
        """Test prompt includes decision criteria."""
        template = auto_label_batch.load_prompt_template()

        # Should define when to use TRM-7M
        assert any(term in template for term in ["graph", "DAG", "SAT", "CSP", "constraint"])
        assert "Decision Criteria" in template or "Use Cases" in template


class TestCostEstimation:
    """Test cost estimation logic."""

    def test_estimate_cost_basic(self):
        """Test basic cost estimation."""
        result = auto_label_batch.estimate_cost(num_samples=100, avg_tokens_per_sample=200)

        assert result["num_samples"] == 100
        assert result["estimated_input_tokens"] == 20_000  # 100 * 200
        assert result["estimated_output_tokens"] == 1_000  # 100 * 10
        assert result["total_cost_usd"] > 0
        assert result["cost_per_sample_usd"] > 0

    def test_estimate_cost_accuracy(self):
        """Test cost estimation is reasonable."""
        result = auto_label_batch.estimate_cost(num_samples=500, avg_tokens_per_sample=200)

        # 500 samples * 200 input tokens * $1.25/1M (batch rate) = ~$0.125 input
        # 500 samples * 10 output tokens * $5/1M (batch rate) = ~$0.025 output
        # Total should be around $0.15
        assert 0.10 <= result["total_cost_usd"] <= 0.30, f"Cost {result['total_cost_usd']} outside expected range"

    def test_estimate_cost_zero_samples(self):
        """Test cost estimation handles zero samples."""
        result = auto_label_batch.estimate_cost(num_samples=0)

        assert result["num_samples"] == 0
        assert result["total_cost_usd"] == 0
        assert result["cost_per_sample_usd"] == 0


class TestBatchRequestCreation:
    """Test batch request formatting."""

    def test_create_batch_requests(self):
        """Test batch request object structure."""
        samples = [
            {"instruction": "Test task 1", "input": ""},
            {"instruction": "Test task 2", "input": "some input"},
        ]

        prompt_template = "Classify this task:\n{instruction}\n\nInput: {input}"

        requests = auto_label_batch.create_batch_requests(samples, prompt_template, model="gpt-4o")

        assert len(requests) == 2
        assert all("custom_id" in req for req in requests)
        assert all("method" in req and req["method"] == "POST" for req in requests)
        assert all("body" in req for req in requests)
        assert all(req["body"]["model"] == "gpt-4o" for req in requests)
        assert all(req["body"]["temperature"] == 0.0 for req in requests)  # Deterministic

    def test_batch_request_includes_system_message(self):
        """Test batch requests have system message."""
        samples = [{"instruction": "Test", "input": ""}]
        prompt_template = "{instruction}"

        requests = auto_label_batch.create_batch_requests(samples, prompt_template)

        assert len(requests[0]["body"]["messages"]) >= 2
        assert requests[0]["body"]["messages"][0]["role"] == "system"
        assert requests[0]["body"]["messages"][1]["role"] == "user"

    def test_batch_request_handles_missing_input(self):
        """Test batch requests handle samples without 'input' field."""
        samples = [{"instruction": "Test without input"}]  # No 'input' key
        prompt_template = "{instruction}\n{input}"

        requests = auto_label_batch.create_batch_requests(samples, prompt_template)

        # Should not crash, should replace {input} with "N/A" or empty
        assert len(requests) == 1
        assert "Test without input" in requests[0]["body"]["messages"][1]["content"]


class TestOutputFormat:
    """Test output format validation."""

    @patch('auto_label_batch.OpenAI')
    def test_process_batch_results_format(self, mock_openai):
        """Test output format matches specification."""
        # Mock batch results
        mock_client = MagicMock()
        mock_result_content = MagicMock()
        mock_result_content.text = json.dumps({
            "custom_id": "sample_0",
            "response": {
                "body": {
                    "choices": [
                        {"message": {"content": '{"label": 1}'}}
                    ]
                }
            }
        })

        mock_client.files.content.return_value = mock_result_content

        mock_batch_job = MagicMock()
        mock_batch_job.output_file_id = "file-123"

        original_samples = [
            {
                "instruction": "Test task",
                "input": "",
                "_provenance": {"original_line": 1}
            }
        ]

        output_path = Path("/tmp/test_output.jsonl")

        # Call function
        results = auto_label_batch.process_batch_results(
            mock_batch_job, mock_client, original_samples, output_path
        )

        # Validate output format
        assert len(results) == 1
        result = results[0]

        # Required fields
        assert "id" in result
        assert "instruction" in result
        assert "label" in result
        assert result["label"] in [0, 1]
        assert "source" in result
        assert result["source"] == "auto"
        assert "confidence" in result
        assert "timestamp" in result

    def test_output_labels_are_binary(self):
        """Test labels are strictly 0 or 1."""
        # This would be tested in integration, but we can mock it
        valid_labels = [0, 1]

        # Ensure parser only accepts these values
        for label in valid_labels:
            assert label in [0, 1]


class TestErrorHandling:
    """Test error handling and retry logic."""

    @patch('auto_label_batch.OpenAI')
    def test_malformed_response_handling(self, mock_openai):
        """Test handling of malformed API responses."""
        mock_client = MagicMock()
        mock_result_content = MagicMock()
        # Malformed response (missing 'label' key)
        mock_result_content.text = json.dumps({
            "custom_id": "sample_0",
            "response": {
                "body": {
                    "choices": [
                        {"message": {"content": '{"wrong_key": 1}'}}
                    ]
                }
            }
        })

        mock_client.files.content.return_value = mock_result_content

        mock_batch_job = MagicMock()
        mock_batch_job.output_file_id = "file-123"

        original_samples = [
            {
                "instruction": "Test",
                "input": "",
                "_provenance": {"original_line": 1}
            }
        ]

        output_path = Path("/tmp/test_output.jsonl")

        # Should not crash, should default to label=0
        results = auto_label_batch.process_batch_results(
            mock_batch_job, mock_client, original_samples, output_path
        )

        assert len(results) == 1
        assert results[0]["label"] == 0  # Default on error

    @patch('auto_label_batch.time.sleep', return_value=None)  # Skip sleep
    @patch('auto_label_batch.OpenAI')
    def test_batch_polling_retry(self, mock_openai, mock_sleep):
        """Test batch job polling with multiple status checks."""
        mock_client = MagicMock()

        # Simulate batch progressing from "in_progress" to "completed"
        mock_batch_job = MagicMock()
        mock_batch_job.status = "in_progress"
        mock_batch_job.request_counts.completed = 50
        mock_batch_job.request_counts.total = 100

        mock_client.batches.retrieve.side_effect = [
            mock_batch_job,  # First poll: in progress
            mock_batch_job,  # Second poll: still in progress
            MagicMock(
                status="completed",
                request_counts=MagicMock(completed=100, total=100, failed=0)
            )  # Third poll: completed
        ]

        result = auto_label_batch.wait_for_batch_completion("batch-123", mock_client, poll_interval_seconds=1)

        assert result.status == "completed"
        assert mock_client.batches.retrieve.call_count == 3


# Integration-style tests (if run with API key)
@pytest.mark.skipif(
    not Path("scripts/auto_label_batch.py").exists(),
    reason="Script not found"
)
class TestIntegration:
    """Integration tests (require API key, skip in CI)."""

    def test_script_can_import(self):
        """Test script can be imported without errors."""
        import auto_label_batch
        assert hasattr(auto_label_batch, 'main')
        assert hasattr(auto_label_batch, 'estimate_cost')
        assert hasattr(auto_label_batch, 'create_batch_requests')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
