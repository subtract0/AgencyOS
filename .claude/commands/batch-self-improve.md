# **Batch Self-Improvement Command**

**Command**: `/batch-self-improve`

**Purpose**: Orchestrate parallel self-improvement analysis for multiple agents simultaneously.

**Usage**: `/batch-self-improve [agents] [focus]`

---

## **Parameters**

- `agents`: Comma-separated list or "all" (e.g., "planner,merger,chief_architect" or "all")
- `focus`: Improvement focus area (optional)
  - `all` - Comprehensive analysis (default)
  - `tools` - Agent tool integration only
  - `constitutional` - Constitutional compliance gaps
  - `metrics` - Performance metrics addition
  - `examples` - Concrete examples and patterns

---

## **What This Command Does**

1. **Launches Parallel Analysis**: Spawns multiple Task agents simultaneously (not sequential)
2. **Generates Proposals**: Each agent analyzes itself and creates improvement proposal
3. **Consolidates Results**: Collects all proposals into review queue
4. **Provides Summary**: Aggregate impact analysis + prioritized recommendations

---

## **Example Usage**

### **Example 1: Analyze All Non-Updated Agents**

```bash
/batch-self-improve all tools
```

**Output**:
```
🚀 Launching parallel analysis for 8 agents...

[in parallel]
→ Planner analyzing tool integration gaps...
→ Chief_Architect analyzing tool integration gaps...
→ Merger analyzing tool integration gaps...
→ Learning_Agent analyzing tool integration gaps...
→ Spec_Generator analyzing tool integration gaps...
→ E2E_Workflow analyzing tool integration gaps...
→ Toolsmith analyzing tool integration gaps...
→ Work_Completion analyzing tool integration gaps...

✅ 8 proposals generated in 45 minutes (vs. 6 hours sequential)

📊 Aggregate Impact:
- Tool integration: 25% → 100% (+75%)
- Average score: 82 → 91 (+9 points)
- Total implementation time: 42 hours

📋 Proposals saved to .claude/proposals/
🔍 Next: Review with /architect-review-proposals
```

### **Example 2: Focus on Constitutional Gaps**

```bash
/batch-self-improve "chief_architect,planner" constitutional
```

**Output**:
```
🚀 Launching parallel analysis for 2 agents...

→ Chief_Architect: Article III COMPLETELY MISSING (CRITICAL)
→ Planner: Article III passive (needs active enforcement)

✅ 2 proposals generated in 15 minutes

📊 Aggregate Impact:
- Constitutional compliance: 80% → 100% (+20%)
- Chief_Architect: 72 → 92 (+20 points)
- Planner: 80 → 93 (+13 points)

🔴 CRITICAL: Chief_Architect has constitutional violation
📋 Proposals saved to .claude/proposals/
```

### **Example 3: Add Metrics to Top Performers**

```bash
/batch-self-improve "auditor,quality_enforcer,code_agent,test_generator" metrics
```

**Output**:
```
🚀 Launching parallel analysis for 4 agents (A-grade)...

→ All agents scored 95-100, analyzing metric gaps only...

✅ 4 proposals generated in 20 minutes

📊 Aggregate Impact:
- Performance tracking: 0% → 100%
- All agents get dashboards + telemetry
- No score change (already excellent)
- Implementation: 8 hours total

📋 Proposals: Enhancement tier (not critical)
```

---

## **Implementation Pattern**

**This command uses parallel Task agents:**

```python
def batch_self_improve(agents: list[str], focus: str = "all"):
    """
    Orchestrate parallel self-improvement analysis.

    Args:
        agents: List of agent names or ["all"]
        focus: Improvement focus area

    Returns:
        Consolidated report with all proposals
    """
    # 1. Determine agent list
    if agents == ["all"]:
        agent_list = get_all_non_updated_agents()
    else:
        agent_list = agents

    # 2. Launch parallel Task agents
    tasks = []
    for agent in agent_list:
        task = Task(
            subagent_type="general-purpose",
            description=f"{agent} self-improvement ({focus})",
            prompt=f"""
            Analyze {agent} agent definition for {focus} improvements.

            Files:
            - Definition: .claude/agents/{agent}.md
            - Audit: logs/audits/agent_definitions_comprehensive_audit_20251007.md
            - Gold Standard: .claude/agents/quality_enforcer.md

            Output:
            - Create proposal: .claude/proposals/{agent}_{focus}_proposal_20251007.md
            - Focus on {focus} improvements only
            - Quantify expected impact
            - Be CONCISE (10-15KB max)
            """
        )
        tasks.append(task)

    # 3. Execute all tasks in PARALLEL
    results = execute_parallel(tasks)

    # 4. Consolidate results
    aggregate_impact = calculate_aggregate_impact(results)
    prioritized_recommendations = prioritize_by_impact(results)

    # 5. Update review queue
    for result in results:
        add_to_review_queue(result.proposal_file, result.metadata)

    # 6. Return summary
    return {
        "proposals_generated": len(results),
        "time_saved": calculate_time_saved(results),
        "aggregate_impact": aggregate_impact,
        "recommendations": prioritized_recommendations,
        "review_queue_path": ".claude/proposals/review_queue.txt"
    }
```

---

## **Output Format**

**Proposal File Naming**:
- `{agent}_{focus}_proposal_{date}.md`
- Example: `planner_tools_proposal_20251007.md`

**Review Queue Entry**:
```
📋 BATCH: {focus} improvements for {N} agents
  Status: Pending Architect Review
  Agents: {agent1}, {agent2}, ...
  Expected Impact: {summary}
  Total Implementation: {hours} hours
  Submitted: {date}
```

---

## **Efficiency Gains**

### **Time Comparison**:

| Agents | Sequential | Parallel (this command) | Gain |
|--------|-----------|-------------------------|------|
| 4 agents | 4 hours | 1 hour | **4x faster** |
| 8 agents | 8 hours | 1.5 hours | **5.3x faster** |
| 12 agents | 12 hours | 2 hours | **6x faster** |

### **Resource Usage**:

- **API Tokens**: Same (parallel doesn't use more tokens)
- **Context Windows**: Isolated per agent (no context bloat)
- **Human Time**: Review queue batched (easier to approve/reject)

---

## **Integration with Architect Review**

After running batch self-improvement:

```bash
# Review all proposals
/architect-review-proposals batch approve-all-critical

# Or review individually
/architect-review-proposals planner_tools_proposal_20251007 approve
/architect-review-proposals chief_architect_constitutional_proposal_20251007 approve
```

---

## **When to Use This Command**

**Use batch-self-improve when:**
- ✅ Multiple agents need same improvement (e.g., all missing tools)
- ✅ After major audit reveals systemic gaps
- ✅ Quarterly/monthly improvement cycles
- ✅ Adding new capability to all agents (e.g., new tool released)

**Don't use when:**
- ❌ Only 1-2 agents need improvement (use `/agent-self-improve` directly)
- ❌ Improvements are highly specific per agent
- ❌ Context window near limit (batch uses more total context)

---

## **Success Metrics**

Track batch improvement cycles over time:

```python
{
  "cycle_date": "2025-10-07",
  "agents_analyzed": 4,
  "proposals_generated": 4,
  "proposals_approved": 3,
  "proposals_implemented": 3,
  "avg_score_before": 80.25,
  "avg_score_after": 93.75,
  "improvement": "+13.5 points",
  "time_saved_hours": 6,  # vs sequential
  "implementation_hours": 34.5
}
```

---

## **Command Lifecycle**

1. **User invokes**: `/batch-self-improve all tools`
2. **Command parses**: Determines 8 agents, focus="tools"
3. **Parallel launch**: 8 Task agents spawn simultaneously
4. **Agents analyze**: Each reads own definition + audit + gold standard
5. **Proposals generated**: 8 files created in `.claude/proposals/`
6. **Queue updated**: 8 entries added to `review_queue.txt`
7. **Summary returned**: Aggregate impact + recommendations
8. **User reviews**: Uses `/architect-review-proposals batch`
9. **Implementation**: Approved proposals applied to agents
10. **Re-audit**: Verify expected improvements achieved

---

**Command Status**: Production-Ready
**Version**: 1.0
**Last Updated**: 2025-10-07
**Expected Usage**: Monthly improvement cycles
