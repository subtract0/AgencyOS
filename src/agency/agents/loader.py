"""
AgentLoader - Hybrid DSPy/Traditional Implementation Loader

Implements ADR-007: DSPy Agent Loader - Hybrid Architecture
Constitutional Compliance: Articles I, II, IV, V

This loader:
1. Parses frontmatter from .claude/agents/*.md files
2. Instantiates preferred implementation (DSPy or traditional)
3. Falls back gracefully when DSPy unavailable
4. Wraps with telemetry for performance comparison
5. Maintains markdown as source of truth
"""

import logging
import time
import yaml
import importlib
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# Check DSPy availability
try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

logger = logging.getLogger(__name__)


# Custom Exceptions
class LoaderError(Exception):
    """Base exception for loader errors."""
    pass


# Pydantic Models for Frontmatter
class ImplementationConfig(BaseModel):
    """Configuration for agent implementations."""
    traditional: str = Field(..., description="Path to traditional implementation")
    dspy: str = Field(..., description="Path to DSPy implementation")
    preferred: Literal["dspy", "traditional"] = Field(..., description="Preferred implementation")
    features: Dict[str, list[str]] = Field(default_factory=dict, description="Feature lists per implementation")


class RolloutConfig(BaseModel):
    """Configuration for rollout strategy."""
    status: str = Field(..., description="Rollout status (gradual, complete, etc)")
    fallback: Literal["traditional", "none"] = Field(..., description="Fallback strategy")
    comparison: bool = Field(..., description="Whether to enable telemetry comparison")


class AgentFrontmatter(BaseModel):
    """Parsed frontmatter from agent markdown files."""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    implementation: ImplementationConfig
    rollout: RolloutConfig


# Telemetry Wrapper
class TelemetryWrapper:
    """
    Wraps an agent to collect performance telemetry.
    
    Enables comparison between DSPy and traditional implementations
    per Constitution Article IV (Continuous Learning).
    """
    
    def __init__(self, agent: Any, implementation_type: str):
        """
        Initialize telemetry wrapper.
        
        Args:
            agent: The agent instance to wrap
            implementation_type: "dspy" or "traditional"
        """
        self._agent = agent
        self.implementation_type = implementation_type
        self.call_count = 0
        self.error_count = 0
        self.last_latency_ms = 0.0
        self.total_latency_ms = 0.0
        
        logger.info(f"TelemetryWrapper initialized for {implementation_type} agent")
    
    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to wrapped agent with telemetry.
        
        Tracks:
        - Call count
        - Latency
        - Error rate
        """
        attr = getattr(self._agent, name)
        
        # If it's a callable, wrap it with telemetry
        if callable(attr):
            def telemetry_wrapper(*args, **kwargs):
                self.call_count += 1
                start_time = time.perf_counter()
                
                try:
                    result = attr(*args, **kwargs)
                    end_time = time.perf_counter()
                    self.last_latency_ms = (end_time - start_time) * 1000
                    self.total_latency_ms += self.last_latency_ms
                    
                    logger.debug(
                        f"{self.implementation_type}.{name} completed in {self.last_latency_ms:.2f}ms"
                    )
                    
                    return result
                    
                except Exception as e:
                    self.error_count += 1
                    end_time = time.perf_counter()
                    self.last_latency_ms = (end_time - start_time) * 1000
                    
                    logger.error(
                        f"{self.implementation_type}.{name} failed after {self.last_latency_ms:.2f}ms: {e}"
                    )
                    raise
            
            return telemetry_wrapper
        
        return attr
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected telemetry metrics."""
        return {
            "implementation": self.implementation_type,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "last_latency_ms": self.last_latency_ms,
            "total_latency_ms": self.total_latency_ms,
            "avg_latency_ms": self.total_latency_ms / self.call_count if self.call_count > 0 else 0,
            "error_rate": self.error_count / self.call_count if self.call_count > 0 else 0
        }


# Main AgentLoader Class
class AgentLoader:
    """
    Loads agents with hybrid DSPy/traditional implementation support.
    
    Per ADR-007, this loader:
    - Parses frontmatter from markdown files
    - Selects preferred implementation
    - Falls back gracefully
    - Wraps with telemetry when enabled
    - Maintains constitutional compliance
    """
    
    def __init__(self):
        """Initialize the agent loader."""
        self.loaded_agents: Dict[str, Any] = {}
        logger.info(f"AgentLoader initialized (DSPy available: {DSPY_AVAILABLE})")
    
    def _parse_frontmatter(self, agent_path: str) -> AgentFrontmatter:
        """
        Parse YAML frontmatter from agent markdown file.
        
        Args:
            agent_path: Path to agent .md file
            
        Returns:
            Parsed AgentFrontmatter
            
        Raises:
            LoaderError: If file not found, invalid YAML, or missing required fields
        """
        file_path = Path(agent_path)
        
        # Check file exists
        if not file_path.exists():
            raise LoaderError(f"File not found: {agent_path}")
        
        try:
            content = file_path.read_text()
            
            # Extract frontmatter between --- markers
            if not content.startswith("---"):
                raise LoaderError(f"No frontmatter found in {agent_path}")
            
            parts = content.split("---", 2)
            if len(parts) < 3:
                raise LoaderError(f"Invalid frontmatter format in {agent_path}")
            
            frontmatter_text = parts[1]
            
            # Parse YAML
            try:
                frontmatter_dict = yaml.safe_load(frontmatter_text)
            except yaml.YAMLError as e:
                raise LoaderError(f"Invalid YAML in {agent_path}: {e}")
            
            # Validate required fields
            required_fields = ["name", "description", "implementation", "rollout"]
            missing = [f for f in required_fields if f not in frontmatter_dict]
            if missing:
                raise LoaderError(f"Missing required field(s): {', '.join(missing)}")
            
            # Parse into Pydantic model
            return AgentFrontmatter(**frontmatter_dict)
            
        except Exception as e:
            if isinstance(e, LoaderError):
                raise
            raise LoaderError(f"Error parsing frontmatter from {agent_path}: {e}")
    
    def _parse_body(self, agent_path: str) -> str:
        """
        Extract markdown body (after frontmatter).
        
        Args:
            agent_path: Path to agent .md file
            
        Returns:
            Markdown body text
        """
        file_path = Path(agent_path)
        content = file_path.read_text()
        
        # Split on frontmatter delimiters
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
        
        return content
    
    def _check_dspy_available(self) -> bool:
        """
        Check if DSPy is available.
        
        Constitutional compliance (Article I): Complete context before action.
        MUST verify DSPy availability before attempting to load.
        
        Returns:
            True if DSPy is available, False otherwise
        """
        return DSPY_AVAILABLE
    
    def _load_dspy_agent(
        self,
        dspy_path: str,
        markdown_spec: str,
        frontmatter: AgentFrontmatter
    ) -> Any:
        """
        Load DSPy implementation of agent.
        
        Args:
            dspy_path: Path to DSPy implementation module
            markdown_spec: Markdown specification for agent
            frontmatter: Parsed frontmatter
            
        Returns:
            Instantiated DSPy agent
            
        Raises:
            Exception: If loading fails
        """
        logger.info(f"Loading DSPy agent from {dspy_path}")
        
        # For now, this is a stub that will be implemented based on actual DSPy agent structure
        # The actual implementation will vary based on how DSPy agents are structured
        
        # Example logic (to be refined):
        # module_name = dspy_path.replace("/", ".").replace(".py", "")
        # module = importlib.import_module(module_name)
        # agent_class = getattr(module, f"DSPy{frontmatter.name.title()}Agent")
        # return agent_class()
        
        raise NotImplementedError(
            f"DSPy agent loading not fully implemented yet. "
            f"To complete: implement dynamic import from {dspy_path}"
        )
    
    def _load_traditional_agent(
        self,
        traditional_path: str,
        markdown_spec: str,
        frontmatter: AgentFrontmatter
    ) -> Any:
        """
        Load traditional implementation of agent.
        
        Args:
            traditional_path: Path to traditional implementation module
            markdown_spec: Markdown specification for agent
            frontmatter: Parsed frontmatter
            
        Returns:
            Instantiated traditional agent
            
        Raises:
            Exception: If loading fails
        """
        logger.info(f"Loading traditional agent from {traditional_path}")
        
        # For now, this is a stub
        # Actual implementation will depend on traditional agent structure
        
        # Example logic (to be refined):
        # module_name = traditional_path.replace("/", ".").replace(".py", "")
        # module = importlib.import_module(module_name)
        # agent_class = getattr(module, f"{frontmatter.name.title()}Agent")
        # return agent_class()
        
        raise NotImplementedError(
            f"Traditional agent loading not fully implemented yet. "
            f"To complete: implement dynamic import from {traditional_path}"
        )
    
    def load_agent_from_frontmatter(
        self,
        frontmatter: AgentFrontmatter,
        markdown_body: str,
        force_implementation: Optional[Literal["dspy", "traditional"]] = None
    ) -> Any:
        """
        Load agent based on parsed frontmatter.
        
        Constitutional Compliance:
        - Article I: Verify DSPy availability before loading
        - Article II: Fallback ensures 100% reliability
        - Article IV: Telemetry enables learning
        - Article V: Markdown remains source of truth
        
        Args:
            frontmatter: Parsed AgentFrontmatter
            markdown_body: Markdown specification
            force_implementation: Override to force specific implementation
            
        Returns:
            Loaded agent (possibly wrapped with telemetry)
        """
        # Determine which implementation to use
        impl_type = force_implementation or frontmatter.implementation.preferred
        
        logger.info(f"Loading agent '{frontmatter.name}' with {impl_type} implementation")
        
        agent = None
        actual_impl_type = impl_type
        
        try:
            # Article I: Check DSPy availability
            dspy_available = self._check_dspy_available()
            
            if impl_type == "dspy" and dspy_available:
                try:
                    agent = self._load_dspy_agent(
                        frontmatter.implementation.dspy,
                        markdown_body,
                        frontmatter
                    )
                except Exception as e:
                    logger.warning(f"DSPy load failed, falling back to traditional: {e}")
                    # Article II: Fallback for 100% reliability
                    agent = self._load_traditional_agent(
                        frontmatter.implementation.traditional,
                        markdown_body,
                        frontmatter
                    )
                    actual_impl_type = "traditional"
            else:
                # Load traditional
                agent = self._load_traditional_agent(
                    frontmatter.implementation.traditional,
                    markdown_body,
                    frontmatter
                )
                actual_impl_type = "traditional"
                
                if impl_type == "dspy" and not dspy_available:
                    logger.info("DSPy preferred but not available, using traditional")
        
        except Exception as e:
            # Final fallback - Article II compliance
            logger.error(f"Primary load failed: {e}")
            if frontmatter.rollout.fallback == "traditional":
                logger.info("Attempting fallback to traditional")
                agent = self._load_traditional_agent(
                    frontmatter.implementation.traditional,
                    markdown_body,
                    frontmatter
                )
                actual_impl_type = "traditional"
            else:
                raise LoaderError(f"Failed to load agent '{frontmatter.name}': {e}")
        
        # Article IV: Wrap with telemetry if comparison enabled
        if frontmatter.rollout.comparison and agent is not None:
            logger.info(f"Wrapping agent with telemetry ({actual_impl_type})")
            agent = TelemetryWrapper(agent, actual_impl_type)
        
        # Cache loaded agent
        self.loaded_agents[frontmatter.name] = agent
        
        logger.info(f"Successfully loaded agent '{frontmatter.name}' ({actual_impl_type})")
        return agent
    
    def load_agent(
        self,
        agent_path: str,
        force_implementation: Optional[Literal["dspy", "traditional"]] = None
    ) -> Any:
        """
        Load agent from markdown file path.
        
        This is the main public API method.
        
        Args:
            agent_path: Path to .claude/agents/*.md file
            force_implementation: Override to force specific implementation
            
        Returns:
            Loaded agent instance
        """
        # Parse frontmatter and body
        frontmatter = self._parse_frontmatter(agent_path)
        markdown_body = self._parse_body(agent_path)
        
        # Load agent using frontmatter
        return self.load_agent_from_frontmatter(
            frontmatter,
            markdown_body,
            force_implementation
        )