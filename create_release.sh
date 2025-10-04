#!/bin/bash
# Create Constitutional Consciousness v1.0.0 Release
# Run this after PR #20 merges

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

VERSION="v1.0.0"

echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     Creating Release: Constitutional Consciousness       ║"
echo "║     Version: $VERSION                                   ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Check if on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo -e "${YELLOW}⚠ Not on main branch (current: $BRANCH)${NC}"
    echo -e "${YELLOW}Switching to main...${NC}"
    git checkout main
    git pull origin main
fi

# Check if PR #20 is merged
echo -e "${BLUE}Checking PR #20 status...${NC}"
PR_STATE=$(gh pr view 20 --json state --jq .state)
if [ "$PR_STATE" != "MERGED" ]; then
    echo -e "${RED}❌ PR #20 not merged yet (state: $PR_STATE)${NC}"
    echo -e "${YELLOW}Merge PR #20 first, then run this script again${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PR #20 merged${NC}\n"

# Pull latest changes
echo -e "${BLUE}Pulling latest changes...${NC}"
git pull origin main
echo -e "${GREEN}✓ Up to date${NC}\n"

# Create tag
echo -e "${BLUE}Creating tag $VERSION...${NC}"
if git tag | grep -q "^$VERSION$"; then
    echo -e "${YELLOW}⚠ Tag $VERSION already exists${NC}"
    read -p "Delete and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d "$VERSION"
        git push origin --delete "$VERSION" 2>/dev/null || true
    else
        echo -e "${RED}Aborted${NC}"
        exit 1
    fi
fi

git tag -a "$VERSION" -m "Constitutional Consciousness v1.0.0

Self-improving AI feedback loop - Production Release

Features:
- Day 1: Observer + Analyzer (pattern detection)
- Day 2: VectorStore integration (cross-session learning)
- Day 3: Prediction engine (95% accuracy)
- Day 4: Agent evolution (improvement proposals)

Deployment:
- Local-only mode (Ollama + sentence-transformers)
- Hybrid Trinity architecture (48GB M4 Pro optimized)
- Beginner-friendly setup scripts
- Autonomous night run capability

Constitutional Compliance:
- Article I: Complete context ✓
- Article II: 100% verification ✓
- Article III: Automated enforcement ✓
- Article IV: Continuous learning ✓
- Article V: Spec-driven development ✓

Platform: macOS (Apple Silicon)
Cost: \$0
Privacy: 100% Local"

echo -e "${GREEN}✓ Tag created${NC}\n"

# Push tag
echo -e "${BLUE}Pushing tag to GitHub...${NC}"
git push origin "$VERSION"
echo -e "${GREEN}✓ Tag pushed${NC}\n"

# Create GitHub release
echo -e "${BLUE}Creating GitHub release...${NC}"
gh release create "$VERSION" \
    --title "Constitutional Consciousness v1.0.0" \
    --notes-file RELEASE_NOTES_v1.0.0.md \
    --latest

echo -e "${GREEN}✓ Release created${NC}\n"

# Add essential files to release
echo -e "${BLUE}Attaching files to release...${NC}"
FILES=(
    "setup_consciousness.sh"
    "start_night_run.sh"
    "stop_night_run.sh"
    "QUICK_START.md"
    "DEPLOY_NIGHT_RUN.md"
    "README_v1.0.0.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        gh release upload "$VERSION" "$file"
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${YELLOW}⚠${NC} $file not found"
    fi
done

echo -e "\n${GREEN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     ✓ Release v1.0.0 Created Successfully!               ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

RELEASE_URL=$(gh release view "$VERSION" --json url --jq .url)
echo -e "${BOLD}Release URL:${NC} $RELEASE_URL"
echo -e "\n${BOLD}Download command for MacBook Pro:${NC}"
echo -e "${BLUE}curl -L https://github.com/subtract0/Agency/archive/refs/tags/$VERSION.tar.gz -o agency.tar.gz${NC}"
echo -e "\n${GREEN}Ready to deploy! 🚀${NC}\n"
