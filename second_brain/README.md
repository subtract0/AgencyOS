# Second Brain

**Your cognitive extension.** Capture thoughts in 5 seconds. AI routes them. Get daily digests.

## Why This Exists

Your brain was designed to *think*, not to *remember*. Every open loop you try to hold in your head is a tax on creativity. This system closes those loops by:

1. **Capturing** thoughts with zero friction
2. **Classifying** them automatically with local AI ($0 cost)
3. **Filing** them into simple buckets: people, projects, ideas, admin
4. **Surfacing** what matters via daily/weekly digests

## Quick Start

```bash
# Capture a thought
python brain.py capture "Call Sarah about the project deadline"

# Interactive capture (dump your brain)
python brain.py capture -i

# Get your daily digest
python brain.py daily

# Weekly review
python brain.py weekly

# Search
python brain.py search "project name"

# Fix a misclassified item
python brain.py fix abc123 projects
```

## The Architecture

```
YOU → Capture (one thought) → AI Classifier → Route → File → Log
                                    ↓
                              confidence < 0.6?
                                    ↓
                              needs_review
```

### Building Blocks

| Block | What It Does | Implementation |
|-------|--------------|----------------|
| **Dropbox** | Frictionless capture | `brain.py capture` |
| **Sorter** | AI classification | vcoder-120b (local, $0) |
| **Form** | Structured fields | Person, Project, Idea, Admin |
| **Filing Cabinet** | Source of truth | JSON files in `data/` |
| **Receipt** | Audit trail | `data/inbox/` |
| **Bouncer** | Confidence filter | threshold=0.6 |
| **Tap on Shoulder** | Proactive surfacing | `brain.py daily/weekly` |
| **Fix Button** | Easy corrections | `brain.py fix` |

## Categories

Keep it painfully simple. Four buckets:

- **people**: Relationships, follow-ups, context about humans
- **projects**: Active work with next actions
- **ideas**: Insights to remember (not act on now)
- **admin**: Errands, bills, logistics

## Data Storage

Everything is local JSON files. Human-readable. Git-friendly.

```
second_brain/
└── data/
    ├── people/      # Person records
    ├── projects/    # Project records
    ├── ideas/       # Idea records
    ├── admin/       # Admin tasks
    └── inbox/       # Audit trail (every capture logged)
```

## Configuration

Set in environment or `.env`:

```bash
# Use local model ($0 cost)
USE_LOCAL_MODEL=true
LOCAL_API_BASE=http://localhost:1234/v1
LOCAL_MODEL=vcoder-120b-1.0-hi-mlx

# Confidence threshold for auto-filing
SB_CONFIDENCE_THRESHOLD=0.6
```

## Integration with Operator

The Second Brain integrates with the voice interface:

```
"Operator, capture: Need to review quarterly goals"
"Operator, what's my daily digest?"
"Operator, any projects stuck?"
```

## Principles

From the engineering playbook:

1. **One behavior**: Human captures, system does the rest
2. **Separate concerns**: Interface → Compute → Memory
3. **Prompts as APIs**: Structured JSON, no surprises
4. **Trust via receipts**: Every action logged
5. **Safe defaults**: Uncertain? Ask, don't guess
6. **Small outputs**: Daily digest < 150 words
7. **Next action**: Projects have specific next steps
8. **Routing > organizing**: Let AI decide the bucket
9. **Minimal fields**: Start simple, add when needed
10. **Design for restart**: No guilt, just resume

## Local-First

Unlike cloud tools:
- Your data stays on your machine
- Works offline
- $0 AI cost with local LLM
- No subscriptions

## License

MIT. Build your own second brain your way.
