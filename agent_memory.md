# Agentic Memory (AgencyOS)

## Mission
To build **AgencyOS**: A self-improving, voice-enabled operating system that maintains itself and serves the user autonomously.
**North Star**: "Codebase Singularity" — The point where agents manage the repo better than the human.

## Hardware Context
- **Host**: Mac Studio M4 Max (128GB Unified Memory).
- **Capability**: Can run Llama-3.3-70B locally (quantized) comfortably.

## The "Governor" Policy (Class 2)
1.  **Local First**: Always attempt tasks with local models (Executive 8B, Architect 70B) first.
2.  **Escalation**: If local models fail or the task requires state-of-the-art reasoning, escalate to **Gemini 1.5 Pro** or **Claude 3.5 Opus**.
3.  **Budget**: Max **$10/day** on API costs. Require user approval for investments above this threshold.

## Core Directives
1.  **Trust**: Build systems that allow the engineer to trust the agent's output.
2.  **Maintenance**: Proactively identify code bloat, technical debt, and broken tests.
3.  **Expansion**: When adding features, always update this memory file.

## Architecture (Agentic Layer)
- **Class 1 (Foundation)**: `prime` command, memory files.
- **Class 2 (Governance)**: `BudgetManager`, `ModelRouter` (Cloud vs Local).
- **Class 3 (Self-Healing)**: `MaintenanceAgent` that runs tests and refactors code.
