# Specification: VectorStore API Harmonization

**Spec ID**: `spec-002-vectorstore-harmonization`
**Status**: Draft
**Author**: ChiefArchitectAgent
**Created**: 2025-09-22
**Last Updated**: 2025-09-22
**Related Plan**: `plan-002-vectorstore-harmonization.md`

---

## Executive Summary

Unify the VectorStore API with the LearningAgent toolchain to eliminate interface mismatches and unblock the continuous learning pipeline.

---

## Goals

### Primary Goals
- [ ] Provide a stable `search(query, namespace, limit)` API on `VectorStore`
- [ ] Ensure statistics keys are backward compatible (`embedding_available` and `has_embeddings`)
- [ ] Namespacing support for learning objects to enable scoped queries

### Success Metrics
- All learning pipeline tools execute without API errors
- Tests referencing VectorStore stats pass without modification
- Future learnings retrievable via namespace-scoped search

---

## Non-Goals
- Changing embedding providers or persistence backends
- Rewriting LearningAgent tools beyond compatibility fixes

---

## User Personas & Journeys

- PlannerAgent: relies on spec-kit to plan harmonization work
- AgencyCodeAgent: implements minimal, compatible changes
- LearningAgent: stores and retrieves learnings reliably

---

## Acceptance Criteria

### Functional Requirements
- [ ] `VectorStore.search` returns ranked results with `relevance_score` and `search_type`
- [ ] `VectorStore.get_stats` includes `has_embeddings`
- [ ] Learning storage records include `namespace`

### Non-Functional Requirements
- [ ] No regression in existing `tests/test_swarm_memory.py`
- [ ] Zero external dependency changes

### Constitutional Compliance
- [ ] Article I: Complete context gathered via audit + learning review
- [ ] Article II: 100% tests pass post-change
- [ ] Article V: Changes follow this spec

---

## Dependencies & Constraints
- Depends on `learning_agent/tools/store_knowledge.py`
- Constrained to in-memory VectorStore for now

---

## Risk Assessment
- Medium: subtle test expectations on stat keys
- Low: search API is additive

---

## Integration Points
- PlannerAgent, AgencyCodeAgent, LearningAgent, MergerAgent

---

## Testing Strategy
- Run existing unit tests
- Add no new tests; rely on compatibility

---

## Implementation Phases

### Phase 1: API additions
- Implement `search`, extended stats, and record retention

### Phase 2: Learning tool alignment
- Add namespace into stored learning metadata and key

---

## Review & Approval
- Stakeholders: @am
- Technical Reviewers: PlannerAgent, MergerAgent

---

## Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-09-22 | ChiefArchitectAgent | Initial specification |
