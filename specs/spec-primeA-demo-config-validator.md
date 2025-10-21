# Specification: Configuration File Validator

**Spec ID**: `spec-primeA-demo-config-validator`
**Status**: `Draft`
**Author**: PlannerAgent (via /primeA orchestrator)
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Plan**: `plan-primeA-demo-config-validator.md` (to be created)

---

## Executive Summary

Implement a configuration file validation system that parses YAML/JSON configuration files, validates their structure using Pydantic models, enforces strict typing constraints, and returns results using the Result<T,E> pattern. This demonstrates Agency's constitutional principles of strict typing (no `Dict[Any, Any]`), functional error handling (Result pattern), and 100% test coverage (TDD).

---

## Goals

### Primary Goals
- [ ] **Goal 1**: Parse YAML and JSON configuration files with strict type validation
- [ ] **Goal 2**: Implement Pydantic models for configuration schema enforcement
- [ ] **Goal 3**: Use Result<T,E> pattern for all error handling (no try/catch control flow)
- [ ] **Goal 4**: Provide clear, actionable validation error messages
- [ ] **Goal 5**: Achieve 100% test coverage with AAA pattern (Arrange-Act-Assert)

### Success Metrics
- **Type Safety**: 100% of configuration fields use explicit Pydantic types (no `Any`)
- **Error Handling**: 100% of failure paths use Result<T,E> pattern
- **Test Coverage**: >95% line coverage with all edge cases tested
- **Function Complexity**: All functions <50 lines (constitutional mandate)
- **Validation Accuracy**: 100% detection rate for invalid configurations

---

## Non-Goals

### Explicit Exclusions
- **Runtime Configuration Updates**: Not supporting hot-reloading or dynamic reconfiguration
- **Multi-Format Conversion**: Not converting between YAML/JSON formats
- **Configuration Generation**: Not creating configuration files, only validating existing ones
- **Environment Variable Substitution**: Not handling ${ENV_VAR} style placeholders
- **Configuration Migration**: Not supporting schema version upgrades

### Future Considerations
- **Schema Evolution**: Version-based configuration migrations (future enhancement)
- **Advanced Validation Rules**: Custom validators for business logic constraints
- **Configuration Merging**: Combining multiple config files with override rules

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: DevOps Engineer
- **Description**: Operations engineer deploying Agency with custom configurations
- **Goals**: Ensure configuration files are valid before deployment to avoid runtime errors
- **Pain Points**: Runtime failures due to typos or invalid values in config files
- **Technical Proficiency**: Intermediate - understands YAML/JSON, needs clear error messages

#### Persona 2: CodingAgent
- **Description**: Development agent loading configuration files during application startup
- **Goals**: Type-safe configuration parsing with comprehensive error reporting
- **Pain Points**: Cryptic parsing errors, ambiguous validation failures
- **Technical Proficiency**: Expert - expects Pydantic models and Result types

#### Persona 3: QualityEnforcerAgent
- **Description**: Quality assurance agent validating constitutional compliance
- **Goals**: Verify strict typing, Result pattern usage, and test coverage
- **Pain Points**: Ad-hoc error handling, `Dict[Any, Any]` usage, untested edge cases
- **Technical Proficiency**: Expert - enforces constitutional standards

### User Journeys

#### Journey 1: Valid Configuration Loading
```
1. User starts with: Valid YAML configuration file for Agency settings
2. User needs to: Load configuration with type safety guarantees
3. System performs: Parses YAML → Validates with Pydantic → Returns Ok(Config)
4. System provides: Fully-typed configuration object ready for use
5. User achieves: Type-safe configuration access with IDE autocomplete
```

#### Journey 2: Invalid Configuration Detection
```
1. User starts with: Configuration file with typo in field name (e.g., "modell" instead of "model")
2. User needs to: Identify the exact error before deployment
3. System performs: Parses file → Validation fails → Returns Err(ValidationError)
4. System provides: Clear error: "Unknown field 'modell' in section 'agents.planner'. Did you mean 'model'?"
5. User achieves: Fixed configuration without trial-and-error debugging
```

#### Journey 3: Missing Required Field
```
1. User starts with: Configuration missing required field (e.g., no API key)
2. User needs to: Identify missing requirements before startup failure
3. System performs: Validation detects missing field → Returns Err(MissingFieldError)
4. System provides: Error: "Missing required field 'api_key' in section 'authentication'"
5. User achieves: Complete configuration before deployment
```

---

## Acceptance Criteria

### Functional Requirements

#### Core Parsing
- [ ] **AC-1.1**: Parse valid YAML files into Pydantic models without data loss
- [ ] **AC-1.2**: Parse valid JSON files into Pydantic models without data loss
- [ ] **AC-1.3**: Detect and report syntax errors in YAML files with line numbers
- [ ] **AC-1.4**: Detect and report syntax errors in JSON files with character positions

#### Strict Typing
- [ ] **AC-2.1**: All configuration fields use explicit Pydantic types (no `Any`)
- [ ] **AC-2.2**: Nested configuration sections use typed Pydantic models (no `Dict[Any, Any]`)
- [ ] **AC-2.3**: Optional fields use `Optional[T]` with explicit None defaults
- [ ] **AC-2.4**: List fields use `list[T]` with explicit element types

#### Result Pattern
- [ ] **AC-3.1**: All parsing functions return `Result[Config, ConfigError]`
- [ ] **AC-3.2**: All validation functions return `Result[T, ValidationError]`
- [ ] **AC-3.3**: No try/catch used for control flow (exceptions only for unexpected errors)
- [ ] **AC-3.4**: Error types provide actionable information (field name, expected type, actual value)

#### Validation
- [ ] **AC-4.1**: Detect unknown fields and suggest similar field names (fuzzy matching)
- [ ] **AC-4.2**: Detect missing required fields with clear error messages
- [ ] **AC-4.3**: Detect type mismatches (e.g., string instead of int) with expected type
- [ ] **AC-4.4**: Validate constraints (e.g., positive integers, non-empty strings)

### Non-Functional Requirements

#### Performance
- [ ] **AC-P.1**: Parse and validate 1KB config file in <100ms
- [ ] **AC-P.2**: Parse and validate 100KB config file in <500ms

#### Quality
- [ ] **AC-Q.1**: >95% test coverage for all parsing and validation logic
- [ ] **AC-Q.2**: All functions <50 lines (constitutional requirement)
- [ ] **AC-Q.3**: Zero linting errors with strict mypy checking enabled

#### Usability
- [ ] **AC-U.1**: Error messages include field path (e.g., `agents.planner.model`)
- [ ] **AC-U.2**: Error messages suggest fixes for common mistakes
- [ ] **AC-U.3**: Validation errors include both expected and actual values

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [ ] **AC-CI.1**: Read entire configuration file before validation (no partial parsing)
- [ ] **AC-CI.2**: Collect all validation errors before returning (no fail-fast mode)
- [ ] **AC-CI.3**: No broken windows in error handling or type annotations

#### Article II: 100% Verification and Stability
- [ ] **AC-CII.1**: 100% test coverage for all parsing logic (TDD)
- [ ] **AC-CII.2**: 100% test coverage for all validation rules
- [ ] **AC-CII.3**: All edge cases tested (empty files, malformed syntax, missing fields)
- [ ] **AC-CII.4**: Tests use AAA pattern (Arrange-Act-Assert) consistently

#### Article III: Automated Merge Enforcement
- [ ] **AC-CIII.1**: Mypy strict mode passes with no type errors
- [ ] **AC-CIII.2**: Pytest runs with no failures or skips
- [ ] **AC-CIII.3**: Linter passes with no warnings

#### Article IV: Continuous Learning and Improvement
- [ ] **AC-CIV.1**: Query VectorStore for similar validation patterns before implementation
- [ ] **AC-CIV.2**: Store successful validation patterns after implementation
- [ ] **AC-CIV.3**: Apply learnings from past Pydantic model patterns

#### Article V: Spec-Driven Development
- [ ] **AC-CV.1**: This specification guides all implementation decisions
- [ ] **AC-CV.2**: Implementation plan created before coding begins
- [ ] **AC-CV.3**: TodoWrite tasks map to acceptance criteria

---

## Technical Specification

### Configuration Schema Example

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class AgentConfig(BaseModel):
    """Configuration for individual agent."""
    model: str = Field(..., description="LLM model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, gt=0)

class MemoryConfig(BaseModel):
    """Configuration for memory system."""
    use_enhanced_memory: bool = Field(default=True)
    vector_store_path: str = Field(..., description="Path to VectorStore")
    session_id: Optional[str] = Field(default=None)

class AgencyConfig(BaseModel):
    """Root configuration for Agency system."""
    planner: AgentConfig
    coder: AgentConfig
    memory: MemoryConfig
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
```

### Result Type Definitions

```python
from shared.type_definitions.result import Result, Ok, Err
from enum import Enum

class ConfigErrorType(Enum):
    """Configuration error categories."""
    SYNTAX_ERROR = "syntax_error"
    VALIDATION_ERROR = "validation_error"
    MISSING_FIELD = "missing_field"
    TYPE_MISMATCH = "type_mismatch"
    UNKNOWN_FIELD = "unknown_field"

class ConfigError(BaseModel):
    """Structured configuration error."""
    error_type: ConfigErrorType
    field_path: str
    message: str
    suggestion: Optional[str] = None
    line_number: Optional[int] = None
```

### API Contract

```python
def parse_config_file(file_path: str) -> Result[AgencyConfig, ConfigError]:
    """
    Parse and validate configuration file.

    Args:
        file_path: Path to YAML or JSON configuration file

    Returns:
        Result with AgencyConfig on success or ConfigError on failure

    Raises:
        Never - uses Result pattern for all errors
    """

def validate_config(data: dict[str, Any]) -> Result[AgencyConfig, ConfigError]:
    """
    Validate configuration data against schema.

    Args:
        data: Parsed configuration dictionary

    Returns:
        Result with validated AgencyConfig or ConfigError

    Raises:
        Never - uses Result pattern for all errors
    """
```

---

## Dependencies & Constraints

### System Dependencies
- **Pydantic**: v2.x for strict type validation
- **PyYAML**: For YAML parsing
- **Result Pattern**: `shared.type_definitions.result`

### Technical Constraints
- **Python Version**: 3.10+ (for `list[T]` syntax)
- **File Size Limit**: Max 10MB configuration files
- **Encoding**: UTF-8 only

### Business Constraints
- **Backward Compatibility**: Existing Agency configs must validate successfully
- **Error Clarity**: Non-technical users must understand validation errors

---

## Risk Assessment

### High Risk Items
- **Risk 1**: Pydantic validation errors may be too technical for DevOps engineers
  - *Mitigation*: Wrap Pydantic errors in user-friendly ConfigError with suggestions

### Medium Risk Items
- **Risk 2**: YAML parsing may fail on complex multi-line strings
  - *Mitigation*: Comprehensive test suite with real-world config examples
- **Risk 3**: Performance degradation on large config files
  - *Mitigation*: Performance benchmarks as acceptance criteria

### Constitutional Risks
- **Constitutional Risk 1**: Pydantic errors may lead to try/catch control flow
  - *Mitigation*: Wrap all Pydantic operations in Result-returning functions
- **Constitutional Risk 2**: Nested configs may use `Dict[Any, Any]`
  - *Mitigation*: Define explicit Pydantic models for all nesting levels

---

## Testing Strategy

### Test Categories

#### Unit Tests (TDD - Write First)
```python
def test_parse_valid_yaml_config():
    """Test parsing valid YAML configuration."""
    # Arrange
    config_yaml = """
    planner:
      model: gpt-5
      temperature: 0.7
    memory:
      use_enhanced_memory: true
      vector_store_path: /path/to/store
    """

    # Act
    result = parse_config_file("config.yaml")

    # Assert
    assert result.is_ok()
    config = result.unwrap()
    assert config.planner.model == "gpt-5"
    assert config.memory.use_enhanced_memory is True

def test_detect_unknown_field():
    """Test detection of unknown fields with suggestions."""
    # Arrange
    config_yaml = """
    planner:
      modell: gpt-5  # Typo: should be 'model'
    """

    # Act
    result = parse_config_file("config.yaml")

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.error_type == ConfigErrorType.UNKNOWN_FIELD
    assert "modell" in error.message
    assert "model" in error.suggestion
```

#### Edge Cases
- [ ] Empty configuration file
- [ ] File with only whitespace
- [ ] Malformed YAML (unclosed quotes, invalid indentation)
- [ ] Malformed JSON (trailing commas, missing brackets)
- [ ] Extremely large files (10MB boundary)
- [ ] Unicode characters in field names/values

#### Integration Tests
- [ ] Parse real Agency configuration files from production
- [ ] Validate all example configs from documentation
- [ ] Test with configs from different Python versions

---

## Implementation Phases

### Phase 1: Foundation (This Spec Task)
- **Scope**: Define requirements, acceptance criteria, success metrics
- **Deliverables**: This specification document
- **Success Criteria**: Goals clearly defined, non-goals explicit, acceptance criteria measurable

### Phase 2: Implementation (Code Task)
- **Scope**: Implement parsing, validation, Pydantic models, Result pattern
- **Deliverables**: `config_validator.py` with strict typing and Result pattern
- **Success Criteria**: All AC-1.x, AC-2.x, AC-3.x, AC-4.x criteria met

### Phase 3: Testing (Test Task)
- **Scope**: Write comprehensive test suite with AAA pattern
- **Deliverables**: `test_config_validator.py` with >95% coverage
- **Success Criteria**: All AC-CII.x criteria met, 100% tests pass

---

## Review & Approval

### Review Criteria
- [ ] **Completeness**: All specification sections filled with appropriate detail
- [ ] **Clarity**: Requirements are unambiguous and testable
- [ ] **Feasibility**: Technical implementation realistic (~3000 tokens)
- [ ] **Constitutional Compliance**: Alignment with all five constitutional articles
- [ ] **Simplicity**: Feature scope appropriate for demo/learning purposes

### Approval Status
- [ ] **Stakeholder Approval**: Pending /primeA orchestrator review
- [ ] **Technical Approval**: Pending CodeAgent feasibility check
- [ ] **Constitutional Compliance**: Pending QualityEnforcer validation
- [ ] **Final Approval**: Ready for implementation

---

## Appendices

### Appendix A: Example Configuration Files

**Valid Config (config_valid.yaml)**:
```yaml
planner:
  model: gpt-5
  temperature: 0.7
  max_tokens: 4000

coder:
  model: gpt-5
  temperature: 0.3
  max_tokens: 8000

memory:
  use_enhanced_memory: true
  vector_store_path: ~/.agency/vector_store
  session_id: demo_session

log_level: INFO
```

**Invalid Config (config_invalid_missing_field.yaml)**:
```yaml
planner:
  # Missing required 'model' field
  temperature: 0.7

memory:
  use_enhanced_memory: true
  vector_store_path: ~/.agency/vector_store
```

### Appendix B: References
- **Constitutional Article II**: 100% Verification and Stability (TDD requirement)
- **Constitutional Law #2**: Strict Typing Always (no `Dict[Any, Any]`)
- **Constitutional Law #5**: Result<T, E> pattern (no try/catch control flow)
- **Constitutional Law #8**: Focused Functions (<50 lines)
- **ADR-008**: Strict Typing Standards
- **ADR-010**: Result Pattern Usage

### Appendix C: Related Documents
- **Plan**: `plan-primeA-demo-config-validator.md` (to be created in Code task)
- **Tests**: `test_config_validator.py` (to be created in Test task)
- **Implementation**: `config_validator.py` (to be created in Code task)

---

## Revision History

| Version | Date       | Author        | Changes                                    |
| ------- | ---------- | ------------- | ------------------------------------------ |
| 1.0     | 2025-10-10 | PlannerAgent  | Initial specification for /primeA demo     |

---

## Success Metrics Summary

**Specification Quality**:
- ✅ Goals clearly defined (5 primary goals)
- ✅ Non-goals explicitly stated (5 exclusions, 3 future considerations)
- ✅ Acceptance criteria measurable (29 functional + 9 non-functional + 15 constitutional)
- ✅ Success metrics defined (5 key metrics with 100% targets)

**Constitutional Alignment**:
- ✅ Article I: Complete context via comprehensive validation (AC-CI.x)
- ✅ Article II: 100% verification via TDD and test coverage (AC-CII.x)
- ✅ Article III: Automated enforcement via mypy/pytest (AC-CIII.x)
- ✅ Article IV: Learning integration via VectorStore query/store (AC-CIV.x)
- ✅ Article V: Spec-driven process followed (this document)

**Feature Scope**:
- ✅ Simple enough for ~3000 token implementation
- ✅ Realistic use case (configuration validation)
- ✅ Demonstrates core patterns (Pydantic, Result, TDD)
- ✅ Educational value for /primeA demonstration

---

*"Configuration validation: Where strict typing meets functional error handling."*
