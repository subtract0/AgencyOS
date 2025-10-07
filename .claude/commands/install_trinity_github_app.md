# Install Trinity GitHub App

**Purpose**: Set up Trinity as a GitHub App that comments on Pull Requests with code quality audits.

**Similar to**: Claude Code's `/install_github_app` command

---

## Command Flow

When user runs `/install_trinity_github_app`:

1. **Check Prerequisites**
   - GitHub CLI (`gh`) installed and authenticated
   - Repository has `.github/workflows/trinity-audit.yml`
   - Scripts exist: `format_pr_comment.py`, `continuous_audit_m4pro.py`

2. **Create GitHub App** (Interactive)
   - Name: "Trinity AI Code Auditor"
   - Description: "Autonomous code quality auditor powered by local LLMs"
   - Homepage URL: "https://github.com/subtract0/Agency"
   - Webhook: Optional (for auto-trigger, not needed for MVP)
   - Permissions:
     - Pull Requests: Read & Write (to post comments)
     - Contents: Read (to checkout PR code)
     - Metadata: Read
   - Events subscription:
     - Pull Request (opened, synchronize, reopened)

3. **Install App on Repository**
   - Prompt user: "Install on all repos or select repos?"
   - Default: Current repository only
   - Generate installation link
   - Wait for user to click "Install"

4. **Configure Workflow**
   - Update `.github/workflows/trinity-audit.yml`
   - Change trigger from `workflow_dispatch` to:
     ```yaml
     on:
       pull_request:
         types: [opened, synchronize, reopened]
     ```
   - Commit and push change

5. **Test Installation**
   - Trigger on existing PR or create test PR
   - Verify comment posts successfully
   - Display success message with next steps

---

## Implementation

```bash
#!/bin/bash
# Trinity GitHub App Installation Script

set -e

echo "🤖 Installing Trinity GitHub App..."
echo ""

# Step 1: Check prerequisites
echo "1️⃣ Checking prerequisites..."

if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found. Install: brew install gh"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI not authenticated. Run: gh auth login"
    exit 1
fi

if [ ! -f ".github/workflows/trinity-audit.yml" ]; then
    echo "❌ Trinity workflow not found. Merge PR #39 first."
    exit 1
fi

echo "✅ Prerequisites met"
echo ""

# Step 2: Create GitHub App
echo "2️⃣ Creating GitHub App..."
echo ""
echo "GitHub doesn't support CLI app creation yet."
echo "Please create manually:"
echo ""
echo "  👉 https://github.com/settings/apps/new"
echo ""
echo "Use these settings:"
echo "  - Name: Trinity-AI-Code-Auditor-[YOURNAME]"
echo "  - Homepage: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "  - Webhook: [Leave unchecked for MVP]"
echo "  - Permissions:"
echo "      Pull Requests: Read & Write"
echo "      Contents: Read"
echo "      Metadata: Read"
echo "  - Events:"
echo "      Pull Request"
echo ""

read -p "Press ENTER after creating the app..."

# Step 3: Get App ID
read -p "Enter your GitHub App ID (from app settings): " APP_ID

if [ -z "$APP_ID" ]; then
    echo "❌ App ID required"
    exit 1
fi

echo "✅ App ID: $APP_ID"
echo ""

# Step 4: Install App
echo "3️⃣ Installing app on repository..."
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo ""
echo "  👉 https://github.com/apps/trinity-ai-code-auditor-[YOURNAME]/installations/new"
echo ""
echo "Select: $REPO"
echo ""

read -p "Press ENTER after installing..."

# Step 5: Configure auto-trigger (optional)
echo ""
read -p "4️⃣ Enable auto-trigger on PR open? (y/n): " ENABLE_AUTO

if [ "$ENABLE_AUTO" = "y" ]; then
    echo "Updating workflow to auto-trigger..."

    # Backup workflow
    cp .github/workflows/trinity-audit.yml .github/workflows/trinity-audit.yml.backup

    # Replace trigger
    sed -i '' 's/workflow_dispatch/pull_request/' .github/workflows/trinity-audit.yml
    sed -i '' '/pull_request:/a\
    types: [opened, synchronize, reopened]
' .github/workflows/trinity-audit.yml

    # Commit
    git add .github/workflows/trinity-audit.yml
    git commit -m "feat: Enable auto-trigger for Trinity on PR events"
    git push

    echo "✅ Auto-trigger enabled"
else
    echo "⏭️  Skipping auto-trigger (manual only)"
fi

echo ""
echo "🎉 Trinity GitHub App installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Open a Pull Request"
echo "  2. Trinity will automatically comment (if auto-trigger enabled)"
echo "  3. Or trigger manually: gh workflow run trinity-audit.yml -f pr_number=N"
echo ""
echo "💰 Monetization ready:"
echo "  - Fiverr: Use docs/FIVERR_GIG_TEMPLATE.md"
echo "  - Freelance: Charge \$97 per audit"
echo "  - SaaS: \$49/mo per repo"
echo ""
```

---

## Usage

### Manual Installation

```bash
# Run the command
/install_trinity_github_app

# Follow interactive prompts
```

### Programmatic Installation

```python
# Use this approach for automated setup
from tools.install_trinity_app import install_trinity_app

result = install_trinity_app(
    repo="subtract0/Agency",
    app_name="Trinity-AI-Code-Auditor",
    auto_trigger=True  # Enable auto-commenting on PRs
)

if result.is_ok():
    print("✅ Trinity installed successfully")
    print(f"App ID: {result.unwrap()['app_id']}")
else:
    print(f"❌ Installation failed: {result.unwrap_err()}")
```

---

## For PR #39 Specifically

To install and comment on PR #39:

```bash
# Step 1: Merge PR #39 (to get workflow in main branch)
gh pr merge 39 --squash --auto

# Step 2: Wait for merge, then install app
/install_trinity_github_app

# Step 3: Trigger on PR #39 (it will still exist as merged)
# Or create new test PR:
git checkout -b test-trinity-app-comment
echo "Testing Trinity comment" > test_trinity.md
git add test_trinity.md
git commit -m "test: Trigger Trinity comment"
git push -u origin test-trinity-app-comment
gh pr create --title "Test Trinity Comment" --body "Validating Trinity GitHub App"

# Trinity will auto-comment with audit results
```

---

## Troubleshooting

### "workflow not found"
- Ensure PR #39 is merged to main
- Check `.github/workflows/trinity-audit.yml` exists

### "permission denied" when posting comment
- GitHub App needs "Pull Requests: Write" permission
- Reinstall app with correct permissions

### "no audit results"
- Check workflow logs: `gh run view --log`
- Verify `continuous_audit_m4pro.py` runs successfully
- Check artifacts uploaded: `gh run view`

### Comment not appearing
- Verify app is installed on repo
- Check app has PR write permissions
- Look for errors in Actions logs

---

## Security Notes

- App only has access to repositories you explicitly install it on
- Private key stored securely (never commit to repo)
- App can be uninstalled anytime from GitHub settings
- Audit runs in GitHub Actions (not on your local machine)

---

## Monetization Integration

After installation, Trinity becomes:

1. **Fiverr Service** ($97/audit)
   - Customer gives GitHub repo URL
   - You install Trinity on their repo (temporary)
   - Run audit, send results, uninstall

2. **GitHub Marketplace App** ($49/mo)
   - Public listing on GitHub Marketplace
   - Auto-install for customers
   - Charge per repository

3. **White-Label License** ($1,997)
   - Customers run their own Trinity instance
   - Rebrand with their company name
   - Enterprise support included

---

## Next Steps After Installation

1. **Test on real PR**
   - Create PR with intentional bugs
   - Verify Trinity catches them
   - Check comment formatting

2. **Customize comment template**
   - Edit `scripts/format_pr_comment.py`
   - Add your branding
   - Customize messaging

3. **Launch marketing**
   - Screenshot Trinity comment
   - Post on Reddit: "Built AI code auditor"
   - Launch Fiverr gig
   - Share on Twitter

4. **Scale to customers**
   - Offer free audits to first 3 people
   - Collect testimonials
   - Start charging $97/audit

---

**Ready to install?** Run `/install_trinity_github_app` now!
