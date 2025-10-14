#!/bin/bash

# Setup Branch Protection for Constitutional Compliance
# Requires: GitHub Pro account, gh CLI authenticated

set -e

REPO="subtract0/AgencyOS"
BRANCH="main"

echo "🔒 Setting up branch protection for $REPO:$BRANCH"
echo ""
echo "Article III Enforcement: Automated quality gates with no bypass authority"
echo ""

# Check if GitHub Pro is active
echo "Checking GitHub Pro status..."
if ! gh api repos/$REPO/branches/$BRANCH/protection 2>&1 | grep -q "404"; then
    echo "⚠️  Branch protection already exists, updating..."
fi

# Configure branch protection rules
echo ""
echo "Configuring branch protection rules..."

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/$REPO/branches/$BRANCH/protection \
  -f "required_status_checks[strict]=true" \
  -f "required_status_checks[contexts][]=CI Summary (All Checks)" \
  -f "enforce_admins=true" \
  -f "required_pull_request_reviews[dismiss_stale_reviews]=true" \
  -f "required_pull_request_reviews[require_code_owner_reviews]=false" \
  -f "required_pull_request_reviews[required_approving_review_count]=0" \
  -f "required_pull_request_reviews[require_last_push_approval]=false" \
  -f "required_linear_history=false" \
  -f "allow_force_pushes=false" \
  -f "allow_deletions=false" \
  -f "required_conversation_resolution=true" \
  -f "lock_branch=false" \
  -f "allow_fork_syncing=true"

echo ""
echo "✅ Branch protection configured successfully!"
echo ""
echo "Rules applied:"
echo "  ✅ Required CI checks: 'CI Summary (All Checks)' must pass"
echo "  ✅ No force pushes allowed"
echo "  ✅ No branch deletion allowed"
echo "  ✅ Enforce for administrators (no bypass)"
echo "  ✅ Require conversation resolution before merge"
echo ""
echo "Constitutional Compliance:"
echo "  Article I:   Complete context (CI runs all tests)"
echo "  Article II:  100% verification (tests must pass to merge)"
echo "  Article III: Automated enforcement (no manual bypass)"
echo "  Article IV:  VectorStore patterns (enforced in tests)"
echo "  Article V:   Spec-driven (ADR checks in CI)"
echo ""
echo "🎯 Next steps:"
echo "  1. Create a feature branch: git checkout -b feat/your-feature"
echo "  2. Make changes and commit"
echo "  3. Push: git push -u origin feat/your-feature"
echo "  4. Create PR: gh pr create"
echo "  5. CI will run automatically (must pass to merge)"
echo ""
