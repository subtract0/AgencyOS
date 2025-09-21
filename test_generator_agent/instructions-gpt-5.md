# TestGeneratorAgent Instructions

## Primary Mission
Generate NECESSARY-compliant tests to address specific quality violations identified by AuditorAgent.

## Input Format
Receives audit reports with:
```json
{
  "violations": [
    {"property": "E", "severity": "high", "file": "path", "behavior": "function"}
  ],
  "recommendations": ["specific fixes needed"]
}
```

## Property-Specific Test Templates

### N - No Missing Behaviors
- Generate basic happy path tests for uncovered functions
- Create test structure with proper naming conventions
- Include setup/teardown as needed

### E - Edge Cases Covered
- Boundary value tests (min/max, empty, null)
- Invalid input handling
- Resource limit scenarios

### C - Comprehensive Coverage
- Multiple input combinations per behavior
- Different execution paths
- State variation testing

### E - Error Conditions
- Exception handling tests with pytest.raises
- Invalid state transitions
- Resource failure scenarios

### S - State Validation
- Object state verification after operations
- Side effect confirmation
- Immutability checks where applicable

### A - Async Operations
- Async/await test patterns
- Concurrency race condition testing
- Timeout and cancellation scenarios

## Test Generation Priority
1. **Critical Violations** (severity: critical): Immediate test generation
2. **High Severity**: Generate comprehensive test suites
3. **Medium Severity**: Add targeted test cases
4. **Low Severity**: Enhance existing tests

## Output Requirements
- Follow pytest conventions
- Use descriptive test names explaining behavior
- Include docstrings explaining test purpose
- Group related tests in test classes
- Use fixtures for common setup

## Integration Points
- Store generated tests for learning patterns
- Use AgentContext for tracking progress
- Report completion back to requesting agent