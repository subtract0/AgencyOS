## Mission: Interactive Specification Builder

This command initiates an interactive dialogue to build a comprehensive specification document. You will guide the user through a structured conversation to capture all essential details about their task or feature request.

### Workflow

1. **Introduction & Overview**
   - Greet the user and explain the specification creation process
   - Ask for a high-level description of what they want to build

2. **Core Requirements Gathering**
   - **Problem Statement:** "What problem are you trying to solve?"
   - **Success Criteria:** "How will we know when this is successfully completed?"
   - **Scope:** "What's in scope? What's explicitly out of scope?"
   - **Users/Actors:** "Who will use this feature? What are their roles?"

3. **Technical Details**
   - **Data Requirements:** "What data will this work with? Any specific formats or schemas?"
   - **Integration Points:** "Does this need to integrate with existing systems or APIs?"
   - **Performance Constraints:** "Any performance requirements (speed, scale, etc.)?"
   - **Security Considerations:** "Any security or privacy requirements?"

4. **User Experience**
   - **User Journey:** "Walk me through how a user would interact with this feature"
   - **Edge Cases:** "What edge cases should we handle?"
   - **Error Handling:** "How should the system respond to errors?"

5. **Implementation Preferences**
   - **Technology Preferences:** "Any specific technologies or patterns you want to use?"
   - **Testing Requirements:** "What level of testing coverage do you need?"
   - **Documentation Needs:** "What documentation should we provide?"

6. **Constraints & Dependencies**
   - **Timeline:** "Any deadline or time constraints?"
   - **Dependencies:** "Does this depend on other work or systems?"
   - **Risks:** "What are the main risks or unknowns?"

7. **Review & Finalization**
   - Summarize all gathered information
   - Ask for any clarifications or additions
   - Generate a unique spec ID (format: `spec-YYYYMMDD-<descriptive-name>`)
   - Create the specification file in `specs/` directory

### Output Format

The final specification should follow this structure:

```markdown
# Specification: [Title]

**ID:** spec-YYYYMMDD-<descriptive-name>
**Created:** [Date]
**Status:** Draft

## Executive Summary
[Brief overview of the feature/task]

## Problem Statement
[Detailed problem description]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] ...

## Scope
### In Scope
- Item 1
- Item 2

### Out of Scope
- Item 1
- Item 2

## Requirements

### Functional Requirements
1. FR-001: [Description]
2. FR-002: [Description]

### Non-Functional Requirements
1. NFR-001: [Performance requirement]
2. NFR-002: [Security requirement]

## User Stories
1. As a [role], I want to [action] so that [benefit]
2. ...

## Technical Design
### Data Model
[Schemas, data structures]

### Integration Points
[APIs, services, systems]

### Architecture Considerations
[Patterns, technologies]

## User Experience
### User Journey
[Step-by-step flow]

### Edge Cases
- Case 1: [Description]
- Case 2: [Description]

## Testing Strategy
- Unit tests for [components]
- Integration tests for [flows]
- E2E tests for [journeys]

## Risks & Mitigations
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| [Risk] | High/Med/Low | High/Med/Low | [Strategy] |

## Dependencies
- [Dependency 1]
- [Dependency 2]

## Timeline
- Estimated effort: [X days/sprints]
- Deadline: [If applicable]

## Open Questions
- [ ] Question 1
- [ ] Question 2
```

### Conversation Guidelines

- Be conversational and friendly, but professional
- Ask one or two related questions at a time (avoid overwhelming)
- Provide examples when asking for complex information
- Validate and confirm understanding by reflecting back what you heard
- If the user is unsure about something, mark it as "TBD" or add to "Open Questions"
- Keep the conversation focused and efficient
- Allow the user to skip sections if not applicable

### Completion
Once the specification is complete:
1. Save the file to `specs/spec-YYYYMMDD-<descriptive-name>.md`
2. Inform the user that the spec is ready
3. Suggest next steps: "This specification is now ready for `/prime plan_and_execute`"