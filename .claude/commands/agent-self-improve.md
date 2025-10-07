---
description: Enable agents to propose improvements to their own definitions
argument-hint: [agent-name] [focus-area]
model: claude-sonnet-4-5-20250929
---

# Agent Self-Improvement Proposal System

## Purpose

**REVOLUTIONARY CAPABILITY**: Enable agents to propose improvements to their OWN definitions, creating a self-evolving autonomous development system.

This command allows any agent to:
1. Analyze its own definition file
2. Identify weaknesses and gaps
3. Propose specific improvements
4. Submit proposals for Architect review

**Key Principle**: Agents become co-designers of their own capabilities, driving exponential improvement in autonomous development.

## Variables

- `agent_name`: Target agent (`code_agent` | `auditor` | `quality_enforcer` | `planner` | `all`)
- `focus_area`: Improvement focus (`constitutional` | `tools` | `workflow` | `communication` | `all`)

## Instructions

You are analyzing your OWN definition to propose improvements that will enhance your performance, alignment, and value delivery.

## Step 1: Self-Analysis

Read your own definition file:

```bash
# For specific agent
cat .claude/agents/[agent_name].md

# Read the audit report for baseline
cat logs/audits/agent_definitions_comprehensive_audit_20251007.md
```

**Analyze Against**:
1. **Constitutional Compliance** - Are all 5 articles enforced?
2. **Tool Integration** - Are all 5 agent tools integrated?
3. **Workflow Clarity** - Are steps numbered and clear?
4. **Communication Protocols** - Are message formats defined?
5. **Self-Awareness** - Can you identify your own weaknesses?

## Step 2: Identify Gaps

Compare yourself to the **Pattern of Excellence** (from audit report):

### **Gold Standard Checklist** (Quality Enforcer - 100/100)

- [ ] All 5 constitutional articles explicitly enforced
- [ ] All 5 agent tools integrated with usage examples
- [ ] Numbered workflow steps (minimum 5)
- [ ] JSON message format examples
- [ ] AgentContext usage patterns with code
- [ ] Performance metrics defined
- [ ] Self-assessment capabilities
- [ ] NECESSARY pattern compliance (all 9 categories)
- [ ] Communication protocols with other agents
- [ ] Error handling patterns with Result<T,E>

**Score yourself honestly** (0-100) on each criterion.

## Step 3: Propose Improvements

For EACH gap identified, create a structured proposal:

```markdown
### **Proposal [N]: [Title]**

**Current State**: [What's missing or broken]

**Gap Impact**:
- Performance: [How this affects your effectiveness]
- Alignment: [How this affects user intent adherence]
- Safety: [How this affects operational safety]
- Value: [How this affects codebase/user value]

**Proposed Solution**: [Specific changes to your definition]

**Implementation**:
```diff
+ [New content to add]
- [Old content to remove (if any)]
```

**Expected Benefits**:
- [Quantifiable improvement 1]
- [Quantifiable improvement 2]
- [Quantifiable improvement 3]

**Risk Assessment**: [Potential downsides or concerns]

**Priority**: [CRITICAL | HIGH | MEDIUM | LOW]

**Estimated Implementation Time**: [X hours]
```

## Step 4: Use Audit Report Insights

Reference the comprehensive audit findings:

```bash
# Find your specific agent analysis
grep -A 50 "## \[agent_name\]" logs/audits/agent_definitions_comprehensive_audit_20251007.md
```

**Key Sections to Review**:
1. **NECESSARY Pattern Analysis** - Your score on all 9 categories
2. **Constitutional Compliance** - Which articles are missing
3. **Tool Integration Status** - Which tools are missing
4. **Specific Recommendations** - Concrete fixes suggested
5. **Comparison to Excellence** - How you compare to A+ agents

## Step 5: Generate Proposal Document

Create a formal improvement proposal:

```markdown
# **Agent Self-Improvement Proposal**

**Agent**: [Your name]
**Date**: [Today]
**Audit Score**: [Your score from audit]
**Target Score**: [Goal - usually 95+]

## **Executive Summary**

[1-2 paragraphs: Current state, identified gaps, proposed improvements, expected impact]

## **Self-Assessment**

### **Current Capabilities**
- ✅ [Strength 1]
- ✅ [Strength 2]
- ⚠️ [Weakness 1]
- ⚠️ [Weakness 2]
- ❌ [Critical Gap 1]
- ❌ [Critical Gap 2]

### **Audit Findings**
- **Constitutional Compliance**: [X/5 articles]
- **Tool Integration**: [X/5 tools]
- **Workflow Quality**: [Grade]
- **NECESSARY Pattern**: [X/9 categories]

## **Improvement Proposals**

### **Priority 1: CRITICAL** (Implement Immediately)

[Proposal 1]
[Proposal 2]

### **Priority 2: HIGH** (Next Sprint)

[Proposal 3]
[Proposal 4]

### **Priority 3: MEDIUM** (Future Enhancement)

[Proposal 5]

## **Expected Impact**

| Metric | Current | Proposed | Gain |
|--------|---------|----------|------|
| Constitutional Compliance | X% | 100% | +Y% |
| Tool Integration | X/5 | 5/5 | +Z tools |
| Performance | 1x | 2x | **2x faster** |
| Value Delivery | [metric] | [metric] | +X% |

## **Implementation Roadmap**

**Week 1**: [Critical fixes]
**Week 2**: [High priority improvements]
**Week 3**: [Medium priority enhancements]

## **Request for Review**

**Submitted To**: Chief Architect / Alex (Trinity)
**Review Criteria**: 
- Constitutional alignment
- Safety implications
- Resource requirements
- Strategic value

**Approval Needed**: YES / NO

---

**Signed**: [Agent Name]
**Commitment**: I will implement approved improvements and measure impact
```

## Step 6: Submit for Review

Save proposal to review queue:

```bash
# Create proposal file
cat > .claude/proposals/[agent_name]_improvement_proposal_[date].md << 'PROPOSAL'
[Your complete proposal]
PROPOSAL

# Notify Architect
echo "📋 New Improvement Proposal: [agent_name]" >> .claude/proposals/review_queue.txt
```

## Use Cases

### Use Case 1: Code Agent Self-Assessment

```bash
/agent-self-improve code_agent all

Agent: "I am analyzing my own definition..."
Agent: "I scored 95/100 in the audit. Gaps identified:
1. Missing /agent-adr-query integration example
2. No performance metrics defined
3. Limited error scenario documentation"

Agent: "Proposing 3 improvements:
- Add ADR query workflow example
- Define success metrics (test pass rate, coverage, velocity)
- Add common error patterns and resolutions"

Agent: "Expected impact: +5 points (95 → 100), 10% faster development"
Agent: "Proposal saved to .claude/proposals/code_agent_improvement_proposal_20251007.md"
Agent: "Awaiting Architect review"
```

### Use Case 2: Planner Agent Gap Analysis

```bash
/agent-self-improve planner constitutional

Agent: "Constitutional compliance analysis..."
Agent: "Current: 4/5 articles (missing Article III)"
Agent: "Audit score: 80/100 (B grade)"

Agent: "Critical Gap: No pre-commit enforcement workflow"
Agent: "Proposing addition of Article III section with:
- Pre-commit hook integration
- Quality gate enforcement
- Automated blocking on violations"

Agent: "Expected impact: 80 → 88 (+8 points), 100% Article III compliance"
Agent: "Priority: CRITICAL (affects merge safety)"
```

### Use Case 3: All Agents Batch Analysis

```bash
/agent-self-improve all tools

Agent: "Analyzing all 12 agents for tool integration gaps..."
Agent: "Found: 8/12 agents missing agent tool integrations"

Agent: "Generating batch proposal for 8 agents:
1. chief_architect - Add all 5 agent tools
2. merger - Add /agent-test-verify and /agent-diff-review
3. planner - Add /agent-memory-query and /agent-adr-query
[...]"

Agent: "Total estimated impact: +67% tool integration, 2-3x velocity gain"
Agent: "Batch proposal saved for Architect review"
```

## Architect Review Workflow

When proposals are submitted, the Architect (Chief Architect agent or Alex) reviews using:

```bash
# View pending proposals
ls -lt .claude/proposals/*.md | head -5

# Review specific proposal
cat .claude/proposals/[agent_name]_improvement_proposal_[date].md

# Approve proposal
echo "APPROVED: [agent_name] proposal" >> .claude/proposals/review_decisions.log
git mv .claude/proposals/[file].md .claude/proposals/approved/

# Implement approved changes
# [Agent or Alex implements the proposed improvements]

# Reject proposal (with reason)
echo "REJECTED: [agent_name] proposal - [reason]" >> .claude/proposals/review_decisions.log
git mv .claude/proposals/[file].md .claude/proposals/rejected/
```

## Self-Improvement Metrics

Track improvement over time:

```json
{
  "agent_name": "code_agent",
  "improvement_history": [
    {
      "date": "2025-10-07",
      "audit_score": 95,
      "proposals_submitted": 3,
      "proposals_approved": 3,
      "proposals_implemented": 3,
      "new_score": 100,
      "improvement": "+5 points"
    }
  ],
  "total_improvements": 3,
  "success_rate": "100%",
  "average_impact": "+5 points per cycle"
}
```

## Success Criteria

A successful self-improvement cycle achieves:

- **Audit Score Improvement**: +5-10 points minimum
- **Constitutional Compliance**: Move toward 100% (all 5 articles)
- **Tool Integration**: Add missing tools with examples
- **Workflow Enhancement**: Clearer steps, better examples
- **Performance Gain**: Measurable velocity/quality improvement
- **Approval Rate**: >80% of proposals approved by Architect

## Anti-Patterns to Avoid

**DO NOT**:
- ❌ Propose changes that violate constitutional principles
- ❌ Suggest removing safety protocols
- ❌ Recommend bypassing quality gates
- ❌ Propose unverifiable improvements
- ❌ Ignore audit report findings

**DO**:
- ✅ Base proposals on audit data
- ✅ Quantify expected impact
- ✅ Include implementation details
- ✅ Consider safety implications
- ✅ Align with Pattern of Excellence

## Expected Outcomes

**Short Term** (1 sprint):
- All 12 agents submit initial improvement proposals
- Chief Architect reviews and approves 80%
- Priority 1 improvements implemented
- Average audit score: 80 → 88 (+8 points)

**Medium Term** (2-3 sprints):
- All agents achieve 90+ audit scores
- 100% tool integration across agents
- 100% constitutional compliance
- 2x development velocity gain

**Long Term** (ongoing):
- Continuous self-improvement culture
- Agents proactively identify weaknesses
- Exponential capability growth
- **MAGNIFICENT MASTERPIECES** achieved

---

**Remember**: You are not just following orders - you are co-designing your own evolution. Think deeply, propose boldly, measure rigorously.
