"""
Test EXECUTOR prompt generation for executable code emphasis.

Validates that EXECUTOR prompts guide agents to generate executable code
instead of pseudocode or abstract plans.
"""

import pytest

from trinity_protocol.core.executor import ExecutorAgent
from trinity_protocol.core.hybrid_executor import HybridExecutor, TaskType
from shared.agent_context import AgentContext
from shared.cost_tracker import CostTracker, MemoryStorage
from shared.message_bus import MessageBus


class TestExecutorPrompts:
    """Test EXECUTOR prompt generation and validation."""

    def test_executor_format_task_prompt_includes_executable_requirements(self):
        """Verify task prompt includes executable code requirements."""
        # Initialize executor
        message_bus = MessageBus()
        cost_tracker = CostTracker(storage=MemoryStorage())
        agent_context = AgentContext()

        executor = ExecutorAgent(
            message_bus=message_bus,
            cost_tracker=cost_tracker,
            agent_context=agent_context,
        )

        # Test prompt generation
        spec = {
            "goal": "Implement user authentication",
            "details": "Add JWT token validation",
            "requirements": "Must support refresh tokens",
        }

        prompt = executor._format_task_prompt(spec)

        # Assert critical requirements are present
        assert "EXECUTABLE CODE" in prompt
        assert "not pseudocode" in prompt
        assert "FORBIDDEN" in prompt
        assert "TODO" in prompt  # Listed as forbidden
        assert "VALIDATION" in prompt
        assert "production" in prompt.lower()

    def test_hybrid_executor_format_task_prompt_includes_agent_context(self):
        """Verify hybrid executor prompt includes agent-specific context."""
        # Initialize hybrid executor
        message_bus = MessageBus()
        cost_tracker = CostTracker(storage=MemoryStorage())
        agent_context = AgentContext()

        hybrid_executor = HybridExecutor(
            message_bus=message_bus,
            cost_tracker=cost_tracker,
            agent_context=agent_context,
        )

        # Test prompt generation
        from trinity_protocol.core.agent_registry import AgentType

        task = {
            "description": "Fix authentication bug",
            "target": "auth/validator.py",
        }

        prompt = hybrid_executor._format_task_prompt(task, AgentType.CODER)

        # Assert critical requirements are present
        assert "EXECUTABLE CODE" in prompt
        assert "coder agent" in prompt.lower()
        assert "production-ready" in prompt.lower()
        assert "Fix authentication bug" in prompt

    def test_validate_executable_code_detects_pseudocode(self):
        """Verify validation layer detects pseudocode markers."""
        # Initialize executor
        message_bus = MessageBus()
        cost_tracker = CostTracker(storage=MemoryStorage())
        agent_context = AgentContext()

        executor = ExecutorAgent(
            message_bus=message_bus,
            cost_tracker=cost_tracker,
            agent_context=agent_context,
        )

        # Test pseudocode detection
        pseudocode_examples = [
            "# TODO: Implement authentication logic here",
            "# Your code here",
            "Step 1: Validate user credentials\nStep 2: Generate token",
            "This is a high-level plan for implementing auth",
            "Pseudocode for login:\n  if user exists:\n    return token",
        ]

        for code in pseudocode_examples:
            is_valid, msg = executor._validate_executable_code(code)
            assert not is_valid, f"Should detect pseudocode in: {code[:50]}"
            assert "pseudocode" in msg.lower() or "short" in msg.lower()

    def test_validate_executable_code_accepts_valid_python(self):
        """Verify validation layer accepts valid Python code."""
        # Initialize executor
        message_bus = MessageBus()
        cost_tracker = CostTracker(storage=MemoryStorage())
        agent_context = AgentContext()

        executor = ExecutorAgent(
            message_bus=message_bus,
            cost_tracker=cost_tracker,
            agent_context=agent_context,
        )

        # Test valid Python code
        valid_code = '''
def authenticate_user(username: str, password: str) -> dict:
    """Authenticate user and return JWT token."""
    import hashlib

    # Hash password (production would use bcrypt)
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Validate credentials (production would check database)
    if username and password_hash:
        return {"token": "jwt_token_here", "user_id": username}

    raise ValueError("Invalid credentials")
'''

        is_valid, msg = executor._validate_executable_code(valid_code)
        assert is_valid, f"Should accept valid Python code: {msg}"
        assert "valid" in msg.lower()

    def test_validate_executable_code_detects_syntax_errors(self):
        """Verify validation layer detects Python syntax errors."""
        # Initialize executor
        message_bus = MessageBus()
        cost_tracker = CostTracker(storage=MemoryStorage())
        agent_context = AgentContext()

        executor = ExecutorAgent(
            message_bus=message_bus,
            cost_tracker=cost_tracker,
            agent_context=agent_context,
        )

        # Test invalid Python syntax
        invalid_code = '''
def broken_function(:
    return "missing parameter"
'''

        is_valid, msg = executor._validate_executable_code(invalid_code)
        assert not is_valid, "Should detect syntax errors"
        assert "syntax" in msg.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
