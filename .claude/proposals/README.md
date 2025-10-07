# Agent Self-Improvement Proposals

This directory contains improvement proposals submitted by agents for their own definitions.

## Structure

```
.claude/proposals/
├── pending/           # Awaiting Architect review
├── approved/          # Approved by Architect, ready for implementation
├── rejected/          # Rejected with rationale
├── review_queue.txt   # Queue of proposals needing review
└── review_decisions.log  # History of review decisions
```

## Workflow

1. **Agent Submission**: Agent uses `/agent-self-improve` to create proposal
2. **Proposal Saved**: File created in `pending/`
3. **Review Queue**: Entry added to `review_queue.txt`
4. **Architect Review**: Chief Architect or Alex reviews proposal
5. **Decision**: Moved to `approved/` or `rejected/` with rationale
6. **Implementation**: Approved proposals are implemented
7. **Verification**: Agent re-audits to measure improvement

## Proposal Format

Each proposal file follows this naming convention:
```
[agent_name]_improvement_proposal_[YYYYMMDD].md
```

Example: `code_agent_improvement_proposal_20251007.md`

## Review Criteria

Architect evaluates proposals based on:

1. **Constitutional Alignment**: Does it support Articles I-V?
2. **Safety**: Does it maintain or improve safety protocols?
3. **Value**: Does it deliver measurable improvement?
4. **Feasibility**: Can it be implemented with available resources?
5. **Strategic Fit**: Does it align with Agency's mission?

## Metrics Tracked

- Proposals submitted per agent
- Approval rate (target: >80%)
- Implementation rate (target: 100% of approved)
- Average audit score improvement (target: +5-10 points)
- Time from submission to implementation (target: <1 week)

---

**Created**: 2025-10-07
**Purpose**: Enable agents to co-design their own evolution
