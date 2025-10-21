# ADR-022: Autonomous-Development-Ready Auditor Architecture

## Status

**Proposed** - Awaiting approval for implementation

## Context

### Current State (5/5 Stars - Phase 4 Complete)

The continuous audit system (`scripts/continuous_audit_m4pro.py`) currently delivers:

- **AST-based detection** with zero false positives
- **Specific function names** and line-level accuracy
- **328 accurate recommendations** across 5 categories
- **Smart deduplication** (>70% similarity merging)
- **Priority elevation** (3+ instances → bump priority)
- **Local M4 Pro execution** (qwen2.5-coder:32b)

**Problem**: Recommendations require **human interpretation** before CodingAgent can act. The autonomous fixer (`scripts/autonomous_recommendation_fixer.py`) exists but lacks critical metadata to make safe, confident decisions.

### The Autonomous Gap

Current recommendation format:
```markdown
## Summary
Remove commented code blocks (38 lines) in validator.py

## Details
Found commented code in function validate_input() lines 45-82

## Steps
1. Remove lines 45-82
2. Run tests to verify no behavior change
```

**Missing for Autonomy**:
- Can this be auto-fixed safely? (no confidence score)
- What's the actual fix code? (no generated patch)
- What dependencies exist? (no inter-file analysis)
- What's the risk? (no quantified risk score)
- How to validate? (vague "run tests" - which tests?)
- What similar fixes succeeded before? (no learning integration)

### Target State (6/5 Stars - Autonomous-Ready)

Make recommendations **immediately actionable** by CodingAgent:
- **Auto-fixability classification** with confidence scores
- **Generated fix code** ready to apply
- **Dependency analysis** for safe ordering
- **Risk quantification** for rollback planning
- **Validation strategies** with specific test commands
- **Learning integration** for success probability

## Decision

**Implement Enhanced Recommendation Model with Auto-Fix Metadata**

Extend the current `Recommendation` Pydantic model (in `scripts/continuous_audit_m4pro.py`) with autonomous execution metadata, and create a new `AutonomousFixer` agent that leverages this metadata for safe, confident fixes.

## Architecture Design

### 1. Enhanced Pydantic Model

**File**: `shared/models/auditor.py` (NEW)

```python
"""
Auditor models for autonomous-ready recommendations.
Constitutional Law #2: Strict typing enforcement
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Enumerations
# ============================================================================


class FixDifficulty(str, Enum):
    """Difficulty levels for automatic fixing."""

    TRIVIAL = "trivial"      # <5min, 1-3 line changes, zero risk
    SIMPLE = "simple"        # 5-15min, single function edits, low risk
    MODERATE = "moderate"    # 15-60min, multi-function changes, medium risk
    COMPLEX = "complex"      # >60min, architectural changes, high risk


class RiskLevel(str, Enum):
    """Risk levels for applying fixes."""

    ZERO = "zero"           # 0.0-0.1: Pure deletion, no behavior change
    LOW = "low"             # 0.1-0.3: Safe refactors, validated patterns
    MEDIUM = "medium"       # 0.3-0.6: Logic changes with test coverage
    HIGH = "high"           # 0.6-0.8: Public API changes
    CRITICAL = "critical"   # 0.8-1.0: Core infrastructure, multi-file


class ValidationStrategy(str, Enum):
    """Validation approaches for fixes."""

    SYNTAX = "syntax"                  # Compile-only check
    UNIT_TESTS = "unit_tests"          # Affected unit tests only
    INTEGRATION_TESTS = "integration_tests"  # Integration tests for module
    FULL_SUITE = "full_suite"          # All 1,568 tests (Article II)
    MANUAL_REVIEW = "manual_review"    # Human required


class RollbackDifficulty(str, Enum):
    """Difficulty of rolling back a fix."""

    EASY = "easy"          # Git revert, single commit
    MEDIUM = "medium"      # Multiple files, manual validation
    HARD = "hard"          # Database migrations, config changes


# ============================================================================
# Sub-Models
# ============================================================================


class FileLocation(BaseModel):
    """Location of an issue in a file (from existing model)."""

    model_config = ConfigDict(extra="forbid")

    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    function_name: str | None = None  # NEW: Specific function affected
    class_name: str | None = None     # NEW: Specific class affected


class DependencyInfo(BaseModel):
    """Inter-file dependencies for fix ordering."""

    model_config = ConfigDict(extra="forbid")

    depends_on_files: list[str] = Field(
        default_factory=list,
        description="Files that must be fixed first"
    )
    blocks_files: list[str] = Field(
        default_factory=list,
        description="Files that depend on this file"
    )
    recommendation_dependencies: list[str] = Field(
        default_factory=list,
        description="Recommendation IDs that must be applied first"
    )
    enables_recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendation IDs enabled by this fix"
    )


class RiskFactors(BaseModel):
    """Detailed risk assessment."""

    model_config = ConfigDict(extra="forbid")

    modifies_public_api: bool = Field(default=False)
    no_test_coverage: bool = Field(default=False)
    changes_core_logic: bool = Field(default=False)
    multi_file_impact: bool = Field(default=False)
    external_dependencies: bool = Field(default=False)
    database_changes: bool = Field(default=False)
    affects_critical_path: bool = Field(default=False)

    risk_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Calculated risk score (0.0=zero risk, 1.0=critical risk)"
    )

    risk_level: RiskLevel = Field(description="Categorical risk level")
    rollback_difficulty: RollbackDifficulty = Field(description="How hard to rollback")

    def calculate_risk_score(self) -> float:
        """Calculate quantified risk score from boolean factors."""
        score = 0.0

        # Weight each factor
        if self.modifies_public_api:
            score += 0.25
        if self.no_test_coverage:
            score += 0.20
        if self.changes_core_logic:
            score += 0.15
        if self.multi_file_impact:
            score += 0.15
        if self.external_dependencies:
            score += 0.10
        if self.database_changes:
            score += 0.10
        if self.affects_critical_path:
            score += 0.05

        return min(1.0, score)


class ImpactMetrics(BaseModel):
    """Quantified impact of applying the fix."""

    model_config = ConfigDict(extra="forbid")

    lines_removed: int = Field(default=0, ge=0)
    lines_added: int = Field(default=0, ge=0)
    complexity_reduction: int = Field(default=0, description="Cyclomatic complexity delta")
    functions_affected: int = Field(default=0, ge=0)
    files_affected: int = Field(default=0, ge=0)
    test_coverage_change: float = Field(default=0.0, description="Percentage point change")
    estimated_time_saved_hours: float = Field(default=0.0, ge=0.0)


class GeneratedFix(BaseModel):
    """LLM-generated fix code with validation."""

    model_config = ConfigDict(extra="forbid")

    fix_type: Literal["deletion", "replacement", "insertion", "refactor"]

    original_code: str = Field(description="Code being changed")
    fixed_code: str = Field(description="Replacement code (empty for deletions)")

    file_path: str
    line_start: int
    line_end: int

    patch_format: str = Field(
        description="Unified diff format patch (for apply_and_verify_patch.py)"
    )

    validation_code: str = Field(
        description="Python code to validate fix (e.g., assert statements)"
    )

    llm_model: str = Field(description="Model that generated fix (e.g., qwen2.5-coder:32b)")
    generation_timestamp: datetime = Field(default_factory=datetime.now)
    generation_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="LLM's confidence in fix correctness"
    )


class ValidationPlan(BaseModel):
    """Comprehensive validation strategy."""

    model_config = ConfigDict(extra="forbid")

    strategy: ValidationStrategy

    test_commands: list[str] = Field(
        default_factory=list,
        description="Exact pytest commands to run"
    )

    estimated_test_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Expected test execution time"
    )

    success_criteria: list[str] = Field(
        default_factory=list,
        description="Conditions for success (e.g., 'All tests pass', 'No syntax errors')"
    )

    rollback_plan: str = Field(
        default="git revert HEAD",
        description="Command to rollback if validation fails"
    )


class ConstitutionalCompliance(BaseModel):
    """Constitutional alignment assessment."""

    model_config = ConfigDict(extra="forbid")

    article_i_complete_context: bool = Field(
        default=True,
        description="Fix requires complete context before action"
    )

    article_ii_verification: bool = Field(
        default=True,
        description="Fix has 100% verification strategy"
    )

    article_iii_automated_enforcement: bool = Field(
        default=True,
        description="Fix enforces via automation (not manual)"
    )

    article_iv_learning_applied: bool = Field(
        default=False,
        description="Fix uses learnings from VectorStore"
    )

    article_v_spec_driven: bool = Field(
        default=True,
        description="Fix follows spec (audit recommendation as spec)"
    )

    compliance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage of articles satisfied"
    )

    blocking_violations: list[str] = Field(
        default_factory=list,
        description="Articles violated (blocks auto-fix if non-empty)"
    )


class LearningMetadata(BaseModel):
    """Learning integration for success prediction."""

    model_config = ConfigDict(extra="forbid")

    similar_past_fixes: int = Field(
        default=0,
        ge=0,
        description="Count of similar successful fixes from VectorStore"
    )

    success_probability: float = Field(
        ge=0.0,
        le=1.0,
        description="ML-based success prediction from historical data"
    )

    failure_modes: list[str] = Field(
        default_factory=list,
        description="Known ways this type of fix can fail"
    )

    pattern_match_ids: list[str] = Field(
        default_factory=list,
        description="VectorStore pattern IDs matching this fix"
    )

    learning_applied: bool = Field(
        default=False,
        description="Whether VectorStore learnings were queried"
    )


# ============================================================================
# Main Enhanced Recommendation Model
# ============================================================================


class EnhancedRecommendation(BaseModel):
    """
    Autonomous-ready recommendation with full metadata.

    Extends existing Recommendation from continuous_audit_m4pro.py with:
    - Auto-fixability classification
    - Generated fix code
    - Dependency analysis
    - Risk quantification
    - Validation strategy
    - Learning integration
    """

    model_config = ConfigDict(extra="forbid")

    # ========================================================================
    # Original Fields (from continuous_audit_m4pro.py)
    # ========================================================================

    number: int = Field(ge=1, description="Recommendation ID")
    title: str = Field(min_length=1, description="Brief title")

    category: str = Field(description="Issue category (pruning, linting, etc.)")
    priority: str = Field(description="P0-P3 priority")
    impact: str = Field(description="Impact level (Low, Medium, High, Critical)")

    summary: str = Field(description="Brief summary")
    details: str = Field(description="Detailed description")

    locations: list[FileLocation] = Field(
        min_length=1,
        description="Affected file locations"
    )

    recommendation_steps: list[str] = Field(
        min_length=1,
        description="Implementation steps"
    )

    effort_hours: float = Field(ge=0.0, description="Estimated effort")

    status: str = Field(default="New", description="Status (New, Updated, Implemented)")
    instance_count: int = Field(default=1, ge=1, description="Instance count")

    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

    constitutional_article: str | None = Field(
        default=None,
        description="Primary constitutional article (I-V)"
    )

    # ========================================================================
    # NEW: Autonomous Execution Metadata
    # ========================================================================

    # Auto-Fixability
    auto_fixable: bool = Field(
        default=False,
        description="Can be fixed without human review"
    )

    fix_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in auto-fix (0.0-1.0)"
    )

    fix_difficulty: FixDifficulty = Field(
        default=FixDifficulty.COMPLEX,
        description="Difficulty classification"
    )

    requires_review: bool = Field(
        default=True,
        description="Manual review required before merge"
    )

    # Generated Fix
    generated_fix: GeneratedFix | None = Field(
        default=None,
        description="LLM-generated fix code (for auto-fixable items)"
    )

    # Dependency Analysis
    dependencies: DependencyInfo = Field(
        default_factory=DependencyInfo,
        description="Inter-file and inter-recommendation dependencies"
    )

    # Risk Assessment
    risk_factors: RiskFactors | None = Field(
        default=None,
        description="Detailed risk analysis"
    )

    # Impact Estimation
    impact_metrics: ImpactMetrics = Field(
        default_factory=ImpactMetrics,
        description="Quantified impact metrics"
    )

    # Validation
    validation_plan: ValidationPlan = Field(
        default_factory=ValidationPlan,
        description="Comprehensive validation strategy"
    )

    # Constitutional Compliance
    constitutional_compliance: ConstitutionalCompliance = Field(
        default_factory=ConstitutionalCompliance,
        description="Constitutional alignment assessment"
    )

    # Learning Integration
    learning_metadata: LearningMetadata = Field(
        default_factory=LearningMetadata,
        description="Learning and success prediction"
    )

    # Batch Processing
    batch_group: str | None = Field(
        default=None,
        description="Batch group identifier (e.g., 'pruning_batch_1')"
    )

    parallel_safe: bool = Field(
        default=False,
        description="Can be applied concurrently with other fixes"
    )

    # ========================================================================
    # Validation Logic
    # ========================================================================

    @field_validator("fix_confidence")
    @classmethod
    def validate_fix_confidence_requires_auto_fixable(
        cls, v: float, info
    ) -> float:
        """If fix_confidence > 0.5, auto_fixable should be True."""
        # Note: Can't access other fields during validation in Pydantic v2
        # This validation happens in classify_auto_fixability() instead
        return v

    def classify_auto_fixability(self) -> None:
        """
        Classify whether this recommendation is auto-fixable.

        Updates:
        - auto_fixable
        - fix_confidence
        - fix_difficulty
        - requires_review
        """
        # Algorithm defined in Section 2 below
        pass

    def calculate_risk_score(self) -> float:
        """Calculate and return overall risk score."""
        if self.risk_factors:
            return self.risk_factors.calculate_risk_score()
        return 1.0  # Unknown = high risk

    def is_safe_for_autonomous_fix(self) -> bool:
        """
        Determine if safe for autonomous fixing.

        Criteria:
        - auto_fixable = True
        - fix_confidence >= 0.80
        - risk_score < 0.30
        - No constitutional blocking violations
        - Validation strategy defined
        """
        if not self.auto_fixable:
            return False

        if self.fix_confidence < 0.80:
            return False

        if self.calculate_risk_score() >= 0.30:
            return False

        if self.constitutional_compliance.blocking_violations:
            return False

        if self.validation_plan.strategy == ValidationStrategy.MANUAL_REVIEW:
            return False

        return True
```

### 2. Auto-Fixability Classification Algorithm

**File**: `auditor_agent/classifiers.py` (NEW)

```python
"""
Auto-fixability classifiers for autonomous recommendations.

Constitutional Compliance:
- Article I: Complete context analysis before classification
- Article II: 100% verification via validation strategies
- Article IV: Learning integration for success prediction
"""

from shared.models.auditor import (
    EnhancedRecommendation,
    FixDifficulty,
    ValidationStrategy,
    RiskLevel,
    RollbackDifficulty,
)
from shared.agent_context import AgentContext


class AutoFixabilityClassifier:
    """Classifies recommendations for autonomous fixing."""

    def __init__(self, context: AgentContext):
        self.context = context

    def classify(self, rec: EnhancedRecommendation) -> None:
        """
        Classify auto-fixability and update recommendation metadata.

        Classification rules:

        TRIVIAL (auto_fixable=True, confidence=0.95+):
        - Pure deletions (commented code, unused imports)
        - <5 lines affected
        - Zero behavior change
        - Syntax-only validation

        SIMPLE (auto_fixable=True, confidence=0.80+):
        - Single function edits
        - Extract 2-3 line helper functions
        - Rename operations
        - 5-20 lines affected
        - Unit tests validation

        MODERATE (auto_fixable=False, confidence=0.60+):
        - Multi-function changes
        - Split 80+ line functions
        - Refactor duplicates
        - 20-100 lines affected
        - Integration tests required

        COMPLEX (auto_fixable=False, confidence=<0.60):
        - Architectural changes
        - Multi-file refactors
        - Public API modifications
        - >100 lines affected
        - Full suite validation
        """

        # Determine fix type and scope
        fix_type = self._determine_fix_type(rec)
        lines_affected = self._count_lines_affected(rec)
        files_affected = len(set(loc.file_path for loc in rec.locations))

        # Check for simple patterns
        is_pure_deletion = self._is_pure_deletion(rec)
        is_rename = self._is_rename_operation(rec)
        is_extract_function = self._is_extract_function(rec)

        # Classify difficulty
        if is_pure_deletion and lines_affected < 5:
            rec.fix_difficulty = FixDifficulty.TRIVIAL
            rec.auto_fixable = True
            rec.fix_confidence = 0.95
            rec.requires_review = False
            rec.validation_plan.strategy = ValidationStrategy.SYNTAX

        elif (is_rename or is_extract_function) and files_affected == 1:
            rec.fix_difficulty = FixDifficulty.SIMPLE
            rec.auto_fixable = True
            rec.fix_confidence = 0.85
            rec.requires_review = False
            rec.validation_plan.strategy = ValidationStrategy.UNIT_TESTS

        elif files_affected == 1 and lines_affected < 100:
            rec.fix_difficulty = FixDifficulty.MODERATE
            rec.auto_fixable = False  # Needs review
            rec.fix_confidence = 0.65
            rec.requires_review = True
            rec.validation_plan.strategy = ValidationStrategy.INTEGRATION_TESTS

        else:
            rec.fix_difficulty = FixDifficulty.COMPLEX
            rec.auto_fixable = False
            rec.fix_confidence = 0.40
            rec.requires_review = True
            rec.validation_plan.strategy = ValidationStrategy.FULL_SUITE

        # Query learnings to boost confidence
        self._apply_learning_boost(rec)

    def _determine_fix_type(self, rec: EnhancedRecommendation) -> str:
        """Determine type of fix from recommendation text."""
        title_lower = rec.title.lower()

        if "remove" in title_lower or "delete" in title_lower:
            return "deletion"
        elif "rename" in title_lower:
            return "rename"
        elif "extract" in title_lower:
            return "extraction"
        elif "split" in title_lower:
            return "split"
        elif "consolidate" in title_lower:
            return "consolidation"
        else:
            return "refactor"

    def _count_lines_affected(self, rec: EnhancedRecommendation) -> int:
        """Count total lines affected across all locations."""
        total = 0
        for loc in rec.locations:
            if loc.line_start and loc.line_end:
                total += (loc.line_end - loc.line_start + 1)
        return total

    def _is_pure_deletion(self, rec: EnhancedRecommendation) -> bool:
        """Check if fix is pure deletion (no replacement)."""
        keywords = ["remove commented code", "delete unused", "remove dead code"]
        return any(kw in rec.title.lower() for kw in keywords)

    def _is_rename_operation(self, rec: EnhancedRecommendation) -> bool:
        """Check if fix is simple rename."""
        return "rename" in rec.title.lower()

    def _is_extract_function(self, rec: EnhancedRecommendation) -> bool:
        """Check if fix is extract helper function."""
        return "extract" in rec.title.lower()

    def _apply_learning_boost(self, rec: EnhancedRecommendation) -> None:
        """
        Query VectorStore for similar fixes and boost confidence.

        Article IV: Continuous Learning integration
        """
        # Query VectorStore for similar fixes
        similar_fixes = self.context.search_memories(
            tags=["autonomous_fix", "success", rec.category],
            query=f"{rec.title} {rec.summary}",
            top_k=5,
            include_session=False  # Cross-session learning
        )

        if similar_fixes:
            rec.learning_metadata.similar_past_fixes = len(similar_fixes)
            rec.learning_metadata.learning_applied = True

            # Calculate success probability from historical data
            success_count = sum(
                1 for fix in similar_fixes
                if fix.get("content", {}).get("success", False)
            )
            rec.learning_metadata.success_probability = (
                success_count / len(similar_fixes)
            )

            # Boost confidence if historical success rate > 80%
            if rec.learning_metadata.success_probability > 0.80:
                rec.fix_confidence = min(
                    0.99,
                    rec.fix_confidence + 0.10
                )
```

### 3. Fix Code Generator

**File**: `auditor_agent/fix_generator.py` (NEW)

```python
"""
LLM-powered fix code generation for autonomous recommendations.

Uses qwen2.5-coder:32b via trinity_protocol AgentRegistry.
"""

from pathlib import Path
from datetime import datetime

from trinity_protocol.core.agent_registry import (
    AgentRegistry,
    AgentType,
    ModelTier,
)
from shared.models.auditor import (
    EnhancedRecommendation,
    GeneratedFix,
    FileLocation,
)
from shared.type_definitions.result import Result, Ok, Err


class FixCodeGenerator:
    """Generates executable fix code using LLM."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.model = "qwen2.5-coder:32b"  # LOCAL tier

    def generate_fix(
        self,
        rec: EnhancedRecommendation
    ) -> Result[GeneratedFix, str]:
        """
        Generate fix code for auto-fixable recommendation.

        Returns:
            Ok(GeneratedFix) if generation succeeds
            Err(error_message) if generation fails
        """
        if not rec.auto_fixable:
            return Err(f"Recommendation {rec.number} not auto-fixable")

        # Get primary location
        if not rec.locations:
            return Err("No locations specified")

        primary_loc = rec.locations[0]

        # Read current code
        current_code_result = self._read_code_section(primary_loc)
        if isinstance(current_code_result, Err):
            return current_code_result

        current_code = current_code_result.value

        # Generate fix with LLM
        fix_prompt = self._build_fix_prompt(rec, current_code)

        # Use trinity_protocol agent
        agent = self.registry.get_agent(AgentType.CODER)

        try:
            response = agent.run(fix_prompt)

            # Parse LLM response
            fixed_code = self._parse_fix_response(response)

            # Generate unified diff patch
            patch = self._generate_patch(
                file_path=primary_loc.file_path,
                original=current_code,
                fixed=fixed_code,
                line_start=primary_loc.line_start or 1
            )

            # Generate validation code
            validation = self._generate_validation(rec, fixed_code)

            # Determine fix type
            fix_type = self._determine_fix_type(current_code, fixed_code)

            return Ok(GeneratedFix(
                fix_type=fix_type,
                original_code=current_code,
                fixed_code=fixed_code,
                file_path=primary_loc.file_path,
                line_start=primary_loc.line_start or 1,
                line_end=primary_loc.line_end or 1,
                patch_format=patch,
                validation_code=validation,
                llm_model=self.model,
                generation_timestamp=datetime.now(),
                generation_confidence=0.85  # From LLM metadata if available
            ))

        except Exception as e:
            return Err(f"Fix generation failed: {str(e)}")

    def _build_fix_prompt(
        self,
        rec: EnhancedRecommendation,
        current_code: str
    ) -> str:
        """Build LLM prompt for fix generation."""
        return f"""
You are a code quality expert. Generate ONLY the fixed code (no explanations).

ISSUE: {rec.title}
CATEGORY: {rec.category}
PRIORITY: {rec.priority}

SUMMARY: {rec.summary}

DETAILS: {rec.details}

CURRENT CODE:
```python
{current_code}
```

STEPS TO FIX:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(rec.recommendation_steps))}

CONSTITUTIONAL REQUIREMENTS:
- Article I: Preserve complete context
- Article II: Maintain 100% test compatibility
- Article V: Follow spec (this recommendation)

Generate ONLY the fixed code (no markdown, no explanations):
"""

    def _parse_fix_response(self, response: str) -> str:
        """Extract code from LLM response."""
        # Remove markdown code blocks if present
        if "```python" in response:
            start = response.index("```python") + 9
            end = response.rindex("```")
            return response[start:end].strip()
        elif "```" in response:
            start = response.index("```") + 3
            end = response.rindex("```")
            return response[start:end].strip()
        else:
            return response.strip()

    def _read_code_section(
        self,
        loc: FileLocation
    ) -> Result[str, str]:
        """Read code section from file."""
        try:
            with open(loc.file_path, 'r') as f:
                lines = f.readlines()

            if loc.line_start and loc.line_end:
                # Extract specific lines
                start_idx = loc.line_start - 1
                end_idx = loc.line_end
                return Ok("".join(lines[start_idx:end_idx]))
            else:
                # Return entire file
                return Ok("".join(lines))

        except FileNotFoundError:
            return Err(f"File not found: {loc.file_path}")
        except Exception as e:
            return Err(f"Read error: {str(e)}")

    def _generate_patch(
        self,
        file_path: str,
        original: str,
        fixed: str,
        line_start: int
    ) -> str:
        """Generate unified diff format patch."""
        import difflib

        original_lines = original.splitlines(keepends=True)
        fixed_lines = fixed.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
            n=3  # Context lines
        )

        return "".join(diff)

    def _generate_validation(
        self,
        rec: EnhancedRecommendation,
        fixed_code: str
    ) -> str:
        """Generate validation code."""
        if rec.fix_difficulty == "trivial":
            # Syntax-only validation
            return f"""
# Syntax validation
try:
    compile('''{fixed_code}''', '<string>', 'exec')
    print("✓ Syntax valid")
except SyntaxError as e:
    print(f"✗ Syntax error: {{e}}")
    raise
"""
        else:
            # Test-based validation
            test_cmd = " ".join(rec.validation_plan.test_commands)
            return f"""
# Test validation
import subprocess
result = subprocess.run(
    ['{test_cmd}'],
    capture_output=True,
    text=True,
    shell=True
)
if result.returncode == 0:
    print("✓ Tests passed")
else:
    print(f"✗ Tests failed: {{result.stderr}}")
    raise AssertionError("Test validation failed")
"""

    def _determine_fix_type(
        self,
        original: str,
        fixed: str
    ) -> str:
        """Determine fix type from code comparison."""
        if not fixed.strip():
            return "deletion"
        elif len(fixed) > len(original) * 1.2:
            return "insertion"
        elif abs(len(fixed) - len(original)) < len(original) * 0.1:
            return "replacement"
        else:
            return "refactor"
```

### 4. Dependency Analyzer

**File**: `auditor_agent/dependency_analyzer.py` (NEW)

```python
"""
AST-based dependency analysis for safe fix ordering.

Constitutional Compliance:
- Article I: Complete context analysis before recommendations
"""

import ast
from pathlib import Path
from typing import Set

from shared.models.auditor import (
    EnhancedRecommendation,
    DependencyInfo,
)


class DependencyAnalyzer:
    """Analyzes inter-file dependencies for safe fix ordering."""

    def __init__(self, codebase_root: Path):
        self.codebase_root = codebase_root
        self.import_graph: dict[str, Set[str]] = {}

    def analyze_dependencies(
        self,
        rec: EnhancedRecommendation
    ) -> DependencyInfo:
        """
        Analyze dependencies for recommendation.

        Returns:
            DependencyInfo with:
            - depends_on_files: Files that must be fixed first
            - blocks_files: Files that depend on this file
        """
        if not rec.locations:
            return DependencyInfo()

        primary_file = rec.locations[0].file_path

        # Build import graph if not cached
        if not self.import_graph:
            self._build_import_graph()

        # Find dependencies
        depends_on = self._get_dependencies(primary_file)
        blocks = self._get_dependents(primary_file)

        return DependencyInfo(
            depends_on_files=list(depends_on),
            blocks_files=list(blocks)
        )

    def _build_import_graph(self) -> None:
        """Build import graph for entire codebase."""
        for py_file in self.codebase_root.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                imports = self._extract_imports(tree)
                self.import_graph[str(py_file)] = imports

            except Exception:
                # Skip files that can't be parsed
                continue

    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract import statements from AST."""
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)

        return imports

    def _get_dependencies(self, file_path: str) -> Set[str]:
        """Get files that file_path imports."""
        if file_path not in self.import_graph:
            return set()

        return self.import_graph[file_path]

    def _get_dependents(self, file_path: str) -> Set[str]:
        """Get files that import file_path."""
        dependents = set()

        # Convert file path to module path
        module_path = self._file_to_module(file_path)

        for file, imports in self.import_graph.items():
            if module_path in imports:
                dependents.add(file)

        return dependents

    def _file_to_module(self, file_path: str) -> str:
        """Convert file path to module path."""
        rel_path = Path(file_path).relative_to(self.codebase_root)
        module = str(rel_path).replace("/", ".").replace(".py", "")
        return module

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".git",
            "venv",
            "node_modules",
            ".archive"
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
```

### 5. Risk Scorer

**File**: `auditor_agent/risk_scorer.py` (NEW)

```python
"""
Risk scoring for autonomous fix decisions.

Constitutional Compliance:
- Article II: 100% verification via risk quantification
"""

from pathlib import Path
from shared.models.auditor import (
    EnhancedRecommendation,
    RiskFactors,
    RiskLevel,
    RollbackDifficulty,
)


class RiskScorer:
    """Quantify risk for recommendations."""

    def __init__(self, codebase_root: Path):
        self.codebase_root = codebase_root

        # Define critical paths
        self.critical_paths = [
            "agency.py",
            "constitution.md",
            "shared/agent_context.py",
            "shared/model_policy.py",
        ]

    def score_risk(
        self,
        rec: EnhancedRecommendation
    ) -> RiskFactors:
        """
        Calculate risk score for recommendation.

        Risk factors:
        - Modifies public API (0.25)
        - No test coverage (0.20)
        - Changes core logic (0.15)
        - Multi-file impact (0.15)
        - External dependencies (0.10)
        - Database changes (0.10)
        - Affects critical path (0.05)

        Returns:
            RiskFactors with quantified risk_score (0.0-1.0)
        """
        if not rec.locations:
            # Unknown = high risk
            return RiskFactors(
                risk_score=1.0,
                risk_level=RiskLevel.CRITICAL,
                rollback_difficulty=RollbackDifficulty.HARD
            )

        primary_file = rec.locations[0].file_path

        # Assess boolean risk factors
        modifies_public_api = self._checks_public_api(rec)
        no_test_coverage = self._checks_test_coverage(primary_file)
        changes_core_logic = self._checks_core_logic(rec)
        multi_file = len(set(loc.file_path for loc in rec.locations)) > 1
        external_deps = self._checks_external_deps(primary_file)
        database_changes = self._checks_database_changes(rec)
        critical_path = self._checks_critical_path(primary_file)

        # Create RiskFactors instance
        risk = RiskFactors(
            modifies_public_api=modifies_public_api,
            no_test_coverage=no_test_coverage,
            changes_core_logic=changes_core_logic,
            multi_file_impact=multi_file,
            external_dependencies=external_deps,
            database_changes=database_changes,
            affects_critical_path=critical_path,
            risk_score=0.0,  # Will be calculated
            risk_level=RiskLevel.ZERO,  # Will be set
            rollback_difficulty=RollbackDifficulty.EASY  # Will be set
        )

        # Calculate score
        risk.risk_score = risk.calculate_risk_score()

        # Set categorical level
        if risk.risk_score < 0.1:
            risk.risk_level = RiskLevel.ZERO
            risk.rollback_difficulty = RollbackDifficulty.EASY
        elif risk.risk_score < 0.3:
            risk.risk_level = RiskLevel.LOW
            risk.rollback_difficulty = RollbackDifficulty.EASY
        elif risk.risk_score < 0.6:
            risk.risk_level = RiskLevel.MEDIUM
            risk.rollback_difficulty = RollbackDifficulty.MEDIUM
        elif risk.risk_score < 0.8:
            risk.risk_level = RiskLevel.HIGH
            risk.rollback_difficulty = RollbackDifficulty.MEDIUM
        else:
            risk.risk_level = RiskLevel.CRITICAL
            risk.rollback_difficulty = RollbackDifficulty.HARD

        return risk

    def _checks_public_api(self, rec: EnhancedRecommendation) -> bool:
        """Check if modifies public API."""
        # Heuristic: look for function name changes or signature changes
        keywords = ["rename", "change signature", "modify api", "public"]
        return any(kw in rec.details.lower() for kw in keywords)

    def _checks_test_coverage(self, file_path: str) -> bool:
        """Check if file has test coverage."""
        # Look for corresponding test file
        test_file = file_path.replace(".py", "_test.py")
        if Path(test_file).exists():
            return False

        test_file2 = str(Path(file_path).parent / "tests" / Path(file_path).name)
        if Path(test_file2).exists():
            return False

        # No test file found
        return True

    def _checks_core_logic(self, rec: EnhancedRecommendation) -> bool:
        """Check if changes core business logic."""
        # Heuristic: look for logic keywords
        keywords = ["algorithm", "calculation", "validation", "processing"]
        return any(kw in rec.details.lower() for kw in keywords)

    def _checks_external_deps(self, file_path: str) -> bool:
        """Check if has external dependencies."""
        # Read imports and check for external packages
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Simple heuristic: check for common external imports
            external_packages = [
                "requests", "numpy", "pandas", "anthropic", "openai"
            ]
            return any(pkg in content for pkg in external_packages)

        except Exception:
            return False

    def _checks_database_changes(self, rec: EnhancedRecommendation) -> bool:
        """Check if involves database changes."""
        keywords = ["database", "migration", "schema", "firestore", "sql"]
        return any(kw in rec.details.lower() for kw in keywords)

    def _checks_critical_path(self, file_path: str) -> bool:
        """Check if file is in critical path."""
        return any(
            critical in file_path
            for critical in self.critical_paths
        )
```

### 6. Integration into continuous_audit_m4pro.py

**Modifications to existing `scripts/continuous_audit_m4pro.py`**:

```python
# Add imports
from shared.models.auditor import EnhancedRecommendation
from auditor_agent.classifiers import AutoFixabilityClassifier
from auditor_agent.fix_generator import FixCodeGenerator
from auditor_agent.dependency_analyzer import DependencyAnalyzer
from auditor_agent.risk_scorer import RiskScorer

# In ContinuousAuditor class:

def __init__(self, ...):
    # ... existing code ...

    # NEW: Initialize autonomous components
    self.classifier = AutoFixabilityClassifier(self.context)
    self.fix_generator = FixCodeGenerator(self.registry)
    self.dependency_analyzer = DependencyAnalyzer(Path.cwd())
    self.risk_scorer = RiskScorer(Path.cwd())

def _process_audit_result(self, issue: Issue) -> None:
    """Process single audit result with autonomous metadata."""

    # ... existing deduplication logic ...

    # NEW: Create enhanced recommendation
    enhanced_rec = EnhancedRecommendation(
        number=self._get_next_number(),
        title=issue.title,
        category=issue.category,
        priority=issue.priority,
        impact=issue.impact,
        summary=issue.summary,
        details=issue.details,
        locations=[
            FileLocation(
                file_path=loc.file_path,
                line_start=loc.line_start,
                line_end=loc.line_end
            )
            for loc in issue.locations
        ],
        recommendation_steps=issue.recommendation_steps,
        effort_hours=issue.effort_hours,
        constitutional_article=issue.constitutional_article
    )

    # NEW: Classify auto-fixability
    self.classifier.classify(enhanced_rec)

    # NEW: Analyze dependencies
    enhanced_rec.dependencies = self.dependency_analyzer.analyze_dependencies(
        enhanced_rec
    )

    # NEW: Score risk
    enhanced_rec.risk_factors = self.risk_scorer.score_risk(enhanced_rec)

    # NEW: Generate fix code (if auto-fixable)
    if enhanced_rec.auto_fixable and enhanced_rec.fix_confidence > 0.80:
        fix_result = self.fix_generator.generate_fix(enhanced_rec)
        if isinstance(fix_result, Ok):
            enhanced_rec.generated_fix = fix_result.value

    # NEW: Calculate impact metrics
    enhanced_rec.impact_metrics.lines_removed = sum(
        (loc.line_end or 0) - (loc.line_start or 0) + 1
        for loc in enhanced_rec.locations
        if loc.line_start and loc.line_end
    )
    enhanced_rec.impact_metrics.files_affected = len(
        set(loc.file_path for loc in enhanced_rec.locations)
    )

    # ... existing write recommendation logic ...
```

## Rationale

### Why Enhanced Metadata?

**Current Pain Point**: The autonomous fixer (`autonomous_recommendation_fixer.py`) must:
1. Parse markdown recommendations (brittle)
2. Guess fix complexity (no confidence scores)
3. Apply fixes blindly (no risk assessment)
4. Validate generically (no specific test commands)
5. Hope for success (no learning integration)

**Solution**: Structured metadata enables:
- **Safe autonomous decisions** (fix_confidence + risk_score thresholds)
- **Specific validation** (exact pytest commands)
- **Learning-driven improvements** (VectorStore success patterns)
- **Intelligent ordering** (dependency-aware execution)
- **Rollback planning** (difficulty assessment)

### Why LLM-Generated Fixes?

**Leverage qwen2.5-coder:32b** (already available locally):
- **Code understanding** superior to regex/AST patterns
- **Context-aware fixes** that preserve intent
- **Unified diff generation** for `apply_and_verify_patch.py`
- **Cost-effective** (local execution, no API costs)

### Why Dependency Analysis?

**Safe fix ordering** prevents:
- Breaking imports before fixing dependencies
- Cascading test failures
- Rollback complexity

**Example**:
```
File A imports File B
Recommendation 42: Refactor File B
Recommendation 43: Update File A imports

Correct Order: 42 → 43 (fix B first, then A)
Wrong Order: 43 → 42 (breaks A's imports!)
```

### Why Risk Quantification?

**Enables graduated autonomy**:
```python
if risk_score < 0.10:
    # Apply immediately, no review
    apply_fix_auto()
elif risk_score < 0.30:
    # Apply to branch, notify for review
    apply_fix_with_review()
else:
    # Human required
    create_github_issue()
```

## Consequences

### Positive

1. **Autonomous Execution** - CodingAgent can apply 60-70% of recommendations without human intervention
2. **Reduced Cognitive Load** - Humans review only high-risk changes
3. **Faster Feedback** - Auto-fixes applied within minutes, not days
4. **Learning Integration** - Article IV compliance through VectorStore success patterns
5. **Constitutional Compliance** - All 5 articles satisfied automatically
6. **Graduated Risk** - Progressive autonomy based on confidence/risk
7. **Specific Validation** - Exact test commands eliminate guesswork
8. **Dependency Safety** - AST-based ordering prevents cascading failures
9. **Rollback Planning** - Risk assessment includes rollback difficulty
10. **Patch Format** - Ready for `apply_and_verify_patch.py` tool

### Negative

1. **Increased Complexity** - More metadata to manage
2. **LLM Dependency** - Fix generation requires qwen2.5-coder:32b
3. **Initial Setup Time** - Classification/generation adds 2-5s per recommendation
4. **Storage Overhead** - Enhanced recommendations are ~3x larger (JSON)
5. **False Confidence** - LLM may generate incorrect fix with high confidence
6. **Validation Overhead** - Test execution adds 2-30s per fix

### Risks

1. **Bad Auto-Fixes**
   - **Mitigation**: Confidence threshold (>0.80), risk threshold (<0.30), test validation
   - **Rollback**: Git revert + telemetry logging

2. **Dependency Graph Errors**
   - **Mitigation**: Conservative dependency analysis (err on side of caution)
   - **Fallback**: Manual ordering if graph analysis fails

3. **LLM Hallucination**
   - **Mitigation**: Syntax validation + test execution before commit
   - **Detection**: Compare generated fix against recommendation steps

4. **Performance Degradation**
   - **Mitigation**: Async fix generation, batch processing
   - **Monitoring**: Telemetry for generation times

## Alternatives Considered

### Alternative 1: Rule-Based Classifiers (No LLM)

**Description**: Use AST analysis + regex patterns to classify and generate fixes

**Pros**:
- Deterministic, no LLM uncertainty
- Faster execution (<100ms vs 2-5s)
- No external dependencies

**Cons**:
- Brittle, requires maintaining rules for each fix type
- Limited to simple patterns (deletions, renames)
- Cannot handle context-aware refactors

**Why Rejected**: Phase 4 already uses qwen2.5-coder:32b for auditing. Leveraging it for fix generation provides superior quality with minimal additional cost.

### Alternative 2: GitHub Issues + Manual Fixes

**Description**: Convert recommendations to GitHub issues, human applies fixes

**Pros**:
- Zero automation risk
- Human judgment on complex cases
- No LLM dependency

**Cons**:
- Slow (days/weeks vs minutes)
- 328 recommendations = overwhelming human load
- Contradicts "autonomous development" goal

**Why Rejected**: Defeats purpose of autonomous auditor. Want to maximize autonomous fixes while keeping humans for complex cases.

### Alternative 3: Diff-Based Fix Generation

**Description**: Use `diff` to generate patches from before/after examples

**Pros**:
- No LLM needed for fix generation
- Deterministic patches

**Cons**:
- Requires before/after examples in recommendations
- Limited to exact matches (no context adaptation)
- Brittle to whitespace/formatting changes

**Why Rejected**: Insufficient flexibility for varied fix types. LLM provides better context understanding.

## Implementation Notes

### Phase 1: Data Models (Week 1)

1. Create `shared/models/auditor.py` with EnhancedRecommendation
2. Add Pydantic models for all sub-structures
3. Write unit tests for validation logic
4. Update `continuous_audit_m4pro.py` to import models

### Phase 2: Classifiers (Week 2)

1. Implement `AutoFixabilityClassifier` with classification algorithm
2. Add unit tests for trivial/simple/moderate/complex detection
3. Integrate VectorStore learning queries
4. Test classification on 50 sample recommendations

### Phase 3: Fix Generation (Week 3)

1. Implement `FixCodeGenerator` with qwen2.5-coder:32b
2. Add prompt engineering for fix generation
3. Implement patch generation (unified diff format)
4. Test on 20 trivial + 10 simple recommendations
5. Measure generation time and accuracy

### Phase 4: Risk & Dependencies (Week 4)

1. Implement `DependencyAnalyzer` with AST import graph
2. Implement `RiskScorer` with quantified risk factors
3. Add unit tests for risk calculation
4. Validate dependency ordering on multi-file recommendations

### Phase 5: Integration (Week 5)

1. Update `continuous_audit_m4pro.py` to use enhanced models
2. Migrate existing Recommendation to EnhancedRecommendation
3. Add async fix generation (parallel processing)
4. Update markdown output to include autonomous metadata
5. Test on full codebase scan

### Phase 6: Autonomous Fixer Enhancement (Week 6)

1. Update `autonomous_recommendation_fixer.py` to consume metadata
2. Implement confidence/risk-based decision logic
3. Add VectorStore learning storage for successful fixes
4. Test autonomous application of 50 recommendations
5. Measure success rate and rollback frequency

### Timeline

- **Total**: 6 weeks (30 hours effort)
- **Validation**: 2 weeks parallel testing
- **Production**: Week 9 deployment

### Dependencies

- **qwen2.5-coder:32b** (already available via Ollama)
- **trinity_protocol AgentRegistry** (production ready)
- **VectorStore** (operational per Article IV)
- **apply_and_verify_patch.py** (existing tool)
- **Test suite** (1,568 tests for validation)

### Success Metrics

- **Auto-Fix Rate**: >60% of recommendations auto-fixable
- **Fix Confidence**: >0.80 average confidence for auto-fixable
- **Success Rate**: >90% of auto-fixes pass validation
- **Rollback Rate**: <5% of applied fixes rolled back
- **Time Savings**: 80% reduction in human fix time

## Constitutional Alignment

### Article I: Complete Context Before Action

**How This Decision Supports**:
- Classifiers analyze complete file context before classification
- Dependency analyzer reads entire import graph
- Fix generator reads full code sections (not snippets)
- Risk scorer examines test coverage, critical paths, external deps

**Example**: Before classifying a recommendation as "trivial", classifier reads entire function, checks imports, analyzes test coverage.

### Article II: 100% Verification and Stability

**How This Decision Enables**:
- Validation strategies specify exact test commands
- Risk scores quantify rollback difficulty
- Generated fixes include validation code
- Test execution required before commit

**Example**: SIMPLE fixes require `ValidationStrategy.UNIT_TESTS` with specific pytest commands. Fix not applied if tests fail.

### Article III: Automated Merge Enforcement

**How This Decision Integrates**:
- Auto-fixability thresholds enforce quality (confidence >0.80, risk <0.30)
- No manual override of risk scores
- Validation strategies are automated (pytest execution)
- Rollback automated on test failure

**Example**: If `risk_score >= 0.30`, `auto_fixable` automatically set to `False`. No human can override.

### Article IV: Continuous Learning and Improvement

**How This Decision Supports**:
- VectorStore integration for similar fix queries
- Success probability calculated from historical data
- Successful fixes stored as learning patterns
- Confidence boosting from learning metadata

**Example**: When classifying recommendation, query VectorStore for similar fixes. If 8/10 similar fixes succeeded, boost `fix_confidence` by +0.10.

### Article V: Spec-Driven Development

**How This Decision Fits**:
- Audit recommendations = specifications for fixes
- Fix generator treats recommendations as formal specs
- Validation strategies enforce spec compliance
- Constitutional compliance section maps to articles

**Example**: Recommendation becomes spec → Fix generator implements spec → Tests validate spec compliance → Commit includes spec reference.

## Compliance Validation

**All 5 Articles Supported**: YES ✓

**No Constitutional Violations**: YES ✓

**Autonomous-Ready**: YES ✓

---

## References

- **ADR-001**: Complete Context Before Action
- **ADR-002**: 100% Verification and Stability
- **ADR-003**: Automated Merge Enforcement
- **ADR-004**: Continuous Learning and Improvement
- **ADR-005**: Per-Agent Model Policy (qwen2.5-coder:32b)
- **ADR-007**: Spec-Driven Development
- **Phase 4 Mission**: `specs/missions/PHASE_4_CONTINUOUS_AUDIT_MISSION.md`
- **Existing Auditor**: `scripts/continuous_audit_m4pro.py`
- **Existing Fixer**: `scripts/autonomous_recommendation_fixer.py`
- **Trinity Protocol**: `trinity_protocol/core/agent_registry.py`

---

**Version**: 1.0
**Author**: ChiefArchitect (via Claude Code)
**Date**: 2025-10-07
**Next Review**: 2025-11-01
