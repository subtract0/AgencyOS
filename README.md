# 👨‍💻 Agency Code

Fully open sourced version of Claude Code built with [Agency Swarm](https://agency-swarm.ai/welcome/overview) framework.

## 🔥 Key features

- **Developer Agent**: The primiary developer agent with the same set of tools as Claude Code.
- **Planner Agent**: Planner agent that acts exactly as Claude Code's planning mode.
- **Full Control**: Full access to all 14 tools from Claude Code, agency structure and prompts.
- **Easy Subagent Creation**: Simple subagent creation process using Cursor or Claude Code itself.

👨‍💻 Additionally, you can experiment by adding other features from Agency Swarm framework, unsupported by Claude Code, like multi-level hybrid communication flows.

## 🚀 Quick start

1. Create and activate a virtual environment (Python 3.13), then install deps:

   ```
   python3.13 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

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

- Additionally, there is a template in the `subagent_template/` folder that you can use to create a new subagent yourself.

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

### 🎮 Real-Time Multiplayer Drawing Game

```
Build a full-stack multiplayer drawing game like Skribbl.io using Next.js 14 with App Router, Socket.io, and Prisma. Create:

Frontend:
- Modern glassmorphism UI with Tailwind CSS and Framer Motion animations
- Canvas drawing board with brush size, color picker, eraser, clear, and undo/redo
- Real-time player list showing scores, avatars, and who's drawing
- Chat with guess submission and proximity indicators (hot/cold)
- Countdown timer with animated progress ring
- Word reveal animation when round ends
- Lobby system with room codes and shareable links
- Mobile responsive with touch drawing support

Backend:
- WebSocket server for real-time drawing synchronization
- SQLite database with Prisma for games, players, scores, and word history
- Game state machine: lobby → choosing word → drawing → guessing → reveal → scores
- Anti-cheat: rate limiting, profanity filter, drawing flood protection
- Word database with difficulty levels and categories
- Dynamic scoring based on guess speed and hints used
- Reconnection handling with game state restoration
- REST API endpoints for leaderboards and statistics

Features:
- Custom word lists creation
- Private rooms with passwords
- Spectator mode
- Drawing replay system
- Power-ups: extra time, letter hints, freeze opponents
- Achievement system with badges
- Sound effects and background music toggles

Deploy-ready with environment variables for production. Include sample .env.local file.
```

### 📈 Stock Price Predictor with Live Charts

```
Build a Streamlit app that predicts stock prices using yfinance and scikit-learn:
- Dropdown to select from 10 popular stocks (AAPL, GOOGL, TSLA, etc.)
- Download last 2 years of data and display candlestick chart using plotly
- Train a simple LSTM model to predict next 30 days
- Show prediction vs actual historical performance
- Display current price, change, and volume in metric cards
- Add moving averages (20, 50, 200 day) overlay on chart
- Buy/sell signal based on moving average crossover
Style with green/red colors for profit/loss.
```

## Contributing

We'll be supporting and improving this repo in the future. Any contributions are welcome! Please feel free to submit a pull request.
