# Technical Plan: VectorStore API Harmonization

**Plan ID**: `plan-002-vectorstore-harmonization`
**Spec Reference**: `spec-002-vectorstore-harmonization.md`
**Status**: In Progress
**Author**: PlannerAgent (delegated by ChiefArchitectAgent)
**Created**: 2025-09-22
**Last Updated**: 2025-09-22
**Implementation Start**: 2025-09-22
**Target Completion**: 2025-09-22

---

## Executive Summary
Add a minimal `search` API and backward-compatible stats to `VectorStore`; ensure LearningAgent stores namespaces. No behavioral change to existing features.

---

## Architecture Overview

### High-Level Design
- Extend `VectorStore` with `_memory_records` for full record retention
- Implement `search(query, namespace, limit)` using `hybrid_search`
- Extend `get_stats` with `has_embeddings`
- Update `StoreKnowledge` to namespace keys and metadata

---

## Agent Assignments

### Primary Agent: AgencyCodeAgent
- Tasks:
  - Implement VectorStore changes
  - Adjust StoreKnowledge
  - Run tests
- Tools Required: Edit, MultiEdit, Bash, TodoWrite

### Supporting Agent: MergerAgent
- Tasks: Verify green tests before approval

---

## Tool Requirements
- Use existing grep/glob/edit tools only

---

## Contracts & Interfaces
- New: `VectorStore.search(query, namespace=None, limit=10) -> List[dict]`
- Stats: `get_stats()` contains both `embedding_available` and `has_embeddings`

---

## Implementation Strategy
- Phase 1: Code changes
- Phase 2: Test run and verification

---

## Quality Assurance Strategy
- Run `pytest` suite

---

## Risk Mitigation
- Changes are additive; preserve old behavior

---

## Rollback Strategy
- Revert VectorStore and StoreKnowledge edits if tests regress

---

## Review & Approval
- Technical Lead Approval: pending

---

