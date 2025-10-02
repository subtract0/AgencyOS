# Specification: Documentation Consolidation System

**Spec ID**: `spec-014-documentation-consolidation-system`
**Status**: `Draft`
**Author**: AuditorAgent
**Created**: 2025-10-02
**Last Updated**: 2025-10-02
**Related Plan**: `plan-014-documentation-consolidation-system.md`

---

## Executive Summary

Consolidate Agency OS documentation from 3 competing master documents (CLAUDE.md, constitution.md, README.md) with 60% redundancy into a single canonical source of truth with automated maintenance, generation from code annotations, and CI-enforced freshness checks. This will improve documentation completeness from 78/100 to 85/100, reducing maintenance burden while increasing clarity and discoverability.

---

## Goals

### Primary Goals
- [ ] **Goal 1**: Eliminate 60% documentation redundancy by consolidating CLAUDE.md, constitution.md, and README.md into unified canonical reference
- [ ] **Goal 2**: Implement autodoc generation from Python docstrings and agent frontmatter annotations
- [ ] **Goal 3**: Add automated doc freshness checking with CI integration to prevent documentation drift
- [ ] **Goal 4**: Establish single source of truth (SSOT) pattern with clear documentation hierarchy
- [ ] **Goal 5**: Reduce documentation maintenance time by 40% through automation

### Success Metrics
- **Redundancy Reduction**: From 60% overlap to <15% acceptable cross-references
- **Documentation Coverage**: 100% of agents, tools, commands documented with auto-validation
- **Freshness Score**: 95%+ documents verified within 30 days via automated checks
- **Maintenance Time**: 40% reduction in manual documentation updates (measured over 3 months)
- **Discoverability**: <2 clicks to find any documentation from entry point
- **Build Integration**: Documentation validation in CI pipeline with zero failures

---

## Non-Goals

### Explicit Exclusions
- **Content Rewriting**: Not changing the substance of existing documentation, only consolidating structure
- **API Documentation**: Not generating comprehensive API docs (defer to future Sphinx/TypeDoc integration)
- **Versioned Documentation**: Not implementing version-specific docs (defer to future enhancement)
- **Internationalization**: English-only documentation for initial implementation

### Future Considerations
- **Multi-Version Docs**: Support for documenting multiple Agency OS versions
- **Interactive Tutorials**: Step-by-step guided workflows with code examples
- **Video Documentation**: Screen recordings of autonomous workflows
- **Community Contributions**: Public documentation contribution workflow

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: New Developer (@am starting fresh session)
- **Description**: Developer starting new session who needs quick context on Agency OS capabilities
- **Goals**: Understand system quickly, find relevant commands, avoid stale documentation
- **Pain Points**: Three docs compete for authority, unclear which is current, redundant reading
- **Technical Proficiency**: Expert in software architecture, expects professional documentation

#### Persona 2: ChiefArchitectAgent (Documentation Consumer)
- **Description**: Agent that needs to reference constitutional principles and ADRs during decision-making
- **Goals**: Quick access to canonical constitutional articles, current ADR index, no conflicting info
- **Pain Points**: Multiple sources provide different versions of same content, unclear precedence
- **Technical Proficiency**: Expert in constitutional governance, requires machine-readable references

#### Persona 3: LearningAgent (Documentation Producer)
- **Description**: Agent responsible for extracting and documenting patterns from sessions
- **Goals**: Update documentation systematically, maintain freshness, avoid duplication
- **Pain Points**: Unclear where to add learnings, manual updates error-prone, no validation
- **Technical Proficiency**: Expert in pattern extraction, requires structured documentation targets

### User Journeys

#### Journey 1: Session Initialization (Current - Painful)
```
1. User starts with: Need to prime session with latest Agency context
2. User reads: CLAUDE.md (404 lines) for quick reference
3. User encounters: References to constitution.md for details
4. User reads: constitution.md (365 lines) for constitutional framework
5. User notices: 60% content overlap with CLAUDE.md
6. User confused: Which document is authoritative? Which is fresher?
7. User wastes: 10-15 minutes reconciling contradictions
```

#### Journey 2: Session Initialization (Future - Streamlined)
```
1. User starts with: Need to prime session with latest Agency context
2. User executes: /prime cc (reads consolidated docs/AGENCY_REFERENCE.md)
3. System presents: Single canonical reference with all context
4. User confirms: "Last verified: 2025-10-02" with CI badge
5. User achieves: Complete context in 2-3 minutes with confidence
```

#### Journey 3: Agent Documentation Update (Current - Manual)
```
1. Agent creates: New tool or capability
2. Agent must update: tools/README.md (doesn't exist), CLAUDE.md section, agent .md file
3. Agent risks: Inconsistency across 3 locations
4. No validation: Documentation can drift immediately
5. Maintenance burden: Manual updates across multiple files
```

#### Journey 4: Agent Documentation Update (Future - Automated)
```
1. Agent creates: New tool with proper docstring annotations
2. System generates: Documentation from annotations via autodoc
3. CI validates: Documentation completeness and freshness on commit
4. Single update: Automatically propagates to canonical reference
5. Zero drift: Automated validation prevents staleness
```

---

## Acceptance Criteria

### Functional Requirements

#### Documentation Consolidation
- [ ] **AC-1.1**: Single canonical documentation file created at `docs/AGENCY_REFERENCE.md` (or similar canonical location)
- [ ] **AC-1.2**: All content from CLAUDE.md, constitution.md, README.md consolidated with deduplication
- [ ] **AC-1.3**: Clear documentation hierarchy: Entry Point → Reference → Deep Dives
- [ ] **AC-1.4**: Cross-references preserved with proper links (internal markdown references)
- [ ] **AC-1.5**: Historical documentation archived to `docs/archive/` with timestamps

#### Autodoc Generation
- [ ] **AC-2.1**: Python tool docstrings automatically extracted to documentation
- [ ] **AC-2.2**: Agent frontmatter (YAML metadata) automatically extracted to agent reference
- [ ] **AC-2.3**: Command descriptions automatically extracted to command reference
- [ ] **AC-2.4**: Autodoc generation runs via `python scripts/generate_docs.py`
- [ ] **AC-2.5**: Generated documentation sections marked with "AUTO-GENERATED - DO NOT EDIT MANUALLY"

#### Freshness Validation
- [ ] **AC-3.1**: CI pipeline includes documentation validation step
- [ ] **AC-3.2**: Validation checks: all agents documented, all tools documented, all commands documented
- [ ] **AC-3.3**: Freshness metadata: "Last verified" timestamps in documentation headers
- [ ] **AC-3.4**: Automated freshness check runs weekly via GitHub Actions
- [ ] **AC-3.5**: Stale documentation (>90 days) triggers warning in CI

#### Documentation Structure
- [ ] **AC-4.1**: Entry point README.md provides overview + links to canonical reference
- [ ] **AC-4.2**: Canonical reference includes: Quick Start, Agent Reference, Tool Reference, Command Reference, Constitutional Framework, ADR Index
- [ ] **AC-4.3**: Deep dive docs remain in respective directories (.claude/agents/, docs/adr/)
- [ ] **AC-4.4**: Navigation is hierarchical: README → Reference → Deep Dives
- [ ] **AC-4.5**: Search functionality via grep/ripgrep patterns documented

### Non-Functional Requirements

#### Performance
- [ ] **AC-P.1**: Documentation generation completes in <30 seconds
- [ ] **AC-P.2**: CI documentation validation adds <1 minute to pipeline
- [ ] **AC-P.3**: Documentation readable with <2 clicks from any entry point

#### Quality
- [ ] **AC-Q.1**: Zero broken internal links in generated documentation
- [ ] **AC-Q.2**: 100% of public tools/agents/commands documented with validation
- [ ] **AC-Q.3**: Documentation passes markdown linting (markdownlint-cli)

#### Maintainability
- [ ] **AC-M.1**: Autodoc generation script includes comprehensive error handling
- [ ] **AC-M.2**: Documentation generation failures provide actionable error messages
- [ ] **AC-M.3**: Manual documentation sections clearly separated from auto-generated

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [ ] **AC-CI.1**: Consolidated documentation provides complete Agency context in single source
- [ ] **AC-CI.2**: No documentation action proceeds without validating current state
- [ ] **AC-CI.3**: Zero broken windows - stale docs detected and fixed immediately

#### Article II: 100% Verification and Stability
- [ ] **AC-CII.1**: 100% test coverage for documentation generation script
- [ ] **AC-CII.2**: All documentation changes validated via CI before merge
- [ ] **AC-CII.3**: No documentation drift tolerated (automated validation)

#### Article III: Automated Merge Enforcement
- [ ] **AC-CIII.1**: CI blocks merge if documentation validation fails
- [ ] **AC-CIII.2**: No manual override for documentation quality gates

#### Article IV: Continuous Learning and Improvement
- [ ] **AC-CIV.1**: Documentation structure enables LearningAgent pattern extraction
- [ ] **AC-CIV.2**: Usage patterns inform documentation improvements (track which sections accessed most)

#### Article V: Spec-Driven Development
- [ ] **AC-CV.1**: This specification drives all documentation consolidation implementation
- [ ] **AC-CV.2**: Documentation structure follows spec-kit patterns

---

## Dependencies & Constraints

### System Dependencies
- **Python 3.12+**: For autodoc generation script
- **Markdown Parser**: For extracting sections and validating structure
- **Git**: For documentation versioning and CI integration
- **GitHub Actions**: For automated freshness checks and CI validation

### External Dependencies
- **markdownlint-cli**: For markdown quality validation
- **PyYAML**: For parsing agent frontmatter metadata
- **Jinja2**: For documentation template rendering (optional)

### Technical Constraints
- **Markdown Format**: All documentation must remain in markdown for git-friendliness
- **Backward Compatibility**: Existing links to CLAUDE.md, constitution.md must redirect gracefully
- **File Size**: Canonical reference should remain <1000 lines for readability
- **Generation Speed**: Autodoc generation must complete in <30 seconds

### Business Constraints
- **No Content Changes**: Consolidation doesn't change documentation substance
- **Zero Downtime**: Documentation remains accessible during migration
- **Incremental Migration**: Can implement in phases without breaking existing references

---

## Risk Assessment

### High Risk Items
- **Risk 1**: Breaking existing references to CLAUDE.md/constitution.md across codebase - *Mitigation*: Implement redirects/symlinks, grep search for all references, update systematically
- **Risk 2**: Autodoc generation introduces errors or inconsistencies - *Mitigation*: Comprehensive testing, manual review of generated docs, gradual rollout

### Medium Risk Items
- **Risk 3**: Documentation becomes too large/unwieldy in single file - *Mitigation*: Keep canonical reference as index with links to deep dives
- **Risk 4**: CI validation slows down development workflow - *Mitigation*: Optimize validation script, run heavy checks only on main branch

### Constitutional Risks
- **Constitutional Risk 1**: Article I violation if incomplete context provided in consolidated doc - *Mitigation*: Comprehensive content audit before consolidation
- **Constitutional Risk 2**: Article II violation if documentation validation is incomplete - *Mitigation*: 100% test coverage for validation script

---

## Integration Points

### Agent Integration
- **PlannerAgent**: Reads canonical reference during prime operations
- **ChiefArchitectAgent**: References ADR index and constitutional articles from canonical docs
- **LearningAgent**: Updates pattern library sections via structured documentation targets
- **QualityEnforcerAgent**: Validates documentation completeness as part of quality checks

### System Integration
- **CI/CD Pipeline**: Documentation validation step blocks merge on failures
- **Prime Commands**: Updated to reference canonical documentation location
- **.claude/ Directory**: Remains authoritative for deep-dive agent/command docs
- **Git Hooks**: Optional pre-commit hook validates documentation freshness

### External Integration
- **GitHub Actions**: Weekly freshness validation workflow
- **Markdown Tools**: Linting and link validation via markdownlint-cli
- **Search Tools**: grep/ripgrep patterns for documentation navigation

---

## Testing Strategy

### Test Categories
- **Unit Tests**: Documentation generation script functions, markdown parsing, metadata extraction
- **Integration Tests**: End-to-end documentation generation from source annotations
- **Validation Tests**: CI pipeline documentation checks (coverage, freshness, broken links)
- **Constitutional Compliance Tests**: Verify all 5 articles supported by documentation structure

### Test Data Requirements
- **Sample Annotations**: Example Python docstrings, agent frontmatter, command metadata
- **Validation Fixtures**: Known-good documentation for comparison
- **Edge Cases**: Missing docstrings, malformed YAML, circular references

### Test Environment Requirements
- **Local Development**: Documentation generation runs locally via `python scripts/generate_docs.py`
- **CI Environment**: GitHub Actions workflow validates documentation on every PR
- **Freshness Checks**: Weekly scheduled workflow validates doc freshness

---

## Implementation Phases

### Phase 1: Content Audit & Consolidation (Week 1)
- **Scope**: Analyze CLAUDE.md, constitution.md, README.md for redundancy and gaps
- **Deliverables**:
  - Content audit report identifying 60% redundancy
  - Consolidated canonical documentation at docs/AGENCY_REFERENCE.md
  - Archive of historical documents
- **Success Criteria**: Single canonical reference contains all critical content with <15% redundancy

### Phase 2: Autodoc Generation Infrastructure (Week 2)
- **Scope**: Build scripts/generate_docs.py for automated documentation generation
- **Deliverables**:
  - Python script extracting docstrings from tools/*.py
  - YAML frontmatter extraction from .claude/agents/*.md and .claude/commands/*.md
  - Template system for documentation sections
- **Success Criteria**: Autodoc script generates complete tool/agent/command reference from source

### Phase 3: CI Integration & Validation (Week 3)
- **Scope**: Add documentation validation to GitHub Actions CI pipeline
- **Deliverables**:
  - .github/workflows/docs-validation.yml workflow
  - Validation checks: coverage, freshness, broken links
  - Weekly freshness check scheduled workflow
- **Success Criteria**: CI blocks merge if documentation validation fails

### Phase 4: Migration & Deprecation (Week 4)
- **Scope**: Update all references to point to canonical documentation
- **Deliverables**:
  - Updated prime commands to reference new structure
  - Deprecation notices in CLAUDE.md, constitution.md with redirects
  - Updated agent instructions to use canonical reference
- **Success Criteria**: Zero broken references, all systems reference canonical docs

---

## Review & Approval

### Stakeholders
- **Primary Stakeholder**: @am (Project Owner)
- **Secondary Stakeholders**: All Agency agents (documentation consumers)
- **Technical Reviewers**: AuditorAgent (quality validation), LearningAgent (pattern compliance)

### Review Criteria
- [ ] **Completeness**: All critical content consolidated without loss
- [ ] **Clarity**: Documentation hierarchy clear and navigable
- [ ] **Feasibility**: Autodoc generation technically viable within constraints
- [ ] **Constitutional Compliance**: All 5 articles supported by implementation
- [ ] **Quality Standards**: Meets Agency's documentation and testing requirements

### Approval Status
- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending agent validation
- [ ] **Constitutional Compliance**: Pending article verification
- [ ] **Final Approval**: Pending all above approvals

---

## Appendices

### Appendix A: Glossary
- **SSOT (Single Source of Truth)**: Canonical documentation source that all references defer to
- **Autodoc**: Automated documentation generation from code annotations
- **Freshness Check**: Automated validation that documentation is current (not stale)
- **CI Validation**: Continuous integration checks that enforce documentation quality

### Appendix B: References
- **ADR-001**: Complete Context Before Action (drives SSOT requirement)
- **ADR-002**: 100% Verification and Stability (drives CI validation requirement)
- **Article IV**: Continuous Learning (drives learning pattern integration)
- **Spec-001**: Spec-Driven Development (template and methodology source)

### Appendix C: Related Documents
- **CLAUDE.md**: Current master document (to be consolidated)
- **constitution.md**: Constitutional framework (to be integrated)
- **README.md**: Entry point documentation (to be simplified)
- **.claude/agents/*.md**: Agent-specific documentation (remains as deep dives)

### Appendix D: Documentation Redundancy Analysis
**Current State:**
- CLAUDE.md: 404 lines
- constitution.md: 365 lines
- README.md: 475 lines
- **Total**: 1,244 lines
- **Unique Content Estimate**: ~500 lines (60% redundancy)

**Target State:**
- docs/AGENCY_REFERENCE.md: ~600 lines (canonical)
- README.md: ~100 lines (entry point)
- **Total**: 700 lines (43% reduction in total lines, 85% reduction in redundancy)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-02 | AuditorAgent | Initial specification for documentation consolidation system |

---

*"A specification is a contract between intention and implementation."*
