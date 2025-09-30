"""
DSPy Configuration Manager

CONSTITUTIONAL COMPLIANCE:
- Article I: Complete Context - Centralized LM configuration
- Article III: Automated Enforcement - Auto-configures DSPy on import
- Article IV: Continuous Learning - Tracks model performance

This module provides centralized configuration for DSPy Language Models,
ensuring all agents use consistent model settings and proper initialization.
"""

import os
import logging
from typing import Optional, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)

# Check if DSPy is available
try:
    import dspy
    from dspy import LM
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    logger.warning("DSPy not available - agents will run in fallback mode")


class DSPyConfig:
    """Centralized DSPy configuration management."""

    _initialized = False
    _lm_cache: Dict[str, object] = {}

    @classmethod
    def initialize(cls, force: bool = False) -> bool:
        """
        Initialize DSPy with appropriate Language Model configuration.

        CONSTITUTIONAL REQUIREMENT: Article III - Automated Enforcement
        Ensures DSPy is properly configured before any agent execution.

        Args:
            force: Force re-initialization even if already initialized

        Returns:
            bool: True if successfully initialized, False otherwise
        """
        if cls._initialized and not force:
            logger.debug("DSPy already initialized")
            return True

        if not DSPY_AVAILABLE:
            logger.warning("DSPy not available - cannot initialize")
            return False

        try:
            # Get API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Try alternative keys
                api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LITELLM_API_KEY")

            if not api_key:
                logger.error("No API key found for DSPy LM configuration")
                logger.info("Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or LITELLM_API_KEY")
                return False

            # Get model from environment or use default
            model_name = os.getenv("DSPY_MODEL", "openai/gpt-4o-mini")

            # Map Agency model names to DSPy format
            model_mapping = {
                "gpt-5": "openai/gpt-4o",  # Map to available model
                "gpt-5-mini": "openai/gpt-4o-mini",
                "gpt-4": "openai/gpt-4",
                "claude-sonnet": "anthropic/claude-3-sonnet",
                "claude-opus": "anthropic/claude-3-opus"
            }

            # Apply mapping if needed
            if model_name in model_mapping:
                actual_model = model_mapping[model_name]
                logger.info(f"Mapping {model_name} -> {actual_model}")
                model_name = actual_model

            # Initialize the Language Model
            logger.info(f"Initializing DSPy with model: {model_name}")

            # Create LM instance with proper configuration
            # Set temperature to 1 for gpt-4o models (they don't support other values)
            temperature = 1.0 if "gpt-4o" in model_name else 0.7

            lm = LM(
                model=model_name,
                api_key=api_key,
                max_tokens=4096,
                temperature=temperature,
                cache=True  # Enable caching for efficiency
            )

            # Configure DSPy globally
            dspy.configure(lm=lm)

            # Cache the LM for reuse
            cls._lm_cache[model_name] = lm
            cls._initialized = True

            logger.info(f"DSPy successfully initialized with {model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize DSPy: {str(e)}")
            logger.debug("Fallback mode will be used for DSPy agents")
            return False

    @classmethod
    def get_lm(cls, model_name: Optional[str] = None) -> Optional[Any]:
        """
        Get a configured Language Model instance.

        Args:
            model_name: Specific model to retrieve, or None for default

        Returns:
            Configured LM instance or None if not available
        """
        if not DSPY_AVAILABLE:
            return None

        if not cls._initialized:
            cls.initialize()

        if model_name and model_name in cls._lm_cache:
            return cls._lm_cache[model_name]

        # Return the default configured LM
        try:
            return dspy.settings.lm
        except:
            return None

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if DSPy is initialized."""
        return cls._initialized

    @classmethod
    def reset(cls):
        """Reset configuration (mainly for testing)."""
        cls._initialized = False
        cls._lm_cache.clear()
        logger.info("DSPy configuration reset")


def configure_dspy_for_agent(agent_type: str = "default") -> bool:
    """
    Configure DSPy for a specific agent type.

    Different agents may need different model configurations.
    This function provides agent-specific initialization.

    Args:
        agent_type: Type of agent (planner, coder, auditor, etc.)

    Returns:
        bool: True if configuration successful
    """
    # Map agent types to preferred models
    agent_model_map = {
        "planner": os.getenv("PLANNER_MODEL", "openai/gpt-4o"),
        "coder": os.getenv("CODER_MODEL", "openai/gpt-4o-mini"),
        "auditor": os.getenv("AUDITOR_MODEL", "openai/gpt-4o-mini"),
        "toolsmith": os.getenv("TOOLSMITH_MODEL", "openai/gpt-4o-mini"),
        "learning": os.getenv("LEARNING_MODEL", "openai/gpt-4o-mini"),
        "default": os.getenv("DSPY_MODEL", "openai/gpt-4o-mini")
    }

    model = agent_model_map.get(agent_type, agent_model_map["default"])

    # Set the model in environment for DSPyConfig to use
    os.environ["DSPY_MODEL"] = model

    return DSPyConfig.initialize(force=True)


# Auto-initialize on import if environment is ready
def auto_initialize():
    """
    Automatically initialize DSPy if environment variables are set.

    CONSTITUTIONAL REQUIREMENT: Article III - Automated Enforcement
    """
    if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        if os.getenv("AUTO_INIT_DSPY", "true").lower() == "true":
            logger.debug("Auto-initializing DSPy configuration")
            DSPyConfig.initialize()
    else:
        logger.debug("No API keys found - DSPy initialization deferred")


# Perform auto-initialization
auto_initialize()


# Export main components
__all__ = [
    "DSPyConfig",
    "configure_dspy_for_agent",
    "DSPY_AVAILABLE"
]