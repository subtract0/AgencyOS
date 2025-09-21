import os

from shared.utils import silence_warnings_and_logs

silence_warnings_and_logs()

import litellm  # noqa: E402 - must import after warning suppression
from agency_swarm import Agency  # noqa: E402 - must import after warning suppression
from agency_swarm.tools import (  # noqa: E402 - must import after warning suppression
    SendMessageHandoff,
)
from dotenv import load_dotenv  # noqa: E402 - must import after warning suppression

from agency_code_agent.agency_code_agent import (  # noqa: E402 - must import after warning suppression
    create_agency_code_agent,
)
from agency_memory import Memory, create_firestore_store  # noqa: E402 - must import after warning suppression
from auditor_agent import create_auditor_agent  # noqa: E402 - must import after warning suppression
from planner_agent.planner_agent import (  # noqa: E402 - must import after warning suppression
    create_planner_agent,
)
from shared.agent_context import create_agent_context  # noqa: E402 - must import after warning suppression
from subagent_example.subagent_example import (  # noqa: E402 - must import after warning suppression
    create_subagent_example,
)
from test_generator_agent import create_test_generator_agent  # noqa: E402 - must import after warning suppression

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
litellm.modify_params = True

# switch between models here
# model = "anthropic/claude-sonnet-4-20250514"
model = "gpt-5"

# Create shared memory and agent context for the agency
# This allows memory sharing between agents while maintaining backward compatibility
memory_store = create_firestore_store() if os.getenv("FRESH_USE_FIRESTORE", "").lower() == "true" else None
shared_memory = Memory(store=memory_store)
shared_context = create_agent_context(memory=shared_memory)

# create agents with shared context
planner = create_planner_agent(
    model=model, reasoning_effort="high", agent_context=shared_context
)
# coder = create_agency_code_agent(model="gpt-5", reasoning_effort="high")
coder = create_agency_code_agent(
    model=model, reasoning_effort="high", agent_context=shared_context
)
auditor = create_auditor_agent(
    model=model, reasoning_effort="high", agent_context=shared_context
)
test_generator = create_test_generator_agent(
    model=model, reasoning_effort="high", agent_context=shared_context
)
subagent_example = create_subagent_example(
    model=model, reasoning_effort="high"
)

agency = Agency(
    coder, planner, auditor, test_generator,
    name="AgencyCode",
    communication_flows=[
        (coder, planner, SendMessageHandoff),
        (planner, coder, SendMessageHandoff),
        (planner, auditor, SendMessageHandoff),
        (auditor, test_generator, SendMessageHandoff),
        (test_generator, coder, SendMessageHandoff),
        # (coder, subagent_example) # example for how to add a subagent
    ],
    shared_instructions="./project-overview.md",
)

if __name__ == "__main__":
    agency.terminal_demo(show_reasoning=False if model.startswith("anthropic") else True)
    # agency.visualize()
