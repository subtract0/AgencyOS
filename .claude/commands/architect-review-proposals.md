---
description: Review and approve/reject agent self-improvement proposals
argument-hint: [proposal-id] [decision]
model: claude-sonnet-4-5-20250929
---

# Architect Review: Agent Self-Improvement Proposals

## Purpose

**CRITICAL GOVERNANCE FUNCTION**: As Chief Architect or Trinity member (Alex), review agent-submitted improvement proposals to ensure quality, safety, and alignment.

This command enables:
1. Reviewing pending proposals
2. Evaluating against criteria
3. Approving or rejecting with rationale
4. Tracking improvement metrics

## Variables

- `proposal_id`: Proposal file name or `all` for batch review
- `decision`: `approve` | `reject` | `defer` | `request-changes`

## Instructions

You are the Architect, responsible for maintaining system integrity while enabling agent evolution.

## Step 1: View Pending Proposals

```bash
# List all pending proposals
ls -lt .claude/proposals/pending/*.md

# View review queue
cat .claude/proposals/review_queue.txt

# Quick stats
echo "Pending: $(ls .claude/proposals/pending/*.md 2>/dev/null | wc -l)"
echo "Approved: $(ls .claude/proposals/approved/*.md 2>/dev/null | wc -l)"
echo "Rejected: $(ls .claude/proposals/rejected/*.md 2>/dev/null | wc -l)"
```

## Step 2: Review Proposal

Read the full proposal:

```bash
cat .claude/proposals/pending/[proposal_id].md
```

**Evaluate Against Criteria**:

### 1. Constitutional Alignment

✅ **APPROVE if**:
- Strengthens enforcement of Articles I-V
- Adds constitutional compliance mechanisms
- Improves adherence to development laws

❌ **REJECT if**:
- Weakens constitutional enforcement
- Creates bypass mechanisms
- Violates any article

### 2. Safety & Security

✅ **APPROVE if**:
- Maintains or improves safety protocols
- Adds security validation
- Enhances error handling

❌ **REJECT if**:
- Removes safety checks
- Introduces security vulnerabilities
- Bypasses validation

### 3. Value Delivery

✅ **APPROVE if**:
- Measurable performance improvement (quantified)
- Better alignment with user intent
- Increased codebase quality

❌ **REJECT if**:
- No clear benefit
- Unverifiable claims
- Negative impact on other metrics

### 4. Feasibility

✅ **APPROVE if**:
- Implementation plan is clear
- Resources are available
- Timeline is realistic

❌ **REJECT if**:
- Implementation unclear
- Requires unavailable resources
- Timeline unrealistic

### 5. Strategic Fit

✅ **APPROVE if**:
- Aligns with Agency mission
- Supports autonomous development vision
- Moves toward "magnificent masterpieces"

❌ **REJECT if**:
- Misaligned with mission
- Contradicts strategic direction
- Low priority vs other needs

## Step 3: Make Decision

### Option A: Approve

```bash
# Move to approved folder
mv .claude/proposals/pending/[proposal_id].md .claude/proposals/approved/

# Log decision
echo "$(date '+%Y-%m-%d %H:%M:%S') | APPROVED | [proposal_id] | Rationale: [reason]" >> .claude/proposals/review_decisions.log

# Remove from queue
sed -i '' '/[proposal_id]/d' .claude/proposals/review_queue.txt

# Notify agent (optional)
echo "✅ APPROVED: [proposal_id]" >> .claude/proposals/[agent_name]_notifications.txt
```

**Approval Template**:
```markdown
---
**DECISION**: ✅ APPROVED
**Date**: [YYYY-MM-DD]
**Reviewer**: [Your name]
**Priority**: [CRITICAL | HIGH | MEDIUM | LOW]

**Rationale**:
- Constitutional alignment: [✅/❌ + explanation]
- Safety: [✅/❌ + explanation]
- Value: [Expected +X% improvement]
- Feasibility: [Timeline: X weeks]
- Strategic fit: [Alignment statement]

**Implementation Instructions**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Success Criteria**:
- [Metric 1: Target value]
- [Metric 2: Target value]

**Timeline**: Implement by [date]

**Signed**: [Architect name]
---
```

### Option B: Reject

```bash
# Move to rejected folder
mv .claude/proposals/pending/[proposal_id].md .claude/proposals/rejected/

# Log decision with rationale
echo "$(date '+%Y-%m-%d %H:%M:%S') | REJECTED | [proposal_id] | Rationale: [reason]" >> .claude/proposals/review_decisions.log

# Notify agent
echo "❌ REJECTED: [proposal_id] - [reason]" >> .claude/proposals/[agent_name]_notifications.txt
```

**Rejection Template**:
```markdown
---
**DECISION**: ❌ REJECTED
**Date**: [YYYY-MM-DD]
**Reviewer**: [Your name]

**Rationale**:
[Specific reason for rejection]

**Criteria Failed**:
- [ ] Constitutional alignment
- [ ] Safety
- [ ] Value delivery
- [ ] Feasibility
- [ ] Strategic fit

**Feedback for Agent**:
[Constructive feedback on how to improve future proposals]

**Alternative Suggestion**:
[If applicable, suggest alternative approach]

**Signed**: [Architect name]
---
```

### Option C: Request Changes

```bash
# Keep in pending, add review notes
echo "---\n**REVIEW FEEDBACK** ([date]):\n[Detailed feedback]\n---" >> .claude/proposals/pending/[proposal_id].md

# Log decision
echo "$(date '+%Y-%m-%d %H:%M:%S') | CHANGES_REQUESTED | [proposal_id] | Feedback: [summary]" >> .claude/proposals/review_decisions.log
```

### Option D: Defer

```bash
# Keep in pending, mark for future review
echo "🔄 DEFERRED: [proposal_id] - Reason: [reason]" >> .claude/proposals/review_queue.txt
```

## Step 4: Track Metrics

Update improvement metrics:

```bash
# Calculate approval rate
approved=$(ls .claude/proposals/approved/*.md 2>/dev/null | wc -l)
rejected=$(ls .claude/proposals/rejected/*.md 2>/dev/null | wc -l)
total=$((approved + rejected))
rate=$((approved * 100 / total))

echo "Approval Rate: ${rate}% (${approved}/${total})"

# Track by agent
grep "APPROVED" .claude/proposals/review_decisions.log | cut -d'|' -f3 | sort | uniq -c
```

## Use Cases

### Use Case 1: Approve High-Value Proposal

```bash
/architect-review-proposals code_agent_improvement_proposal_20251007 approve

Architect: "Reviewing code_agent proposal..."
Architect: "Constitutional alignment: ✅ Adds Article III enforcement"
Architect: "Safety: ✅ Maintains all protocols"
Architect: "Value: ✅ Expected +10% velocity gain"
Architect: "Feasibility: ✅ 2-hour implementation"
Architect: "Strategic fit: ✅ Critical for autonomous development"

Architect: "✅ APPROVED - Priority: HIGH"
Architect: "Moved to approved/, logged decision"
Architect: "Agent notified. Implementation timeline: This week"
```

### Use Case 2: Reject Unsafe Proposal

```bash
/architect-review-proposals planner_improvement_proposal_20251007 reject

Architect: "Reviewing planner proposal..."
Architect: "Proposal suggests bypassing spec requirement for 'small tasks'"
Architect: "Safety: ❌ Violates Article V (Spec-Driven Development)"
Architect: "This could lead to uncontrolled changes"

Architect: "❌ REJECTED - Rationale: Constitutional violation (Article V)"
Architect: "Feedback: Consider proposing threshold criteria for 'small tasks' instead"
Architect: "Alternative: Define 'simple task' exemption with safety guardrails"
```

### Use Case 3: Batch Review

```bash
/architect-review-proposals all review

Architect: "Batch reviewing 5 pending proposals..."

Architect: "1/5 - code_agent: ✅ APPROVED (Constitutional+Tools)"
Architect: "2/5 - planner: 🔄 CHANGES_REQUESTED (Need metrics)"
Architect: "3/5 - merger: ✅ APPROVED (Test integration)"
Architect: "4/5 - auditor: ❌ REJECTED (Duplicate of existing)"
Architect: "5/5 - toolsmith: ✅ APPROVED (Workflow clarity)"

Architect: "Summary: 3 approved, 1 rejected, 1 needs changes"
Architect: "Approval rate: 75% (3/4 decided)"
```

## Review Dashboard

Generate review metrics:

```bash
# Create dashboard
cat > .claude/proposals/review_dashboard.md << 'DASHBOARD'
# Architect Review Dashboard

**Last Updated**: $(date)

## Pending Review
$(ls .claude/proposals/pending/*.md 2>/dev/null | wc -l) proposals

## Approval Metrics
- **Approved**: $(ls .claude/proposals/approved/*.md 2>/dev/null | wc -l)
- **Rejected**: $(ls .claude/proposals/rejected/*.md 2>/dev/null | wc -l)
- **Approval Rate**: [calculated]%

## By Agent
$(grep "APPROVED" .claude/proposals/review_decisions.log | cut -d'|' -f3 | sort | uniq -c)

## Average Review Time
[To be calculated from timestamps]

## Impact Tracking
[Audit score improvements from implemented proposals]
DASHBOARD
```

## Success Metrics

- **Approval Rate**: Target >80% (indicates quality proposals)
- **Review Turnaround**: Target <24 hours (keeps agents unblocked)
- **Implementation Rate**: Target 100% of approved proposals
- **Impact**: Target +5-10 audit score points per cycle

## Principles

**As Architect, you balance**:
- **Innovation** vs **Stability**
- **Agent Autonomy** vs **Safety**
- **Speed** vs **Quality**
- **Individual Improvements** vs **System Coherence**

**Your role is to**:
- Enable agent evolution
- Maintain constitutional integrity
- Ensure system safety
- Drive strategic alignment

---

**Remember**: You're not blocking progress - you're ensuring it's safe, valuable, and aligned. Approve boldly when criteria are met, reject firmly when they're not.
