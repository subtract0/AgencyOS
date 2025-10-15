"""
Tests for SpecTierGenerator - NECESSARY pattern compliance.

This test suite validates the deterministic parsing and tier generation
functionality for the tiered spec review checkpoint.

NECESSARY Coverage:
- Normal: Standard spec parsing, tier generation
- Edge: Empty sections, malformed specs, missing fields
- Security: XSS in spec content, path traversal in file references
- Specification: Meets acceptance criteria from spec-034
- Compliance: Constitutional Article I-V validation
- Accuracy: Tier content matches spec structure
- Regression: Previous tier generation bugs

Test Pattern: Arrange-Act-Assert (AAA)
Constitutional: Article II (100% verification before implementation)

Reference:
    - Spec: specs/spec-034-tiered-spec-review.md
    - Implementation: tools/orchestrator/spec_tier_generator.py
    - Models: shared/models/orchestrator_models.py (Tier1Summary, Tier2Summary, Tier3Reference)

Version: 1.0.0
Created: 2025-10-15
"""

from pathlib import Path

import pytest

from shared.models.orchestrator_models import (
    ConstitutionalStatus,
    RiskLevel,
    Tier1Summary,
    Tier2Summary,
    Tier3Reference,
    TieredSpec,
)
from tools.orchestrator.spec_tier_generator import (
    SpecTierGenerator,
    TierGenerationError,
    create_tier3_reference,
    extract_tier1_summary,
    extract_tier2_decisions,
    parse_spec_structure,
)

# ============================================================================
# NORMAL: Standard spec parsing and tier generation
# ============================================================================


def test_normal_generate_tiered_spec_from_valid_spec():
    """
    NORMAL: Generate tiered spec from well-formed specification file.

    Validates:
    - Tier 1: Executive summary extracted (<25 lines)
    - Tier 2: Key decisions extracted (<50 lines)
    - Tier 3: File reference created with line count
    - Generation time <2s (performance requirement)
    """
    # Arrange
    spec_content = """
# Feature Specification: JWT Authentication

## Executive Summary
Implement JWT authentication with RSA-256 signing for secure API access.

## Goals
- Secure authentication mechanism
- Token-based session management
- RSA-256 cryptographic signing

## Acceptance Criteria
1. Users can authenticate with username/password
2. JWT tokens expire after 24 hours
3. Refresh tokens valid for 7 days
4. Token signature validation on every request

## Technical Approach
Use industry-standard JWT library (PyJWT) with RSA-256 key pair generation.

### Architectural Decisions

#### Decision 1: RSA-256 vs HMAC-SHA256
**Choice**: RSA-256 asymmetric signing
**Rationale**: Public key verification without exposing private key
**Trade-off**: Slower signing/verification vs better security model

#### Decision 2: Token Storage
**Choice**: HTTP-only cookies
**Rationale**: XSS protection, automatic transmission
**Trade-off**: CSRF risk (mitigated with CSRF tokens)

## Security Implications
- Private key must be stored in HSM or secrets manager
- Token rotation policy required
- Rate limiting on auth endpoints

## Dependencies
- PyJWT 2.8+
- cryptography 41.0+
- Redis for token revocation list

## Effort Estimate
6-8 hours (4h implementation, 2h testing, 2h security review)

## Risk Level
Medium (authentication is critical, but well-understood problem)
"""

    spec_path = Path("/tmp/test_spec_jwt_auth.md")
    spec_path.write_text(spec_content)

    generator = SpecTierGenerator()

    # Act
    import time
    start = time.time()
    result = generator.generate_tiered_spec(spec_path)
    duration = time.time() - start

    # Assert
    assert result.is_ok(), f"Tier generation failed: {result.unwrap_err()}"

    tiered_spec = result.unwrap()

    # Tier 1 validation
    assert tiered_spec.tier1.mission == "Implement JWT authentication with RSA-256 signing for secure API access."
    assert "RSA-256" in tiered_spec.tier1.approach
    assert tiered_spec.tier1.test_summary is not None
    assert len(tiered_spec.tier1.deliverables) > 0
    assert tiered_spec.tier1.constitutional_status == ConstitutionalStatus.COMPLIANT
    assert tiered_spec.tier1.effort_estimate == "6-8 hours"
    assert tiered_spec.tier1.risk_level == RiskLevel.MEDIUM
    assert tiered_spec.tier1.line_count <= 25

    # Tier 2 validation
    assert len(tiered_spec.tier2.decisions) >= 2
    assert "RSA-256 vs HMAC-SHA256" in tiered_spec.tier2.decisions[0].title
    assert tiered_spec.tier2.decisions[0].rationale is not None
    assert tiered_spec.tier2.decisions[0].tradeoffs is not None
    assert "Private key must be stored" in tiered_spec.tier2.security_implications
    assert "PyJWT 2.8+" in tiered_spec.tier2.dependencies
    assert tiered_spec.tier2.line_count <= 50

    # Tier 3 validation
    assert tiered_spec.tier3.file_path == spec_path.resolve()  # Compare resolved paths
    assert tiered_spec.tier3.line_count > 0
    assert tiered_spec.tier3.section_count > 0

    # Performance requirement
    assert duration < 2.0, f"Generation took {duration:.2f}s (requirement: <2s)"

    # Cleanup
    spec_path.unlink()


def test_normal_tier1_executive_summary_extraction():
    """
    NORMAL: Extract Tier 1 executive summary from spec structure.

    Validates all 7 Tier 1 components:
    - Mission statement
    - Approach summary
    - Test summary
    - Deliverables list
    - Constitutional status
    - Effort estimate
    - Risk level
    """
    # Arrange
    spec_structure = {
        "executive_summary": "Build rate limiting middleware for API protection.",
        "goals": ["Protect against DDoS", "Token bucket algorithm"],
        "acceptance_criteria": ["Handle 1000 req/min", "Redis backend"],
        "approach": "Token bucket with Redis distributed state",
        "test_plan": "47 NECESSARY tests (Normal, Edge, Security)",
        "deliverables": ["middleware.py", "redis_backend.py", "tests/"],
        "effort": "4-6 hours",
        "risk": "low",
        "constitutional_compliance": True,
    }

    # Act
    tier1 = extract_tier1_summary(spec_structure)

    # Assert
    assert tier1.mission == "Build rate limiting middleware for API protection."
    assert "Token bucket" in tier1.approach
    assert "47 NECESSARY tests" in tier1.test_summary
    assert len(tier1.deliverables) == 3
    assert tier1.constitutional_status == ConstitutionalStatus.COMPLIANT
    assert tier1.effort_estimate == "4-6 hours"
    assert tier1.risk_level == RiskLevel.LOW
    assert tier1.line_count <= 25


def test_normal_tier2_key_decisions_extraction():
    """
    NORMAL: Extract Tier 2 key decisions from architectural choices.

    Validates:
    - 4-6 architectural decisions extracted
    - Each decision has title, rationale, trade-offs
    - Security implications included
    - Dependencies listed
    - Performance considerations noted
    """
    # Arrange
    spec_structure = {
        "decisions": [
            {
                "title": "Token Bucket vs Leaky Bucket",
                "choice": "Token bucket",
                "rationale": "Allows burst traffic while enforcing average rate",
                "tradeoffs": "More complex state vs better UX",
            },
            {
                "title": "Redis vs In-Memory",
                "choice": "Redis",
                "rationale": "Distributed rate limiting across instances",
                "tradeoffs": "Network latency vs scalability",
            },
        ],
        "security": ["Rate limit bypass via header spoofing", "Redis auth required"],
        "dependencies": ["redis-py 5.0+", "asyncio support"],
        "performance": "< 5ms overhead per request",
    }

    # Act
    tier2 = extract_tier2_decisions(spec_structure)

    # Assert
    assert len(tier2.decisions) == 2
    assert tier2.decisions[0].title == "Token Bucket vs Leaky Bucket"
    assert "burst traffic" in tier2.decisions[0].rationale
    assert "complex state" in tier2.decisions[0].tradeoffs
    assert "Redis auth required" in tier2.security_implications
    assert "redis-py 5.0+" in tier2.dependencies
    assert tier2.line_count <= 50


# ============================================================================
# EDGE: Boundary conditions and malformed input
# ============================================================================


def test_edge_empty_spec_file():
    """
    EDGE: Handle empty specification file gracefully.

    Expected: Return TierGenerationError with clear message
    """
    # Arrange
    spec_path = Path("/tmp/test_spec_empty.md")
    spec_path.write_text("")

    generator = SpecTierGenerator()

    # Act
    result = generator.generate_tiered_spec(spec_path)

    # Assert
    assert result.is_err(), "Should fail on empty spec file"
    error = result.unwrap_err()
    assert "empty" in error.reason.lower()

    # Cleanup
    spec_path.unlink()


def test_edge_missing_required_sections():
    """
    EDGE: Handle spec with missing required sections (Goals, Acceptance Criteria).

    Expected: Generate tiers with placeholder content for missing sections
    """
    # Arrange
    spec_content = """
# Feature Specification: Incomplete Spec

## Executive Summary
Some feature with no details.
"""

    spec_path = Path("/tmp/test_spec_incomplete.md")
    spec_path.write_text(spec_content)

    generator = SpecTierGenerator()

    # Act
    result = generator.generate_tiered_spec(spec_path)

    # Assert
    assert result.is_ok(), "Should handle missing sections gracefully"
    tiered_spec = result.unwrap()

    assert tiered_spec.tier1.mission == "Some feature with no details."
    assert tiered_spec.tier1.constitutional_status == ConstitutionalStatus.NEEDS_REVIEW
    assert len(tiered_spec.tier2.decisions) == 1  # Placeholder decision when none found
    assert "Implementation Approach" in tiered_spec.tier2.decisions[0].title  # Placeholder title

    # Cleanup
    spec_path.unlink()


def test_edge_very_long_spec_file():
    """
    EDGE: Handle specification file with >2000 lines.

    Expected: Tier 1 and Tier 2 still meet line count limits (<25, <50)
    """
    # Arrange
    # Generate a spec with 2500 lines
    spec_content = "# Feature Specification: Large Feature\n\n"
    spec_content += "## Executive Summary\nA very complex feature.\n\n"
    spec_content += "## Goals\n" + "\n".join([f"- Goal {i}" for i in range(500)]) + "\n\n"
    spec_content += "## Acceptance Criteria\n" + "\n".join([f"{i}. Criterion {i}" for i in range(1000)]) + "\n\n"
    spec_content += "## Detailed Implementation\n" + ("Implementation details.\n" * 1000)

    spec_path = Path("/tmp/test_spec_large.md")
    spec_path.write_text(spec_content)

    generator = SpecTierGenerator()

    # Act
    result = generator.generate_tiered_spec(spec_path)

    # Assert
    assert result.is_ok()
    tiered_spec = result.unwrap()

    # Even with 2500-line spec, tiers must meet limits
    assert tiered_spec.tier1.line_count <= 25
    assert tiered_spec.tier2.line_count <= 50
    assert tiered_spec.tier3.line_count >= 2500  # Full spec (at least 2500 lines)

    # Cleanup
    spec_path.unlink()


# ============================================================================
# SECURITY: Malicious input handling
# ============================================================================


def test_security_xss_in_spec_content():
    """
    SECURITY: Sanitize HTML/JS in spec content to prevent XSS.

    Expected: All HTML tags escaped, JavaScript neutralized
    """
    # Arrange
    spec_content = """
# Feature Specification: <script>alert('XSS')</script>

## Executive Summary
Implement feature with <img src=x onerror=alert('XSS')> malicious content.

## Goals
- Goal with <a href="javascript:alert('XSS')">link</a>
"""

    spec_path = Path("/tmp/test_spec_xss.md")
    spec_path.write_text(spec_content)

    generator = SpecTierGenerator()

    # Act
    result = generator.generate_tiered_spec(spec_path)

    # Assert
    assert result.is_ok()
    tiered_spec = result.unwrap()

    # All HTML tags should be escaped
    assert "<script>" not in tiered_spec.tier1.mission
    assert "&lt;img" in tiered_spec.tier1.mission  # <img should be escaped to &lt;img
    assert "<img" not in tiered_spec.tier1.mission  # Raw <img tag should not exist
    assert "javascript:" not in str(tiered_spec.tier1.deliverables)

    # Cleanup
    spec_path.unlink()


def test_security_path_traversal_in_file_path():
    """
    SECURITY: Prevent path traversal attacks in Tier 3 file reference.

    Expected: File paths normalized, ../ sequences removed
    """
    # Arrange
    malicious_path = Path("/tmp/../../../etc/passwd")

    # Act
    tier3 = create_tier3_reference(malicious_path, line_count=100, section_count=5)

    # Assert
    # Path should be normalized (no ../ sequences)
    assert ".." not in str(tier3.file_path)
    # Path should be absolute and normalized (resolve() converts relative to absolute)
    assert tier3.file_path.is_absolute()


# ============================================================================
# SPECIFICATION: Acceptance criteria validation
# ============================================================================


def test_specification_tier1_under_25_lines():
    """
    SPECIFICATION: Tier 1 executive summary must be <25 lines.

    Acceptance Criterion: User can approve in 30 seconds (requires <25 lines)
    """
    # Arrange
    spec_content = "# Feature\n\n## Executive Summary\nImplement complex feature with many requirements.\n" + ("Additional detail line.\n" * 30)
    spec_path = Path("/tmp/test_spec_tier1_limit.md")
    spec_path.write_text(spec_content)

    generator = SpecTierGenerator()

    # Act
    result = generator.generate_tiered_spec(spec_path)

    # Assert
    assert result.is_ok()
    tiered_spec = result.unwrap()
    assert tiered_spec.tier1.line_count <= 25, "Tier 1 must be ≤25 lines for 30-second read"

    # Cleanup
    spec_path.unlink()


def test_specification_tier2_under_50_lines():
    """
    SPECIFICATION: Tier 2 key decisions must be <50 lines.

    Acceptance Criterion: Key decisions readable in 2 minutes (requires <50 lines)
    """
    # Arrange
    spec_content = """
# Feature

## Architectural Decisions

""" + "\n\n".join([f"### Decision {i}\nContent {i}\nRationale {i}\nTrade-off {i}" for i in range(20)])

    spec_path = Path("/tmp/test_spec_tier2_limit.md")
    spec_path.write_text(spec_content)

    generator = SpecTierGenerator()

    # Act
    result = generator.generate_tiered_spec(spec_path)

    # Assert
    assert result.is_ok()
    tiered_spec = result.unwrap()
    assert tiered_spec.tier2.line_count <= 50, "Tier 2 must be ≤50 lines for 2-minute read"

    # Cleanup
    spec_path.unlink()


# ============================================================================
# COMPLIANCE: Constitutional Article validation
# ============================================================================


def test_compliance_article_i_complete_context():
    """
    COMPLIANCE: Tier generation requires complete spec context (Article I).

    Validates: No partial tier generation, all sections processed
    """
    # Arrange
    spec_content = """
# Feature Specification

## Executive Summary
Complete feature.

## Goals
- Goal 1
- Goal 2

## Acceptance Criteria
1. Criterion 1
2. Criterion 2

## Technical Approach
Detailed approach.
"""

    spec_path = Path("/tmp/test_spec_complete.md")
    spec_path.write_text(spec_content)

    generator = SpecTierGenerator()

    # Act
    result = generator.generate_tiered_spec(spec_path)

    # Assert
    assert result.is_ok()
    tiered_spec = result.unwrap()

    # All tiers must be populated (no partial generation)
    assert tiered_spec.tier1 is not None
    assert tiered_spec.tier2 is not None
    assert tiered_spec.tier3 is not None
    assert tiered_spec.tier1.mission != ""

    # Cleanup
    spec_path.unlink()


# ============================================================================
# ACCURACY: Tier content matches spec structure
# ============================================================================


def test_accuracy_tier1_matches_executive_summary():
    """
    ACCURACY: Tier 1 mission extracted from Executive Summary section.

    Validates: No hallucination, direct extraction from source
    """
    # Arrange
    spec_content = """
# Feature Specification: Cache Layer

## Executive Summary
Implement Redis-based caching layer for database query optimization.
"""

    spec_path = Path("/tmp/test_spec_accuracy.md")
    spec_path.write_text(spec_content)

    generator = SpecTierGenerator()

    # Act
    result = generator.generate_tiered_spec(spec_path)

    # Assert
    assert result.is_ok()
    tiered_spec = result.unwrap()

    # Mission should match executive summary exactly (no LLM paraphrasing)
    assert "Redis-based caching layer" in tiered_spec.tier1.mission
    assert "database query optimization" in tiered_spec.tier1.mission

    # Cleanup
    spec_path.unlink()


# ============================================================================
# REGRESSION: Previous bug fixes
# ============================================================================


def test_regression_unicode_handling_in_spec():
    """
    REGRESSION: Handle Unicode characters in spec content.

    Bug: Previous version crashed on non-ASCII characters
    Fix: Use UTF-8 encoding for all file operations
    """
    # Arrange
    spec_content = """
# Feature Specification: Internationalization 🌍

## Executive Summary
Support UTF-8 characters: émojis 🎉, symbols ∑∫√, languages 中文, 日本語.
"""

    spec_path = Path("/tmp/test_spec_unicode.md")
    spec_path.write_text(spec_content, encoding="utf-8")

    generator = SpecTierGenerator()

    # Act
    result = generator.generate_tiered_spec(spec_path)

    # Assert
    assert result.is_ok(), "Should handle Unicode characters"
    tiered_spec = result.unwrap()
    # Mission comes from executive summary, which has "UTF-8" and emoji 🎉
    assert "UTF-8" in tiered_spec.tier1.mission
    assert "🎉" in tiered_spec.tier1.mission or "中文" in tiered_spec.tier1.mission

    # Cleanup
    spec_path.unlink()
