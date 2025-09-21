# Integration Architecture: AuditorAgent & TestGeneratorAgent

## Overview
The AuditorAgent and TestGeneratorAgent implement a quality assurance pipeline following the NECESSARY pattern and Q(T) score methodology, integrated with the existing Agency framework.

## Agent Communication Flow

```
Planner → Auditor → TestGenerator → Coder
    ↑                                  ↓
    ←――――――――――――――――――――――――――――――――――――
```

### Communication Patterns

1. **Planner → Auditor**: Initiates quality analysis request
   - Sends target codebase path
   - Specifies analysis mode (full/verification)

2. **Auditor → TestGenerator**: Passes violation report
   - JSON audit report with Q(T) scores
   - Prioritized violation list
   - NECESSARY compliance analysis

3. **TestGenerator → Coder**: Delivers generated tests
   - Test file paths and content
   - Implementation recommendations
   - Integration instructions

## Shared Context Structure

### Memory Integration Points

```python
# AuditorAgent memory storage
agent_context.store_memory(
    f"audit_report_{session_id}",
    {
        "qt_score": 0.85,
        "violations": [...],
        "target_path": "/path/to/code",
        "timestamp": "2025-09-21T...",
        "recommendations": [...]
    },
    ["audit", "quality", "necessary"]
)

# TestGeneratorAgent memory storage
agent_context.store_memory(
    f"test_generation_{session_id}",
    {
        "tests_generated": 15,
        "violations_addressed": [...],
        "test_files": [...],
        "patterns_used": [...]
    },
    ["test_generation", "necessary", "quality"]
)
```

### Context Sharing

- **AgentContext**: Shared session state and memory access
- **Memory API**: Learning from audit patterns and test generation success
- **SendMessageHandoff**: Structured communication between agents

## NECESSARY Pattern Implementation

### Nine Properties Tracked

1. **N** - No Missing Behaviors: Function/method coverage analysis
2. **E** - Edge Cases Covered: Boundary condition detection
3. **C** - Comprehensive Coverage: Multiple test vectors per behavior
4. **E** - Error Conditions: Exception handling validation
5. **S** - State Validation: Object state verification patterns
6. **S** - Side Effects: External impact testing
7. **A** - Async Operations: Concurrency pattern testing
8. **R** - Regression Prevention: Historical bug coverage
9. **Y** - Yielding Confidence: Overall test quality metrics

### Q(T) Score Calculation

```python
Q(T) = (Σ property_scores) / 9
Property Score = (compliant_behaviors / total_behaviors)
```

## Tool Integration

### AuditorAgent Tools
- **AnalyzeCodebase**: Primary analysis tool with AST parsing
- **AST Analyzer**: Lightweight code structure extraction
- **Grep/Read/Glob**: File pattern matching and content analysis

### TestGeneratorAgent Tools
- **GenerateTests**: Main test generation tool
- **Write/MultiEdit**: Test file creation and modification
- **Read**: Source code analysis for test generation

## R&D Framework Principles

### Learning and Adaptation
- Store successful audit patterns in Memory
- Track Q(T) score improvements over time
- Learn from test generation effectiveness

### Continuous Improvement
- Analyze violation patterns across projects
- Refine NECESSARY property heuristics
- Enhance test template quality

### Knowledge Transfer
- Share insights between audit sessions
- Build repository of common violations
- Develop project-specific quality profiles

## Usage Patterns

### 1. Quality Assessment Workflow
```
1. Planner receives quality assessment request
2. Planner → Auditor: "Analyze codebase at /path"
3. Auditor performs NECESSARY analysis
4. Auditor → TestGenerator: Passes violation report
5. TestGenerator creates compliant tests
6. TestGenerator → Coder: Delivers implementation
```

### 2. Continuous Integration Workflow
```
1. Code changes trigger quality check
2. Auditor compares Q(T) scores
3. If Q(T) < threshold, generate tests
4. TestGenerator addresses specific violations
5. Store results for learning
```

### 3. Project Onboarding Workflow
```
1. Initial comprehensive audit
2. Establish Q(T) baseline
3. Generate foundational test suite
4. Set up monitoring for future changes
```

## Error Handling and Resilience

- **Graceful Degradation**: Continue with available analysis if some tools fail
- **Validation**: Verify file paths and permissions before analysis
- **Rollback**: Maintain original test files before modifications
- **Logging**: Track all operations through Memory API

## Performance Considerations

- **Incremental Analysis**: Support for analyzing only changed files
- **Caching**: Store AST analysis results for large codebases
- **Parallel Processing**: Multiple file analysis where possible
- **Resource Limits**: Timeout controls for large codebases

## Extension Points

- **Custom NECESSARY Properties**: Project-specific quality metrics
- **Test Templates**: Domain-specific test generation patterns
- **Integration Hooks**: CI/CD pipeline integration
- **Quality Gates**: Automated Q(T) threshold enforcement