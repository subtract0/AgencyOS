# DSPy Audit System

## Overview

An advanced, self-optimizing audit and refactoring system that learns from historical patterns and improves with each execution. This system can operate alongside the legacy audit system with seamless fallback mechanisms.

## Features

- **Dynamic Optimization**: Uses DSPy teleprompters to optimize audit logic
- **Learning Integration**: Queries VectorStore for historical patterns
- **Parallel Execution**: Concurrent audit of multiple modules
- **Automatic Prioritization**: Constitutional violations > Security > Coverage > Complexity
- **Verified Refactoring**: Test-driven fixes with automatic rollback
- **Continuous Learning**: Stores successful patterns for future use

## Installation

### Optional DSPy Installation

```bash
# Uncomment in requirements.txt or install directly:
pip install dspy-ai>=2.4.0
pip install faiss-cpu>=1.7.0
```

## Configuration

### Environment Variables

```bash
# Enable DSPy audit system
export USE_DSPY_AUDIT=true

# Enable optimization
export USE_DSPY_OPTIMIZATION=true

# Enable learning
export ENABLE_VECTORSTORE_LEARNING=true

# Parallel execution
export PARALLEL_AUDIT=true
export MAX_PARALLEL_AUDITS=3

# Auto rollback on test failure
export AUTO_ROLLBACK=true

# A/B testing (optional)
export AB_TEST_AUDIT=true
export AB_TEST_PERCENTAGE=0.1  # 10% use new system
```

### Feature Flags

All features can be controlled via environment variables. See `config.py` for complete list.

## Usage

### Basic Audit

```python
from dspy_audit.adapter import AuditAdapter

adapter = AuditAdapter()
results = adapter.run_audit(
    code_path="agency/",
    max_fixes=3
)

print(f"Q(T) Score: {results['qt_score']}")
print(f"Issues Found: {len(results['issues'])}")
```

### Force DSPy System

```python
results = adapter.run_audit(
    code_path="tools/",
    force_dspy=True  # Force DSPy even if flags say otherwise
)
```

### Compare Systems

```python
comparison = adapter.compare_systems("agency/")

print(f"Legacy Q(T): {comparison['legacy']['qt_score']}")
print(f"DSPy Q(T): {comparison['dspy']['qt_score']}")
print(f"Improvement: {comparison['comparison']['qt_score_delta']}")
```

### Optimize Module

```python
from dspy_audit.optimize import optimize_audit_module, save_optimized_module

# Optimize with training data
module = optimize_audit_module()

# Save for future use
save_optimized_module(module)
```

## Architecture

### Core Components

1. **Signatures** (`signatures.py`)
   - Typed specifications for audit operations
   - NECESSARY pattern compliance
   - Issue prioritization

2. **Modules** (`modules.py`)
   - `AuditRefactorModule`: Main audit pipeline
   - `MultiAgentAuditModule`: Coordinates multiple agents

3. **Metrics** (`metrics.py`)
   - Effectiveness scoring
   - Constitutional compliance
   - Learning effectiveness

4. **Optimization** (`optimize.py`)
   - Training data loading
   - Module compilation
   - Performance evaluation

5. **Config** (`config.py`)
   - Feature flags
   - Performance settings
   - Path configuration

6. **Adapter** (`adapter.py`)
   - Bridges legacy and DSPy systems
   - Automatic fallback
   - A/B testing support

## Workflow

### Enhanced Audit Workflow

1. **Pre-Audit Learning**
   - Query VectorStore for patterns
   - Load historical fixes

2. **Parallel Audit**
   - Split codebase into modules
   - Run concurrent analysis
   - Aggregate results

3. **Dynamic Prioritization**
   - Constitutional violations (P0)
   - Security issues (P1)
   - Coverage gaps (P2)
   - Complexity (P3)

4. **Verified Refactoring**
   - Create snapshot
   - Apply fix
   - Run tests
   - Rollback if failed

5. **Learning Capture**
   - Store successful patterns
   - Log anti-patterns
   - Update metrics

## Metrics

### Q(T) Score Calculation

```
Q(T) = (Σ NECESSARY scores) / 9

Where NECESSARY =
  N: No missing behaviors (0.8 threshold)
  E: Edge cases (0.7 threshold)
  C: Comprehensive (0.8 threshold)
  E: Error conditions (0.7 threshold)
  S: State validation (0.9 threshold)
  S: Side effects (0.9 threshold)
  A: Async operations (0.6 threshold)
  R: Regression prevention (0.8 threshold)
  Y: Yielding confidence (0.7 threshold)
```

### Performance Targets

- **Fix Success Rate**: >95%
- **Audit Speed**: 50% faster than legacy
- **Learning Reuse**: >60% pattern application
- **Constitutional Compliance**: 100%

## Migration Path

### Phase 1: Shadow Mode
- Run DSPy in parallel with legacy
- Compare results but use legacy output
- Collect training data

### Phase 2: A/B Testing
- Enable for 10% of audits
- Monitor success metrics
- Gradually increase percentage

### Phase 3: Primary System
- Make DSPy default
- Keep legacy as fallback
- Continue optimization

### Phase 4: Full Migration
- Remove legacy system
- Pure DSPy operation
- Continuous learning loop

## Troubleshooting

### DSPy Not Available

If DSPy is not installed, the system automatically falls back to legacy auditor.

### Performance Issues

1. Reduce `MAX_PARALLEL_AUDITS`
2. Disable learning with `ENABLE_VECTORSTORE_LEARNING=false`
3. Use cache with longer TTL

### Optimization Failures

1. Check training data quality
2. Reduce `num_candidates` in DSPy settings
3. Use simpler metrics initially

## Development

### Adding New Signatures

```python
class CustomSignature(dspy.Signature):
    """Your custom signature."""
    input_field: str = dspy.InputField(desc="Description")
    output_field: str = dspy.OutputField(desc="Description")
```

### Custom Metrics

```python
def custom_metric(example, prediction, trace=None):
    """Your custom metric."""
    # Calculate score
    return score
```

### Training Data

Store audit examples in `logs/audits/*.json` for automatic training data collection.

## Future Enhancements

- [ ] Real-time optimization during execution
- [ ] Multi-model ensemble voting
- [ ] Automatic hyperparameter tuning
- [ ] Cross-project learning transfer
- [ ] GUI for monitoring and control

## Contributing

1. Test changes with both systems
2. Ensure backward compatibility
3. Add feature flags for new features
4. Document configuration changes
5. Include metrics for evaluation