#!/bin/bash
# Migration script from Agency fork to AgencyOS private repo

echo "==================================="
echo "Migration to AgencyOS Private Repo"
echo "==================================="
echo ""
echo "This script will help you migrate from the Agency fork to AgencyOS private repo."
echo ""

# Step 1: Instructions for creating the repo
echo "📋 Step 1: Create the private repository"
echo "----------------------------------------"
echo "Please go to https://github.com/new and create a new repository with:"
echo "  • Repository name: AgencyOS"
echo "  • Description: Elite autonomous agent orchestration system"
echo "  • Visibility: Private"
echo "  • Do NOT initialize with README, .gitignore, or license"
echo ""
read -p "Press Enter when you've created the repository..."

# Step 2: Add new remote
echo ""
echo "📋 Step 2: Configuring remotes"
echo "------------------------------"
echo "Adding AgencyOS as the new primary remote..."

# Remove existing agencyos remote if it exists
git remote remove agencyos 2>/dev/null || true

# Add AgencyOS as new remote
git remote add agencyos https://github.com/subtract0/AgencyOS.git

# Rename origin to upstream (to keep reference to original fork)
git remote rename origin upstream 2>/dev/null || true

# Make agencyos the new origin
git remote add origin https://github.com/subtract0/AgencyOS.git 2>/dev/null || true

echo "Current remotes:"
git remote -v

# Step 3: Push to new repository
echo ""
echo "📋 Step 3: Pushing to AgencyOS"
echo "------------------------------"
echo "Pushing all branches and tags to the new repository..."

# Push main branch
git push agencyos main

# Push all tags
git push agencyos --tags

# Set upstream for main branch
git branch --set-upstream-to=agencyos/main main

echo ""
echo "📋 Step 4: Update local configuration"
echo "-------------------------------------"

# Update the primary remote
git remote remove origin 2>/dev/null || true
git remote rename agencyos origin

echo ""
echo "✅ Migration Complete!"
echo "====================="
echo ""
echo "Your repository now points to:"
git remote -v
echo ""
echo "The original fork is still accessible as 'upstream' remote."
echo "You can remove it with: git remote remove upstream"
echo ""
echo "Next steps:"
echo "1. Update any CI/CD webhooks to point to the new repository"
echo "2. Update any deployment configurations"
echo "3. Invite team members to the private repository"
echo "4. Update the README if needed to reflect the new repository location"