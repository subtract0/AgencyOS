# 👨‍💻 Agency Code

Fully open sourced version of Claude Code built with [Agency Swarm](https://agency-swarm.ai/welcome/overview) framework.

## 🔥 Key features

- **Developer Agent**: The primary developer agent with the same set of tools as Claude Code.
- **Planner Agent**: Planner agent that acts exactly as Claude Code's planning mode.
- **Full Control**: Full access to all 14 tools from Claude Code, agency structure and prompts.
- **Easy Subagent Creation**: Simple subagent creation process using Cursor or Claude Code itself.
- **Memory API & Learning**: Built-in memory system with in-memory default and optional Firestore backend for persistent learning across sessions.
- **CodeHealer Integration**: Specialized test quality automation with NECESSARY pattern analysis and Q(T) scoring.

👨‍💻 Additionally, you can experiment by adding other features from Agency Swarm framework, unsupported by Claude Code, like multi-level hybrid communication flows.

## 🏥 CodeHealer - Test Quality Automation

The Agency has been enhanced with **CodeHealer** capabilities - a specialized test quality automation system:

### AuditorAgent
- Analyzes codebases using the NECESSARY pattern (9 universal test properties)
- Calculates Q(T) scores: `Q(T) = Π(p_i) × (|B_c| / |B|)`
- Identifies test quality violations with severity levels
- Generates actionable improvement recommendations

### TestGeneratorAgent
- Generates NECESSARY-compliant tests based on audit reports
- Property-specific test templates for each violation type
- Prioritizes high-impact improvements
- Creates comprehensive test suites that maximize Q(T) scores

### NECESSARY Pattern
The 9 universal properties of high-quality tests:
- **N**: No Missing Behaviors (comprehensive coverage)
- **E**: Edge Cases (boundary condition testing)
- **C**: Comprehensive (multiple test vectors)
- **E**: Error Conditions (exception handling)
- **S**: State Validation (object state verification)
- **S**: Side Effects (external impact testing)
- **A**: Async Operations (asynchronous code coverage)
- **R**: Regression Prevention (historical bug coverage)
- **Y**: Yielding Confidence (overall quality assurance)

## 🧠 Memory API & Learning

Agency Code includes a comprehensive memory system that enables agents to learn and retain information across sessions:

### Memory Backends
- **In-Memory Store** (default): Fast, session-based memory that doesn't persist between runs
- **Firestore Backend** (optional): Persistent storage that maintains memory across sessions and agent restarts

### Key Environment Variables
- `FRESH_USE_FIRESTORE=true`: Enable Firestore backend for persistent memory
- `FIRESTORE_EMULATOR_HOST=localhost:8080`: Use local Firestore emulator for development

### Session Transcripts
- All session interactions are automatically logged to `logs/sessions/`
- Transcripts include memory records, timestamps, and tagged content
- Sessions can be analyzed for learning consolidation and pattern recognition

### Memory Integration
- Agents automatically store and retrieve contextual information
- Memory is tagged and searchable for efficient retrieval
- Learning consolidation provides insights into memory usage patterns
- Verbose fallback policy ensures graceful degradation when memory operations fail

> **Note**: Memory system follows MCP Ref 688cf28d-e69c-4624-b7cb-0725f36f9518 assumptions for agent context integration.

## 🚀 Quick start

1. Create and activate a virtual environment (Python 3.13), then install deps:

   ```
   python3.13 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

   > ⚠️ There is currently a bug in LiteLLM with Anthropic reasoning models.  
   > To fix this, after installing the requirements, run:
   >
   > ```
   > python -m pip install git+https://github.com/openai/openai-agents-python.git@main
   > ```

2. Try the agency (terminal demo):

   ```
   sudo python agency.py
   ```

- Don't forget to run the command with sudo if you're on macOS.
- The agent won't be able to edit files outside of your current directory.

## 🔧 Adding Subagents

- To add a subagent, simply prompt _Cursor_ or _Claude Code_ itself. For example:

  ```
  Ask me questions until you have enough context to create a QA tester subagent for my project
  ```

  After that it should create another folder in the root directory called `qa_tester_agent/` and modify the `agency.py` structure.

- Additionally, there is a template in the `subagent_example/` folder that you can use to create a new subagent yourself.

## 📝 Demo Tasks

### 🌌 Particle Galaxy Simulator

```
Create a full-screen interactive particle galaxy simulator using HTML5 Canvas and JavaScript. Include:
  - 2000 glowing particles that form a spiral galaxy shape
  - Particles should have different colors (blues, purples, pinks, whites) and sizes
  - Mouse movement creates gravitational pull that attracts/repels particles
  - Click to create a "supernova" explosion effect that pushes particles outward
  - Add trailing effects for particle movement
  - Include controls to adjust: particle count, rotation speed, color themes (nebula/aurora/cosmic)
  - Add background stars that twinkle
  - Display FPS counter and particle count
  - Make it responsive and add a glow/bloom effect to particles
  All in a single HTML file with inline CSS and JavaScript. Make it mesmerizing and cinematic.
```

### 🎨 Multiplayer Pixel Art Board

```
Create a shared pixel art canvas like r/place using Next.js and Socket.io:

- 50x50 grid where each player can color one pixel at a time
- 16 color palette at the bottom
- See other players' cursors moving in real-time with their names
- 5-second cooldown between placing pixels (show countdown on cursor)
- Minimap in corner showing full canvas
- Chat box for players to coordinate
- Download canvas as image button
- Show "Player X placed a pixel" notifications
- Persist canvas state in JSON file
- Mobile friendly with pinch to zoom

Simple and fun - just a shared canvas everyone can draw on together. Add rainbow gradient background.
```

### 📚 Agency Swarm PDF Chat App

```
Create a Streamlit PDF chat app using PyPDF2 and OpenAI API with Agency Swarm framework:
- File uploader accepting multiple PDFs
- Extract and display PDF text in expandable sections
- Chat interface where users ask questions about the PDFs
- Use agency-swarm to create an agent that can answer questions about the PDFs. (Reference below)
   - Use file_ids parameter in agency.get_response_sync method for allowing the agent to use the uploaded files.
- Create an endpoint for uploading files to openai. (Reference below)
   - Set purpose to "user_data".
   - Attach file in file_ids parameter of get_response method in agency-swarm. (Check reference.)
- OPENAI_API_KEY is provided in the ./.env file. Copy it to the .env file in the backend server folder.
- Export conversation as markdown
Include sample questions and nice chat UI with user/assistant message bubbles.

References:
- agency-swarm quick start: https://agency-swarm.ai/welcome/getting-started/from-scratch
- Openai API file upload reference: https://platform.openai.com/docs/api-reference/files/create

Before starting the task make sure to first use the WebSearch tool to read the references above.

**Important**: The agency-swarm integration must **actually** work. Do not use any placeholder messages and do not come back to me until it's fully tested and completed. Run the backend server and test the integration.
```

## Contributing

We'll be supporting and improving this repo in the future. Any contributions are welcome! Please feel free to submit a pull request.
