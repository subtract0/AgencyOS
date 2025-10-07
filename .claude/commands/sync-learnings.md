---
description: Extract patterns from recent sessions and sync to VectorStore (Article IV automation)
argument-hint: [since] [confidence-min]
model: claude-sonnet-4-5-20250929
---

# Purpose

Continuously update institutional memory with validated patterns from `.output/logs/`. Automates Article IV (Continuous Learning) by extracting, validating, and storing patterns in VectorStore.

# Variables

- `since`: Time window for analysis (`1h` | `24h` | `7d` | `all`, default: `24h`)
- `confidence_min`: Minimum confidence threshold (default: `0.6`)

# Instructions

## Step 1: Scan Recent Logs

Analyze logs from `.output/logs/` based on time window:
- `autonomous_healing/` - Healing events and violations
- `constitutional_telemetry/` - Compliance events
- `events/` - General telemetry
- `sessions/` - Session transcripts (if available)

## Step 2: Extract Patterns

Run LearningAgent analysis to identify:
- Recurring violations (frequency ≥ 3)
- Successful healing strategies
- Common error patterns
- Constitutional compliance patterns

## Step 3: Validate Patterns

Filter patterns by:
- Confidence ≥ `confidence_min` (default: 0.6)
- Evidence count ≥ 3 occurrences
- Proven effectiveness (success rate > 80%)

## Step 4: Store in VectorStore

For each validated pattern:
```python
context.store_memory(
    key=f"pattern_{pattern_type}_{uuid}",
    content={
        "pattern_type": type,
        "frequency": count,
        "confidence": score,
        "fix_strategy": strategy,
        "evidence_count": occurrences
    },
    tags=["learning", "pattern", pattern_type, "validated"]
)
```

## Step 5: Deduplicate

Check against existing patterns:
- If similar pattern exists (>90% similarity): update frequency
- If new pattern: store as new entry
- Merge overlapping patterns with low confidence

# Report

```
## Learning Sync Report

**Time Window**: [since]
**Logs Analyzed**: X sessions, Y events
**Patterns Extracted**: N total

### Validated Patterns (Confidence ≥ 0.6)
1. **Test Fixture Violations** (conf: 0.95, freq: 194)
   - Stored: Yes
   - Tags: [learning, pattern, violation, article_i]

2. **Cascading Failures** (conf: 0.93, freq: 97)
   - Stored: Yes
   - Tags: [learning, pattern, article_i, article_ii]

### Rejected Patterns (Below Threshold)
- Pattern X: confidence 0.55 (< 0.6)
- Pattern Y: evidence 2 (< 3)

### VectorStore Stats
- Patterns before: M
- Patterns added: K
- Patterns updated: L
- Total patterns: M + K
- Average confidence: 0.XX

**Article IV Compliance**: ✅ Continuous learning active
```

---

**Remember**: This enables institutional memory. Run daily/weekly for best results.
