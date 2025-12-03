# Morning Brief Generator

Generate a comprehensive morning briefing with calendar, email, and priorities.

## What This Does

Creates a personalized morning brief that includes:
- **Today's Schedule**: All calendar events with prep suggestions
- **Email Triage**: Categorized as Urgent, Needs Response, or FYI
- **Suggested Priorities**: Time-based focus recommendations
- **Focus Time Analysis**: How much uninterrupted time you have

## Usage

```bash
# Generate and display brief
/morning-brief

# Generate and save to file
/morning-brief --save

# Generate quietly (just save, no console output)
/morning-brief --save --quiet
```

## Output Location

Briefs are saved to: `~/.agency/briefs/YYYY-MM-DD.md`

## Night Shift Integration

To auto-generate briefs every morning, add to Night Shift backlog:

```json
{
  "type": "morning_brief",
  "schedule": "06:00",
  "config": {
    "save": true,
    "email": "your@email.com"
  }
}
```

## Example Output

```markdown
# Morning Brief - Monday, January 15, 2024

> Good morning! New week, fresh start.

---

## 📅 TODAY'S SCHEDULE

- **9:00 AM**: Team Standup
  - *Prep: Review notes and agenda*
- **2:00 PM**: 1:1 with Sarah
  - *Prep: Review notes and agenda*
- **4:00 PM**: Deep Work Block

## 📧 EMAIL TRIAGE

### 🔴 Urgent
- **legal@company.com**: Contract Review - Action Required

### 🟡 Needs Response
- **sarah@company.com**: Re: Q1 Planning

### 🟢 FYI (12 more)
- newsletter@tech.com: Weekly Tech Digest

## 🎯 SUGGESTED PRIORITIES

- You have 2 hour(s) of focus time before your first event
- Start with a quick planning session to set the week's priorities

## ⏰ FOCUS TIME

🟡 **Good**: ~5.0 hours of potential focus time today

---

*Have a productive day!*
```

## Configuration

Set these environment variables for real API integration:

```bash
# Calendar backend
LIFE_CALENDAR_BACKEND=google  # or "apple" or "mock"

# Email backend
LIFE_EMAIL_BACKEND=gmail      # or "smtp" or "mock"

# Google OAuth (if using Google backends)
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
```

## Implementation

Run the generator:

```python
from tools.life.morning_brief import MorningBriefGenerator

generator = MorningBriefGenerator()
brief = generator.generate()
print(brief.to_markdown())

# Save to file
path = generator.save(brief)
print(f"Saved to: {path}")
```
