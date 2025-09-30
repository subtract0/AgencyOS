# Trinity Protocol - Quick Start Guide

Get up and running with Trinity Protocol in 5 minutes.

---

## Prerequisites

1. **Ollama** (for local models)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull required models
ollama pull qwen2.5-coder:1.5b   # For WITNESS (986 MB)
ollama pull qwen2.5-coder:7b     # For EXECUTOR (4.7 GB)
ollama pull codestral-22b        # For ARCHITECT (13.4 GB, optional)
```

2. **Python Dependencies**
```bash
# Install Trinity dependencies
uv pip install faiss-cpu sentence-transformers websockets httpx
```

---

## Running the Integration Demo

The fastest way to see Trinity Protocol in action:

```bash
cd /Users/am/Code/Agency
python trinity_protocol/demo_integration.py
```

**Expected output**:
```
✅ 5/5 events detected correctly
✅ 5/5 signals published to improvement_queue
✅ 5/5 patterns persisted for learning
✅ Priority routing: 2 CRITICAL, 1 HIGH, 2 NORMAL
```

---

## Running Tests

Verify everything is working:

```bash
# All Trinity tests (172 tests, ~5s)
python -m pytest tests/trinity_protocol/ -o addopts="" -q

# Specific components
python -m pytest tests/trinity_protocol/test_persistent_store.py -o addopts="" -q
python -m pytest tests/trinity_protocol/test_message_bus.py -o addopts="" -q
python -m pytest tests/trinity_protocol/test_pattern_detector.py -o addopts="" -q
python -m pytest tests/trinity_protocol/test_witness_agent.py -o addopts="" -q
```

---

## Using Trinity Components

### 1. Persistent Store

Store and search patterns with semantic similarity:

```python
from trinity_protocol.persistent_store import PersistentStore

# Create store
store = PersistentStore("patterns.db")

# Store a pattern
pattern_id = store.store_pattern(
    pattern_type="failure",
    pattern_name="critical_error",
    content="ModuleNotFoundError in agent initialization",
    confidence=0.85,
    metadata={"file": "agent.py", "line": 42}
)

# Search patterns
patterns = store.search_patterns(
    query="module error",  # Semantic search
    pattern_type="failure",
    min_confidence=0.7,
    limit=10
)

# Get statistics
stats = store.get_stats()
print(f"Total patterns: {stats['total_patterns']}")

# Cleanup
store.close()
```

### 2. Message Bus

Async pub/sub with persistence:

```python
import asyncio
from trinity_protocol.message_bus import MessageBus

async def publisher():
    bus = MessageBus("messages.db")

    # Publish message
    msg_id = await bus.publish(
        queue_name="telemetry_stream",
        message={"error": "Test error", "severity": "critical"},
        priority=10,
        correlation_id="task-123"
    )

    bus.close()

async def subscriber():
    bus = MessageBus("messages.db")

    # Subscribe to queue
    async for message in bus.subscribe("telemetry_stream"):
        print(f"Received: {message}")

        # Acknowledge message
        await bus.ack(message['_message_id'])
        break

    bus.close()

# Run
asyncio.run(publisher())
asyncio.run(subscriber())
```

### 3. Local Model Server

Interact with local models via Ollama:

```python
import asyncio
from shared.local_model_server import LocalModelServer

async def generate():
    async with LocalModelServer() as server:
        # Check availability
        if await server.is_local_available():
            # Generate text
            response = await server.generate(
                prompt="Explain what a critical error is in one sentence",
                model="qwen2.5-coder:1.5b",
                temperature=0.3,
                max_tokens=100
            )
            print(f"Response: {response}")

            # Stream generation
            print("Streaming:")
            async for chunk in server.generate_stream(
                prompt="Count to 5",
                model="qwen2.5-coder:1.5b"
            ):
                print(chunk, end="", flush=True)

asyncio.run(generate())
```

### 4. Pattern Detector

Classify events into patterns:

```python
from trinity_protocol.pattern_detector import PatternDetector

# Create detector
detector = PatternDetector(min_confidence=0.7)

# Detect pattern
event_text = "Fatal error: ModuleNotFoundError when importing core library"
metadata = {"file": "agent.py", "error_type": "ModuleNotFoundError"}

pattern = detector.detect(event_text, metadata)

if pattern:
    print(f"Pattern: {pattern.pattern_name}")
    print(f"Type: {pattern.pattern_type}")
    print(f"Confidence: {pattern.confidence:.2f}")
    print(f"Keywords matched: {pattern.keywords_matched}")
else:
    print("No pattern detected (below confidence threshold)")

# Get statistics
stats = detector.get_pattern_stats()
print(f"Total detections: {stats['total_detections']}")
```

### 5. WITNESS Agent

Full autonomous pattern detection:

```python
import asyncio
from trinity_protocol.message_bus import MessageBus
from trinity_protocol.persistent_store import PersistentStore
from trinity_protocol.witness_agent import WitnessAgent

async def run_witness():
    # Initialize infrastructure
    message_bus = MessageBus("messages.db")
    pattern_store = PersistentStore("patterns.db")

    # Create WITNESS agent
    witness = WitnessAgent(
        message_bus=message_bus,
        pattern_store=pattern_store,
        min_confidence=0.7
    )

    # Start WITNESS in background
    witness_task = asyncio.create_task(witness.run())

    # Publish some events
    await message_bus.publish(
        "telemetry_stream",
        {"message": "Fatal crash in production", "severity": "critical"}
    )

    # Wait for processing
    await asyncio.sleep(1.0)

    # Check results
    stats = witness.get_stats()
    print(f"Detections: {stats['detector']['total_detections']}")

    # Stop WITNESS
    await witness.stop()
    try:
        await asyncio.wait_for(witness_task, timeout=2.0)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        pass

    # Cleanup
    message_bus.close()
    pattern_store.close()

asyncio.run(run_witness())
```

---

## Model Selection & Routing

Use complexity-based routing to optimize costs:

```python
from shared.model_policy_enhanced import (
    assess_complexity,
    classify_complexity,
    get_model_for_agent,
    should_use_local
)

# Assess task complexity
task = "Fix a typo in docstring"
complexity = assess_complexity(
    task_description=task,
    scope="single-file",
    priority="NORMAL"
)

level = classify_complexity(complexity)
print(f"Complexity: {level.value} ({complexity:.2f})")

# Get model for agent
model = get_model_for_agent("witness", complexity=complexity)
print(f"Model selected: {model}")

# Check if local is appropriate
use_local = should_use_local("witness", complexity)
print(f"Use local model: {use_local}")

# For critical tasks, it escalates automatically
critical_task = "Security vulnerability in authentication"
critical_complexity = assess_complexity(
    critical_task,
    keywords=["security"],
    scope="architecture",
    priority="CRITICAL"
)
critical_model = get_model_for_agent("architect", complexity=critical_complexity)
print(f"Critical task model: {critical_model}")  # Will escalate to cloud
```

---

## Troubleshooting

### Ollama not running
```bash
# Check Ollama status
ollama list

# Start Ollama
ollama serve

# Test model
ollama run qwen2.5-coder:1.5b "Hello"
```

### FAISS not available
This is optional! Trinity works without FAISS (semantic search disabled):
```python
store = PersistentStore()
stats = store.get_stats()
print(stats['faiss_available'])  # Will be False, but everything else works
```

### Tests failing
```bash
# Install test dependencies
uv pip install pytest pytest-asyncio

# Run with verbose output
python -m pytest tests/trinity_protocol/ -v

# Run single test
python -m pytest tests/trinity_protocol/test_pattern_detector.py::TestPatternDetector::test_detects_critical_error -v
```

---

## Next Steps

1. **Read the docs**: `docs/trinity_protocol/IMPLEMENTATION_STATUS.md`
2. **Explore the code**: Start with `trinity_protocol/witness_agent.py`
3. **Run the demo**: `python trinity_protocol/demo_integration.py`
4. **Check specs**: `docs/trinity_protocol/WITNESS.md` for canonical spec

---

## Architecture Overview

```
┌─────────────┐
│  telemetry  │ ← Events published here
│   _stream   │
└──────┬──────┘
       │
       v
┌─────────────┐
│   WITNESS   │ ← Detects patterns (Week 3 ✅)
│   Agent     │
└──────┬──────┘
       │
       v
┌─────────────┐
│improvement_ │ ← Signals published here
│   queue     │
└──────┬──────┘
       │
       v
┌─────────────┐
│ ARCHITECT   │ ← Strategic planning (Week 5)
│   Agent     │
└──────┬──────┘
       │
       v
┌─────────────┐
│ execution_  │
│   queue     │
└──────┬──────┘
       │
       v
┌─────────────┐
│  EXECUTOR   │ ← Meta-orchestration (Week 6)
│   Agent     │
└─────────────┘
```

---

## Key Files

```
trinity_protocol/
├── __init__.py
├── persistent_store.py      # Week 1: Pattern storage
├── message_bus.py           # Week 1: Async messaging
├── pattern_detector.py      # Week 3: Pattern classification
├── witness_agent.py         # Week 3: Autonomous detection
└── demo_integration.py      # Integration demo

shared/
├── local_model_server.py    # Week 2: Ollama integration
└── model_policy_enhanced.py # Week 2: Hybrid routing

tests/trinity_protocol/
├── test_persistent_store.py     # 21 tests
├── test_message_bus.py          # 23 tests
├── test_pattern_detector.py     # 59 tests
└── test_witness_agent.py        # 69 tests
```

---

## Support

For issues or questions:
- Check `docs/trinity_protocol/IMPLEMENTATION_STATUS.md`
- Read the canonical specs in `docs/trinity_protocol/*.md`
- Review test examples in `tests/trinity_protocol/`

---

**Trinity Protocol**: Autonomous improvement through continuous perception, cognition, and action.
