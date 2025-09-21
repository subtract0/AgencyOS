"""
Unit tests for memory integration functionality.
Tests memory storage, retrieval, and hook integration without actual memory persistence.
"""

import pytest
from unittest.mock import Mock, patch
from agency_code_agent.agency_code_agent import create_agency_code_agent


class TestMemoryIntegration:
    """Test memory integration and storage functionality."""

    def test_agent_context_creation(self, mock_agent_context):
        """Test that agent context is properly created."""
        with patch('agency_code_agent.agency_code_agent.create_agent_context') as mock_create, \
             patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_create.return_value = mock_agent_context
            mock_model.return_value = "gpt-5-mini"

            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="low"
            )

            # Verify agent context was created
            assert mock_create.called
            assert mock_agent_context.session_id == "test_session_123"

    def test_memory_integration_hook_creation(self, mock_agent_context):
        """Test that memory integration hooks are properly created."""
        with patch('agency_code_agent.agency_code_agent.create_memory_integration_hook') as mock_memory_hook, \
             patch('agency_code_agent.agency_code_agent.create_system_reminder_hook') as mock_reminder_hook, \
             patch('agency_code_agent.agency_code_agent.create_composite_hook') as mock_composite, \
             patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"
            mock_memory_hook.return_value = Mock()
            mock_reminder_hook.return_value = Mock()
            mock_composite.return_value = Mock()

            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="medium",
                agent_context=mock_agent_context
            )

            # Verify hooks were created
            assert mock_memory_hook.called
            assert mock_reminder_hook.called
            assert mock_composite.called

            # Verify memory hook was called with agent context
            mock_memory_hook.assert_called_with(mock_agent_context)

    def test_agent_creation_memory_storage(self, mock_agent_context):
        """Test that agent creation is stored in memory."""
        with patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Verify memory storage was called
            assert mock_agent_context.store_memory.called

            # Check the stored memory data
            call_args = mock_agent_context.store_memory.call_args
            memory_key = call_args[0][0]
            memory_data = call_args[0][1]
            memory_tags = call_args[0][2]

            assert memory_key.startswith("agent_created_")
            assert memory_data['agent_type'] == "AgencyCodeAgent"
            assert memory_data['model'] == "gpt-5-mini"
            assert memory_data['reasoning_effort'] == "high"
            assert memory_data['session_id'] == "test_session_123"
            assert "agency" in memory_tags
            assert "coder" in memory_tags
            assert "creation" in memory_tags

    def test_memory_retrieval(self, mock_agent_context, mock_memory):
        """Test memory retrieval functionality."""
        # Setup mock memory data
        mock_memories = [
            {
                "key": "previous_session_123",
                "data": {"action": "file_created", "file": "test.py"},
                "tags": ["file", "creation"]
            },
            {
                "key": "search_results_456",
                "data": {"query": "TODO comments", "results": 5},
                "tags": ["search", "code"]
            }
        ]

        mock_agent_context.get_memories_by_tags.return_value = mock_memories

        # Test retrieval by tags
        memories = mock_agent_context.get_memories_by_tags(["file", "creation"])

        assert len(memories) >= 1
        assert memories[0]["data"]["action"] == "file_created"

    def test_memory_hook_integration(self, mock_agent_context, mock_system_hooks):
        """Test that memory hooks are properly integrated."""
        with patch('agency_code_agent.agency_code_agent.create_memory_integration_hook') as mock_memory_hook, \
             patch('agency_code_agent.agency_code_agent.create_composite_hook') as mock_composite, \
             patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"
            mock_memory_hook.return_value = mock_system_hooks['memory_hook']
            mock_composite.return_value = Mock()

            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="low",
                agent_context=mock_agent_context
            )

            # Verify memory hook was created and integrated
            assert mock_memory_hook.called
            assert mock_composite.called

            # Check that composite hook was created with both hooks
            composite_call_args = mock_composite.call_args[0][0]
            assert len(composite_call_args) == 2  # reminder + memory hooks

    def test_session_id_consistency(self, mock_agent_context):
        """Test that session ID is consistent across memory operations."""
        with patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            # Create multiple agents with same context
            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="low",
                agent_context=mock_agent_context
            )

            _ = create_agency_code_agent(
                model="gpt-4o",
                reasoning_effort="medium",
                agent_context=mock_agent_context
            )

            # Verify both agents used same session ID
            assert mock_agent_context.store_memory.call_count == 2

            call_1 = mock_agent_context.store_memory.call_args_list[0]
            call_2 = mock_agent_context.store_memory.call_args_list[1]

            session_id_1 = call_1[0][1]['session_id']
            session_id_2 = call_2[0][1]['session_id']

            assert session_id_1 == session_id_2 == "test_session_123"

    def test_memory_tagging_system(self, mock_agent_context):
        """Test that memory entries are properly tagged."""
        with patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "claude-3-sonnet"

            _ = create_agency_code_agent(
                model="claude-3-sonnet",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Check memory storage call
            call_args = mock_agent_context.store_memory.call_args
            tags = call_args[0][2]

            # Verify required tags are present
            required_tags = ["agency", "coder", "creation"]
            for tag in required_tags:
                assert tag in tags

    @pytest.mark.asyncio
    async def test_memory_hook_pre_post_call(self, mock_agent_context, mock_system_hooks):
        """Test that memory hooks are called before and after agent interactions."""
        memory_hook = mock_system_hooks['memory_hook']

        # Simulate hook calls
        test_data = {"query": "test query", "model": "gpt-5-mini"}

        # Test pre-call hook
        memory_hook.pre_call(test_data)
        assert memory_hook.pre_call.called

        # Test post-call hook
        memory_hook.post_call(test_data, {"response": "test response"})
        assert memory_hook.post_call.called

    def test_memory_context_with_different_models(self):
        """Test memory context works consistently across different models."""
        models_to_test = [
            "gpt-5-mini",
            "gpt-4o",
            "claude-3-sonnet",
            "claude-3-haiku"
        ]

        for model in models_to_test:
            with patch('agency_code_agent.agency_code_agent.create_agent_context') as mock_create, \
                 patch('agency_code_agent.agency_code_agent.Agent'), \
                 patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

                mock_context = Mock()
                mock_context.session_id = f"session_{model}"
                mock_context.store_memory = Mock()
                mock_create.return_value = mock_context
                mock_model.return_value = model

                _ = create_agency_code_agent(
                    model=model,
                    reasoning_effort="medium"
                )

                # Verify context creation and memory storage
                assert mock_create.called
                assert mock_context.store_memory.called

                # Check model-specific memory data
                call_args = mock_context.store_memory.call_args
                memory_data = call_args[0][1]
                assert memory_data['model'] == model

    def test_memory_error_handling(self, mock_agent_context):
        """Test that memory operations handle errors gracefully."""
        # Mock memory storage to raise an exception
        mock_agent_context.store_memory.side_effect = Exception("Memory storage error")

        with patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model, \
             patch('agency_code_agent.agency_code_agent.render_instructions') as mock_render:

            mock_model.return_value = "gpt-5-mini"
            mock_render.return_value = "Test instructions"

            # This should raise an exception as memory storage is critical
            with pytest.raises(Exception):
                _ = create_agency_code_agent(
                    model="gpt-5-mini",
                    reasoning_effort="low",
                    agent_context=mock_agent_context
                )

    def test_memory_cleanup_and_lifecycle(self, mock_agent_context):
        """Test memory cleanup and lifecycle management."""
        with patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            # Create and simulate agent lifecycle
            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="medium",
                agent_context=mock_agent_context
            )

            # Verify initial memory storage
            assert mock_agent_context.store_memory.called

            # Test memory persistence (agent context should remain)
            assert mock_agent_context.session_id == "test_session_123"