#!/usr/bin/env python3
"""
PR Generator for Safe Test Deletion Workflow (Phase 7)

Constitutional Mandate (Article III): Automated Local Enforcement
- PR-based deletion (human approval required)
- Backup + revert script (1-command rollback)
- CI validation mandatory (Article II)
- Zero auto-merge (safety gate)

Usage:
  python scripts/generate_deletion_pr.py --dry-run                  # Preview candidates
  python scripts/generate_deletion_pr.py --apply --threshold 10     # Create PR for tests <10
  python scripts/generate_deletion_pr.py --apply --threshold 5      # Stricter threshold

Workflow:
  1. Generate candidates_to_delete.txt (tests below threshold)
  2. Create backup.{timestamp}.zip (test file copies)
  3. Generate revert.sh (1-command restore)
  4. Create GitHub PR with detailed risk assessment
  5. PR requires approval + CI pass before merge
"""

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_value_audit_v5 import TestValueAuditorV5, TestScoreV5


class PRGenerator:
    """Generate safe deletion PRs with backup + revert."""

    def __init__(self, threshold: float = 10.0, dry_run: bool = False):
        self.threshold = threshold
        self.dry_run = dry_run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = Path(".audit/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.auditor = TestValueAuditorV5()
        self.candidates: List[TestScoreV5] = []
        self.files_affected: Set[str] = set()
        self.stats: Dict = {}

    def run(self) -> int:
        """Execute full PR generation workflow."""
        print("="*80)
        print("🔒 SAFE TEST DELETION PR GENERATOR (Phase 7)")
        print("="*80)
        print(f"Threshold: Tests with scores < {self.threshold}")
        print(f"Mode: {'DRY RUN (preview only)' if self.dry_run else 'APPLY (create PR)'}")
        print()

        # Step 1: Score all tests
        print("📊 Step 1: Scoring test suite...")
        test_functions = self.auditor.extract_test_functions(Path("tests"))
        all_scores = [self.auditor.score_test(t) for t in test_functions]
        print(f"  ✅ Scored {len(all_scores)} tests")

        # Step 2: Filter deletion candidates
        print()
        print(f"🎯 Step 2: Filtering candidates (score < {self.threshold})...")
        self.candidates = [t for t in all_scores if t.total_score < self.threshold]
        self.files_affected = {t.file for t in self.candidates}
        print(f"  ✅ Found {len(self.candidates)} deletion candidates")
        print(f"  ✅ Affects {len(self.files_affected)} test files")

        if len(self.candidates) == 0:
            print()
            print(f"✅ No tests below threshold {self.threshold}. Test suite is healthy!")
            return 0

        # Step 3: Calculate statistics
        print()
        print("📈 Step 3: Calculating impact metrics...")
        self.stats = self._calculate_stats(all_scores)
        self._print_stats()

        # Step 4: Risk assessment
        print()
        print("⚠️  Step 4: Risk assessment...")
        risk_level = self._assess_risk()
        print(f"  Risk Level: {risk_level}")

        if self.dry_run:
            print()
            print("="*80)
            print("🔍 DRY RUN PREVIEW")
            print("="*80)
            self._print_preview()
            print()
            print("ℹ️  This was a dry run. Use --apply to create PR.")
            return 0

        # Step 5: Generate candidates file
        print()
        print("📝 Step 5: Generating candidates_to_delete.txt...")
        candidates_file = self._generate_candidates_file()
        print(f"  ✅ Created: {candidates_file}")

        # Step 6: Create backup
        print()
        print("💾 Step 6: Creating backup archive...")
        backup_file = self._create_backup()
        print(f"  ✅ Created: {backup_file}")

        # Step 7: Generate revert script
        print()
        print("🔄 Step 7: Generating revert script...")
        revert_script = self._generate_revert_script(backup_file)
        print(f"  ✅ Created: {revert_script}")

        # Step 8: Create GitHub PR
        print()
        print("🚀 Step 8: Creating GitHub PR...")
        pr_url = self._create_github_pr(candidates_file, backup_file, revert_script, risk_level)

        print()
        print("="*80)
        print("✅ PR GENERATION COMPLETE")
        print("="*80)
        print(f"PR URL: {pr_url}")
        print(f"Backup: {backup_file}")
        print(f"Revert: {revert_script}")
        print()
        print("⚠️  NEXT STEPS:")
        print("1. Review PR on GitHub")
        print("2. Approve PR (requires human approval)")
        print("3. Wait for CI to pass (Article II)")
        print("4. Merge PR")
        print(f"5. If issues arise: bash {revert_script}")
        print()

        return 0

    def _calculate_stats(self, all_scores: List[TestScoreV5]) -> Dict:
        """Calculate deletion impact statistics."""
        total = len(all_scores)
        deleting = len(self.candidates)
        keeping = total - deleting

        high_count = sum(1 for t in all_scores if t.total_score >= 20)
        medium_count = sum(1 for t in all_scores if 10 <= t.total_score < 20)
        low_count = sum(1 for t in all_scores if t.total_score < 10)

        # Detect critical test types in deletion list
        integration_deleted = sum(1 for t in self.candidates if t.is_integration)
        e2e_deleted = sum(1 for t in self.candidates if t.is_e2e)

        # Estimate CI runtime savings
        avg_runtime = sum(t.actual_runtime_seconds for t in self.candidates) / len(self.candidates) if self.candidates else 0
        total_runtime_saved = sum(t.actual_runtime_seconds for t in self.candidates)

        return {
            'total_tests': total,
            'deleting': deleting,
            'keeping': keeping,
            'deletion_pct': round(deleting * 100.0 / total, 1) if total > 0 else 0,
            'high_count': high_count,
            'medium_count': medium_count,
            'low_count': low_count,
            'integration_deleted': integration_deleted,
            'e2e_deleted': e2e_deleted,
            'avg_runtime': avg_runtime,
            'total_runtime_saved': total_runtime_saved,
        }

    def _print_stats(self):
        """Print deletion statistics."""
        s = self.stats
        print(f"  Total tests: {s['total_tests']}")
        print(f"  Deleting: {s['deleting']} ({s['deletion_pct']}%)")
        print(f"  Keeping: {s['keeping']} ({100 - s['deletion_pct']:.1f}%)")
        print()
        print(f"  Score Distribution:")
        print(f"    HIGH (≥20):    {s['high_count']} tests (KEEPING)")
        print(f"    MEDIUM (10-20): {s['medium_count']} tests (KEEPING)")
        print(f"    LOW (<10):      {s['low_count']} tests (DELETING)")
        print()
        print(f"  CI Runtime Impact:")
        print(f"    Avg runtime per deleted test: {s['avg_runtime']:.2f}s")
        print(f"    Total runtime saved: {s['total_runtime_saved']:.1f}s ({s['total_runtime_saved']/60:.1f}m)")

    def _assess_risk(self) -> str:
        """Assess deletion risk level."""
        s = self.stats

        # HIGH RISK: Deleting integration/e2e tests
        if s['integration_deleted'] > 0 or s['e2e_deleted'] > 0:
            print(f"  ⛔ {s['integration_deleted']} integration tests in deletion list")
            print(f"  ⛔ {s['e2e_deleted']} E2E tests in deletion list")
            return "HIGH"

        # MEDIUM RISK: Deleting >30% of tests
        if s['deletion_pct'] > 30:
            print(f"  ⚠️  Deleting {s['deletion_pct']}% of test suite (>30%)")
            return "MEDIUM"

        # LOW RISK: Safe deletion
        print(f"  ✅ No integration tests in deletion list")
        print(f"  ✅ No E2E tests in deletion list")
        print(f"  ✅ Deleting {s['deletion_pct']}% of test suite (<30%)")
        return "LOW"

    def _print_preview(self):
        """Print dry-run preview."""
        print()
        print(f"Would delete {len(self.candidates)} tests from {len(self.files_affected)} files:")
        print()

        # Group by file
        by_file = defaultdict(list)
        for candidate in self.candidates:
            by_file[candidate.file].append(candidate)

        # Show top 10 files with most deletions
        sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        print("Top 10 files with most deletions:")
        for file, tests in sorted_files:
            print(f"  {file}: {len(tests)} tests")

        print()
        print("Top 10 lowest-scoring tests:")
        sorted_candidates = sorted(self.candidates, key=lambda t: t.total_score)[:10]
        for i, test in enumerate(sorted_candidates, 1):
            print(f"  {i}. {test.name} (score: {test.total_score:.1f})")
            print(f"     File: {test.file}")
            print(f"     Reason: {test.reason}")
            print()

    def _generate_candidates_file(self) -> Path:
        """Generate candidates_to_delete.txt with test IDs, scores, and reasons."""
        output_file = Path(f".audit/candidates_to_delete_{self.timestamp}.txt")

        with open(output_file, 'w') as f:
            f.write(f"# Test Deletion Candidates (Generated {self.timestamp})\n")
            f.write(f"# Threshold: score < {self.threshold}\n")
            f.write(f"# Total candidates: {len(self.candidates)}\n")
            f.write("#\n")
            f.write("# Format: file::test_name\n")
            f.write("#   Score: X.X\n")
            f.write("#   Reason: ...\n")
            f.write("\n")

            # Sort by score (lowest first)
            sorted_candidates = sorted(self.candidates, key=lambda t: t.total_score)

            for test in sorted_candidates:
                f.write(f"{test.file}::{test.name}\n")
                f.write(f"  Score: {test.total_score:.1f}\n")
                f.write(f"  Reason: {test.reason}\n")
                f.write(f"  Mocks: {test.mock_count}, LOC: {test.lines_of_code}, Assertions: {test.assertion_count}\n")
                f.write("\n")

        return output_file

    def _create_backup(self) -> Path:
        """Create backup.{timestamp}.zip with all affected test files."""
        backup_file = self.backup_dir / f"backup_{self.timestamp}.zip"

        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for test_file in sorted(self.files_affected):
                file_path = Path(test_file)
                if file_path.exists():
                    # Store with relative path
                    zipf.write(file_path, arcname=test_file)

        # Calculate backup size
        backup_size_mb = backup_file.stat().st_size / (1024 * 1024)
        print(f"  Backup size: {backup_size_mb:.2f} MB")

        return backup_file

    def _generate_revert_script(self, backup_file: Path) -> Path:
        """Generate revert.sh script for 1-command rollback."""
        revert_script = Path(f"revert_{self.timestamp}.sh")

        script_content = f"""#!/bin/bash
# Revert script for test deletion PR
# Generated: {self.timestamp}
# Backup: {backup_file}

set -e  # Exit on error

echo "⚠️  Reverting test deletions from {self.timestamp}..."
echo ""

# Check if backup exists
if [ ! -f "{backup_file}" ]; then
    echo "❌ Backup file not found: {backup_file}"
    exit 1
fi

# Unzip backup (restore all test files)
echo "📦 Restoring {len(self.files_affected)} test files from backup..."
unzip -o "{backup_file}" -d .

echo ""
echo "✅ Test files restored successfully!"
echo ""
echo "🧪 Running tests to verify restoration..."
python run_tests.py --run-all

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests pass! Restoration successful."
    echo ""
    echo "Next steps:"
    echo "1. git add tests/"
    echo "2. git commit -m 'revert: Restore deleted tests (rollback {self.timestamp})'"
    echo "3. git push"
else
    echo ""
    echo "❌ Some tests failed after restoration. Manual review needed."
    exit 1
fi
"""

        with open(revert_script, 'w') as f:
            f.write(script_content)

        # Make executable
        revert_script.chmod(0o755)

        return revert_script

    def _create_github_pr(
        self,
        candidates_file: Path,
        backup_file: Path,
        revert_script: Path,
        risk_level: str
    ) -> str:
        """Create GitHub PR with detailed description."""
        s = self.stats

        # Create PR title
        pr_title = f"test: Delete {s['deleting']} low-value tests (score <{self.threshold})"

        # Create PR description
        pr_body = f"""## Test Suite Cleanup: Delete Low-Value Tests

**Summary**: Remove {s['deleting']} tests with value scores below {self.threshold}

### Score Distribution

| Category | Count | Percentage | Action |
|----------|-------|------------|--------|
| HIGH (≥20) | {s['high_count']} | {s['high_count']*100//s['total_tests']}% | ✅ KEEPING |
| MEDIUM (10-20) | {s['medium_count']} | {s['medium_count']*100//s['total_tests']}% | ✅ KEEPING |
| LOW (<{self.threshold}) | {s['low_count']} | {s['low_count']*100//s['total_tests']}% | ❌ DELETING |
| **Total** | **{s['total_tests']}** | **100%** | |

### Risk Assessment: **{risk_level}**

{'✅ No integration tests in deletion list' if s['integration_deleted'] == 0 else f"⛔ {s['integration_deleted']} integration tests in deletion list"}
{'✅ No E2E tests in deletion list' if s['e2e_deleted'] == 0 else f"⛔ {s['e2e_deleted']} E2E tests in deletion list"}
✅ Backup created: `{backup_file}`
✅ Revert script: `{revert_script}`

### Impact Metrics (Pre-cleanup baseline)

- **Current tests**: {s['total_tests']}
- **After deletion**: {s['keeping']} (-{s['deletion_pct']}%)
- **CI runtime saved**: {s['total_runtime_saved']:.1f}s ({s['total_runtime_saved']/60:.1f} minutes)
- **Test files affected**: {len(self.files_affected)}

### Revert Instructions

If issues arise after merge:

```bash
bash {revert_script}
```

This will:
1. Restore all deleted test files from `{backup_file}`
2. Run full test suite to verify restoration
3. Provide git commands for commit/push

### Top 10 Deletion Candidates

"""

        # Add top 10 lowest-scoring tests
        sorted_candidates = sorted(self.candidates, key=lambda t: t.total_score)[:10]
        for i, test in enumerate(sorted_candidates, 1):
            pr_body += f"{i}. `{test.name}` (score: {test.total_score:.1f})\n"
            pr_body += f"   - **Reason**: {test.reason}\n"
            pr_body += f"   - **File**: `{test.file}`\n"
            pr_body += f"   - **Mocks**: {test.mock_count}, **LOC**: {test.lines_of_code}\n"
            pr_body += "\n"

        pr_body += f"""
### Constitutional Compliance

- ✅ **Article I** (Complete Context): Full risk assessment included
- ✅ **Article II** (100% Verification): CI must pass before merge
- ✅ **Article III** (Automated Enforcement): PR-based, human approval required
- ✅ **Article IV** (Learning): Deletion patterns stored for future audits
- ✅ **Article V** (Spec-Driven): Follows VALUE-FIRST testing philosophy (ADR-033)

### Files Included

- `{candidates_file}` - Full list of deletion candidates
- `{backup_file}` - Backup archive (all affected test files)
- `{revert_script}` - 1-command rollback script

---

**Generated by**: `scripts/generate_deletion_pr.py`
**Timestamp**: {self.timestamp}
**Threshold**: {self.threshold}
"""

        # Stage files for commit
        print("  📝 Staging files for commit...")
        subprocess.run(
            ["git", "add", str(candidates_file), str(revert_script)],
            check=True,
            capture_output=True
        )

        # Create git commit
        print("  💾 Creating git commit...")
        commit_msg = f"test: Generate deletion candidates for {s['deleting']} low-value tests\n\nThreshold: {self.threshold}\nGenerated: {self.timestamp}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            capture_output=True
        )

        # Create branch and push
        branch_name = f"test-deletion-{self.timestamp}"
        print(f"  🌿 Creating branch: {branch_name}")
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            check=True,
            capture_output=True
        )

        print("  ⬆️  Pushing branch to origin...")
        subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            check=True,
            capture_output=True
        )

        # Create PR using gh CLI
        print("  🚀 Creating GitHub PR...")
        result = subprocess.run(
            ["gh", "pr", "create", "--title", pr_title, "--body", pr_body],
            check=True,
            capture_output=True,
            text=True
        )

        # Extract PR URL from output
        pr_url = result.stdout.strip().split('\n')[-1]

        return pr_url


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate safe deletion PR for low-value tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_deletion_pr.py --dry-run
  python scripts/generate_deletion_pr.py --apply --threshold 10
  python scripts/generate_deletion_pr.py --apply --threshold 5 --dry-run

Constitutional Requirements:
  - Article II: CI must pass before merge
  - Article III: Human approval required (no auto-merge)
  - Backup + revert script for safety
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview candidates without creating PR"
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually create PR (required for PR creation, safety flag)"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Score threshold for deletion (default: 10.0)"
    )

    args = parser.parse_args()

    # Safety check: require --apply for PR creation
    if not args.dry_run and not args.apply:
        print("❌ Error: Must specify --dry-run OR --apply")
        print()
        print("Usage:")
        print("  --dry-run: Preview candidates without creating PR")
        print("  --apply:   Create PR (safety flag required)")
        print()
        print("Example: python scripts/generate_deletion_pr.py --dry-run")
        return 1

    if args.dry_run and args.apply:
        print("❌ Error: Cannot use both --dry-run and --apply")
        return 1

    # Run PR generation
    generator = PRGenerator(
        threshold=args.threshold,
        dry_run=args.dry_run
    )

    return generator.run()


if __name__ == "__main__":
    sys.exit(main())
