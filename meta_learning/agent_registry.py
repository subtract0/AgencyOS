"""
Agent Registry - Track agent performance and improvements.

Minimal implementation: file-based storage, no external dependencies.
Every line adds measurable value to agent learning tracking.
"""

import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from shared.type_definitions.json import JSONValue


class AgentStatus(Enum):
    ACTIVE = "active"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


@dataclass
class Agent:
    """Core agent metadata - minimal fields for maximum value."""
    agent_id: str
    name: str
    version: str = "1.0.0"
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: datetime = None
    metadata: Dict[str, JSONValue] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentInstance:
    """Agent configuration instance."""
    instance_id: str
    agent_id: str
    config: Dict[str, JSONValue] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.config is None:
            self.config = {}


@dataclass
class AIQEvent:
    """AI Intelligence Quotient measurement event."""
    event_id: str
    agent_instance_id: str
    aiq_score: float
    timestamp: datetime = None
    metrics: Dict[str, float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metrics is None:
            self.metrics = {}


class AgentRegistry:
    """Simple, effective agent tracking with file persistence."""

    def __init__(self, storage_path: str = "data/agent_registry.json"):
        self.storage_path = Path(storage_path)
        self.agents: Dict[str, Agent] = {}
        self.instances: Dict[str, AgentInstance] = {}
        self.aiq_events: List[AIQEvent] = []

        # Ensure data directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def register_agent(self, name: str, version: str = "1.0.0") -> str:
        """Register new agent - returns agent_id."""
        agent_id = str(uuid.uuid4())
        agent = Agent(agent_id=agent_id, name=name, version=version)
        self.agents[agent_id] = agent
        self._save()
        return agent_id

    def create_instance(self, agent_id: str, config: Dict[str, JSONValue] = None) -> str:
        """Create agent instance - returns instance_id."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        instance_id = str(uuid.uuid4())
        instance = AgentInstance(
            instance_id=instance_id,
            agent_id=agent_id,
            config=config or {}
        )
        self.instances[instance_id] = instance
        self._save()
        return instance_id

    def record_aiq(self, instance_id: str, aiq_score: float, metrics: Dict[str, float] = None) -> str:
        """Record AIQ measurement - returns event_id."""
        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not found")

        event_id = str(uuid.uuid4())
        event = AIQEvent(
            event_id=event_id,
            agent_instance_id=instance_id,
            aiq_score=aiq_score,
            metrics=metrics or {}
        )
        self.aiq_events.append(event)
        self._save()
        return event_id

    def get_agent_aiq_history(self, agent_id: str, limit: int = 10) -> List[AIQEvent]:
        """Get AIQ history for agent."""
        # Find all instances for this agent
        instance_ids = {i.instance_id for i in self.instances.values() if i.agent_id == agent_id}

        # Filter and sort events
        events = [e for e in self.aiq_events if e.agent_instance_id in instance_ids]
        events.sort(key=lambda x: x.timestamp, reverse=True)

        return events[:limit]

    def get_top_performers(self, limit: int = 5) -> List[tuple[str, float]]:
        """Get top performing agents by latest AIQ score."""
        if not self.aiq_events:
            return []

        # Get latest score per agent
        latest_scores = {}
        for event in sorted(self.aiq_events, key=lambda x: x.timestamp, reverse=True):
            instance = self.instances.get(event.agent_instance_id)
            if instance and instance.agent_id not in latest_scores:
                agent = self.agents.get(instance.agent_id)
                if agent:
                    latest_scores[instance.agent_id] = (agent.name, event.aiq_score)

        # Sort by score
        return sorted(latest_scores.values(), key=lambda x: x[1], reverse=True)[:limit]

    def _save(self):
        """Persist to file."""
        data = {
            "agents": [self._agent_to_dict(a) for a in self.agents.values()],
            "instances": [self._instance_to_dict(i) for i in self.instances.values()],
            "aiq_events": [self._event_to_dict(e) for e in self.aiq_events]
        }

        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load from file."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            # Load agents
            for agent_data in data.get("agents", []):
                agent = self._dict_to_agent(agent_data)
                self.agents[agent.agent_id] = agent

            # Load instances
            for instance_data in data.get("instances", []):
                instance = self._dict_to_instance(instance_data)
                self.instances[instance.instance_id] = instance

            # Load events
            for event_data in data.get("aiq_events", []):
                event = self._dict_to_event(event_data)
                self.aiq_events.append(event)

        except (json.JSONDecodeError, KeyError) as e:
            # Graceful degradation on corruption
            print(f"Warning: Could not load registry: {e}")

    def _agent_to_dict(self, agent: Agent) -> Dict[str, JSONValue]:
        """Convert agent to dict for JSON storage."""
        data = asdict(agent)
        data["status"] = agent.status.value
        data["created_at"] = agent.created_at.isoformat()
        return data

    def _dict_to_agent(self, data: Dict[str, JSONValue]) -> Agent:
        """Convert dict to agent from JSON storage."""
        data["status"] = AgentStatus(data["status"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return Agent(**data)

    def _instance_to_dict(self, instance: AgentInstance) -> Dict[str, JSONValue]:
        """Convert instance to dict for JSON storage."""
        data = asdict(instance)
        data["created_at"] = instance.created_at.isoformat()
        return data

    def _dict_to_instance(self, data: Dict[str, JSONValue]) -> AgentInstance:
        """Convert dict to instance from JSON storage."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return AgentInstance(**data)

    def _event_to_dict(self, event: AIQEvent) -> Dict[str, JSONValue]:
        """Convert event to dict for JSON storage."""
        data = asdict(event)
        data["timestamp"] = event.timestamp.isoformat()
        return data

    def _dict_to_event(self, data: Dict[str, JSONValue]) -> AIQEvent:
        """Convert dict to event from JSON storage."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return AIQEvent(**data)